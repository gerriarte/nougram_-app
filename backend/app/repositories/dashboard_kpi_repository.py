"""
Repository: dashboard KPI aggregates using latest quote per project.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, Quote, project_taxes
from app.models.tax import Tax


@dataclass(frozen=True)
class DashboardKpiTotals:
    """Aggregated KPI values (organization scope, already filtered)."""

    total_cotizado_con_impuestos: Decimal
    costo_total_operacional: Decimal
    margen_neto_total: Decimal
    numero_propuestas_realizadas: int
    numero_propuestas_ganadas: int


class DashboardKpiRepository:
    """Data access for unified dashboard KPIs (latest quote per project)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_latest_quotes_kpis(
        self,
        organization_id: int,
        range_start_utc: datetime,
        range_end_utc: datetime,
    ) -> DashboardKpiTotals:
        """
        Sum KPIs over projects whose *latest* quote (max version, tie-break max id)
        falls in [range_start_utc, range_end_utc] on Quote.updated_at.
        Excludes Project.status == 'Draft'. Excludes soft-deleted projects.
        """
        max_version_sq = (
            select(Quote.project_id.label("pid"), func.max(Quote.version).label("mv"))
            .join(Project, Project.id == Quote.project_id)
            .where(
                Project.organization_id == organization_id,
                Project.deleted_at.is_(None),
                Quote.is_active == 1,
            )
            .group_by(Quote.project_id)
            .subquery()
        )

        candidates_sq = (
            select(
                Quote.id.label("qid"),
                Quote.project_id.label("proj_id"),
                Quote.updated_at.label("qu_updated_at"),
                Quote.created_at.label("qu_created_at"),
                Quote.total_client_price.label("client_price"),
                Quote.total_internal_cost.label("internal_cost"),
                Project.status.label("proj_status"),
            )
            .join(Project, Project.id == Quote.project_id)
            .join(
                max_version_sq,
                and_(
                    Quote.project_id == max_version_sq.c.pid,
                    Quote.version == max_version_sq.c.mv,
                ),
            )
            .where(
                Project.organization_id == organization_id,
                Project.deleted_at.is_(None),
                Quote.is_active == 1,
            )
            .subquery()
        )

        latest_id_sq = (
            select(
                candidates_sq.c.proj_id.label("pid2"),
                func.max(candidates_sq.c.qid).label("latest_qid"),
            )
            .group_by(candidates_sq.c.proj_id)
            .subquery()
        )

        latest_sq = (
            select(
                candidates_sq.c.proj_id,
                candidates_sq.c.client_price,
                candidates_sq.c.internal_cost,
                candidates_sq.c.proj_status,
            )
            .join(
                latest_id_sq,
                and_(
                    candidates_sq.c.proj_id == latest_id_sq.c.pid2,
                    candidates_sq.c.qid == latest_id_sq.c.latest_qid,
                ),
            )
            .where(
                candidates_sq.c.proj_status != "Draft",
                func.coalesce(candidates_sq.c.qu_updated_at, candidates_sq.c.qu_created_at)
                >= range_start_utc,
                func.coalesce(candidates_sq.c.qu_updated_at, candidates_sq.c.qu_created_at)
                <= range_end_utc,
            )
            .subquery()
        )

        tax_pct_sq = (
            select(
                project_taxes.c.project_id.label("proj_id"),
                func.coalesce(func.sum(Tax.percentage), 0).label("tax_pct"),
            )
            .select_from(project_taxes)
            .join(Tax, Tax.id == project_taxes.c.tax_id)
            .where(Tax.deleted_at.is_(None))
            .group_by(project_taxes.c.project_id)
            .subquery()
        )

        billed_expr = func.coalesce(latest_sq.c.client_price, 0) * (
            1 + (func.coalesce(tax_pct_sq.c.tax_pct, 0) / 100)
        )
        cost_expr = func.coalesce(latest_sq.c.internal_cost, 0)
        margin_expr = billed_expr - cost_expr

        totals_stmt = select(
            func.coalesce(func.sum(billed_expr), 0).label("total_billed"),
            func.coalesce(func.sum(cost_expr), 0).label("total_cost"),
            func.coalesce(func.sum(margin_expr), 0).label("total_margin"),
            func.count().label("total_count"),
            func.coalesce(
                func.sum(case((latest_sq.c.proj_status == "Won", 1), else_=0)),
                0,
            ).label("won_count"),
        ).select_from(
            latest_sq.outerjoin(
                tax_pct_sq,
                tax_pct_sq.c.proj_id == latest_sq.c.proj_id,
            )
        )

        totals_row = (await self.db.execute(totals_stmt)).one()

        return DashboardKpiTotals(
            total_cotizado_con_impuestos=Decimal(str(totals_row.total_billed or 0)),
            costo_total_operacional=Decimal(str(totals_row.total_cost or 0)),
            margen_neto_total=Decimal(str(totals_row.total_margin or 0)),
            numero_propuestas_realizadas=int(totals_row.total_count or 0),
            numero_propuestas_ganadas=int(totals_row.won_count or 0),
        )
