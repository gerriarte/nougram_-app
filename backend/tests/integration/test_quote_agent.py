"""
Integration tests for the Quote Agent (chat) module.

Covers gating (super-admin-only module toggle + feature flag), multi-tenant
isolation, the message → deterministic-estimate flow (mocked OpenAI), and
confirm → draft Project+Quote with agent provenance.
"""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.team import TeamMember
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.credit_service import CreditService
from tests.auth_helpers import get_auth_headers

# --------------------------------------------------------------------------- fakes


class _FakeToolCall:
    def __init__(self, call_id: str, name: str, arguments: dict):
        self.id = call_id
        self.function = SimpleNamespace(name=name, arguments=json.dumps(arguments))


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none: bool = False):
        data = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in self.tool_calls
            ]
        return data


class _FakeResponse:
    def __init__(self, message: _FakeMessage):
        self.choices = [SimpleNamespace(message=message)]
        self.usage = SimpleNamespace(prompt_tokens=100, completion_tokens=50, total_tokens=150)


class _FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self._index = 0

    async def create(self, **kwargs):
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response


class _FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


def _propose_then_reply(service_id: int, hours: float = 40.0):
    """Fake OpenAI flow: first a propose_quote tool call, then a final text reply."""
    tool_call = _FakeToolCall(
        "call_1",
        "propose_quote",
        {"items": [{"service_id": service_id, "estimated_hours": hours}]},
    )
    return _FakeClient(
        [
            _FakeResponse(_FakeMessage(content=None, tool_calls=[tool_call])),
            _FakeResponse(_FakeMessage(content="Propuse una estimación. Revisá el desglose.")),
        ]
    )


# ------------------------------------------------------------------------ fixtures


