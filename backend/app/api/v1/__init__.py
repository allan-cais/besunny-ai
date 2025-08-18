"""
API v1 router for BeSunny.ai Python backend.
Includes all v1 API endpoints and sub-routers.
"""

from fastapi import APIRouter

from . import documents, projects, emails, drive, calendar, classification, attendee, ai, embeddings, meeting_intelligence, microservices, enterprise, webhooks, auth, user, gmail_watch, drive_subscription

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include all sub-routers
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(emails.router, prefix="/emails", tags=["emails"])
router.include_router(drive.router, prefix="/drive", tags=["drive"])
router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
router.include_router(classification.router, prefix="/classification", tags=["classification"])
router.include_router(attendee.router, prefix="/attendee", tags=["attendee"])

# AI Service Routers
router.include_router(ai.router, prefix="/ai", tags=["ai"])
router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
router.include_router(meeting_intelligence.router, prefix="/meeting-intelligence", tags=["meeting-intelligence"])

# Microservices Architecture Routers
router.include_router(microservices.router, tags=["microservices"])

# Webhook Routers
router.include_router(webhooks.router, tags=["webhooks"])

# Enterprise Features - Phase 4
router.include_router(enterprise.router, tags=["enterprise"])

# Authentication Router - Phase 5
router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Utility Functions Router - Phase 7
router.include_router(user.router, prefix="/user", tags=["user-utilities"])
router.include_router(gmail_watch.router, prefix="/gmail-watch", tags=["gmail-watch"])
router.include_router(drive_subscription.router, prefix="/drive-subscription", tags=["drive-subscription"])

# Health check endpoint
@router.get("/health")
async def health_check():
    """API v1 health check."""
    return {
        "status": "healthy",
        "version": "v1",
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
            "/microservices",
            "/webhooks",
            "/enterprise",
            "/auth",
            "/user",
            "/gmail-watch",
            "/drive-subscription"
        ]
    }
