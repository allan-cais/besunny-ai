"""
API v1 router for BeSunny.ai Python backend.
Optimized for maximum efficiency and reliability.
"""

from fastapi import APIRouter

from . import documents, projects, emails, drive, calendar, classification, attendee, ai, embeddings, meeting_intelligence, microservices, enterprise, webhooks, auth, user, drive_subscription, ai_orchestration, performance_monitoring, sync, gmail_watches, oauth, gmail, admin, rag_agent

# Create the main router
router = APIRouter()

# Core Service Routers - Phase 1
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(user.router, prefix="/user", tags=["user-management"])
router.include_router(projects.router, prefix="/projects", tags=["project-management"])

# AI Service Routers - Phase 2
router.include_router(ai.router, prefix="/ai", tags=["ai-services"])
router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
router.include_router(classification.router, prefix="/classification", tags=["classification"])
router.include_router(meeting_intelligence.router, prefix="/meeting-intelligence", tags=["meeting-intelligence"])
router.include_router(ai_orchestration.router, prefix="/ai-orchestration", tags=["ai-orchestration"])
router.include_router(rag_agent.router, prefix="/rag-agent", tags=["rag-agent"])

# Integration Routers - Phase 3
router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
router.include_router(drive.router, prefix="/drive", tags=["drive"])
router.include_router(emails.router, prefix="/emails", tags=["emails"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(gmail_watches.router, prefix="/gmail-watches", tags=["gmail-watches"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
router.include_router(gmail.router, prefix="/gmail", tags=["gmail"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Enterprise Routers - Phase 4
router.include_router(enterprise.router, prefix="/enterprise", tags=["enterprise"])
router.include_router(performance_monitoring.router, prefix="/performance", tags=["performance"])

# Utility Routers - Phase 5
router.include_router(sync.router, prefix="/sync", tags=["sync"])
router.include_router(attendee.router, prefix="/attendee", tags=["attendee"])

# Utility Functions Router - Phase 7
router.include_router(drive_subscription.router, prefix="/drive-subscription", tags=["drive-subscription"])

# Lightweight health check endpoint
@router.get("/health")
async def health_check():
    """API v1 health check - lightweight and fast."""
    return {
        "status": "healthy",
        "version": "v1",
        "message": "API v1 is operational",
        "endpoints": [
            "/documents",
            "/projects", 
            "/emails",
            "/drive",
            "/calendar",
            "/classification",
            "/attendee",
            "/ai",
            "/embeddings",
            "/meeting-intelligence",
            "/ai-orchestration",
            "/microservices",
            "/webhooks",
            "/enterprise",
            "/performance",
            "/auth",
            "/user",
            "/gmail-watches",
            "/drive-subscription",
            "/oauth",
            "/gmail",
            "/admin"
        ]
    }
