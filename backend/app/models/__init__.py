"""
Database models
"""

from app.models.agent_conversation import AgentConversation, AgentMessage
from app.models.ai_usage import AIUsageEvent
from app.models.annual_sales_projection import AnnualSalesProjection, AnnualSalesProjectionEntry
from app.models.audit_log import AuditLog
from app.models.billing_request import BillingRequest
from app.models.capacity import CapacityCommitment, CapacityEvent
from app.models.client import Client
from app.models.cost import CostFixed
from app.models.credit_account import CreditAccount
from app.models.credit_transaction import CreditTransaction
from app.models.equipment import EquipmentAmortization
from app.models.financial_ledger import FinancialLedgerEvent
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.project import (
    Project,
    Quote,
    QuoteItem,
    QuoteItemAllocation,
    QuoteItemCellAssignment,
)
from app.models.proposal import ProposalClientLink, ProposalDocument
from app.models.service import Service
from app.models.settings import AgencySettings
from app.models.subscription import Subscription
from app.models.tax import Tax
from app.models.team import TeamMember
from app.models.team_cells import TeamCell, TeamCellMemberVersion, TeamCellVersion, TeamGroup
from app.models.template import IndustryTemplate
from app.models.user import User
from app.models.vendor import Vendor

# Roles and DeleteRequest disabled during rollback
# from app.models.role import DeleteRequest, UserRole, DeleteRequestStatus

__all__ = [
    "AgentConversation",
    "AgentMessage",
    "AIUsageEvent",
    "AnnualSalesProjection",
    "AnnualSalesProjectionEntry",
    "AuditLog",
    "BillingRequest",
    "CapacityCommitment",
    "CapacityEvent",
    "Client",
    "CostFixed",
    "CreditAccount",
    "CreditTransaction",
    "EquipmentAmortization",
    "FinancialLedgerEvent",
    "AgencySettings",
    "IndustryTemplate",
    "Invitation",
    "Organization",
    "Project",
    "ProposalClientLink",
    "ProposalDocument",
    "Quote",
    "QuoteItem",
    "QuoteItemAllocation",
    "QuoteItemCellAssignment",
    "Service",
    "Subscription",
    "Tax",
    "TeamCell",
    "TeamCellMemberVersion",
    "TeamCellVersion",
    "TeamGroup",
    "TeamMember",
    "User",
    "Vendor",
    # "DeleteRequest",
    # "UserRole",
    # "DeleteRequestStatus",
]
