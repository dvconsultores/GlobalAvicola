"""Correction service — creates immutable correction audit trail."""
import re
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_correction
from ..operations.models import EventStatus, EventType, OperationalEvent
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
        if event.status not in ESTADOS_CORREGIBLES:
            # `S1-I18N-01`: el operador ve el estado en español, no el valor crudo del enum.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El evento no se puede corregir en estado '{_traducir_estado(event.status)}'",
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
        valor_corregido_texto = data.corrected_value
        if _parsear_submovimiento(data.field_name) is not None:
            # `S1-CORR-01` · `GA-UAT-BREEDER-CRIA-S1-2026-11-10 §3`: el campo corregido de un
            # submovimiento se identifica con el **id de su fila** (`bird_movements[<id>].<campo>`)
            # y se escribe en la fila, no en el evento. La guarda de estado y la unidad operativa
            # ya se aplicaron arriba, igual que para un campo del evento.
            valor_original, valor_corregido_texto = await self._corregir_submovimiento(
                event, data, operaciones)
        else:
            valor_original = _leer_valor(event, data.field_name)
            valor_aplicado = _convertir(event, data.field_name, data.corrected_value)
            if valor_aplicado is None and data.field_name in NO_VACIABLES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_VACIABLES[data.field_name])
            operaciones.validar_cantidades_del_candidato(event, {data.field_name: valor_aplicado})
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
            if data.field_name in ("vaccine_id", "medication_id"):
                # `GA-UAT-BREEDER-CRIA-S1-2026-11-10` · `spec 015 §4.1`: la corrección respeta
                # `RR-21`/`RR-22`. Vaciar la referencia (`corrected_value` vacío ⇒ `None`) deja la
                # vacunación o la medicación sin su dato mínimo, igual que en el alta y la edición.
                from ..operations.validators import validate_contenido_minimo

                validate_contenido_minimo(
                    event.event_type,
                    valor_aplicado if data.field_name == "vaccine_id" else event.vaccine_id,
                    valor_aplicado if data.field_name == "medication_id" else event.medication_id,
                    event.bird_movements, event.feed_movements)
            if data.field_name in ("lot_id", "farm_id", "house_id", "destination_farm_id", "event_date", "sap_document_ref",
                                   "extra_data", "supplier_id", "transport_id",  # `GA-REM-042`: el plan de importación y sus maestros
                                   # `GA-REM-002-D` · `R-179` `AC-R179-04`: corregir una referencia a catálogo **es** repuntarla,
                                   # y pasa por la misma guarda que la edición (pertenencia de la empresa, `BR-07`).
                                   "cause_id", "cull_cause_id", "vaccine_id", "medication_id", "destination_plant_id"):
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
            corrected_value=valor_corregido_texto,
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
            corrected_value=valor_corregido_texto,
            reason=data.reason,
            lot_id=event.lot_id,
        )

        await self._anotar_nombres([correction])
        return correction

    async def _corregir_submovimiento(self, event, data: schemas.CorrectionCreate, operaciones) -> tuple[str | None, str | None]:
        """Aplica la corrección a una fila de `bird_movements` / `feed_movements`.

        `S1-CORR-01` · `spec 015 §3`. Sin migración: la fila destino viaja en el propio
        `field_name` (`bird_movements[<id>].<campo>`), que es lo que queda en el
        `CorrectionLog`. Devuelve `(valor_original, valor_corregido)` como texto, que es lo
        que el registro de corrección guarda.

        Revalidación (`§3`): una salida de aves se mide por el **delta** — el saldo del lote
        ya incluye la salida de este evento, así que subir la cantidad no puede volver a
        consumir lo que ya consumió (`BR-01`).
        """
        tabla, fila_id, campo = _parsear_submovimiento(data.field_name)
        es_recepcion_breeder = (
            event.event_type == EventType.BIRD_RECEPTION
            and await _es_lote_breeder(operaciones, event.lot_id)
        )
        filas = event.bird_movements if tabla == "bird_movements" else event.feed_movements
        fila = next((f for f in filas if f.id == fila_id), None)
        if (fila is None
                or campo not in SUBMOV_CORREGIBLES[tabla]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El campo '{data.field_name}' no es corregible. "
                    f"Campos admitidos: {_campos_admitidos(event, es_recepcion_breeder)}"
                ),
            )
        if tabla == "bird_movements" and campo == "quantity" and es_recepcion_breeder:
            # `BR-20` · identidad del cuadre de recepción (`NO_CORREGIBLES_POR_IDENTIDAD`).
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("La cantidad recibida de un lote de reproductoras no se corrige aislada "
                        "(cuadre de recepción); edite el registro completo."),
            )

        valor = _convertir_valor_de_fila(data.field_name, campo, data.corrected_value)
        valor_previo = getattr(fila, campo, None)

        if (tabla == "bird_movements" and campo == "quantity"
                and event.event_type in SALIDAS_DE_AVES and event.lot_id is not None):
            from ..operations.validators import (
                BusinessRuleViolation,
                bloquear_saldo_del_lote,
                get_current_bird_balance,
            )

            suma_actual = sum(bm.quantity or 0 for bm in event.bird_movements)
            suma_nueva = suma_actual - (fila.quantity or 0) + (valor or 0)
            if suma_nueva <= 0:
                raise BusinessRuleViolation(
                    f"La cantidad total de la {_ETIQUETA_SALIDA.get(event.event_type, 'salida')} "
                    "debe ser mayor a cero", "BR-01")
            delta = suma_nueva - suma_actual
            if delta > 0:
                await bloquear_saldo_del_lote(self.db, event.lot_id)
                saldo = await get_current_bird_balance(self.db, event.lot_id)
                if delta > saldo:
                    raise BusinessRuleViolation(
                        f"La cantidad corregida ({suma_nueva}) excede el saldo de aves "
                        f"disponibles ({saldo + suma_actual})", "BR-01")

        if (tabla == "bird_movements" and campo == "avg_weight"
                and event.event_type == EventType.WEIGHT_RECORDING):
            # `GA-UAT-BREEDER-CRIA-S1-2026-11-10` · `spec 015 §4.1`: la corrección respeta `RR-20`.
            # Vaciar el peso de la última fila con peso deja el pesaje sin su dato mínimo; se evalúa
            # el estado candidato (las filas persistidas con esta fila ya cambiada).
            from types import SimpleNamespace

            from ..operations.validators import validate_contenido_minimo

            candidatas = [SimpleNamespace(avg_weight=valor)] + [
                SimpleNamespace(avg_weight=otra.avg_weight)
                for otra in event.bird_movements if otra.id != fila.id]
            validate_contenido_minimo(event.event_type, event.vaccine_id, event.medication_id,
                                      candidatas, event.feed_movements)

        setattr(fila, campo, valor)
        event.version += 1
        return (
            None if valor_previo is None else str(valor_previo),
            None if valor is None else str(valor),
        )

    async def campos_corregibles_de_evento(self, event_id: int) -> list[dict]:
        """Campos realmente corregibles de **ese** evento (`S1-CORR-01`).

        El formulario de corrección consume esta lista en lugar de ofrecer «Observaciones»
        fijo: los campos del evento con valor, más los de cada fila de submovimiento con el
        id de su fila. Un evento fuera de estado corregible no es un error, es una lista
        vacía (`AC-S1-C05`).
        """
        from ..operations.service import OperationsService

        operaciones = OperationsService(self.db, self.current_user)
        event = await operaciones.get_event(event_id)
        if event.status not in ESTADOS_CORREGIBLES:
            return []
        es_recepcion_breeder = (
            event.event_type == EventType.BIRD_RECEPTION
            and await _es_lote_breeder(operaciones, event.lot_id)
        )

        campos: list[dict] = []
        columnas = OperationalEvent.__table__.columns
        for campo in sorted(campos_corregibles()):
            if campo in FUERA_DEL_SELECTOR:
                continue
            valor = getattr(event, campo, None)
            if valor is None and campo not in SIEMPRE_OFRECIDOS:
                continue
            columna = columnas.get(campo)
            campos.append({
                "field_name": campo,
                "label_key": f"corrections.fields.{campo}",
                "current_value": None if valor is None else str(valor),
                "row_id": None,
                "row_label": None,
                "value_type": _tipo_de_valor(columna.type.python_type if columna is not None else str),
                # `AC-S2-C04`: de qué catálogo es el campo y cómo se llama hoy su registro.
                "master": MAESTROS_CORREGIBLES[campo][0] if campo in MAESTROS_CORREGIBLES else None,
                "current_display": await self._nombre_de_maestro(campo, valor),
            })

        for bm in event.bird_movements:
            for campo in sorted(SUBMOV_CORREGIBLES["bird_movements"]):
                if campo == "quantity" and es_recepcion_breeder:
                    continue
                campos.append({
                    "field_name": f"bird_movements[{bm.id}].{campo}",
                    "label_key": f"corrections.fields.bird_movements.{campo}",
                    "current_value": None if getattr(bm, campo) is None else str(getattr(bm, campo)),
                    "row_id": bm.id,
                    "row_label": bm.sex,
                    "value_type": _tipo_de_valor(float if campo == "avg_weight" else int),
                })
        for fm in event.feed_movements:
            for campo in sorted(SUBMOV_CORREGIBLES["feed_movements"]):
                campos.append({
                    "field_name": f"feed_movements[{fm.id}].{campo}",
                    "label_key": f"corrections.fields.feed_movements.{campo}",
                    "current_value": None if getattr(fm, campo) is None else str(getattr(fm, campo)),
                    "row_id": fm.id,
                    "row_label": None,
                    "value_type": "decimal",
                })
        return campos

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
        correcciones = list(result.scalars().all())
        await self._anotar_nombres(correcciones)
        return correcciones

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
        await self._anotar_nombres(corrections)
        return corrections, total

    async def _nombre_de_maestro(self, campo: str, valor) -> str | None:
        """Nombre del registro de catálogo que un campo de maestro referencia (`AC-S2-C04`); `None` si no aplica."""
        if campo not in MAESTROS_CORREGIBLES or valor is None:
            return None
        try:
            identificador = int(str(valor))
        except ValueError:
            return None
        from ..masters import models as masters_models

        modelo = getattr(masters_models, MAESTROS_CORREGIBLES[campo][1])
        consulta = select(modelo.name).where(modelo.id == identificador)
        if hasattr(modelo, "company_id") and self.company_id is not None:
            # el catálogo compartido (`company_id` nulo) es legible; el de otra empresa no se nombra
            consulta = consulta.where(or_(modelo.company_id == self.company_id, modelo.company_id.is_(None)))
        return (await self.db.execute(consulta)).scalar_one_or_none()

    async def _anotar_nombres(self, correcciones) -> None:
        """`AC-S2-C05`: el historial lee nombres de maestro, no ids (atributos transitorios de lectura)."""
        for c in correcciones:
            if c.field_name in MAESTROS_CORREGIBLES:
                c.original_display = await self._nombre_de_maestro(c.field_name, c.original_value)
                c.corrected_display = await self._nombre_de_maestro(c.field_name, c.corrected_value)
            else:
                c.original_display = None
                c.corrected_display = None


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


