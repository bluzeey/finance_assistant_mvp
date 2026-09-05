from __future__ import annotations

import pytest
from pydantic import ValidationError

from finance_assistant.domain.query_state import (
    QueryState,
    StateField,
    StateOperation,
    StateOperationType,
    apply_state_operation,
)


def test_replace_metric_and_add_remove_vendor_filter_are_deterministic() -> None:
    state = QueryState(context_version=0)
    with_metric = apply_state_operation(
        state,
        StateOperation(
            operation=StateOperationType.REPLACE,
            field=StateField.METRIC,
            value="vendor_spend",
        ),
    )
    with_vendors = apply_state_operation(
        with_metric,
        StateOperation(
            operation=StateOperationType.ADD,
            field=StateField.FILTERS,
            filter_key="vendor_ids",
            value=["V0003", "V0001"],
        ),
    )
    removed = apply_state_operation(
        with_vendors,
        StateOperation(
            operation=StateOperationType.REMOVE,
            field=StateField.FILTERS,
            filter_key="vendor_ids",
            value="V0001",
        ),
    )

    assert str(with_metric.metric) == "vendor_spend"
    assert with_vendors.filters.vendor_ids == ("V0001", "V0003")
    assert removed.filters.vendor_ids == ("V0003",)
    assert removed.context_version == 3


def test_clear_and_reset_do_not_mutate_prior_state() -> None:
    state = QueryState.model_validate(
        {
            "context_version": 4,
            "metric": "vendor_payout_amount",
            "date_range": None,
            "filters": {"vendor_ids": ["V0003"]},
            "group_by": ["vendor_id"],
            "sort": [],
            "comparison": None,
            "referenced_query_ids": [],
            "pending_clarification": None,
        }
    )

    cleared = apply_state_operation(
        state,
        StateOperation(operation=StateOperationType.CLEAR, field=StateField.FILTERS),
    )
    reset = apply_state_operation(
        state,
        StateOperation(operation=StateOperationType.RESET_ALL),
    )

    assert state.filters.vendor_ids == ("V0003",)
    assert cleared.filters.vendor_ids == ()
    assert cleared.metric == state.metric
    assert reset.metric is None
    assert reset.context_version == 5


def test_add_remove_requires_filter_key() -> None:
    with pytest.raises(ValidationError):
        StateOperation(operation=StateOperationType.ADD, field=StateField.FILTERS, value="V0003")
