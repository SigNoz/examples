from fastapi import HTTPException
from agents import (
    Agent,
    OpenAIConversationsSession,
    Runner,
    WebSearchTool,
)

from app.config import NBA_INTERACTIVE_PROMPT, NBA_TOPIC_MAPPING, OPENAI_MODEL
from app.guardrails import nba_content_guardrail
from app.output_formatting import sanitize_agent_message
from app.prompts import build_nba_turn_prompt
from app.tools import calculate_win_percentage


NBA_AGENT = Agent(
    name="NBA_Reporter",
    instructions=NBA_INTERACTIVE_PROMPT,
    tools=[WebSearchTool(), calculate_win_percentage],
    input_guardrails=[nba_content_guardrail],
    model=OPENAI_MODEL,
)


def _validate_topic(topic: str) -> str:
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        supported_topics = ", ".join(sorted(NBA_TOPIC_MAPPING))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid NBA topic '{topic}'. Supported topics: {supported_topics}",
        )

    return nba_topic


def run_agent_turn(
    topic: str,
    user_message: str | None,
    session_id: str | None,
) -> dict:
    nba_topic = _validate_topic(topic)
    prompt = build_nba_turn_prompt(nba_topic, user_message)

    # if no session ID was given, the sdk internally creates a session_id during the turn
    # subsequent calls which pass the ID maintain the conversation context
    session = OpenAIConversationsSession(conversation_id=session_id)
    result = Runner.run_sync(NBA_AGENT, prompt, session=session)

    message = sanitize_agent_message((result.final_output or "").strip())
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI Agents SDK run did not produce any output text",
        )

    usage = None
    # attach usage context to the response for immediate feedback to the client,
    # as token usage tends to rise as conversations continue
    if getattr(result, "context_wrapper", None) is not None:
        context_usage = getattr(result.context_wrapper, "usage", None)
        if context_usage is not None:
            usage = {
                "input_tokens": getattr(context_usage, "input_tokens", 0),
                "output_tokens": getattr(context_usage, "output_tokens", 0),
                "total_tokens": getattr(context_usage, "total_tokens", 0),
            }

    return {
        "topic": topic,
        "session_id": session.session_id,
        "message": message,
        "model": OPENAI_MODEL,
        "usage": usage,
    }