#: `S1-CORR-01` · `spec 015 §3`: campos corregibles de un **submovimiento**. La clave es la
#: tabla; el campo corregido se guarda en el `CorrectionLog` como `<tabla>[<id>].<campo>`.
SUBMOV_CORREGIBLES: dict[str, set[str]] = {
    "bird_movements": {"avg_weight", "quantity", "week_number"},
    "feed_movements": {"quantity_kg"},
}

#: Estados desde los que se admite corregir. `OD-17.a` / `AC-S02`: `REJECTED` no es terminal.
ESTADOS_CORREGIBLES = (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW, EventStatus.IN_REVIEW,
                       EventStatus.RETURNED, EventStatus.REJECTED)

#: `S1-I18N-01`: el mensaje de estado no muestra el valor crudo del enum.
ESTADO_ES = {
    "registered": "Registrado",
    "pending_review": "Pendiente de revisión",
    "in_review": "En revisión",
    "returned": "Devuelto",
    "corrected": "Corregido",
    "approved": "Aprobado",
    "rejected": "Rechazado",
    "consolidated": "Consolidado",
    "sent_to_sap": "Enviado a SAP",
    "sap_confirmed": "Confirmado por SAP",
    "sap_error": "Error SAP",
    "cancelled": "Anulado",
    "draft": "Borrador",
    "reversed": "Revertido",
}

