"""Curvas estándar de peso por línea genética — `GA-REM-037`, decisión `OD-06`.

Cubre `AC01`…`AC10`, `AC23` y `AC24`.

`spec.md §4.5` exige alertar cuando el peso se desvía del estándar, pero el estándar no
existía en ninguna parte: ni tabla, ni versión, ni referencia desde el lote. `OD-06`
resolvió que Global Avícola administra esas curvas, y este archivo certifica que la
referencia contra la que se juzga un lote es la que le corresponde y no cambia bajo sus
pies.

Las tablas de estos tests son artificiales a propósito: se eligen números redondos para
que la interpolación sea comprobable a mano. No son las curvas de Cobb ni de Aviagen, y
ninguna se siembra.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot

PREFIJO = "GC-TEST-"

#: Dos puntos que hacen la aritmética verificable sin calculadora: a los 15 días, la
#: interpolación lineal de 10→20 cae exactamente en la mitad.
TABLA = [
    {"age_days": 10, "min_weight": 90.0, "target_weight": 100.0, "max_weight": 110.0},
    {"age_days": 20, "min_weight": 180.0, "target_weight": 200.0, "max_weight": 220.0},
]


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.masters.models import (
        GeneticLine, GeneticWeightCurve, GeneticWeightCurvePoint,
    )

    async with e.begin() as c:
        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if lotes:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        lineas = (await c.execute(
            select(GeneticLine.id).where(GeneticLine.name.like(f"{PREFIJO}%")))).scalars().all()
        if lineas:
            curvas = (await c.execute(select(GeneticWeightCurve.id).where(
                GeneticWeightCurve.genetic_line_id.in_(lineas)))).scalars().all()
            if curvas:
                await c.execute(delete(GeneticWeightCurvePoint).where(
                    GeneticWeightCurvePoint.curve_id.in_(curvas)))
                await c.execute(delete(GeneticWeightCurve).where(
                    GeneticWeightCurve.id.in_(curvas)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "geneticline",
                AuditLog.entity_id.in_([str(i) for i in lineas])))
            await c.execute(delete(GeneticLine).where(GeneticLine.id.in_(lineas)))
    await e.dispose()


async def _linea(client, cab, company_id) -> int:
    r = await client.post("/api/v1/masters/genetic-lines", headers=cab, json={
        "company_id": company_id, "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


async def _curva(client, cab, linea_id, version="v1", puntos=None, activa=True):
    return await client.post("/api/v1/masters/weight-curves", headers=cab, json={
        "genetic_line_id": linea_id, "version_label": version,
        "is_active": activa, "points": puntos if puntos is not None else TABLA})


async def _lote(client, cab, seeded_ids, **extra):
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed",
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots", headers=cab, json=cuerpo)


# ── AC01 · el catálogo de líneas ──────────────────────────────────────────────

async def test_t_037_01_las_tres_lineas_iniciales_se_siembran(test_database_url):
    """`AC01` · Cobb 500, Ross 308 y Hubbard existen tras la siembra, en cada empresa.

    `OD-06` las nombra como las iniciales. Se siembra **el nombre**, nunca la curva: la
    tabla la carga el administrador desde la publicación del proveedor.
    """
    from app.masters.models import Company, GeneticLine, GeneticWeightCurve
    from seeds.baseline_seeds import EMPRESAS_CERTIFICACION, LINEAS_GENETICAS, sembrar_baseline

    motor = create_async_engine(test_database_url)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    try:
        async with fabrica() as s:
            await sembrar_baseline(s)
            for datos in EMPRESAS_CERTIFICACION:
                empresa = (await s.execute(
                    select(Company).where(Company.name == datos["name"]))).scalar_one()
                nombres = {
                    g.name for g in (await s.execute(select(GeneticLine).where(
                        GeneticLine.company_id == empresa.id))).scalars()
                }
                for esperado, _, _ in LINEAS_GENETICAS:
                    assert esperado in nombres, (
                        f"{empresa.name}: falta la línea {esperado!r}; hay {sorted(nombres)}"
                    )

            # Y ninguna curva: sembrar valores inventados daría una referencia falsa con
            # toda la apariencia de ser la del proveedor.
            curvas = (await s.execute(select(GeneticWeightCurve))).scalars().all()
            assert curvas == [], (
                f"la siembra cargó {len(curvas)} curvas; `OD-06` solo autoriza nombres"
            )
    finally:
        await motor.dispose()


async def test_t_037_02_se_pueden_anadir_otras_lineas(client, auth_headers, seeded_ids, motor):
    """`AC01` · el catálogo no es un enum: una línea nueva se crea por la API."""
    nombre = f"{PREFIJO}{uuid.uuid4().hex[:8]}"
    r = await client.post("/api/v1/masters/genetic-lines", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "name": nombre})
    assert r.status_code in (200, 201), r.text
    assert r.json()["name"] == nombre


# ── AC02 · AC03 · AC04 — el modelo ────────────────────────────────────────────

async def test_t_037_03_una_linea_admite_varias_versiones(
    client, auth_headers, seeded_ids, motor
):
    """`AC02` · dos versiones conviven y solo una queda activa."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])

    primera = await _curva(client, auth_headers, linea, version="2019", activa=True)
    assert primera.status_code == 201, primera.text
    segunda = await _curva(client, auth_headers, linea, version="2024", activa=True)
    assert segunda.status_code == 201, segunda.text

    r = await client.get(
        f"/api/v1/masters/genetic-lines/{linea}/weight-curves", headers=auth_headers)
    assert r.status_code == 200, r.text
    versiones = {c["version_label"]: c["is_active"] for c in r.json()}
    assert versiones == {"2019": False, "2024": True}, versiones


