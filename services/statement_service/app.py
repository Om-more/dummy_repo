"""FastAPI application for account statements."""

from fastapi import FastAPI

app = FastAPI(title="Statement Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}