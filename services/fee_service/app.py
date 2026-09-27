"""FastAPI application for fee calculations."""

from fastapi import FastAPI

app = FastAPI(title="Fee Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}