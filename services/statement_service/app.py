"""Account statement aggregation and HTTP endpoints."""

from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel

from services.settlement_service.app import (
    SettlementRecord,
    list_account_settlements,
)

app = FastAPI(title="Statement Service")


class Statement(BaseModel):
    """Summary of settled account activity."""

    account_id: str
    transaction_count: int
    total_settled: Decimal
    generated_at: datetime
    settlements: list[SettlementRecord]


def summarize_settlements(records: list[SettlementRecord]) -> tuple[int, Decimal]:
    """Count settlement records and total their transaction amounts."""
    return len(records), sum((record.amount for record in records), Decimal("0.00"))


def generate_statement(account_id: str) -> Statement:
    """Build an account statement from settlement service records."""
    records = list_account_settlements(account_id)
    transaction_count, total_settled = summarize_settlements(records)
    return Statement(
        account_id=account_id,
        transaction_count=transaction_count,
        total_settled=total_settled,
        generated_at=datetime.now().astimezone(),
        settlements=records,
    )


def list_statement_transactions(account_id: str) -> list[SettlementRecord]:
    """Return the settlement rows included in an account statement."""
    statement = generate_statement(account_id)
    return statement.settlements


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.get("/statements/{account_id}", response_model=Statement)
def read_statement(account_id: str) -> Statement:
    """Generate a summary of settled activity for an account."""
    return generate_statement(account_id)


@app.get("/statements/{account_id}/settlements", response_model=list[SettlementRecord])
def read_statement_transactions(account_id: str) -> list[SettlementRecord]:
    """List the settled transactions included in an account statement."""
    return list_statement_transactions(account_id)