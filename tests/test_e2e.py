"""End-to-end tests for the Customer Success FTE system."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.fixture
def mock_db():
    """Mock database operations for e2e tests."""
    with patch("src.api.main.get_db_pool") as mock_pool:
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 1
        mock_pool.return_value = AsyncMock()
        mock_pool.return_value.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.return_value.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_pool


@pytest.fixture
def mock_kafka():
    """Mock Kafka producer."""
    with patch("src.api.main.kafka_producer") as mock:
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock.publish = AsyncMock()
        yield mock


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, mock_db):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestWebFormEndpoint:
    @pytest.mark.asyncio
    async def test_submit_valid_form(self, mock_db, mock_kafka):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/support/submit",
                json={
                    "name": "Test User",
                    "email": "test@example.com",
                    "subject": "Cannot access dashboard",
                    "category": "technical",
                    "priority": "high",
                    "message": "I cannot access my dashboard since yesterday. Getting a 403 error.",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"

    @pytest.mark.asyncio
    async def test_submit_invalid_email(self, mock_db, mock_kafka):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/support/submit",
                json={
                    "name": "Test",
                    "email": "invalid",
                    "subject": "Test",
                    "category": "general",
                    "priority": "low",
                    "message": "This should fail validation.",
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_missing_fields(self, mock_db, mock_kafka):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/support/submit",
                json={"name": "Test"},
            )
            assert response.status_code == 422


class TestTicketEndpoint:
    @pytest.mark.asyncio
    async def test_ticket_not_found(self, mock_db):
        with patch("src.api.main.get_ticket_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/support/ticket/nonexistent")
                assert response.status_code == 404


class TestWhatsAppWebhook:
    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self, mock_db, mock_kafka):
        with patch("src.api.main.validate_twilio_request", return_value=False):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/webhooks/whatsapp",
                    data={"From": "whatsapp:+1234567890", "Body": "hello"},
                    headers={"X-Twilio-Signature": "bad_sig"},
                )
                assert response.status_code == 403