async def test_t_037_04_la_version_es_unica_dentro_de_la_linea(
    client, auth_headers, seeded_ids, motor
):
    """`AC02` · repetir el número de versión haría ambigua la referencia del lote."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    assert (await _curva(client, auth_headers, linea, version="v1")).status_code == 201
    repetida = await _curva(client, auth_headers, linea, version="v1")
    assert repetida.status_code == 409, repetida.text


@pytest.mark.parametrize("punto,campo", [
    ({"age_days": 10, "min_weight": 200.0, "max_weight": 150.0}, "min_weight"),
    ({"age_days": 10, "min_weight": 90.0, "max_weight": 110.0, "target_weight": 500.0},
     "target_weight"),
])
async def test_t_037_05_un_punto_incoherente_se_rechaza(
    client, auth_headers, seeded_ids, motor, punto, campo
):
    """`AC03` · rango invertido u objetivo fuera del rango describen una curva imposible."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea, puntos=[punto])
    assert r.status_code == 422, r.text
    errores = r.json()["detail"]["errores"]
    assert [e["campo"] for e in errores] == [campo], errores


async def test_t_037_06_la_edad_negativa_se_rechaza(client, auth_headers, seeded_ids, motor):
    """`AC03` · un día negativo no existe en la vida de un lote."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea,
                     puntos=[{"age_days": -1, "min_weight": 90.0, "max_weight": 110.0}])
    assert r.status_code == 422, r.text


async def test_t_037_07_dos_puntos_con_la_misma_edad_se_rechazan(
    client, auth_headers, seeded_ids, motor
):
    """`AC04` · el motor tendría que elegir entre dos verdades, y cualquiera sería arbitraria."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea, puntos=[
        {"age_days": 10, "min_weight": 90.0, "max_weight": 110.0},
        {"age_days": 10, "min_weight": 95.0, "max_weight": 115.0},
    ])
    assert r.status_code == 422, r.text
    errores = r.json()["detail"]["errores"]
    assert errores[0]["campo"] == "age_days", errores
    assert errores[0]["fila"] == 2, errores


# ── AC05 · AC06 — la carga ────────────────────────────────────────────────────

