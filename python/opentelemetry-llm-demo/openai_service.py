from openai.types.responses.easy_input_message import EasyInputMessage
import sys
from agents import RunContextWrapper
from agents import TResponseInputItem
from prompts import build_nba_report_prompt
import uuid
from fastapi import HTTPException
from openai import OpenAI
from agents import (
    Agent,
    Runner,
    WebSearchTool,
    function_tool,
    input_guardrail,
    GuardrailFunctionOutput,
)

from config import NBA_SYSTEM_PROMPT, OPENAI_MODEL, NBA_INTERACTIVE_PROMPT
from cached_response import response_entry

# In-memory session database mapping session_id (str) -> list of messages (list)
SESSIONS: dict[str, EasyInputMessage] = {
    "3957422c-280f-418e-af49-a7104c08f73a": response_entry
}


# OpenTelemetry support for the Responses API is still evolving in the current
# released instrumentation, so the demo uses chat completions for the primary flow.
def run_openai_prompt(prompt: str) -> dict[str, object]:
    response = OpenAI().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": NBA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        top_p=0.98,
    )

    if not response.choices:
        raise HTTPException(
            status_code=502, detail="OpenAI SDK response did not include any choices"
        )

    message = (response.choices[0].message.content or "").strip()
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI SDK response did not include assistant message content",
        )

    usage = None
    if response.usage is not None:
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return {
        "message": message,
        "response_id": response.id,
        "model": response.model,
        "finish_reasons": [
            choice.finish_reason for choice in response.choices if choice.finish_reason
        ],
        "usage": usage,
    }


def run_openai_responses_prompt(prompt: str) -> dict[str, object]:
    response = OpenAI().responses.create(
        model=OPENAI_MODEL,
        instructions=NBA_SYSTEM_PROMPT,
        input=prompt,
        tools=[{"type": "web_search"}],
        include=["web_search_call.action.sources"],
        temperature=1,
        top_p=0.98,
    )

    message = response.output_text.strip()
    if not message:
        raise RuntimeError("OpenAI Responses API result did not include output text")

    usage = None
    if response.usage is not None:
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return {
        "message": message,
        "response_id": response.id,
        "model": response.model,
        "usage": usage,
    }


@function_tool
def calculate_win_percentage(wins: int, losses: int) -> str:
    """Calculates the winning percentage for an NBA team given their wins and losses.

    Args:
        wins: The number of games won.
        losses: The number of games lost.
    """

    total_games = wins + losses
    if total_games == 0:
        return "0.000"
    win_pct = wins / total_games
    return f"{win_pct:.3f}"


@input_guardrail()
def nba_content_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Ensures the user query is relevant to basketball/NBA."""

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
    ]

    # TODO: validate lists once sessions are sorted out
    if isinstance(input_data, list):
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=None)
    #     print(
    #         "received list input", len(input_data), input_data[-1], type(input_data[-1])
    #     )

    input_query = input_data if isinstance(input_data, str) else input_data[-1]

    input_query = input_query.lower()
    is_relevant = any(kw in input_query for kw in keywords)

    if len(input_query) < 5 or is_relevant:
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=None)

    return GuardrailFunctionOutput(
        tripwire_triggered=True,
        output_info={
            "reason": "The request is off-topic. Please ask questions relevant to NBA/basketball."
        },
    )


# Reusable single NBA Agent instance containing our tools and input guardrail
nba_agent = Agent(
    name="NBA_Reporter",
    instructions=NBA_INTERACTIVE_PROMPT,
    tools=[WebSearchTool(), calculate_win_percentage],
    input_guardrails=[nba_content_guardrail],
    model=OPENAI_MODEL,
)


def run_openai_agents_prompt(prompt: str) -> dict[str, object]:
    result = Runner.run_sync(nba_agent, prompt)

    message = (result.final_output or "").strip()
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI Agents SDK run did not produce any output text",
        )

    usage = None
    if getattr(result, "context_wrapper", None) is not None:
        cw_usage = getattr(result.context_wrapper, "usage", None)
        if cw_usage is not None:
            usage = {
                "input_tokens": getattr(cw_usage, "input_tokens", 0),
                "output_tokens": getattr(cw_usage, "output_tokens", 0),
                "total_tokens": getattr(cw_usage, "total_tokens", 0),
            }

    return {
        "message": message,
        "response_id": getattr(result, "id", None) or "agents_run_result",
        "model": OPENAI_MODEL,
        "usage": usage,
    }


def run_nba_report(nba_topic: str) -> dict[str, object]:
    report_prompt = build_nba_report_prompt(nba_topic)
    result = Runner.run_sync(nba_agent, report_prompt)

    message = (result.final_output or "").strip()
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI Agents SDK failed to generate the report",
        )

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = result.to_input_list()
    print("SAVED SESSION!!")
    print(SESSIONS[session_id])

    usage = None
    if getattr(result, "context_wrapper", None) is not None:
        cw_usage = getattr(result.context_wrapper, "usage", None)
        if cw_usage is not None:
            usage = {
                "input_tokens": getattr(cw_usage, "input_tokens", 0),
                "output_tokens": getattr(cw_usage, "output_tokens", 0),
                "total_tokens": getattr(cw_usage, "total_tokens", 0),
            }

    return {
        "session_id": session_id,
        "message": message,
        "model": OPENAI_MODEL,
        "usage": usage,
    }


def run_nba_chat(session_id: str, user_message: str) -> dict[str, object]:
    if session_id not in SESSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found. Please generate a report first to start a conversation.",
        )

    history = SESSIONS[session_id]
    updated_history = history + [{"role": "user", "content": user_message}]

    result = Runner.run_sync(nba_agent, updated_history)

    message = (result.final_output or "").strip()
    if not message:
        raise HTTPException(
            status_code=502,
            detail="OpenAI Agents SDK failed to generate a chat response",
        )

    # TODO: use final_output_as here to convert it into pydantic model
    SESSIONS[session_id] = result.to_input_list()

    usage = None
    if getattr(result, "context_wrapper", None) is not None:
        cw_usage = getattr(result.context_wrapper, "usage", None)
        if cw_usage is not None:
            usage = {
                "input_tokens": getattr(cw_usage, "input_tokens", 0),
                "output_tokens": getattr(cw_usage, "output_tokens", 0),
                "total_tokens": getattr(cw_usage, "total_tokens", 0),
            }

    return {
        "message": message,
        "model": OPENAI_MODEL,
        "usage": usage,
    }
