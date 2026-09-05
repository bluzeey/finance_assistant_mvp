"""Deterministic vendor resolver.

The resolver returns canonical vendor IDs only for exact unambiguous matches. Fuzzy
matches are candidates for clarification and never auto-selected.
"""
from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum
from functools import lru_cache

from finance_assistant.metadata import repo_root

_VENDOR_ID_RE = re.compile(r"^V[0-9]{4}$", re.IGNORECASE)


class EntityResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"


class VendorResolutionMethod(StrEnum):
    VENDOR_ID = "vendor_id"
    EXACT_ALIAS = "exact_alias"
    EXACT_NAME = "exact_name"
    FUZZY_CANDIDATES = "fuzzy_candidates"


@dataclass(frozen=True, slots=True)
class VendorCandidate:
    vendor_id: str
    display_name: str
    legal_name: str
    vendor_category: str
    matched_alias: str | None = None
    score: float | None = None


@dataclass(frozen=True, slots=True)
class EntityResolution:
    phrase: str
    status: EntityResolutionStatus
    vendor_ids: tuple[str, ...]
    candidates: tuple[VendorCandidate, ...]
    method: VendorResolutionMethod | None


@dataclass(frozen=True, slots=True)
class _VendorRecord:
    vendor_id: str
    display_name: str
    legal_name: str
    vendor_category: str
    aliases: tuple[str, ...]

    def candidate(
        self,
        matched_alias: str | None = None,
        score: float | None = None,
    ) -> VendorCandidate:
        return VendorCandidate(
            vendor_id=self.vendor_id,
            display_name=self.display_name,
            legal_name=self.legal_name,
            vendor_category=self.vendor_category,
            matched_alias=matched_alias,
            score=score,
        )


def normalize_vendor_phrase(value: str) -> str:
    normalized = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def resolve_vendor(phrase: str) -> EntityResolution:
    normalized = normalize_vendor_phrase(phrase)
    if not normalized:
        return EntityResolution(
            phrase=phrase,
            status=EntityResolutionStatus.NOT_FOUND,
            vendor_ids=(),
            candidates=(),
            method=None,
        )

    by_id, by_alias = _vendor_indexes()
    if _VENDOR_ID_RE.match(phrase.strip()):
        vendor = by_id.get(phrase.strip().upper())
        if vendor:
            return _resolved(phrase, vendor, VendorResolutionMethod.VENDOR_ID)

    alias_matches = by_alias.get(normalized, ())
    if len(alias_matches) == 1:
        return _resolved(
            phrase,
            alias_matches[0],
            VendorResolutionMethod.EXACT_ALIAS,
            matched_alias=normalized,
        )
    if len(alias_matches) > 1:
        return EntityResolution(
            phrase=phrase,
            status=EntityResolutionStatus.AMBIGUOUS,
            vendor_ids=tuple(vendor.vendor_id for vendor in alias_matches),
            candidates=tuple(
                vendor.candidate(matched_alias=normalized) for vendor in alias_matches
            ),
            method=VendorResolutionMethod.EXACT_ALIAS,
        )

    name_matches = [
        vendor
        for vendor in by_id.values()
        if normalize_vendor_phrase(vendor.display_name) == normalized
        or normalize_vendor_phrase(vendor.legal_name) == normalized
    ]
    if len(name_matches) == 1:
        return _resolved(phrase, name_matches[0], VendorResolutionMethod.EXACT_NAME)
    if len(name_matches) > 1:
        return EntityResolution(
            phrase=phrase,
            status=EntityResolutionStatus.AMBIGUOUS,
            vendor_ids=tuple(vendor.vendor_id for vendor in name_matches),
            candidates=tuple(vendor.candidate() for vendor in name_matches),
            method=VendorResolutionMethod.EXACT_NAME,
        )

    candidates = _fuzzy_candidates(normalized, by_id.values())
    return EntityResolution(
        phrase=phrase,
        status=EntityResolutionStatus.AMBIGUOUS if candidates else EntityResolutionStatus.NOT_FOUND,
        vendor_ids=(),
        candidates=tuple(candidates),
        method=VendorResolutionMethod.FUZZY_CANDIDATES if candidates else None,
    )


def _resolved(
    phrase: str,
    vendor: _VendorRecord,
    method: VendorResolutionMethod,
    matched_alias: str | None = None,
) -> EntityResolution:
    return EntityResolution(
        phrase=phrase,
        status=EntityResolutionStatus.RESOLVED,
        vendor_ids=(vendor.vendor_id,),
        candidates=(vendor.candidate(matched_alias=matched_alias),),
        method=method,
    )


def _fuzzy_candidates(
    normalized: str,
    vendors: Iterable[_VendorRecord],
    limit: int = 5,
) -> list[VendorCandidate]:
    scored: list[VendorCandidate] = []
    for vendor in vendors:
        labels = (vendor.display_name, vendor.legal_name, *vendor.aliases)
        best_label = max(
            labels,
            key=lambda label: SequenceMatcher(
                None,
                normalized,
                normalize_vendor_phrase(label),
            ).ratio(),
        )
        score = SequenceMatcher(None, normalized, normalize_vendor_phrase(best_label)).ratio()
        if score >= 0.72:
            scored.append(vendor.candidate(matched_alias=best_label, score=round(score, 4)))
    return sorted(
        scored,
        key=lambda candidate: (-float(candidate.score or 0), candidate.display_name),
    )[:limit]


@lru_cache(maxsize=1)
def _vendor_indexes() -> tuple[dict[str, _VendorRecord], dict[str, tuple[_VendorRecord, ...]]]:
    csv_dir = repo_root() / "data" / "csv"
    vendors: dict[str, _VendorRecord] = {}
    aliases_by_vendor: dict[str, list[str]] = {}

    with (csv_dir / "vendor_aliases.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            aliases_by_vendor.setdefault(row["vendor_id"], []).append(row["alias"])

    with (csv_dir / "vendors.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            vendor_id = row["vendor_id"]
            vendors[vendor_id] = _VendorRecord(
                vendor_id=vendor_id,
                display_name=row["display_name"],
                legal_name=row["legal_name"],
                vendor_category=row["vendor_category"],
                aliases=tuple(sorted(set(aliases_by_vendor.get(vendor_id, [])))),
            )

    alias_index: dict[str, dict[str, _VendorRecord]] = {}
    for vendor in vendors.values():
        labels = (vendor.display_name, vendor.legal_name, *vendor.aliases)
        for label in labels:
            alias_index.setdefault(normalize_vendor_phrase(label), {})[vendor.vendor_id] = vendor

    return vendors, {key: tuple(value.values()) for key, value in alias_index.items()}
