"""Audit REST API router — read-only, immutable."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
async def list_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    lot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("audit", "read")),
):
    """List audit logs with advanced filters. Read-only."""
    logs, total = await AuditService(db, current_user).list_logs(
        user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id,
        module=module, lot_id=lot_id, farm_id=farm_id,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )
    return {"logs": logs, "total": total}


@router.get("/{log_id}", response_model=schemas.AuditLogRead)
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("audit", "read")),
):
    """Get a single audit log entry."""
    return await AuditService(db, current_user).get_log(log_id)


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("audit", "read")),
):
    """Get complete audit timeline for a specific entity (chronological)."""
    logs = await AuditService(db, current_user).get_entity_timeline(entity_type, entity_id)
    return {"entity_type": entity_type, "entity_id": entity_id, "timeline": logs, "total_steps": len(logs)}
