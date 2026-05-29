import logging
from typing import Any

from agents import InputGuardrailTripwireTriggered
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace

from app.agent_service import run_agent_turn
from app.models import AgentTurnRequest, AgentTurnResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="OpenTelemetry NBA Agent Demo")


@app.exception_handler(InputGuardrailTripwireTriggered)
async def handle_guardrail_block(
    request: Request,
    exc: InputGuardrailTripwireTriggered,
) -> JSONResponse:
    guardrail_msg = exc.guardrail_result.output.output_info
    span = trace.get_current_span()

    # record the guardrail trip as a span exception event
    # note that this method captures the entire stack-trace although that is unneeded in our case
    span.record_exception(exc)

    return JSONResponse(status_code=400, content={"detail": guardrail_msg})


@app.get("/")
def index() -> dict[str, str]:
    return {"message": "OpenTelemetry NBA agent demo is running"}


@app.post("/agent/turn", response_model=AgentTurnResponse)
def agent_turn(req: AgentTurnRequest) -> dict[str, Any]:
    return run_agent_turn(req.topic, req.message, req.session_id)
