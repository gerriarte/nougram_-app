"""
Main API router for v1
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, costs, team, services, quotes, projects, insights, integrations, settings, taxes, maintenance, delete_requests, users, ai, organizations, templates, billing, stripe_webhooks, credits, support, invitations, expenses, sales_projection, annual_projection, onboarding

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(costs.router, prefix="/settings", tags=["costs"])
api_router.include_router(team.router, prefix="/settings", tags=["team"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(expenses.router, prefix="/projects", tags=["expenses"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(taxes.router, prefix="/taxes", tags=["taxes"])
api_router.include_router(maintenance.router, prefix="", tags=["maintenance"])
api_router.include_router(delete_requests.router, prefix="/delete-requests", tags=["delete-requests"])
api_router.include_router(users.router, prefix="", tags=["users"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(invitations.router, tags=["Invitations"])  # Uses prefix from router definition
api_router.include_router(templates.router, tags=["templates"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(stripe_webhooks.router, prefix="/stripe", tags=["stripe-webhooks"])
api_router.include_router(credits.router, prefix="/credits", tags=["credits"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(sales_projection.router, prefix="/sales", tags=["sales-projection"])
api_router.include_router(annual_projection.router, prefix="/projections", tags=["annual-projection"])
