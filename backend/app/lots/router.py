"""REST API router for Lot management."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from . import schemas
from ..tenancy import verificar_vinculo_generacional
from .service import LotService

router = APIRouter(route_class=RutaTransaccional, prefix="/lots", tags=["Lots"])


def _service(db: AsyncSession, user: dict):
    return LotService(db, user)


# ============================================================
# Lot CRUD
# ============================================================

@router.get("", response_model=list[schemas.LotRead])
async def list_lots(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    farm_id: int | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    items, total = await _service(db, current_user).get_lots(
        skip=skip, limit=limit, search=search, farm_id=farm_id, status=status,
    )
    return [schemas.LotRead.model_validate(item) for item in items]


@router.post("", response_model=schemas.LotRead, status_code=201)
async def create_lot(
    data: schemas.LotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    lot = await _service(db, current_user).create_lot(data)
    return schemas.LotRead.model_validate(lot)


@router.get("/{lot_id}", response_model=schemas.LotDetailRead)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    service = _service(db, current_user)
    lot = await service.get_lot(lot_id)
    result = schemas.LotDetailRead.model_validate(lot)
    # Eager load phases and opening balance
    result.phases = [
        schemas.LotPhaseRead.model_validate(p)
        for p in (await service.get_lot_phases(lot_id))
    ]
    ob = await service.get_opening_balance(lot_id)
    if ob:
        result.opening_balance = schemas.OpeningBalanceRead.model_validate(ob)
    return result


@router.put("/{lot_id}", response_model=schemas.LotRead)
async def update_lot(
    lot_id: int,
    data: schemas.LotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "update")),
):
    lot = await _service(db, current_user).update_lot(lot_id, data)
    return schemas.LotRead.model_validate(lot)


@router.post("/{lot_id}/close", response_model=schemas.LotClosureSummary)
async def close_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    """
    `BR-05` / `G-09`. Cierra el lote y devuelve su resumen final.

    `GA-REM-029 AC02`. Antes validaba el resultado como `LotRead`, pero el servicio
    devuelve un resumen, no el lote: eran cuatro fuentes concordantes contra una línea.
    """
    return await _service(db, current_user).close_lot(lot_id)


# ============================================================
# Manual Activation (Opening Balance)
# ============================================================

@router.post("/activate-manual", response_model=schemas.OpeningBalanceRead, status_code=201)
async def activate_manual(
    data: schemas.OpeningBalanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    ob = await _service(db, current_user).activate_manual(data)
    return schemas.OpeningBalanceRead.model_validate(ob)


@router.get("/{lot_id}/opening-balance", response_model=schemas.OpeningBalanceRead)
async def get_opening_balance(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    ob = await _service(db, current_user).get_opening_balance(lot_id)
    if not ob:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Balance de apertura no encontrado")
    return schemas.OpeningBalanceRead.model_validate(ob)


# ============================================================
# Lot Phases
# ============================================================

@router.get("/{lot_id}/phases", response_model=list[schemas.LotPhaseRead])
async def get_lot_phases(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    phases = await _service(db, current_user).get_lot_phases(lot_id)
    return [schemas.LotPhaseRead.model_validate(p) for p in phases]


@router.post("/{lot_id}/phases", response_model=schemas.LotPhaseRead, status_code=201)
async def add_lot_phase(
    lot_id: int,
    data: schemas.LotPhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    if data.lot_id != lot_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="lot_id mismatch")
    phase = await _service(db, current_user).add_phase(data)
    return schemas.LotPhaseRead.model_validate(phase)


# ============================================================
# T-083: Generational Traceability
# ============================================================

@router.get("/{lot_id}/traceability", response_model=schemas.TraceabilityNode)
async def get_lot_traceability(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "read")),
):
    """Return full generational traceability tree for a lot (egg batches + chick batches)."""
    from sqlalchemy import select
    from .models import EggBatch, ChickBatch

    # Use LotService to validate company isolation
    svc = _service(db, current_user)
    lot = await svc.get_lot(lot_id)

    egg_sent_r = await db.execute(select(EggBatch).where(EggBatch.source_lot_id == lot_id))
    egg_sent = egg_sent_r.scalars().all()
    egg_recv_r = await db.execute(select(EggBatch).where(EggBatch.hatchery_lot_id == lot_id))
    egg_recv = egg_recv_r.scalars().all()
    chick_sent_r = await db.execute(select(ChickBatch).where(ChickBatch.hatchery_lot_id == lot_id))
    chick_sent = chick_sent_r.scalars().all()
    # Received chicks: destination_lot_id (generalized) OR legacy broiler_lot_id
    from sqlalchemy import or_
    chick_recv_r = await db.execute(
        select(ChickBatch).where(
            or_(
                ChickBatch.destination_lot_id == lot_id,
                ChickBatch.broiler_lot_id == lot_id,
            )
        )
    )
    chick_recv = chick_recv_r.scalars().all()

    lot_ref = schemas.LotRef(
        id=lot.id, lot_code=lot.lot_code or f"L-{lot.id}",
        bird_type=lot.bird_type.value if lot.bird_type else None,
        status=lot.status.value if hasattr(lot.status, "value") else str(lot.status),
    )
    # `GA-REM-031-A` · `R-178` · `OD-10 §2.5`: el árbol muestra el linaje **efectivo**, derivado del
    # estado de los eventos del par; la fila se conserva (historia, `BR-10`).
    estados = await _estado_de_eventos(db, egg_sent + egg_recv + chick_sent + chick_recv)
    return schemas.TraceabilityNode(
        lot=lot_ref,
        egg_batches_sent=_vinculos_efectivos(egg_sent, estados, schemas.EggBatchRead, "emisor"),
        egg_batches_received=_vinculos_efectivos(egg_recv, estados, schemas.EggBatchRead, "receptor"),
        chick_batches_sent=_vinculos_efectivos(chick_sent, estados, schemas.ChickBatchRead, "emisor"),
        chick_batches_received=_vinculos_efectivos(chick_recv, estados, schemas.ChickBatchRead, "receptor"),
    )


async def _estado_de_eventos(db: AsyncSession, vinculos) -> dict:
    """Estado de los eventos de despacho y recepción referenciados por los vínculos (una consulta)."""
    from sqlalchemy import select

    from ..operations.models import OperationalEvent

    ids = {i for v in vinculos for i in (v.dispatch_event_id, v.reception_event_id) if i is not None}
    if not ids:
        return {}
    filas = await db.execute(select(OperationalEvent.id, OperationalEvent.status).where(OperationalEvent.id.in_(ids)))
    return {fila_id: estado for fila_id, estado in filas.all()}


def _vinculos_efectivos(vinculos, estados: dict, lectura, lado: str) -> list:
    """`GA-REM-031-A` §A.1.1: un traspaso cuyo despacho está anulado desaparece de ambos lados
    (`OD-10 §2.5`); uno cuya recepción está anulada queda **incompleto** para el emisor (`GA-REM-008 AC04`)
    y desaparece para el receptor. Los vínculos manuales (sin eventos) se listan siempre. Solo lectura:
    la fila no cambia.
    """
    from ..operations.models import EventStatus

    salida = []
    for v in vinculos:
        if v.dispatch_event_id is not None and estados.get(v.dispatch_event_id) == EventStatus.CANCELLED:
            continue
        recepcion_anulada = v.reception_event_id is not None and estados.get(v.reception_event_id) == EventStatus.CANCELLED
        if recepcion_anulada and lado == "receptor":
            continue
        item = lectura.model_validate(v)
        if recepcion_anulada:
            item.quantity_received = None
            item.reception_date = None
        salida.append(item)
    return salida


@router.post("/egg-batches", response_model=schemas.EggBatchRead, status_code=201)
async def create_egg_batch(
    data: schemas.EggBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    """Link a breeder/grandparent lot → hatchery lot via egg batch."""
    from .models import EggBatch
    # `GA-REM-030 AC01/AC02/AC03`. El cuerpo entraba tal cual: cualquiera con `lots:create`
    # podía enlazar lotes ajenos o de dos compañías distintas (`R-60`).
    servicio = _service(db, current_user)
    await verificar_vinculo_generacional(db, servicio.company_id, [
        (data.source_lot_id, "Lote origen"),
        (data.hatchery_lot_id, "Lote de incubadora"),
    ])
    # `GA-REM-040` fase 5. Despachar es operar **sobre el lote origen**: exige tenerlo al
    # alcance. Sin esto, el usuario de una cadena podía crear un traspaso saliendo del lote
    # de otra — operar sobre la cadena ajena por la puerta del contrato.
    #
    # El **destino** no exige tener su cadena concedida, y eso es lo que lo hace un contrato
    # y no un permiso: se le dirige el traspaso sin obtener acceso a él (`OD-10.a`).
    origen = await servicio.get_lot(data.source_lot_id)
    destino = await _lote_destino(db, data.hatchery_lot_id)
    _validar_flujo("egg_batch", origen, destino)

    batch = EggBatch(**data.model_dump())
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return schemas.EggBatchRead.model_validate(batch)


@router.post("/chick-batches", response_model=schemas.ChickBatchRead, status_code=201)
async def create_chick_batch(
    data: schemas.ChickBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("lots", "create")),
):
    """Link a hatchery lot → destination lot (breeder or broiler) via chick batch."""
    from .models import ChickBatch
    # `GA-REM-030 AC06`. La misma guarda en las dos puertas: una regla aplicada en una y
    # ausente en la otra no es una regla.
    servicio = _service(db, current_user)
    await verificar_vinculo_generacional(db, servicio.company_id, [
        (data.hatchery_lot_id, "Lote de incubadora"),
        (data.destination_lot_id or data.broiler_lot_id, "Lote destino"),
    ])
    origen = await servicio.get_lot(data.hatchery_lot_id)
    destino = await _lote_destino(db, data.destination_lot_id or data.broiler_lot_id)
    _validar_flujo("chick_batch", origen, destino)

    payload = data.model_dump()
    # Sync: if destination_lot_id provided, also set broiler_lot_id for backward compat
    if payload.get("destination_lot_id") and not payload.get("broiler_lot_id"):
        payload["broiler_lot_id"] = payload["destination_lot_id"]
    elif payload.get("broiler_lot_id") and not payload.get("destination_lot_id"):
        payload["destination_lot_id"] = payload["broiler_lot_id"]
    batch = ChickBatch(**payload)
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return schemas.ChickBatchRead.model_validate(batch)


async def _lote_destino(db: AsyncSession, lot_id: int):
    """El lote de destino, **sin** exigir su cadena al que despacha.

    Se lee directo y no por `LotService`, a propósito: el servicio acota por unidad, y aquí
    el destino es legítimamente de otra cadena. Su pertenencia a la empresa ya la comprobó
    `verificar_vinculo_generacional`, que es la primera frontera y sigue siéndolo.
    """
    from sqlalchemy import select

    from ..masters.models import Lot

    return (await db.execute(select(Lot).where(Lot.id == lot_id))).scalar_one_or_none()


def _validar_flujo(flujo: str, origen, destino) -> None:
    """Las dos cadenas tienen que ser las que el flujo admite (`CROSS_MODULE_FLOW_MATRIX`).

    Aceptar un destino fuera de la tabla escribiría una cadena que `P-10` no puede
    reconstruir, y la trazabilidad generacional está certificada sobre ella.
    """
    from fastapi import HTTPException, status as _st

    from ..business_units.handoff import DestinoInvalido, validar_flujo

    try:
        validar_flujo(flujo, origen=origen, destino=destino)
    except DestinoInvalido as exc:
        raise HTTPException(status_code=_st.HTTP_400_BAD_REQUEST, detail=str(exc))
