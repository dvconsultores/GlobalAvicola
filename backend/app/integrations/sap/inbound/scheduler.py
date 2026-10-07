"""Sincronización programada — SPEC 005 `§40`, `FR-17`.

Sin Celery ni Redis: una tarea del propio proceso en el `lifespan`, como la del SLA de
revisiones. Cuatro garantías:

    no corre en las pruebas     el `lifespan` no la lanza con `GA_TEST_ENV=1`
    no llama a HANA a ciegas    sin configuración completa no hace nada, ni un job fallido
    no solapa                   un cerrojo en el proceso y un advisory lock por objeto en la base
    no avanza si falla          el watermark es del savepoint de cada objeto
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import select

from .adapter import SapInboundAdapter
from .models import ENTITY_COMPANY_CODE, SOURCE_SYSTEM, SapEntityMapping
from .service import SapInboundService
from .settings import HanaSettings

logger = logging.getLogger("ga.sap.inbound")
_en_curso = asyncio.Lock()


async def run_scheduled_sync(
    session_factory: Callable[[], Any], *, cfg: HanaSettings | None = None,
    adapter_factory: Optional[Callable[[HanaSettings], SapInboundAdapter]] = None,
    company_ids: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Una pasada: sincroniza cada empresa que tenga una sociedad SAP mapeada."""
    cfg = cfg or HanaSettings.from_settings()
    if not cfg.configured:
        return {"ran": False, "reason": "PENDING_CREDENTIALS", "companies": []}

    async with session_factory() as sesion:
        consulta = select(SapEntityMapping.company_id).where(
            SapEntityMapping.source_system == SOURCE_SYSTEM,
            SapEntityMapping.client == cfg.client,
            SapEntityMapping.entity_type == ENTITY_COMPANY_CODE,
            SapEntityMapping.is_active.is_(True)).distinct()
        if company_ids is not None:
            consulta = consulta.where(SapEntityMapping.company_id.in_(list(company_ids)))
        empresas = sorted((await sesion.execute(consulta)).scalars().all())

    hechas: list[int] = []
    for company_id in empresas:
        async with session_factory() as sesion:
            try:
                servicio = SapInboundService(
                    sesion, {"id": None, "company_id": company_id, "is_super_admin": False},
                    adapter=adapter_factory(cfg) if adapter_factory else None, cfg=cfg)
                await servicio.sync(None, trigger="scheduled")
                await sesion.commit()
                hechas.append(company_id)
            except Exception as exc:  # noqa: BLE001 — una empresa no detiene a las demás
                await sesion.rollback()
                logger.warning("Sync programado de la empresa %s falló: %s", company_id,
                               cfg.redact(f"{type(exc).__name__}: {exc}"))
    return {"ran": True, "companies": hechas}


async def vigilar_sap_inbound(intervalo_segundos: int) -> None:
    """Bucle del `lifespan`. Sin credenciales se limita a esperar: ni reintentos ni ruido."""
    from ....database import async_session

    avisado = False
    while True:
        await asyncio.sleep(max(60, int(intervalo_segundos)))
        if _en_curso.locked():
            continue
        async with _en_curso:
            try:
                resumen = await run_scheduled_sync(async_session)
                if not resumen["ran"] and not avisado:
                    logger.info("SAP HANA inbound: %s. El scheduler queda en espera.",
                                resumen["reason"])
                    avisado = True
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("SAP HANA inbound: pasada programada fallida (%s).",
                               type(exc).__name__)
