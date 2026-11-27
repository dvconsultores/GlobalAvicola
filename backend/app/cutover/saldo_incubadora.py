"""SPEC 018 §10 · saldo de apertura de incubadora disponible para cargar — una sola semántica.

Preview (derivado `eggs_available_to_set`), reconciliación (`current.eggs_available_hatchery`) y BR-03
operativo (`get_hatchery_egg_balance`) leen el saldo de apertura con ESTA función: para los mismos datos no
puede haber dos verdades.

- V4 (`CUTOVER_HATCHERY_V4`, OD-HATCH-V4-02): `received − set − oversized − dirty − broken − pit` solo si
  los seis son KNOWN. Si cualquiera es UNKNOWN el saldo es **UNKNOWN** (`None`): `UNKNOWN ≠ 0` y
  `UNKNOWN ≠ seguro de ignorar`. La suma conocida sirve para detectar una imposibilidad (validación de
  consistencia, D-21), **nunca** para autorizar consumo.
- V3 histórica: su contrato no tenía esos componentes; el saldo es `received − set` (sin cambios).
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .contracts import KNOWN

#: Salidas PRE-CARGA del huevo recibido (SPEC 018 §9 · D-21): no incubables y fosa.
COMPONENTES_PRE_CARGA = ("eggs_non_incubable_oversized", "eggs_non_incubable_dirty",
                         "eggs_non_incubable_broken", "fertile_eggs_to_pit")

#: Mensaje funcional de BR-03 cuando el saldo de apertura no es exacto (sin nombres técnicos).
MENSAJE_SALDO_INCOMPLETO = (
    "No se puede determinar el saldo disponible para cargar porque la carga inicial de Incubadora "
    "contiene valores desconocidos. Corrija o complete la carga inicial antes de registrar una nueva "
    "carga de huevos."
)
#: Código de la regla para la respuesta 400 (`rule`).
REGLA_SALDO_INCOMPLETO = "CUTOVER_BALANCE_INCOMPLETE"


def saldo_apertura_por_cargar(valores: dict[str, Optional[int]], es_v4: bool) -> Optional[int]:
    """Saldo exacto de apertura por cargar, o `None` (UNKNOWN) si falta un componente necesario.

    `valores` lleva cada campo como entero (KNOWN) o `None` (UNKNOWN). Un `0` conocido es un cero real.
    """
    recibidos, cargados = valores.get("eggs_received"), valores.get("eggs_set")
    if recibidos is None or cargados is None:
        return None
    if not es_v4:
        return recibidos - cargados
    componentes = [valores.get(campo) for campo in COMPONENTES_PRE_CARGA]
    if any(valor is None for valor in componentes):
        return None
    return recibidos - cargados - sum(componentes)


def valores_de_apertura(apertura: Any) -> dict[str, Optional[int]]:
    """Valores KNOWN de un `HatcheryOpening` (`None` = UNKNOWN o no aplicable; nunca un 0 inventado)."""
    return {
        campo: (getattr(apertura, campo) if getattr(apertura, f"{campo}_status") == KNOWN else None)
        for campo in ("eggs_received", "eggs_set") + COMPONENTES_PRE_CARGA
    }


async def version_de_apertura(db: AsyncSession, lot_id: int) -> Optional[str]:
    """Versión de plantilla del batch que aplicó la apertura del lote (`None` si no hay batch aplicado)."""
    from .models import CutoverBatch, CutoverItem, CutoverItemStatus

    return (await db.execute(
        select(CutoverBatch.template_version)
        .join(CutoverItem, CutoverItem.batch_id == CutoverBatch.id)
        .where(CutoverItem.lot_id == lot_id,
               CutoverItem.validation_status == CutoverItemStatus.APPLIED.value,
               CutoverBatch.business_unit == "hatchery")
        .order_by(CutoverItem.id.desc())
        .limit(1)
    )).scalar_one_or_none()


def es_version_v4(version: Optional[str]) -> bool:
    """V4 o posterior sin batch identificable ⇒ semántica estricta V4 (fail-safe); solo V3 es la histórica."""
    return version != "v3" if version is not None else True


async def saldo_apertura_del_lote(db: AsyncSession, lot_id: int) -> tuple[bool, Optional[int]]:
    """`(hay_apertura, saldo)` del lote: sin apertura migrada ⇒ `(False, 0)`; con apertura ⇒ saldo exacto o `None`."""
    from .models import HatcheryOpening

    apertura = (await db.execute(
        select(HatcheryOpening).where(HatcheryOpening.lot_id == lot_id))).scalar_one_or_none()
    if apertura is None:
        return False, 0
    es_v4 = es_version_v4(await version_de_apertura(db, lot_id))
    return True, saldo_apertura_por_cargar(valores_de_apertura(apertura), es_v4)

