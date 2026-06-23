"""Dashboard REST API router — mobile and admin KPIs."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from .service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/mobile")
async def get_mobile_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Quick KPIs for mobile operators."""
    return await DashboardService(db, current_user).get_mobile_dashboard()


@router.get("/admin")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin/supervisor KPIs with status distribution and trends."""
    return await DashboardService(db, current_user).get_admin_dashboard()