#: Salidas humanas del saldo de aves cuya cantidad se mide por delta al corregir (`BR-01`).
SALIDAS_DE_AVES = (EventType.MORTALITY_RECORDING, EventType.CULL_RECORDING, EventType.BIRD_EXIT)

_ETIQUETA_SALIDA = {
    EventType.MORTALITY_RECORDING: "mortalidad",
    EventType.CULL_RECORDING: "descarte",
    EventType.BIRD_EXIT: "salida de aves",
}

#: Campos del evento que no se ofrecen en el selector de corrección: se corrigen editando
#: el registro completo, no campo a campo.
FUERA_DEL_SELECTOR = frozenset({"lot_id", "farm_id", "house_id", "extra_data"})

#: `observations` se ofrece siempre, aunque esté vacío: es el campo de uso más frecuente.
SIEMPRE_OFRECIDOS = frozenset({"observations"})

#: `GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.1`: lo que no es anulable no se puede vaciar.
NO_VACIABLES: dict[str, str] = {"event_date": "La fecha del evento no puede quedar vacía"}

#: `GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.3` · `AC-S2-C03`: nombre que el operador lee en el
#: formulario para cada campo corregible. El mensaje de un valor imposible se muestra en pantalla,
#: junto al dato: el identificador técnico (`sample_size`) no le dice nada.
ETIQUETAS_CAMPO: dict[str, str] = {
    "observations": "Observaciones",
    "event_date": "Fecha del evento",
    "sap_document_ref": "Documento SAP",
    "vaccination_route": "Vía de aplicación",
    "vaccine_lot_number": "Lote de vacuna",
    "dosage_per_bird": "Dosis por ave",
    "treatment_days": "Días de tratamiento",
    "sample_size": "Tamaño de muestra",
    "water_liters": "Litros de agua",
    "chicks_healthy": "Pollitos sanos",
    "chicks_weak": "Pollitos débiles",
    "supplier_id": "Proveedor",
    "cause_id": "Causa de mortalidad",
    "cull_cause_id": "Causa de descarte",
    "vaccine_id": "Vacuna",
    "medication_id": "Medicamento",
    "transport_id": "Transporte",
    "destination_farm_id": "Granja destino",
    "destination_plant_id": "Planta destino",
    "lot_id": "Lote",
    "farm_id": "Granja",
    "house_id": "Galpón",
    "extra_data": "Datos adicionales",
    "quantity": "Cantidad",
    "avg_weight": "Peso promedio",
    "week_number": "Semana",
    "quantity_kg": "Cantidad de alimento (kg)",
}

