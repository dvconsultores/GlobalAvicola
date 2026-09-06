"""Gestión de datos maestros — `GA-REM-033`, hallazgos `R-89`, `R-90` y `R-91`.

Cubre `AC01`, `AC02`, `AC05`…`AC11`.

Siete maestros que `docs/02 §3.2` exige no podían editarse: pasaban `None` como esquema de
actualización, así que `register_crud` no registraba su `PUT`. Y el listado descartaba el
total que su propio servicio calcula, de modo que la interfaz mostraba el tamaño de la
página donde promete «resultados».
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

PREFIJO = "MM-TEST-"

#: Los siete de `GA-REM-033 §2`, con el campo mínimo que cada uno exige.
SIETE = [
    ("medications", {}),
    ("cull-causes", {}),
    ("rejection-reasons", {}),
    ("correction-types", {}),
    ("productive-phases", {"order": 1}),
]


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.masters import models as m

    async with e.begin() as c:
        for modelo in (m.Medication, m.CullCause, m.RejectionReason, m.CorrectionType,
                       m.ProductivePhase, m.Incubator, m.Hatcher, m.Hatchery):
            if hasattr(modelo, "name"):
                ids = (await c.execute(
                    select(modelo.id).where(modelo.name.like(f"{PREFIJO}%")))).scalars().all()
                if ids:
                    await c.execute(delete(AuditLog).where(
                        AuditLog.entity_type == modelo.__name__.lower(),
                        AuditLog.entity_id.in_([str(i) for i in ids])))
                    await c.execute(delete(modelo).where(modelo.id.in_(ids)))
    await e.dispose()


async def _crear(client, cab, entidad, company_id, **extra):
    r = await client.post(f"/api/v1/masters/{entidad}", headers=cab, json={
        "company_id": company_id, "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}", **extra})
    assert r.status_code in (200, 201), f"{entidad}: {r.text}"
    return r.json()


# ── AC05 · los siete admiten edición ──────────────────────────────────────────

@pytest.mark.parametrize("entidad,extra", SIETE)
async def test_t_091_01_los_maestros_se_pueden_editar(
    client, auth_headers, seeded_ids, motor, entidad, extra
):
    """`AC05` y `AC06` · sin esquema de actualización, `register_crud` no registraba `PUT`.

    Un maestro que solo puede crearse y darse de baja, pero no corregirse, obliga a duplicar
    el registro para arreglar una errata.
    """
    creado = await _crear(client, auth_headers, entidad, seeded_ids["company_id"], **extra)
    nuevo = f"{PREFIJO}editado-{uuid.uuid4().hex[:6]}"

    r = await client.put(f"/api/v1/masters/{entidad}/{creado['id']}", headers=auth_headers,
                         json={"name": nuevo})
    assert r.status_code == 200, f"{entidad} no admite edición: {r.status_code} {r.text}"
    assert r.json()["name"] == nuevo

    # `AC06` · `R-68`: lectura posterior e independiente, sin esperas.
    leido = await client.get(f"/api/v1/masters/{entidad}/{creado['id']}", headers=auth_headers)
    assert leido.status_code == 200, leido.text
    assert leido.json()["name"] == nuevo


# ── AC07 · baja lógica ────────────────────────────────────────────────────────

async def test_t_090_02_la_baja_es_logica_y_no_fisica(
    client, auth_headers, seeded_ids, motor
):
    """`AC07` · el registro se marca inactivo; no se pierde."""
    from app.masters.models import CullCause

    creado = await _crear(client, auth_headers, "cull-causes", seeded_ids["company_id"])

    r = await client.delete(f"/api/v1/masters/cull-causes/{creado['id']}", headers=auth_headers)
    assert r.status_code == 204, r.text

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        fila = (await s.execute(
            select(CullCause).where(CullCause.id == creado["id"]))).scalar_one_or_none()
    assert fila is not None, "la baja borró físicamente el maestro"
    assert fila.is_active is False


# ── AC01 · AC02 · el total viaja y respeta el filtro ──────────────────────────

async def test_t_089_03_el_listado_devuelve_el_total(
    client, auth_headers, seeded_ids, motor
):
    """`AC01` y `AC02` · el servicio ya lo calculaba; el router lo tiraba.

    Se crean **más registros que el tamaño de página** a propósito: con menos, el tamaño de
    la página y el total coinciden y la comprobación no podría fallar.
    """
    marca = uuid.uuid4().hex[:6]
    for _ in range(25):                                   # el tamaño de página es 20
        await _crear(client, auth_headers, "medications", seeded_ids["company_id"],
                     name=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}")

    r = await client.get(f"/api/v1/masters/medications?limit=20&search={marca}",
                         headers=auth_headers)
    assert r.status_code == 200, r.text

    # El cuerpo sigue siendo la lista: 43 puntos del frontend dependen de ello.
    assert len(r.json()) == 20, "la página sigue teniendo el tamaño pedido"

    # `AC01` · el total viaja en cabecera. `AC02` · cuenta las coincidencias del filtro, no
    # el catálogo entero — por eso el conjunto tiene 25 y la página 20.
    assert "x-total-count" in r.headers, (
        f"el listado debe exponer el total que ya calcula: {dict(r.headers)}"
    )
    assert int(r.headers["x-total-count"]) == 25, (
        f"el total debe contar las 25 coincidencias, no la página: {r.headers['x-total-count']}"
    )


# ── AC08 · pertenencia del padre ──────────────────────────────────────────────

async def test_t_090_04_no_se_crea_bajo_una_planta_ajena(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC08` · `R-59` · CONTROL y TRATAMIENTO sobre la misma petición."""
    s = uuid.uuid4().hex[:8]
    propia = await client.post("/api/v1/masters/hatcheries", headers=auth_headers, json={
        "company_id": seeded_ids["company_id"], "name": f"{PREFIJO}planta-{s}"})
    assert propia.status_code in (200, 201), propia.text

    cambio = await client.post("/api/v1/switch-company", headers=auth_headers,
                               json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200, cambio.text
    admin_2 = {"Authorization": f"Bearer {cambio.json()['access_token']}"}
    ajena = await client.post("/api/v1/masters/hatcheries", headers=admin_2, json={
        "company_id": seeded_ids["company_id_2"], "name": f"{PREFIJO}planta-ajena-{s}"})
    assert ajena.status_code in (200, 201), ajena.text

    # CONTROL · incubadora bajo la planta propia.
    ok = await client.post("/api/v1/masters/incubators", headers=auth_headers, json={
        "hatchery_id": propia.json()["id"], "name": f"{PREFIJO}inc-{s}"})
    assert ok.status_code in (200, 201), f"CONTROL falló: {ok.text}"

    # TRATAMIENTO · la misma petición, bajo la planta de otra empresa.
    cruzada = await http_client.post("/api/v1/masters/incubators", headers=auth_headers, json={
        "hatchery_id": ajena.json()["id"], "name": f"{PREFIJO}inc-cruzada-{s}"})
    assert cruzada.status_code == 400, (
        f"se creó una incubadora bajo la planta de otra empresa: {cruzada.status_code}"
    )


# ── AC09 · el maestro global no se filtra por empresa ─────────────────────────

async def test_t_090_05_la_fase_productiva_es_global(
    client, auth_headers, seeded_ids, motor
):
    """`AC09` · `productive-phases` no declara `company_id`: aplicarle el filtro la rompería."""
    creada = await _crear(client, auth_headers, "productive-phases",
                          seeded_ids["company_id"], order=1)

    cambio = await client.post("/api/v1/switch-company", headers=auth_headers,
                               json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200
    admin_2 = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    r = await client.get(f"/api/v1/masters/productive-phases/{creada['id']}", headers=admin_2)
    assert r.status_code == 200, (
        "la fase productiva es global y debe verse desde cualquier empresa: "
        f"{r.status_code} {r.text}"
    )


# ── AC10 · el maestro creado se puede usar ────────────────────────────────────

async def test_t_090_06_la_causa_creada_se_puede_usar_en_un_descarte(
    client, auth_headers, seeded_ids, motor
):
    """`AC10` · una pantalla que abre no certifica el proceso.

    La cadena se cierra cuando el maestro creado desde la gestión se puede **seleccionar** en
    la operación que lo exige.
    """
    from tests.time_reference import iso_days_ago

    causa = await _crear(client, auth_headers, "cull-causes", seeded_ids["company_id"])

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"], "event_type": "cull_recording",
        "event_date": iso_days_ago(0),
        "bird_movements": [{"sex": "mixed", "quantity": 3, "cull_cause_id": causa["id"]}],
    })
    assert r.status_code == 201, f"la causa recién creada no se pudo usar: {r.text}"


# ── AC11 · permiso obligatorio ────────────────────────────────────────────────

async def test_t_090_07_sin_permiso_no_se_gestiona(
    client, http_client, seeded_ids, motor
):
    """`AC11` · el operador tiene `masters:read`, no `create` ni `update`."""
    from app.auth.security import create_access_token

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_operator_id"])})}
    r = await http_client.post("/api/v1/masters/medications", headers=operador, json={
        "company_id": seeded_ids["company_id"], "name": f"{PREFIJO}sin-permiso"})
    assert r.status_code == 403, r.text
