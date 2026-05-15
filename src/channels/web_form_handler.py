"""Web form channel handler - FastAPI endpoints for the Next.js support form."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from src.kafka_client import FTEKafkaProducer, TOPICS


class WebFormSubmission(BaseModel):
    """Schema for incoming web form support requests."""
    name: str = Field(..., min_length=1, max_length=200, description="Customer full name")
    email: EmailStr = Field(..., description="Customer email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Issue subject")
    category: str = Field(
        default="general",
        description="Issue category: technical, billing, account, feedback, general",
    )
    priority: str = Field(
        default="medium",
        description="Issue priority: low, medium, high, urgent",
    )
    message: str = Field(..., min_length=10, max_length=5000, description="Detailed message")


class TicketStatusRequest(BaseModel):
    """Schema for checking ticket status."""
    ticket_id: str = Field(..., description="The ticket ID to check")
    email: str = Field(..., description="Customer email for verification")


async def handle_web_form_submission(
    submission: WebFormSubmission, kafka_producer: FTEKafkaProducer
) -> dict:
    """Process a web form submission and publish to Kafka.

    Args:
        submission: Validated web form data.
        kafka_producer: Kafka producer instance.

    Returns:
        Acknowledgment with tracking info.
    """
    event = {
        "channel": "web_form",
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "category": submission.category,
        "priority": submission.priority,
        "body": submission.message,
    }

    await kafka_producer.publish(TOPICS["webform_inbound"], event)

    return {
        "status": "received",
        "message": "Your support request has been received. We'll get back to you shortly.",
    }