#: `GA-UAT-BREEDER-CRIA-S2` · `spec 020 §3.2` · `AC-S2-C04`: campo de maestro → (recurso de la API
#: del catálogo, modelo ORM). Un `*_id` se corrige con el identificador pero se **lee** por nombre.
MAESTROS_CORREGIBLES: dict[str, tuple[str, str]] = {
    "supplier_id": ("suppliers", "Supplier"),
    "cause_id": ("mortality-causes", "MortalityCause"),
    "cull_cause_id": ("cull-causes", "CullCause"),
    "vaccine_id": ("vaccines", "Vaccine"),
    "medication_id": ("medications", "Medication"),
    "destination_farm_id": ("farms", "Farm"),
    "destination_plant_id": ("processing-plants", "ProcessingPlant"),
    "transport_id": ("transports", "Transport"),
}

_PATRON_SUBMOVIMIENTO = re.compile(r"^(bird_movements|feed_movements)\[(\d+)\]\.(\w+)$")


def _traducir_estado(estado) -> str:
    """El estado en español, con el valor crudo como respaldo (`S1-I18N-01`)."""
    crudo = getattr(estado, "value", estado)
    return ESTADO_ES.get(str(crudo), str(crudo))


def _parsear_submovimiento(field_name: str) -> tuple[str, int, str] | None:
    """`bird_movements[12].avg_weight` → `("bird_movements", 12, "avg_weight")`."""
    encontrado = _PATRON_SUBMOVIMIENTO.match(field_name or "")
    if encontrado is None:
        return None
    tabla, fila_id, campo = encontrado.groups()
    return tabla, int(fila_id), campo


