from fastapi import HTTPException
from agents import (
    Agent,
    OpenAIConversationsSession,
    Runner,
    WebSearchTool,
)

from app.config import NBA_INTERACTIVE_PROMPT, NBA_TOPIC_MAPPING, OPENAI_MODEL
from app.guardrails import nba_content_guardrail
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


def _resolve_session_id(session: OpenAIConversationsSession) -> str:
    # the conversation session is lazily-created, so the ID gets generated
    # after the runner has interacted with the session during a turn
    return session.session_id


def run_agent_turn(
    topic: str,
    user_message: str | None,
    session_id: str | None,
) -> dict:
    nba_topic = _validate_topic(topic)
    prompt = build_nba_turn_prompt(nba_topic, user_message)

    session = OpenAIConversationsSession(conversation_id=session_id)
    result = Runner.run_sync(NBA_AGENT, prompt, session=session)

    message = (result.final_output or "").strip()
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI Agents SDK run did not produce any output text",
        )

    usage = None
    # attach usage context to the response
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
        "session_id": _resolve_session_id(session),
        "message": message,
        "model": OPENAI_MODEL,
        "usage": usage,
    }
