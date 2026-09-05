from __future__ import annotations

from finance_assistant.resolution.vendors import (
    EntityResolutionStatus,
    VendorResolutionMethod,
    normalize_vendor_phrase,
    resolve_vendor,
)


def test_normalization_matches_contract() -> None:
    assert normalize_vendor_phrase("  AWS-India!! ") == "aws india"


def test_exact_vendor_id_resolves_canonical_vendor() -> None:
    result = resolve_vendor("V0003")

    assert result.status == EntityResolutionStatus.RESOLVED
    assert result.vendor_ids == ("V0003",)
    assert result.method == VendorResolutionMethod.VENDOR_ID


def test_unique_alias_resolves_aws() -> None:
    result = resolve_vendor("AWS")

    assert result.status == EntityResolutionStatus.RESOLVED
    assert result.vendor_ids == ("V0003",)
    assert result.candidates[0].display_name == "AWS"
    assert result.method == VendorResolutionMethod.EXACT_ALIAS


def test_acme_and_abc_are_ambiguous_and_block_autoselect() -> None:
    acme = resolve_vendor("Acme")
    abc = resolve_vendor("ABC")

    assert acme.status == EntityResolutionStatus.AMBIGUOUS
    assert acme.vendor_ids == ("V0001", "V0002")
    assert abc.status == EntityResolutionStatus.AMBIGUOUS
    assert abc.vendor_ids == ("V0044", "V0045")


def test_fuzzy_candidates_never_auto_select() -> None:
    result = resolve_vendor("Acme Clod")

    assert result.status == EntityResolutionStatus.AMBIGUOUS
    assert result.vendor_ids == ()
    assert result.method == VendorResolutionMethod.FUZZY_CANDIDATES
    assert any(candidate.vendor_id == "V0001" for candidate in result.candidates)
