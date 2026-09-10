"""Correction service — creates immutable correction audit trail."""
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_correction
from ..operations.models import EventStatus, OperationalEvent
from . import models, schemas


class CorrectionService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def create_correction(self, data: schemas.CorrectionCreate) -> models.CorrectionLog:
        """Create a correction log entry and update the event status to CORRECTED."""
        # `GA-REM-006-A` · `AC-S05…S07`: el evento se resuelve con el **mismo alcance** que el
        # resto de sus escrituras —empresa y unidad efectiva para el actor (`404`), y la
        # guarda de escritura productiva (`OD-16.e/f`: la autoridad global, situada y solo
        # sobre unidad habilitada). Antes solo se comparaba la empresa: un corrector
        # alcanzaba los eventos de cadenas que no tenía, o apagadas.
        from ..operations.service import OperationsService

        operaciones = OperationsService(self.db, self.current_user)
        event = await operaciones.get_event(data.event_id)
        await operaciones.exigir_unidad_operativa(event=event)

        # `GA-REM-041` · `AC-RV06`: la contrapartida de un reverso no se corrige (`OD-19 §4`).
        from ..reversals.service import es_contrapartida

        if await es_contrapartida(self.db, event.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Una contrapartida de reverso no se corrige")
        # Event must be in a correctable state. `OD-17.a` / `AC-S02`: `REJECTED` no es terminal.
        correctable = (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW, EventStatus.IN_REVIEW,
                       EventStatus.RETURNED, EventStatus.REJECTED)
        if event.status not in correctable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento no se puede corregir en estado '{event.status.value}'",
            )

        # P0-2: aplicar el valor corregido al dato.
        #
        # Hasta ahora se creaba el registro de correccion, se cambiaba el estado a
        # CORRECTED y **no se escribia nada**: el dato erroneo era el que se aprobaba, el
        # que alimentaba los KPI y el que se consolidaba hacia SAP. El sistema quedaba con
        # dos verdades divergentes.
        #
        # Regla vigente `RR-01` (Wave 1.5): la correccion escribe el valor en el acto,
        # conserva el original en el `CorrectionLog` y deja el registro pendiente de
        # aprobacion.
        valor_original = _leer_valor(event, data.field_name)
        valor_aplicado = _convertir(event, data.field_name, data.corrected_value)
        if data.field_name in ("chicks_healthy", "chicks_weak"):  # `GA-REM-021-C` · `AC-B13-11`: la corrección respeta `BR-21`
            from ..operations.validators import validate_birth_registration

            validate_birth_registration(
                event.event_type, await operaciones._tipo_de_lote(event.lot_id),
                valor_aplicado if data.field_name == "chicks_healthy" else event.chicks_healthy,
                valor_aplicado if data.field_name == "chicks_weak" else event.chicks_weak,
                [(bm.sex, bm.quantity) for bm in event.bird_movements])
        if data.field_name == "water_liters":  # `GA-REM-021-A` · `AC-C03`: la corrección respeta `RR-11`
            from ..operations.validators import validate_water_consumption

            validate_water_consumption(event.event_type, valor_aplicado, await operaciones._tipo_de_lote(event.lot_id))
        if data.field_name in ("lot_id", "farm_id", "house_id", "destination_farm_id", "event_date", "sap_document_ref"):
            # `GA-REM-005-E` · `R-173` · `AC-R173-11…14`: corregir el lote o la ubicación **es** una
            # reasignación; pasa por la misma guarda que la edición (empresa, unidad, lote activo,
            # fecha, ubicación y regla de saldo, bajo el bloqueo de los lotes). Antes se aplicaba
            # tal cual: un evento podía moverse a un lote de otra empresa o de una unidad apagada.
            # `GA-REM-023-B` · `R-176` (+ `R-45`): la fecha y el documento SAP también pasan por ella
            # (`BR-06`, `BR-19`, `BR-11`, `BR-18`): corregir no es una puerta trasera.
            await operaciones.verificar_destino_de_edicion(event, {data.field_name: valor_aplicado})
        setattr(event, data.field_name, valor_aplicado)
        event.version += 1

        # El log guarda lo que **habia**, no lo que el cliente dijera que habia: si el
        # valor original lo aporta quien corrige, la auditoria deja de ser evidencia.
        correction = models.CorrectionLog(
            event_id=data.event_id,
            field_name=data.field_name,
            original_value=valor_original,
            corrected_value=data.corrected_value,
            corrected_by_id=self.current_user["id"],
            correction_type_id=data.correction_type_id,
            reason=data.reason,
        )
        self.db.add(correction)

        # Update event status to CORRECTED
        event.status = EventStatus.CORRECTED
        await self.db.flush()
        await self.db.refresh(correction)
        await self.db.refresh(event)

        # Audit: field-level correction
        await audit_correction(
            self.db, data.event_id, self.current_user,
            field_name=data.field_name,
            original_value=valor_original,
            corrected_value=data.corrected_value,
            reason=data.reason,
            lot_id=event.lot_id,
        )

        return correction

    async def get_corrections_for_event(self, event_id: int) -> list[models.CorrectionLog]:
        """Get all corrections for a given event."""
        result = await self.db.execute(
            select(models.CorrectionLog)
            .join(OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id)
            .where(
                models.CorrectionLog.event_id == event_id,
                OperationalEvent.company_id == self.company_id,
            )
            .order_by(models.CorrectionLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_corrections(
        self,
        lot_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[models.CorrectionLog], int]:
        """List corrections with optional lot filter."""
        base = select(models.CorrectionLog).join(
            OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id
        ).where(OperationalEvent.company_id == self.company_id)
        cq = select(func_count()).select_from(models.CorrectionLog).join(
            OperationalEvent, models.CorrectionLog.event_id == OperationalEvent.id
        ).where(OperationalEvent.company_id == self.company_id)

        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
            cq = cq.where(OperationalEvent.lot_id == lot_id)

        base = base.order_by(models.CorrectionLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(base)
        corrections = list(result.scalars().all())
        count_r = await self.db.execute(cq)
        total = count_r.scalar() or 0
        return corrections, total


def func_count():
    from sqlalchemy import func
    return func.count()


# ═══════════════════════════════════════════════════════════════════════════
# Aplicacion del valor corregido — P0-2 / RR-01
# ═══════════════════════════════════════════════════════════════════════════

#: `GA-REM-021-B` · `B01`: los sumandos del cuadre (`BR-20`) forman una identidad; corregir uno solo
#: siempre descuadra un registro cuadrado. Se editan juntos por `PUT` (`OperationalEventUpdate`) o se
#: devuelve el registro (`R-135`). Excepción explícita a la derivación de `RR-01`.
NO_CORREGIBLES_POR_IDENTIDAD = frozenset({"received_total", "dead_on_arrival", "rejected_on_arrival"})


def campos_corregibles() -> set[str]:
    """Campos del evento que una correccion puede modificar.

    Lista blanca explicita, no `setattr` sobre lo que llegue. `field_name` lo elige el
    cliente: sin acotarlo, una correccion podria escribir `status`, `company_id`,
    `registered_by_id` o `approved_by_id` y convertirse en la misma escalada de
    privilegios que `R-32`.
    """
    from ..operations.schemas import OperationalEventUpdate

    return set(OperationalEventUpdate.model_fields) - NO_CORREGIBLES_POR_IDENTIDAD


def _leer_valor(event, campo: str) -> str | None:
    valor = getattr(event, campo, None)
    return None if valor is None else str(valor)


def _convertir(event, campo: str, valor: str | None):
    """Convierte el valor recibido al tipo de la columna.

    `corrected_value` llega como texto. Escribirlo tal cual en una columna numerica o de
    fecha produciria un error de base de datos —un 500— en lugar de un mensaje util.
    """
    from datetime import date as _date

    if campo not in campos_corregibles():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El campo '{campo}' no es corregible. "
                f"Campos admitidos: {', '.join(sorted(campos_corregibles()))}"
            ),
        )
    if valor is None or valor == "":
        return None

    columna = OperationalEvent.__table__.columns.get(campo)
    tipo = columna.type.python_type if columna is not None else str
    try:
        if tipo is _date:
            return _date.fromisoformat(valor)
        if tipo is bool:
            return valor.strip().lower() in ("true", "1", "si", "sí")
        if tipo is dict:
            import json

            return json.loads(valor)
        return tipo(valor)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El valor '{valor}' no es valido para el campo '{campo}' "
                f"(se esperaba {tipo.__name__})"
            ),
        ) from None
