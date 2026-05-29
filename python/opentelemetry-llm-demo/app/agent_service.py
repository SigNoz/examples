from fastapi import HTTPException
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    WebSearchTool,
    function_tool,
    input_guardrail,
)

from app.config import NBA_INTERACTIVE_PROMPT, NBA_TOPIC_MAPPING, OPENAI_MODEL
from app.prompts import build_nba_turn_prompt


@function_tool
def calculate_win_percentage(wins: int, losses: int) -> str:
    """Calculates the winning percentage for an NBA team given their wins and losses."""

    total_games = wins + losses
    if total_games == 0:
        return "0.000"

    return f"{wins / total_games:.3f}"


@input_guardrail()
def nba_content_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Ensures the user query is relevant to basketball/NBA."""

    del context, agent

    keywords = [
        "nba",
        "basketball",
        "player",
        "team",
        "finals",
        "playoff",
        "standing",
        "court",
        "wins",
        "losses",
        "score",
        "game",
        "championship",
        "conference",
        "mvp",
        "report",
        "news",
        "cavs",
        "knicks",
        "thunder",
        "spurs",
    ]

    if isinstance(input_data, list):
        # find the last user message in the input data
        latest_user_message = next(
            (
                item.get("content", "")
                for item in reversed(input_data)
                if isinstance(item, dict) and item.get("role") == "user"
            ),
            "",
        )
        input_query = latest_user_message
    else:
        input_query = input_data

    input_query = input_query.lower()
    is_relevant = any(keyword in input_query for keyword in keywords)

    if len(input_query) < 5 or is_relevant:
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=None)

    return GuardrailFunctionOutput(
        tripwire_triggered=True,
        output_info={
            "reason": "The request is off-topic. Please ask questions relevant to NBA or basketball."
        },
    )


def validate_topic(topic: str) -> str:
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        supported_topics = ", ".join(sorted(NBA_TOPIC_MAPPING))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid NBA topic '{topic}'. Supported topics: {supported_topics}",
        )

    return nba_topic


# TODO: check if above functions should be moved to a dedicated module
NBA_AGENT = Agent(
    name="NBA_Reporter",
    instructions=NBA_INTERACTIVE_PROMPT,
    tools=[WebSearchTool(), calculate_win_percentage],
    input_guardrails=[nba_content_guardrail],
    model=OPENAI_MODEL,
)


def run_agent_turn(topic: str, user_message: str | None) -> dict[str, object]:
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
