"""SPEC 006 · Cutover v2 — registry cerrado de contratos de plantilla por unidad de negocio.

Una plantilla **por BU** (`ONE_CONTRACT_PER_BUSINESS_UNIT`): progenitoras y reproductoras
comparten el contrato de población de aves por sexo; engorde tiene población mixta;
incubadora describe un proceso de incubación en curso. Cada campo declara su significado,
tipo, unidad, obligatoriedad, si admite UNKNOWN (celda vacía) o N/A, el maestro al que
referencia y **dónde termina** tras el apply (`targets`). De aquí se generan la hoja
`Instrucciones`, la matriz de linaje (`07_DATA_LINEAGE_MATRIX`) y la de destino
(`10_APPLY_DESTINATION_MATRIX`): `UNMAPPED_TEMPLATE_FIELDS = 0` es una prueba, no una promesa.

Semántica universal de celda: **vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE**.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

TEMPLATE_VERSION = "v2"
HATCHERY_TEMPLATE_VERSION = "v3"  # SPEC 009: incubadora versionada por la columna nueva egg_origin.
#: Versiones aceptadas por el parser. `v1` está **retirada** (Q6): no se reinterpreta.
SUPPORTED_TEMPLATE_VERSIONS = frozenset({TEMPLATE_VERSION, HATCHERY_TEMPLATE_VERSION})
RETIRED_TEMPLATE_VERSIONS = frozenset({"v1"})

#: SPEC 009 · procedencia (gobernanza) de cada categoría de la hoja `Catalogos`.
SOURCE_SAP = "SAP"
SOURCE_GLOBAL_AVICOLA = "GLOBAL_AVICOLA"
#: farm/house están gobernadas por SAP vía el mapping canónico `sap_entity_mappings`
#: (ENTITY_PLANT->farm_id, ENTITY_STORAGE_LOCATION->house_id). El resto es maestro interno GA.
CATALOG_SOURCE = {"farm": SOURCE_SAP, "house": SOURCE_SAP}


def catalog_source(catalog_key: str) -> str:
    """Procedencia declarada de una categoría de `Catalogos` (SAP vs Global Avícola)."""
    return CATALOG_SOURCE.get(catalog_key, SOURCE_GLOBAL_AVICOLA)


UNIDADES = ("grandparent", "breeder", "hatchery", "broiler")

KNOWN = "KNOWN"
UNKNOWN = "UNKNOWN"
NOT_APPLICABLE = "NOT_APPLICABLE"

#: Fases compatibles por BU (códigos globales del catálogo de fases productivas).
FASES_POR_BU = {
    "grandparent": ("CRIA", "PROD"),
    "breeder": ("CRIA", "PROD"),
    "broiler": ("ENGORDE",),
    "hatchery": ("INCUB",),
}


@dataclass(frozen=True)
class FieldSpec:
    """Un campo de la hoja `Datos` y su recorrido hasta el dominio."""

    name: str
    kind: str                      # text | int | decimal | date | enum
    meaning: str
    required: bool = False
    #: Métrica: la celda vacía es un dato (`UNKNOWN`) y no una omisión.
    metric: bool = False
    allow_na: bool = False
    unit: Optional[str] = None
    example: Optional[str] = None
    values: tuple[str, ...] = ()
    master: Optional[str] = None   # farm | house | area | productive_phase | genetic_line | breed | hatchery | incubator | hatcher | lot | source_lot
    targets: tuple[str, ...] = ()  # "tabla.columna"
    status_column: Optional[str] = None
    promotion: str = ""
    consumer: str = ""
    max_len: Optional[int] = None
    positive: bool = False         # decimal > 0 (pesos)
    normalized_name: Optional[str] = None  # si el nombre normalizado difiere

    @property
    def allow_unknown(self) -> bool:
        return self.metric and not self.required

    @property
    def normalized(self) -> str:
        return self.normalized_name or self.name


@dataclass(frozen=True)
class TemplateContract:
    business_unit: str
    schema_id: str
    fields: tuple[FieldSpec, ...]
    bird_type: str
    #: Campo de fecha que fija `lots.start_date`.
    lot_date_field: str
    phases: tuple[str, ...]
    implicit_phase: Optional[str] = None
    version: str = TEMPLATE_VERSION
    #: Campos de dominio que la plantilla debe exponer (auditoría del modelo, §11–§14 del mandato).
    required_domain_fields: frozenset[str] = field(default_factory=frozenset)

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields)

    @property
    def by_name(self) -> dict[str, FieldSpec]:
        return {f.name: f for f in self.fields}

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields if f.required)

    @property
    def filename_stem(self) -> str:
        return f"cutover_template_{self.business_unit}_{self.version}"


# ── Campos comunes de lotes de aves ──────────────────────────────────────────

def _identificacion_aves(bu: str) -> tuple[FieldSpec, ...]:
    return (
        FieldSpec("legacy_lot_code", "text", "Código del lote en el sistema anterior. Único en el batch y en la empresa.",
                  required=True, example="GP-2025-014", max_len=60,
                  targets=("lots.legacy_lot_code", "lots.lot_code", "opening_balances.legacy_lot_code"),
                  promotion="lot_code = legacy_lot_code cuando no hay existing_lot_code", consumer="todas las operaciones (lote)"),
        FieldSpec("existing_lot_code", "text", "Código de un lote YA existente en Global Avícola para reutilizarlo (misma empresa, activo, sin eventos).",
                  example="", master="lot", max_len=100, targets=("lots.id",),
                  promotion="REUSE del lote; sin este campo se crea un lote MIGRATED", consumer="—"),
        FieldSpec("farm_code", "text", "Código de la granja donde está el lote (hoja Catalogos → farm).",
                  required=True, example="GR-01", master="farm", targets=("lots.farm_id",),
                  promotion="resuelto por código en la empresa efectiva", consumer="eventos con granja (BR-08)"),
        FieldSpec("house_name", "text", "Nombre del galpón dentro de la granja (Catalogos → house, parent_code = granja).",
                  example="G-03", master="house", targets=("lots.house_id",),
                  promotion="resuelto por nombre dentro de la granja", consumer="eventos con galpón, capacidad (G-R04)"),
        FieldSpec("area_code", "text", "Código del área funcional (Catalogos → area).",
                  example="", master="area", targets=("lots.area_id",), promotion="resuelto por código", consumer="avisos (GA-REM-039)"),
        FieldSpec("productive_phase_code", "text",
                  f"Fase productiva REAL del lote al corte. Valores para esta unidad: {', '.join(FASES_POR_BU[bu])}.",
                  required=True, example=FASES_POR_BU[bu][-1], master="productive_phase", values=FASES_POR_BU[bu],
                  targets=("lot_phases.phase_id", "opening_balances.phase_at_activation_id"),
                  promotion="fase declarada; nunca la primera activa", consumer="transición de fase (R-191), KPIs por fase"),
        FieldSpec("real_start_date", "date", "Fecha real de inicio del lote (alojamiento). AAAA-MM-DD, ≤ fecha del corte.",
                  required=True, example="2025-11-03", targets=("lots.start_date", "opening_balances.activation_date", "opening_balances.age_days"),
                  promotion="start_date = medianoche UTC; edad = corte − inicio", consumer="BR-06, edad en semanas"),
        FieldSpec("phase_start_date", "date", "Fecha de inicio de la fase declarada. Vacío = se toma la fecha real de inicio.",
                  metric=True, example="2026-04-20", targets=("lot_phases.start_date",),
                  promotion="phase_start_date | real_start_date", consumer="duración de fase"),
        FieldSpec("genetic_line_code", "text", "Código de la línea genética (Catalogos → genetic_line).",
                  example="", master="genetic_line", targets=("lots.genetic_line_id",), promotion="resuelto por código", consumer="curvas de peso (OD-06)"),
        FieldSpec("breed_name", "text", "Nombre de la raza dentro de la línea genética (Catalogos → breed, parent_code = línea).",
                  example="", master="breed", targets=("lots.breed_id",), promotion="resuelto por nombre dentro de la línea", consumer="informes"),
        FieldSpec("sex", "enum", "Sexo del lote. Vacío = mixto para engorde; vacío = sin declarar para reproductoras.",
                  values=("male", "female", "mixed"), example="mixed", targets=("lots.sex",), promotion="enum", consumer="informes"),
    )


_PROCEDENCIA = (
    FieldSpec("source_system", "text", "Sistema de origen del dato (p. ej. LEGACY, SAP, EXCEL). Vacío = el del batch.",
              example="LEGACY", max_len=40, targets=("lots.source_system", "opening_balances.source_system"),
              promotion="fila | batch | tipo de archivo", consumer="auditoría"),
    FieldSpec("source_reference", "text", "Referencia en el sistema de origen (documento, planilla, lote).",
              example="PLANILLA-2026-10", max_len=200, targets=("lots.source_reference", "opening_balances.source_reference"),
              promotion="texto", consumer="auditoría"),
    FieldSpec("notes", "text", "Notas libres. Nunca sustituyen a un campo del contrato.",
              example="", targets=("cutover_items.opening_state.notes",), promotion="texto", consumer="—"),
)

def _metricas_reproductoras(bu: str) -> tuple[FieldSpec, ...]:
    _req = bu == "breeder"  # SPEC 009: mortalidad obligatoria solo en Reproductoras (breeder).
    return (
    FieldSpec("live_males", "int", "Machos vivos al momento del corte.", required=True, metric=True, unit="aves", example="1000",
              targets=("opening_balances.initial_male_count",), promotion="saldo vivo (no se resta lo histórico, RC-08)",
              consumer="BR-01 mortalidad/descarte/salida, saldo de aves"),
    FieldSpec("live_females", "int", "Hembras vivas al momento del corte.", required=True, metric=True, unit="aves", example="9000",
              targets=("opening_balances.initial_female_count",), promotion="saldo vivo", consumer="BR-01, postura (hen-day)"),
    FieldSpec("birds_placed_males", "int", "Machos alojados originalmente (histórico).", metric=True, unit="aves", example="1100",
              targets=("opening_balances.placed_male_count",), status_column="placed_status",
              promotion="consistencia: alojadas − mortalidad − descartes = vivas (solo si todo KNOWN)", consumer="informe de lote"),
    FieldSpec("birds_placed_females", "int", "Hembras alojadas originalmente (histórico).", metric=True, unit="aves", example="9600",
              targets=("opening_balances.placed_female_count",), status_column="placed_status", promotion="ídem", consumer="informe de lote"),
    FieldSpec("historical_mortality_males", "int", "Mortalidad acumulada de machos ANTES del corte.", required=_req, metric=True, unit="aves", example="50",
              targets=("opening_balances.accumulated_mortality_male",), status_column="mortality_status",
              promotion="histórico; no se resta al saldo", consumer="lifetime mortalidad, KPI"),
    FieldSpec("historical_mortality_females", "int", "Mortalidad acumulada de hembras ANTES del corte.", required=_req, metric=True, unit="aves", example="450",
              targets=("opening_balances.accumulated_mortality_female",), status_column="mortality_status", promotion="ídem", consumer="lifetime mortalidad"),
    FieldSpec("historical_culls_males", "int", "Descartes acumulados de machos antes del corte.", metric=True, unit="aves", example="0",
              targets=("opening_balances.accumulated_culls_male",), status_column="culls_status", promotion="histórico", consumer="lifetime descartes"),
    FieldSpec("historical_culls_females", "int", "Descartes acumulados de hembras antes del corte.", metric=True, unit="aves", example="0",
              targets=("opening_balances.accumulated_culls_female",), status_column="culls_status", promotion="histórico", consumer="lifetime descartes"),
    FieldSpec("accumulated_feed_kg", "decimal", "Alimento acumulado consumido antes del corte.", metric=True, unit="kg", example="120000.5",
              targets=("opening_balances.accumulated_feed_kg",), status_column="feed_status", promotion="histórico", consumer="FCR/AFCR lifetime"),
    FieldSpec("current_avg_weight_g", "decimal", "Peso promedio actual del ave al corte.", metric=True, unit="g", example="3200", positive=True,
              targets=("opening_balances.current_avg_weight",), status_column="weight_status", promotion="gramos (unidad canónica)", consumer="FCR (peso inicial)"),
    FieldSpec("accumulated_egg_production", "int", "Huevos producidos acumulados antes del corte. N/A en cría.", metric=True, allow_na=True,
              unit="huevos", example="180000", targets=("opening_balances.accumulated_egg_production",), status_column="egg_production_status",
              promotion="histórico; prohibido KNOWN en fase CRIA", consumer="lifetime producción"),
    FieldSpec("accumulated_eggs_to_hatchery", "int", "Huevos enviados a incubadora acumulados antes del corte. N/A en cría.", metric=True, allow_na=True,
              unit="huevos", example="150000", targets=("opening_balances.accumulated_eggs_to_hatchery",), status_column="eggs_to_hatchery_status",
              promotion="≤ producción si ambas KNOWN", consumer="lifetime despachos"),
)

_METRICAS_ENGORDE = (
    FieldSpec("live_birds", "int", "Aves vivas (mixtas) al momento del corte.", required=True, metric=True, unit="aves", example="10000",
              targets=("opening_balances.initial_mixed_count",), promotion="saldo vivo mixto", consumer="BR-01 mortalidad, saldo de aves"),
    FieldSpec("age_days", "int", "Edad del lote en días al corte. Vacío = se deriva de la fecha de inicio.", metric=True, unit="días", example="20",
              targets=("opening_balances.age_days",), status_column="age_status", promotion="declarada | derivada (corte − inicio)", consumer="curvas de peso, IPE"),
    FieldSpec("accumulated_birds_received", "int", "Aves recibidas acumuladas (alojadas) antes del corte.", metric=True, unit="aves", example="10500",
              targets=("opening_balances.accumulated_broiler_received",), status_column="broiler_received_status",
              promotion="consistencia: recibidas − mortalidad − descartes − salidas = vivas (solo si todo KNOWN)", consumer="informe de lote"),
    FieldSpec("historical_mortality", "int", "Mortalidad acumulada antes del corte.", metric=True, unit="aves", example="300",
              targets=("opening_balances.accumulated_mortality_mixed",), status_column="mortality_status", promotion="histórico", consumer="lifetime mortalidad"),
    FieldSpec("historical_culls", "int", "Descartes acumulados antes del corte.", metric=True, unit="aves", example="200",
              targets=("opening_balances.accumulated_culls_mixed",), status_column="culls_status", promotion="histórico", consumer="lifetime descartes"),
    FieldSpec("partial_outbound_birds", "int", "Aves salidas parcialmente a planta antes del corte. N/A si no hubo salidas parciales.",
              metric=True, allow_na=True, unit="aves", example="0", targets=("opening_balances.accumulated_outbound_birds",),
              status_column="outbound_status", promotion="histórico", consumer="cierre, IPE"),
    FieldSpec("accumulated_feed_kg", "decimal", "Alimento acumulado consumido antes del corte.", metric=True, unit="kg", example="15000",
              targets=("opening_balances.accumulated_feed_kg",), status_column="feed_status", promotion="histórico", consumer="FCR/AFCR"),
    FieldSpec("current_avg_weight_g", "decimal", "Peso promedio actual del ave al corte.", metric=True, unit="g", example="900", positive=True,
              targets=("opening_balances.current_avg_weight",), status_column="weight_status", promotion="gramos", consumer="FCR, IPE"),
)

_INCUBADORA = (
    FieldSpec("legacy_lot_code", "text", "Código del proceso/lote de incubación en el sistema anterior.", required=True, example="INC-2026-07",
              max_len=60, targets=("lots.legacy_lot_code", "lots.lot_code", "opening_balances.legacy_lot_code"),
              promotion="lot_code = legacy_lot_code cuando no hay existing_lot_code", consumer="eventos de incubadora (lote)"),
    FieldSpec("existing_lot_code", "text", "Código de un lote de incubadora YA existente para reutilizar (sin eventos).", master="lot",
              example="", max_len=100, targets=("lots.id",), promotion="REUSE", consumer="—"),
    FieldSpec("hatchery_code", "text", "Código de la planta de incubación (Catalogos → hatchery).", required=True, example="INC-01", master="hatchery",
              targets=("hatchery_openings.hatchery_id",), promotion="resuelto por código en la empresa", consumer="eventos de incubadora"),
    FieldSpec("incubator_name", "text", "Nombre de la incubadora dentro de la planta (Catalogos → incubator, parent_code = planta).",
              example="INC-A1", master="incubator", targets=("hatchery_openings.incubator_id",), promotion="resuelto por nombre dentro de la planta",
              consumer="carga de incubación"),
    FieldSpec("hatcher_name", "text", "Nombre de la nacedora dentro de la planta (Catalogos → hatcher).", example="NAC-1", master="hatcher",
              targets=("hatchery_openings.hatcher_id",), promotion="resuelto por nombre dentro de la planta", consumer="transferencia a nacedora"),
    FieldSpec("source_lot_code", "text", "Código (actual o legado) del lote de reproductoras/progenitoras que originó los huevos.",
              example="", master="source_lot", targets=("hatchery_openings.source_lot_id", "hatchery_openings.source_lot_reference"),
              promotion="resuelto si existe; la referencia escrita se conserva siempre", consumer="trazabilidad generacional"),
    FieldSpec("generation", "enum", "Generación del huevo incubado: grandparent (huevo de progenitoras → pollito reproductor) o breeder (→ pollito de engorde).",
              values=("grandparent", "breeder"), example="breeder", targets=("lots.hatchery_purpose", "hatchery_openings.generation"),
              promotion="enum", consumer="despacho de pollitos (destino)"),
    FieldSpec("egg_origin", "enum", "Origen comercial del huevo: internal (propio de Global Avícola) o purchased (comprado a un tercero). No es la generación biológica.",
              required=True, values=("internal", "purchased"), example="internal", targets=("hatchery_openings.egg_origin",),
              promotion="enum", consumer="trazabilidad y origen del huevo"),
    FieldSpec("reception_date", "date", "Fecha de recepción del huevo en la planta. ≤ corte.", required=True, example="2026-09-20",
              targets=("lots.start_date", "hatchery_openings.reception_date", "opening_balances.activation_date"), promotion="start_date = medianoche UTC",
              consumer="BR-06"),
    FieldSpec("set_date", "date", "Fecha de carga en incubadora. Vacío = desconocida; N/A = aún no cargado.", metric=True, allow_na=True,
              example="2026-09-22", targets=("hatchery_openings.set_date",), status_column="set_date_status",
              promotion="recepción ≤ carga ≤ corte", consumer="día de incubación, nacimiento esperado"),
    FieldSpec("expected_hatch_date", "date", "Fecha prevista de nacimiento. ≥ fecha de carga.", metric=True, allow_na=True, example="2026-10-13",
              targets=("hatchery_openings.expected_hatch_date",), status_column="expected_hatch_date_status", promotion="≥ set_date", consumer="planificación"),
    FieldSpec("eggs_received", "int", "Huevos fértiles recibidos en la planta.", required=True, metric=True, unit="huevos", example="10000",
              targets=("hatchery_openings.eggs_received",), status_column="eggs_received_status",
              promotion="saldo de huevo en planta = recibidos − cargados", consumer="BR-03 carga de incubación"),
    FieldSpec("eggs_set", "int", "Huevos ya cargados en incubadora. ≤ recibidos.", required=True, metric=True, unit="huevos", example="9000",
              targets=("hatchery_openings.eggs_set",), status_column="eggs_set_status", promotion="≤ eggs_received", consumer="huevos en proceso"),
    FieldSpec("eggs_transferred", "int", "Huevos ya transferidos a nacedora. ≤ cargados.", metric=True, allow_na=True, unit="huevos", example="0",
              targets=("hatchery_openings.eggs_transferred",), status_column="eggs_transferred_status", promotion="≤ eggs_set", consumer="nacimientos"),
    FieldSpec("eggs_discarded", "int", "Huevos descartados (ovoscopia, rotos) del proceso. ≤ cargados.", metric=True, allow_na=True, unit="huevos",
              example="100", targets=("hatchery_openings.eggs_discarded",), status_column="eggs_discarded_status", promotion="≤ eggs_set", consumer="rendimiento"),
    FieldSpec("chicks_hatched", "int", "Pollitos ya nacidos del proceso antes del corte.", metric=True, allow_na=True, unit="pollitos", example="0",
              targets=("opening_balances.accumulated_chicks_hatched",), status_column="chicks_hatched_status",
              promotion="≤ transferidos (o ≤ cargados si transferidos no es KNOWN)", consumer="lifetime nacimientos"),
    FieldSpec("chicks_available", "int", "Pollitos nacidos que siguen en planta sin despachar al corte.", metric=True, allow_na=True, unit="pollitos",
              example="0", targets=("opening_balances.initial_mixed_count",), promotion="≤ nacidos; saldo de pollitos viables",
              consumer="BR-04 despacho de pollitos"),
) + _PROCEDENCIA

_DOMINIO_AVES = frozenset({
    "legacy_lot_code", "farm_code", "house_name", "productive_phase_code", "real_start_date", "genetic_line_code",
    "breed_name", "sex", "live_males", "live_females", "historical_mortality_males", "historical_mortality_females",
    "historical_culls_males", "historical_culls_females", "accumulated_feed_kg", "current_avg_weight_g",
    "accumulated_egg_production", "accumulated_eggs_to_hatchery", "source_system", "source_reference",
})
_DOMINIO_ENGORDE = frozenset({
    "legacy_lot_code", "farm_code", "house_name", "productive_phase_code", "real_start_date", "age_days", "genetic_line_code",
    "breed_name", "live_birds", "historical_mortality", "historical_culls", "accumulated_feed_kg", "current_avg_weight_g",
    "accumulated_birds_received", "partial_outbound_birds", "source_system", "source_reference",
})
_DOMINIO_INCUBADORA = frozenset({
    "legacy_lot_code", "hatchery_code", "incubator_name", "hatcher_name", "source_lot_code", "generation", "egg_origin", "reception_date",
    "set_date", "expected_hatch_date", "eggs_received", "eggs_set", "eggs_transferred", "eggs_discarded", "chicks_hatched",
    "chicks_available", "source_system", "source_reference",
})


def _contrato_aves(bu: str, schema_id: str) -> TemplateContract:
    return TemplateContract(
        business_unit=bu, schema_id=schema_id, bird_type=bu, lot_date_field="real_start_date",
        phases=FASES_POR_BU[bu], fields=_identificacion_aves(bu) + _metricas_reproductoras(bu) + _PROCEDENCIA,
        required_domain_fields=_DOMINIO_AVES,
    )


CONTRACTS: dict[str, TemplateContract] = {
    "grandparent": _contrato_aves("grandparent", "CUTOVER_GRANDPARENT_V2"),
    "breeder": _contrato_aves("breeder", "CUTOVER_BREEDER_V2"),
    "broiler": TemplateContract(
        business_unit="broiler", schema_id="CUTOVER_BROILER_V2", bird_type="broiler", lot_date_field="real_start_date",
        phases=FASES_POR_BU["broiler"], fields=_identificacion_aves("broiler") + _METRICAS_ENGORDE + _PROCEDENCIA,
        required_domain_fields=_DOMINIO_ENGORDE,
    ),
    "hatchery": TemplateContract(
        business_unit="hatchery", schema_id="CUTOVER_HATCHERY_V3", version=HATCHERY_TEMPLATE_VERSION, bird_type="hatchery",
        lot_date_field="reception_date", phases=FASES_POR_BU["hatchery"], implicit_phase="INCUB", fields=_INCUBADORA,
        required_domain_fields=_DOMINIO_INCUBADORA,
    ),
}

SCHEMA_IDS = {bu: c.schema_id for bu, c in CONTRACTS.items()}


def contrato(business_unit: str) -> TemplateContract:
    try:
        return CONTRACTS[business_unit]
    except KeyError as exc:
        raise ValueError(f"BUSINESS_UNIT_INVALID: {business_unit!r}") from exc


def campos_dominio_requeridos(business_unit: str) -> set[str]:
    """Campos de dominio que la plantilla de la BU debe exponer (`REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE`)."""
    return set(contrato(business_unit).required_domain_fields)


def lineage() -> dict:
    """Matriz de linaje (mandato §10): una fila por (BU, campo) con las 16 columnas y los dos contadores de cierre."""
    filas: list[dict] = []
    sin_destino = 0
    faltantes = 0
    for bu, c in CONTRACTS.items():
        nombres = {f.name for f in c.fields}
        faltantes += len(c.required_domain_fields - nombres)
        for f in c.fields:
            if not f.targets:
                sin_destino += 1
            entidades = sorted({t.split(".")[0] for t in f.targets})
            filas.append({
                "BU": bu, "TEMPLATE_FIELD": f.name, "BUSINESS_MEANING": f.meaning, "TYPE": f.kind, "UNIT": f.unit or "",
                "REQUIRED": f.required, "ALLOW_UNKNOWN": f.allow_unknown, "ALLOW_NA": f.allow_na,
                "VALIDATION": _regla_de_validacion(f), "MASTER_REFERENCE": f.master or "",
                "NORMALIZED_FIELD": f.normalized, "STAGING_FIELD": f"cutover_staging_rows.normalized.{f.normalized}",
                "TARGET_ENTITY": ", ".join(entidades), "TARGET_COLUMN": ", ".join(f.targets),
                "PROMOTION_RULE": f.promotion, "FIRST_OPERATION_CONSUMER": f.consumer,
            })
    return {"rows": filas, "UNMAPPED_TEMPLATE_FIELDS": sin_destino,
            "REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE": faltantes}


def _regla_de_validacion(f: FieldSpec) -> str:
    partes = [f.kind]
    if f.required:
        partes.append("obligatorio")
    if f.kind in ("int", "decimal"):
        partes.append("> 0" if f.positive else "≥ 0")
    if f.values:
        partes.append("∈ {" + ", ".join(f.values) + "}")
    if f.master:
        partes.append(f"maestro {f.master} de la empresa, activo")
    if f.max_len:
        partes.append(f"≤ {f.max_len} caracteres")
    return " · ".join(partes)
