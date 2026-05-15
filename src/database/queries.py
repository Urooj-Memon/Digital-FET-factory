"""Database access functions for the Customer Success FTE CRM system."""

import os
import json
import asyncpg
from typing import Optional
from datetime import datetime, timedelta

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "fte_db"),
            user=os.getenv("POSTGRES_USER", "fte_user"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            min_size=5,
            max_size=20,
        )
    return _pool


async def close_db_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# --- Customer Operations ---

async def find_customer_by_email(email: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1", email
        )
        return dict(row) if row else None


async def find_customer_by_phone(phone: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT c.* FROM customers c
               JOIN customer_identifiers ci ON ci.customer_id = c.id
               WHERE ci.identifier_type = 'whatsapp' AND ci.identifier_value = $1""",
            phone,
        )
        return dict(row) if row else None


async def create_customer(email: str = None, phone: str = None, name: str = "") -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await conn.fetchval(
            """INSERT INTO customers (email, phone, name)
               VALUES ($1, $2, $3) RETURNING id""",
            email, phone, name,
        )
        if email:
            await conn.execute(
                """INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified)
                   VALUES ($1, 'email', $2, true) ON CONFLICT DO NOTHING""",
                customer_id, email,
            )
        if phone:
            await conn.execute(
                """INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
                   VALUES ($1, 'whatsapp', $2) ON CONFLICT DO NOTHING""",
                customer_id, phone,
            )
        return str(customer_id)


async def resolve_customer(message: dict) -> str:
    """Resolve or create customer from message identifiers."""
    email = message.get("customer_email")
    phone = message.get("customer_phone")
    name = message.get("customer_name", "")

    if email:
        customer = await find_customer_by_email(email)
        if customer:
            return str(customer["id"])
        return await create_customer(email=email, name=name)

    if phone:
        customer = await find_customer_by_phone(phone)
        if customer:
            return str(customer["id"])
        return await create_customer(phone=phone, name=name)

    raise ValueError("Could not resolve customer: no email or phone provided")


# --- Conversation Operations ---

async def get_or_create_conversation(customer_id: str, channel: str) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        active = await conn.fetchrow(
            """SELECT id FROM conversations
               WHERE customer_id = $1 AND status = 'active'
               AND started_at > NOW() - INTERVAL '24 hours'
               ORDER BY started_at DESC LIMIT 1""",
            customer_id,
        )
        if active:
            return str(active["id"])

        conversation_id = await conn.fetchval(
            """INSERT INTO conversations (customer_id, initial_channel, status)
               VALUES ($1, $2, 'active') RETURNING id""",
            customer_id, channel,
        )
        return str(conversation_id)


async def load_conversation_history(conversation_id: str) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT role, content, channel, created_at
               FROM messages WHERE conversation_id = $1
               ORDER BY created_at ASC LIMIT 50""",
            conversation_id,
        )
        messages = []
        for row in rows:
            role = "user" if row["role"] == "customer" else "assistant"
            messages.append({"role": role, "content": row["content"]})
        return messages


async def update_conversation_sentiment(conversation_id: str, score: float):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE conversations SET sentiment_score = $1 WHERE id = $2",
            score, conversation_id,
        )


# --- Message Operations ---

async def store_message(
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
    channel_message_id: str = None,
    latency_ms: int = None,
    tool_calls: list = None,
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        msg_id = await conn.fetchval(
            """INSERT INTO messages
               (conversation_id, channel, direction, role, content,
                channel_message_id, latency_ms, tool_calls, delivery_status)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'sent')
               RETURNING id""",
            conversation_id, channel, direction, role, content,
            channel_message_id, latency_ms,
            json.dumps(tool_calls or []),
        )
        return str(msg_id)


async def update_delivery_status(channel_message_id: str, status: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET delivery_status = $1 WHERE channel_message_id = $2",
            status, channel_message_id,
        )


# --- Ticket Operations ---

async def create_ticket_record(
    customer_id: str,
    source_channel: str,
    subject: str = None,
    category: str = None,
    priority: str = "medium",
    conversation_id: str = None,
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        ticket_id = await conn.fetchval(
            """INSERT INTO tickets
               (customer_id, conversation_id, source_channel, subject, category, priority, status)
               VALUES ($1, $2, $3, $4, $5, $6, 'open')
               RETURNING id""",
            customer_id, conversation_id, source_channel, subject, category, priority,
        )
        return str(ticket_id)


async def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tickets WHERE id = $1", ticket_id)
        if not row:
            return None
        result = dict(row)
        # Get associated messages
        messages = await conn.fetch(
            """SELECT m.* FROM messages m
               JOIN conversations c ON c.id = m.conversation_id
               WHERE c.id = $1
               ORDER BY m.created_at ASC""",
            result.get("conversation_id"),
        )
        result["messages"] = [dict(m) for m in messages] if messages else []
        return result


async def update_ticket_status(ticket_id: str, status: str, notes: str = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        resolved_at = datetime.utcnow() if status in ("resolved", "closed") else None
        await conn.execute(
            """UPDATE tickets SET status = $1, resolution_notes = $2,
               resolved_at = $3, updated_at = NOW() WHERE id = $4""",
            status, notes, resolved_at, ticket_id,
        )


# --- Knowledge Base Operations ---

async def search_knowledge_base(embedding: list, max_results: int = 5) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT title, content, category,
                      1 - (embedding <=> $1::vector) as similarity
               FROM knowledge_base
               WHERE embedding IS NOT NULL
               ORDER BY embedding <=> $1::vector
               LIMIT $2""",
            str(embedding), max_results,
        )
        return [dict(r) for r in rows]


async def search_knowledge_base_text(query: str, max_results: int = 5) -> list[dict]:
    """Fallback text-based search when embeddings are not available."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT title, content, category
               FROM knowledge_base
               WHERE LOWER(title) LIKE LOWER($1) OR LOWER(content) LIKE LOWER($1)
               LIMIT $2""",
            f"%{query}%", max_results,
        )
        return [dict(r) for r in rows]


# --- Customer History ---

async def get_customer_history(customer_id: str) -> list[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT c.initial_channel, c.started_at, c.status, c.sentiment_score,
                      m.content, m.role, m.channel, m.created_at as msg_time
               FROM conversations c
               JOIN messages m ON m.conversation_id = c.id
               WHERE c.customer_id = $1
               ORDER BY m.created_at DESC LIMIT 20""",
            customer_id,
        )
        return [dict(r) for r in rows]


# --- Metrics ---

async def record_metric(name: str, value: float, channel: str = None, dimensions: dict = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
               VALUES ($1, $2, $3, $4)""",
            name, value, channel, json.dumps(dimensions or {}),
        )


async def get_channel_metrics() -> dict:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT
                initial_channel as channel,
                COUNT(*) as total_conversations,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) FILTER (WHERE status = 'escalated') as escalations
               FROM conversations
               WHERE started_at > NOW() - INTERVAL '24 hours'
               GROUP BY initial_channel"""
        )
        return {row["channel"]: dict(row) for row in rows}
