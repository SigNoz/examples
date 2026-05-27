import json
import logging

from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from agents import InputGuardrailTripwireTriggered

from config import NBA_TOPIC_MAPPING
from openai_service import (
    run_openai_prompt,
    run_openai_responses_prompt,
    run_openai_agents_prompt,
    run_nba_report,
    run_nba_chat,
)
from prompts import build_nba_analysis_prompt


class ChatRequest(BaseModel):
    session_id: str
    message: str


load_dotenv()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()


@app.get("/openai_nba")
def news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    return run_openai_prompt(build_nba_analysis_prompt(nba_topic))


# TODO: how to opt-out of capturing chat messages in span attributes?
@app.get("/openai_agents_nba")
def agents_news(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    try:
        return run_openai_agents_prompt(build_nba_analysis_prompt(nba_topic))
    except InputGuardrailTripwireTriggered as e:
        raise HTTPException(
            status_code=400, detail=f"Guardrail blocked query: {str(e)}"
        )


# TODO: this should return a downloadable file
@app.get("/openai_agents_report")
def agents_report(topic: str):
    nba_topic = NBA_TOPIC_MAPPING.get(topic)
    if nba_topic is None:
        raise HTTPException(status_code=400, detail="Invalid NBA topic")

    try:
        return run_nba_report(nba_topic)
    except InputGuardrailTripwireTriggered as e:
        raise HTTPException(
            status_code=400, detail=f"Guardrail blocked query: {str(e)}"
        )


# TODO: this could accept the file as input to further chat on it, while retaining conversation context from the same API?
# TODO: or perhaps we could merge these two APIs into one?
@app.post("/openai_agents_chat")
def agents_chat(req: ChatRequest):
    try:
        return run_nba_chat(req.session_id, req.message)
    except InputGuardrailTripwireTriggered as e:
        raise HTTPException(
            status_code=400, detail=f"Guardrail blocked query: {str(e)}"
        )


@app.get("/")
def index():
    return {"message": "OpenAI NBA News Reporter API is running"}


# def main() -> None:
#     prompt = build_nba_analysis_prompt("Finals")
#     result = run_openai_responses_prompt(prompt)
#     print(json.dumps(result, indent=2))


# main()
