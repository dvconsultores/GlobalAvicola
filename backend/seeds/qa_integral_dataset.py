"""SPEC 007 · QA INTEGRAL SYNTHETIC DATASET AND USER ACCEPTANCE PACK — seed canónico `QA-DEMO-V1`.

    uso (desde backend/):
        .venv/bin/python -m seeds.qa_integral_dataset --inventory
        .venv/bin/python -m seeds.qa_integral_dataset --apply   --confirm-target <nombre_bd> [--fixtures-dir DIR]
        .venv/bin/python -m seeds.qa_integral_dataset --verify
        .venv/bin/python -m seeds.qa_integral_dataset --cleanup --dry-run
        .venv/bin/python -m seeds.qa_integral_dataset --cleanup --confirm-target <nombre_bd> [--force-unmarked]

Reglas: sintético, trazable (`QA-`/`qa.`/`QA_DEMO_V1`/`QA_SYNTHETIC`), idempotente (dos `--apply` no duplican),
removible (`--cleanup` solo borra lo marcado, fail-closed ante ambigüedad), aislado (dos empresas QA propias).
Ninguna llamada a SAP: los datos SAP son `QA_SYNTHETIC` y el readiness real no se toca. Contraseñas: nunca en
código ni en logs — `GA_QA_SEED_PASSWORD` o archivo temporal 0600 fuera del repositorio.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from seeds.qa_integral_builders import (ALL_BU, COMPANY_ISO, COMPANY_MAIN, EMAIL_DOMAIN, MARKER, PREFIX, SAP_SOURCE,
                                        TAX_ISO, TAX_MAIN, USER_PREFIX, USUARIOS, VERSION, Contexto, D, QaBuilder)

FORBIDDEN_ENVIRONMENTS = {"production", "prod", "staging", "pre", "preprod"}
CREDENCIALES_POR_DEFECTO = Path("/tmp/global_avicola_qa_credentials.txt")
FIXTURES_POR_DEFECTO = Path(__file__).resolve().parents[2] / "audit" / "qa-integral-dataset" / "fixtures"


# ── guardas ──────────────────────────────────────────────────────────────────

def es_codigo_qa(codigo: str) -> bool:
    """`QA-…` y los códigos SAP cortos de centro/almacén (`QAP1`, `QAP1-0001`): todos sintéticos."""
    return codigo.startswith(PREFIX) or codigo.startswith("QAP")


def destino_configurado() -> tuple[str, str]:
    """(host, base) del `DATABASE_URL` efectivo, sin credenciales."""
    url = settings.database_url
    resto = url.split("@", 1)[-1]
    host = resto.split("/", 1)[0]
    base = resto.split("/", 1)[1].split("?", 1)[0] if "/" in resto else ""
    return host or "(socket)", base


def exigir_entorno_seguro(*, escribe: bool, confirm_target: Optional[str]) -> None:
    entorno = (settings.ENVIRONMENT or "").strip().lower()
    if entorno in FORBIDDEN_ENVIRONMENTS:
        sys.exit(f"[qa-seed] ABORTADO: ENVIRONMENT='{entorno}' no es un entorno autorizado para datos sintéticos.")
    host, base = destino_configurado()
    print(f"[qa-seed] entorno={entorno or 'development'} · destino host={host} · base={base}")
    if escribe:
        esperado = confirm_target or os.environ.get("GA_QA_SEED_CONFIRM_TARGET")
        if not esperado or esperado != base:
            sys.exit(f"[qa-seed] ABORTADO: la escritura exige --confirm-target {base!r} (o GA_QA_SEED_CONFIRM_TARGET). "
                     "No hay override silencioso.")


def credenciales(ruta: Path, *, usuarios: tuple[str, ...]) -> dict[str, str]:
    """Una contraseña por usuario QA. `GA_QA_SEED_PASSWORD` (misma para todos) o archivo 0600 fuera del repo."""
    desde_env = os.environ.get("GA_QA_SEED_PASSWORD")
    if desde_env:
        return {u: desde_env for u in usuarios}
    if ruta.exists():
        datos = json.loads(ruta.read_text())
        if all(u in datos for u in usuarios):
            return {u: datos[u] for u in usuarios}
        # usuarios nuevos en el dataset: se completan sin tocar los existentes
        clave_comun = next(iter(datos.values()))
        datos.update({u: clave_comun for u in usuarios if u not in datos})
    else:
        clave_comun = secrets.token_urlsafe(14)
        datos = {u: clave_comun for u in usuarios}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2))
    os.chmod(ruta, stat.S_IRUSR | stat.S_IWUSR)
    print(f"[qa-seed] credenciales QA en {ruta} (0600; entregar al Owner por canal separado; no se versionan)")
    return datos


def sha_actual() -> Optional[str]:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=Path(__file__).resolve().parents[2]).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


# ── escenarios ───────────────────────────────────────────────────────────────

async def escenarios(b: QaBuilder) -> None:
    """Lotes, historia operativa (4–8 semanas), workflow, correcciones, reversos, notificaciones y cutover."""
    ctx = b.ctx
    m = ctx.companies["MAIN"]
    cat = ctx.catalogs
    feed = lambda n: cat[f"feed:{m.id}:{n}"].id  # noqa: E731
    vac = lambda n: cat[f"vaccine:{m.id}:{n}"].id  # noqa: E731
    med = lambda n: cat[f"medication:{m.id}:{n}"].id  # noqa: E731
    mort = lambda n: cat[f"mortality_cause:{m.id}:{n}"].id  # noqa: E731
    cull = lambda n: cat[f"cull_cause:{m.id}:{n}"].id  # noqa: E731
    tr = lambda n: cat[f"transport:{m.id}:{n}"].id  # noqa: E731
    planta_benef = cat[f"plant:{m.id}:1"].id
    prov_genetica = cat[f"supplier:{m.id}:genetica"].id
    inc = ctx.hatcheries["QA-INC-01"]
    incubadora = lambda n: ctx.incubators[f"QA Incubadora A{n}"].id  # noqa: E731
    nacedora = lambda n: ctx.hatchers[f"QA Nacedora N{n}"].id  # noqa: E731
    farm_inc, farm_gp, farm_br, farm_en1, farm_en2 = (ctx.farms[k] for k in ("QA-INC-F1", "QA-GP-01", "QA-BR-01", "QA-EN-01", "QA-EN-02"))

    def aves(sexo, q, peso=None, **k):
        d = {"sex": sexo, "quantity": q}
        if peso is not None:
            d["avg_weight"] = peso
        d.update(k)
        return d

    async def inspeccion(actor, lote, dias, clave, house):
        return await b.evento(actor, lote, "farm_inspection", dias, clave, inspection_details=[
            {"house_id": house, "parameter": "limpieza y desinfección", "value": "conforme"},
            {"house_id": house, "parameter": "temperatura", "value": "31 °C"}])

    # ── PROGENITORAS ───────────────────────────────────────────────────────
    gp_cria = await b.lote("QA-GP-CRIA-001", empresa="MAIN", bu="grandparent", farm="QA-GP-01", house="QA-GP-01-G1", line="QA-LINE-GP",
                           start_days=42, area="QA-AREA-GP")
    await b.fase_de_lote(gp_cria, "CRIA", 42, 1200, 4800)
    await inspeccion("qa.operator.gp", gp_cria, 42, "gp-cria-insp-0", gp_cria.house_id)
    await b.evento("qa.operator.gp", gp_cria, "grandparent_import", 42, "gp-cria-import", sap_document_ref="QA-OC-GP-IMPORT-005",
                   supplier_id=prov_genetica, transport_id=tr(1),
                   extra_data={"import_plan": {"origin_country": "Francia", "purchased_total": 6200, "shipped_total": 6100, "received_total": 6000,
                                               "transit_mortality": 100, "departure_date": D(44).isoformat(), "arrival_date": D(42).isoformat(),
                                               "quarantine_days": 21, "quarantine_end_date": D(21).isoformat()}},
                   bird_movements=[aves("male", 1200, 42.0), aves("female", 4800, 40.0)])
    await b.evento("qa.operator.gp", gp_cria, "transport_inspection", 42, "gp-cria-transp", transport_id=tr(1),
                   inspection_details=[{"parameter": "temperatura del vehículo", "value": "24 °C"}, {"parameter": "ventilación", "value": "conforme"}])
    await b.evento("qa.operator.gp", gp_cria, "bird_reception", 42, "gp-cria-recepcion", sap_document_ref="QA-OC-GP-IMPORT-005",
                   supplier_id=prov_genetica, transport_id=tr(1),
                   bird_movements=[aves("male", 1200, 42.0, target_house_id=gp_cria.house_id), aves("female", 4800, 40.0, target_house_id=gp_cria.house_id)])
    await b.evento("qa.operator.gp", gp_cria, "bird_distribution", 41, "gp-cria-distrib",
                   bird_movements=[aves("mixed", 6000, target_house_id=gp_cria.house_id)])
    for i, dias in enumerate((35, 28, 21, 14, 7), start=1):
        await b.evento("qa.operator.gp", gp_cria, "feed_registration", dias, f"gp-cria-feed-{i}", feed_movements=[{"feed_type_id": feed(1 if i < 3 else 2), "quantity_kg": 1800 + i * 350, "sacks_count": (1800 + i * 350) // 40}])
        await b.evento("qa.operator.gp", gp_cria, "weight_recording", dias, f"gp-cria-peso-{i}", bird_movements=[aves("mixed", 30, [110, 230, 380, 540, 700][i - 1], week_number=i)])
        await b.evento("qa.operator.gp", gp_cria, "mortality_recording", dias, f"gp-cria-mort-{i}", cause_id=mort(1 + i % 3), bird_movements=[aves("female", 7, 300.0), aves("male", 3, 320.0)])
    await b.evento("qa.operator.gp", gp_cria, "vaccination", 35, "gp-cria-vac-1", vaccine_id=vac(1), vaccination_route="water", vaccine_lot_number="QA-VL-001")
    await b.evento("qa.operator.gp", gp_cria, "vaccination", 21, "gp-cria-vac-2", vaccine_id=vac(2), vaccination_route="water", vaccine_lot_number="QA-VL-002")
    await b.evento("qa.operator.gp", gp_cria, "medication", 24, "gp-cria-med-1", medication_id=med(2), dosage_per_bird=0.5, treatment_days=3)
    await b.evento("qa.operator.gp", gp_cria, "cull_recording", 14, "gp-cria-cull-1", cull_cause_id=cull(1), bird_movements=[aves("male", 5, 500.0)])

    gp_prod = await b.lote("QA-GP-PROD-001", empresa="MAIN", bu="grandparent", farm="QA-GP-01", house="QA-GP-01-G2", line="QA-LINE-GP",
                           start_days=200, area="QA-AREA-GP")
    await b.apertura_manual(gp_prod, fase="PROD", machos=900, hembras=8500, edad=200, mort_m=100, mort_f=500, feed_kg=150000, peso_g=3400, huevos=120000, a_incubadora=100000)
    await b.fase_de_lote(gp_prod, "PROD", 60, 900, 8500)
    await b.evento("qa.operator.gp", gp_prod, "egg_collection", 84, "gp-prod-huevos-0", egg_movements=[{"egg_type": "fertile", "quantity": 38000}, {"egg_type": "dirty", "quantity": 900}])
    await b.evento("qa.operator.gp", gp_prod, "egg_dispatch", 81, "gp-prod-desp-0", destination_farm_id=farm_inc.id, transport_id=tr(2), egg_movements=[{"egg_type": "fertile", "quantity": 20000}])
    for i, dias in enumerate((56, 49, 42, 35, 28, 21, 14, 7), start=1):
        await b.evento("qa.operator.gp", gp_prod, "egg_collection", dias, f"gp-prod-huevos-{i}", egg_movements=[
            {"egg_type": "fertile", "quantity": 38000 - i * 150}, {"egg_type": "dirty", "quantity": 900}, {"egg_type": "broken", "quantity": 300}, {"egg_type": "discarded", "quantity": 200}])
        await b.evento("qa.operator.gp", gp_prod, "egg_classification", dias, f"gp-prod-clasif-{i}", egg_movements=[{"egg_type": "fertile", "quantity": 37000, "classification_date": D(dias).isoformat()}])
        await b.evento("qa.operator.gp", gp_prod, "feed_registration", dias, f"gp-prod-feed-{i}", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 9800, "sacks_count": 0}])
        await b.evento("qa.operator.gp", gp_prod, "weight_recording", dias, f"gp-prod-peso-{i}", bird_movements=[aves("female", 30, 3450 + i * 8, week_number=28 + i)])
        await b.evento("qa.operator.gp", gp_prod, "mortality_recording", dias, f"gp-prod-mort-{i}", cause_id=mort(1), bird_movements=[aves("female", 14, 3400.0), aves("male", 2, 3900.0)])
        if i <= 6:
            await b.evento("qa.operator.gp", gp_prod, "egg_dispatch", dias - 2, f"gp-prod-desp-{i}", destination_farm_id=farm_inc.id, transport_id=tr(2), egg_movements=[{"egg_type": "fertile", "quantity": 20000}])
    await inspeccion("qa.operator.gp", gp_prod, 30, "gp-prod-insp-1", gp_prod.house_id)
    await b.evento("qa.operator.gp", gp_prod, "vaccination", 40, "gp-prod-vac-1", vaccine_id=vac(4), vaccination_route="spray", vaccine_lot_number="QA-VL-004")

    gp_close = await b.lote("QA-GP-CLOSE-001", empresa="MAIN", bu="grandparent", farm="QA-GP-01", house="QA-GP-01-G3", line="QA-LINE-GP",
                            start_days=420, area="QA-AREA-GP", planned_close_days=10)
    await b.apertura_manual(gp_close, fase="PROD", machos=200, hembras=2000, edad=420, mort_m=60, mort_f=400, feed_kg=310000, peso_g=3600, huevos=380000, a_incubadora=330000)
    await b.fase_de_lote(gp_close, "PROD", 280, 200, 2000)
    for i, dias in enumerate((28, 21, 14, 7), start=1):
        await b.evento("qa.operator.gp", gp_close, "egg_collection", dias, f"gp-close-huevos-{i}", egg_movements=[{"egg_type": "fertile", "quantity": 5200}, {"egg_type": "commercial", "quantity": 900}])
        await b.evento("qa.operator.gp", gp_close, "feed_registration", dias, f"gp-close-feed-{i}", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 2400, "sacks_count": 0}])
        await b.evento("qa.operator.gp", gp_close, "mortality_recording", dias, f"gp-close-mort-{i}", cause_id=mort(3), bird_movements=[aves("female", 9, 3500.0)])
    await b.notificar(empresa="MAIN", destinatario="qa.supervisor", tipo="lot_near_close", leida=True, ocurrencia=f"near-close:{gp_close.lot_code}",
                      payload={"lot_id": gp_close.id, "lot_code": gp_close.lot_code, "planned_close_date": D(-10).isoformat()}, entidad="lot", entidad_id=gp_close.id)
    await b.notificar(empresa="MAIN", destinatario="qa.operator.gp", tipo="lot_near_close", leida=False, ocurrencia=f"near-close-op:{gp_close.lot_code}",
                      payload={"lot_id": gp_close.id, "lot_code": gp_close.lot_code, "planned_close_date": D(-10).isoformat()}, entidad="lot", entidad_id=gp_close.id)

    gp_closed = await b.lote("QA-GP-CLOSED-001", empresa="MAIN", bu="grandparent", farm="QA-GP-01", house="QA-GP-01-G3", line="QA-LINE-GP", start_days=500, area="QA-AREA-GP")
    await b.apertura_manual(gp_closed, fase="PROD", machos=150, hembras=1400, edad=500, mort_m=50, mort_f=600, feed_kg=360000, peso_g=3700, huevos=410000, a_incubadora=360000)
    await b.evento("qa.operator.gp", gp_closed, "feed_registration", 60, "gp-closed-feed-1", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 1600, "sacks_count": 0}])
    await b.evento("qa.operator.gp", gp_closed, "weight_recording", 60, "gp-closed-peso-1", bird_movements=[aves("female", 30, 3700, week_number=70)])
    await b.evento("qa.operator.gp", gp_closed, "bird_exit", 58, "gp-closed-salida", destination_plant_id=planta_benef, transport_id=tr(3), bird_movements=[aves("male", 150, 4200.0), aves("female", 1400, 3700.0)])
    await b.evento("qa.operator.gp", gp_closed, "lot_closure", 58, "gp-closed-cierre")
    await b.cerrar_lote(gp_closed, 58)

    # ── REPRODUCTORAS ──────────────────────────────────────────────────────
    br_cria = await b.lote("QA-BR-CRIA-001", empresa="MAIN", bu="breeder", farm="QA-BR-01", house="QA-BR-01-G1", line="QA-LINE-BR", start_days=56, area="QA-AREA-BR")
    await b.fase_de_lote(br_cria, "CRIA", 56, 500, 4500)
    # Cadena generacional GP → huevo → incubadora → pollito reproductor → este lote (ver proceso QA-HAT-GPGEN-001).
    hat_gpgen = await b.lote("QA-HAT-GPGEN-001", empresa="MAIN", bu="hatchery", farm="QA-INC-F1", house="QA-INC-F1-G1", line=None, start_days=80, area="QA-AREA-INC", hatchery_purpose="grandparent")
    await b.fase_de_lote(hat_gpgen, "INCUB", 80, 0, 0)
    await b.evento("qa.operator.hatchery", hat_gpgen, "egg_reception_hatchery", 80, "hat-gpgen-recep", egg_movements=[{"egg_type": "fertile", "quantity": 20000}])
    await b.evento("qa.operator.hatchery", hat_gpgen, "egg_reception_classification", 80, "hat-gpgen-clasif", egg_movements=[{"egg_type": "fertile", "quantity": 19000}, {"egg_type": "discarded", "quantity": 1000}])
    await b.evento("qa.operator.hatchery", hat_gpgen, "incubation_load", 79, "hat-gpgen-carga", hatchery_params=[{"hatchery_id": inc.id, "incubator_id": incubadora(1), "quantity_loaded": 19000, "temperature": 37.6, "humidity": 55.0, "co2": 0.4, "turning": True}])
    await b.evento("qa.operator.hatchery", hat_gpgen, "ovoscopy", 72, "hat-gpgen-ovo", egg_movements=[{"egg_type": "infertile", "quantity": 800}])
    await b.evento("qa.operator.hatchery", hat_gpgen, "transfer_to_hatcher", 61, "hat-gpgen-transf", hatchery_params=[{"hatchery_id": inc.id, "hatcher_id": nacedora(1), "quantity_transferred": 18000, "temperature": 36.9, "humidity": 65.0}])
    await b.evento("qa.operator.hatchery", hat_gpgen, "birth_registration", 58, "hat-gpgen-nac", chicks_healthy=16000, chicks_weak=500, bird_movements=[aves("mixed", 16500, 40.0)])
    await b.evento("qa.operator.hatchery", hat_gpgen, "chick_dispatch", 56, "hat-gpgen-desp", destination_farm_id=farm_br.id, transport_id=tr(1), bird_movements=[aves("mixed", 5000, 41.0)])
    await inspeccion("qa.operator.breeder", br_cria, 56, "br-cria-insp-0", br_cria.house_id)
    await b.evento("qa.operator.breeder", br_cria, "bird_reception", 56, "br-cria-recepcion", sap_document_ref="QA-OC-BR-AVES-002", transport_id=tr(1),
                   received_total=5100, dead_on_arrival=60, rejected_on_arrival=40,
                   bird_movements=[aves("male", 500, 41.0, target_house_id=br_cria.house_id), aves("female", 4500, 40.0, target_house_id=br_cria.house_id)])
    await b.evento("qa.operator.breeder", br_cria, "bird_distribution", 55, "br-cria-distrib", bird_movements=[aves("mixed", 5000, target_house_id=br_cria.house_id)])
    for i, dias in enumerate((49, 42, 35, 28, 21, 14, 7), start=1):
        await b.evento("qa.operator.breeder", br_cria, "feed_registration", dias, f"br-cria-feed-{i}", feed_movements=[{"feed_type_id": feed(1 if i < 3 else 2), "quantity_kg": 1500 + i * 300, "sacks_count": (1500 + i * 300) // 40}])
        await b.evento("qa.operator.breeder", br_cria, "water_consumption", dias, f"br-cria-agua-{i}", water_liters=3000 + i * 500)
        await b.evento("qa.operator.breeder", br_cria, "weight_recording", dias, f"br-cria-peso-{i}", bird_movements=[aves("mixed", 30, [110, 230, 380, 540, 700, 860, 1000][i - 1], week_number=i)])
        await b.evento("qa.operator.breeder", br_cria, "mortality_recording", dias, f"br-cria-mort-{i}", cause_id=mort(2), bird_movements=[aves("female", 6, 400.0), aves("male", 1, 420.0)])
    await b.evento("qa.operator.breeder", br_cria, "vaccination", 49, "br-cria-vac-1", vaccine_id=vac(1), vaccination_route="water", vaccine_lot_number="QA-VL-011")
    await b.evento("qa.operator.breeder", br_cria, "vaccination", 35, "br-cria-vac-2", vaccine_id=vac(3), vaccination_route="injection", vaccine_lot_number="QA-VL-012")
    await b.evento("qa.operator.breeder", br_cria, "medication", 28, "br-cria-med-1", medication_id=med(1), dosage_per_bird=0.2, treatment_days=5)
    await b.evento("qa.operator.breeder", br_cria, "cull_recording", 21, "br-cria-cull-1", cull_cause_id=cull(2), bird_movements=[aves("female", 12, 600.0)])

    br_prod1 = await b.lote("QA-BR-PROD-001", empresa="MAIN", bu="breeder", farm="QA-BR-01", house="QA-BR-01-G2", line="QA-LINE-BR", start_days=220, area="QA-AREA-BR")
    await b.apertura_manual(br_prod1, fase="PROD", machos=1000, hembras=9000, edad=220, mort_m=80, mort_f=420, feed_kg=160000, peso_g=3300, huevos=200000, a_incubadora=170000)
    await b.fase_de_lote(br_prod1, "PROD", 80, 1000, 9000)
    for i, dias in enumerate((56, 49, 42, 35, 28, 21), start=1):
        await b.evento("qa.operator.breeder", br_prod1, "egg_collection", dias, f"br-prod1-huevos-{i}", egg_movements=[
            {"egg_type": "fertile", "quantity": 43400}, {"egg_type": "dirty", "quantity": 1000}, {"egg_type": "broken", "quantity": 400}])
        await b.evento("qa.operator.breeder", br_prod1, "egg_classification", dias, f"br-prod1-clasif-{i}", egg_movements=[{"egg_type": "fertile", "quantity": 43000, "classification_date": D(dias).isoformat()}])
        await b.evento("qa.operator.breeder", br_prod1, "feed_registration", dias, f"br-prod1-feed-{i}", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 11200, "sacks_count": 0}])
        await b.evento("qa.operator.breeder", br_prod1, "water_consumption", dias, f"br-prod1-agua-{i}", water_liters=21000)
        await b.evento("qa.operator.breeder", br_prod1, "weight_recording", dias, f"br-prod1-peso-{i}", bird_movements=[aves("female", 30, 3300 + i * 6, week_number=31 + i)])
        await b.evento("qa.operator.breeder", br_prod1, "mortality_recording", dias, f"br-prod1-mort-{i}", cause_id=mort(1), bird_movements=[aves("female", 16, 3300.0), aves("male", 2, 3800.0)])
    for d in range(14, 0, -1):  # recolección diaria (serie para reportes)
        await b.evento("qa.operator.breeder", br_prod1, "egg_collection", d, f"br-prod1-huevos-d{d}", egg_movements=[
            {"egg_type": "fertile", "quantity": 6100 + (d % 4) * 90}, {"egg_type": "dirty", "quantity": 150}, {"egg_type": "broken", "quantity": 60}])
    for i, dias in enumerate((14, 7), start=7):
        await b.evento("qa.operator.breeder", br_prod1, "feed_registration", dias, f"br-prod1-feed-{i}", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 11000, "sacks_count": 0}])
        await b.evento("qa.operator.breeder", br_prod1, "water_consumption", dias, f"br-prod1-agua-{i}", water_liters=20500)
        await b.evento("qa.operator.breeder", br_prod1, "mortality_recording", dias, f"br-prod1-mort-{i}", cause_id=mort(1), bird_movements=[aves("female", 12, 3300.0)])

    br_prod2 = await b.lote("QA-BR-PROD-002", empresa="MAIN", bu="breeder", farm="QA-BR-01", house="QA-BR-01-G3", line="QA-LINE-BR", start_days=180, area="QA-AREA-BR")
    await b.apertura_manual(br_prod2, fase="PROD", machos=800, hembras=7200, edad=180, mort_m=40, mort_f=300, feed_kg=120000, peso_g=3250, huevos=90000, a_incubadora=70000)
    await b.fase_de_lote(br_prod2, "PROD", 40, 800, 7200)
    for i, dias in enumerate((42, 35, 28, 21, 14, 7), start=1):
        await b.evento("qa.operator.breeder", br_prod2, "egg_collection", dias, f"br-prod2-huevos-{i}", egg_movements=[{"egg_type": "fertile", "quantity": 34000}, {"egg_type": "dirty", "quantity": 700}])
        await b.evento("qa.operator.breeder", br_prod2, "feed_registration", dias, f"br-prod2-feed-{i}", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 9000, "sacks_count": 0}])
        await b.evento("qa.operator.breeder", br_prod2, "water_consumption", dias, f"br-prod2-agua-{i}", water_liters=17000)
        await b.evento("qa.operator.breeder", br_prod2, "mortality_recording", dias, f"br-prod2-mort-{i}", cause_id=mort(4), bird_movements=[aves("female", 10, 3250.0)])

    br_closed = await b.lote("QA-BR-CLOSED-001", empresa="MAIN", bu="breeder", farm="QA-BR-01", house="QA-BR-01-G3", line="QA-LINE-BR", start_days=460, area="QA-AREA-BR")
    await b.apertura_manual(br_closed, fase="PROD", machos=100, hembras=900, edad=460, mort_m=40, mort_f=500, feed_kg=300000, peso_g=3600, huevos=330000, a_incubadora=290000)
    await b.evento("qa.operator.breeder", br_closed, "feed_registration", 70, "br-closed-feed-1", feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 900, "sacks_count": 0}])
    await b.evento("qa.operator.breeder", br_closed, "weight_recording", 70, "br-closed-peso-1", bird_movements=[aves("female", 30, 3600, week_number=65)])
    await b.evento("qa.operator.breeder", br_closed, "bird_exit", 66, "br-closed-salida", destination_plant_id=planta_benef, transport_id=tr(3), bird_movements=[aves("male", 100, 4000.0), aves("female", 900, 3600.0)])
    await b.evento("qa.operator.breeder", br_closed, "lot_closure", 66, "br-closed-cierre")
    await b.cerrar_lote(br_closed, 66)

    # ── INCUBADORA (procesos en distintas etapas, alimentados por QA-BR-PROD-001) ──
    async def proceso(code, *, desp, recep, cargar=None, inc_n=1, ovo=None, transf=None, nac=None, pollitos=None, desp_pollitos=None, mort=None):
        lote = await b.lote(code, empresa="MAIN", bu="hatchery", farm="QA-INC-F1", house="QA-INC-F1-G1", line=None, start_days=recep[0], area="QA-AREA-INC", hatchery_purpose="breeder")
        await b.fase_de_lote(lote, "INCUB", recep[0], 0, 0)
        await b.evento("qa.operator.breeder", br_prod1, "egg_dispatch", desp[0], f"{code}-desp-origen", destination_farm_id=farm_inc.id, transport_id=tr(2), egg_movements=[{"egg_type": "fertile", "quantity": desp[1]}])
        await b.evento("qa.operator.hatchery", lote, "egg_reception_hatchery", recep[0], f"{code}-recep", egg_movements=[{"egg_type": "fertile", "quantity": recep[1]}])
        await b.evento("qa.operator.hatchery", lote, "egg_reception_classification", recep[0], f"{code}-clasif", egg_movements=[{"egg_type": "fertile", "quantity": recep[1] - 400}, {"egg_type": "discarded", "quantity": 400}])
        if cargar:
            await b.evento("qa.operator.hatchery", lote, "incubation_load", cargar[0], f"{code}-carga", hatchery_params=[{"hatchery_id": inc.id, "incubator_id": incubadora(inc_n), "quantity_loaded": cargar[1], "temperature": 37.6, "humidity": 55.0, "co2": 0.4, "turning": True}])
        if ovo:
            await b.evento("qa.operator.hatchery", lote, "ovoscopy", ovo[0], f"{code}-ovo", egg_movements=[{"egg_type": "infertile", "quantity": ovo[1]}])
        if transf:
            await b.evento("qa.operator.hatchery", lote, "transfer_to_hatcher", transf[0], f"{code}-transf", hatchery_params=[{"hatchery_id": inc.id, "hatcher_id": nacedora(1 if inc_n != 3 else 2), "quantity_transferred": transf[1], "temperature": 36.9, "humidity": 65.0}])
        if nac:
            await b.evento("qa.operator.hatchery", lote, "birth_registration", nac[0], f"{code}-nac", chicks_healthy=nac[2], chicks_weak=nac[1] - nac[2], bird_movements=[aves("mixed", nac[1], 40.0)])
        if mort:
            await b.evento("qa.operator.hatchery", lote, "mortality_recording", mort[0], f"{code}-mort", cause_id=mort[2], bird_movements=[aves("mixed", mort[1], 40.0)])
        if desp_pollitos:
            await b.evento("qa.operator.hatchery", lote, "chick_dispatch", desp_pollitos[0], f"{code}-desp-pollitos", destination_farm_id=desp_pollitos[2], transport_id=tr(1), bird_movements=[aves("mixed", desp_pollitos[1], 41.0)])
        return lote

    await proceso("QA-HAT-REC-001", desp=(3, 30000), recep=(2, 30000))
    await proceso("QA-HAT-INC-001", desp=(13, 30000), recep=(12, 30000), cargar=(11, 28000), inc_n=1)
    await proceso("QA-HAT-OVO-001", desp=(11, 30000), recep=(10, 30000), cargar=(9, 29000), inc_n=2)
    await proceso("QA-HAT-NAC-001", desp=(22, 30000), recep=(21, 30000), cargar=(20, 28500), inc_n=3, ovo=(13, 1200), transf=(2, 27000))
    await proceso("QA-HAT-BIRTH-001", desp=(26, 30000), recep=(25, 30000), cargar=(24, 29000), inc_n=1, ovo=(17, 1300), transf=(6, 27500), nac=(3, 24000, 23500))
    hat_chick = await proceso("QA-HAT-CHICK-001", desp=(30, 30000), recep=(29, 30000), cargar=(28, 30000), inc_n=2, ovo=(21, 1400), transf=(10, 28400),
                              nac=(7, 25000, 24400), mort=(5, 50, mort(1)), desp_pollitos=(6, 10000, farm_en1.id))
    await b.evento("qa.operator.hatchery", None, "hatchery_inspection", 15, "hat-insp-1", empresa="MAIN", farm_id=None, house_id=None,
                   inspection_details=[{"parameter": "temperatura sala incubación", "value": "25 °C"}, {"parameter": "higiene nacedoras", "value": "conforme"}])

    # ── POLLO DE ENGORDE ───────────────────────────────────────────────────
    bro1 = await b.lote("QA-BRO-001", empresa="MAIN", bu="broiler", farm="QA-EN-01", house="QA-EN-01-G1", line="QA-LINE-BRO", start_days=6, area="QA-AREA-ENG", planned_close_days=36)
    await b.fase_de_lote(bro1, "ENGORDE", 6, 0, 0)
    await b.evento("qa.operator.broiler", bro1, "bird_reception", 6, "bro1-recepcion", sap_document_ref="QA-OC-BRO-AVES-003", transport_id=tr(1),
                   bird_movements=[aves("mixed", 10000, 41.0, target_house_id=bro1.house_id)])
    await b.evento("qa.operator.broiler", bro1, "bird_distribution", 6, "bro1-distrib", bird_movements=[aves("mixed", 10000, target_house_id=bro1.house_id)])
    for d in range(5, 0, -1):
        await b.evento("qa.operator.broiler", bro1, "feed_registration", d, f"bro1-feed-d{d}", feed_movements=[{"feed_type_id": feed(1), "quantity_kg": 260 + (6 - d) * 60, "sacks_count": (260 + (6 - d) * 60) // 40}])
        await b.evento("qa.operator.broiler", bro1, "water_consumption", d, f"bro1-agua-d{d}", water_liters=600 + (6 - d) * 120)
        await b.evento("qa.operator.broiler", bro1, "mortality_recording", d, f"bro1-mort-d{d}", cause_id=mort(1), bird_movements=[aves("mixed", 4 + d % 3, 60.0)])
    await b.evento("qa.operator.broiler", bro1, "weight_recording", 3, "bro1-peso-1", bird_movements=[aves("mixed", 50, 95.0, week_number=1)])
    await b.evento("qa.operator.broiler", bro1, "vaccination", 4, "bro1-vac-1", vaccine_id=vac(1), vaccination_route="water", vaccine_lot_number="QA-VL-021")

    bro2 = await b.lote("QA-BRO-002", empresa="MAIN", bu="broiler", farm="QA-EN-01", house="QA-EN-01-G2", line="QA-LINE-BRO", start_days=28, area="QA-AREA-ENG", planned_close_days=14)
    await b.fase_de_lote(bro2, "ENGORDE", 28, 0, 0)
    await inspeccion("qa.operator.broiler", bro2, 28, "bro2-insp-0", bro2.house_id)
    await b.evento("qa.operator.broiler", bro2, "bird_reception", 28, "bro2-recepcion", sap_document_ref="QA-OC-BRO-AVES-004", transport_id=tr(1),
                   bird_movements=[aves("mixed", 12000, 42.0, target_house_id=bro2.house_id)])
    rec_extra = await b.evento("qa.operator.broiler", bro2, "bird_reception", 27, "bro2-recepcion-extra", sap_document_ref="QA-OC-BRO-AVES-004", transport_id=tr(1),
                               bird_movements=[aves("mixed", 500, 42.0, target_house_id=bro2.house_id)])
    for i, dias in enumerate((21, 14, 7), start=1):
        await b.evento("qa.operator.broiler", bro2, "feed_registration", dias, f"bro2-feed-{i}", feed_movements=[{"feed_type_id": feed(2), "quantity_kg": 2000 + i * 2000, "sacks_count": (2000 + i * 2000) // 40}])
        await b.evento("qa.operator.broiler", bro2, "water_consumption", dias, f"bro2-agua-{i}", water_liters=5000 + i * 3500)
        await b.evento("qa.operator.broiler", bro2, "weight_recording", dias, f"bro2-peso-{i}", bird_movements=[aves("mixed", 50, [450, 900, 1400][i - 1], week_number=i)])
        await b.evento("qa.operator.broiler", bro2, "mortality_recording", dias, f"bro2-mort-{i}", cause_id=mort(2), bird_movements=[aves("mixed", 40 - i * 5, 700.0)])
    await b.evento("qa.operator.broiler", bro2, "cull_recording", 14, "bro2-cull-1", cull_cause_id=cull(1), bird_movements=[aves("mixed", 20, 600.0)])
    await b.evento("qa.operator.broiler", bro2, "medication", 10, "bro2-med-1", medication_id=med(1), dosage_per_bird=0.3, treatment_days=4)
    await b.evento("qa.operator.broiler", bro2, "vaccination", 21, "bro2-vac-1", vaccine_id=vac(2), vaccination_route="water", vaccine_lot_number="QA-VL-022")
    await b.evento("qa.operator.broiler", bro2, "bird_transfer", 12, "bro2-transfer-1",
                   bird_movements=[aves("mixed", 300, 900.0, source_house_id=bro2.house_id, target_house_id=ctx.houses["QA-EN-01-G3"].id)])
    # Reverso efectivo (OC-4 "con histórico de reverso"): la recepción extra de 500 aves.
    await b.reversar(rec_extra, solicitante="qa.supervisor", motivo=f"{MARKER}: recepción duplicada por error de digitación (500 aves)", aprobar_con="qa.approver")

    bro3 = await b.lote("QA-BRO-003", empresa="MAIN", bu="broiler", farm="QA-EN-02", house="QA-EN-02-G3", line="QA-LINE-BRO", start_days=42, area="QA-AREA-ENG", planned_close_days=3)
    await b.fase_de_lote(bro3, "ENGORDE", 42, 0, 0)
    await b.evento("qa.operator.broiler", bro3, "bird_reception", 42, "bro3-recepcion", transport_id=tr(2), bird_movements=[aves("mixed", 15000, 42.0, target_house_id=bro3.house_id)])
    await b.evento("qa.operator.broiler", bro3, "bird_distribution", 42, "bro3-distrib", bird_movements=[aves("mixed", 15000, target_house_id=bro3.house_id)])
    for i, dias in enumerate((35, 28, 21, 14, 7, 1), start=1):
        await b.evento("qa.operator.broiler", bro3, "feed_registration", dias, f"bro3-feed-{i}", feed_movements=[{"feed_type_id": feed(2 if i < 4 else 3), "quantity_kg": 4000 + i * 1800, "sacks_count": 0}])
        await b.evento("qa.operator.broiler", bro3, "water_consumption", dias, f"bro3-agua-{i}", water_liters=8000 + i * 3000)
        await b.evento("qa.operator.broiler", bro3, "weight_recording", dias, f"bro3-peso-{i}", bird_movements=[aves("mixed", 50, [400, 850, 1400, 1950, 2500, 2900][i - 1], week_number=i)])
        await b.evento("qa.operator.broiler", bro3, "mortality_recording", dias, f"bro3-mort-{i}", cause_id=mort(3 if i == 4 else 1), bird_movements=[aves("mixed", 600 if i == 4 else 60 - i * 5, 1200.0)])
    await b.evento("qa.operator.broiler", bro3, "cull_recording", 21, "bro3-cull-1", cull_cause_id=cull(2), bird_movements=[aves("mixed", 45, 1300.0)])
    await b.evento("qa.operator.broiler", bro3, "bird_exit", 2, "bro3-salida-parcial", destination_plant_id=planta_benef, transport_id=tr(3), bird_movements=[aves("mixed", 3000, 2950.0)])
    await b.notificar(empresa="MAIN", destinatario="qa.operator.broiler", tipo="lot_near_close", leida=False, ocurrencia=f"near-close:{bro3.lot_code}",
                      payload={"lot_id": bro3.id, "lot_code": bro3.lot_code, "planned_close_date": D(-3).isoformat()}, entidad="lot", entidad_id=bro3.id)

    bro_closed = await b.lote("QA-BRO-CLOSED-001", empresa="MAIN", bu="broiler", farm="QA-EN-02", house="QA-EN-02-G1", line="QA-LINE-BRO", start_days=80, area="QA-AREA-ENG")
    await b.fase_de_lote(bro_closed, "ENGORDE", 80, 0, 0)
    await b.evento("qa.operator.broiler", bro_closed, "bird_reception", 80, "broc-recepcion", transport_id=tr(1), bird_movements=[aves("mixed", 9000, 42.0, target_house_id=bro_closed.house_id)])
    muertas = 0
    for i, dias in enumerate((75, 68, 61, 54, 47), start=1):
        await b.evento("qa.operator.broiler", bro_closed, "feed_registration", dias, f"broc-feed-{i}", feed_movements=[{"feed_type_id": feed(2), "quantity_kg": 3000 + i * 1500, "sacks_count": 0}])
        await b.evento("qa.operator.broiler", bro_closed, "weight_recording", dias, f"broc-peso-{i}", bird_movements=[aves("mixed", 50, [450, 900, 1450, 2000, 2550][i - 1], week_number=i)])
        await b.evento("qa.operator.broiler", bro_closed, "mortality_recording", dias, f"broc-mort-{i}", cause_id=mort(1), bird_movements=[aves("mixed", 50, 1200.0)])
        muertas += 50
    await b.evento("qa.operator.broiler", bro_closed, "bird_exit", 44, "broc-salida", destination_plant_id=planta_benef, transport_id=tr(3), bird_movements=[aves("mixed", 9000 - muertas, 2600.0)])
    await b.evento("qa.operator.broiler", bro_closed, "lot_closure", 44, "broc-cierre")
    await b.cerrar_lote(bro_closed, 44)

    # ── WORKFLOW (servicios reales; estados deliberadamente distribuidos) ──
    w = {}
    w["gp-draft"] = await b.evento("qa.operator.gp", gp_cria, "feed_registration", 1, "wf-gp-draft", aprobar=False, feed_movements=[{"feed_type_id": feed(2), "quantity_kg": 3600, "sacks_count": 90}])
    w["gp-returned"] = await b.evento("qa.operator.gp", gp_cria, "mortality_recording", 2, "wf-gp-returned", aprobar=False, cause_id=mort(1), bird_movements=[aves("female", 4, 700.0)])
    w["gp-registered"] = await b.evento("qa.operator.gp", gp_prod, "feed_registration", 1, "wf-gp-registered", aprobar=False, feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 9700, "sacks_count": 0}])
    w["gp-pending"] = await b.evento("qa.operator.gp", gp_prod, "egg_collection", 1, "wf-gp-pending", aprobar=False, egg_movements=[{"egg_type": "fertile", "quantity": 5400}, {"egg_type": "dirty", "quantity": 120}])
    w["br-draft"] = await b.evento("qa.operator.breeder", br_cria, "water_consumption", 1, "wf-br-draft", aprobar=False, water_liters=6500)
    w["br-returned"] = await b.evento("qa.operator.breeder", br_cria, "feed_registration", 2, "wf-br-returned", aprobar=False, feed_movements=[{"feed_type_id": feed(2), "quantity_kg": 3700, "sacks_count": 92}])
    w["br-registered"] = await b.evento("qa.operator.breeder", br_prod2, "mortality_recording", 1, "wf-br-registered", aprobar=False, cause_id=mort(2), bird_movements=[aves("female", 7, 3250.0)])
    w["br-inreview"] = await b.evento("qa.operator.breeder", br_prod1, "weight_recording", 1, "wf-br-inreview", aprobar=False, bird_movements=[aves("female", 30, 3350, week_number=40)])
    w["br-corrected-approve"] = await b.evento("qa.operator.breeder", br_prod1, "feed_registration", 1, "wf-br-corrected-1", aprobar=False, feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 11100, "sacks_count": 0}])
    w["br-corrected-reject"] = await b.evento("qa.operator.breeder", br_prod2, "feed_registration", 1, "wf-br-corrected-2", aprobar=False, feed_movements=[{"feed_type_id": feed(4), "quantity_kg": 8900, "sacks_count": 0}])
    w["bro-returned"] = await b.evento("qa.operator.broiler", bro2, "weight_recording", 1, "wf-bro-returned", aprobar=False, bird_movements=[aves("mixed", 50, 1700.0, week_number=4)])
    w["bro-registered"] = await b.evento("qa.operator.broiler", bro1, "feed_registration", 1, "wf-bro-registered", aprobar=False, feed_movements=[{"feed_type_id": feed(1), "quantity_kg": 560, "sacks_count": 14}])
    w["bro-pending"] = await b.evento("qa.operator.broiler", bro3, "mortality_recording", 1, "wf-bro-pending", aprobar=False, cause_id=mort(1), bird_movements=[aves("mixed", 18, 2900.0)])
    w["bro-inreview"] = await b.evento("qa.operator.broiler", bro2, "water_consumption", 1, "wf-bro-inreview", aprobar=False, water_liters=16000)
    w["bro-batch-1"] = await b.evento("qa.operator.broiler", bro3, "feed_registration", 2, "wf-bro-batch-1", aprobar=False, feed_movements=[{"feed_type_id": feed(3), "quantity_kg": 13500, "sacks_count": 0}])
    w["bro-batch-2"] = await b.evento("qa.operator.broiler", bro3, "water_consumption", 2, "wf-bro-batch-2", aprobar=False, water_liters=26000)
    w["bro-batch-3"] = await b.evento("qa.operator.broiler", bro2, "mortality_recording", 2, "wf-bro-batch-3", aprobar=False, cause_id=mort(2), bird_movements=[aves("mixed", 15, 1600.0)])
    w["bro-full-approved"] = await b.evento("qa.operator.broiler", bro2, "cull_recording", 3, "wf-bro-approved-full", aprobar=False, cull_cause_id=cull(3), bird_movements=[aves("mixed", 8, 1500.0)])
    w["bro-rejected"] = await b.evento("qa.operator.broiler", bro1, "mortality_recording", 2, "wf-bro-rejected", aprobar=False, cause_id=mort(1), bird_movements=[aves("mixed", 9, 70.0)])
    w["bro-cancelled"] = await b.evento("qa.operator.broiler", bro1, "water_consumption", 2, "wf-bro-cancelled", aprobar=False, water_liters=900)
    w["hat-draft"] = await b.evento("qa.operator.hatchery", ctx.lots["QA-HAT-REC-001"], "egg_reception_classification", 1, "wf-hat-draft", aprobar=False, egg_movements=[{"egg_type": "fertile", "quantity": 29000}])
    w["hat-pending"] = await b.evento("qa.operator.hatchery", ctx.lots["QA-HAT-INC-001"], "ovoscopy", 1, "wf-hat-pending", aprobar=False, egg_movements=[{"egg_type": "infertile", "quantity": 900}])
    w["br14-approver-corrected"] = await b.evento("qa.operator.breeder", br_prod1, "mortality_recording", 2, "wf-br14", aprobar=False, cause_id=mort(1), bird_movements=[aves("female", 11, 3300.0)])
    w["sup-corrected"] = await b.evento("qa.operator.gp", gp_prod, "mortality_recording", 2, "wf-sup-corrected", aprobar=False, cause_id=mort(2), bird_movements=[aves("female", 13, 3400.0)])

    await b.flujo(w["gp-draft"], "draft", operador="qa.operator.gp")
    await b.flujo(w["br-draft"], "draft", operador="qa.operator.breeder")
    await b.flujo(w["hat-draft"], "draft", operador="qa.operator.hatchery")
    await b.flujo(w["gp-returned"], "returned", operador="qa.operator.gp", observacion=f"{MARKER}: indique la causa de mortalidad y el galpón")
    await b.flujo(w["br-returned"], "returned", operador="qa.operator.breeder", observacion=f"{MARKER}: la cantidad de sacos no coincide con los kg")
    await b.flujo(w["bro-returned"], "returned", operador="qa.operator.broiler", observacion=f"{MARKER}: el peso promedio parece fuera de curva; verifique la muestra")
    await b.flujo(w["gp-pending"], "pending_review", operador="qa.operator.gp")
    await b.flujo(w["bro-pending"], "pending_review", operador="qa.operator.broiler")
    await b.flujo(w["hat-pending"], "pending_review", operador="qa.operator.hatchery")
    await b.flujo(w["br-inreview"], "in_review", operador="qa.operator.breeder")
    await b.flujo(w["bro-inreview"], "in_review", operador="qa.operator.broiler")
    for clave in ("br-corrected-approve", "br-corrected-reject", "bro-batch-1", "bro-batch-2", "bro-batch-3"):
        await b.flujo(w[clave], "corrected", operador="qa.operator.breeder" if clave.startswith("br-") else "qa.operator.broiler")
    await b.flujo(w["bro-full-approved"], "approved", operador="qa.operator.broiler", observacion=f"{MARKER}: flujo completo operador → supervisor → aprobador")
    await b.flujo(w["bro-rejected"], "rejected", operador="qa.operator.broiler", observacion=f"{MARKER}: la mortalidad declarada no coincide con el parte diario")
    await b.corregir(w["br14-approver-corrected"], corrector="qa.approver", campo="observations", valor=f"[{MARKER}] corregido por el aprobador (caso BR-14)",
                     motivo=f"{MARKER}: ajuste de observación para demostrar que quien corrige no aprueba (BR-14)")
    await b.corregir(w["sup-corrected"], corrector="qa.supervisor", campo="observations", valor=f"[{MARKER}] observación corregida por supervisión",
                     motivo=f"{MARKER}: corrección formal con antes/después para auditoría")
    if w["bro-cancelled"].status.value == "registered":
        from app.operations.service import OperationsService
        await OperationsService(b.db, b.actor("qa.operator.broiler", m)).cancel_event(w["bro-cancelled"].id)
    # Consolidación interna (pre-SAP) de la historia de alimento del lote cerrado: estado CONSOLIDATED.
    from app.integrations.sap.service import SapService
    consolidados = await SapService(b.db, b.actor("qa.sap", m)).consolidate_approved(lot_id=bro_closed.id, event_type="feed_registration")
    if consolidados:
        b.c.marcar("consolidated_movements", "created")

    # ── EMPRESA DE AISLAMIENTO ─────────────────────────────────────────────
    iso = ctx.companies["ISO"]
    iso_br = await b.lote("QA-ISO-BR-001", empresa="ISO", bu="breeder", farm="QA-ISO-F1", house="QA-ISO-F1-G1", line=None, start_days=150, area="QA-ISO-AREA")
    await b.apertura_manual(iso_br, fase="PROD", machos=300, hembras=2700, edad=150, mort_m=10, mort_f=80, feed_kg=42000, peso_g=3200, huevos=60000, a_incubadora=50000, actor="qa.isolation")
    await b.fase_de_lote(iso_br, "PROD", 30, 300, 2700)
    await b.evento("qa.isolation.operator", iso_br, "egg_collection", 2, "iso-br-huevos-1", egg_movements=[{"egg_type": "fertile", "quantity": 2100}])
    iso_bro = await b.lote("QA-ISO-BRO-001", empresa="ISO", bu="broiler", farm="QA-ISO-F1", house="QA-ISO-F1-G2", line=None, start_days=20, area="QA-ISO-AREA")
    await b.fase_de_lote(iso_bro, "ENGORDE", 20, 0, 0)
    await b.evento("qa.isolation.operator", iso_bro, "bird_reception", 20, "iso-bro-recepcion", sap_document_ref="QA-ISO-OC-001", bird_movements=[aves("mixed", 4000, 42.0, target_house_id=iso_bro.house_id)])
    await b.evento("qa.isolation.operator", iso_bro, "feed_registration", 13, "iso-bro-feed-1", feed_movements=[{"feed_type_id": cat[f"feed:{iso.id}:1"].id, "quantity_kg": 1200, "sacks_count": 30}])
    await b.evento("qa.isolation.operator", iso_bro, "mortality_recording", 13, "iso-bro-mort-1", cause_id=cat[f"mortality_cause:{iso.id}:1"].id, bird_movements=[aves("mixed", 12, 500.0)])
    w["iso-registered"] = await b.evento("qa.isolation.operator", iso_bro, "feed_registration", 1, "iso-bro-wf-registered", aprobar=False, feed_movements=[{"feed_type_id": cat[f"feed:{iso.id}:1"].id, "quantity_kg": 1500, "sacks_count": 38}])

    # ── CARGAS INICIALES aplicadas (SPEC 006) — una por BU, con UNKNOWN deliberado ──
    comun = dict(farm_code="QA-GP-01", house_name="QA-GP-01-G3", real_start_date=D(190).isoformat(), genetic_line_code="QA-LINE-GP", source_system=MARKER, source_reference=ctx.run_id)
    await b.cutover_aplicado("grandparent", [{**comun, "legacy_lot_code": "QA-CUT-GP-001", "productive_phase_code": "PROD", "phase_start_date": D(50).isoformat(),
                                             "live_males": 500, "live_females": 4500, "historical_mortality_males": 30, "historical_mortality_females": 250,
                                             "historical_culls_males": 0, "historical_culls_females": 0, "accumulated_feed_kg": None, "current_avg_weight_g": 3350,
                                             "accumulated_egg_production": 60000, "accumulated_eggs_to_hatchery": 52000, "notes": "alimento acumulado desconocido (UNKNOWN deliberado)"}])
    await b.cutover_aplicado("breeder", [{"legacy_lot_code": "QA-CUT-BR-001", "farm_code": "QA-BR-01", "house_name": "QA-BR-01-G1", "productive_phase_code": "CRIA",
                                         "real_start_date": D(70).isoformat(), "genetic_line_code": "QA-LINE-BR", "live_males": 450, "live_females": 4050,
                                         "historical_mortality_males": 20, "historical_mortality_females": 150, "historical_culls_males": 0, "historical_culls_females": 0,
                                         "accumulated_feed_kg": 42000, "current_avg_weight_g": 1100, "accumulated_egg_production": "N/A", "accumulated_eggs_to_hatchery": "N/A",
                                         "source_system": MARKER, "source_reference": ctx.run_id}])
    await b.cutover_aplicado("hatchery", [{"legacy_lot_code": "QA-CUT-HAT-001", "hatchery_code": "QA-INC-01", "incubator_name": "QA Incubadora A3", "hatcher_name": "QA Nacedora N2",
                                          "generation": "breeder", "reception_date": D(18).isoformat(), "set_date": D(17).isoformat(), "expected_hatch_date": D(-4).isoformat(),
                                          "eggs_received": 8000, "eggs_set": 7000, "eggs_transferred": 0, "eggs_discarded": None, "chicks_hatched": 0, "chicks_available": 0,
                                          "source_system": MARKER, "source_reference": ctx.run_id, "notes": "descartados desconocidos (UNKNOWN deliberado)"}])
    await b.cutover_aplicado("broiler", [{"legacy_lot_code": "QA-CUT-BRO-001", "farm_code": "QA-EN-02", "house_name": "QA-EN-02-G2", "productive_phase_code": "ENGORDE",
                                         "real_start_date": D(30).isoformat(), "genetic_line_code": "QA-LINE-BRO", "live_birds": 6000, "age_days": 20,
                                         "accumulated_birds_received": 6300, "historical_mortality": 220, "historical_culls": 80, "partial_outbound_birds": 0,
                                         "accumulated_feed_kg": None, "current_avg_weight_g": 900, "source_system": MARKER, "source_reference": ctx.run_id,
                                         "notes": "alimento acumulado desconocido (UNKNOWN deliberado)"}])


def fixtures_cutover(ctx: Contexto, directorio: Path) -> list[Path]:
    """Plantillas QA listas para que la persona QA ejecute su propio ciclo (códigos libres, empresa en blanco)."""
    directorio.mkdir(parents=True, exist_ok=True)
    rutas = []
    filas = {
        "grandparent": [{"legacy_lot_code": "QA-CUT-GP-NEW-001", "farm_code": "QA-GP-01", "house_name": "QA-GP-01-G2", "productive_phase_code": "PROD",
                         "real_start_date": D(210).isoformat(), "genetic_line_code": "QA-LINE-GP", "live_males": 400, "live_females": 3600,
                         "historical_mortality_males": 25, "historical_mortality_females": 200, "historical_culls_males": 0, "historical_culls_females": 0,
                         "accumulated_feed_kg": 95000.5, "current_avg_weight_g": 3400, "accumulated_egg_production": 55000, "accumulated_eggs_to_hatchery": 48000,
                         "source_system": "LEGACY", "source_reference": "QA-FIXTURE-GP", "notes": "fixture QA para ciclo manual"},
                        {"legacy_lot_code": "QA-CUT-GP-NEW-002", "farm_code": "QA-GP-01", "house_name": "QA-GP-01-G1", "productive_phase_code": "CRIA",
                         "real_start_date": D(60).isoformat(), "live_males": 300, "live_females": 2700, "historical_mortality_males": None, "historical_mortality_females": None,
                         "accumulated_egg_production": "N/A", "accumulated_eggs_to_hatchery": "N/A", "source_system": "LEGACY", "notes": "mortalidad histórica desconocida (vacío)"}],
        "breeder": [{"legacy_lot_code": "QA-CUT-BR-NEW-001", "farm_code": "QA-BR-01", "house_name": "QA-BR-01-G2", "productive_phase_code": "PROD",
                     "real_start_date": D(230).isoformat(), "genetic_line_code": "QA-LINE-BR", "live_males": 700, "live_females": 6300,
                     "historical_mortality_males": 50, "historical_mortality_females": 350, "historical_culls_males": 10, "historical_culls_females": 20,
                     "accumulated_feed_kg": 118000, "current_avg_weight_g": 3300, "accumulated_egg_production": 140000, "accumulated_eggs_to_hatchery": 120000,
                     "source_system": "LEGACY", "source_reference": "QA-FIXTURE-BR"}],
        "hatchery": [{"legacy_lot_code": "QA-CUT-HAT-NEW-001", "hatchery_code": "QA-INC-01", "incubator_name": "QA Incubadora A1", "hatcher_name": "QA Nacedora N1",
                      "generation": "breeder", "reception_date": D(12).isoformat(), "set_date": D(11).isoformat(), "expected_hatch_date": D(-10).isoformat(),
                      "eggs_received": 12000, "eggs_set": 11000, "eggs_transferred": 0, "eggs_discarded": 150, "chicks_hatched": 0, "chicks_available": 0,
                      "source_system": "LEGACY", "source_reference": "QA-FIXTURE-HAT"}],
        "broiler": [{"legacy_lot_code": "QA-CUT-BRO-NEW-001", "farm_code": "QA-EN-01", "house_name": "QA-EN-01-G3", "productive_phase_code": "ENGORDE",
                     "real_start_date": D(21).isoformat(), "genetic_line_code": "QA-LINE-BRO", "live_birds": 9000, "age_days": 21, "accumulated_birds_received": 9400,
                     "historical_mortality": 300, "historical_culls": 100, "partial_outbound_birds": 0, "accumulated_feed_kg": 12500, "current_avg_weight_g": 950,
                     "source_system": "LEGACY", "source_reference": "QA-FIXTURE-BRO"}],
    }
    for bu, rows in filas.items():
        ruta = directorio / f"QA_cutover_{bu}.xlsx"
        ruta.write_bytes(QaBuilder.xlsx_cutover(bu, rows, company_id=None, cutover=None))
        rutas.append(ruta)
    return rutas


# ── inventario / verificación / limpieza ─────────────────────────────────────

async def _empresas_qa(db: AsyncSession) -> list[Any]:
    from app.masters.models import Company
    return list((await db.execute(select(Company).where(Company.tax_id.in_([TAX_MAIN, TAX_ISO])))).scalars().all())


async def inventario(db: AsyncSession) -> dict[str, Any]:
    from app.auth.models import User
    from app.cutover.models import CutoverBatch
    from app.integrations.sap.inbound.models import SapInboundRecord
    from app.integrations.sap.models import SapReference
    from app.masters.models import Farm, Lot
    from app.operations.models import OperationalEvent

    empresas = await _empresas_qa(db)
    ids = [e.id for e in empresas]
    async def n(modelo, columna):
        if not ids:
            return 0
        return (await db.execute(select(func.count()).select_from(modelo).where(columna.in_(ids)))).scalar() or 0
    return {
        "dataset_version": VERSION, "qa_companies": [{"id": e.id, "name": e.name} for e in empresas],
        "qa_users": (await db.execute(select(func.count()).select_from(User).where(User.username.like(f"{USER_PREFIX}%")))).scalar() or 0,
        "qa_farms": await n(Farm, Farm.company_id), "qa_lots": await n(Lot, Lot.company_id),
        "qa_operations": await n(OperationalEvent, OperationalEvent.company_id),
        "qa_sap_references": await n(SapReference, SapReference.company_id),
        "qa_inbound_records": await n(SapInboundRecord, SapInboundRecord.company_id),
        "qa_cutover_batches": await n(CutoverBatch, CutoverBatch.company_id),
    }


async def verificar(db: AsyncSession) -> list[tuple[str, bool, str]]:
    from app.auth.models import User
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
    from app.cutover.models import CutoverBatch
    from app.integrations.sap.inbound.models import SapInboundRecord
    from app.integrations.sap.models import SapReference
    from app.lots.models import ChickBatch, EggBatch, OpeningBalance
    from app.masters.models import Farm, Hatcher, Hatchery, House, Incubator, Lot
    from app.operations.models import BirdMovement, EggMovement, EventStatus, FeedMovement, OperationalEvent

    r: list[tuple[str, bool, str]] = []
    empresas = {e.tax_id: e for e in await _empresas_qa(db)}
    r.append(("2 QA companies", len(empresas) == 2, ", ".join(sorted(e.name for e in empresas.values()))))
    if len(empresas) != 2:
        return r
    main, iso = empresas[TAX_MAIN], empresas[TAX_ISO]
    bus = {b.code: b.id for b in (await db.execute(select(BusinessUnit))).scalars().all()}
    cbus = {(c.company_id, c.business_unit_id): c.is_enabled for c in (await db.execute(select(CompanyBusinessUnit).where(
        CompanyBusinessUnit.company_id.in_([main.id, iso.id])))).scalars().all()}
    r.append(("4 BU primary enabled", all(cbus.get((main.id, bus[b])) for b in ALL_BU), str({b: cbus.get((main.id, bus[b])) for b in ALL_BU})))
    r.append(("isolation BU on/off", cbus.get((iso.id, bus["breeder"])) is True and cbus.get((iso.id, bus["broiler"])) is True
              and cbus.get((iso.id, bus["grandparent"])) is False and cbus.get((iso.id, bus["hatchery"])) is False,
              str({b: cbus.get((iso.id, bus[b])) for b in ALL_BU})))
    usuarios = {u.username: u for u in (await db.execute(select(User).where(User.username.like(f"{USER_PREFIX}%")))).scalars().all()}
    esperados = {u[0]: u for u in USUARIOS}
    faltan = [u for u in esperados if u not in usuarios]
    roles_ok = all(usuarios[u].role and usuarios[u].role.name == esperados[u][1] for u in esperados if u in usuarios)
    r.append(("users and roles correct", not faltan and roles_ok, f"faltan={faltan}; roles_ok={roles_ok}"))
    grants_ok = True
    detalle_grants = []
    for username, _, emp, unidades, *_ in USUARIOS:
        if username not in usuarios:
            continue
        empresa = main if emp == "MAIN" else iso
        concedidas = set((await db.execute(
            select(BusinessUnit.code).join(CompanyBusinessUnit, CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
            .join(UserBusinessUnit, UserBusinessUnit.company_business_unit_id == CompanyBusinessUnit.id)
            .where(UserBusinessUnit.user_id == usuarios[username].id, UserBusinessUnit.revoked_at.is_(None),
                   CompanyBusinessUnit.company_id == empresa.id))).scalars().all())
        if concedidas != set(unidades):
            grants_ok = False; detalle_grants.append(f"{username}: {sorted(concedidas)} ≠ {sorted(unidades)}")
    r.append(("BU grants correct", grants_ok, "; ".join(detalle_grants) or "ok"))
    r.append(("qa.mobile view_type mobile", usuarios.get("qa.mobile") is not None and usuarios["qa.mobile"].view_type == "mobile", ""))
    granjas = (await db.execute(select(Farm).where(Farm.company_id == main.id))).scalars().all()
    galpones = (await db.execute(select(func.count()).select_from(House).join(Farm, House.farm_id == Farm.id).where(Farm.company_id == main.id))).scalar() or 0
    inactivo = (await db.execute(select(func.count()).select_from(House).join(Farm, House.farm_id == Farm.id).where(Farm.company_id == main.id, House.is_active.is_(False)))).scalar() or 0
    r.append(("farms/houses valid", len(granjas) >= 4 and galpones >= 12 and inactivo >= 1, f"granjas={len(granjas)} galpones={galpones} inactivos={inactivo}"))
    plantas = (await db.execute(select(Hatchery).where(Hatchery.company_id == main.id))).scalars().all()
    incub = (await db.execute(select(func.count()).select_from(Incubator).join(Hatchery, Incubator.hatchery_id == Hatchery.id).where(Hatchery.company_id == main.id))).scalar() or 0
    nac = (await db.execute(select(func.count()).select_from(Hatcher).join(Hatchery, Hatcher.hatchery_id == Hatchery.id).where(Hatchery.company_id == main.id))).scalar() or 0
    r.append(("hatchery equipment valid", len(plantas) >= 1 and incub >= 3 and nac >= 2, f"plantas={len(plantas)} incubadoras={incub} nacedoras={nac}"))
    lotes = (await db.execute(select(Lot).where(Lot.company_id.in_([main.id, iso.id])))).scalars().all()
    r.append(("lots have company/BU", bool(lotes) and all(l.company_id and l.bird_type for l in lotes), f"lotes={len(lotes)}"))
    por_bu = {bu: sum(1 for l in lotes if l.company_id == main.id and l.bird_type.value == bu) for bu in ALL_BU}
    r.append(("lots per BU (GP≥4, BR≥4, HAT≥6, BRO≥4)", por_bu["grandparent"] >= 4 and por_bu["breeder"] >= 4 and por_bu["hatchery"] >= 6 and por_bu["broiler"] >= 4, str(por_bu)))
    eventos = (await db.execute(select(OperationalEvent).where(OperationalEvent.company_id.in_([main.id, iso.id])))).scalars().all()
    ids_ev = [e.id for e in eventos]
    con_detalle = set()
    for modelo in (BirdMovement, EggMovement, FeedMovement):
        con_detalle |= set((await db.execute(select(modelo.event_id).where(modelo.event_id.in_(ids_ev)))).scalars().all())
    tipos_con_detalle = {"bird_reception", "mortality_recording", "cull_recording", "weight_recording", "feed_registration", "egg_collection", "egg_dispatch",
                         "egg_reception_hatchery", "birth_registration", "chick_dispatch", "bird_exit", "bird_distribution"}
    sin_detalle = [e.id for e in eventos if e.event_type.value in tipos_con_detalle and e.id not in con_detalle]
    r.append(("event details exist", not sin_detalle, f"eventos={len(eventos)} sin_detalle={len(sin_detalle)}"))
    estados = {}
    for e in eventos:
        estados[e.status.value] = estados.get(e.status.value, 0) + 1
    necesarios = ("draft", "registered", "pending_review", "in_review", "returned", "corrected", "approved", "rejected", "consolidated", "reversed", "cancelled")
    r.append(("workflow states valid", all(estados.get(s, 0) >= 1 for s in necesarios) and estados.get("sent_to_sap", 0) == 0 and estados.get("sap_confirmed", 0) == 0,
              str(estados)))
    tipos = {e.event_type.value for e in eventos}
    todos = {t.value for t in OperationalEvent.event_type.type.enum_class} if hasattr(OperationalEvent.event_type.type, "enum_class") else tipos
    faltan_tipos = sorted(todos - tipos)
    r.append(("event types coverage", not faltan_tipos, f"faltan={faltan_tipos}"))
    refs = (await db.execute(select(SapReference).where(SapReference.company_id.in_([main.id, iso.id])))).scalars().all()
    no_sinteticas = [r_.sap_code for r_ in refs if not (es_codigo_qa(r_.sap_code) and (r_.extra_data or {}).get("source") == SAP_SOURCE)]
    r.append(("SAP refs company-scoped & synthetic", bool(refs) and not no_sinteticas, f"refs={len(refs)} no_sinteticas={no_sinteticas[:5]}"))
    ocs = {r_.sap_code: r_ for r_ in refs if r_.ref_type.value == "purchase_order"}
    r.append(("PO quantities coherent (BR-18 set)", all(ocs.get(c) and ocs[c].quantity for c in ("QA-OC-GP-AVES-001", "QA-OC-BR-AVES-002", "QA-OC-BRO-AVES-003", "QA-OC-BRO-AVES-004", "QA-OC-BR18-TEST")),
              ", ".join(f"{c}={int(ocs[c].quantity) if ocs.get(c) and ocs[c].quantity else None}" for c in ("QA-OC-GP-AVES-001", "QA-OC-BR-AVES-002", "QA-OC-BRO-AVES-003", "QA-OC-BRO-AVES-004", "QA-OC-BR18-TEST"))))
    inbound = (await db.execute(select(SapInboundRecord).where(SapInboundRecord.company_id.in_([main.id, iso.id])))).scalars().all()
    objetos = {i.object_type for i in inbound}
    r.append(("inbound 14 objects staged, QA_SYNTHETIC", len(objetos) == 14 and all(i.source_system == SAP_SOURCE for i in inbound), f"objetos={len(objetos)} registros={len(inbound)}"))
    ids_lotes = [l.id for l in lotes]
    eb = (await db.execute(select(func.count()).select_from(EggBatch).where(EggBatch.hatchery_lot_id.in_(ids_lotes)))).scalar() or 0
    cb = (await db.execute(select(func.count()).select_from(ChickBatch).where(ChickBatch.hatchery_lot_id.in_(ids_lotes)))).scalar() or 0
    r.append(("EggBatch/ChickBatch coherent", eb >= 6 and cb >= 2, f"egg_batches={eb} chick_batches={cb}"))
    aprobados = sum(1 for e in eventos if e.status in (EventStatus.APPROVED, EventStatus.CONSOLIDATED) and e.event_type.value in ("feed_registration", "weight_recording", "mortality_recording", "egg_collection"))
    r.append(("reports have source data", aprobados >= 100, f"aprobados_para_reportes={aprobados}"))
    openings = (await db.execute(select(OpeningBalance).where(OpeningBalance.lot_id.in_(ids_lotes)))).scalars().all()
    r.append(("UNKNOWN scenario present", any(o.feed_status == "UNKNOWN" for o in openings), f"openings={len(openings)}"))
    marcados = all((e.extra_data or {}).get("qa_marker") == MARKER or (e.observations or "").startswith(f"Reverso de") or (e.observations or "").find(MARKER) >= 0 for e in eventos)
    r.append(("QA markers present", marcados and all(l.lot_code.startswith(PREFIX) for l in lotes) and all(u.email.endswith(EMAIL_DOMAIN) for u in usuarios.values()), ""))
    cut = (await db.execute(select(CutoverBatch).where(CutoverBatch.company_id == main.id, CutoverBatch.status == "applied"))).scalars().all()
    r.append(("cutover applied per BU", {c.business_unit for c in cut} >= set(ALL_BU), f"aplicadas={[c.business_unit for c in cut]}"))
    reales = (await db.execute(select(func.count()).select_from(SapInboundRecord).where(SapInboundRecord.company_id.in_([main.id, iso.id]),
                                                                                         SapInboundRecord.source_system != SAP_SOURCE))).scalar() or 0
    r.append(("real SAP calls = 0", reales == 0, f"registros no sintéticos en empresas QA={reales}"))
    return r


async def limpiar(db: AsyncSession, *, dry_run: bool, force_unmarked: bool) -> dict[str, Any]:
    """Elimina exclusivamente `QA-DEMO-V1` en orden FK seguro. Fail-closed ante entidades sin marcador."""
    from app.audit.models import AuditLog
    from app.auth.models import RevokedToken, User
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from app.corrections.models import CorrectionLog
    from app.cutover.models import CutoverBatch, CutoverItem, CutoverStagingRow, HatcheryOpening, OpeningBalanceCorrection
    from app.integrations.sap.inbound.models import SapEntityMapping, SapInboundRecord, SapInboundSyncJob, SapInboundWatermark
    from app.integrations.sap.models import ConsolidatedMovement, SapPayload, SapReference, SapResponse, SapSyncJob
    from app.lots.models import ChickBatch, EggBatch, LotPhase, OpeningBalance
    from app.masters.models import (Area, Breed, Company, CorrectionType, CullCause, Farm, FeedType, GeneticLine, GeneticWeightCurve,
                                    GeneticWeightCurvePoint, Hatcher, Hatchery, House, Incubator, Lot, Medication, MortalityCause,
                                    ProcessingPlant, RejectionReason, Supplier, Transport, Vaccine)
    from app.notifications.models import Notification
    from app.operations.models import (BirdMovement, EggMovement, EggStorage, Evidence, FeedMovement, HatcheryParams, InspectionDetail,
                                       OperationalAlert, OperationalEvent, Reversal)
    from app.review.models import ApprovalAction, ApprovalStep, ReviewBatch

    empresas = await _empresas_qa(db)
    if not empresas:
        return {"status": "NOTHING_TO_CLEAN", "deleted": {}}
    ids = [e.id for e in empresas]
    informe: dict[str, Any] = {"companies": [e.name for e in empresas], "deleted": {}, "ambiguous": []}

    # Fail-closed: todo lo que viva en una empresa QA debe reconocerse como sintético.
    usuarios = (await db.execute(select(User).where(User.company_id.in_(ids)))).scalars().all()
    lotes = (await db.execute(select(Lot).where(Lot.company_id.in_(ids)))).scalars().all()
    refs = (await db.execute(select(SapReference).where(SapReference.company_id.in_(ids)))).scalars().all()
    for u in usuarios:
        if not u.username.startswith(USER_PREFIX):
            informe["ambiguous"].append(f"user:{u.username}")
    for l in lotes:
        if not l.lot_code.startswith(PREFIX):
            informe["ambiguous"].append(f"lot:{l.lot_code}")
    for r_ in refs:
        if not es_codigo_qa(r_.sap_code):
            informe["ambiguous"].append(f"sap_reference:{r_.sap_code}")
    if informe["ambiguous"] and not force_unmarked:
        informe["status"] = "AMBIGUOUS_QA_DATA"
        return informe

    ids_usuarios = [u.id for u in usuarios]
    ids_lotes = [l.id for l in lotes]
    ids_eventos = list((await db.execute(select(OperationalEvent.id).where(OperationalEvent.company_id.in_(ids)))).scalars().all())
    ids_openings = list((await db.execute(select(OpeningBalance.id).where(OpeningBalance.lot_id.in_(ids_lotes)))).scalars().all()) if ids_lotes else []
    ids_lineas = list((await db.execute(select(GeneticLine.id).where(GeneticLine.company_id.in_(ids)))).scalars().all())
    ids_curvas = list((await db.execute(select(GeneticWeightCurve.id).where(GeneticWeightCurve.genetic_line_id.in_(ids_lineas)))).scalars().all()) if ids_lineas else []
    ids_granjas = list((await db.execute(select(Farm.id).where(Farm.company_id.in_(ids)))).scalars().all())
    ids_plantas = list((await db.execute(select(Hatchery.id).where(Hatchery.company_id.in_(ids)))).scalars().all())
    ids_batches = list((await db.execute(select(CutoverBatch.id).where(CutoverBatch.company_id.in_(ids)))).scalars().all())
    ids_payloads = list((await db.execute(select(SapPayload.id).where(SapPayload.company_id.in_(ids)))).scalars().all())

    def cond(col, valores):
        return col.in_(valores) if valores else None

    pasos = [
        ("opening_balance_corrections", OpeningBalanceCorrection, cond(OpeningBalanceCorrection.opening_id, ids_openings)),
        ("hatchery_openings", HatcheryOpening, cond(HatcheryOpening.lot_id, ids_lotes)),
        ("chick_batches", ChickBatch, cond(ChickBatch.hatchery_lot_id, ids_lotes)),
        ("chick_batches(destino)", ChickBatch, cond(ChickBatch.destination_lot_id, ids_lotes)),
        ("egg_batches", EggBatch, cond(EggBatch.hatchery_lot_id, ids_lotes)),
        ("egg_batches(origen)", EggBatch, cond(EggBatch.source_lot_id, ids_lotes)),
        ("approval_actions", ApprovalAction, cond(ApprovalAction.event_id, ids_eventos)),
        ("correction_logs", CorrectionLog, cond(CorrectionLog.event_id, ids_eventos)),
        ("evidences", Evidence, Evidence.company_id.in_(ids)),
        ("bird_movements", BirdMovement, cond(BirdMovement.event_id, ids_eventos)),
        ("egg_movements", EggMovement, cond(EggMovement.event_id, ids_eventos)),
        ("feed_movements", FeedMovement, cond(FeedMovement.event_id, ids_eventos)),
        ("hatchery_params", HatcheryParams, cond(HatcheryParams.event_id, ids_eventos)),
        ("inspection_details", InspectionDetail, cond(InspectionDetail.event_id, ids_eventos)),
        ("egg_storage", EggStorage, cond(EggStorage.event_id, ids_eventos)),
        ("operational_alerts", OperationalAlert, OperationalAlert.company_id.in_(ids)),
        ("reversals", Reversal, Reversal.company_id.in_(ids)),
        ("consolidated_movements", ConsolidatedMovement, ConsolidatedMovement.company_id.in_(ids)),
        ("notifications", Notification, Notification.company_id.in_(ids)),
        ("sap_responses", SapResponse, cond(SapResponse.payload_id, ids_payloads)),
        ("sap_payloads", SapPayload, SapPayload.company_id.in_(ids)),
        ("audit_logs", AuditLog, AuditLog.company_id.in_(ids)),
        ("operational_events", OperationalEvent, OperationalEvent.company_id.in_(ids)),
        ("cutover_items", CutoverItem, CutoverItem.company_id.in_(ids)),
        ("cutover_staging_rows", CutoverStagingRow, cond(CutoverStagingRow.batch_id, ids_batches)),
        ("cutover_batches", CutoverBatch, CutoverBatch.company_id.in_(ids)),
        ("opening_balances", OpeningBalance, cond(OpeningBalance.lot_id, ids_lotes)),
        ("lot_phases", LotPhase, cond(LotPhase.lot_id, ids_lotes)),
        ("lots", Lot, Lot.company_id.in_(ids)),
        ("review_batches", ReviewBatch, ReviewBatch.company_id.in_(ids)),
        ("approval_steps", ApprovalStep, ApprovalStep.company_id.in_(ids)),
        ("sap_inbound_records", SapInboundRecord, SapInboundRecord.company_id.in_(ids)),
        ("sap_inbound_sync_jobs", SapInboundSyncJob, SapInboundSyncJob.company_id.in_(ids)),
        ("sap_inbound_watermarks", SapInboundWatermark, SapInboundWatermark.company_id.in_(ids)),
        ("sap_entity_mappings", SapEntityMapping, SapEntityMapping.company_id.in_(ids)),
        ("sap_references", SapReference, SapReference.company_id.in_(ids)),
        ("sap_sync_jobs", SapSyncJob, SapSyncJob.company_id.in_(ids)),
        ("genetic_weight_curve_points", GeneticWeightCurvePoint, cond(GeneticWeightCurvePoint.curve_id, ids_curvas)),
        ("genetic_weight_curves", GeneticWeightCurve, cond(GeneticWeightCurve.genetic_line_id, ids_lineas)),
        ("breeds", Breed, cond(Breed.genetic_line_id, ids_lineas)),
        ("genetic_lines", GeneticLine, GeneticLine.company_id.in_(ids)),
        ("houses", House, cond(House.farm_id, ids_granjas)),
        ("farms", Farm, Farm.company_id.in_(ids)),
        ("incubators", Incubator, cond(Incubator.hatchery_id, ids_plantas)),
        ("hatchers", Hatcher, cond(Hatcher.hatchery_id, ids_plantas)),
        ("hatcheries", Hatchery, Hatchery.company_id.in_(ids)),
        ("suppliers", Supplier, Supplier.company_id.in_(ids)), ("feed_types", FeedType, FeedType.company_id.in_(ids)),
        ("vaccines", Vaccine, Vaccine.company_id.in_(ids)), ("medications", Medication, Medication.company_id.in_(ids)),
        ("mortality_causes", MortalityCause, MortalityCause.company_id.in_(ids)), ("cull_causes", CullCause, CullCause.company_id.in_(ids)),
        ("transports", Transport, Transport.company_id.in_(ids)), ("processing_plants", ProcessingPlant, ProcessingPlant.company_id.in_(ids)),
        ("rejection_reasons", RejectionReason, RejectionReason.company_id.in_(ids)), ("correction_types", CorrectionType, CorrectionType.company_id.in_(ids)),
        ("user_business_units", UserBusinessUnit, cond(UserBusinessUnit.user_id, ids_usuarios)),
        ("company_business_units", CompanyBusinessUnit, CompanyBusinessUnit.company_id.in_(ids)),
        ("revoked_tokens", RevokedToken, cond(RevokedToken.user_id, ids_usuarios)),
        ("users", User, User.company_id.in_(ids)),
        ("areas", Area, Area.company_id.in_(ids)),
        ("companies", Company, Company.id.in_(ids)),
    ]
    # Orden FK seguro derivado del propio metadata (dependientes primero); estable para pasos de una misma tabla.
    from app.database import Base
    orden = {t.name: i for i, t in enumerate(reversed(Base.metadata.sorted_tables))}
    pasos.sort(key=lambda p: orden[p[1].__tablename__])
    for nombre, modelo, condicion in pasos:
        if condicion is None:
            informe["deleted"][nombre] = 0; continue
        cuenta = (await db.execute(select(func.count()).select_from(modelo).where(condicion))).scalar() or 0
        if not dry_run and cuenta:
            await db.execute(delete(modelo).where(condicion))
        informe["deleted"][nombre] = int(cuenta)
    if not dry_run:
        await db.commit()
    informe["status"] = "DRY_RUN" if dry_run else "CLEANED"
    informe["total"] = sum(informe["deleted"].values())
    return informe


# ── apply ────────────────────────────────────────────────────────────────────

async def aplicar(db: AsyncSession, *, run_id: str, creds: dict[str, str], reset_passwords: bool, fixtures_dir: Optional[Path]) -> Contexto:
    ctx = Contexto(run_id=run_id, creds=creds, reset_passwords=reset_passwords)
    b = QaBuilder(db, ctx)
    fases = (("empresas", b.empresas), ("roles", b.roles), ("usuarios", b.usuarios), ("unidades", b.unidades), ("fases", b.fases),
             ("maestros_principal", b.maestros_principal), ("maestros_aislamiento", b.maestros_aislamiento),
             ("pasos_de_aprobacion", b.pasos_de_aprobacion), ("sap_sintetico", b.sap_sintetico))
    for nombre, fase in fases:
        await fase()
        await db.commit()
        print(f"[qa-seed] fase {nombre}: ok")
    await escenarios(b)
    await db.commit()
    print("[qa-seed] fase escenarios: ok")
    if fixtures_dir is not None:
        rutas = fixtures_cutover(ctx, fixtures_dir)
        print(f"[qa-seed] fixtures de cargas iniciales: {len(rutas)} archivos en {fixtures_dir}")
    return ctx


def imprimir_contadores(ctx: Contexto) -> None:
    c = ctx.contadores
    print(f"\nCREATED = {c.created}\nEXISTING = {c.existing}\nUPDATED = {c.updated}\nSKIPPED = {c.skipped}")
    for entidad, d in sorted(c.detalle.items()):
        print(f"  {entidad:<28} created={d['created']:<4} existing={d['existing']:<4} updated={d['updated']:<3} skipped={d['skipped']}")


async def main_async(args) -> int:
    if args.inventory:
        exigir_entorno_seguro(escribe=False, confirm_target=None)
        async with async_session() as db:
            print(json.dumps(await inventario(db), indent=2, ensure_ascii=False))
        return 0
    if args.verify:
        exigir_entorno_seguro(escribe=False, confirm_target=None)
        async with async_session() as db:
            resultados = await verificar(db)
        ok = True
        for nombre, paso, detalle in resultados:
            ok &= paso
            print(f"  [{'PASS' if paso else 'FAIL'}] {nombre}  {detalle}")
        print(f"\nQA_DATA_VERIFY = {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    if args.cleanup:
        exigir_entorno_seguro(escribe=not args.dry_run, confirm_target=args.confirm_target)
        async with async_session() as db:
            informe = await limpiar(db, dry_run=args.dry_run, force_unmarked=args.force_unmarked)
        print(json.dumps(informe, indent=2, ensure_ascii=False))
        return 0 if informe.get("status") in ("DRY_RUN", "CLEANED", "NOTHING_TO_CLEAN") else 2
    if args.apply:
        exigir_entorno_seguro(escribe=not args.dry_run, confirm_target=args.confirm_target)
        if args.dry_run:
            async with async_session() as db:
                print("[qa-seed] --apply --dry-run: sin escrituras; inventario actual:")
                print(json.dumps(await inventario(db), indent=2, ensure_ascii=False))
            return 0
        creds = credenciales(Path(args.credentials_file), usuarios=tuple(u[0] for u in USUARIOS))
        run_id = args.run_id or f"{VERSION}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        async with async_session() as db:
            ctx = await aplicar(db, run_id=run_id, creds=creds, reset_passwords=args.reset_passwords,
                                fixtures_dir=Path(args.fixtures_dir) if args.fixtures_dir else None)
        imprimir_contadores(ctx)
        if args.manifest:
            async with async_session() as db:
                inv = await inventario(db)
            manifiesto = {"dataset_version": VERSION, "marker": MARKER, "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
                          "sha": sha_actual(), "prefixes": {"codes": PREFIX, "users": USER_PREFIX, "sap_source": SAP_SOURCE},
                          "companies": [COMPANY_MAIN, COMPANY_ISO], "users": [u[0] for u in USUARIOS], "inventory": inv,
                          "counters": {"created": ctx.contadores.created, "existing": ctx.contadores.existing, "updated": ctx.contadores.updated,
                                       "detail": ctx.contadores.detalle}, "lots": sorted(ctx.lots), "sap_refs": sorted(ctx.sap_refs)}
            Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
            Path(args.manifest).write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False))
            print(f"[qa-seed] manifest: {args.manifest}")
        return 0
    return 1


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--inventory", action="store_true"); g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true"); g.add_argument("--cleanup", action="store_true")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--run-id"); p.add_argument("--confirm-target")
    p.add_argument("--fixtures-dir", default=str(FIXTURES_POR_DEFECTO)); p.add_argument("--credentials-file", default=str(CREDENCIALES_POR_DEFECTO))
    p.add_argument("--reset-passwords", action="store_true"); p.add_argument("--force-unmarked", action="store_true")
    p.add_argument("--manifest", help="ruta del manifest JSON a escribir tras --apply")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
