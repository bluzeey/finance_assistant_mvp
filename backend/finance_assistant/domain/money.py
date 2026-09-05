"""Decimal-only money helpers.

Money enters and leaves the API as decimal strings. Floats are rejected because
binary floating point cannot represent cents/paise exactly.
"""
from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

PAISE = Decimal("0.01")
ZERO_MONEY = Decimal("0.00")


class MoneyParseError(ValueError):
    """Raised when a value cannot safely become a two-decimal Decimal."""


def parse_money(value: str | int | Decimal) -> Decimal:
    """Parse an API/database money value and reject floats or excess precision."""
    if isinstance(value, bool):
        raise MoneyParseError("booleans are not valid money values")
    if isinstance(value, float):
        raise MoneyParseError("floats are not valid money values")

    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MoneyParseError("invalid money value") from exc

    if not parsed.is_finite():
        raise MoneyParseError("money value must be finite")
    exponent = parsed.as_tuple().exponent
    if not isinstance(exponent, int) or exponent < -2:
        raise MoneyParseError("money value has more than two decimal places")
    return parsed.quantize(PAISE, rounding=ROUND_HALF_UP)


def money_to_api(value: Decimal) -> str:
    """Return the canonical JSON decimal string with two places."""
    return f"{parse_money(value):.2f}"


def sum_money(values: Iterable[str | int | Decimal]) -> Decimal:
    total = ZERO_MONEY
    for value in values:
        total += parse_money(value)
    return total.quantize(PAISE)


def format_inr(value: str | int | Decimal) -> str:
    """Format a Decimal using Indian digit grouping for UI copy."""
    parsed = parse_money(value)
    sign = "−" if parsed < 0 else ""
    absolute = abs(parsed)
    integer_part, fraction = f"{absolute:.2f}".split(".")
    return f"{sign}₹{_group_indian(integer_part)}.{fraction}"


def _group_indian(integer_part: str) -> str:
    if len(integer_part) <= 3:
        return integer_part
    last_three = integer_part[-3:]
    leading = integer_part[:-3]
    groups: list[str] = []
    while leading:
        groups.insert(0, leading[-2:])
        leading = leading[:-2]
    return f"{','.join(groups)},{last_three}"
