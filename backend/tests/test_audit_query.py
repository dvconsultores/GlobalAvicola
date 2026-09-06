"""Contrato de consulta de auditoría — `GA-REM-032`, hallazgo `R-82`.

Cubre `AC09`, `AC10`, `AC12` y `AC13`.

`docs/02 §3.11.2` exige siete filtros: usuario, lote, fecha, tipo de operación, módulo,
**estado** y **documento SAP**. El backend implementaba cinco. La interfaz, entretanto,
enviaba `search`, `action_contains` y `group_by`, que no aparecen en ninguna fuente
normativa y FastAPI descartaba en silencio.

El conjunto de prueba es deliberadamente distinguible: cada filtro debe devolver un
subconjunto **exacto**, no «alguno» ni «al menos uno».
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.audit.models import AuditAction, AuditLog, AuditModule

ENTIDAD = "AQ-TEST"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    async with e.begin() as c:
        await c.execute(delete(AuditLog).where(AuditLog.entity_type == ENTIDAD))
    await e.dispose()


@pytest_asyncio.fixture
async def conjunto(motor, seeded_ids):
    """Seis registros que se distinguen entre sí en cada dimensión que se va a filtrar.

    Se insertan directamente: aquí se prueba la **consulta**, no la emisión —que tiene sus
    propias pruebas—, y depender de ella mezclaría dos cosas.
    """
    from app.integrations.sap.models import SapReference, SapReferenceType

    ahora = datetime.now(timezone.utc)
    c1, c2 = seeded_ids["company_id"], seeded_ids["company_id_2"]
    admin, operador = seeded_ids["user_admin_id"], seeded_ids["user_operator_id"]

    # `sap_reference_id` tiene clave foránea real, pese a lo que dice el comentario del
    # modelo: las referencias deben existir.
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        refs = [SapReference(company_id=c1, ref_type=SapReferenceType.PURCHASE_ORDER,
                             sap_code=f"{ENTIDAD}-{n}", description="filtro") for n in (1, 2)]
        for r in refs:
            s.add(r)
        await s.commit()
        sap_a, sap_b = refs[0].id, refs[1].id

    filas = [
        # id            empresa usuario   acción                    módulo        lote  estado      sap
        ("a", c1, admin,    AuditAction.CREATED,   AuditModule.OPERATIONS, seeded_ids["lot_id"], "registered", sap_a, 0),
        ("b", c1, admin,    AuditAction.UPDATED,   AuditModule.MASTERS,    None,                 "approved",   None, 1),
        ("c", c1, operador, AuditAction.CREATED,   AuditModule.OPERATIONS, None,                 "approved",   sap_b, 2),
        ("d", c1, operador, AuditAction.LOGIN,     AuditModule.AUTH,       None,                 None,         None, 40),
        ("e", c1, admin,    AuditAction.EXPORT,    AuditModule.SAP,        None,                 None,         sap_a, 3),
        ("f", c2, admin,    AuditAction.CREATED,   AuditModule.OPERATIONS, None,                 "registered", None, 0),
    ]
    async with fabrica() as s:
        for clave, empresa, usuario, accion, modulo, lote, estado, sap, dias in filas:
            s.add(AuditLog(
                id=str(uuid.uuid4()), company_id=empresa, user_id=usuario, action=accion,
                entity_type=ENTIDAD, entity_id=clave, module=modulo, lot_id=lote,
                new_state=estado, sap_reference_id=sap,
                created_at=ahora - timedelta(days=dias),
            ))
        await s.commit()
    return {"c1": c1, "c2": c2, "admin": admin, "operador": operador,
            "lote": seeded_ids["lot_id"], "sap_a": sap_a}


async def _claves(client, cabecera, **params):
    """Identificadores del conjunto de prueba que devuelve la consulta."""
    q = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    r = await client.get(f"/api/v1/audit?limit=200&{q}", headers=cabecera)
    assert r.status_code == 200, r.text
    return sorted(f["entity_id"] for f in r.json()["logs"]
                  if f.get("entity_type") == ENTIDAD)


# ── AC09 · los siete filtros ──────────────────────────────────────────────────

async def test_t_082_01_filtro_por_usuario(client, auth_headers, conjunto):
    """`AC09` · subconjunto **exacto**, no «al menos uno»."""
    assert await _claves(client, auth_headers, user_id=conjunto["operador"]) == ["c", "d"]


async def test_t_082_02_filtro_por_tipo_de_operacion(client, auth_headers, conjunto):
    assert await _claves(client, auth_headers, action="created") == ["a", "c"]


async def test_t_082_03_filtro_por_modulo(client, auth_headers, conjunto):
    assert await _claves(client, auth_headers, module="operations") == ["a", "c"]


async def test_t_082_04_filtro_por_lote(client, auth_headers, conjunto):
    assert await _claves(client, auth_headers, lot_id=conjunto["lote"]) == ["a"]


async def test_t_082_05_filtro_por_fecha(client, auth_headers, conjunto):
    """El registro `d` tiene 40 días: queda fuera de una ventana de 10."""
    desde = (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat()
    assert await _claves(client, auth_headers, date_from=desde) == ["a", "b", "c", "e"]


async def test_t_082_06_filtro_por_estado(client, auth_headers, conjunto):
    """`AC09` · «estado» es uno de los siete de `§3.11.2` y no existía."""
    assert await _claves(client, auth_headers, state="approved") == ["b", "c"]


async def test_t_082_07_filtro_por_documento_sap(client, auth_headers, conjunto):
    """`AC09` · «documento SAP» es el séptimo, y tampoco existía."""
    assert await _claves(client, auth_headers,
                         sap_reference_id=conjunto["sap_a"]) == ["a", "e"]


async def test_t_082_08_filtros_combinados(client, auth_headers, conjunto):
    """`AC09` · componer dos filtros acota de verdad; no basta con que cada uno funcione."""
    assert await _claves(client, auth_headers,
                         action="created", user_id=conjunto["admin"]) == ["a"]


# ── AC10 · el filtrado ocurre en el servidor ──────────────────────────────────

async def test_t_082_09_el_filtro_precede_a_la_paginacion(client, auth_headers, conjunto):
    """`AC10` · con `limit=1`, el filtro ya debe haber acotado el universo.

    Si se filtrara la página ya recuperada, pedir una sola fila devolvería la primera del
    total y el filtro no encontraría nada.
    """
    r = await client.get("/api/v1/audit?limit=1&action=export", headers=auth_headers)
    assert r.status_code == 200, r.text
    filas = r.json()["logs"]
    assert len(filas) == 1
    assert filas[0]["entity_id"] == "e", filas[0]


# ── AC12 · aislamiento entre empresas ─────────────────────────────────────────

async def test_t_082_10_no_se_ven_registros_de_otra_empresa(
    client, http_client, auth_headers, seeded_ids, conjunto
):
    """`AC12` · CONTROL y TRATAMIENTO con la misma consulta.

    El registro `f` es de la empresa 2 y por lo demás idéntico a `a`: misma acción, mismo
    módulo, mismo actor. Lo único que cambia es de quién es.
    """
    # CONTROL · el auditor de la empresa 1 ve los suyos.
    propios = await _claves(client, auth_headers)
    assert "a" in propios, propios

    # TRATAMIENTO · y no ve el de la empresa 2.
    assert "f" not in propios, "un auditor vio un registro de otra empresa"


# ── AC13 · sin permiso no se consulta ─────────────────────────────────────────

async def test_t_082_11_sin_permiso_no_se_consulta(
    client, http_client, seeded_ids, conjunto
):
    """`AC13` · `audit:read` es obligatorio."""
    from app.auth.security import create_access_token

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_operator_id"])})}
    r = await http_client.get("/api/v1/audit", headers=operador)
    assert r.status_code == 403, r.text
