import datetime as dt

from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from agents import Agent, Runner, WebSearchTool, ModelSettings
from claude_agent_sdk import ClaudeAgentOptions, query as claude_query
from claude_agent_sdk.types import ResultMessage

load_dotenv()


OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
CLAUDE_MODEL = "claude-4.5-haiku-20260929"
NBA_REPORTER_PROMPT = "You're an NBA news reporter that gives the user the latest news and analysis on the NBA."

NBA_TOPIC_MAPPING = {
    "eastern": "Eastern Conference",
    "western": "Western Conference",
    "finals": "Finals",
    "general": "Season",
}

openai_agent = Agent(
    name="NBA News Reporter v2",
    instructions=(
        NBA_REPORTER_PROMPT + " "
        "Use web search to verify current facts before answering questions about recent news, "
        "standings, or playoff state."
    ),
    model=OPENAI_MODEL,
    tools=[WebSearchTool(external_web_access=True)],
    model_settings=ModelSettings(include_usage=True),
)
openai_client = OpenAI()
claude_options = ClaudeAgentOptions(
    model=CLAUDE_MODEL,
    system_prompt=NBA_REPORTER_PROMPT,
    permission_mode="bypassPermissions",
)

app = FastAPI()


def build_nba_prompt(nba_topic: str) -> str:
    return f"What is the latest news and analysis for NBA {nba_topic}, as of {dt.date.today()}?"


def run_openai_sdk_prompt(prompt: str) -> dict[str, object]:
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            NBA_REPORTER_PROMPT + " "
            "Use web search to verify current facts before answering questions about recent news, "
            "standings, or playoff state."
        ),
        input=prompt,
        tools=[{"type": "web_search"}],
        include=["web_search_call.action.sources"],
        temperature=1,
        top_p=0.98,
    )
    message = response.output_text.strip()
    if not message:
        raise HTTPException(
            status_code=502, detail="OpenAI SDK response did not include output text"
        )

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


async def run_claude_prompt(prompt: str) -> str:
    async for message in claude_query(prompt=prompt, options=claude_options):
        if isinstance(message, ResultMessage):
            if message.is_error:
                detail = message.result or "Claude request failed"
                raise HTTPException(status_code=502, detail=detail)
            if message.result is None:
                raise HTTPException(
                    status_code=502,
                    detail="Claude response did not include a final result",
                )
            return message.result

    raise HTTPException(
        status_code=502, detail="Claude response ended without a result"
    )


@app.get("/openai_nba")
def news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    runner = Runner.run_sync(
        openai_agent,
        input=build_nba_prompt(nba_topic),
    )
    return {"message": runner.final_output}


@app.get("/claude_nba")
async def claude_news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    return {"message": await run_claude_prompt(build_nba_prompt(nba_topic))}


@app.get("/openai_sdk_nba")
def openai_sdk_news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    return run_openai_sdk_prompt(build_nba_prompt(nba_topic))


@app.get("/")
def index():
    return {"message": "NBA News Reporter API is running"}
