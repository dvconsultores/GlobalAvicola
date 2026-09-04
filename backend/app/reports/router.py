"""Reports REST API router — KPIs, lot reports, SAP comparison."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user, require_permission
from .service import ReportsService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/kpis")
async def get_all_kpis(
    lot_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Get all KPI values (mortality, feed conversion, egg production, hatchery yield)."""
    return await ReportsService(db, current_user).get_all_kpis(lot_id=lot_id)


@router.get("/kpis/mortality")
async def get_mortality_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Calculate mortality rate for a lot."""
    return await ReportsService(db, current_user).get_kpi_mortality(lot_id)


@router.get("/kpis/feed-conversion")
async def get_feed_conversion_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Calculate feed conversion ratio for a lot."""
    return await ReportsService(db, current_user).get_kpi_feed_conversion(lot_id)


@router.get("/kpis/egg-production")
async def get_egg_production_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Calculate egg production KPIs for a lot."""
    return await ReportsService(db, current_user).get_kpi_egg_production(lot_id)


@router.get("/kpis/hatchery")
async def get_hatchery_kpi(
    lot_id: Optional[int] = Query(None),
    hatchery_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Calculate hatchery yield KPIs."""
    return await ReportsService(db, current_user).get_kpi_hatchery(lot_id=lot_id)


@router.get("/kpis/animal-welfare")
async def get_animal_welfare_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-01: Calculate animal welfare index for a lot."""
    return await ReportsService(db, current_user).get_kpi_animal_welfare(lot_id)


@router.get("/kpis/vaccination-efficiency")
async def get_vaccination_efficiency_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-02: Calculate vaccination efficiency for a lot."""
    return await ReportsService(db, current_user).get_kpi_vaccination_efficiency(lot_id)


@router.get("/kpis/transfer-efficiency")
async def get_transfer_efficiency_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-03: Calculate transfer efficiency (hatchery → broiler)."""
    return await ReportsService(db, current_user).get_kpi_transfer_efficiency(lot_id)


@router.get("/kpis/afcr")
async def get_afcr_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-04: Calculate Adjusted FCR for a lot."""
    return await ReportsService(db, current_user).get_kpi_afcr(lot_id)


@router.get("/kpis/production-index")
async def get_production_index_kpi(
    lot_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-05: Calculate Broiler Production Index for a lot."""
    return await ReportsService(db, current_user).get_kpi_production_index(lot_id)


@router.get("/kpi/ipe/{lot_id}")
async def get_kpi_ipe(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-06: European Production Index (IPE) = (Viabilidad × Ganancia Diaria × 100) / (FCR × 10)."""
    return await ReportsService(db, current_user).get_kpi_ipe(lot_id)


@router.get("/kpi/weight-uniformity/{lot_id}")
async def get_kpi_weight_uniformity(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """G-07: Weight uniformity (CV%) across weight_recording events for the lot."""
    return await ReportsService(db, current_user).get_kpi_weight_uniformity(lot_id)


@router.get("/lot/{lot_id}")
async def get_lot_report(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Generate complete report for a lot."""
    return await ReportsService(db, current_user).get_lot_report(lot_id)


@router.get("/sap-comparison")
async def get_sap_comparison(
    lot_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("reports", "read")),
):
    """Compare Global Avícola data vs SAP references."""
    return await ReportsService(db, current_user).get_sap_comparison(lot_id=lot_id)