async def test_t_037_08_una_tabla_valida_se_importa_entera(
    client, auth_headers, seeded_ids, motor
):
    """`AC05` · la versión queda con exactamente los puntos enviados."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea)
    assert r.status_code == 201, r.text
    puntos = r.json()["points"]
    assert len(puntos) == len(TABLA), puntos
    assert {p["age_days"] for p in puntos} == {t["age_days"] for t in TABLA}
    diez = next(p for p in puntos if p["age_days"] == 10)
    assert (diez["min_weight"], diez["target_weight"], diez["max_weight"]) == (90.0, 100.0, 110.0)


async def test_t_037_09_una_tabla_invalida_no_deja_nada(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC06` · rechazo entero, cero puntos persistidos, y el error dice fila y motivo.

    Una curva a medias no es una curva incompleta: es una curva **equivocada**. Un lote
    evaluado contra ella recibiría un veredicto falso sin que nada lo delatara.
    """
    from app.masters.models import GeneticWeightCurve, GeneticWeightCurvePoint

    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea, puntos=[
        {"age_days": 10, "min_weight": 90.0, "max_weight": 110.0},   # válida
        {"age_days": 20, "min_weight": 300.0, "max_weight": 200.0},  # rango invertido
        {"age_days": 30, "min_weight": 400.0, "max_weight": 500.0},  # válida
    ])
    assert r.status_code == 422, r.text

    detalle = r.json()["detail"]["errores"]
    assert len(detalle) == 1, detalle
    assert detalle[0]["fila"] == 2, detalle
    assert detalle[0]["campo"] == "min_weight", detalle
    assert detalle[0]["motivo"], "el rechazo no explica el motivo"

    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            curvas = (await c.execute(select(GeneticWeightCurve.id).where(
                GeneticWeightCurve.genetic_line_id == linea))).scalars().all()
            assert curvas == [], f"quedó una versión huérfana: {curvas}"
            # Ni un punto suelto: la fila 1 y la 3 eran válidas y tampoco entran.
            sueltos = (await c.execute(select(GeneticWeightCurvePoint.id).where(
                GeneticWeightCurvePoint.curve_id.in_(curvas or [-1])))).scalars().all()
            assert sueltos == [], sueltos
    finally:
        await e.dispose()


async def test_t_037_10_el_informe_enumera_todos_los_defectos(
    client, auth_headers, seeded_ids, motor
):
    """`AC06` · quien carga 60 filas necesita ver los seis errores, no el primero."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _curva(client, auth_headers, linea, puntos=[
        {"age_days": 10, "min_weight": 300.0, "max_weight": 200.0},
        {"age_days": 20, "min_weight": 90.0, "max_weight": 110.0, "target_weight": 999.0},
    ])
    assert r.status_code == 422, r.text
    filas = {e["fila"] for e in r.json()["detail"]["errores"]}
    assert filas == {1, 2}, r.json()["detail"]["errores"]


# ── AC07 · AC08 · AC09 · AC10 — la asignación ─────────────────────────────────

async def test_t_037_11_el_lote_guarda_la_version_concreta(
    client, auth_headers, seeded_ids, motor
):
    """`AC07` y `AC09` · un lote nuevo toma la versión activa de su línea, por id."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    curva = (await _curva(client, auth_headers, linea, version="2024")).json()

    r = await _lote(client, auth_headers, seeded_ids, genetic_line_id=linea)
    assert r.status_code == 201, r.text
    assert r.json()["weight_curve_id"] == curva["id"], r.json()


