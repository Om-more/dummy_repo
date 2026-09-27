"""FastAPI application for payment settlement."""

from fastapi import FastAPI

app = FastAPI(title="Settlement Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}