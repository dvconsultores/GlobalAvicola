"""SAP Integration REST API router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...dependencies import get_current_user, require_permission
from . import schemas
from .service import SapService

router = APIRouter(prefix="/sap", tags=["SAP Integration"])


# ============================================================
# SAP References
# ============================================================

@router.post("/references/import", status_code=201)
async def import_sap_references(
    data: schemas.SapReferenceImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Bulk import SAP references (manual mode)."""
    return await SapService(db, current_user).import_references(data)


@router.get("/references")
async def list_sap_references(
    ref_type: Optional[str] = Query(None, description="Filter by reference type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """List SAP references."""
    refs, total = await SapService(db, current_user).list_references(
        ref_type=ref_type, limit=limit, offset=offset
    )
    return {"references": refs, "total": total}


# ============================================================
# Consolidation
# ============================================================

@router.post("/consolidate", status_code=201)
async def consolidate_approved_events(
    data: Optional[schemas.ConsolidateRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Consolidate approved events into SAP-ready movements."""
    if data is None:
        data = schemas.ConsolidateRequest()
    return await SapService(db, current_user).consolidate_approved(
        lot_id=data.lot_id, event_type=data.event_type,
        date_from=data.date_from, date_to=data.date_to,
    )


@router.get("/consolidated")
async def list_consolidated(
    lot_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """List consolidated movements."""
    items, total = await SapService(db, current_user).list_consolidated(
        lot_id=lot_id, limit=limit, offset=offset
    )
    return {"consolidated": items, "total": total}


# ============================================================
# SAP Export
# ============================================================

@router.post("/export", response_model=schemas.SapExportResponse)
async def export_to_sap(
    data: Optional[schemas.SapExportRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Export consolidated movements to SAP."""
    if data is None:
        data = schemas.SapExportRequest()
    return await SapService(db, current_user).export_to_sap(
        consolidated_ids=data.consolidated_ids, file_name=data.file_name,
    )


@router.post("/retry")
async def retry_failed_payloads(
    data: Optional[schemas.SapRetryRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Retry failed SAP payloads."""
    if data is None:
        data = schemas.SapRetryRequest()
    return await SapService(db, current_user).retry_failed(
        payload_ids=data.payload_ids, max_retries=data.max_retries,
    )


# ============================================================
# Sync Jobs & Payloads
# ============================================================

@router.get("/sync/jobs")
async def list_sync_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """List SAP sync jobs."""
    jobs, total = await SapService(db, current_user).list_sync_jobs(limit=limit, offset=offset)
    return {"jobs": jobs, "total": total}


@router.get("/payloads")
async def list_payloads(
    status: Optional[str] = Query(None, description="Filter by payload status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """List SAP payloads."""
    items, total = await SapService(db, current_user).list_payloads(
        status=status, limit=limit, offset=offset
    )
    return {"payloads": items, "total": total}


@router.get("/errors")
async def list_sap_errors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """List SAP errors (failed payloads)."""
    return await SapService(db, current_user).list_errors(limit=limit, offset=offset)


# ============================================================
# Health
# ============================================================

@router.get("/connection-check")
async def check_sap_connection(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """Estado real del adaptador SAP en uso.

    GA-REM-010: `delivers_to_sap` indica si el adaptador realiza una entrega
    verificada. Un adaptador manual o simulado informa `false` y no afirma
    conectividad con un sistema SAP real.
    """
    adapter = SapService(db, current_user).get_adapter()
    is_connected = await adapter.check_connection()
    return {
        "connected": is_connected,
        "adapter": await adapter.get_adapter_name(),
        "delivers_to_sap": adapter.delivers_to_sap,
        "mode": "manual" if not adapter.delivers_to_sap else "real",
    }
