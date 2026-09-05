#!/usr/bin/env python3
"""Privacy helpers shared by fixture tests and recommended backend implementation."""
from __future__ import annotations

import re
from typing import Iterable, Mapping


def mask_account_number(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value)
    if len(value) <= 4:
        return "•" * len(value)
    return "•" * (len(value) - 4) + value[-4:]


def mask_utr(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value)
    visible = min(6, len(value))
    return "•" * max(6, len(value) - visible) + value[-visible:]


def redact_known_account_numbers(text: str | None, account_numbers: Iterable[str]) -> str | None:
    if text is None:
        return None
    result = str(text)
    # Longest first prevents a shorter known value from partially replacing a longer one.
    for number in sorted({str(n) for n in account_numbers if n}, key=len, reverse=True):
        result = result.replace(number, mask_account_number(number) or "")
    return result


def sanitize_record(row: Mapping[str, str | None], account_numbers: Iterable[str]) -> dict[str, str | None]:
    """Return a safe API/UI record. Never expose raw account numbers or UTR values."""
    safe = dict(row)
    if "account_number" in safe:
        safe["account_number"] = mask_account_number(safe.get("account_number"))
    if "utr_number" in safe:
        safe["utr_number"] = mask_utr(safe.get("utr_number"))
    if "description" in safe:
        safe["description"] = redact_known_account_numbers(safe.get("description"), account_numbers)
    return safe


def contains_probable_raw_account_number(text: str | None, account_numbers: Iterable[str]) -> bool:
    if not text:
        return False
    return any(str(number) in text for number in account_numbers if number)
