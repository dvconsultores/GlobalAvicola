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
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from . import schemas
from .service import OperationsService

router = APIRouter(route_class=RutaTransaccional, prefix="/operations", tags=["Operations"])

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


# ============================================================
# `GA-REM-040` fase 6 · clasificación pendiente (`OD-10.c`)
#
# Se declaran **antes** de `/{event_id}` para que la ruta literal gane: si fueran después,
# `pending-classification` se leería como un identificador y la bandeja no existiría.
# ============================================================

@router.get("/pending-classification",
            response_model=list[schemas.OperationalEventRead], tags=["Operations"])
async def pending_classification(
    skip: int = 0,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    """Los registros cuya cadena productiva todavía no se sabe.

    Superficie **aparte** del listado operativo, a propósito. Mezclarlos obligaría a que cada
    consulta recordara la excepción de quien lo registró, y la que la olvidara abriría el
    sistema en silencio.

    Ve los suyos quien los registró; los de su empresa, el control autorizado.
    """
    from sqlalchemy import select

    from ..business_units.classification import predicado_de_pendientes
    from .models import OperationalEvent

    consulta = (select(OperationalEvent)
                .where(*predicado_de_pendientes(current_user))
                .order_by(OperationalEvent.event_date.desc(), OperationalEvent.id.desc())
                .offset(skip).limit(limit))
    filas = (await db.execute(consulta)).scalars().all()
    return [schemas.OperationalEventRead.model_validate(e) for e in filas]


@router.post("/{event_id}/classify",
             response_model=schemas.OperationalEventRead, tags=["Operations"])
async def classify_event(
    event_id: int,
    data: schemas.ClassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "update")),
):
    """Fija la cadena de un registro que no podía derivarla. `T-040-17`.

    Exige el permiso de administración de datos maestros y no el de operar: decidir a qué
    cadena pertenece un registro es configuración, no producción. **Ver un pendiente no
    basta para clasificarlo** — quien lo registró lo ve y no puede decidirlo.
    """
    from sqlalchemy import select

    from fastapi import status as _st

    from ..business_units.classification import (
        ClasificacionInvalida, clasificar, predicado_de_pendientes,
    )
    from ..business_units.models import CompanyBusinessUnit
    from .models import OperationalEvent

    evento = (await db.execute(
        select(OperationalEvent).where(
            OperationalEvent.id == event_id,
            *predicado_de_pendientes(current_user))
    )).scalar_one_or_none()
    if evento is None:
        raise HTTPException(status_code=_st.HTTP_404_NOT_FOUND,
                            detail="Registro pendiente no encontrado")

    habilitacion = (await db.execute(
        select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.id == data.company_business_unit_id)
    )).scalar_one_or_none()
    try:
        await clasificar(db, evento=evento, company_business_unit=habilitacion,
                         actor=current_user)
    except ClasificacionInvalida as exc:
        raise HTTPException(status_code=_st.HTTP_400_BAD_REQUEST, detail=str(exc))
    # Tras el `flush`, serializar la instancia dispara una carga perezosa fuera del contexto
    # asíncrono. Se refresca antes de proyectarla: el objeto ya está en sesión y refrescarlo
    # es más honesto que declarar la respuesta a medias.
    await db.refresh(evento)
    return schemas.OperationalEventRead.model_validate(evento)


@router.post("/{event_id}/reclassify",
             response_model=schemas.OperationalEventRead, tags=["Operations"])
async def reclassify_event(
    event_id: int,
    data: schemas.ReclassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "correct")),
):
    """Corrige la cadena de un registro **ya clasificado**. `OD-10.d`.

    Permiso distinto del de la primera clasificación a propósito: sacar un registro de
    «pendiente» y cambiar una atribución que ya estaba puesta no son el mismo acto ni el
    mismo riesgo.

    Responde `409` cuando el registro ya produjo efectos —aprobado, consolidado, enviado a
    SAP o participante en un traspaso—, y dice **cuáles**: una negativa sin motivo obliga a
    adivinar qué hay que revertir.
    """
    from fastapi import status as _st
    from sqlalchemy import select

    from ..business_units.classification import (
        ClasificacionInvalida, ReclasificacionBloqueada, reclasificar,
    )
    from ..business_units.models import CompanyBusinessUnit
    from .models import OperationalEvent

    evento = (await db.execute(
        select(OperationalEvent).where(
            OperationalEvent.id == event_id,
            OperationalEvent.company_id == current_user.get("company_id"))
    )).scalar_one_or_none()
    if evento is None:
        raise HTTPException(status_code=_st.HTTP_404_NOT_FOUND,
                            detail="Registro no encontrado")

    habilitacion = (await db.execute(
        select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.id == data.company_business_unit_id)
    )).scalar_one_or_none()
    try:
        await reclasificar(db, evento=evento, company_business_unit=habilitacion,
                           motivo=data.reason, actor=current_user)
    except ReclasificacionBloqueada as exc:
        raise HTTPException(status_code=_st.HTTP_409_CONFLICT, detail=str(exc))
    except ClasificacionInvalida as exc:
        raise HTTPException(status_code=_st.HTTP_400_BAD_REQUEST, detail=str(exc))
    await db.refresh(evento)
    return schemas.OperationalEventRead.model_validate(evento)


@router.get("/{event_id}/weight-evaluation",
            response_model=schemas.WeightEvaluationRead)
async def get_weight_evaluation(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("operations", "read")),
):
    """La evaluación de los pesos del evento contra la curva del lote. `AC26`…`AC28`.

    Va declarada **antes** de `/{event_id}` no por casualidad: `R-38` costó un endpoint
    inalcanzable porque una ruta genérica se declaró primero y capturó a la específica.

    La tenencia la impone `get_event`, que ya filtra por empresa (`AC28`).
    """
    servicio = _service(db, current_user)
    event = await servicio.get_event(event_id)
    pesos = [bm.avg_weight for bm in event.bird_movements]
    return schemas.WeightEvaluationRead.model_validate(
        await servicio.evaluar_pesajes(event, pesos)
    )


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
