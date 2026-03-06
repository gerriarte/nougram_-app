"""
Normalize legacy monetary records to organization primary currency.

Usage:
  - Dry run all organizations:
      python backend/scripts/normalize_primary_currency.py
  - Apply changes all organizations:
      python backend/scripts/normalize_primary_currency.py --apply
  - Dry run one organization:
      python backend/scripts/normalize_primary_currency.py --organization-id 12
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from sqlalchemy import select

# Ensure backend app imports work when script is run from repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXCHANGE_RATES_TO_USD: dict[str, float] = {}
SUPPORTED_CURRENCIES: set[str] = set()
TABLES_SUPPORTED = ("team_members", "costs_fixed", "equipment_amortization")
logger: Any = None


@dataclass
class TableCounters:
    scanned: int = 0
    mismatched: int = 0
    converted: int = 0
    skipped_invalid_currency: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "scanned": self.scanned,
            "mismatched": self.mismatched,
            "converted": self.converted,
            "skipped_invalid_currency": self.skipped_invalid_currency,
        }


def _quant(amount: Decimal, scale: int) -> Decimal:
    return amount.quantize(Decimal("1").scaleb(-scale), rounding=ROUND_HALF_UP)


def _convert_decimal(amount: Decimal, from_currency: str, to_currency: str, scale: int) -> Decimal:
    if from_currency == to_currency:
        return _quant(amount, scale)

    from_rate = EXCHANGE_RATES_TO_USD.get(from_currency)
    to_rate = EXCHANGE_RATES_TO_USD.get(to_currency)
    if from_rate is None or to_rate is None:
        raise ValueError(f"Unsupported currency conversion: {from_currency} -> {to_currency}")

    converted = (amount / Decimal(str(from_rate))) * Decimal(str(to_rate))
    return _quant(converted, scale)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _normalize_team_members(
    session,
    organization_id: int,
    primary_currency: str,
    dry_run: bool,
) -> dict[str, Any]:
    counters = TableCounters()
    changed_ids: list[int] = []
    from app.models.team import TeamMember

    result = await session.execute(
        select(TeamMember).where(TeamMember.organization_id == organization_id)
    )
    records = result.scalars().all()
    counters.scanned = len(records)

    for record in records:
        from_currency = (record.currency or "").upper()
        if from_currency == primary_currency:
            continue

        counters.mismatched += 1
        if from_currency not in SUPPORTED_CURRENCIES:
            counters.skipped_invalid_currency += 1
            logger.warning(
                "Skipping team member with unsupported currency",
                module="normalize_primary_currency",
                function="_normalize_team_members",
                organization_id=organization_id,
                team_member_id=record.id,
                currency=from_currency,
            )
            continue

        converted_salary = _convert_decimal(
            Decimal(str(record.salary_monthly_brute)),
            from_currency,
            primary_currency,
            scale=4,
        )
        counters.converted += 1
        changed_ids.append(record.id)

        if not dry_run:
            record.salary_monthly_brute = converted_salary
            record.currency = primary_currency

    return {
        "table": "team_members",
        **counters.to_dict(),
        "changed_ids_preview": changed_ids[:50],
    }


async def _normalize_fixed_costs(
    session,
    organization_id: int,
    primary_currency: str,
    dry_run: bool,
) -> dict[str, Any]:
    counters = TableCounters()
    changed_ids: list[int] = []
    from app.models.cost import CostFixed

    result = await session.execute(
        select(CostFixed).where(CostFixed.organization_id == organization_id)
    )
    records = result.scalars().all()
    counters.scanned = len(records)

    for record in records:
        from_currency = (record.currency or "").upper()
        if from_currency == primary_currency:
            continue

        counters.mismatched += 1
        if from_currency not in SUPPORTED_CURRENCIES:
            counters.skipped_invalid_currency += 1
            logger.warning(
                "Skipping fixed cost with unsupported currency",
                module="normalize_primary_currency",
                function="_normalize_fixed_costs",
                organization_id=organization_id,
                cost_id=record.id,
                currency=from_currency,
            )
            continue

        converted_amount = _convert_decimal(
            Decimal(str(record.amount_monthly)),
            from_currency,
            primary_currency,
            scale=4,
        )
        counters.converted += 1
        changed_ids.append(record.id)

        if not dry_run:
            record.amount_monthly = converted_amount
            record.currency = primary_currency

    return {
        "table": "costs_fixed",
        **counters.to_dict(),
        "changed_ids_preview": changed_ids[:50],
    }


async def _normalize_equipment(
    session,
    organization_id: int,
    primary_currency: str,
    dry_run: bool,
) -> dict[str, Any]:
    counters = TableCounters()
    changed_ids: list[int] = []
    from app.models.equipment import EquipmentAmortization

    result = await session.execute(
        select(EquipmentAmortization).where(EquipmentAmortization.organization_id == organization_id)
    )
    records = result.scalars().all()
    counters.scanned = len(records)

    for record in records:
        from_currency = (record.currency or "").upper()
        if from_currency == primary_currency:
            continue

        counters.mismatched += 1
        if from_currency not in SUPPORTED_CURRENCIES:
            counters.skipped_invalid_currency += 1
            logger.warning(
                "Skipping equipment with unsupported currency",
                module="normalize_primary_currency",
                function="_normalize_equipment",
                organization_id=organization_id,
                equipment_id=record.id,
                currency=from_currency,
            )
            continue

        converted_purchase_price = _convert_decimal(
            Decimal(str(record.purchase_price)),
            from_currency,
            primary_currency,
            scale=2,
        )
        converted_salvage_value = _convert_decimal(
            Decimal(str(record.salvage_value)),
            from_currency,
            primary_currency,
            scale=2,
        )
        counters.converted += 1
        changed_ids.append(record.id)

        if not dry_run:
            record.purchase_price = converted_purchase_price
            record.salvage_value = converted_salvage_value
            record.currency = primary_currency
            # After normalization to tenant primary currency this legacy hint is no longer relevant.
            record.exchange_rate_at_purchase = None

    return {
        "table": "equipment_amortization",
        **counters.to_dict(),
        "changed_ids_preview": changed_ids[:50],
    }


async def run(organization_id: int | None, apply_changes: bool) -> dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.core.currency import EXCHANGE_RATES_TO_USD as rates
    from app.core.logging import get_logger
    from app.models.organization import Organization
    from app.services.settings_service import SettingsService

    global EXCHANGE_RATES_TO_USD, SUPPORTED_CURRENCIES, logger
    EXCHANGE_RATES_TO_USD = rates
    SUPPORTED_CURRENCIES = set(EXCHANGE_RATES_TO_USD.keys())
    logger = get_logger(__name__)

    dry_run = not apply_changes
    report: dict[str, Any] = {
        "timestamp_utc": _utc_now_iso(),
        "mode": "apply" if apply_changes else "dry_run",
        "organization_id_filter": organization_id,
        "tables_supported": list(TABLES_SUPPORTED),
        "organizations": [],
    }

    async with AsyncSessionLocal() as session:
        settings_service = SettingsService(session)

        org_query = select(Organization)
        if organization_id is not None:
            org_query = org_query.where(Organization.id == organization_id)

        org_result = await session.execute(org_query)
        organizations = org_result.scalars().all()

        if not organizations:
            logger.warning(
                "No organizations found for filter",
                module="normalize_primary_currency",
                function="run",
                organization_id_filter=organization_id,
            )
            return report

        logger.info(
            "Starting currency normalization run",
            module="normalize_primary_currency",
            function="run",
            mode=report["mode"],
            organizations=len(organizations),
        )

        for org in organizations:
            org_primary_currency = await settings_service.get_primary_currency(org.id)
            if org_primary_currency not in SUPPORTED_CURRENCIES:
                logger.warning(
                    "Skipping organization with unsupported primary currency",
                    module="normalize_primary_currency",
                    function="run",
                    organization_id=org.id,
                    primary_currency=org_primary_currency,
                )
                continue

            team_report = await _normalize_team_members(
                session=session,
                organization_id=org.id,
                primary_currency=org_primary_currency,
                dry_run=dry_run,
            )
            costs_report = await _normalize_fixed_costs(
                session=session,
                organization_id=org.id,
                primary_currency=org_primary_currency,
                dry_run=dry_run,
            )
            equipment_report = await _normalize_equipment(
                session=session,
                organization_id=org.id,
                primary_currency=org_primary_currency,
                dry_run=dry_run,
            )

            report["organizations"].append(
                {
                    "organization_id": org.id,
                    "organization_name": org.name,
                    "primary_currency": org_primary_currency,
                    "tables": {
                        "team_members": team_report,
                        "costs_fixed": costs_report,
                        "equipment_amortization": equipment_report,
                    },
                }
            )

            if apply_changes:
                await session.commit()
            else:
                await session.rollback()

    # Compute global summary
    summary = {
        "organizations_processed": len(report["organizations"]),
        "scanned": 0,
        "mismatched": 0,
        "converted": 0,
        "skipped_invalid_currency": 0,
    }
    for org_report in report["organizations"]:
        for table_name in TABLES_SUPPORTED:
            table_report = org_report["tables"][table_name]
            summary["scanned"] += table_report["scanned"]
            summary["mismatched"] += table_report["mismatched"]
            summary["converted"] += table_report["converted"]
            summary["skipped_invalid_currency"] += table_report["skipped_invalid_currency"]
    report["summary"] = summary
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize legacy monetary records to primary currency per organization."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Default mode is dry-run.",
    )
    parser.add_argument(
        "--organization-id",
        type=int,
        default=None,
        help="Optional organization ID filter.",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="backend/scripts/reports/primary_currency_normalization_report.json",
        help="Path where JSON report will be written.",
    )
    return parser


def _write_report(report_path: str, payload: dict[str, Any]) -> None:
    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def _main_async() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()
    from app.core.logging import get_logger
    local_logger = get_logger(__name__)

    report = await run(
        organization_id=args.organization_id,
        apply_changes=args.apply,
    )
    _write_report(args.report_path, report)

    local_logger.info(
        "Normalization finished",
        module="normalize_primary_currency",
        function="_main_async",
        mode=report.get("mode"),
        summary=report.get("summary"),
        report_path=args.report_path,
    )
    return 0


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    raise SystemExit(main())
