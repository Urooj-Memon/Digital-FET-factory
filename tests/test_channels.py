"""Tests for channel handlers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.channels.web_form_handler import WebFormSubmission, handle_web_form_submission
from src.channels.whatsapp_handler import validate_twilio_request


class TestWebFormHandler:
    def test_valid_submission(self):
        submission = WebFormSubmission(
            name="John Doe",
            email="john@example.com",
            subject="Cannot login to my account",
            category="technical",
            priority="high",
            message="I've been trying to login but keep getting an error message.",
        )
        assert submission.name == "John Doe"
        assert submission.email == "john@example.com"
        assert submission.category == "technical"

    def test_invalid_email_rejected(self):
        with pytest.raises(Exception):
            WebFormSubmission(
                name="Jane",
                email="not-an-email",
                subject="Test",
                category="general",
                priority="low",
                message="This is a test message for validation.",
            )

    def test_short_message_rejected(self):
        with pytest.raises(Exception):
            WebFormSubmission(
                name="Jane",
                email="jane@example.com",
                subject="Test",
                category="general",
                priority="low",
                message="Short",
            )

    def test_default_category_and_priority(self):
        submission = WebFormSubmission(
            name="Test User",
            email="test@example.com",
            subject="General question",
            message="I have a general question about TechFlow features.",
        )
        assert submission.category == "general"
        assert submission.priority == "medium"

    @pytest.mark.asyncio
    async def test_handle_submission_publishes_to_kafka(self):
        mock_producer = AsyncMock()
        submission = WebFormSubmission(
            name="Alice",
            email="alice@example.com",
            subject="Feature question",
            category="feedback",
            priority="low",
            message="Does TechFlow support Jira integration?",
        )

        result = await handle_web_form_submission(submission, mock_producer)
        assert result["status"] == "received"
        mock_producer.publish.assert_called_once()


class TestWhatsAppHandler:
    @patch("src.channels.whatsapp_handler.TWILIO_AUTH_TOKEN", "test_token")
    def test_validate_request_with_bad_signature(self):
        result = validate_twilio_request(
            url="https://example.com/webhook",
            params={"Body": "hello"},
            signature="invalid_signature",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_process_whatsapp_message(self):
        from src.channels.whatsapp_handler import process_whatsapp_message

        mock_producer = AsyncMock()
        form_data = {
            "From": "whatsapp:+1234567890",
            "Body": "I need help with my account",
            "MessageSid": "SM123",
            "ProfileName": "John",
            "NumMedia": "0",
        }

        await process_whatsapp_message(form_data, mock_producer)
        mock_producer.publish.assert_called_once()

        call_args = mock_producer.publish.call_args
        event = call_args[0][1]
        assert event["channel"] == "whatsapp"
        assert event["customer_phone"] == "+1234567890"
        assert event["body"] == "I need help with my account"
