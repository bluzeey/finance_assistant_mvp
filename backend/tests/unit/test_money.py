from __future__ import annotations

from decimal import Decimal

import pytest

from finance_assistant.domain.money import (
    MoneyParseError,
    format_inr,
    money_to_api,
    parse_money,
    sum_money,
)


def test_parse_money_preserves_two_decimal_decimal_values() -> None:
    assert parse_money("10000874.04") == Decimal("10000874.04")
    assert money_to_api(Decimal("10000874.04")) == "10000874.04"


def test_parse_money_rejects_float_and_excess_precision() -> None:
    with pytest.raises(MoneyParseError):
        parse_money(1.1)  # type: ignore[arg-type]
    with pytest.raises(MoneyParseError):
        parse_money("1.001")


def test_sum_money_and_inr_format_are_exact() -> None:
    assert sum_money(["10.10", Decimal("0.90"), 4]) == Decimal("15.00")
    assert format_inr("10000874.04") == "₹1,00,00,874.04"
    assert format_inr("-380000.00") == "−₹3,80,000.00"
