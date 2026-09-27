"""Tests for fraud rules and their HTTP interface."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from services.fraud_rule_engine.app import app, check_transaction, recent_transactions

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_velocity_state() -> None:
    """Reset the rolling velocity window before each test."""
    recent_transactions.clear()


def test_normal_transaction_is_not_flagged() -> None:
    assert check_transaction("acct-10", Decimal("250.00")) is False


def test_blocklisted_account_is_flagged() -> None:
    response = client.post("/checks", json={"account_id": "acct-frozen", "amount": "12.00"})

    assert response.status_code == 200
    assert response.json() == {"flagged": True, "reasons": ["account_blocklisted"]}


def test_amount_threshold_is_flagged() -> None:
    assert check_transaction("acct-11", Decimal("10000.00")) is True


def test_fourth_attempt_in_a_minute_is_flagged() -> None:
    outcomes = [check_transaction("acct-12", Decimal("5.00")) for _ in range(4)]

    assert outcomes == [False, False, False, True]


def test_rules_endpoint_lists_active_controls() -> None:
    response = client.get("/rules")

    assert response.status_code == 200
    assert len(response.json()) == 3