"""Mapping multiempresa fail-closed — SPEC 005 `§21`, `§22`, `FR-09`.

    SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY

Tres respuestas posibles, y ninguna es «la primera empresa que encaje»:

    MAPPED            la sociedad y todos los centros de la fila son de esta empresa
    PENDING_MAPPING   falta resolver algo: la fila se retiene y no se promueve
    FOREIGN           la sociedad pertenece a OTRA empresa GA: la fila ni siquiera se persiste

No hay fallback transversal ni atajo para la autoridad global.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ENTITY_COMPANY_CODE, ENTITY_PLANT, ENTITY_STORAGE_LOCATION, M_MAPPED, M_PENDING_MAPPING,
    SOURCE_SYSTEM, SapEntityMapping,
)
from .settings import HanaSettings

FOREIGN = "FOREIGN"


@dataclass
class MappingContext:
    company_id: int
    client: str
    #: Sociedades de esta empresa, ya recortadas por la lista de admisión del entorno.
    company_codes: tuple[str, ...] = ()
    #: Sociedades del mismo mandante que pertenecen a otra empresa GA.
    foreign_company_codes: frozenset[str] = frozenset()
    #: Datos planos, no entidades: el contexto sobrevive a los savepoints del sync.
    plants: dict[str, dict] = field(default_factory=dict)
    storage_locations: dict[str, dict] = field(default_factory=dict)
    allowed_plants: tuple[str, ...] = ()

    def resolve(self, company_code: str | None, plants: tuple[str, ...]) -> tuple[str, str]:
        """Estado de mapping de una fila y, si no es `MAPPED`, el porqué."""
        if company_code:
            if company_code in self.foreign_company_codes:
                return FOREIGN, f"la sociedad {company_code} pertenece a otra empresa"
            if company_code not in self.company_codes:
                return M_PENDING_MAPPING, f"sociedad {company_code} sin mapping a esta empresa"
        elif not self.company_codes:
            return M_PENDING_MAPPING, "la empresa no tiene ninguna sociedad mapeada"
        for planta in plants:
            if planta not in self.plants:
                return M_PENDING_MAPPING, f"centro {planta} sin mapping a esta empresa"
            if self.allowed_plants and planta not in self.allowed_plants:
                return M_PENDING_MAPPING, f"centro {planta} fuera de SAP_HANA_PLANTS"
        return M_MAPPED, ""


async def load_context(db: AsyncSession, company_id: int, cfg: HanaSettings) -> MappingContext:
    filas = (await db.execute(
        select(SapEntityMapping).where(
            SapEntityMapping.source_system == SOURCE_SYSTEM,
            SapEntityMapping.client == cfg.client,
            SapEntityMapping.is_active.is_(True),
        ))).scalars().all()

    propias, ajenas = [], set()
    plantas: dict[str, dict] = {}
    almacenes: dict[str, dict] = {}
    for m in filas:
        mio = m.company_id == company_id
        dato = {"parent": m.parent_sap_key, "farm_id": m.farm_id, "house_id": m.house_id,
                "business_unit_code": m.business_unit_code}
        if m.entity_type == ENTITY_COMPANY_CODE:
            (propias.append(m.sap_key) if mio else ajenas.add(m.sap_key))
        elif m.entity_type == ENTITY_PLANT and mio:
            plantas[m.sap_key] = dato
        elif m.entity_type == ENTITY_STORAGE_LOCATION and mio:
            almacenes[m.sap_key] = dato

    if cfg.company_codes:
        # La lista del entorno solo puede restringir: nunca añade sociedades.
        propias = [c for c in propias if c in cfg.company_codes]
    # Un centro solo cuenta si cuelga de una sociedad vigente de esta misma empresa.
    plantas = {k: m for k, m in plantas.items() if m["parent"] in propias}
    return MappingContext(
        company_id=company_id, client=cfg.client, company_codes=tuple(sorted(propias)),
        foreign_company_codes=frozenset(ajenas), plants=plantas, storage_locations=almacenes,
        allowed_plants=cfg.plants)
