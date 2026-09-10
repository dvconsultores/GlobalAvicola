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

    `company_id` nulo —la autoridad global sin contexto, o un actor sin empresa— **falla
    cerrado**: `OD-14.d` («sin empresa → todas las empresas» está prohibido) sustituyó la
    regla anterior, que aquí devolvía sin comprobar (`GA-REM-002-C` / `R-139` `AC26`). La
    administración legítima de la autoridad global pasa por situarse en una empresa
    (`switch-company`, `OD-14.b`).
    """
    if recurso_id is None:
        return
    if company_id is None:
        raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")

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


async def verificar_catalogo_de_empresa(
    db: AsyncSession,
    modelo: Any,
    recurso_id: int | None,
    company_id: int | None,
    etiqueta: str,
) -> None:
    """`GA-REM-002` enmienda D · `R-179`: un catálogo referenciado por un evento es de su empresa — o compartido.

    El ADDENDUM Wave 3 de esta misma spec fijó la semántica y acotó su ampliación a las referencias
    **estructurales** (`lot_id`, `farm_id`, `house_id`):

        «los catálogos maestros declaran `company_id` como anulable, lo que significa **global si es nulo,
         propio de la empresa si está fijado**, y bloquear una referencia a un catálogo compartido sería un error»

    De ahí las dos ramas: `company_id IS NULL` es un catálogo compartido y se acepta desde cualquier empresa;
    fijado, tiene que ser la del evento. La denegación conserva la semántica de `verificar_pertenencia`: el ajeno
    **se comporta como inexistente** (`BR-07`), para no distinguir «no existe» de «no es tuyo» (`AC26`).
    """
    if recurso_id is None:
        return
    if company_id is None:
        raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")
    fila = (await db.execute(
        select(modelo.company_id).where(modelo.id == recurso_id)
    )).one_or_none()
    if fila is None:
        raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")
    duenio = fila[0]
    if duenio is not None and duenio != company_id:
        raise BusinessRuleViolation(f"{etiqueta} no encontrado", "BR-07")


async def verificar_catalogos_del_evento(db: AsyncSession, company_id: int | None, **campos) -> None:
    """Los catálogos que un evento (o sus submovimientos) referencia, por nombre de campo.

    `GA-REM-002-D §D.2`. Solo entran los `TENANT_OWNED_NULLABLE`; los derivados (máquina de incubación,
    nacedora) se comprueban por su **padre**, y los `PLATFORM_GLOBAL` sin `company_id` —razas, fases
    productivas— no entran: no se convierten en dato de inquilino.
    """
    from .masters.models import (CullCause, FeedType, Hatcher, Hatchery, Incubator, Medication, MortalityCause,
                                 ProcessingPlant, Supplier, Transport, Vaccine)

    directos = {
        "supplier_id": (Supplier, "Proveedor"),
        "transport_id": (Transport, "Transporte"),
        "cause_id": (MortalityCause, "Causa de mortalidad"),
        "cull_cause_id": (CullCause, "Causa de descarte"),
        "vaccine_id": (Vaccine, "Vacuna"),
        "medication_id": (Medication, "Medicamento"),
        "destination_plant_id": (ProcessingPlant, "Planta de beneficio"),
        "feed_type_id": (FeedType, "Tipo de alimento"),
        "hatchery_id": (Hatchery, "Incubadora"),
    }
    derivados = {"incubator_id": (Incubator, "Incubadora"), "hatcher_id": (Hatcher, "Nacedora")}

    for campo, valor in campos.items():
        if valor is None:
            continue
        if campo in directos:
            modelo, etiqueta = directos[campo]
            await verificar_catalogo_de_empresa(db, modelo, valor, company_id, etiqueta)
        elif campo in derivados:
            modelo, etiqueta = derivados[campo]
            padre = (await db.execute(select(modelo.hatchery_id).where(modelo.id == valor))).one_or_none()
            if padre is None:
                raise BusinessRuleViolation(f"{etiqueta} no encontrada", "BR-07")
            await verificar_catalogo_de_empresa(db, Hatchery, padre[0], company_id, etiqueta)


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


# ── La empresa efectiva de una petición — `OD-11` · `GA-REM-040 AC-C09…AC-C14` ──

async def resolver_empresa_efectiva(
    db: AsyncSession, *, user: Any, reclamada: Any = None, puede_cambiar: bool = False
) -> int | None:
    """En qué empresa se evalúa esta petición.

    ```
    empresa efectiva  =  la empresa persistida del usuario
                         SALVO contexto de cambio EXPLÍCITAMENTE AUTORIZADO y válido
    ```

    Vive aquí y no dentro de `get_current_user` porque un servicio o una tarea de fondo
    también necesitan saber en qué empresa están, y no tienen petición de la que sacarlo.
    `R-48` había resuelto la regla; lo que faltaba era poder invocarla.

    **Una reclamación no es autoridad por existir.** Para un usuario normal manda la base y la
    reclamación se ignora: sobre esa propiedad se sostiene el aislamiento multiempresa, porque
    si bastara con pedir otra compañía no habría ninguna separación.

    Para quien sí puede cambiar de empresa, las tres condiciones se comprueban **aquí y ahora**,
    no al emitir el token: el token vive treinta minutos y la renovación lo reemite, de modo que
    una empresa desactivada entretanto seguiría dando contexto. Un contexto validado hace media
    hora no prueba nada sobre este instante.

    Devolver `None` significa **no hay empresa efectiva**, y el acceso productivo se deniega. No
    se resuelve «todas las empresas»: elegir una es un acto, no un valor por defecto (`OD-11.c`).

    Y lo que esto **no** contesta: ni qué unidades ve —eso es `unidades_efectivas`— ni qué puede
    hacer —eso es `RBAC`—. Tres dimensiones, y mezclarlas es de donde salen los atajos.
    """
    from .masters.models import Company

    persistida = getattr(user, "company_id", None)

    if reclamada is None or str(reclamada) == str(persistida):
        return persistida

    if not puede_cambiar:
        # `R-48`: la reclamación se descarta y manda la base. No es un error del cliente
        # —el token pudo emitirse antes de un cambio legítimo—, es que no tiene autoridad.
        return persistida

    try:
        destino = int(reclamada)
    except (TypeError, ValueError):
        return None

    activa = (await db.execute(
        select(Company.id).where(Company.id == destino, Company.is_active.is_(True))
    )).scalar_one_or_none()
    return destino if activa is not None else None
