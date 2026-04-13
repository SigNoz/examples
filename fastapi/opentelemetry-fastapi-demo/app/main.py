import asyncio
import logging
import random

import httpx
from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()
tracer = trace.get_tracer("sample-fastapi-app")


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/ping")
async def health_check():
    return "pong"


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    # create a custom span to capture business logic and add detailed context for better analysis
    with tracer.start_as_current_span("load-item") as span:
        span.set_attribute("demo.item_id", item_id)
        span.set_attribute("demo.has_query", q is not None)

        if item_id % 2 == 0:
            # simulate variable I/O latency
            seconds = random.uniform(0, 3)
            span.set_attribute("demo.io_delay_seconds", round(seconds, 3))
            await asyncio.sleep(seconds)

        return {"item_id": item_id, "q": q}


@app.get("/invalid")
async def invalid():
    raise ValueError("Invalid request")


@app.get("/exception")
async def exception():
    try:
        raise ValueError("sadness")
    except Exception as ex:
        span = trace.get_current_span()

        logger.error(ex, exc_info=True)
        seconds = random.uniform(0, 30)

        # record_exception converts the exception into a span event.
        exception = IOError(f"Failed at {seconds}")
        span.record_exception(exception)
        span.set_attributes({"error.simulated": True})
        # Update the span status to failed.
        span.set_status(Status(StatusCode.ERROR, "internal error"))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Got sadness",
        )


@app.get("/external-api")
async def external_api():
    seconds = random.uniform(0, 3)
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"https://httpbin.org/delay/{seconds}")

        return {"status": response.status_code}
