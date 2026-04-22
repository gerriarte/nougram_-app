"""
Database models
"""

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

# Roles and DeleteRequest disabled during rollback
# from app.models.role import DeleteRequest, UserRole, DeleteRequestStatus

__all__ = [
    "User",
    "CostFixed",
    "TeamMember",
    "Service",
    "Client",
    "Project",
    "Quote",
    "QuoteItem",
    "QuoteItemAllocation",
    "QuoteItemCellAssignment",
    "AgencySettings",
    "Tax",
    "Organization",
    "Subscription",
    "BillingRequest",
    "IndustryTemplate",
    "AuditLog",
    "CreditAccount",
    "CreditTransaction",
    "Invitation",
    "AnnualSalesProjection",
    "AnnualSalesProjectionEntry",
    "EquipmentAmortization",
    "ProposalDocument",
    "ProposalClientLink",
    "AIUsageEvent",
    "FinancialLedgerEvent",
    "TeamGroup",
    "TeamCell",
    "TeamCellVersion",
    "TeamCellMemberVersion",
    "CapacityCommitment",
    "CapacityEvent",
    # "DeleteRequest",
    # "UserRole",
    # "DeleteRequestStatus",
]
