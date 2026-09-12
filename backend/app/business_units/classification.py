"""Clasificación pendiente de la cadena productiva — `GA-REM-040` fase 6 · `OD-10.c`.

    SIN CLASIFICAR  ≠  DE TODA LA EMPRESA
    SIN CLASIFICAR  ≠  UNA QUINTA CADENA
    SIN CLASIFICAR  ≠  BORRADO

Un evento sin lote —las inspecciones de granja lo permiten desde `i9j0k1l2m3n4`— no puede
derivar su cadena. No se adivina, no se abre y no se borra: queda **pendiente**, y lo ven dos
partes nombradas —quien lo registró y el control autorizado—, no «todos».

La importación de abuelas (`R-153` · `OD-25 (B)`) es la excepción **nombrada**: su tipo ya
dice su cadena —`grandparent`, y su plan la exige (`BR-22`)—, así que deriva de él y nunca
queda pendiente; sin esa derivación su aprobación —la que crea el lote— sería inalcanzable.

**El estado se deriva, no se guarda.** Un evento está pendiente cuando ni su lote ni su columna
de clasificación dicen a qué cadena pertenece. Persistir además un `status` daría dos fuentes que
discreparían el día que alguien rellene el lote sin tocar el estado — el mismo error que
`GA-REM-039` evitó al no guardar el gerente dentro del área.

Y una regla que es fácil de perder de vista: **haber creado el registro no es un salvoconducto
permanente**. En cuanto está clasificado manda el alcance normal, y si el creador no tiene esa
cadena, deja de verlo.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

#: Quién puede clasificar. Es un acto de **configuración** —decide a qué cadena pertenece un
#: registro— y por eso vive en el permiso de administración de datos maestros, no en el de
#: operar. Un permiso propio pertenecería al catálogo de `GA-REM-034`, y crearlo aquí sería
#: ampliar el `RBAC` desde una fase que no lo gobierna: queda anotado para la fase 7.
PERMISO_DE_CLASIFICACION = ("masters", "update")


def puede_clasificar(current_user: dict) -> bool:
    """`§5`: por permiso, nunca por el nombre del rol.

    `GA-REM-034` permite crear roles y el nombre es texto editable: si bastara con llamarse
    «Contralor», la capacidad se saltaría desde la pantalla de roles.
    """
    from ..auth.security import tiene_permiso

    return tiene_permiso(current_user, *PERMISO_DE_CLASIFICACION)


async def estado_de_clasificacion(db: AsyncSession, evento) -> str:
    """`derived`, `manual` o `pending`. Derivado del dato, no leído de una columna."""
    from ..masters.models import Lot

    if evento.lot_id is not None:
        tipo = (await db.execute(
            select(Lot.bird_type).where(Lot.id == evento.lot_id))).scalar_one_or_none()
        if tipo is not None:
            return "derived"
    if (evento.lot_id is None and evento.business_unit_id is None
            and getattr(evento.event_type, "value", evento.event_type) == "grandparent_import"):
        # `R-153` · `OD-25 (B)`: el tipo es inequívoco; deriva de él (ver `predicado_de_evento`).
        return "derived"
    return "manual" if evento.business_unit_id is not None else "pending"


def predicado_de_evento(unidades, company_id):
    """Los eventos cuya cadena está **al alcance**, por derivación o por clasificación.

    ```
    lote alcanzable            el lote lleva la cadena y el usuario la tiene
      OR
    clasificado a mano a una   alguien autorizado dijo a qué cadena pertenece
      habilitación alcanzable
    ```

    Lo pendiente queda fuera de las dos ramas, y es deliberado: no se filtra por accidente,
    se excluye por no poder atribuirse. Su superficie es la bandeja, aparte.
    """
    from ..masters.models import Lot
    from ..operations.models import OperationalEvent
    from .models import BusinessUnit, CompanyBusinessUnit
    from .scope import lotes_alcanzables, predicado

    por_lote = OperationalEvent.lot_id.in_(lotes_alcanzables(company_id, unidades))

    habilitaciones = select(CompanyBusinessUnit.id).where(
        CompanyBusinessUnit.company_id == company_id,
        CompanyBusinessUnit.is_enabled.is_(True),
    )
    condicion = predicado(Lot, unidades)
    if condicion is None:  # pragma: no cover - `Lot` siempre tiene política
        return por_lote
    habilitaciones = habilitaciones.join(
        BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id
    ).where(BusinessUnit.is_active.is_(True),
            BusinessUnit.code.in_(list(unidades) or [""]))

    ramas = [por_lote, OperationalEvent.business_unit_id.in_(habilitaciones)]
    # `R-153` · `OD-25 (B)`: tercer origen de cadena — el **tipo del evento** cuando es
    # inequívoco. La importación de abuelas no admite otra cadena (su plan la exige), así que
    # sin lote y sin clasificación manual se atribuye a `grandparent` en vez de quedar
    # pendiente: pendiente significaría inaprobable —la aprobación es la que crea el lote—.
    # La atribución manual manda cuando existe (la rama solo cubre `NULL`) y la unidad
    # apagada sigue siendo inaccesible porque `unidades` son las efectivas.
    if "grandparent" in (unidades or ()):
        from ..operations.models import EventType

        ramas.append(and_(
            OperationalEvent.event_type == EventType.GRANDPARENT_IMPORT,
            OperationalEvent.lot_id.is_(None),
            OperationalEvent.business_unit_id.is_(None),
        ))

    return or_(*ramas)


def predicado_de_pendientes(current_user: dict):
    """Los pendientes que este actor puede ver. `OD-10.c §4.1`.

    ```
    quien lo registró                   sus propios pendientes
    el control autorizado               los de su empresa
    ```

    **No** «todos los de la empresa» para cualquiera, ni «los de mi cadena»: un registro
    pendiente no tiene cadena, así que no hay cadena por la que reclamarlo.
    """
    from ..masters.models import Lot
    from ..operations.models import EventType, OperationalEvent

    # Pendiente es **no poder derivar ni tener decidido**. Un campo nulable no basta: si el
    # evento tiene lote y el lote tiene cadena, se deriva y no pasa por aquí. Sin esta
    # segunda condición, la bandeja se llenaría de registros que no necesitan a nadie.
    derivables = select(Lot.id).where(Lot.bird_type.isnot(None))
    sin_clasificar = and_(
        OperationalEvent.business_unit_id.is_(None),
        or_(OperationalEvent.lot_id.is_(None),
            OperationalEvent.lot_id.notin_(derivables)),
        # `R-153` · `OD-25 (B)`: el tipo inequívoco deriva la cadena (`predicado_de_evento`);
        # mientras derive, no hay nada que clasificar y la bandeja no lo reclama.
        OperationalEvent.event_type != EventType.GRANDPARENT_IMPORT,
    )
    de_la_empresa = OperationalEvent.company_id == current_user.get("company_id")

    if puede_clasificar(current_user):
        return (sin_clasificar, de_la_empresa)
    return (sin_clasificar, de_la_empresa,
            OperationalEvent.registered_by_id == current_user.get("id"))


class ClasificacionInvalida(ValueError):
    """La habilitación elegida no sirve para clasificar este registro."""


async def clasificar(db: AsyncSession, *, evento, company_business_unit, actor: dict):
    """Fija la cadena de un registro que no podía derivarla. `T-040-17`.

    Comprueba lo que hay que comprobar, y **no hace nada más**:

        la habilitación es de la MISMA empresa que el registro
        la habilitación está activa
        el registro no tenía ya cadena derivable

    Y sobre todo, lo que **no** hace, porque sería la forma más silenciosa de abrir el
    sistema:

        NO concede la cadena a nadie          clasificar no es autorizar
        NO habilita la unidad a la empresa    eso es configuración comercial
        NO toca `bird_type` del lote          el dato de dominio es de otro eje
    """
    if company_business_unit is None:
        raise ClasificacionInvalida("la habilitación no existe")
    if company_business_unit.company_id != evento.company_id:
        raise ClasificacionInvalida(
            "la habilitación pertenece a otra empresa que el registro")
    if not company_business_unit.is_enabled:
        raise ClasificacionInvalida("la unidad no está habilitada para la empresa")

    from datetime import datetime, timezone

    anterior = await estado_de_clasificacion(db, evento)
    if anterior == "derived":
        raise ClasificacionInvalida(
            "el registro ya deriva su cadena de su lote: no hay nada que clasificar")

    evento.business_unit_id = company_business_unit.id
    evento.classified_at = datetime.now(timezone.utc)
    evento.classified_by_id = actor.get("id")
    await db.flush()

    # `§32`: en `P-09`, con el mecanismo que ya existe. Un registro paralelo daría dos
    # historias del mismo hecho.
    from ..audit.helpers import audit_accion
    from ..audit.models import AuditAction, AuditModule
    from .models import BusinessUnit

    codigo = (await db.execute(
        select(BusinessUnit.code)
        .where(BusinessUnit.id == company_business_unit.business_unit_id)
    )).scalar_one_or_none()

    await audit_accion(
        db, usuario={"id": actor.get("id"), "company_id": evento.company_id},
        accion=AuditAction.UPDATED, modulo=AuditModule.OPERATIONS,
        entity_type="operational_event", entity_id=str(evento.id),
        company_id=evento.company_id,
        previous_state=anterior, new_state=str(codigo),
    )
    return evento


#: Quién puede **corregir** una atribución ya hecha. Distinto del permiso de la primera
#: clasificación a propósito: sacar un registro de «pendiente» y cambiar una atribución que ya
#: estaba puesta no son el mismo acto ni el mismo riesgo. `corrections:correct` es el permiso
#: que el catálogo ya reserva para enmendar un registro, y esto es exactamente eso.
PERMISO_DE_RECLASIFICACION = ("corrections", "correct")


class ReclasificacionBloqueada(RuntimeError):
    """El registro ya produjo efectos y no se reclasifica en el sitio."""


async def efectos_productivos(db: AsyncSession, evento) -> list[str]:
    """Qué hechos ya ocurrieron por cuenta de este registro. `OD-10.d §4bis.3`.

    Cambiar la cadena de algo que ya se aprobó, ya cruzó una frontera o ya se envió a un
    sistema externo **reinterpreta hechos pasados**: los agregados de ayer pasarían a contar
    otra cosa, y la trazabilidad diría que ocurrió algo que no ocurrió así.

    Devuelve la lista de efectos encontrados, vacía si no hay ninguno. Se devuelve la lista y
    no un booleano para que la negativa pueda decir **por qué**: «no se puede» sin motivo
    obliga a adivinar qué hay que revertir.
    """
    from sqlalchemy import func

    from ..lots.models import ChickBatch, EggBatch
    from ..operations.models import EventStatus, OperationalEvent
    from ..review.models import ApprovalAction

    encontrados: list[str] = []

    consolidados = {EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
                    EventStatus.SAP_ERROR}
    if evento.status in consolidados:
        encontrados.append(f"el registro está en estado {evento.status.value!r}")

    for modelo, etiqueta in ((EggBatch, "un traspaso de huevo"),
                             (ChickBatch, "un traspaso de pollito")):
        cuantos = (await db.execute(
            select(func.count(modelo.id)).where(
                or_(modelo.dispatch_event_id == evento.id,
                    modelo.reception_event_id == evento.id))
        )).scalar_one()
        if cuantos:
            encontrados.append(f"participa en {etiqueta}")

    aprobaciones = (await db.execute(
        select(func.count(ApprovalAction.id))
        .where(ApprovalAction.event_id == evento.id)
    )).scalar_one()
    if aprobaciones:
        encontrados.append("tiene acciones de aprobación registradas")

    return encontrados


async def reclasificar(db: AsyncSession, *, evento, company_business_unit, motivo: str,
                       actor: dict):
    """Corrige una atribución ya hecha. `OD-10.d` · `AC-G10`…`AC-G14`.

    Es **alto control**, no una edición: exige permiso propio, motivo y que el registro no
    haya producido efectos aguas abajo. Ante la duda se deniega — si no se puede demostrar
    que no los tiene, tampoco se reclasifica.

    Y lo que **no** hace, que es tan importante como lo que hace:

        NO concede la cadena nueva a nadie
        NO habilita la unidad a la empresa
        NO devuelve el registro a «pendiente» ni restaura la excepción de quien lo registró
        NO reasigna a los hijos en cascada — eso reinterpretaría operaciones históricas
                                             sin que nadie las hubiera revisado

    La historia anterior no se borra: vive en `P-09`, que es donde vive el resto.
    """
    if company_business_unit is None:
        raise ClasificacionInvalida("la habilitación no existe")
    if company_business_unit.company_id != evento.company_id:
        raise ClasificacionInvalida(
            "la habilitación pertenece a otra empresa que el registro")
    if not company_business_unit.is_enabled:
        raise ClasificacionInvalida("la unidad no está habilitada para la empresa")
    if evento.business_unit_id is None:
        raise ClasificacionInvalida(
            "el registro no está clasificado: use la primera clasificación")

    efectos = await efectos_productivos(db, evento)
    if efectos:
        raise ReclasificacionBloqueada(
            "no se reclasifica en el sitio un registro con efectos ya producidos: "
            + "; ".join(efectos)
            + ". Revierta primero por los procesos que los gobiernan."
        )

    from datetime import datetime, timezone

    from .models import BusinessUnit, CompanyBusinessUnit

    async def _codigo(cbu_id):
        return (await db.execute(
            select(BusinessUnit.code)
            .join(CompanyBusinessUnit,
                  CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
            .where(CompanyBusinessUnit.id == cbu_id)
        )).scalar_one_or_none()

    anterior = await _codigo(evento.business_unit_id)
    nuevo = await _codigo(company_business_unit.id)

    evento.business_unit_id = company_business_unit.id
    evento.classified_at = datetime.now(timezone.utc)
    evento.classified_by_id = actor.get("id")
    await db.flush()

    from ..audit.helpers import audit_accion
    from ..audit.models import AuditAction, AuditModule

    await audit_accion(
        db, usuario={"id": actor.get("id"), "company_id": evento.company_id},
        accion=AuditAction.CORRECTED, modulo=AuditModule.OPERATIONS,
        entity_type="operational_event", entity_id=str(evento.id),
        company_id=evento.company_id,
        previous_state=str(anterior), new_state=str(nuevo),
        change_reason=motivo,
    )
    return evento
