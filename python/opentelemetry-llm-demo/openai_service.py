from fastapi import HTTPException
from openai import OpenAI

from config import NBA_SYSTEM_PROMPT, OPENAI_MODEL


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
