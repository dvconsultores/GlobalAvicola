"""Audit service — query-only. AuditLogs are created automatically by event listeners."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas


def _instante(valor: Optional[str], fin_del_dia: bool = False) -> Optional[datetime]:
    """Convierte `YYYY-MM-DD` —o un ISO completo— en un instante UTC comparable."""
    if not valor:
        return None
    try:
        momento = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    if fin_del_dia and len(valor) == 10:
        momento = momento + timedelta(days=1) - timedelta(microseconds=1)
    return momento


class AuditService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def list_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        module: Optional[str] = None,
        lot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        state: Optional[str] = None,
        sap_reference_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[models.AuditLog], int]:
        base = select(models.AuditLog).where(models.AuditLog.company_id == self.company_id)
        cq = select(func_count()).select_from(models.AuditLog).where(models.AuditLog.company_id == self.company_id)

        if user_id:
            base = base.where(models.AuditLog.user_id == user_id)
            cq = cq.where(models.AuditLog.user_id == user_id)
        if action:
            base = base.where(models.AuditLog.action == action)
            cq = cq.where(models.AuditLog.action == action)
        if entity_type:
            base = base.where(models.AuditLog.entity_type == entity_type)
            cq = cq.where(models.AuditLog.entity_type == entity_type)
        if entity_id:
            base = base.where(models.AuditLog.entity_id == entity_id)
            cq = cq.where(models.AuditLog.entity_id == entity_id)
        if module:
            base = base.where(models.AuditLog.module == module)
            cq = cq.where(models.AuditLog.module == module)
        if lot_id:
            base = base.where(models.AuditLog.lot_id == lot_id)
            cq = cq.where(models.AuditLog.lot_id == lot_id)
        if farm_id:
            base = base.where(models.AuditLog.farm_id == farm_id)
            cq = cq.where(models.AuditLog.farm_id == farm_id)
        # `R-84`. Se comparaba la cadena directamente contra una columna `timestamptz` y
        # PostgreSQL respondía «operator does not exist», es decir **500**. El filtro de
        # fecha es además el único que la interfaz enviaba, de modo que estrenarlo rompía la
        # pantalla. Se convierte a instante antes de comparar; `date_to` cubre el día
        # entero, que es lo que un auditor espera al escribir una fecha.
        desde = _instante(date_from)
        if desde is not None:
            base = base.where(models.AuditLog.created_at >= desde)
            cq = cq.where(models.AuditLog.created_at >= desde)
        hasta = _instante(date_to, fin_del_dia=True)
        if hasta is not None:
            base = base.where(models.AuditLog.created_at <= hasta)
            cq = cq.where(models.AuditLog.created_at <= hasta)

        # `GA-REM-032 AC09`. «Estado» y «documento SAP» son dos de los siete filtros que
        # `docs/02 §3.11.2` exige y no existían, aunque sus columnas ya estaban.
        if state:
            base = base.where(models.AuditLog.new_state == state)
            cq = cq.where(models.AuditLog.new_state == state)
        if sap_reference_id:
            base = base.where(models.AuditLog.sap_reference_id == sap_reference_id)
            cq = cq.where(models.AuditLog.sap_reference_id == sap_reference_id)

        base = base.order_by(models.AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(base)
        logs = list(result.scalars().all())
        cr = await self.db.execute(cq)
        total = cr.scalar() or 0
        return logs, total

    async def get_log(self, log_id: str) -> models.AuditLog:
        from fastapi import HTTPException, status
        result = await self.db.execute(
            select(models.AuditLog).where(
                models.AuditLog.id == log_id,
                models.AuditLog.company_id == self.company_id,
            )
        )
        log = result.scalar_one_or_none()
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de auditoría no encontrado")
        return log

    async def get_entity_timeline(self, entity_type: str, entity_id: str) -> list[models.AuditLog]:
        """Get full audit timeline for a specific entity."""
        result = await self.db.execute(
            select(models.AuditLog).where(
                models.AuditLog.company_id == self.company_id,
                models.AuditLog.entity_type == entity_type,
                models.AuditLog.entity_id == entity_id,
            ).order_by(models.AuditLog.created_at.asc())
        )
        return list(result.scalars().all())


def func_count():
    from sqlalchemy import func
    return func.count()
