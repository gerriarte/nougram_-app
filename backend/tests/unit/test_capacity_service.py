from datetime import datetime, timezone
from decimal import Decimal

from app.services.capacity_service import CapacityService


def test_merge_commitments_by_unique_key_aggregates_hours():
    period_start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)

    raw_entries = [
        (10, 1, period_start, period_end, Decimal("6")),
        (10, 2, period_start, period_end, Decimal("4")),
        (11, None, period_start, period_end, Decimal("3")),
    ]

    merged = CapacityService._merge_commitments_by_unique_key(
        organization_id=1,
        source_type="quote",
        source_id=99,
        state="tentative",
        raw_entries=raw_entries,
    )

    assert len(merged) == 2
    by_member = {item.team_member_id: item for item in merged}
    assert by_member[10].hours == Decimal("10")
    assert by_member[11].hours == Decimal("3")


def test_merge_commitments_by_unique_key_prefers_first_non_null_cell():
    period_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 30, 23, 59, 59, tzinfo=timezone.utc)

    raw_entries = [
        (20, None, period_start, period_end, Decimal("2")),
        (20, 7, period_start, period_end, Decimal("1")),
    ]

    merged = CapacityService._merge_commitments_by_unique_key(
        organization_id=1,
        source_type="quote",
        source_id=100,
        state="tentative",
        raw_entries=raw_entries,
    )

    assert len(merged) == 1
    assert merged[0].cell_id == 7
    assert merged[0].hours == Decimal("3")
