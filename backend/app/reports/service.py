"""Reports service — KPI calculations, lot reports, SAP comparison."""
from datetime import date
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..lots.models import LotPhase, OpeningBalance
from ..lots.service import _dia
from ..masters.models import Lot
from ..operations.models import BirdMovement, EggMovement, EventStatus, EventType, FeedMovement, OperationalEvent


#: `GA-REM-022` (R-141, Owner 2026-09-16): el conjunto de estados del detalle
#: certificado en `R-218` es el MISMO que alimenta los agregados:
#: FILTERED DETAIL SET = AGGREGATE INPUT SET.
_ESTADOS_ACEPTADOS = [
    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
]


class ReportsService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self._unidades_cache = None

    async def _unidades(self) -> list[str]:
        """El alcance de lectura productiva de quien pregunta (`OD-16` · `GA-FE-02-D`).

        La autoridad global lee por las **habilitadas** de la empresa (la concesión no se le
        exige; la habilitación jamás se salta): con todo apagado, los indicadores no
        alcanzan ningún lote.
        """
        if self._unidades_cache is None:
            from ..business_units.service import unidades_de_alcance_productivo

            self._unidades_cache = await unidades_de_alcance_productivo(
                self.db, current_user=self.current_user, company_id=self.company_id
            )
        return self._unidades_cache

    async def _exigir_lote(self, lot_id):
        """El lote tiene que estar al alcance del usuario. `GA-REM-040` fase 4.

        Casi todos los indicadores de `P-15` son **por lote**: no suman la empresa, pero
        devuelven el detalle de cualquier lote cuyo identificador alguien conozca. Un
        indicador de mortalidad de un lote ajeno da la población inicial, las muertes y la
        tasa — más de lo que el listado ocultaba.

        Responde `404`, como el detalle del lote, para no distinguir «no existe» de «no es
        tuyo».
        """
        if lot_id is None:
            return
        from fastapi import HTTPException, status as _st
        from sqlalchemy import select as _select

        from ..business_units.scope import lotes_alcanzables

        alcanzable = (await self.db.execute(
            _select(Lot.id).where(
                Lot.id == lot_id,
                Lot.id.in_(lotes_alcanzables(self.company_id, await self._unidades())))
        )).scalar_one_or_none()
        if alcanzable is None:
            raise HTTPException(status_code=_st.HTTP_404_NOT_FOUND,
                                detail="Lote no encontrado")

    async def _filtro_de_lotes(self):
        """Predicado para los agregados **sin** lote: solo los lotes alcanzables aportan."""
        from ..business_units.scope import lotes_alcanzables

        # `GA-FE-02-D` · `OD-16`: la autoridad global no queda fuera del filtro — su
        # alcance son las unidades habilitadas (agregados a cero con todo apagado).
        return lotes_alcanzables(self.company_id, await self._unidades())

    # ============================================================
    # KPI Helpers
    # ============================================================

    async def _sum_bird_quantity(self, lot_id: int, event_types: list[EventType]) -> float:
        result = await self.db.execute(
            select(func.coalesce(func.sum(BirdMovement.quantity), 0))
            .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.event_type.in_(event_types),
                OperationalEvent.status.in_([
                    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
                ]),
            )
        )
        return result.scalar() or 0.0

    async def _sum_feed_kg(self, lot_id: int) -> float:
        result = await self.db.execute(
            select(func.coalesce(func.sum(FeedMovement.quantity_kg), 0.0))
            .join(OperationalEvent, FeedMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.event_type == EventType.FEED_REGISTRATION,
                OperationalEvent.status.in_([
                    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
                ]),
            )
        )
        return result.scalar() or 0.0

    async def _sum_egg_quantity(self, lot_id: int) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.sum(EggMovement.quantity), 0))
            .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.event_type.in_([EventType.EGG_COLLECTION, EventType.EGG_CLASSIFICATION]),
                OperationalEvent.status.in_([
                    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
                ]),
            )
        )
        return result.scalar() or 0

    async def _get_opening_balance(self, lot_id: int) -> Optional[OpeningBalance]:
        result = await self.db.execute(
            select(OpeningBalance)
            .join(Lot, OpeningBalance.lot_id == Lot.id)
            .where(
                Lot.id == lot_id,
                Lot.company_id == self.company_id,
            )
            .order_by(OpeningBalance.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    # ============================================================
    # KPI Calculations
    # ============================================================

    async def get_weekly_series(self, lot_id: int) -> dict:
        """`R-218` · C-01=A: serie semanal del lote (agregado de solo lectura).

        La LISTA de `/operations` se aligeró por contrato y ya no expone sublistas,
        de modo que la vista semanal y los gráficos leían el vacío. Este agregado
        pasa por `_exigir_lote` (tenencia/unidad) y suma solo eventos aceptados,
        como el resto de indicadores (`P-15`): mortalidad, alimento, agua y peso por
        `week_number`. El agua se atribuye una vez por (evento, semana).
        """
        await self._exigir_lote(lot_id)
        aceptados = [EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                     EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED]

        filas = (await self.db.execute(
            select(BirdMovement.week_number, BirdMovement.quantity, BirdMovement.avg_weight,
                   OperationalEvent.event_type, OperationalEvent.water_liters,
                   OperationalEvent.id)
            .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.status.in_(aceptados),
            )
        )).all()
        filas_feed = (await self.db.execute(
            select(FeedMovement.week_number, FeedMovement.quantity_kg,
                   OperationalEvent.water_liters, OperationalEvent.id)
            .join(OperationalEvent, FeedMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.status.in_(aceptados),
            )
        )).all()

        semanas: dict[int, dict] = {}
        agua_vista: set[tuple[int, int]] = set()

        def _semana(w):
            return semanas.setdefault(w, {"week": w, "mortality": 0,
                                          "feed_kg": 0.0, "water_l": 0.0,
                                          "weight_g": None})

        for week, cantidad, peso, tipo, agua, eid in filas:
            w = week or 0
            s = _semana(w)
            if tipo == "mortality_recording":
                s["mortality"] += cantidad or 0
            if tipo == "weight_recording" and peso:
                s["weight_g"] = max(s["weight_g"] or 0.0, peso)
            if agua and (eid, w) not in agua_vista:
                agua_vista.add((eid, w))
                s["water_l"] += agua
        for week, kg, agua, eid in filas_feed:
            w = week or 0
            s = _semana(w)
            s["feed_kg"] += kg or 0.0
            if agua and (eid, w) not in agua_vista:
                agua_vista.add((eid, w))
                s["water_l"] += agua

        semanas_ordenadas = [semanas[w] for w in sorted(semanas)]
        return {"lot_id": lot_id, "weeks": semanas_ordenadas}

    async def get_kpi_mortality(self, lot_id: int) -> dict:
        """`GA-REM-022` (R-132): la base es la **población inicial real del lote**.

        Denominador = apertura (`OpeningBalance`) + entradas del motor
        (`BIRD_RECEPTION`, `BIRTH_REGISTRATION`, aceptadas) — misma taxonomía que
        el saldo `R-67`/`RR-08`. Antes solo contaba la apertura: todo lote
        activado por recepción reportaba mortalidad 0 % sobre muertes reales.
        """
        await self._exigir_lote(lot_id)
        total_deaths = await self._sum_bird_quantity(lot_id, [EventType.MORTALITY_RECORDING])
        ob = await self._get_opening_balance(lot_id)
        opening_pop = (ob.initial_male_count + ob.initial_female_count) if ob else 0
        receptions = await self._sum_bird_quantity(
            lot_id, [EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION])
        initial_pop = opening_pop + receptions

        rate = (total_deaths / initial_pop * 100) if initial_pop > 0 else 0
        return {
            "lot_id": lot_id,
            "initial_population": initial_pop,
            "opening_population": opening_pop,
            "receptions": round(receptions, 0),
            "total_deaths": round(total_deaths, 0),
            "mortality_rate_pct": round(rate, 2),
            "unit": "%",
        }

    async def _pesos_del_lote(self, lot_id: int) -> tuple[float | None, float | None]:
        """Peso inicial y final (g) del lote desde pesajes aceptados + apertura.

        Inicial: `OpeningBalance.current_avg_weight` (peso de la foto de apertura)
        o el primer pesaje si hay ≥2; final: el último pesaje aceptado.
        Sin datos suficientes, `None` — el FCR jamás se fabrica.
        """
        filas = (await self.db.execute(
            select(BirdMovement.avg_weight)
            .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
                OperationalEvent.status.in_(_ESTADOS_ACEPTADOS),
                BirdMovement.avg_weight != None,
            )
            .order_by(OperationalEvent.event_date, OperationalEvent.id)
        )).scalars().all()
        ob = await self._get_opening_balance(lot_id)
        inicial = ob.current_avg_weight if (ob and ob.current_avg_weight is not None) else None
        if inicial is None and len(filas) >= 2:
            inicial = float(filas[0])
        final = float(filas[-1]) if filas else None
        return inicial, final

    async def get_kpi_feed_conversion(self, lot_id: int) -> dict:
        """`GA-REM-022` · R-131 (Owner 2026-09-16): FCR canónico.

        `FCR = masa total de alimento consumido / ganancia total de peso vivo`.
        Numerador y denominador normalizados a **kg** (los pesos llegan en gramos:
        única conversión `/1000` demostrada). Cualquier `/1000` fijo queda fuera de
        la fórmula. Sin pesos suficientes ⇒ `feed_conversion_ratio = null`
        (UNKNOWN), nunca un número fabricado. **OD-22 no cambia.**
        """
        await self._exigir_lote(lot_id)
        total_feed_kg = await self._sum_feed_kg(lot_id)
        inicial_g, final_g = await self._pesos_del_lote(lot_id)
        ob = await self._get_opening_balance(lot_id)
        apertura = (int(ob.initial_male_count or 0) + int(ob.initial_female_count or 0)) if ob else 0
        entradas = await self._sum_bird_quantity(
            lot_id, [EventType.BIRD_RECEPTION, EventType.BIRTH_REGISTRATION])
        poblacion_base = apertura + entradas

        ganancia_kg: float | None = None
        if inicial_g is not None and final_g is not None and poblacion_base > 0:
            delta_g = final_g - inicial_g
            if delta_g > 0:
                ganancia_kg = round(delta_g / 1000.0 * poblacion_base, 4)

        fcr = (round(total_feed_kg / ganancia_kg, 2)
               if (ganancia_kg and ganancia_kg > 0 and total_feed_kg > 0) else None)
        return {
            "lot_id": lot_id,
            "total_feed_kg": round(total_feed_kg, 2),
            "feed_conversion_ratio": fcr,
            "avg_weight_initial_g": inicial_g,
            "avg_weight_final_g": final_g,
            "population_basis": poblacion_base,
            "weight_gain_kg": round(ganancia_kg, 2) if ganancia_kg is not None else None,
            "unit": "kg feed / kg gain",
            "status": "ok" if fcr is not None else "insufficient_data",
            "note": ("FCR = alimento kg / ganancia de peso vivo kg; "
                     "requiere peso inicial (apertura o primer pesaje) y final"),
        }

    async def get_kpi_egg_production(self, lot_id: int) -> dict:
        await self._exigir_lote(lot_id)
        total_eggs = await self._sum_egg_quantity(lot_id)
        ob = await self._get_opening_balance(lot_id)
        initial_females = ob.initial_female_count if ob else 0

        hen_day = (total_eggs / (initial_females * 30) * 100) if initial_females > 0 else 0
        return {
            "lot_id": lot_id,
            "total_eggs": total_eggs,
            "initial_females": initial_females,
            "hen_day_production_pct": round(hen_day, 2),
            # `R-86` / `AC06`. «Fertilidad» es uno de los trece indicadores de
            # `docs/02 §3.12.1` y no lo calculaba nadie, aunque el dato estaba:
            # `EggMovement.egg_type` distingue `fertile` de `infertile`.
            "fertilidad_pct": await self._fertilidad(lot_id),
            "unit": "%",
        }

    async def _fertilidad(self, lot_id: Optional[int]) -> float | None:
        """% de huevos fértiles sobre el total recibido en incubadora."""
        totales = await self._huevos_por_tipo(lot_id, EventType.EGG_RECEPTION_HATCHERY)
        fertiles = await self._huevos_fertiles(lot_id, EventType.EGG_RECEPTION_HATCHERY)
        return self._porcentaje(fertiles, totales)

    async def get_kpi_hatchery(self, lot_id: Optional[int] = None) -> dict:
        await self._exigir_lote(lot_id)
        # `R-204` · `OD-16`: agregado **sin lote** ⇒ predicado de lotes alcanzables. El
        # bloque incubadora no suma unidades no concedidas ni apagadas; sin ninguna
        # alcanzable la suma queda en 0 — subconjunto, no 403 (`C-01`).
        lotes = await self._filtro_de_lotes() if lot_id is None else None
        base = select(
            func.coalesce(func.sum(BirdMovement.quantity), 0).label("total_born")
        ).join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id).where(
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.BIRTH_REGISTRATION,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )
        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)
        elif lotes is not None:
            base = base.where(OperationalEvent.lot_id.in_(lotes))

        result = await self.db.execute(base)
        born = result.scalar() or 0

        # `R-14` / `GA-REM-022 AC01-bis`. El campo devolvía una frase en español alegando que
        # faltaban los datos de carga. **La alegación era falsa**: `HatcheryParams` los
        # guarda y `get_hatchery_egg_balance` ya los sumaba desde antes.
        cargados = await self._huevos_cargados(lot_id, lotes=lotes)
        fertiles = await self._huevos_fertiles(lot_id, EventType.EGG_RECEPTION_HATCHERY,
                                              lotes=lotes)

        # `R-85`. `docs/02 §3.12.1` separa dos cocientes con **denominadores distintos**, y el
        # endpoint los fundía en uno solo mal llamado. Un documento de proceso manda sobre una
        # spec de remediación, así que se devuelven ambos con su nombre.
        nacimiento = self._porcentaje(born, cargados)
        eclosion = self._porcentaje(born, fertiles)

        # `docs/02 §3.12.1` pide además «Rendimiento incubadora = pollitos viables ÷ huevos
        # cargados». «Viables» no es un campo del modelo, y la única representación de
        # pollitos no viables es el descarte, así que se toma **nacidos − descartados**.
        # El supuesto queda declarado en `GA-REM-022` enmienda A: sin descartes registrados
        # el rendimiento coincide con el nacimiento, que es lo correcto, y se afina a medida
        # que se registran. No se usa `get_viable_chick_balance`, que resta **despachos** y
        # mide otra cosa: cuántos quedan disponibles, no cuántos nacieron viables.
        descartados = await self._descartados(lot_id, lotes=lotes)
        rendimiento = self._porcentaje(max(born - descartados, 0), cargados)

        return {
            "total_chicks_born": born,
            "eggs_loaded": cargados,
            "fertile_eggs": fertiles,
            "nacimiento_pct": nacimiento,
            "eclosion_pct": eclosion,
            "rendimiento_pct": rendimiento,
            # Alias histórico. `AC01` fijó este nombre y la pantalla ya lo lee; retirarlo
            # sería romper un contrato que ningún requisito pide.
            "hatchability_pct": nacimiento,
            "unit": "%",
            # `AC02`. Cero significa «se midió y dio cero»; la ausencia de base es nula y se
            # declara. Confundirlas hace que un lote sin datos y uno con eclosión nula se
            # vean igual.
            "insufficient_data": nacimiento is None and eclosion is None,
        }

    @staticmethod
    def _porcentaje(numerador: int, denominador: int) -> float | None:
        """Porcentaje, o `None` cuando no hay base sobre la que medir (`AC02`)."""
        if not denominador:
            return None
        return round(numerador * 100.0 / denominador, 2)

    def _aprobados(self, consulta):
        """Los KPI solo cuentan eventos aprobados (`GA-REM-022 AC05`)."""
        return consulta.where(OperationalEvent.status.in_([
            EventStatus.APPROVED, EventStatus.CONSOLIDATED,
            EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
        ]))

    async def _huevos_cargados(self, lot_id: Optional[int], lotes=None) -> int:
        from ..operations.models import HatcheryParams

        q = self._aprobados(
            select(func.coalesce(func.sum(HatcheryParams.quantity_loaded), 0))
            .join(OperationalEvent, HatcheryParams.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type == EventType.INCUBATION_LOAD,
            )
        )
        if lot_id:
            q = q.where(OperationalEvent.lot_id == lot_id)
        elif lotes is not None:  # `R-204`: agregado acotado a lotes alcanzables
            q = q.where(OperationalEvent.lot_id.in_(lotes))
        return int((await self.db.execute(q)).scalar() or 0)

    async def _huevos_por_tipo(
        self, lot_id: Optional[int], evento: "EventType", tipo: Optional[str] = None,
        lotes=None,
    ) -> int:
        q = self._aprobados(
            select(func.coalesce(func.sum(EggMovement.quantity), 0))
            .join(OperationalEvent, EggMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type == evento,
            )
        )
        if tipo:
            q = q.where(EggMovement.egg_type == tipo)
        if lot_id:
            q = q.where(OperationalEvent.lot_id == lot_id)
        elif lotes is not None:
            q = q.where(OperationalEvent.lot_id.in_(lotes))
        return int((await self.db.execute(q)).scalar() or 0)

    async def _huevos_fertiles(self, lot_id: Optional[int], evento: "EventType",
                               lotes=None) -> int:
        return await self._huevos_por_tipo(lot_id, evento, "fertile", lotes=lotes)

    async def _descartados(self, lot_id: Optional[int], lotes=None) -> int:
        q = self._aprobados(
            select(func.coalesce(func.sum(BirdMovement.quantity), 0))
            .join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type == EventType.CULL_RECORDING,
            )
        )
        if lot_id:
            q = q.where(OperationalEvent.lot_id == lot_id)
        elif lotes is not None:
            q = q.where(OperationalEvent.lot_id.in_(lotes))
        return int((await self.db.execute(q)).scalar() or 0)

    # ============================================================
    # Lot Complete Report
    # ============================================================

    async def get_lot_report(self, lot_id: int) -> dict:
        await self._exigir_lote(lot_id)
        lot_result = await self.db.execute(
            select(Lot).where(Lot.id == lot_id, Lot.company_id == self.company_id)
        )
        lot = lot_result.scalar_one_or_none()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

        phases_result = await self.db.execute(
            select(LotPhase).where(LotPhase.lot_id == lot_id).order_by(LotPhase.start_date)
        )
        phases = list(phases_result.scalars().all())

        ob = await self._get_opening_balance(lot_id)

        events_result = await self.db.execute(
            select(OperationalEvent.event_type, func.count().label("cnt")).where(
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.company_id == self.company_id,
            ).group_by(OperationalEvent.event_type)
        )
        event_counts = {row.event_type.value: row.cnt for row in events_result.fetchall()}

        status_result = await self.db.execute(
            select(OperationalEvent.status, func.count().label("cnt")).where(
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.company_id == self.company_id,
            ).group_by(OperationalEvent.status)
        )
        status_dist = {row.status.value: row.cnt for row in status_result.fetchall()}

        return {
            "lot": {
                "id": lot.id,
                "lot_code": lot.lot_code if hasattr(lot, 'lot_code') else f"L-{lot.id}",
                "status": lot.status.value if hasattr(lot, 'status') else "unknown",
                "start_date": str(lot.start_date) if hasattr(lot, 'start_date') else None,
            },
            "opening_balance": {
                "total_birds": (ob.initial_male_count + ob.initial_female_count) if ob else 0,
                "total_males": ob.initial_male_count if ob else 0,
                "total_females": ob.initial_female_count if ob else 0,
                "total_feed_kg": ob.accumulated_feed_kg if ob else 0,
            } if ob else None,
            "phases": [
                {
                    "id": p.id,
                    "start_date": str(p.start_date) if p.start_date else None,
                    "end_date": str(p.end_date) if p.end_date else None,
                    "is_active": p.is_active,
                }
                for p in phases
            ],
            "event_summary": {
                "total_events": sum(event_counts.values()),
                "by_type": event_counts,
                "by_status": status_dist,
            },
        }

    # ============================================================
    # SAP Comparison Report
    # ============================================================

    async def get_sap_comparison(self, lot_id: Optional[int] = None) -> dict:
        await self._exigir_lote(lot_id)
        base = select(OperationalEvent).where(
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.sap_document_ref != None,
        )
        if lot_id:
            base = base.where(OperationalEvent.lot_id == lot_id)

        result = await self.db.execute(base)
        events = list(result.scalars().all())

        matched = [e for e in events if e.status in (EventStatus.SAP_CONFIRMED, EventStatus.SENT_TO_SAP)]
        unmatched = [e for e in events if e.status == EventStatus.APPROVED]

        return {
            "total_with_sap_ref": len(events),
            "matched_with_sap": len(matched),
            "pending_sap_sync": len(unmatched),
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type.value,
                    "lot_id": e.lot_id,
                    "status": e.status.value,
                    "sap_ref": e.sap_document_ref,
                    "event_date": str(e.event_date),
                }
                for e in events[:50]
            ],
        }

    # ============================================================
    # All KPIs summary
    # ============================================================

    async def get_all_kpis(self, lot_id: Optional[int] = None) -> dict:
        await self._exigir_lote(lot_id)
        mortality = await self.get_kpi_mortality(lot_id) if lot_id else None
        feed = await self.get_kpi_feed_conversion(lot_id) if lot_id else None
        eggs = await self.get_kpi_egg_production(lot_id) if lot_id else None
        hatchery = await self.get_kpi_hatchery(lot_id)
        welfare = await self.get_kpi_animal_welfare(lot_id) if lot_id else None
        vacc_eff = await self.get_kpi_vaccination_efficiency(lot_id) if lot_id else None
        transfer_eff = await self.get_kpi_transfer_efficiency(lot_id) if lot_id else None

        return {
            "mortality": mortality,
            "feed_conversion": feed,
            "egg_production": eggs,
            "hatchery_yield": hatchery,
            "animal_welfare": welfare,
            "vaccination_efficiency": vacc_eff,
            "transfer_efficiency": transfer_eff,
        }

    # ============================================================
    # G-01: Animal Welfare Index
    # ============================================================

    async def get_kpi_animal_welfare(self, lot_id: int) -> dict:
        """Calculate animal welfare index based on health incidents, temperature, and observations."""
        await self._exigir_lote(lot_id)
        result = await self.db.execute(
            select(
                func.count(OperationalEvent.id).label("total_inspections"),
                func.count().filter(OperationalEvent.observations.ilike("%salud%")).label("health_issues"),
            ).where(
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type.in_([
                    EventType.FARM_INSPECTION, EventType.HATCHERY_INSPECTION,
                ]),
            )
        )
        row = result.one()
        total = row.total_inspections or 1
        issues = row.health_issues or 0
        welfare_score = max(0, 100 - (issues / total * 100)) if total > 0 else 100

        return {
            "lot_id": lot_id,
            "total_inspections": total,
            "health_incidents": issues,
            "welfare_score_pct": round(welfare_score, 1),
            "unit": "%",
        }

    # ============================================================
    # G-02: Vaccination Efficiency (Hatchery)
    # ============================================================

    async def get_kpi_vaccination_efficiency(self, lot_id: int) -> dict:
        """Vaccination efficiency: vaccinated chicks / total chicks born."""
        await self._exigir_lote(lot_id)
        q = select(
            func.coalesce(func.sum(BirdMovement.quantity), 0).label("total"),
        ).join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )

        born_result = await self.db.execute(
            q.where(OperationalEvent.event_type == EventType.BIRTH_REGISTRATION)
        )
        total_born = born_result.scalar() or 0

        vacc_result = await self.db.execute(
            select(func.count(OperationalEvent.id)).where(
                OperationalEvent.lot_id == lot_id,
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type == EventType.VACCINATION,
            )
        )
        vacc_events = vacc_result.scalar() or 0

        efficiency = (vacc_events / (total_born / 1000) * 100) if total_born > 0 else 0
        return {
            "lot_id": lot_id,
            "total_born": total_born,
            "vaccination_events": vacc_events,
            "vaccination_coverage_pct": round(min(efficiency, 100), 1),
            "unit": "%",
        }

    # ============================================================
    # G-03: Transfer Efficiency (Hatchery → Broiler)
    # ============================================================

    async def get_kpi_transfer_efficiency(self, lot_id: int) -> dict:
        """Transfer efficiency: chicks alive at dispatch / chicks born healthy."""
        await self._exigir_lote(lot_id)
        q_base = select(
            func.coalesce(func.sum(BirdMovement.quantity), 0).label("total"),
        ).join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )

        born_result = await self.db.execute(
            q_base.where(OperationalEvent.event_type == EventType.BIRTH_REGISTRATION)
        )
        total_born = born_result.scalar() or 1

        dispatch_result = await self.db.execute(
            q_base.where(OperationalEvent.event_type == EventType.CHICK_DISPATCH)
        )
        dispatched = dispatch_result.scalar() or 0

        efficiency = (dispatched / total_born * 100) if total_born > 0 else 0
        return {
            "lot_id": lot_id,
            "chicks_born": total_born,
            "chicks_dispatched": dispatched,
            "transfer_efficiency_pct": round(efficiency, 1),
            "unit": "%",
        }

    # ============================================================
    # G-04: Adjusted Feed Conversion Ratio (AFCR)
    # ============================================================

    async def get_kpi_afcr(self, lot_id: int) -> dict:
        """Adjusted FCR accounting for mortality."""
        await self._exigir_lote(lot_id)
        total_feed_kg = await self._sum_feed_kg(lot_id)

        q = select(
            func.coalesce(func.sum(BirdMovement.quantity), 0).label("total"),
        ).join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type.in_([
                EventType.WEIGHT_RECORDING, EventType.BIRD_EXIT,
            ]),
        )
        result = await self.db.execute(q)
        total_weight_kg = (result.scalar() or 0) / 1000  # convert g to kg

        afcr = total_feed_kg / total_weight_kg if total_weight_kg > 0 else 0
        return {
            "lot_id": lot_id,
            "total_feed_kg": round(total_feed_kg, 2),
            "total_weight_kg": round(total_weight_kg, 2),
            "afcr": round(afcr, 2),
            "unit": "kg feed / kg weight",
        }

    # ============================================================
    # G-05: Production Index (Broiler)
    # ============================================================

    async def get_kpi_production_index(self, lot_id: int) -> dict:
        """Broiler production index = (avg_weight_g * viability_pct) / (age_days * FCR)."""
        await self._exigir_lote(lot_id)
        # Get viability
        mortality_kpi = await self.get_kpi_mortality(lot_id)
        viability = 100 - mortality_kpi["mortality_rate_pct"]

        # Get average weight
        q = select(
            func.avg(BirdMovement.avg_weight).label("avg_w"),
        ).join(OperationalEvent, BirdMovement.event_id == OperationalEvent.id).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            # `GA-REM-022` (R-141): mismo conjunto filtrado que el detalle — pesajes
            # cancelados/pendientes ni entran, ni de cualquier otro tipo de evento.
            OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
            OperationalEvent.status.in_(_ESTADOS_ACEPTADOS),
            BirdMovement.avg_weight != None,
        )
        result = await self.db.execute(q)
        avg_weight_g = result.scalar() or 0

        # Get age
        lot_result = await self.db.execute(
            select(Lot).where(Lot.id == lot_id, Lot.company_id == self.company_id)
        )
        lot = lot_result.scalar_one_or_none()
        # `R-186` · `R-75` / `GA-REM-028`: misma normalización canónica que `get_kpi_ipe`
        # (R-184). `Lot.start_date` es `DateTime(timezone=True)`; sin normalizar,
        # `date − datetime` elevaba `TypeError` ⇒ HTTP 500 en todo lote con inicio.
        # `GA-REM-022` (R-131b): un lote cerrado no envejece — la edad se congela
        # en `end_date`; usar `today()` inflaba la edad (y el IPE) tras el cierre.
        hasta = _dia(lot.end_date) if (lot and lot.end_date) else date.today()
        age_days = (hasta - _dia(lot.start_date)).days if lot and lot.start_date else 30

        # Get FCR
        fcr_kpi = await self.get_kpi_feed_conversion(lot_id)
        fcr = fcr_kpi["feed_conversion_ratio"] or 1

        pi = (avg_weight_g * viability) / (age_days * fcr * 10) if (age_days * fcr) > 0 else 0
        return {
            "lot_id": lot_id,
            "avg_weight_g": round(avg_weight_g, 1),
            "viability_pct": round(viability, 1),
            "age_days": age_days,
            "fcr": round(fcr, 2),
            "production_index": round(pi, 1),
            "unit": "index",
        }

    # ============================================================
    # G-06: IPE — Índice de Producción Europeo
    # ============================================================

    async def get_kpi_ipe(self, lot_id: int) -> dict:
        """
        European Production Index (IPE).

        `OD-22` (2026-09-11, `GA-OD-01`; implementado por `R-187`): la viabilidad ya
        llega como porcentaje (0-100), así que el `× 100` histórico era una doble
        conversión fracción→porcentaje — se retira y el índice queda en la escala
        estándar del indicador (EPEF). Bandas/etiquetas/umbrales no cambian.
        IPE = (Viabilidad% × Ganancia_Diaria_g) / (FCR × 10)
        Ganancia diaria = avg_weight_g / age_days
        """
        await self._exigir_lote(lot_id)
        mortality_kpi = await self.get_kpi_mortality(lot_id)
        viabilidad = 100.0 - mortality_kpi["mortality_rate_pct"]

        q = select(func.avg(BirdMovement.avg_weight)).join(
            OperationalEvent, BirdMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
            # `GA-REM-022` (R-141): solo estados aceptados (detalle certificado).
            OperationalEvent.status.in_(_ESTADOS_ACEPTADOS),
            BirdMovement.avg_weight != None,
        )
        result = await self.db.execute(q)
        avg_weight_g = result.scalar() or 0.0

        lot_result = await self.db.execute(
            select(Lot).where(Lot.id == lot_id, Lot.company_id == self.company_id)
        )
        lot = lot_result.scalar_one_or_none()
        # `R-184` · `R-75` / `GA-REM-028`: `Lot.start_date` es `DateTime(timezone=True)`
        # y la edad del IPE es un día de calendario. Sin normalizar, `date − datetime`
        # elevaba `TypeError` ⇒ HTTP 500 en todo lote con inicio declarado (todo alta
        # fija). Se reutiliza la normalización canónica del día de negocio.
        # `GA-REM-022` (R-131b): un lote cerrado no envejece — la edad se congela
        # en `end_date`; usar `today()` inflaba la edad (y el IPE) tras el cierre.
        hasta = _dia(lot.end_date) if (lot and lot.end_date) else date.today()
        age_days = (hasta - _dia(lot.start_date)).days if lot and lot.start_date else 30
        if age_days <= 0:
            age_days = 1

        fcr_kpi = await self.get_kpi_feed_conversion(lot_id)
        fcr = fcr_kpi.get("feed_conversion_ratio") or 0.0

        ganancia_diaria = avg_weight_g / age_days if age_days > 0 else 0.0
        # `OD-22` / `R-187`: sin el `× 100` histórico (doble conversión — la viabilidad
        # ya es porcentaje 0-100). Escala estándar del indicador (típica ~200-400).
        ipe = (viabilidad * ganancia_diaria) / (fcr * 10) if fcr > 0 else 0.0

        return {
            "lot_id": lot_id,
            "viabilidad_pct": round(viabilidad, 2),
            "avg_weight_g": round(avg_weight_g, 1),
            "ganancia_diaria_g": round(ganancia_diaria, 2),
            "age_days": age_days,
            "fcr": round(fcr, 2),
            "ipe": round(ipe, 1),
            "reference": {"excellent": ">300", "good": "250-300", "average": "200-250"},
        }

    # ============================================================
    # G-07: Uniformidad de lote (CV% del peso)
    # ============================================================

    async def get_kpi_weight_uniformity(self, lot_id: int) -> dict:
        """
        Weight uniformity (lot uniformity).
        CV% = (STDDEV_SAMP(avg_weight) / AVG(avg_weight)) × 100
        Computed across all weight_recording events for the lot.
        Excellent: CV% < 8%, Acceptable: 8-12%, Poor: > 12%
        """
        await self._exigir_lote(lot_id)
        from sqlalchemy import text as sa_text
        q = select(
            func.avg(BirdMovement.avg_weight).label("mean_w"),
            func.stddev_samp(BirdMovement.avg_weight).label("std_w"),
            func.count(BirdMovement.id).label("n_samples"),
            func.min(BirdMovement.avg_weight).label("min_w"),
            func.max(BirdMovement.avg_weight).label("max_w"),
        ).join(
            OperationalEvent, BirdMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.WEIGHT_RECORDING,
            # `GA-REM-022` (R-141): un pesaje cancelado no es una muestra.
            OperationalEvent.status.in_(_ESTADOS_ACEPTADOS),
            BirdMovement.avg_weight != None,
            BirdMovement.avg_weight > 0,
        )
        result = await self.db.execute(q)
        row = result.one_or_none()
        if not row or not row.mean_w or row.n_samples < 2:
            return {
                "lot_id": lot_id,
                "n_samples": row.n_samples if row else 0,
                "mean_weight_g": None,
                "cv_pct": None,
                "uniformity_status": "insufficient_data",
            }

        mean_w = float(row.mean_w)
        std_w = float(row.std_w or 0)
        cv_pct = (std_w / mean_w * 100) if mean_w > 0 else 0.0

        if cv_pct < 8:
            status = "excellent"
        elif cv_pct < 12:
            status = "acceptable"
        else:
            status = "poor"

        return {
            "lot_id": lot_id,
            "n_samples": row.n_samples,
            "mean_weight_g": round(mean_w, 1),
            "std_weight_g": round(std_w, 1),
            "min_weight_g": round(float(row.min_w), 1),
            "max_weight_g": round(float(row.max_w), 1),
            "cv_pct": round(cv_pct, 2),
            "uniformity_status": status,
            "reference": {"excellent": "CV% < 8%", "acceptable": "CV% 8-12%", "poor": "CV% > 12%"},
        }
