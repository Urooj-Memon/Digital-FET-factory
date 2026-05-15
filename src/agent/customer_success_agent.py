"""Customer Success FTE Agent built with OpenAI Agents SDK."""

import os
from agents import Agent, Runner, ModelSettings

from src.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from src.agent.tools import ALL_TOOLS


def create_customer_success_agent(
    customer_id: str = "",
    conversation_id: str = "",
    channel: str = "web_form",
    ticket_subject: str = "",
) -> Agent:
    """Create and configure the Customer Success FTE agent.

    Args:
        customer_id: The unique customer identifier.
        conversation_id: The current conversation thread ID.
        channel: The channel (email, whatsapp, web_form).
        ticket_subject: The original subject/topic.

    Returns:
        Configured Agent instance ready to run.
    """
    # Inject context variables into the system prompt
    prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT.replace("{{customer_id}}", customer_id)
    prompt = prompt.replace("{{conversation_id}}", conversation_id)
    prompt = prompt.replace("{{channel}}", channel)
    prompt = prompt.replace("{{ticket_subject}}", ticket_subject)

    agent = Agent(
        name="Customer Success FTE",
        instructions=prompt,
        tools=ALL_TOOLS,
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        model_settings=ModelSettings(
            temperature=0.3,
            top_p=0.9,
        ),
    )

    return agent


async def run_agent(
    message: str,
    customer_id: str = "",
    conversation_id: str = "",
    channel: str = "web_form",
    ticket_subject: str = "",
    conversation_history: list = None,
) -> str:
    """Run the Customer Success agent on a customer message.

    Args:
        message: The customer's message.
        customer_id: The unique customer identifier.
        conversation_id: The current conversation thread ID.
        channel: The channel (email, whatsapp, web_form).
        ticket_subject: The original subject/topic.
        conversation_history: Prior conversation messages for context.

    Returns:
        The agent's final response text.
    """
    agent = create_customer_success_agent(
        customer_id=customer_id,
        conversation_id=conversation_id,
        channel=channel,
        ticket_subject=ticket_subject,
    )

    # Build input messages with history if available
    input_messages = []
    if conversation_history:
        input_messages.extend(conversation_history)

    input_messages.append({"role": "user", "content": message})

    result = await Runner.run(agent, input_messages)

    return result.final_output
