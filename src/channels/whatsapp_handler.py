"""WhatsApp channel handler using Twilio API."""

import os

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from src.kafka_client import FTEKafkaProducer, TOPICS

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")


def get_twilio_client() -> Client:
    """Create and return a Twilio client."""
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def validate_twilio_request(url: str, params: dict, signature: str) -> bool:
    """Validate that a request is genuinely from Twilio."""
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    return validator.validate(url, params, signature)


async def process_whatsapp_message(form_data: dict, kafka_producer: FTEKafkaProducer):
    """Process an incoming WhatsApp message from Twilio webhook and publish to Kafka.

    Args:
        form_data: The form data from Twilio webhook POST.
        kafka_producer: Kafka producer instance.
    """
    sender = form_data.get("From", "")  # e.g., "whatsapp:+1234567890"
    body = form_data.get("Body", "")
    message_sid = form_data.get("MessageSid", "")
    profile_name = form_data.get("ProfileName", "")
    num_media = int(form_data.get("NumMedia", "0"))

    # Extract phone number from WhatsApp format
    phone = sender.replace("whatsapp:", "").strip()

    event = {
        "channel": "whatsapp",
        "customer_phone": phone,
        "customer_name": profile_name,
        "body": body,
        "message_sid": message_sid,
        "has_media": num_media > 0,
    }

    await kafka_producer.publish(TOPICS["whatsapp_inbound"], event)


def send_whatsapp_message(to_phone: str, message: str) -> str:
    """Send a WhatsApp message via Twilio.

    Args:
        to_phone: Recipient phone number (e.g., "+1234567890").
        message: The message text to send.

    Returns:
        The Twilio message SID.
    """
    client = get_twilio_client()

    twilio_message = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to_phone}",
    )

    return twilio_message.sid
