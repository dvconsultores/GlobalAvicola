"""GA-REQ-061 · Cutover — rutas del ciclo crear→subir→validar→aprobar→aplicar (+ SPEC 006).

RBAC: `cutover:{create,validate,submit,approve,apply,read}` (módulo del catálogo cerrado R-199).
El backend es la autoridad; los gates de tenancy/BU/grants se aplican en el servicio.

SPEC 006 añade: `GET /cutover-batches` (listado), `GET /cutover-batches/{id}` (detalle),
`GET …/preview` (resumen funcional por BU) y `GET …/errors?format=csv|xlsx` (informe
descargable). El upload acepta `.xlsx` y `.csv` (`?template_version=` fija la versión del CSV).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
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


@router.get("", response_model=schemas.CutoverBatchList)
async def listar_batches(
    status: Optional[str] = Query(None, alias="status"),
    business_unit: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Batches de la empresa efectiva (más recientes primero): el trabajo no se pierde al recargar."""
    return await CutoverService(db, current_user).listar(estado=status, business_unit=business_unit, limit=limit, offset=offset)


@router.get("/{batch_id}", response_model=schemas.CutoverBatchRead)
async def detalle_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Detalle de un batch (404 si es de otra empresa)."""
    return await CutoverService(db, current_user).detalle(batch_id)


@router.post("/{batch_id}/upload", response_model=schemas.CutoverBatchRead)
async def subir_plantilla(
    batch_id: int,
    file: UploadFile = File(...),
    template_version: Optional[str] = Query(None, description="Versión del contrato para CSV (por defecto v2)."),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "validate")),
):
    """Sube la plantilla (XLSX o CSV): parse + normalización + validación de dominio + staging. Nunca toca tablas operacionales."""
    contenido = await file.read()
    return await CutoverService(db, current_user).subir_y_validar(
        batch_id, file.filename or "plantilla.xlsx", contenido, template_version=template_version)


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
    """APPROVED → APPLIED (terminal): lotes migrados + fases + openings (+ incubadora), todo-o-nada."""
    return await CutoverService(db, current_user).aplicar(batch_id)


@router.get("/{batch_id}/validation", response_model=schemas.CutoverValidationRead)
async def validacion_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Resultado de validación: conteos + errores estructurados (fila/campo/código/mensaje/recibido)."""
    return await CutoverService(db, current_user).validacion(batch_id)


@router.get("/{batch_id}/errors")
async def informe_de_errores(
    batch_id: int,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Informe de errores descargable (CSV `;` UTF-8 o XLSX): `row_number, field, error_code, message, received_value`."""
    contenido, mime, nombre = await CutoverService(db, current_user).informe_de_errores(batch_id, format)
    return Response(content=contenido, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/{batch_id}/preview", response_model=schemas.CutoverPreviewRead)
async def preview_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Preview funcional por BU: resumen (lotes, vivas, fases, granjas/plantas, UNKNOWN) + filas con valor/estado."""
    return await CutoverService(db, current_user).preview(batch_id)


@router.get("/{batch_id}/items", response_model=schemas.CutoverItemsResponse)
async def items_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Filas del batch (staging normalizado) con su estado de validación."""
    return {"items": await CutoverService(db, current_user).items(batch_id)}


@router.get("/{batch_id}/reconciliation", response_model=schemas.CutoverReconciliationRead)
async def reconciliacion_del_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "read")),
):
    """Opening/Post/Lifetime/Current por lote y métrica: saldo vivo real (9.965, nunca 9.465), UNKNOWN visible."""
    return await CutoverService(db, current_user).reconciliacion(batch_id)
