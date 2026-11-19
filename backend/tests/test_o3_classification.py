"""`SPEC 016` · `O-3` — clasificación manual de un pendiente **por el código de la unidad**.

La bandeja de `OD-10.c` sabía decir *qué* registros no tienen cadena y no sabía ofrecer *a
cuáles* clasificarlos: la pantalla tenía que conocer el identificador de la habilitación, que
es un dato de administración. `O-3` cierra las dos mitades:

```
GET  /operations/{id}/classification-candidates   qué destinos existen para este pendiente
POST /operations/{id}/classify                    elige uno **por su código** y dice por qué
```

Tres invariantes que estas pruebas fijan, y que son las que pueden romperse en silencio:

* el código se resuelve **contra la empresa del evento**, nunca contra una que venga en el
  cuerpo — si no, clasificar el registro del vecino sería cuestión de escribir su código;
* el motivo es **obligatorio**: sin él la trazabilidad diría que la cadena cambió y no por qué;
* clasificar sigue sin conceder nada, y una segunda clasificación del mismo registro no
  reescribe nada: el acto es único y su rastro también.

Reutiliza el escenario `BUPEND-` de `test_pending_classification.py` —empresa A con
reproductora e incubadora, empresa B con reproductora, cuatro actores y la inspección sin lote—.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from tests.test_pending_classification import _token, pend  # noqa: F401

pytestmark = pytest.mark.asyncio

MOTIVO = "Clasificacion manual de prueba"

#: El mensaje exacto del rechazo por código. Uno solo para las tres causas —no existe, no está
#: habilitada, es de otra empresa—: distinguirlas diría qué unidades tiene el vecino.
SIN_UNIDAD = "la unidad no existe o no esta habilitada para la empresa"


# ── Lecturas de la base, fuera de la petición ────────────────────────────────

async def _estado_evento(url: str, event_id: int):
    """`(business_unit_id, classified_at, classified_by_id)` del evento, leído aparte."""
    from app.operations.models import OperationalEvent

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor)() as s:
            evento = await s.get(OperationalEvent, event_id)
            return (evento.business_unit_id, evento.classified_at,
                    evento.classified_by_id)
    finally:
        await motor.dispose()


async def _auditoria(url: str, event_id: int):
    """Las filas de `P-09` del evento, como tuplas planas y en orden cronológico."""
    from app.audit.models import AuditLog

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor)() as s:
            filas = (await s.execute(
                select(AuditLog)
                .where(AuditLog.entity_type == "operational_event",
                       AuditLog.entity_id == str(event_id))
                .order_by(AuditLog.created_at))).scalars().all()
            return [(f.action, f.user_id, f.company_id, f.previous_state, f.new_state,
                     f.change_reason) for f in filas]
    finally:
        await motor.dispose()


async def _habilitar(url: str, *, company_id: int, code: str, is_enabled: bool) -> int:
    """Crea la habilitación que el escenario no trae —la apagada o la de la otra empresa—."""
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            unidad = (await s.execute(
                select(BusinessUnit).where(BusinessUnit.code == code))).scalar_one()
            fila = CompanyBusinessUnit(company_id=company_id,
                                       business_unit_id=unidad.id, is_enabled=is_enabled)
            s.add(fila)
            await s.flush()
            nuevo = fila.id
            await s.commit()
            return nuevo
    finally:
        await motor.dispose()


async def _efectivas(url: str, user_id: int):
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas

    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor)() as s:
            usuario = (await s.execute(
                select(User).where(User.id == user_id))).scalar_one()
            return await unidades_efectivas(s, usuario)
    finally:
        await motor.dispose()


async def _candidatos(http_client, event_id: int, user_id: int):
    return await http_client.get(
        f"/api/v1/operations/{event_id}/classification-candidates",
        headers=_token(user_id))


# ── AC-O3-01 · clasificar por código ─────────────────────────────────────────

async def test_ac_o3_01_clasificar_por_codigo_de_unidad(http_client, pend,
                                                         test_database_url):
    """`AC-O3-01`. El código basta: la pantalla no necesita el id de la habilitación."""
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert r.status_code == 200, r.text
    assert r.json()["id"] == pend["sin_lote"]

    unidad, clasificado, quien = await _estado_evento(test_database_url, pend["sin_lote"])
    assert unidad == pend["hab_hatchery"], "el código no resolvió a la habilitación de A"
    assert clasificado is not None
    assert quien == pend["clasif"]


# ── AC-O3-02 · el motivo es obligatorio ──────────────────────────────────────

async def test_ac_o3_02_el_motivo_es_obligatorio(http_client, pend, test_database_url):
    """`AC-O3-02`. Ausente, vacío, en blanco, nulo o de dos letras: 422 y sigue pendiente.

    Y el registro **no se toca**: un `422` que dejara la clasificación hecha sería peor que
    aceptarla, porque la pantalla mostraría el error y la cadena ya estaría decidida.
    """
    variantes = [
        {},
        {"reason": ""},
        {"reason": "   "},
        {"reason": None},
        {"reason": "ab"},
    ]
    for extra in variantes:
        r = await http_client.post(
            f"/api/v1/operations/{pend['sin_lote']}/classify",
            headers=_token(pend["clasif"]),
            json={"business_unit_code": "hatchery", **extra})
        assert r.status_code == 422, f"{extra}: {r.text}"
        unidad, clasificado, quien = await _estado_evento(
            test_database_url, pend["sin_lote"])
        assert unidad is None, f"{extra} clasificó el registro pese al 422"
        assert clasificado is None, f"{extra} dejó fecha de clasificación"


# ── AC-O3-03 · una sola unidad, ni dos ni ninguna ────────────────────────────

async def test_ac_o3_03_ni_dos_unidades_ni_ninguna(http_client, pend, test_database_url):
    """`AC-O3-03`. Dos caminos para el mismo dato admiten dos respuestas distintas."""
    cuerpos = [
        {"company_business_unit_id": pend["hab_hatchery"],
         "business_unit_code": "hatchery", "reason": MOTIVO},
        {"reason": MOTIVO},
        {"company_business_unit_id": None, "business_unit_code": None, "reason": MOTIVO},
    ]
    for cuerpo in cuerpos:
        r = await http_client.post(
            f"/api/v1/operations/{pend['sin_lote']}/classify",
            headers=_token(pend["clasif"]), json=cuerpo)
        assert r.status_code == 422, f"{cuerpo}: {r.text}"
        assert "business_unit_code" in r.text, r.text
        unidad, _, _ = await _estado_evento(test_database_url, pend["sin_lote"])
        assert unidad is None, f"{cuerpo} clasificó el registro"


# ── AC-O3-04 · el código se resuelve contra la empresa del evento ────────────

async def test_ac_o3_04_codigos_que_no_resuelven(http_client, pend, test_database_url):
    """`AC-O3-04`. Inexistente, deshabilitada y de la otra empresa: 400 y sigue pendiente.

    Los tres casos comparten mensaje a propósito: decir cuál de los tres fue convertiría el
    rechazo en un oráculo de la configuración del vecino.
    """
    # Una unidad apagada **de la empresa A** y otra encendida **solo en B**.
    await _habilitar(test_database_url, company_id=pend["empresa_a"],
                     code="broiler", is_enabled=False)
    await _habilitar(test_database_url, company_id=pend["empresa_b"],
                     code="grandparent", is_enabled=True)

    for codigo in ("no-existe", "broiler", "grandparent"):
        r = await http_client.post(
            f"/api/v1/operations/{pend['sin_lote']}/classify",
            headers=_token(pend["clasif"]),
            json={"business_unit_code": codigo, "reason": MOTIVO})
        assert r.status_code == 400, f"{codigo}: {r.text}"
        assert SIN_UNIDAD in r.text, r.text
        unidad, clasificado, _ = await _estado_evento(
            test_database_url, pend["sin_lote"])
        assert unidad is None, f"{codigo} clasificó el registro"
        assert clasificado is None


# ── AC-O3-05 · ver no es decidir ─────────────────────────────────────────────

async def test_ac_o3_05_el_creador_no_clasifica_ni_por_codigo(http_client, pend,
                                                              test_database_url):
    """`AC-O3-05`. Sin `masters:update`, el código no abre nada: 403."""
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["creador"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert r.status_code == 403, r.text
    assert (await _estado_evento(test_database_url, pend["sin_lote"]))[0] is None


# ── AC-O3-06 · ajeno, y una sola vez ─────────────────────────────────────────

async def test_ac_o3_06_el_ajeno_no_clasifica_y_el_acto_es_unico(
        http_client, pend, test_database_url):
    """`AC-O3-06`. La empresa B no ve el pendiente; y clasificar dos veces no reescribe.

    Lo segundo importa más de lo que parece: si la segunda llamada respondiera `200`, la
    historia tendría dos filas del mismo acto y la primera —la que decidió de verdad— dejaría
    de ser distinguible de un reintento.
    """
    from app.audit.models import AuditAction

    ajeno = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif_b"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert ajeno.status_code in (400, 403, 404), ajeno.text
    assert (await _estado_evento(test_database_url, pend["sin_lote"]))[0] is None

    primera = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert primera.status_code == 200, primera.text

    segunda = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "breeder", "reason": "otra vez"})
    assert segunda.status_code == 404, segunda.text

    unidad, _, quien = await _estado_evento(test_database_url, pend["sin_lote"])
    assert unidad == pend["hab_hatchery"], "la segunda clasificación reescribió la cadena"
    assert quien == pend["clasif"]
    filas = await _auditoria(test_database_url, pend["sin_lote"])
    actualizaciones = [f for f in filas if f[0] == AuditAction.UPDATED]
    assert len(actualizaciones) == 1, filas


# ── AC-O3-07 · el rastro dice de dónde a dónde y por qué ─────────────────────

async def test_ac_o3_07_el_rastro_lleva_el_motivo_y_el_actor(http_client, pend,
                                                            test_database_url):
    """`AC-O3-07`. `previous_state='pending'`, `new_state='hatchery'`, el motivo y quién."""
    from app.audit.models import AuditAction

    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert r.status_code == 200, r.text

    filas = await _auditoria(test_database_url, pend["sin_lote"])
    actualizaciones = [f for f in filas if f[0] == AuditAction.UPDATED]
    assert len(actualizaciones) == 1, filas
    _, user_id, company_id, anterior, nuevo, motivo = actualizaciones[0]
    assert user_id == pend["clasif"]
    assert company_id == pend["empresa_a"]
    assert anterior == "pending", anterior
    assert nuevo == "hatchery", nuevo
    assert motivo == MOTIVO, motivo


# ── AC-O3-08 · clasificar sigue sin conceder nada ────────────────────────────

async def test_ac_o3_08_clasificar_por_codigo_no_concede_ni_abre(http_client, pend,
                                                                 test_database_url):
    """`AC-O3-08`. Las unidades efectivas no cambian, y quien no tiene la cadena no lo ve.

    Es la misma comprobación que la primera clasificación ya tenía, sobre el camino nuevo:
    un `business_unit_code` de más no puede ser una puerta de atrás para conceder accesos.
    """
    antes = {uid: await _efectivas(test_database_url, uid)
             for uid in (pend["creador"], pend["clasif"])}

    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert r.status_code == 200, r.text

    despues = {uid: await _efectivas(test_database_url, uid)
               for uid in (pend["creador"], pend["clasif"])}
    assert antes == despues, f"{antes} → {despues}"

    for actor in ("creador", "ajeno"):  # solo reproductora
        detalle = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                                        headers=_token(pend[actor]))
        assert detalle.status_code == 404, f"{actor}: {detalle.text}"
    # ...y quien sí la tiene lo ve: el rechazo de arriba es por la cadena, no por otra cosa.
    detalle = await http_client.get(f"/api/v1/operations/{pend['sin_lote']}",
                                    headers=_token(pend["incub"]))
    assert detalle.status_code == 200, detalle.text


# ── AC-O3-09 · los candidatos ────────────────────────────────────────────────

async def test_ac_o3_09_1_candidatos_solo_lo_habilitado_de_la_empresa(
        http_client, pend, test_database_url):
    """`AC-O3-09`. `{code, name_key}` y nada más; solo lo habilitado y activo de **A**.

    Ofrecer una unidad apagada sería ofrecer un destino que la clasificación rechaza; ofrecer
    una de otra empresa, además, contaría qué tiene configurado el vecino.
    """
    await _habilitar(test_database_url, company_id=pend["empresa_a"],
                     code="broiler", is_enabled=False)
    await _habilitar(test_database_url, company_id=pend["empresa_b"],
                     code="grandparent", is_enabled=True)

    r = await _candidatos(http_client, pend["sin_lote"], pend["clasif"])
    assert r.status_code == 200, r.text
    filas = r.json()
    for fila in filas:
        assert set(fila) == {"code", "name_key"}, f"campo de más: {fila}"
    codigos = [f["code"] for f in filas]
    assert codigos == ["breeder", "hatchery"], codigos
    assert all(f["name_key"] for f in filas), filas


async def test_ac_o3_09_2_candidatos_permiso_y_tenencia(http_client, pend):
    """`AC-O3-09`. El creador no puede listarlos (403) y la empresa B no ve el evento (404)."""
    creador = await _candidatos(http_client, pend["sin_lote"], pend["creador"])
    assert creador.status_code == 403, creador.text

    otra_empresa = await _candidatos(http_client, pend["sin_lote"], pend["clasif_b"])
    assert otra_empresa.status_code == 404, otra_empresa.text


async def test_ac_o3_09_3_candidatos_de_un_evento_que_ya_no_es_pendiente(http_client, pend):
    """`AC-O3-09`. Ya clasificado, `404`: no hay nada que clasificar ni que ofrecer."""
    r = await http_client.post(
        f"/api/v1/operations/{pend['sin_lote']}/classify",
        headers=_token(pend["clasif"]),
        json={"business_unit_code": "hatchery", "reason": MOTIVO})
    assert r.status_code == 200, r.text

    ya = await _candidatos(http_client, pend["sin_lote"], pend["clasif"])
    assert ya.status_code == 404, ya.text
    assert "Registro pendiente no encontrado" in ya.text


async def test_ac_o3_09_4_candidatos_de_un_evento_inexistente(http_client, pend):
    """`AC-O3-09`. Un id que no existe responde lo mismo: `404`, nunca una lista vacía."""
    r = await _candidatos(http_client, 99_999_999, pend["clasif"])
    assert r.status_code == 404, r.text
    assert "Registro pendiente no encontrado" in r.text
