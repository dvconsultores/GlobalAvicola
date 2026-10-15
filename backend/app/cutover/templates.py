"""SPEC 006 · Cutover v2 — plantillas por unidad de negocio (XLSX con catálogos y CSV).

`GET /cutover-templates/{bu}?format=xlsx|csv&batch_id=` — la BU la fija el contrato; si se
pasa `batch_id`, el batch debe ser de la empresa efectiva **y de esa BU** (la descarga sigue
al batch, nunca a un selector), y `Meta.cutover_datetime` queda rellenado.

XLSX: hojas `Instrucciones` (una fila por campo: significado, obligatorio, tipo, unidad,
formato, ejemplo, valores, UNKNOWN, N/A, destino), `Meta` (`template_version`, `schema_id`,
`company`, `business_unit`, `generated_at`, `cutover_datetime`), `Datos` (cabecera exacta del
contrato) y `Catalogos` (`catalog, code, description, status, parent_code`) construida para la
empresa efectiva y la BU, solo con maestros activos. CSV: solo la cabecera de `Datos`.

Gate: `cutover:create` (el mismo que crear el batch).
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import require_permission
from ..lots.models import OpeningBalance
from ..masters.models import (Area, Breed, Farm, GeneticLine, Hatcher, Hatchery, House, Incubator, Lot,
                              LotStatus, ProductivePhase)
from ..transaction import RutaTransaccional
from .contracts import CONTRACTS, UNIDADES, TemplateContract, contrato
from .models import CutoverBatch

router = APIRouter(route_class=RutaTransaccional, prefix="/cutover-templates", tags=["Cutover"])

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CSV_DELIMITER = ";"

CABECERA_INSTRUCCIONES = ("campo", "significado", "obligatorio", "tipo", "unidad", "formato", "ejemplo",
                          "valores_permitidos", "admite_UNKNOWN_(vacío)", "admite_N/A", "destino_tras_apply")

SEMANTICA = (
    "PLANTILLA DE CORTE OPERACIONAL (Cargas Iniciales) — cómo se llena",
    "",
    "Cada fila de la hoja Datos es un lote (o un proceso de incubación en curso) tal como estaba AL MOMENTO DEL CORTE.",
    "Semántica de cada celda de métrica (se conserva tal cual, jamás se fabrica un dato):",
    "  · celda VACÍA = UNKNOWN (no se conoce el dato en el sistema de origen)",
    "  · 0 = cero CONOCIDO (realmente cero)",
    "  · N/A = NOT_APPLICABLE (la métrica no aplica a este lote/fase)",
    "Fechas en formato AAAA-MM-DD. Fecha y hora del corte: AAAA-MM-DDTHH:MM:SS+00:00 (la fija el batch).",
    "Números enteros sin separador de miles; decimales con punto. Pesos en GRAMOS; alimento en KILOGRAMOS.",
    "Los códigos y nombres de maestros se toman de la hoja Catalogos (solo registros activos de su empresa).",
    "No use fórmulas, macros ni formatos como dato: el importador lee valores y rechaza fórmulas.",
    "No cambie la cabecera de la hoja Datos ni la hoja Meta.",
    "",
)


def _formato(tipo: str) -> str:
    return {"text": "texto", "int": "entero ≥ 0", "decimal": "decimal con punto", "date": "AAAA-MM-DD", "enum": "uno de la lista"}[tipo]


def _filas_instrucciones(c: TemplateContract) -> list[list]:
    filas: list[list] = [[linea] for linea in SEMANTICA]
    filas.append(list(CABECERA_INSTRUCCIONES))
    for f in c.fields:
        filas.append([
            f.name, f.meaning, "sí" if f.required else "no", f.kind, f.unit or "", _formato(f.kind), f.example or "",
            ", ".join(f.values), "sí" if f.allow_unknown else ("no (obligatorio)" if f.required else "vacío = sin dato"),
            "sí" if f.allow_na else "no", ", ".join(f.targets),
        ])
    return filas


async def catalogos(db: AsyncSession, company_id: int, c: TemplateContract) -> list[list]:
    """Filas `catalog, code, description, status, parent_code` de la empresa efectiva y la BU."""
    filas: list[list] = []
    activo = "active"
    fases = (await db.execute(select(ProductivePhase).where(ProductivePhase.is_active == True)  # noqa: E712
                              .order_by(ProductivePhase.order, ProductivePhase.id))).scalars().all()
    for fase in fases:
        if fase.code in c.phases:
            filas.append(["productive_phase", fase.code, fase.name, activo, ""])
    if c.business_unit == "hatchery":
        plantas = (await db.execute(select(Hatchery).where(Hatchery.company_id == company_id, Hatchery.is_active == True)  # noqa: E712
                                    .order_by(Hatchery.code, Hatchery.id))).scalars().all()
        for planta in plantas:
            filas.append(["hatchery", planta.code or "", planta.name, activo, ""])
            for inc in (await db.execute(select(Incubator).where(Incubator.hatchery_id == planta.id, Incubator.is_active == True)  # noqa: E712
                                         .order_by(Incubator.name))).scalars().all():
                filas.append(["incubator", inc.name, f"capacidad {inc.capacity or ''}".strip(), activo, planta.code or ""])
            for nac in (await db.execute(select(Hatcher).where(Hatcher.hatchery_id == planta.id, Hatcher.is_active == True)  # noqa: E712
                                         .order_by(Hatcher.name))).scalars().all():
                filas.append(["hatcher", nac.name, f"capacidad {nac.capacity or ''}".strip(), activo, planta.code or ""])
        fuentes = (await db.execute(select(Lot).where(
            Lot.company_id == company_id, Lot.status == LotStatus.ACTIVE,
            Lot.bird_type.in_(["grandparent", "breeder"])).order_by(Lot.lot_code))).scalars().all()
        for lote in fuentes:
            filas.append(["source_lot", lote.lot_code, f"{lote.bird_type.value if lote.bird_type else ''} · legado {lote.legacy_lot_code or '-'}",
                          activo, lote.bird_type.value if lote.bird_type else ""])
    else:
        granjas = (await db.execute(select(Farm).where(Farm.company_id == company_id, Farm.is_active == True)  # noqa: E712
                                    .order_by(Farm.code, Farm.id))).scalars().all()
        for granja in granjas:
            filas.append(["farm", granja.code or "", granja.name, activo, ""])
            for galpon in (await db.execute(select(House).where(House.farm_id == granja.id, House.is_active == True)  # noqa: E712
                                            .order_by(House.name))).scalars().all():
                filas.append(["house", galpon.name, f"capacidad {galpon.capacity or ''}".strip(), activo, granja.code or ""])
        areas = (await db.execute(select(Area).where(
            (Area.company_id == company_id) | (Area.company_id.is_(None)), Area.is_active == True).order_by(Area.code))).scalars().all()  # noqa: E712
        for area in areas:
            filas.append(["area", area.code or "", area.name, activo, ""])
        lineas = (await db.execute(select(GeneticLine).where(
            (GeneticLine.company_id == company_id) | (GeneticLine.company_id.is_(None)),
            GeneticLine.is_active == True).order_by(GeneticLine.code))).scalars().all()  # noqa: E712
        for linea in lineas:
            filas.append(["genetic_line", linea.code or "", linea.name, activo, ""])
            for raza in (await db.execute(select(Breed).where(Breed.genetic_line_id == linea.id, Breed.is_active == True)  # noqa: E712
                                          .order_by(Breed.name))).scalars().all():
                if raza.bird_type is None or raza.bird_type.value == c.bird_type:
                    filas.append(["breed", raza.name, raza.bird_type.value if raza.bird_type else "", activo, linea.code or ""])
    # Lotes existentes de la BU sin apertura (candidatos a existing_lot_code).
    con_opening = select(OpeningBalance.lot_id)
    candidatos = (await db.execute(select(Lot).where(
        Lot.company_id == company_id, Lot.status == LotStatus.ACTIVE, Lot.bird_type == c.bird_type,
        Lot.id.not_in(con_opening)).order_by(Lot.lot_code))).scalars().all()
    for lote in candidatos:
        filas.append(["lot", lote.lot_code, f"lote existente sin apertura · legado {lote.legacy_lot_code or '-'}", activo, ""])
    return filas


def construir_plantilla_xlsx(c: TemplateContract, *, company_id: int, catalogo: list[list],
                             cutover_datetime: Optional[datetime] = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    instrucciones = wb.active
    instrucciones.title = "Instrucciones"
    for fila in _filas_instrucciones(c):
        instrucciones.append(fila)
    instrucciones.column_dimensions["A"].width = 30
    instrucciones.column_dimensions["B"].width = 90

    meta = wb.create_sheet("Meta")
    meta.append(["key", "value"])
    meta.append(["template_version", c.version])
    meta.append(["schema_id", c.schema_id])
    meta.append(["company", company_id])
    meta.append(["business_unit", c.business_unit])
    meta.append(["generated_at", datetime.now(timezone.utc).isoformat()])
    meta.append(["cutover_datetime", cutover_datetime.isoformat() if cutover_datetime else ""])

    datos = wb.create_sheet("Datos")
    datos.append(list(c.columns))
    for celda in datos[1]:
        celda.font = Font(bold=True)
    for i, f in enumerate(c.fields, start=1):
        datos.column_dimensions[datos.cell(row=1, column=i).column_letter].width = max(14, min(32, len(f.name) + 2))

    cat = wb.create_sheet("Catalogos")
    cat.append(["catalog", "code", "description", "status", "parent_code"])
    for fila in catalogo:
        cat.append(fila)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def construir_plantilla_csv(c: TemplateContract) -> bytes:
    buf = io.StringIO()
    csv.writer(buf, delimiter=CSV_DELIMITER, lineterminator="\n").writerow(list(c.columns))
    return ("﻿" + buf.getvalue()).encode("utf-8")


# Compatibilidad con llamadores previos (C9): plantilla v2 sin catálogos ni corte.
def construir_plantilla(business_unit: str, company_id: int, template_version: str = "v2") -> bytes:
    if template_version != "v2":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"TEMPLATE_VERSION_UNSUPPORTED: {template_version}")
    return construir_plantilla_xlsx(contrato(business_unit), company_id=company_id, catalogo=[])


@router.get("/{business_unit}")
async def descargar_plantilla(
    business_unit: str,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    batch_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("cutover", "create")),
):
    """`GET /cutover-templates/{bu}?format=xlsx|csv&batch_id=` — plantilla v2 de la BU (la BU la fija el batch si se indica)."""
    if business_unit not in UNIDADES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"BUSINESS_UNIT_INVALID: '{business_unit}' no es una unidad de negocio")
    empresa = current_user.get("effective_company_id") or current_user.get("company_id")
    if not empresa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Se requiere una empresa efectiva para descargar la plantilla.")
    c = CONTRACTS[business_unit]
    corte: Optional[datetime] = None
    if batch_id is not None:
        batch = (await db.execute(select(CutoverBatch).where(CutoverBatch.id == batch_id))).scalar_one_or_none()
        if batch is None or batch.company_id != int(empresa):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch de cutover no encontrado")
        if batch.business_unit != business_unit:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=(f"BUSINESS_UNIT_MISMATCH: el batch {batch.id} es de {batch.business_unit}; "
                                        f"descargue la plantilla de esa unidad."))
        corte = batch.cutover_datetime
    if format == "csv":
        return Response(content=construir_plantilla_csv(c), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{c.filename_stem}.csv"'})
    contenido = construir_plantilla_xlsx(c, company_id=int(empresa), catalogo=await catalogos(db, int(empresa), c),
                                         cutover_datetime=corte)
    return Response(content=contenido, media_type=XLSX_MIME,
                    headers={"Content-Disposition": f'attachment; filename="{c.filename_stem}.xlsx"'})
