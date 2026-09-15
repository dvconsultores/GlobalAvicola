"""GA-REQ-061 · Cutover — rutas del ciclo crear→subir→validar (C2).

RBAC: `cutover:{create,validate,read}` (módulo del catálogo cerrado R-199). El
backend es la autoridad; los gates de tenancy/BU/grants se aplican en el servicio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import require_permission
from ..transaction import RutaTransaccional
from . import schemas
from .service import CutoverService

router = APIRouter(route_class=RutaTransaccional, prefix="/cutover-batches", tags=["Cutover"])


@router.post("", response_model=schemas.CutoverBatchRead, status_code=201)
async def crear_batch(
    data: schemas.CutoverBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "create")),
):
    """Crea un batch de cutover en DRAFT (empresa efectiva del actor)."""
    return await CutoverService(db, current_user).crear_batch(data)


@router.post("/{batch_id}/upload", response_model=schemas.CutoverBatchRead)
async def subir_plantilla(
    batch_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "validate")),
):
    """Sube la plantilla: parse + staging + validación. El Excel nunca toca tablas operacionales."""
    contenido = await file.read()
    return await CutoverService(db, current_user).subir_y_validar(
        batch_id, file.filename or "plantilla.xlsx", contenido)


@router.post("/{batch_id}/submit", response_model=schemas.CutoverBatchRead)
async def enviar_a_aprobacion(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "submit")),
):
    """VALIDATED → PENDING_APPROVAL."""
    return await CutoverService(db, current_user).enviar_a_aprobacion(batch_id)


@router.post("/{batch_id}/approve", response_model=schemas.CutoverBatchRead)
async def aprobar_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "approve")),
):
    """PENDING_APPROVAL → APPROVED (segregación: el creador no aprueba)."""
    return await CutoverService(db, current_user).aprobar(batch_id)


@router.post("/{batch_id}/reject", response_model=schemas.CutoverBatchRead)
async def rechazar_batch(
    batch_id: int,
    data: schemas.CutoverRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "approve")),
):
    """PENDING_APPROVAL → REJECTED (terminal), con razón obligatoria."""
    return await CutoverService(db, current_user).rechazar(batch_id, data.reason)


@router.post("/{batch_id}/apply", response_model=schemas.CutoverBatchRead)
async def aplicar_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "apply")),
):
    """APPROVED → APPLIED (terminal): lotes migrados + snapshots de opening, todo-o-nada."""
    return await CutoverService(db, current_user).aplicar(batch_id)


@router.get("/{batch_id}/validation", response_model=schemas.CutoverValidationRead)
async def validacion_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Preview de validación: conteos + errores estructurados (fila/campo/código/recibido)."""
    return await CutoverService(db, current_user).validacion(batch_id)


@router.get("/{batch_id}/items", response_model=schemas.CutoverItemsResponse)
async def items_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Filas del batch (staging normalizado) con su estado de validación."""
    return {"items": await CutoverService(db, current_user).items(batch_id)}
