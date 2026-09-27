"""Fraud rules and HTTP endpoints."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Fraud Rule Engine")
BLOCKED_ACCOUNTS = {"acct-frozen"}
MAX_TRANSACTION_AMOUNT = Decimal("10000.00")
MAX_TRANSACTIONS_PER_MINUTE = 3
recent_transactions: dict[str, list[datetime]] = {}


class CheckRequest(BaseModel):
    """Transaction details submitted for fraud screening."""

    account_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)


class CheckResult(BaseModel):
    """Fraud screening result and the rules that matched."""

    flagged: bool
    reasons: list[str]


def _is_blocked_account(account_id: str) -> bool:
    """Check whether an account is on the demo blocklist."""
    return account_id in BLOCKED_ACCOUNTS


def _exceeds_amount_limit(amount: Decimal) -> bool:
    """Check whether a payment reaches the manual-review threshold."""
    return amount >= MAX_TRANSACTION_AMOUNT


def _exceeds_velocity_limit(account_id: str, now: datetime) -> bool:
    """Record an attempt and flag the fourth attempt within one minute."""
    cutoff = now - timedelta(minutes=1)
    recent = [stamp for stamp in recent_transactions.get(account_id, []) if stamp > cutoff]
    recent.append(now)
    recent_transactions[account_id] = recent
    return len(recent) > MAX_TRANSACTIONS_PER_MINUTE


def assess_transaction(account_id: str, amount: Decimal) -> list[str]:
    """Collect the rules that flag a transaction for review."""
    reasons: list[str] = []
    now = datetime.now(timezone.utc)
    if _is_blocked_account(account_id):
        reasons.append("account_blocklisted")
    if _exceeds_amount_limit(amount):
        reasons.append("amount_threshold")
    if _exceeds_velocity_limit(account_id, now):
        reasons.append("velocity_limit")
    return reasons


def check_transaction(account_id: str, amount: Decimal) -> bool:
    """Return whether the transaction matches any fraud rule."""
    return bool(assess_transaction(account_id, amount))


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service process is ready."""
    return {"status": "ok"}


@app.post("/checks", response_model=CheckResult)
def check(request: CheckRequest) -> CheckResult:
    """Evaluate a transaction and return matching rule names."""
    reasons = assess_transaction(request.account_id, request.amount)
    return CheckResult(flagged=bool(reasons), reasons=reasons)


@app.get("/rules", response_model=list[str])
def list_rules() -> list[str]:
    """Describe the active demo fraud rules."""
    return ["blocked account", "amount at or above 10000", "more than 3 attempts per minute"]