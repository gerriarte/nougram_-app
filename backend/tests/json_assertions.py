"""Helpers for asserting API JSON money/numeric fields (often serialized as strings)."""

from decimal import Decimal


def money_eq(actual, expected) -> None:
    """Compare money-like values from JSON (str/float/int/Decimal)."""
    assert Decimal(str(actual)) == Decimal(str(expected))
