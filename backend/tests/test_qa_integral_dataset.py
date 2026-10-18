"""SPEC 007 · guardas del seed canónico `QA-DEMO-V1` (`seeds/qa_integral_dataset.py`).

Lo que se prueba aquí es lo que **no** puede depender de una corrida completa: entorno
prohibido, confirmación de destino, ausencia de secretos en el código, marcadores de
trazabilidad y el fail-closed del cleanup ante datos no marcados. El ciclo completo
CREATE → VERIFY → CLEAN → RECREATE se ejecuta en la base aislada del arnés y queda en
`audit/qa-integral-dataset/06…07`.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from seeds import qa_integral_builders as b
from seeds import qa_integral_dataset as ds

SEEDS = Path(__file__).resolve().parents[1] / "seeds"
FUENTES = (SEEDS / "qa_integral_dataset.py", SEEDS / "qa_integral_builders.py")


# ── sin secretos ni datos reales ─────────────────────────────────────────────

def test_sin_contrasenas_literales_en_el_seed():
    patron = re.compile(r"(password|contrase[nñ]a|pwd)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE)
    ofensas = []
    for ruta in FUENTES:
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if linea.lstrip().startswith("#"):
                continue
            if patron.search(linea) and "hash_password(" not in linea and "environ" not in linea:
                ofensas.append(f"{ruta.name}:{n}: {linea.strip()}")
    assert not ofensas, "contraseñas literales en el seed:\n" + "\n".join(ofensas)


def test_sin_dsn_ni_hosts_reales_en_el_seed():
    texto = "\n".join(r.read_text(encoding="utf-8") for r in FUENTES)
    assert "postgresql+asyncpg://" not in texto.replace("postgresql+asyncpg://user", "")
    assert not re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", texto), "IP literal en el seed"
    assert '"SAP_HANA_CLOUD"' not in texto and "'SAP_HANA_CLOUD'" not in texto, \
        "el seed no debe presentar datos como provenientes de SAP real (solo puede citarlo en documentación)"


def test_marcadores_de_trazabilidad():
    assert b.VERSION == "QA-DEMO-V1" and b.MARKER == "QA_DEMO_V1"
    assert b.PREFIX == "QA-" and b.USER_PREFIX == "qa." and b.SAP_SOURCE == "QA_SYNTHETIC"
    assert all(u[0].startswith(b.USER_PREFIX) for u in b.USUARIOS)
    assert len({u[0] for u in b.USUARIOS}) == len(b.USUARIOS) == 12
    assert not b.EMAIL_DOMAIN.endswith((".local", ".test", ".example", ".invalid"))
    assert b.COMPANY_MAIN.startswith("QA ") and b.COMPANY_ISO.startswith("QA ")


def test_es_codigo_qa():
    assert ds.es_codigo_qa("QA-OC-GP-AVES-001") and ds.es_codigo_qa("QAP1") and ds.es_codigo_qa("QAP1-0001")
    assert not ds.es_codigo_qa("4500000123") and not ds.es_codigo_qa("P100") and not ds.es_codigo_qa("LOTE-REAL")


# ── guarda de entorno y confirmación de destino ──────────────────────────────

@pytest.mark.parametrize("entorno", sorted(ds.FORBIDDEN_ENVIRONMENTS))
def test_entorno_prohibido_aborta_antes_de_conectar(entorno, monkeypatch):
    monkeypatch.setattr(ds.settings, "ENVIRONMENT", entorno)
    with pytest.raises(SystemExit) as exc:
        ds.exigir_entorno_seguro(escribe=False, confirm_target=None)
    assert "ABORTADO" in str(exc.value)


def test_escritura_sin_confirm_target_aborta(monkeypatch):
    monkeypatch.setattr(ds.settings, "ENVIRONMENT", "test")
    # `R1`: ya no existe el fallback por entorno; la variable —aunque tenga la base correcta— no autoriza nada.
    monkeypatch.setenv("GA_QA_SEED_CONFIRM_TARGET", ds.destino_configurado()[1])
    with pytest.raises(SystemExit) as exc:
        ds.exigir_entorno_seguro(escribe=True, confirm_target=None)
    assert "confirm-target" in str(exc.value)
    with pytest.raises(SystemExit):
        ds.exigir_entorno_seguro(escribe=True, confirm_target="otra_base")


@pytest.mark.parametrize("entorno", ["produccion", "prd", "live", "stg", "staging2", "pre-eu", "desconocido"])
def test_entorno_fuera_de_allowlist_aborta(entorno, monkeypatch):
    """`R1`: la lista blanca manda — lo que no está permitido aborta aunque no figure en la lista negra."""
    monkeypatch.setattr(ds.settings, "ENVIRONMENT", entorno)
    assert entorno not in ds.ENTORNOS_PERMITIDOS
    with pytest.raises(SystemExit) as exc:
        ds.exigir_entorno_seguro(escribe=False, confirm_target=None)
    assert "ABORTADO" in str(exc.value)


def test_escritura_con_confirm_target_correcto_pasa(monkeypatch):
    monkeypatch.setattr(ds.settings, "ENVIRONMENT", "test")
    _, base = ds.destino_configurado()
    ds.exigir_entorno_seguro(escribe=True, confirm_target=base)  # no lanza


def test_lectura_no_exige_confirmacion(monkeypatch):
    monkeypatch.setattr(ds.settings, "ENVIRONMENT", "development")
    ds.exigir_entorno_seguro(escribe=False, confirm_target=None)


# ── credenciales fuera del repositorio ───────────────────────────────────────

def test_credenciales_desde_env_o_archivo_0600(tmp_path, monkeypatch):
    ruta = tmp_path / "creds.json"
    monkeypatch.setenv("GA_QA_SEED_PASSWORD", "clave-de-prueba-env")
    creds = ds.credenciales(ruta, usuarios=("qa.a", "qa.b"))
    assert creds == {"qa.a": "clave-de-prueba-env", "qa.b": "clave-de-prueba-env"}
    assert not ruta.exists()

    monkeypatch.delenv("GA_QA_SEED_PASSWORD")
    creds = ds.credenciales(ruta, usuarios=("qa.a", "qa.b"))
    assert ruta.exists() and oct(ruta.stat().st_mode & 0o777) == "0o600"
    assert len(set(creds.values())) == 1 and len(creds["qa.a"]) >= 16
    # Una segunda lectura reutiliza el archivo y completa usuarios nuevos sin cambiar los existentes.
    otra = ds.credenciales(ruta, usuarios=("qa.a", "qa.b", "qa.c"))
    assert otra["qa.a"] == creds["qa.a"] and otra["qa.c"] == creds["qa.a"]


# ── cleanup: acotado y fail-closed ───────────────────────────────────────────

def _modelos_del_plan(texto: str) -> set[str]:
    """Modelos del plan `pasos` de `limpiar()` extraídos con `ast`.

    La regex anterior (`\\("[a-z_()]+", ([A-Za-z]+), `) dependía del formato exacto de la línea; con
    `ast` los pasos complementarios (`"hatchery_openings(planta)"`, `"roles"`…) se leen igual y el
    plan puede reordenarse o reformatearse sin que la guarda se vuelva ciega.
    """
    arbol = ast.parse(texto)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.AsyncFunctionDef, ast.FunctionDef)) and nodo.name == "limpiar":
            for interno in ast.walk(nodo):
                if isinstance(interno, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pasos" for t in interno.targets):
                    return {paso.elts[1].id for paso in interno.value.elts
                            if isinstance(paso, ast.Tuple) and len(paso.elts) >= 3 and isinstance(paso.elts[1], ast.Name)}
    raise AssertionError("no se encontró el plan `pasos` dentro de limpiar()")


def test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra():
    """Toda tabla con FK hacia una tabla del plan de limpieza debe estar en el plan (si no, el DELETE rompería)."""
    import app.main  # noqa: F401 — registra todos los modelos
    from app.database import Base

    texto = (SEEDS / "qa_integral_dataset.py").read_text(encoding="utf-8")
    modelos = _modelos_del_plan(texto)
    assert {"HatcheryOpening", "UserBusinessUnit", "AuditLog"} <= modelos, f"pasos ausentes del plan: {sorted(modelos)}"
    tablas = {mp.class_.__tablename__ for mp in Base.registry.mappers if mp.class_.__name__ in modelos}
    faltan = sorted(t.name for t in Base.metadata.sorted_tables
                    if t.name not in tablas and any(fk.column.table.name in tablas for fk in t.foreign_keys))
    assert not faltan, f"tablas referenciando al plan de limpieza sin estar en él: {faltan}"


@pytest.mark.asyncio
async def test_cleanup_fail_closed_ante_datos_no_marcados():
    """Una empresa QA con un lote sin prefijo `QA-` ⇒ AMBIGUOUS_QA_DATA y ningún borrado (dry-run y real)."""
    from app.database import async_session
    from app.masters.models import Company

    async with async_session() as db:
        if await db.scalar(select(Company).where(Company.tax_id == b.TAX_MAIN)):
            pytest.skip("el dataset QA ya está presente en esta base; la prueba exige una base sin él")
        empresa = Company(name=b.COMPANY_MAIN, tax_id=b.TAX_MAIN, country="Venezuela", currency="USD", approval_levels=1, is_active=True)
        db.add(empresa)
        await db.flush()
        from app.masters.models import Lot, BirdTypeEnum, SexEnum, LotStatus
        from app.masters.models import Farm, FarmType, House, HouseType
        granja = Farm(company_id=empresa.id, code="QA-TMP-F", name="QA tmp", location="x", farm_type=FarmType.FATTENING, is_active=True)
        db.add(granja); await db.flush()
        galpon = House(farm_id=granja.id, name="QA-TMP-G1", capacity=1000, house_type=HouseType.OPEN, is_active=True)
        db.add(galpon); await db.flush()
        from datetime import datetime, timezone
        lote = Lot(company_id=empresa.id, farm_id=granja.id, house_id=galpon.id, lot_code="LOTE-REAL-SIN-MARCA",
                   bird_type=BirdTypeEnum.BROILER, sex=SexEnum.MIXED, status=LotStatus.ACTIVE, activation_type="normal",
                   start_date=datetime.now(timezone.utc), origin="NATIVE")
        db.add(lote); await db.commit()
        try:
            informe = await ds.limpiar(db, dry_run=True, force_unmarked=None)
            assert informe["status"] == "AMBIGUOUS_QA_DATA" and "lot:LOTE-REAL-SIN-MARCA" in informe["ambiguous"]
            informe = await ds.limpiar(db, dry_run=False, force_unmarked=None)
            assert informe["status"] == "AMBIGUOUS_QA_DATA"
            assert await db.scalar(select(Lot).where(Lot.lot_code == "LOTE-REAL-SIN-MARCA")) is not None
            assert await db.scalar(select(Company).where(Company.tax_id == b.TAX_MAIN)) is not None
        finally:
            await db.execute(delete(Lot).where(Lot.id == lote.id))
            await db.execute(delete(House).where(House.id == galpon.id))
            await db.execute(delete(Farm).where(Farm.id == granja.id))
            await db.execute(delete(Company).where(Company.id == empresa.id))
            await db.commit()


@pytest.mark.asyncio
async def test_force_unmarked_exige_tax_id_exacto():
    """`force_unmarked` solo autoriza con el `tax_id` exacto de una empresa QA (R1: ya no es un booleano).

    Con un valor distinto el cleanup sigue fail-closed; con `TAX_MAIN` el dry-run continúa pero no borra nada.
    """
    from app.database import async_session
    from app.masters.models import Company

    async with async_session() as db:
        if await db.scalar(select(Company).where(Company.tax_id == b.TAX_MAIN)):
            pytest.skip("el dataset QA ya está presente en esta base; la prueba exige una base sin él")
        empresa = Company(name=b.COMPANY_MAIN, tax_id=b.TAX_MAIN, country="Venezuela", currency="USD", approval_levels=1, is_active=True)
        db.add(empresa)
        await db.flush()
        from app.masters.models import Lot, BirdTypeEnum, SexEnum, LotStatus
        from app.masters.models import Farm, FarmType, House, HouseType
        granja = Farm(company_id=empresa.id, code="QA-TMP-F", name="QA tmp", location="x", farm_type=FarmType.FATTENING, is_active=True)
        db.add(granja); await db.flush()
        galpon = House(farm_id=granja.id, name="QA-TMP-G1", capacity=1000, house_type=HouseType.OPEN, is_active=True)
        db.add(galpon); await db.flush()
        from datetime import datetime, timezone
        lote = Lot(company_id=empresa.id, farm_id=granja.id, house_id=galpon.id, lot_code="LOTE-REAL-SIN-MARCA",
                   bird_type=BirdTypeEnum.BROILER, sex=SexEnum.MIXED, status=LotStatus.ACTIVE, activation_type="normal",
                   start_date=datetime.now(timezone.utc), origin="NATIVE")
        db.add(lote); await db.commit()
        try:
            informe = await ds.limpiar(db, dry_run=True, force_unmarked="otro")
            assert informe["status"] == "AMBIGUOUS_QA_DATA" and "lot:LOTE-REAL-SIN-MARCA" in informe["ambiguous"]
            informe = await ds.limpiar(db, dry_run=True, force_unmarked=b.TAX_MAIN)
            assert informe["status"] == "DRY_RUN"
            assert await db.scalar(select(Lot).where(Lot.lot_code == "LOTE-REAL-SIN-MARCA")) is not None
            assert await db.scalar(select(Company).where(Company.tax_id == b.TAX_MAIN)) is not None
        finally:
            await db.execute(delete(Lot).where(Lot.id == lote.id))
            await db.execute(delete(House).where(House.id == galpon.id))
            await db.execute(delete(Farm).where(Farm.id == granja.id))
            await db.execute(delete(Company).where(Company.id == empresa.id))
            await db.commit()


def test_sync_request_id_unico_por_objeto():
    """`sync_request_id` es único por `(run, objeto)`, ≤ 36 caracteres, determinista y distinto por `run_id`."""
    from app.integrations.sap.inbound.registry import HanaObject
    from seeds.qa_integral_builders import sync_request_id

    run_id = "QA-DEMO-V1-20261018"
    ids = [sync_request_id(run_id, objeto) for objeto in HanaObject]
    assert len(set(ids)) == len(HanaObject), f"ids repetidos para {run_id}: {sorted(ids)}"
    assert all(len(i) <= 36 for i in ids), [i for i in ids if len(i) > 36]
    assert all(i.startswith("qa-") for i in ids)
    assert all(sync_request_id(run_id, o) == sync_request_id(run_id, o) for o in HanaObject), "no es determinista"
    otros = {sync_request_id("QA-DEMO-V1-20261019", o) for o in HanaObject}
    assert not (otros & set(ids)), "otro run_id reutiliza ids del anterior"


@pytest.mark.asyncio
async def test_cleanup_sin_empresas_qa_no_hace_nada():
    from app.database import async_session
    from app.masters.models import Company

    async with async_session() as db:
        if await db.scalar(select(Company).where(Company.tax_id.in_([b.TAX_MAIN, b.TAX_ISO]))):
            pytest.skip("el dataset QA está presente en esta base")
        informe = await ds.limpiar(db, dry_run=False, force_unmarked=None)
        assert informe["status"] == "NOTHING_TO_CLEAN"
        inv = await ds.inventario(db)
        assert inv["qa_companies"] == [] and inv["qa_users"] == 0 and inv["qa_lots"] == 0
