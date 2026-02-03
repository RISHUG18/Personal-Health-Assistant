"""FastAPI application entrypoint."""
from fastapi import FastAPI

from routes import reports

app = FastAPI(
    title="Personal Health Assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}

# Mount the reports router that exposes the Supabase upload endpoint.
app.include_router(reports.router)
