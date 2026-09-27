"""FastAPI application for fraud rule evaluation."""

from fastapi import FastAPI

app = FastAPI(title="Fraud Rule Engine")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}