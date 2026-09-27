"""Fee calculation rules and HTTP endpoints."""

from decimal import Decimal, ROUND_HALF_UP

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Fee Service")


class FeeRequest(BaseModel):
    """Input for a fee quote."""

    amount: Decimal = Field(gt=0)


class FeeQuote(BaseModel):
    """A monetary amount and its calculated fee."""

    amount: Decimal
    fee: Decimal


def round_money(amount: Decimal) -> Decimal:
    """Round a monetary amount to cents using standard half-up rounding."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_transaction_fee(amount: Decimal) -> Decimal:
    """Calculate the standard transaction fee at 0.5 percent."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    return round_money(amount * Decimal("0.005"))


def calculate_late_fee(outstanding_balance: Decimal) -> Decimal:
    """Calculate a late fee for a positive outstanding balance."""
    if outstanding_balance <= 0:
        raise ValueError("outstanding balance must be positive")
    return round_money(outstanding_balance * Decimal("0.012"))


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.post("/fees/transaction", response_model=FeeQuote)
def quote_transaction_fee(request: FeeRequest) -> FeeQuote:
    """Return the fee charged for a transaction amount."""
    return FeeQuote(amount=request.amount, fee=calculate_transaction_fee(request.amount))


@app.post("/fees/late", response_model=FeeQuote)
def quote_late_fee(request: FeeRequest) -> FeeQuote:
    """Return the late fee for an outstanding balance."""
    return FeeQuote(amount=request.amount, fee=calculate_late_fee(request.amount))