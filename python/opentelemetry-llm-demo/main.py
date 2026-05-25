import datetime as dt

from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI

load_dotenv()


OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
NBA_REPORTER_PROMPT = "You're an NBA news reporter that gives the user the latest news and analysis on the NBA."

NBA_TOPIC_MAPPING = {
    "eastern": "Eastern Conference",
    "western": "Western Conference",
    "finals": "Finals",
    "general": "Season",
}

openai_client = OpenAI()

app = FastAPI()


def build_nba_prompt(nba_topic: str) -> str:
    return f"What is the latest news and analysis for NBA {nba_topic}, as of {dt.date.today()}?"


# OpenTelemetry support for the Responses API is under active development, to instrument LLM calls utilize the chat-completions API
def run_openai_prompt(prompt: str) -> dict[str, object]:
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    NBA_REPORTER_PROMPT + " "
                    "Use web search to verify current facts before answering questions about recent news, "
                    "standings, or playoff state."
                ),
            },
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


@app.get("/openai_nba")
def news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    return run_openai_prompt(build_nba_prompt(nba_topic))


@app.get("/")
def index():
    return {"message": "OpenAI NBA News Reporter API is running"}
