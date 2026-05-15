"""Tests for the Customer Success FTE agent and tools."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agent.formatters import (
    format_for_email,
    format_for_whatsapp,
    format_for_web,
    format_response,
)
from src.agent.customer_success_agent import create_customer_success_agent


# --- Formatter Tests ---


class TestFormatForEmail:
    def test_includes_greeting(self):
        result = format_for_email("Your issue is resolved.", ticket_id="T-123", customer_name="Alice")
        assert "Dear Alice" in result

    def test_includes_ticket_reference(self):
        result = format_for_email("Fixed.", ticket_id="T-456")
        assert "T-456" in result

    def test_includes_signature(self):
        result = format_for_email("Done.")
        assert "TechCorp AI Support Team" in result

    def test_default_customer_name(self):
        result = format_for_email("Hello.")
        assert "Dear Customer" in result


class TestFormatForWhatsapp:
    def test_short_message_unchanged(self):
        msg = "Your password has been reset."
        result = format_for_whatsapp(msg)
        assert msg in result
        assert "Reply for more help" in result

    def test_long_message_truncated(self):
        long_msg = "A" * 400
        result = format_for_whatsapp(long_msg)
        # The response part should be truncated to 297 + "..."
        assert "..." in result
        assert len(result.split("\n")[0]) <= 300


class TestFormatForWeb:
    def test_includes_help_footer(self):
        result = format_for_web("Here's the answer.")
        assert "support portal" in result


class TestFormatResponse:
    def test_routes_email(self):
        result = format_response("Test", "email", customer_name="Bob", ticket_id="T-1")
        assert "Dear Bob" in result

    def test_routes_whatsapp(self):
        result = format_response("Test", "whatsapp")
        assert "Reply for more help" in result

    def test_routes_web_default(self):
        result = format_response("Test", "web_form")
        assert "support portal" in result

    def test_unknown_channel_defaults_to_web(self):
        result = format_response("Test", "unknown")
        assert "support portal" in result


# --- Agent Creation Tests ---


class TestCreateAgent:
    def test_agent_has_correct_name(self):
        agent = create_customer_success_agent()
        assert agent.name == "Customer Success FTE"

    def test_agent_has_tools(self):
        agent = create_customer_success_agent()
        assert len(agent.tools) == 5

    def test_context_variables_injected(self):
        agent = create_customer_success_agent(
            customer_id="C-123",
            conversation_id="CONV-456",
            channel="email",
            ticket_subject="Login issue",
        )
        assert "C-123" in agent.instructions
        assert "CONV-456" in agent.instructions
        assert "email" in agent.instructions
        assert "Login issue" in agent.instructions


# --- Tool Tests (with mocked DB) ---


class TestCreateTicketTool:
    @pytest.mark.asyncio
    @patch("src.agent.tools.create_ticket_record", new_callable=AsyncMock)
    @patch("src.agent.tools.record_metric", new_callable=AsyncMock)
    async def test_creates_ticket_successfully(self, mock_metric, mock_create):
        from src.agent.tools import create_ticket, CreateTicketInput

        mock_create.return_value = "T-001"

        input_data = CreateTicketInput(
            customer_id="C-1",
            subject="Cannot login",
            category="technical",
            priority="high",
            channel="email",
        )

        result = await create_ticket.on_invoke_tool(
            MagicMock(), json.dumps(input_data.model_dump())
        )
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["ticket_id"] == "T-001"


class TestSearchKnowledgeBaseTool:
    @pytest.mark.asyncio
    @patch("src.agent.tools.search_knowledge_base_text", new_callable=AsyncMock)
    async def test_returns_results(self, mock_search):
        from src.agent.tools import search_knowledge_base, SearchKnowledgeBaseInput

        mock_search.return_value = [
            {"title": "Password Reset", "content": "Go to Settings > Security", "category": "account"}
        ]

        input_data = SearchKnowledgeBaseInput(query="password reset")
        result = await search_knowledge_base.on_invoke_tool(
            MagicMock(), json.dumps(input_data.model_dump())
        )
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["results_count"] == 1

    @pytest.mark.asyncio
    @patch("src.agent.tools.search_knowledge_base_text", new_callable=AsyncMock)
    async def test_no_results(self, mock_search):
        from src.agent.tools import search_knowledge_base, SearchKnowledgeBaseInput

        mock_search.return_value = []

        input_data = SearchKnowledgeBaseInput(query="nonexistent topic")
        result = await search_knowledge_base.on_invoke_tool(
            MagicMock(), json.dumps(input_data.model_dump())
        )
        data = json.loads(result)
        assert data["status"] == "no_results"


class TestEscalateToHumanTool:
    @pytest.mark.asyncio
    @patch("src.agent.tools.update_ticket_status", new_callable=AsyncMock)
    @patch("src.agent.tools.record_metric", new_callable=AsyncMock)
    async def test_escalation(self, mock_metric, mock_update):
        from src.agent.tools import escalate_to_human, EscalateToHumanInput

        input_data = EscalateToHumanInput(
            ticket_id="T-1",
            reason="pricing_inquiry",
            summary="Customer asked about enterprise pricing",
            channel="email",
        )

        result = await escalate_to_human.on_invoke_tool(
            MagicMock(), json.dumps(input_data.model_dump())
        )
        data = json.loads(result)
        assert data["status"] == "escalated"
        mock_update.assert_called_once()
