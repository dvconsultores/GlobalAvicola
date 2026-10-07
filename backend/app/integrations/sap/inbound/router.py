"""API interna inbound SAP — SPEC 005 `§33`…`§37`.

Es la API de Global Avícola, no un proxy de HANA: ninguna ruta acepta SQL, schema ni tabla.

    sap:read        estado, catálogo, jobs, registros, errores, mappings
    sap:send_sap    operar el conector: sincronizar y configurar el mapping

`sap:send_sap` autoriza operar la integración (`OD-12`). **No autoriza escribir en SAP**: en
esta fase no existe ninguna ruta que lo haga.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....dependencies import require_permission
from ....transaction import RutaTransaccional
from . import schemas
from .registry import HanaObject
from .service import SapInboundService

router = APIRouter(route_class=RutaTransaccional, prefix="/sap/inbound",
                   tags=["SAP Inbound (READ ONLY)"])


def _respuesta_sync(jobs) -> schemas.SyncResponse:
    return schemas.SyncResponse(
        sync_request_id=jobs[0].sync_request_id if jobs else None,
        jobs=[schemas.JobRead.model_validate(j) for j in jobs])


@router.get("/readiness")
async def readiness(current_user: dict = Depends(require_permission("sap", "read"))):
    """Estado del conector. Responde sin credenciales y sin tocar la red."""
    return SapInboundService(None, current_user).readiness()


@router.get("/objects")
async def list_objects(current_user: dict = Depends(require_permission("sap", "read"))):
    """Catálogo de objetos sincronizables. Describe el contrato; no expone SQL."""
    return {"objects": SapInboundService(None, current_user).list_objects()}


@router.post("/sync", response_model=schemas.SyncResponse)
async def sync_all(
    data: Optional[schemas.SyncRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Sincroniza los objetos pedidos (todos, si no se indica ninguno) de la empresa efectiva.

    Un fallo de SAP no es un error HTTP: es el resultado auditado de un job (`failed`).
    """
    data = data or schemas.SyncRequest()
    jobs = await SapInboundService(db, current_user).sync(
        data.object_types, date_from=data.date_from, date_to=data.date_to)
    return _respuesta_sync(jobs)


@router.post("/sync/{object_type}", response_model=schemas.SyncResponse)
async def sync_object(
    object_type: HanaObject,
    data: Optional[schemas.SyncWindow] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Sincroniza un objeto del registry. El nombre es un valor cerrado, no texto libre."""
    data = data or schemas.SyncWindow()
    jobs = await SapInboundService(db, current_user).sync(
        [object_type], date_from=data.date_from, date_to=data.date_to)
    return _respuesta_sync(jobs)


@router.get("/jobs")
async def list_jobs(
    object_type: Optional[HanaObject] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    jobs, total = await SapInboundService(db, current_user).list_jobs(
        limit=limit, offset=offset, object_type=object_type.value if object_type else None)
    return {"jobs": [schemas.JobRead.model_validate(j) for j in jobs], "total": total}


@router.get("/records")
async def list_records(
    object_type: Optional[HanaObject] = Query(None),
    validation_status: Optional[str] = Query(None, pattern=r"^[A-Z_]{1,30}$"),
    mapping_status: Optional[str] = Query(None, pattern=r"^[A-Z_]{1,30}$"),
    promotion_status: Optional[str] = Query(None, pattern=r"^[A-Z_]{1,30}$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    registros, total = await SapInboundService(db, current_user).list_records(
        object_type=object_type.value if object_type else None,
        validation_status=validation_status, mapping_status=mapping_status,
        promotion_status=promotion_status, limit=limit, offset=offset)
    return {"records": [schemas.RecordRead.model_validate(r) for r in registros],
            "total": total}


@router.get("/errors")
async def list_errors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    """Registros retenidos o inválidos y jobs fallidos. Mensajes saneados, sin stack trace."""
    registros, jobs = await SapInboundService(db, current_user).list_errors(
        limit=limit, offset=offset)
    return {"records": [schemas.RecordRead.model_validate(r) for r in registros],
            "jobs": [schemas.JobRead.model_validate(j) for j in jobs]}


@router.get("/mappings")
async def list_mappings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "read")),
):
    mappings = await SapInboundService(db, current_user).list_mappings()
    return {"mappings": [schemas.MappingRead.model_validate(m) for m in mappings]}


@router.put("/mappings", response_model=schemas.MappingRead)
async def upsert_mapping(
    data: schemas.MappingUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    """Declara que una sociedad, centro o almacén SAP pertenece a la empresa efectiva."""
    return await SapInboundService(db, current_user).upsert_mapping(**data.model_dump())


@router.delete("/mappings/{mapping_id}")
async def delete_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("sap", "send_sap")),
):
    await SapInboundService(db, current_user).delete_mapping(mapping_id)
    return {"deleted": mapping_id}
