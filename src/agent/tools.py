"""Tool definitions for the Customer Success FTE agent using OpenAI Agents SDK."""

import os
import json
from datetime import datetime
from pydantic import BaseModel, Field

from agents import function_tool

from src.database.queries import (
    create_ticket_record,
    get_customer_history as db_get_customer_history,
    search_knowledge_base_text,
    update_ticket_status,
    store_message,
    record_metric,
)
from src.agent.formatters import format_response


# --- Pydantic Input Models ---


class CreateTicketInput(BaseModel):
    customer_id: str = Field(description="The unique customer identifier")
    subject: str = Field(description="Brief subject line for the ticket")
    category: str = Field(
        description="Ticket category: technical, billing, account, feedback, or general"
    )
    priority: str = Field(
        default="medium",
        description="Ticket priority: low, medium, high, or urgent",
    )
    channel: str = Field(description="Source channel: email, whatsapp, or web_form")


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(description="Search query for the knowledge base")
    max_results: int = Field(
        default=3, description="Maximum number of results to return"
    )


class GetCustomerHistoryInput(BaseModel):
    customer_id: str = Field(description="The unique customer identifier")


class EscalateToHumanInput(BaseModel):
    ticket_id: str = Field(description="The ticket ID to escalate")
    reason: str = Field(
        description="Reason for escalation: pricing_inquiry, refund_request, legal_threat, angry_customer, technical_emergency, customer_request, or unresolved"
    )
    summary: str = Field(
        description="Brief summary of the issue and what has been attempted"
    )
    channel: str = Field(description="Current channel: email, whatsapp, or web_form")


class SendResponseInput(BaseModel):
    ticket_id: str = Field(description="The associated ticket ID")
    conversation_id: str = Field(description="The conversation ID")
    response: str = Field(description="The response content to send to the customer")
    channel: str = Field(description="Channel to respond on: email, whatsapp, or web_form")
    customer_name: str = Field(default="Customer", description="Customer name for personalization")


# --- Tool Definitions ---


@function_tool
async def create_ticket(input: CreateTicketInput) -> str:
    """Create a new support ticket to log the customer interaction. ALWAYS call this first before any other action."""
    try:
        ticket_id = await create_ticket_record(
            customer_id=input.customer_id,
            source_channel=input.channel,
            subject=input.subject,
            category=input.category,
            priority=input.priority,
        )

        await record_metric(
            "ticket_created", 1.0, channel=input.channel,
            dimensions={"category": input.category, "priority": input.priority},
        )

        return json.dumps({
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Ticket {ticket_id} created successfully for {input.subject}",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@function_tool
async def search_knowledge_base(input: SearchKnowledgeBaseInput) -> str:
    """Search the product knowledge base for relevant information to answer customer questions."""
    try:
        results = await search_knowledge_base_text(
            query=input.query, max_results=input.max_results
        )

        if not results:
            return json.dumps({
                "status": "no_results",
                "message": "No matching articles found. Consider rephrasing the search or escalating if this is the second failed attempt.",
            })

        articles = []
        for r in results:
            articles.append({
                "title": r["title"],
                "content": r["content"],
                "category": r.get("category", "general"),
            })

        return json.dumps({
            "status": "success",
            "results_count": len(articles),
            "articles": articles,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@function_tool
async def get_customer_history(input: GetCustomerHistoryInput) -> str:
    """Retrieve the customer's interaction history across all channels. Call this after creating a ticket to check for prior context."""
    try:
        history = await db_get_customer_history(input.customer_id)

        if not history:
            return json.dumps({
                "status": "success",
                "has_history": False,
                "message": "No previous interactions found. This appears to be a new customer.",
            })

        interactions = []
        for h in history:
            interactions.append({
                "channel": h.get("channel", "unknown"),
                "role": h.get("role", "unknown"),
                "content": h.get("content", "")[:200],
                "timestamp": str(h.get("msg_time", "")),
                "sentiment": h.get("sentiment_score"),
            })

        return json.dumps({
            "status": "success",
            "has_history": True,
            "interaction_count": len(interactions),
            "interactions": interactions,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@function_tool
async def escalate_to_human(input: EscalateToHumanInput) -> str:
    """Escalate a ticket to a human agent. Use when escalation triggers are detected."""
    try:
        await update_ticket_status(
            ticket_id=input.ticket_id,
            status="escalated",
            notes=f"Escalated by AI agent. Reason: {input.reason}. Summary: {input.summary}",
        )

        await record_metric(
            "escalation", 1.0, channel=input.channel,
            dimensions={"reason": input.reason},
        )

        channel_messages = {
            "email": "I've escalated your case to our support team. A human agent will follow up via email within 2 hours.",
            "whatsapp": "Connecting you with a human agent. You'll hear back shortly.",
            "web_form": "Your case has been escalated to our support team. A human agent will reach out within 2 hours.",
        }

        return json.dumps({
            "status": "escalated",
            "ticket_id": input.ticket_id,
            "reason": input.reason,
            "message": channel_messages.get(input.channel, channel_messages["web_form"]),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@function_tool
async def send_response(input: SendResponseInput) -> str:
    """Send a formatted response to the customer. ALWAYS call this as the final action - never respond without this tool."""
    try:
        formatted = format_response(
            response=input.response,
            channel=input.channel,
            ticket_id=input.ticket_id,
            customer_name=input.customer_name,
        )

        start_time = datetime.utcnow()

        await store_message(
            conversation_id=input.conversation_id,
            channel=input.channel,
            direction="outbound",
            role="agent",
            content=formatted,
        )

        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        await record_metric(
            "response_sent", 1.0, channel=input.channel,
            dimensions={"latency_ms": latency},
        )

        return json.dumps({
            "status": "sent",
            "ticket_id": input.ticket_id,
            "channel": input.channel,
            "formatted_response": formatted,
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# All tools list for agent registration
ALL_TOOLS = [
    create_ticket,
    search_knowledge_base,
    get_customer_history,
    escalate_to_human,
    send_response,
]
