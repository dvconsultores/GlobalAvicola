"""Dashboard REST API router — mobile and admin KPIs."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from .service import DashboardService

router = APIRouter(route_class=RutaTransaccional, prefix="/dashboard", tags=["Dashboard"])


@router.get("/mobile")
async def get_mobile_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboard", "read")),
):
    """Quick KPIs for mobile operators."""
    return await DashboardService(db, current_user).get_mobile_dashboard()


@router.get("/admin")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("dashboard", "read")),
):
    """Admin/supervisor KPIs with status distribution and trends."""
    return await DashboardService(db, current_user).get_admin_dashboard()
