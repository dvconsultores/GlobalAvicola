"""Pertenencia de recursos al inquilino — `GA-REM-002` `AC10` / `AC11`.

```
LIST FILTERING  ≠  TENANT DATA INTEGRITY
READ ISOLATION  ≠  WRITE ISOLATION
```

`R-42` lo demostró: los filtros de listado protegían la lectura mientras una escritura
aceptaba el `lot_id` de otra empresa. El evento quedaba archivado bajo la empresa A pero
ligado a un lote de B, y el saldo de aves —calculado por `lot_id`— quedaba contaminado.

El gate de la Wave 3 encontró que la lección no se había extendido: `farm_id`, `house_id` y
`event_id` seguían sin comprobarse.

**Existir no basta.** Para toda clave foránea estructural que el cliente puede enviar, el
recurso referenciado debe **pertenecer** a la compañía efectiva.

Vive aquí, en un único sitio, y no repartido por los servicios: una regla de aislamiento
aplicada en un sitio y ausente en otro no es una regla, es una casualidad.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .operations.validators import BusinessRuleViolation


async def verificar_pertenencia(
    db: AsyncSession,
    modelo: Any,
    recurso_id: int | None,
    company_id: int | None,
    etiqueta: str,
) -> None:
    """Comprueba que el recurso referenciado es de la compañía efectiva.

    Un recurso ajeno se comporta como **inexistente**, que es lo que debe parecerle a quien
    no tiene derecho a verlo: distinguir «no existe» de «no es tuyo» ya filtra información.

    `company_id` nulo —el Super Admin sin contexto— no impone filtro: opera sobre todas las
    compañías por definición, y acotarlo aquí rompería la administración legítima.
    """
    if recurso_id is None or company_id is None:
        return

    consulta = select(modelo.id).where(modelo.id == recurso_id)
    if hasattr(modelo, "company_id"):
        consulta = consulta.where(modelo.company_id == company_id)
    elif hasattr(modelo, "farm_id"):
        # El galpón pertenece a la compañía **a través de su granja**: no declara
        # `company_id` propio.
        from .masters.models import Farm

        consulta = (
            select(modelo.id)
            .join(Farm, Farm.id == modelo.farm_id)
            .where(modelo.id == recurso_id, Farm.company_id == company_id)
        )

    if (await db.execute(consulta)).scalar_one_or_none() is None:
        raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")


async def verificar_ubicacion(
    db: AsyncSession,
    company_id: int | None,
    farm_id: int | None = None,
    house_id: int | None = None,
    destination_farm_id: int | None = None,
) -> None:
    """Pertenencia de las referencias de ubicación de un evento operativo."""
    from .masters.models import Farm, House

    await verificar_pertenencia(db, Farm, farm_id, company_id, "Granja")
    await verificar_pertenencia(db, House, house_id, company_id, "Galpón")
    await verificar_pertenencia(db, Farm, destination_farm_id, company_id, "Granja destino")


async def verificar_vinculo_generacional(
    db: AsyncSession,
    company_id: int | None,
    extremos: list[tuple[int | None, str]],
) -> None:
    """Pertenencia y coherencia de los dos extremos de un vínculo generacional.

    `GA-REM-030` / `R-60`. Son **dos** reglas y conviene no fundirlas:

    `A` · **pertenencia del actor** — quien no es Super Admin solo referencia lotes de su
    compañía efectiva. Es `verificar_pertenencia` sin más, con su exención documentada para
    el Super Admin sin contexto.

    `B` · **coherencia del par** — los dos lotes son de la **misma** compañía, y esto
    vincula a *todo* actor, Super Admin incluido. No es autorización sino integridad del
    dato: `EggBatch` y `ChickBatch` no declaran `company_id`, de modo que su dueño es
    derivado de los lotes que enlazan. Un vínculo entre compañías queda **sin dueño
    posible** y hace insatisfacible `GA-REM-008 AC06` —ya certificado—, que promete que un
    usuario nunca obtiene un lote de trazabilidad que referencie lotes de otra compañía.

    El Super Admin conserva su autoridad global: puede crear vínculos en cualquier compañía.
    Lo que no gana es la de crear un registro que ninguna compañía puede reclamar.
    """
    from .masters.models import Lot

    for recurso_id, etiqueta in extremos:
        await verificar_pertenencia(db, Lot, recurso_id, company_id, etiqueta)

    declarados = [(i, e) for i, e in extremos if i is not None]
    if not declarados:
        return

    filas = dict(
        (await db.execute(
            select(Lot.id, Lot.company_id).where(Lot.id.in_([i for i, _ in declarados]))
        )).all()
    )

    # Existir es requisito previo a comparar. Sin esto, un identificador inventado llegaba
    # al `INSERT` y salía como 500 por violación de clave foránea en vez de como un 400
    # con el contrato de error vigente.
    for recurso_id, etiqueta in declarados:
        if recurso_id not in filas:
            raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")

    if len({filas[i] for i, _ in declarados}) > 1:
        raise BusinessRuleViolation(
            "Los lotes de un vínculo de trazabilidad deben pertenecer a la misma compañía",
            "BR-07",
        )
