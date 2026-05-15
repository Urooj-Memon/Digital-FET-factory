"""Unified message processor - Kafka consumer that routes messages to the AI agent."""

import json
import logging
import time

from src.kafka_client import FTEKafkaConsumer, FTEKafkaProducer, TOPICS
from src.database.queries import (
    resolve_customer,
    get_or_create_conversation,
    store_message,
    load_conversation_history,
    record_metric,
)
from src.agent.customer_success_agent import run_agent
from src.channels.gmail_handler import send_email_reply
from src.channels.whatsapp_handler import send_whatsapp_message

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Consumes messages from all channel topics and processes them via the AI agent."""

    def __init__(self):
        self.consumer = FTEKafkaConsumer(
            topics=[
                TOPICS["email_inbound"],
                TOPICS["whatsapp_inbound"],
                TOPICS["webform_inbound"],
            ],
            group_id="fte-message-processor",
        )
        self.producer = FTEKafkaProducer()

    async def start(self):
        """Start the message processor."""
        await self.producer.start()
        await self.consumer.start()
        logger.info("Message processor started - listening on all channel topics")
        await self.consumer.consume(self.handle_message)

    async def stop(self):
        """Stop the message processor."""
        await self.consumer.stop()
        await self.producer.stop()
        logger.info("Message processor stopped")

    async def handle_message(self, topic: str, message: dict):
        """Route incoming message to the appropriate processing pipeline."""
        start_time = time.time()
        channel = message.get("channel", "unknown")

        try:
            logger.info(f"Processing {channel} message from topic {topic}")

            # Step 1: Resolve or create customer
            customer_id = await resolve_customer(message)

            # Step 2: Get or create conversation
            conversation_id = await get_or_create_conversation(customer_id, channel)

            # Step 3: Store inbound message
            body = message.get("body", "")
            await store_message(
                conversation_id=conversation_id,
                channel=channel,
                direction="inbound",
                role="customer",
                content=body,
                channel_message_id=message.get("message_id") or message.get("message_sid"),
            )

            # Step 4: Load conversation history for context
            history = await load_conversation_history(conversation_id)

            # Step 5: Run AI agent
            subject = message.get("subject", "Support Request")
            agent_response = await run_agent(
                message=body,
                customer_id=customer_id,
                conversation_id=conversation_id,
                channel=channel,
                ticket_subject=subject,
                conversation_history=history,
            )

            # Step 6: Deliver response via channel
            await self._deliver_response(channel, message, agent_response)

            # Step 7: Record metrics
            processing_time = (time.time() - start_time) * 1000
            await record_metric(
                "message_processed", 1.0, channel=channel,
                dimensions={"processing_time_ms": processing_time},
            )
            logger.info(f"Processed {channel} message in {processing_time:.0f}ms")

        except Exception as e:
            logger.error(f"Error processing {channel} message: {e}")
            # Publish to dead letter queue
            await self.producer.publish(
                TOPICS["dlq"],
                {
                    "original_topic": topic,
                    "original_message": message,
                    "error": str(e),
                    "channel": channel,
                },
            )
            await record_metric(
                "message_error", 1.0, channel=channel,
                dimensions={"error": str(e)[:200]},
            )

    async def _deliver_response(self, channel: str, original_message: dict, response: str):
        """Deliver the agent's response back through the appropriate channel."""
        if channel == "email":
            send_email_reply(
                to=original_message.get("customer_email", ""),
                subject=original_message.get("subject", "Support"),
                body=response,
                thread_id=original_message.get("thread_id"),
            )
            await self.producer.publish(
                TOPICS["email_outbound"],
                {"to": original_message.get("customer_email"), "response": response},
            )

        elif channel == "whatsapp":
            phone = original_message.get("customer_phone", "")
            if phone:
                sid = send_whatsapp_message(phone, response)
                await self.producer.publish(
                    TOPICS["whatsapp_outbound"],
                    {"to": phone, "response": response, "message_sid": sid},
                )

        elif channel == "web_form":
            # Web form responses are stored in DB; frontend polls for updates
            logger.info("Web form response stored in database for frontend polling")


async def run_message_processor():
    """Entry point for the message processor worker."""
    processor = MessageProcessor()
    try:
        await processor.start()
    except KeyboardInterrupt:
        await processor.stop()
