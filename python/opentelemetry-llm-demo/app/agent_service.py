from fastapi import HTTPException
from agents import (
    Agent,
    Runner,
    WebSearchTool,
)

from app.config import NBA_INTERACTIVE_PROMPT, NBA_TOPIC_MAPPING, OPENAI_MODEL
from app.guardrails import nba_content_guardrail
from app.prompts import build_nba_turn_prompt
from app.tools import calculate_win_percentage


def validate_topic(topic: str) -> str:
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        supported_topics = ", ".join(sorted(NBA_TOPIC_MAPPING))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid NBA topic '{topic}'. Supported topics: {supported_topics}",
        )

    return nba_topic


NBA_AGENT = Agent(
    name="NBA_Reporter",
    instructions=NBA_INTERACTIVE_PROMPT,
    tools=[WebSearchTool(), calculate_win_percentage],
    input_guardrails=[nba_content_guardrail],
    model=OPENAI_MODEL,
)


def run_agent_turn(topic: str, user_message: str | None) -> dict:
    nba_topic = validate_topic(topic)
    prompt = build_nba_turn_prompt(nba_topic, user_message)
    result = Runner.run_sync(NBA_AGENT, prompt)

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
        "session_id": None,
        "message": message,
        "model": OPENAI_MODEL,
        "usage": usage,
    }
