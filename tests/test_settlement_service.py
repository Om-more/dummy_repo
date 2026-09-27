"""Tests for settlement processing and account queries."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from services.fraud_rule_engine.app import recent_transactions
from services.payment_service.app import PaymentRequest, app as payment_app, payments, process_payment
from services.settlement_service.app import app, settle_payment, settlements

client = TestClient(app)
payment_client = TestClient(payment_app)


@pytest.fixture(autouse=True)
def reset_service_state() -> None:
    """Isolate each test from payment and settlement state."""
    payments.clear()
    settlements.clear()
    recent_transactions.clear()


def test_settlement_updates_payment_and_account_activity() -> None:
    payment = process_payment(
        PaymentRequest(account_id="acct-4", payee_id="shop-4", amount=Decimal("42.00"))
    )

    record = settle_payment(payment.payment_id)

    assert payments[payment.payment_id].status == "settled"
    assert record.account_id == "acct-4"
    assert client.get("/accounts/acct-4/settlements").json()[0]["settlement_id"] == record.settlement_id


def test_cannot_settle_the_same_payment_twice() -> None:
    payment = process_payment(
        PaymentRequest(account_id="acct-5", payee_id="shop-5", amount=Decimal("10.00"))
    )
    settle_payment(payment.payment_id)

    with pytest.raises(ValueError, match="not eligible"):
        settle_payment(payment.payment_id)


def test_unknown_payment_returns_not_found() -> None:
    response = client.post("/settlements/unknown")

    assert response.status_code == 404


def test_payment_created_over_http_can_be_settled() -> None:
    payment_response = payment_client.post(
        "/payments",
        json={"account_id": "acct-6", "payee_id": "shop-6", "amount": "19.00"},
    )
    settlement_response = client.post(f"/settlements/{payment_response.json()['payment_id']}")

    assert payment_response.status_code == 201
    assert settlement_response.status_code == 201