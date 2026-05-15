"""Background metrics collector for FTE performance monitoring."""

import asyncio
import logging
from datetime import datetime

from src.database.queries import get_channel_metrics, record_metric, get_db_pool

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL = 60  # seconds


async def collect_channel_metrics():
    """Collect and store per-channel metrics."""
    try:
        metrics = await get_channel_metrics()
        for channel, data in metrics.items():
            await record_metric(
                "channel_summary",
                float(data.get("total_conversations", 0)),
                channel=channel,
                dimensions={
                    "avg_sentiment": float(data.get("avg_sentiment") or 0),
                    "escalations": int(data.get("escalations", 0)),
                },
            )
        logger.debug(f"Collected metrics for {len(metrics)} channels")
    except Exception as e:
        logger.error(f"Error collecting channel metrics: {e}")


async def collect_response_time_metrics():
    """Collect average response time metrics."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT
                    AVG(latency_ms) as avg_latency,
                    MAX(latency_ms) as max_latency,
                    COUNT(*) as total_messages
                   FROM messages
                   WHERE direction = 'outbound'
                   AND created_at > NOW() - INTERVAL '1 hour'"""
            )
            if row and row["avg_latency"]:
                await record_metric(
                    "avg_response_time_ms",
                    float(row["avg_latency"]),
                    dimensions={
                        "max_latency_ms": float(row["max_latency"] or 0),
                        "total_messages": int(row["total_messages"]),
                    },
                )
    except Exception as e:
        logger.error(f"Error collecting response time metrics: {e}")


async def collect_ticket_metrics():
    """Collect ticket status distribution metrics."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT status, source_channel, COUNT(*) as count
                   FROM tickets
                   WHERE created_at > NOW() - INTERVAL '24 hours'
                   GROUP BY status, source_channel"""
            )
            for row in rows:
                await record_metric(
                    "ticket_status_count",
                    float(row["count"]),
                    channel=row["source_channel"],
                    dimensions={"status": row["status"]},
                )
    except Exception as e:
        logger.error(f"Error collecting ticket metrics: {e}")


async def run_metrics_collector():
    """Main loop for the metrics collector worker."""
    logger.info("Metrics collector started")
    while True:
        await collect_channel_metrics()
        await collect_response_time_metrics()
        await collect_ticket_metrics()
        await asyncio.sleep(COLLECTION_INTERVAL)
