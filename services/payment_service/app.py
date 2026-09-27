"""Payment initiation rules and HTTP endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.fee_service.app import calculate_transaction_fee
from services.fraud_rule_engine.app import check_transaction

app = FastAPI(title="Payment Service")
payments: dict[str, "PaymentRecord"] = {}


class PaymentRequest(BaseModel):
    """Details required to initiate a payment."""

    account_id: str = Field(min_length=1)
    payee_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)


class PaymentRecord(BaseModel):
    """Persisted in-memory payment and its processing state."""

    payment_id: str
    account_id: str
    payee_id: str
    amount: Decimal
    fee: Decimal
    total_debit: Decimal
    status: str
    created_at: datetime


def process_payment(request: PaymentRequest) -> PaymentRecord:
    """Screen a payment, calculate its fee, and store the accepted record."""
    if check_transaction(request.account_id, request.amount):
        raise ValueError("payment flagged for review")
    fee = calculate_transaction_fee(request.amount)
    record = PaymentRecord(
        payment_id=str(uuid4()),
        account_id=request.account_id,
        payee_id=request.payee_id,
        amount=request.amount,
        fee=fee,
        total_debit=request.amount + fee,
        status="accepted",
        created_at=datetime.now(timezone.utc),
    )
    payments[record.payment_id] = record
    return record


def get_payment(payment_id: str) -> PaymentRecord | None:
    """Return a payment by identifier, if it exists."""
    return payments.get(payment_id)


def list_account_payments(account_id: str) -> list[PaymentRecord]:
    """Return all payments belonging to an account."""
    return [record for record in payments.values() if record.account_id == account_id]


def mark_payment_settled(payment_id: str) -> PaymentRecord | None:
    """Mark an accepted payment settled and return its updated record."""
    record = get_payment(payment_id)
    if record is None:
        return None
    updated = record.model_copy(update={"status": "settled"})
    payments[payment_id] = updated
    return updated


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.post("/payments", response_model=PaymentRecord, status_code=201)
def initiate_payment(request: PaymentRequest) -> PaymentRecord:
    """Create an accepted payment unless fraud screening rejects it."""
    try:
        return process_payment(request)
    except ValueError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@app.get("/payments/{payment_id}", response_model=PaymentRecord)
def read_payment(payment_id: str) -> PaymentRecord:
    """Fetch one payment record."""
    record = get_payment(payment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="payment not found")
    return record


@app.get("/accounts/{account_id}/payments", response_model=list[PaymentRecord])
def read_account_payments(account_id: str) -> list[PaymentRecord]:
    """List payments initiated by an account."""
    return list_account_payments(account_id)