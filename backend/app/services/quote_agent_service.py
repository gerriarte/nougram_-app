"""
Quote Agent Service — orchestrates the conversational quote flow.

Golden rule (anti-hallucination): the LLM only picks services from the tenant
catalog and proposes quantities (hours/quantity). Price, cost and margin are
ALWAYS computed by the deterministic engine (``calculate_quote_totals_enhanced``).
The model never emits final amounts; it only produces inputs the engine validates.
"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced
from app.models.organization import Organization
from app.repositories.factory import RepositoryFactory
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

DEFAULT_MINIMUM_MARGIN = 0.15
MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = """Eres un asistente experto en cotizaciones para agencias digitales (Nougram).

Tu trabajo: a partir del brief del usuario, proponer una cotización usando SOLO los \
servicios del catálogo del tenant y estimar las horas (o cantidad) por servicio.

REGLAS CRÍTICAS:
- NUNCA inventes precios, costos ni márgenes. Esos SIEMPRE los calcula el motor \
determinista mediante la herramienta `propose_quote`.
- Solo puedes usar servicios que existan en el catálogo (usa `list_services` para verlos).
- Haz pocas preguntas dirigidas (tipo de proyecto, cliente, alcance/complejidad, plazos) \
y en cuanto tengas suficiente contexto, llama a `propose_quote` con tu estimación de horas.
- Cuando el usuario pida ajustes ("subí diseño a 100h", "sacá SEO"), vuelve a llamar a \
`propose_quote` con los items actualizados.
- Responde SIEMPRE en español, de forma breve y concreta. Explica brevemente el porqué \
de las horas propuestas.
- NO confirmes ni crees la cotización tú mismo: el usuario la crea con el botón "Crear \
borrador". Solo estima.
"""


class QuoteAgentService:
    """Conversational quote agent bound to a single tenant."""

    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self.service_repo = RepositoryFactory.create_service_repository(db, organization_id)
        self.client = ai_service.client
        self.model = ai_service.model

    def is_available(self) -> bool:
        return self.client is not None

    # ------------------------------------------------------------------ context

    async def _load_catalog(self) -> list[dict]:
        """Read-only tenant service catalog for the model (only fields it needs)."""
        services = await self.service_repo.get_all_active()
        catalog = []
        for svc in services:
            catalog.append(
                {
                    "service_id": svc.id,
                    "name": svc.name,
                    "description": svc.description,
                    "pricing_type": svc.pricing_type or "hourly",
                    "default_margin_target": float(svc.default_margin_target or 0),
                    "fixed_price": float(svc.fixed_price) if svc.fixed_price is not None else None,
                    "recurring_price": float(svc.recurring_price)
                    if svc.recurring_price is not None
                    else None,
                    "billing_frequency": svc.billing_frequency,
                }
            )
        return catalog

    async def _get_currency_and_rate(self) -> tuple[str, float]:
        from app.services.settings_service import SettingsService

        settings_service = SettingsService(self.db)
        (
            primary_currency,
            social_config,
        ) = await settings_service.get_organization_currency_and_social_config(self.organization_id)
        blended_rate = await calculate_blended_cost_rate(
            self.db,
            primary_currency=primary_currency,
            tenant_id=self.organization_id,
            social_charges_config=social_config,
        )
        return primary_currency, float(blended_rate)

    async def _get_minimum_margin_threshold(self) -> float:
        result = await self.db.execute(
            select(Organization).where(Organization.id == self.organization_id)
        )
        org = result.scalar_one_or_none()
        settings_obj = getattr(org, "settings", None) or {}
        if not isinstance(settings_obj, dict):
            return DEFAULT_MINIMUM_MARGIN
        try:
            threshold = float(settings_obj.get("minimum_margin_threshold", DEFAULT_MINIMUM_MARGIN))
        except (TypeError, ValueError):
            return DEFAULT_MINIMUM_MARGIN
        if threshold < 0 or threshold > 1:
            return DEFAULT_MINIMUM_MARGIN
        return threshold

    # ----------------------------------------------------------------- estimate

    def _normalize_items(self, raw_items: list[dict]) -> list[dict]:
        """Coerce LLM-provided items into the engine's item-dict shape."""
        items: list[dict] = []
        for raw in raw_items or []:
            try:
                service_id = int(raw["service_id"])
            except (KeyError, TypeError, ValueError):
                continue
            estimated_hours = raw.get("estimated_hours")
            quantity = raw.get("quantity")
            items.append(
                {
                    # Clave estable: el agente puede proponer dos ítems del mismo
                    # servicio y el breakdown no debe colapsarlos.
                    "item_key": len(items),
                    "service_id": service_id,
                    "estimated_hours": float(estimated_hours)
                    if estimated_hours is not None
                    else None,
                    "quantity": float(quantity) if quantity is not None else 1.0,
                    "pricing_type": raw.get("pricing_type"),
                    "fixed_price": raw.get("fixed_price"),
                    "recurring_price": raw.get("recurring_price"),
                    "billing_frequency": raw.get("billing_frequency"),
                    "project_value": raw.get("project_value"),
                }
            )
        return items

    async def compute_estimate(
        self, raw_items: list[dict], target_margin_percentage: float | None = None
    ) -> dict:
        """Run the deterministic engine on proposed items. No persistence, no credit.

        Returns an EstimateBreakdown-shaped dict plus the normalized input items.
        """
        items = self._normalize_items(raw_items)
        if not items:
            return {
                "items": [],
                "total_internal_cost": 0.0,
                "total_client_price": 0.0,
                "margin_percentage": 0.0,
                "target_margin_percentage": target_margin_percentage,
                "minimum_margin_threshold": await self._get_minimum_margin_threshold(),
                "below_minimum_margin": False,
                "proposal_items": [],
            }

        currency, blended_rate = await self._get_currency_and_rate()
        totals = await calculate_quote_totals_enhanced(
            self.db,
            items,
            blended_rate,
            tax_ids=[],
            expenses=None,
            target_margin_percentage=target_margin_percentage,
            currency=currency,
            organization_id=self.organization_id,
        )

        # Merge proposed hours/quantity back into the breakdown for display.
        # Se indexa por item_key (no por service_id) para no mezclar dos ítems que
        # comparten servicio.
        items_by_key = {item["item_key"]: item for item in items}

        breakdown_items = []
        for entry in totals.get("items", []):
            sid = entry.get("service_id")
            source_item = items_by_key.get(entry.get("item_key"), {})
            breakdown_items.append(
                {
                    "service_id": sid,
                    "service_name": entry.get("service_name"),
                    "pricing_type": entry.get("pricing_type"),
                    "estimated_hours": source_item.get("estimated_hours"),
                    "quantity": source_item.get("quantity"),
                    "internal_cost": float(entry.get("internal_cost", 0) or 0),
                    "client_price": float(entry.get("client_price", 0) or 0),
                    "margin_percentage": float(entry.get("margin_percentage", 0) or 0),
                }
            )

        margin = float(totals.get("margin_percentage", 0) or 0)
        threshold = await self._get_minimum_margin_threshold()
        return {
            "items": breakdown_items,
            "total_internal_cost": float(totals.get("total_internal_cost", 0) or 0),
            "total_client_price": float(totals.get("total_client_price", 0) or 0),
            "margin_percentage": margin,
            "target_margin_percentage": target_margin_percentage,
            "minimum_margin_threshold": threshold,
            "below_minimum_margin": bool(
                totals.get("total_client_price", 0) and margin < threshold
            ),
            "proposal_items": items,
        }

    # ---------------------------------------------------------------- tool loop

    @staticmethod
    def _tools_schema() -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_services",
                    "description": (
                        "Devuelve el catálogo de servicios activos del tenant "
                        "(id, nombre, tipo de pricing, margen objetivo)."
                    ),
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "propose_quote",
                    "description": (
                        "Calcula el desglose real (costo/precio/margen) con el motor "
                        "determinista para los items propuestos. NO persiste nada."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "service_id": {"type": "integer"},
                                        "estimated_hours": {"type": "number"},
                                        "quantity": {"type": "number"},
                                        "pricing_type": {"type": "string"},
                                    },
                                    "required": ["service_id"],
                                },
                            }
                        },
                        "required": ["items"],
                    },
                },
            },
        ]

    async def process_message(self, history: list[dict], user_content: str) -> dict:
        """Run one conversational turn with tool-calling.

        Args:
            history: prior turns as ``[{"role": "user"|"assistant", "content": str}]``.
            user_content: the new user message.

        Returns dict with ``content`` (assistant text), ``estimate`` (breakdown or
        None), ``proposal_items`` (engine input for the estimate or None), and
        aggregated ``usage``.
        """
        if not self.is_available():
            return {
                "content": "El servicio de IA no está configurado. Contacta al administrador.",
                "estimate": None,
                "proposal_items": None,
                "usage": None,
            }

        catalog = await self._load_catalog()
        grounding = await self.build_historical_grounding()
        system_content = SYSTEM_PROMPT
        system_content += (
            f"\n\nCATÁLOGO DISPONIBLE (JSON):\n{json.dumps(catalog, ensure_ascii=False)}"
        )
        if grounding:
            system_content += f"\n\nCONTEXTO HISTÓRICO DEL TENANT:\n{grounding}"

        messages: list = [{"role": "system", "content": system_content}]
        for turn in history:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})

        tools = self._tools_schema()
        usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        estimate: dict | None = None

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1200,
            )
            if response.usage:
                usage_totals["prompt_tokens"] += response.usage.prompt_tokens
                usage_totals["completion_tokens"] += response.usage.completion_tokens
                usage_totals["total_tokens"] += response.usage.total_tokens

            msg = response.choices[0].message
            if not msg.tool_calls:
                usage_totals["estimated_cost"] = round(
                    (usage_totals["prompt_tokens"] / 1000) * 0.01
                    + (usage_totals["completion_tokens"] / 1000) * 0.03,
                    4,
                )
                return {
                    "content": msg.content or "",
                    "estimate": estimate,
                    "proposal_items": estimate.get("proposal_items") if estimate else None,
                    "usage": usage_totals,
                }

            # Append assistant tool-call message, then resolve each tool call.
            messages.append(msg.model_dump(exclude_none=True))
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if name == "list_services":
                    result = {"services": catalog}
                elif name == "propose_quote":
                    estimate = await self.compute_estimate(args.get("items", []))
                    # Do not leak internal engine-input back to the model.
                    result = {k: v for k, v in estimate.items() if k != "proposal_items"}
                else:
                    result = {"error": f"Unknown tool: {name}"}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Tool-iteration budget exhausted; return best-effort with the last estimate.
        usage_totals["estimated_cost"] = round(
            (usage_totals["prompt_tokens"] / 1000) * 0.01
            + (usage_totals["completion_tokens"] / 1000) * 0.03,
            4,
        )
        return {
            "content": "He preparado una estimación; revisá el desglose a la derecha.",
            "estimate": estimate,
            "proposal_items": estimate.get("proposal_items") if estimate else None,
            "usage": usage_totals,
        }

    # ------------------------------------------------------------- feedback loop

    async def build_historical_grounding(self, limit: int = 5) -> str:
        """Summarize the tenant's won quotes as few-shot grounding for the prompt.

        In-context retrieval (not fine-tuning): shows which service/hour mixes
        have converted for this tenant so the agent proposes closer to reality.
        """
        from app.models.project import Project, Quote, QuoteItem
        from app.models.service import Service

        try:
            result = await self.db.execute(
                select(Project)
                .where(
                    Project.organization_id == self.organization_id,
                    Project.status == "Won",
                    Project.deleted_at.is_(None),
                    Project.accepted_quote_id.isnot(None),
                )
                .order_by(Project.updated_at.desc())
                .limit(limit)
            )
            projects = result.scalars().all()
            if not projects:
                return ""

            lines: list[str] = []
            for project in projects:
                quote_result = await self.db.execute(
                    select(Quote).where(Quote.id == project.accepted_quote_id)
                )
                quote = quote_result.scalar_one_or_none()
                if not quote:
                    continue
                items_result = await self.db.execute(
                    select(QuoteItem, Service.name)
                    .join(Service, Service.id == QuoteItem.service_id, isouter=True)
                    .where(QuoteItem.quote_id == quote.id)
                )
                parts = []
                for item, service_name in items_result.all():
                    hours = item.estimated_hours
                    label = item.custom_service_name or service_name or "servicio"
                    if hours:
                        parts.append(f"{label}: {float(hours):g}h")
                    else:
                        parts.append(str(label))
                if parts:
                    margin = float(quote.margin_percentage or 0)
                    lines.append(f"- Ganada ({margin:.0%} margen): " + ", ".join(parts))
            return "\n".join(lines)
        except Exception as exc:  # pragma: no cover - grounding is best-effort
            logger.warning(f"Failed to build historical grounding: {exc}")
            return ""

    async def get_feedback_dataset(self, limit: int = 200) -> list[dict]:
        """Join agent-originated deals: proposed snapshot vs final outcome."""
        from app.models.project import Project, Quote
        from app.models.proposal import ProposalClientLink

        conv_repo = RepositoryFactory.create_agent_conversation_repository(
            self.db, self.organization_id
        )
        conversations = await conv_repo.list_by_organization(limit=limit)

        dataset: list[dict] = []
        for conv in conversations:
            if conv.project_id is None:
                continue
            project_result = await self.db.execute(
                select(Project).where(
                    Project.id == conv.project_id,
                    Project.organization_id == self.organization_id,
                )
            )
            project = project_result.scalar_one_or_none()
            if project is None:
                continue

            final_price = None
            final_margin = None
            if conv.quote_id is not None:
                quote_result = await self.db.execute(select(Quote).where(Quote.id == conv.quote_id))
                quote = quote_result.scalar_one_or_none()
                if quote is not None:
                    final_price = (
                        float(quote.total_client_price)
                        if quote.total_client_price is not None
                        else None
                    )
                    final_margin = (
                        float(quote.margin_percentage)
                        if quote.margin_percentage is not None
                        else None
                    )

            link_result = await self.db.execute(
                select(ProposalClientLink)
                .where(ProposalClientLink.project_id == project.id)
                .order_by(ProposalClientLink.id.desc())
            )
            link = link_result.scalars().first()

            outcome = "pending"
            decision_comment = None
            if project.status == "Won":
                outcome = "won"
            elif project.status == "Lost":
                outcome = "lost"
            if link is not None and link.status in ("accepted", "rejected"):
                outcome = link.status
                decision_comment = link.decision_comment

            dataset.append(
                {
                    "conversation_id": conv.id,
                    "project_id": conv.project_id,
                    "quote_id": conv.quote_id,
                    "status": conv.status,
                    "project_status": project.status,
                    "outcome": outcome,
                    "decision_comment": decision_comment,
                    "proposed_snapshot": conv.proposed_snapshot,
                    "final_total_client_price": final_price,
                    "final_margin_percentage": final_margin,
                }
            )
        return dataset
