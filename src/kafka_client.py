"""Kafka producer and consumer for multi-channel event streaming."""

import json
import os
from datetime import datetime

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Topic definitions for multi-channel FTE
TOPICS = {
    # Incoming tickets from all channels (unified queue)
    "tickets_incoming": "fte.tickets.incoming",
    # Channel-specific inbound
    "email_inbound": "fte.channels.email.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    # Channel-specific outbound
    "email_outbound": "fte.channels.email.outbound",
    "whatsapp_outbound": "fte.channels.whatsapp.outbound",
    # Escalations
    "escalations": "fte.escalations",
    # Metrics and monitoring
    "metrics": "fte.metrics",
    # Dead letter queue for failed processing
    "dlq": "fte.dlq",
}


class FTEKafkaProducer:
    """Kafka producer for publishing FTE events."""

    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, event: dict):
        """Publish an event to a Kafka topic.
        If the producer is not started (e.g., Kafka unavailable), the event is dropped and a warning is logged.
        """
        if self.producer is None:
            logging.getLogger(__name__).warning("Kafka producer not started – event dropped for topic %s", topic)
            return
        event["timestamp"] = datetime.utcnow().isoformat()
        await self.producer.send_and_wait(topic, event)


class FTEKafkaConsumer:
    """Kafka consumer for processing FTE events."""

    def __init__(self, topics: list, group_id: str):
        self.topics = topics
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self, handler):
        """Consume messages and pass to handler function."""
        async for msg in self.consumer:
            await handler(msg.topic, msg.value)
