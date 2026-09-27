"""Tests for payment initiation and retrieval."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from services.fraud_rule_engine.app import recent_transactions
from services.payment_service.app import PaymentRequest, app, payments, process_payment

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_payments() -> None:
    """Isolate each test from the in-memory demo state."""
    payments.clear()
    recent_transactions.clear()


def test_process_payment_calculates_fee_and_stores_record() -> None:
    request = PaymentRequest(account_id="acct-1", payee_id="shop-1", amount=Decimal("100.00"))

    record = process_payment(request)

    assert record.status == "accepted"
    assert record.fee == Decimal("0.50")
    assert record.total_debit == Decimal("100.50")
    assert payments[record.payment_id] == record


def test_payment_endpoints_create_and_list_records() -> None:
    response = client.post(
        "/payments",
        json={"account_id": "acct-2", "payee_id": "shop-2", "amount": "24.00"},
    )

    assert response.status_code == 201
    payment_id = response.json()["payment_id"]
    assert client.get(f"/payments/{payment_id}").status_code == 200
    account_response = client.get("/accounts/acct-2/payments")
    assert len(account_response.json()) == 1


def test_fraudulent_payment_is_rejected_without_storage() -> None:
    response = client.post(
        "/payments",
        json={"account_id": "acct-3", "payee_id": "shop-3", "amount": "10000.00"},
    )

    assert response.status_code == 403
    assert payments == {}


def test_missing_payment_returns_not_found() -> None:
    assert client.get("/payments/missing").status_code == 404