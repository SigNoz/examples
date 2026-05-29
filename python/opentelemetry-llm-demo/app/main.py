import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="OpenTelemetry NBA Agent Demo")
app.include_router(router)
