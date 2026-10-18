"""
Enriquecimiento **aditivo** de los listados.

Los listados (`/lots`, `/operations`, bandejas de revisión y aprobación) devuelven
instancias ORM. Para que la UI muestre nombres en lugar de ids se anotan sobre cada
instancia atributos **no mapeados** —el mismo patrón que
`integrations.sap.service._anotar_cadena_de_las_ordenes`— y los esquemas `Read` los
declaran como campos opcionales. No se persiste nada ni se altera la fila: el atributo
solo viaja en la respuesta.

El coste es acotado: tres consultas por página (lotes, granjas, usuarios) y dos para los
lotes (granjas, naves), con `.in_(ids)` sobre los ids ya filtrados por empresa, de modo
que aquí no se repite ningún filtro de alcance.
"""
from sqlalchemy import select

from ..auth.models import User
from ..masters.models import Farm, House, Lot

__all__ = ["anotar_nombres", "anotar_nombres_de_lotes"]


def _ids(valores) -> list[int]:
    return sorted({v for v in valores if v is not None})


async def anotar_nombres(db, eventos: list) -> None:
    """Anota `lot_code`, `farm_name` y `registered_by_name` en cada evento.

    `registered_by_name` es "nombre apellidos" y cae al usuario cuando no hay nombre
    declarado (hay cuentas técnicas que no lo tienen).
    """
    if not eventos:
        return

    lot_ids = _ids(getattr(ev, "lot_id", None) for ev in eventos)
    farm_ids = _ids(getattr(ev, "farm_id", None) for ev in eventos)
    user_ids = _ids(getattr(ev, "registered_by_id", None) for ev in eventos)

    codigos: dict[int, str] = {}
    if lot_ids:
        filas = await db.execute(
            select(Lot.id, Lot.lot_code).where(Lot.id.in_(lot_ids))
        )
        codigos = dict(filas.all())

    granjas: dict[int, str] = {}
    if farm_ids:
        filas = await db.execute(
            select(Farm.id, Farm.name).where(Farm.id.in_(farm_ids))
        )
        granjas = dict(filas.all())

    usuarios: dict[int, str] = {}
    if user_ids:
        filas = await db.execute(
            select(User.id, User.first_name, User.last_name, User.username)
            .where(User.id.in_(user_ids))
        )
        for uid, first, last, username in filas.all():
            nombre = f"{(first or '').strip()} {(last or '').strip()}".strip()
            nombre = nombre or (username or "").strip()
            if nombre:
                usuarios[uid] = nombre

    for ev in eventos:
        ev.lot_code = codigos.get(getattr(ev, "lot_id", None))
        ev.farm_name = granjas.get(getattr(ev, "farm_id", None))
        ev.registered_by_name = usuarios.get(getattr(ev, "registered_by_id", None))


async def anotar_nombres_de_lotes(db, lotes: list) -> None:
    """Anota `farm_name` y `house_name` en cada lote."""
    if not lotes:
        return

    farm_ids = _ids(getattr(lote, "farm_id", None) for lote in lotes)
    house_ids = _ids(getattr(lote, "house_id", None) for lote in lotes)

    granjas: dict[int, str] = {}
    if farm_ids:
        filas = await db.execute(
            select(Farm.id, Farm.name).where(Farm.id.in_(farm_ids))
        )
        granjas = dict(filas.all())

    naves: dict[int, str] = {}
    if house_ids:
        filas = await db.execute(
            select(House.id, House.name).where(House.id.in_(house_ids))
        )
        naves = dict(filas.all())

    for lote in lotes:
        lote.farm_name = granjas.get(getattr(lote, "farm_id", None))
        lote.house_name = naves.get(getattr(lote, "house_id", None))
