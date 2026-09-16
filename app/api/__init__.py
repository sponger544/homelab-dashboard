"""API routes for the dashboard."""
from .dashboard import router as dashboard_router
from .admin import router as admin_router
from .wizard import router as wizard_router

__all__ = ["dashboard_router", "admin_router", "wizard_router"]
