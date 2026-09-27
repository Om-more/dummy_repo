"""FastAPI application for payment initiation."""

from fastapi import FastAPI

app = FastAPI(title="Payment Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}