async def _make_org(db_session: AsyncSession, *, quote_agent: bool) -> Organization:
    unique = uuid.uuid4().hex[:8]
    org = Organization(
        name=f"Org {unique}",
        slug=f"org-{unique}",
        subscription_plan="professional",
        subscription_status="active",
        settings={"modules": {"quote_agent": quote_agent}} if quote_agent else {},
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


async def _make_user(db_session: AsyncSession, org: Organization, role: str = "owner") -> User:
    unique = uuid.uuid4().hex[:8]
    user = User(
        email=f"{role}_{unique}@test.com",
        full_name=f"{role} user",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
        role=role,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_service(db_session: AsyncSession, org: Organization) -> Service:
    service = Service(
        name="Diseño",
        description="Servicio de diseño",
        default_margin_target=0.40,
        is_active=True,
        pricing_type="hourly",
        organization_id=org.id,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


async def _seed_costs_and_team(db_session: AsyncSession, org: Organization, owner: User) -> None:
    """Seed a fixed cost + team member so the blended cost rate is > 0."""
    db_session.add(
        CostFixed(
            name="Software",
            amount_monthly=1000.0,
            currency="USD",
            category="Overhead",
            organization_id=org.id,
        )
    )
    db_session.add(
        TeamMember(
            user_id=owner.id,
            name="Diseñador",
            role="Designer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=org.id,
        )
    )
    await db_session.commit()


# --------------------------------------------------------------------------- tests


@pytest.mark.integration
class TestQuoteAgentGating:
    async def test_module_off_hides_flag_and_blocks_endpoints(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        org = await _make_org(db_session, quote_agent=False)
        owner = await _make_user(db_session, org)
        headers = get_auth_headers(owner)

        features = await async_client.get("/api/v1/settings/features", headers=headers)
        assert features.status_code == 200
        assert features.json()["quote_agent_enabled"] is False

        blocked = await async_client.post("/api/v1/quote-agent/conversations", headers=headers)
        assert blocked.status_code == 403

    async def test_org_admin_cannot_toggle_module(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        org = await _make_org(db_session, quote_agent=False)
        owner = await _make_user(db_session, org, role="owner")
        headers = get_auth_headers(owner)

        response = await async_client.put(
            f"/api/v1/organizations/{org.id}/modules",
            json={"quote_agent": True},
            headers=headers,
        )
        assert response.status_code == 403

    async def test_super_admin_enables_module(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        org = await _make_org(db_session, quote_agent=False)
        owner = await _make_user(db_session, org, role="owner")
        super_admin = await _make_user(db_session, org, role="super_admin")

        toggle = await async_client.put(
            f"/api/v1/organizations/{org.id}/modules",
            json={"quote_agent": True},
            headers=get_auth_headers(super_admin),
        )
        assert toggle.status_code == 200

        features = await async_client.get(
            "/api/v1/settings/features", headers=get_auth_headers(owner)
        )
        assert features.json()["quote_agent_enabled"] is True

        created = await async_client.post(
            "/api/v1/quote-agent/conversations", headers=get_auth_headers(owner)
        )
        assert created.status_code == 200
        assert created.json()["id"] > 0


@pytest.mark.integration
class TestQuoteAgentIsolation:
    async def test_conversation_not_visible_across_tenants(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        org_a = await _make_org(db_session, quote_agent=True)
        org_b = await _make_org(db_session, quote_agent=True)
        user_a = await _make_user(db_session, org_a)
        user_b = await _make_user(db_session, org_b)

        created = await async_client.post(
            "/api/v1/quote-agent/conversations", headers=get_auth_headers(user_a)
        )
        conversation_id = created.json()["id"]

        cross = await async_client.get(
            f"/api/v1/quote-agent/conversations/{conversation_id}",
            headers=get_auth_headers(user_b),
        )
        assert cross.status_code == 404


@pytest.mark.integration
class TestQuoteAgentFlow:
    async def test_message_returns_deterministic_estimate(
        self, async_client: AsyncClient, db_session: AsyncSession, test_settings
    ):
        org = await _make_org(db_session, quote_agent=True)
        owner = await _make_user(db_session, org)
        service = await _make_service(db_session, org)
        await _seed_costs_and_team(db_session, org, owner)
        headers = get_auth_headers(owner)

        created = await async_client.post("/api/v1/quote-agent/conversations", headers=headers)
        conversation_id = created.json()["id"]

        fake = _propose_then_reply(service.id, hours=40.0)
        with (
            patch.object(ai_service, "client", fake),
            patch.object(ai_service, "model", "gpt-4o-mini"),
        ):
            response = await async_client.post(
                f"/api/v1/quote-agent/conversations/{conversation_id}/messages",
                json={"content": "Necesito una web con diseño"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["assistant_message"]["role"] == "assistant"
        assert data["estimate"] is not None
        item_ids = [item["service_id"] for item in data["estimate"]["items"]]
        assert service.id in item_ids

    async def test_confirm_creates_draft_with_provenance(
        self, async_client: AsyncClient, db_session: AsyncSession, test_settings
    ):
        org = await _make_org(db_session, quote_agent=True)
        owner = await _make_user(db_session, org)
        service = await _make_service(db_session, org)
        await _seed_costs_and_team(db_session, org, owner)
        headers = get_auth_headers(owner)

        account = await CreditService.get_or_create_credit_account(org.id, db_session)
        account.credits_available = 100
        await db_session.commit()

        created = await async_client.post("/api/v1/quote-agent/conversations", headers=headers)
        conversation_id = created.json()["id"]

        fake = _propose_then_reply(service.id, hours=40.0)
        with (
            patch.object(ai_service, "client", fake),
            patch.object(ai_service, "model", "gpt-4o-mini"),
        ):
            await async_client.post(
                f"/api/v1/quote-agent/conversations/{conversation_id}/messages",
                json={"content": "Cotizá diseño"},
                headers=headers,
            )

        confirm = await async_client.post(
            f"/api/v1/quote-agent/conversations/{conversation_id}/confirm",
            json={"client_name": "ACME", "allow_low_margin": True},
            headers=headers,
        )
        assert confirm.status_code == 200, confirm.text
        body = confirm.json()
        assert body["project_id"] > 0
        assert body["quote_id"] > 0

        project = (
            await db_session.execute(select(Project).where(Project.id == body["project_id"]))
        ).scalar_one()
        assert project.status == "Draft"
        assert project.source == "quote_agent"

        # Confirming twice is rejected.
        again = await async_client.post(
            f"/api/v1/quote-agent/conversations/{conversation_id}/confirm",
            json={"client_name": "ACME"},
            headers=headers,
        )
        assert again.status_code == 400

    async def test_confirm_without_proposal_is_rejected(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        org = await _make_org(db_session, quote_agent=True)
        owner = await _make_user(db_session, org)
        headers = get_auth_headers(owner)

        created = await async_client.post("/api/v1/quote-agent/conversations", headers=headers)
        conversation_id = created.json()["id"]

        confirm = await async_client.post(
            f"/api/v1/quote-agent/conversations/{conversation_id}/confirm",
            json={"client_name": "ACME"},
            headers=headers,
        )
        assert confirm.status_code == 400
