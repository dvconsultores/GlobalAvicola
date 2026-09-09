"""Carga y administración de curvas estándar de peso — `GA-REM-037`, decisión `OD-06`.

La curva es la referencia contra la que se juzga si un lote va bien. Por eso la carga es
**todo o nada** (`AC06`): una tabla a medias no es una curva incompleta, es una curva
**equivocada**, y un lote evaluado contra ella recibiría un veredicto falso sin que nada
lo delate. Se valida entera antes de escribir una sola fila.

El motor que la consume vive aparte, en `app.operations.weight_curve`: aquí se decide qué
entra, allí qué significa.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas


def _error(fila: int, campo: str, motivo: str) -> dict:
    """Una fila del informe de rechazo. `AC06` exige fila, campo y motivo."""
    return {"fila": fila, "campo": campo, "motivo": motivo}


def validar_tabla(puntos: list[schemas.WeightCurvePointIn]) -> list[dict]:
    """Devuelve **todos** los defectos de la tabla, no solo el primero.

    Quien carga una tabla de 60 filas desde el PDF del proveedor necesita ver los seis
    errores de una vez; devolver el primero convierte la carga en seis viajes.
    """
    errores: list[dict] = []
    edades_vistas: dict[int, int] = {}

    for indice, punto in enumerate(puntos, start=1):
        # `AC04`. Dos valores para el mismo día dejarían la curva ambigua: el motor
        # tendría que elegir, y cualquier elección sería arbitraria.
        if punto.age_days in edades_vistas:
            errores.append(_error(
                indice, "age_days",
                f"edad {punto.age_days} repetida (ya definida en la fila "
                f"{edades_vistas[punto.age_days]})",
            ))
        else:
            edades_vistas[punto.age_days] = indice

        # `AC03`. Un rango invertido no es un rango: todo peso quedaría fuera.
        if punto.min_weight > punto.max_weight:
            errores.append(_error(
                indice, "min_weight",
                f"el mínimo ({punto.min_weight}) supera al máximo ({punto.max_weight})",
            ))

        # `AC03`. Un objetivo fuera de su propio rango describe una curva imposible.
        if punto.target_weight is not None and not (
            punto.min_weight <= punto.target_weight <= punto.max_weight
        ):
            errores.append(_error(
                indice, "target_weight",
                f"el objetivo ({punto.target_weight}) cae fuera del rango "
                f"[{punto.min_weight}, {punto.max_weight}]",
            ))

    return errores


async def _linea_del_usuario(
    db: AsyncSession, genetic_line_id: int, current_user: dict
) -> models.GeneticLine:
    """La línea genética, si el usuario puede verla. `AC24`.

    La curva no lleva `company_id` propio: hereda el de su línea, como `Incubator` hereda
    el de su `Hatchery`. Dos fuentes de tenencia para el mismo dato acaban discrepando.
    """
    # `GA-REM-002-C` / `R-139` · `OD-14.c`: la línea se resuelve **siempre** contra la
    # empresa efectiva. La condición anterior (`not is_super_admin and company_id`) dejaba
    # sin filtro a la autoridad global y también al actor sin empresa (`R-116`).
    company_id = current_user.get("company_id")
    if company_id is None:
        raise HTTPException(status_code=404, detail="Línea genética no encontrada")
    consulta = select(models.GeneticLine).where(
        models.GeneticLine.id == genetic_line_id,
        models.GeneticLine.company_id == company_id,
    )
    linea = (await db.execute(consulta)).scalar_one_or_none()
    if linea is None:
        raise HTTPException(status_code=404, detail="Línea genética no encontrada")
    return linea


async def crear_version(
    db: AsyncSession, datos: schemas.WeightCurveCreate, current_user: dict
) -> models.GeneticWeightCurve:
    """Crea una versión con su tabla completa, o no crea nada."""
    linea = await _linea_del_usuario(db, datos.genetic_line_id, current_user)

    errores = validar_tabla(datos.points)
    if errores:
        raise HTTPException(
            status_code=422,
            detail={"mensaje": "La tabla se rechazó entera", "errores": errores},
        )

    duplicada = (
        await db.execute(
            select(models.GeneticWeightCurve).where(
                models.GeneticWeightCurve.genetic_line_id == linea.id,
                models.GeneticWeightCurve.version_label == datos.version_label,
            )
        )
    ).scalar_one_or_none()
    if duplicada is not None:
        raise HTTPException(
            status_code=409,
            detail=f"La línea ya tiene una versión «{datos.version_label}»",
        )

    curva = models.GeneticWeightCurve(
        genetic_line_id=linea.id,
        version_label=datos.version_label,
        source=datos.source,
        is_active=False,  # se decide abajo, para pasar por la exclusividad
    )
    db.add(curva)
    await db.flush()

    for punto in datos.points:
        db.add(models.GeneticWeightCurvePoint(
            curve_id=curva.id,
            age_days=punto.age_days,
            min_weight=punto.min_weight,
            max_weight=punto.max_weight,
            target_weight=punto.target_weight,
        ))
    await db.flush()

    if datos.is_active:
        await activar(db, curva)

    await db.refresh(curva)
    return curva


async def activar(db: AsyncSession, curva: models.GeneticWeightCurve) -> None:
    """Marca esta versión como la activa de su línea, desactivando la anterior.

    «Activa» significa *la que toma un lote nuevo por defecto* (`AC09`), y solo puede
    haber una. No toca `Lot.weight_curve_id` de nadie: `AC08` es explícito en que publicar
    una curva nueva no reescribe la referencia de los lotes ya en marcha.
    """
    anteriores = (
        await db.execute(
            select(models.GeneticWeightCurve).where(
                models.GeneticWeightCurve.genetic_line_id == curva.genetic_line_id,
                models.GeneticWeightCurve.is_active.is_(True),
                models.GeneticWeightCurve.id != curva.id,
            )
        )
    ).scalars().all()
    for anterior in anteriores:
        anterior.is_active = False
    curva.is_active = True
    await db.flush()


async def version_activa(
    db: AsyncSession, genetic_line_id: int
) -> models.GeneticWeightCurve | None:
    """La versión activa de una línea, o `None` si la línea aún no tiene curva cargada."""
    return (
        await db.execute(
            select(models.GeneticWeightCurve).where(
                models.GeneticWeightCurve.genetic_line_id == genetic_line_id,
                models.GeneticWeightCurve.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
