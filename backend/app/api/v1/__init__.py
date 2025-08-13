"""
API v1 router for BeSunny.ai Python backend.
Includes all v1 API endpoints and sub-routers.
"""

from fastapi import APIRouter

from . import documents, projects, emails, drive, calendar, classification, attendee

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
            "/attendee"
        ]
    }