def etiqueta_de_campo(field_name: str) -> str:
    """Nombre funcional (español) de un campo corregible; nunca el identificador técnico (`AC-S2-C03`)."""
    parseado = _parsear_submovimiento(field_name)
    campo = parseado[2] if parseado is not None else field_name
    return ETIQUETAS_CAMPO.get(campo, campo)


def _campos_admitidos(event, es_recepcion_breeder: bool = False) -> str:
    """Lista de campos corregibles: los del evento y los de sus filas, con su id."""
    admitidos = sorted(campos_corregibles())
    for tabla, campos in SUBMOV_CORREGIBLES.items():
        filas = event.bird_movements if tabla == "bird_movements" else event.feed_movements
        for fila in filas:
            for campo in sorted(campos):
                if tabla == "bird_movements" and campo == "quantity" and es_recepcion_breeder:
                    continue
                admitidos.append(f"{tabla}[{fila.id}].{campo}")
    return ", ".join(admitidos)


def _convertir_valor_de_fila(field_name: str, campo: str, valor: str | None):
    """Convierte el texto recibido al tipo de la columna de la fila (400 en español).

    Cantidades y semanas son enteros ≥ 0; el peso medio y los kilos son decimales > 0.
    Vacío/`None` solo vale para `avg_weight` y `week_number` (`NULL` = sin dato).
    """
    opcional = campo in ("avg_weight", "week_number")
    if valor is None or str(valor).strip() == "":
        if opcional:
            return None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"«{etiqueta_de_campo(field_name)}» requiere un valor numérico",
        )
    texto = str(valor).strip()
    decimal = campo in ("avg_weight", "quantity_kg")
    try:
        numero = float(texto) if decimal else int(texto)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El valor '{valor}' no es válido para «{etiqueta_de_campo(field_name)}»: "
                f"se esperaba un {'número decimal' if decimal else 'número entero'}"
            ),
        ) from None
    if numero < 0 or (decimal and numero <= 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El valor '{valor}' no es válido para «{etiqueta_de_campo(field_name)}»: "
                "debe ser mayor a cero"
            ),
        )
    return numero


async def _es_lote_breeder(operaciones, lot_id: int | None) -> bool:
    """`Lot.bird_type` del lote es reproductoras (`BR-20`: cuadre de recepción)."""
    if lot_id is None:
        return False
    tipo = await operaciones._tipo_de_lote(lot_id)
    return getattr(tipo, "value", tipo) == "breeder"


def _tipo_de_valor(python_type) -> str:
    """`value_type` del contrato del selector: text | integer | decimal | date."""
    from datetime import date as _date

    if isinstance(python_type, type):
        if issubclass(python_type, _date):
            return "date"
        if issubclass(python_type, bool):
            return "text"
        if issubclass(python_type, int):
            return "integer"
        if issubclass(python_type, float):
            return "decimal"
    return "text"


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
        # `AC-S2-C03`: el aviso se lee en el formulario, junto al dato; el nombre técnico no.
        if tipo is _date:
            descripcion = "una fecha (AAAA-MM-DD)"
        elif tipo is int:
            descripcion = "un número entero"
        elif tipo is float:
            descripcion = "un número decimal"
        elif tipo is bool:
            descripcion = "sí o no"
        elif tipo is dict:
            descripcion = "un objeto JSON"
        else:
            descripcion = "texto"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El valor '{valor}' no es válido para «{etiqueta_de_campo(campo)}»: "
                f"se esperaba {descripcion}"
            ),
        ) from None
