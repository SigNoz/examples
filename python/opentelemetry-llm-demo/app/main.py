import logging
from typing import Any

from agents import InputGuardrailTripwireTriggered
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.agent_service import run_agent_turn
from app.models import AgentTurnRequest, AgentTurnResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="OpenTelemetry NBA Agent Demo")


@app.get("/")
def index() -> dict[str, str]:
    return {"message": "OpenTelemetry NBA agent demo is running"}


@app.post("/agent/turn", response_model=AgentTurnResponse)
def agent_turn(req: AgentTurnRequest) -> dict[str, Any]:
    try:
        return run_agent_turn(req.topic, req.message)
    except InputGuardrailTripwireTriggered as exc:
        raise HTTPException(
            status_code=400, detail=f"Guardrail blocked query: {str(exc)}"
        ) from exc
