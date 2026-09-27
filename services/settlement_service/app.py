"""Settlement rules and HTTP endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.payment_service.app import get_payment, mark_payment_settled

app = FastAPI(title="Settlement Service")
settlements: dict[str, "SettlementRecord"] = {}


class SettlementRecord(BaseModel):
    """Confirmation that an accepted payment was settled."""

    settlement_id: str
    payment_id: str
    account_id: str
    amount: Decimal
    settled_at: datetime


def settle_payment(payment_id: str) -> SettlementRecord:
    """Settle an accepted payment through the payment service."""
    payment = get_payment(payment_id)
    if payment is None:
        raise LookupError("payment not found")
    if payment.status != "accepted":
        raise ValueError("payment is not eligible for settlement")
    updated_payment = mark_payment_settled(payment_id)
    if updated_payment is None:
        raise LookupError("payment not found")
    record = SettlementRecord(
        settlement_id=str(uuid4()),
        payment_id=payment_id,
        account_id=updated_payment.account_id,
        amount=updated_payment.amount,
        settled_at=datetime.now(timezone.utc),
    )
    settlements[record.settlement_id] = record
    return record


def get_settlement(settlement_id: str) -> SettlementRecord | None:
    """Return a settlement confirmation by identifier."""
    return settlements.get(settlement_id)


def list_account_settlements(account_id: str) -> list[SettlementRecord]:
    """Return settled transactions for an account."""
    return [record for record in settlements.values() if record.account_id == account_id]


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.post("/settlements/{payment_id}", response_model=SettlementRecord, status_code=201)
def create_settlement(payment_id: str) -> SettlementRecord:
    """Settle a payment that has been accepted by the payment service."""
    try:
        return settle_payment(payment_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/settlements/{settlement_id}", response_model=SettlementRecord)
def read_settlement(settlement_id: str) -> SettlementRecord:
    """Fetch one settlement confirmation."""
    record = get_settlement(settlement_id)
    if record is None:
        raise HTTPException(status_code=404, detail="settlement not found")
    return record


@app.get("/accounts/{account_id}/settlements", response_model=list[SettlementRecord])
def read_account_settlements(account_id: str) -> list[SettlementRecord]:
    """List settled transactions for an account."""
    return list_account_settlements(account_id)