async def test_t_037_12_publicar_una_version_no_toca_los_lotes_existentes(
    client, auth_headers, seeded_ids, motor
):
    """`AC08` y `AC23` · el lote conserva la curva con la que nació.

    Es la diferencia entre una referencia histórica y una que se reescribe: si activar la
    revisión de 2024 cambiara la de los lotes de 2019, los veredictos ya emitidos sobre
    ellos dejarían de ser reproducibles.
    """
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    vieja = (await _curva(client, auth_headers, linea, version="2019")).json()

    lote = (await _lote(client, auth_headers, seeded_ids, genetic_line_id=linea)).json()
    assert lote["weight_curve_id"] == vieja["id"]

    nueva = (await _curva(client, auth_headers, linea, version="2024", activa=True)).json()
    assert nueva["is_active"] is True

    r = await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["weight_curve_id"] == vieja["id"], (
        "activar una versión nueva reescribió la referencia de un lote existente"
    )


async def test_t_037_13_una_curva_de_otra_linea_se_rechaza(
    client, auth_headers, seeded_ids, motor
):
    """`AC10` · juzgar un Ross contra la tabla de un Cobb da un veredicto sin garantías."""
    ross = await _linea(client, auth_headers, seeded_ids["company_id"])
    cobb = await _linea(client, auth_headers, seeded_ids["company_id"])
    curva_ross = (await _curva(client, auth_headers, ross, version="r1")).json()
    curva_cobb = (await _curva(client, auth_headers, cobb, version="c1")).json()

    # CONTROL · la curva de su propia línea entra.
    propio = await _lote(client, auth_headers, seeded_ids,
                         genetic_line_id=ross, weight_curve_id=curva_ross["id"])
    assert propio.status_code == 201, propio.text

    # TRATAMIENTO · la de la otra línea, no.
    cruzado = await _lote(client, auth_headers, seeded_ids,
                          genetic_line_id=ross, weight_curve_id=curva_cobb["id"])
    assert cruzado.status_code == 400, cruzado.text


async def test_t_037_14_un_lote_sin_curva_cargada_no_inventa_ninguna(
    client, auth_headers, seeded_ids, motor
):
    """`AC09` · sin versión activa el lote queda sin referencia, y lo dice."""
    linea = await _linea(client, auth_headers, seeded_ids["company_id"])
    r = await _lote(client, auth_headers, seeded_ids, genetic_line_id=linea)
    assert r.status_code == 201, r.text
    assert r.json()["weight_curve_id"] is None, r.json()


# ── AC24 — tenencia ───────────────────────────────────────────────────────────

async def test_t_037_15_las_curvas_no_cruzan_de_empresa(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC24` · un operador solo ve las curvas de las líneas de su empresa.

    El sujeto negativo es un operador con empresa propia, no el Super Administrador: su
    exención de tenencia haría que el test pasara sin comprobar nada.
    """
    from app.auth.security import create_access_token

    # `GA-REM-002-C` / `R-139` · `OD-14.c`: las curvas son superficie de inquilino también
    # para la autoridad global. La línea y la curva de la empresa 2 se crean **situado** en
    # la empresa 2 (reclamación autorizada, `OD-11`), como `771b402` hizo en
    # `test_lot_closure`; antes esta fixture dependía del atajo que `R-139` retira.
    situado_2 = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_admin_id"]),
              "company_id": seeded_ids["company_id_2"]})}
    propia = await _linea(client, auth_headers, seeded_ids["company_id"])
    ajena = await _linea(client, situado_2, seeded_ids["company_id_2"])
    curva_propia = (await _curva(client, auth_headers, propia, version="p1")).json()
    curva_ajena = (await _curva(client, situado_2, ajena, version="a1")).json()
    assert "id" in curva_propia and "id" in curva_ajena, (curva_propia, curva_ajena)

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_other_company_id"])})}

    # CONTROL · el operador de la empresa 2 ve la curva de la línea de la empresa 2.
    suya = await http_client.get(
        f"/api/v1/masters/weight-curves/{curva_ajena['id']}", headers=operador)
    assert suya.status_code == 200, suya.text

    # TRATAMIENTO · la de la empresa 1 no existe para él.
    cruzada = await http_client.get(
        f"/api/v1/masters/weight-curves/{curva_propia['id']}", headers=operador)
    assert cruzada.status_code == 404, (
        f"un operador leyó la curva de otra empresa: {cruzada.text}"
    )
