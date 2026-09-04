"""REST API router for operational events — unified endpoint for 24 event types."""
import os
import uuid
from datetime import date
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import OperationsService

router = APIRouter(prefix="/operations", tags=["Operations"])

MEDIA_DIR = os.environ.get("MEDIA_DIR", "/app/media")
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def _service(db: AsyncSession, user: dict):
    return OperationsService(db, user)


# ============================================================
# Event Types Reference
# ============================================================

@router.get("/event-types", tags=["Operations"])
async def list_event_types():
    return schemas.ALL_EVENT_TYPES


# ============================================================
# CRUD
# ============================================================

@router.get("", response_model=list[schemas.OperationalEventRead])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(
        None,
        description="Estado, o varios separados por coma (p. ej. 'draft,registered')",
    ),
    registered_by_me: bool = Query(
        False, description="Solo los eventos registrados por el usuario autenticado"
    ),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    items, total = await _service(db, current_user).get_events(
        skip=skip, limit=limit, lot_id=lot_id, farm_id=farm_id,
        event_type=event_type, status=status,
        registered_by_me=registered_by_me,
        date_from=date_from, date_to=date_to,
    )
    return [schemas.OperationalEventRead.model_validate(item) for item in items]


@router.post("", response_model=schemas.OperationalEventRead, status_code=201)
async def create_event(
    data: schemas.OperationalEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "create")),
):
    event = await _service(db, current_user).create_event(data)
    return schemas.OperationalEventRead.model_validate(event)


# ─── Alertas ──────────────────────────────────────────────────────────────────
# Estas rutas van ANTES de las que llevan `{event_id}`: FastAPI resuelve en orden de
# declaración, de modo que `/{event_id}` capturaba `/alerts` e intentaba interpretar
# "alerts" como un entero. El endpoint de alertas era inalcanzable (`R-38`).
# ============================================================

@router.get("/alerts", response_model=list[schemas.OperationalAlertRead])
async def list_alerts(
    lot_id: Optional[int] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    """Return auto-generated alerts filtered by lot and resolution status."""
    return await _service(db, current_user).get_alerts(
        lot_id=lot_id, is_resolved=is_resolved, skip=skip, limit=limit
    )


@router.patch("/alerts/{alert_id}/resolve", response_model=schemas.OperationalAlertRead)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "update")),
):
    """Mark an alert as resolved."""
    return await _service(db, current_user).resolve_alert(alert_id)


@router.get("/{event_id}", response_model=schemas.OperationalEventDetailRead)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    event = await _service(db, current_user).get_event(event_id)
    # Convert ORM object to dict excluding relationships to avoid Pydantic validation errors
    event_dict = {
        k: v for k, v in event.__dict__.items()
        if not k.startswith("_") and not k.startswith("__")
    }
    # Remove SQLAlchemy relationship/sa_instance_state attributes
    for rel_key in ("bird_movements", "egg_movements", "feed_movements",
                     "hatchery_params", "inspection_details", "egg_storage_records",
                     "evidences", "alerts"):
        event_dict.pop(rel_key, None)
    result = schemas.OperationalEventDetailRead.model_validate(event_dict, from_attributes=True)
    result.bird_movements = [schemas.BirdMovementSchema.model_validate(bm) for bm in event.bird_movements]
    result.egg_movements = [schemas.EggMovementSchema.model_validate(em) for em in event.egg_movements]
    result.feed_movements = [schemas.FeedMovementSchema.model_validate(fm) for fm in event.feed_movements]
    result.hatchery_params = [schemas.HatcheryParamsSchema.model_validate(hp) for hp in event.hatchery_params]
    result.inspection_details = [schemas.InspectionDetailSchema.model_validate(detail) for detail in event.inspection_details]
    return result


@router.put("/{event_id}", response_model=schemas.OperationalEventRead)
async def update_event(
    event_id: int,
    data: schemas.OperationalEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "update")),
):
    event = await _service(db, current_user).update_event(event_id, data)
    return schemas.OperationalEventRead.model_validate(event)


# ============================================================
# State Transitions
# ============================================================

@router.post("/{event_id}/submit", response_model=schemas.OperationalEventRead)
async def submit_to_review(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "create")),
):
    event = await _service(db, current_user).submit_to_review(event_id)
    return schemas.OperationalEventRead.model_validate(event)


@router.post("/{event_id}/cancel", response_model=schemas.OperationalEventRead)
async def cancel_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "create")),
):
    event = await _service(db, current_user).cancel_event(event_id)
    return schemas.OperationalEventRead.model_validate(event)


# ============================================================
# Evidence / Attachments
# ============================================================

@router.get("/{event_id}/evidences", response_model=list[schemas.EvidenceRead])
async def list_evidences(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    evidences = await _service(db, current_user).get_evidences(event_id)
    return [schemas.EvidenceRead.model_validate(e) for e in evidences]


@router.post("/{event_id}/evidences", response_model=schemas.EvidenceRead, status_code=201)
async def upload_evidence(
    event_id: int,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "create")),
):
    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Permitidos: jpg, png, gif, webp, pdf",
        )
    content = await file.read()
    if len(content) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx. 10 MB)")

    svc = _service(db, current_user)
    event = await svc.get_event(event_id)
    company_dir = os.path.join(MEDIA_DIR, "evidences", str(event.company_id), str(event_id))
    os.makedirs(company_dir, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    file_path = os.path.join(company_dir, safe_name)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    evidence_type = "photo" if (file.content_type or "").startswith("image/") else "document"
    evidence = await svc.create_evidence(
        event_id=event_id,
        file_name=file.filename or safe_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        evidence_type=evidence_type,
        description=description or None,
    )
    return schemas.EvidenceRead.model_validate(evidence)


@router.get("/{event_id}/evidences/{evidence_id}/download")
async def download_evidence(
    event_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    evidence = await _service(db, current_user).get_evidence_for_download(event_id, evidence_id)
    if not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    return FileResponse(
        evidence.file_path,
        filename=evidence.file_name,
        media_type=evidence.mime_type or "application/octet-stream",
    )


@router.delete("/{event_id}/evidences/{evidence_id}", status_code=204)
async def delete_evidence(
    event_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "delete")),
):
    await _service(db, current_user).delete_evidence(event_id, evidence_id)


# ============================================================
# Alerts
