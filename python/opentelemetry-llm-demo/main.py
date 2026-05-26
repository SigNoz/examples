import json
import logging

from fastapi import HTTPException
from dotenv import load_dotenv
from fastapi import FastAPI

from config import NBA_TOPIC_MAPPING
from openai_service import run_openai_prompt, run_openai_responses_prompt
from prompts import build_nba_analysis_prompt

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


@app.get("/")
def index():
    return {"message": "OpenAI NBA News Reporter API is running"}


def main() -> None:
    prompt = build_nba_analysis_prompt("Finals")
    result = run_openai_responses_prompt(prompt)
    print(json.dumps(result, indent=2))


main()
