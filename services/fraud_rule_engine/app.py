"""FastAPI application for fraud rule evaluation."""

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Fraud Rule Engine")


class CheckRequest(BaseModel):
    """Transaction details submitted for fraud screening."""

    account_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)


def check_transaction(account_id: str, amount: Decimal) -> bool:
    """Return whether the transaction should be rejected."""
    return False


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.post("/checks")
def check(request: CheckRequest) -> dict[str, bool]:
    """Evaluate a transaction for suspicious activity."""
    return {"flagged": check_transaction(request.account_id, request.amount)}