"""
Pydantic schemas for request/response validation
"""

from app.schemas.auth import (
    GoogleConnectRequest,
    GoogleLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import ErrorResponse, ResponseBase
from app.schemas.cost import (
    CostFixedCreate,
    CostFixedListResponse,
    CostFixedResponse,
    CostFixedUpdate,
)
from app.schemas.insight import (
    AIAdvisorRequest,
    AIAdvisorResponse,
)
from app.schemas.integration import (
    GoogleSheetsSyncRequest,
    GoogleSheetsSyncResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectCreateWithQuote,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    QuoteItemCreate,
    QuoteItemResponse,
    QuoteResponse,
    QuoteResponseWithItems,
)
from app.schemas.quote import (
    BlendedCostRateResponse,
    CurrencyInfo,
    QuoteCalculateRequest,
    QuoteCalculateResponse,
)
from app.schemas.quote import (
    QuoteItemCreate as QuoteItemCreateBase,
)
from app.schemas.quote import (
    QuoteItemResponse as QuoteItemResponseBase,
)
from app.schemas.service import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
)
from app.schemas.team import (
    TeamMemberCreate,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberUpdate,
)

__all__ = [
    # Cost schemas
    "CostFixedCreate",
    "CostFixedUpdate",
    "CostFixedResponse",
    "CostFixedListResponse",
    # Team schemas
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamMemberResponse",
    "TeamMemberListResponse",
    # Service schemas
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceListResponse",
    # Quote schemas
    "QuoteItemCreateBase",
    "QuoteCalculateRequest",
    "QuoteCalculateResponse",
    "BlendedCostRateResponse",
    "CurrencyInfo",
    "QuoteItemResponseBase",
    # Project schemas
    "ProjectCreate",
    "ProjectCreateWithQuote",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "QuoteResponse",
    "QuoteResponseWithItems",
    "QuoteItemCreate",
    "QuoteItemResponse",
    # Auth schemas
    "GoogleLoginRequest",
    "GoogleConnectRequest",
    "TokenResponse",
    "UserResponse",
    # Integration schemas
    "GoogleSheetsSyncRequest",
    "GoogleSheetsSyncResponse",
    # Insight schemas
    "AIAdvisorRequest",
    "AIAdvisorResponse",
    # Common schemas
    "ResponseBase",
    "ErrorResponse",
]
