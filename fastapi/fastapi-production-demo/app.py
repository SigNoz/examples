import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenTelemetry will be available after running opentelemetry-instrument
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer(__name__)
except ImportError:
    tracer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="FastAPI Production Demo",
    description="Production-ready FastAPI app with OpenTelemetry instrumentation",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI Production Demo",
        "status": "healthy",
        "service": os.getenv("OTEL_SERVICE_NAME", "fastapi-demo")
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "fastapi-demo"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID - shows manual span creation"""
    if tracer:
        span = tracer.start_span("get_user_from_db")
        span.set_attribute("user.id", user_id)
    else:
        span = None
    
    try:
        if span:
            span.add_event("querying_database", {"user_id": user_id})
        
        await asyncio.sleep(0.1)  # Simulate DB call
        
        if user_id < 1:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        if user_id > 100:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        }
        
        if span:
            span.set_attribute("user.name", user_data["name"])
            span.set_status(Status(StatusCode.OK))
        
        logger.info(f"Retrieved user {user_id}")
        return user_data
        
    except HTTPException:
        if span:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception()
        raise
    except Exception as e:
        if span:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if span:
            span.end()


@app.get("/api/users/{user_id}/orders")
async def get_user_orders(user_id: int):
    """Get user orders - shows nested spans"""
    if tracer:
        parent_span = tracer.start_span("get_user_orders")
        parent_span.set_attribute("user.id", user_id)
    else:
        parent_span = None
    
    try:
        if parent_span:
            with tracer.start_as_current_span("fetch_orders_from_api") as child_span:
                child_span.set_attribute("http.method", "GET")
                child_span.set_attribute("http.url", f"https://api.example.com/users/{user_id}/orders")
                await asyncio.sleep(0.2)  # Simulate network latency
        
        orders = [
            {"id": i, "user_id": user_id, "total": 100.0 * i}
            for i in range(1, 4)
        ]
        
        if parent_span:
            parent_span.set_attribute("orders.count", len(orders))
            parent_span.set_status(Status(StatusCode.OK))
        
        return {"user_id": user_id, "orders": orders}
        
    except Exception as e:
        if parent_span:
            parent_span.set_status(Status(StatusCode.ERROR))
            parent_span.record_exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if parent_span:
            parent_span.end()


@app.get("/api/metrics/demo")
async def metrics_demo():
    """Demo endpoint for metrics"""
    return {"message": "Check SigNoz for metrics"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
