"""`GA-UAT-BREEDER-CRIA-S1` · `spec 015 §1` (`D1`) y `§5` — trazabilidad de la inspección de granja.

    LA CADENA SE DERIVA DEL DATO, NO DEL NOMBRE NI DEL ROL;
    LO QUE NO TIENE CADENA INEQUÍVOCA NO SE ATRIBUYE A NINGUNA.

`farm_inspection` sin lote es el único tipo de `LOT_OPTIONAL_EVENTS` que no declaraba su
unidad (`C-02`/`GL-OD-13`): nacía con `business_unit_id = null` y por tanto fuera de
Historial, detalle, Revisión y Aprobaciones — solo visible en la bandeja de pendientes.
`D1` resuelve el hueco con la **opción A**: se deriva la unidad de la **granja** cuando es
inequívoca —todos sus lotes vivos con cadena comparten una sola, y esa unidad está
efectiva para quien opera— y, si no lo es, el evento **nace pendiente** (`GA-REM-040 §11`),
sin inventar una unidad falsa (`AC-S1-T04`).

Contrato:
  AC-S1-T01  granja de **una sola cadena** ⇒ nace con la unidad derivada y aparece en el
             listado operativo normal, con detalle accesible para el autor
  AC-S1-T02  granja **sin lotes** o **multicadena** ⇒ nace pendiente: aparece en la
             bandeja del autor y **no** en el listado normal
  (control)  un lote **cancelado** no compone la cadena de la granja
  D4         el saldo de aves sigue siendo **por total**, no por sexo

El listado normal se consulta acotado por `farm_id`: es el mismo endpoint
(`GET /operations`) y la misma consulta, con el filtro que hace la aserción determinista
frente al volumen de eventos de la base de pruebas.
"""
from __future__ import annotations

import inspect
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "UATS1TR-"


@pytest_asyncio.fixture
async def granjas(test_database_url):
    """Tres granjas de la empresa de pruebas, con composición de lotes **distinta**.

    ```
    Empresa (semilla TEST)
        GRANJA-UNA    lote BREEDER activo + lote BROILER **cancelado**   ⇒ una sola cadena
        GRANJA-SIN    ningún lote                                        ⇒ pendiente
        GRANJA-MULTI  lote BREEDER activo + lote BROILER activo           ⇒ pendiente
    ```

    Las tres viven en la empresa del usuario sembrado (`test_admin`), que tiene las cuatro
    cadenas habilitadas y concedidas: la derivación no se ve estorbada por el alcance y lo
    que se mide es la regla, no la concesión.
    """
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House, Lot,
                                    LotStatus)
    from seeds.test_seeds import TEST_COMPANY_NAME

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        empresa = (await s.execute(
            select(Company).where(Company.name == TEST_COMPANY_NAME))).scalar_one()
        # Los eventos del escenario se limpian por identidad creciente: los crea esta
        # fixture (y sus tests) y ninguno existe antes de ella.
        evento_previo = int((await s.execute(
            text("SELECT coalesce(max(id), 0) FROM operational_events"))).scalar() or 0)

        hab_breeder = (await s.execute(
            select(CompanyBusinessUnit.id)
            .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
            .where(CompanyBusinessUnit.company_id == empresa.id,
                   BusinessUnit.code == "breeder"))).scalar_one()
        hab_hatchery = (await s.execute(
            select(CompanyBusinessUnit.id)
            .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
            .where(CompanyBusinessUnit.company_id == empresa.id,
                   BusinessUnit.code == "hatchery"))).scalar_one()

        def _granja(marca):
            return Farm(company_id=empresa.id, name=f"{PREFIJO}GRANJA-{marca}",
                        code=f"{PREFIJO}G-{marca}", farm_type=FarmType.BREEDING,
                        is_active=True)

        una, sin, multi = _granja("UNA"), _granja("SIN"), _granja("MULTI")
        s.add_all([una, sin, multi])
        await s.flush()

        galpones = {}
        for marca, granja in (("UNA", una), ("SIN", sin), ("MULTI", multi)):
            galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON-{marca}",
                           capacity=5_000, is_active=True)
            s.add(galpon)
            await s.flush()
            galpones[marca] = galpon

        def _lote(granja, marca, tipo, estado=LotStatus.ACTIVE):
            fila = Lot(company_id=empresa.id,
                       lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status=estado, farm_id=granja.id)
            s.add(fila)
            return fila

        _lote(una, "UNA-RE", BirdTypeEnum.BREEDER)
        # Un lote cancelado de **otra** cadena no compone la cadena viva de la granja.
        _lote(una, "UNA-BR-CANCELADO", BirdTypeEnum.BROILER, LotStatus.CANCELLED)
        _lote(multi, "MULTI-RE", BirdTypeEnum.BREEDER)
        _lote(multi, "MULTI-BR", BirdTypeEnum.BROILER)
        await s.flush()
        await s.commit()

        datos = {"compania": empresa.id, "url": test_database_url,
                 "una": una.id, "sin": sin.id, "multi": multi.id, "evento_previo": evento_previo,
                 "galpon_una": galpones["UNA"].id, "galpon_sin": galpones["SIN"].id,
                 "galpon_multi": galpones["MULTI"].id,
                 "hab_breeder": hab_breeder, "hab_hatchery": hab_hatchery}
    yield datos

    eventos = ("SELECT id FROM operational_events "
               "WHERE id > :max AND company_id = :c")
    granjas = "SELECT id FROM farms WHERE name LIKE :p"
    galpones = "SELECT id FROM houses WHERE name LIKE :p"
    async with motor.begin() as c:
        params = {"max": datos["evento_previo"], "c": datos["compania"],
                  "p": f"{PREFIJO}%"}
        for sql in (
            # `audit_logs` referencia granja y galpón: se borra antes que ellos.
            f"DELETE FROM audit_logs WHERE house_id IN ({galpones}) "
            f"OR farm_id IN ({granjas})",
            f"DELETE FROM inspection_details WHERE event_id IN ({eventos})",
            f"DELETE FROM bird_movements WHERE event_id IN ({eventos})",
            f"DELETE FROM hatchery_params WHERE event_id IN ({eventos})",
            "DELETE FROM operational_events WHERE id > :max AND company_id = :c",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE name LIKE :p",
            "DELETE FROM farms WHERE name LIKE :p",
        ):
            await c.execute(text(sql), params)
    await motor.dispose()


def _inspeccion(granja: int, galpon: int, marca: str) -> dict:
    """`farm_inspection` **sin lote**, por granja y galpón (`BR-08`)."""
    return {"event_type": "farm_inspection", "event_date": recent_event_date(),
            "farm_id": granja, "house_id": galpon, "observations": f"{PREFIJO}{marca}"}


async def _unidad_del_evento(url: str, evento: int):
    """`operational_events.business_unit_id` tal como quedó persistido."""
    motor = create_async_engine(url)
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(
                "SELECT business_unit_id FROM operational_events WHERE id = :e"),
                {"e": evento})).scalar()
    finally:
        await motor.dispose()


async def _ids(r) -> set[int]:
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    return {f["id"] for f in filas}


async def _listado_normal(client, headers, granja: int) -> set[int]:
    return await _ids(await client.get("/api/v1/operations",
                                       headers=headers,
                                       params={"limit": 100, "farm_id": granja}))


async def _pendientes(client, headers) -> set[int]:
    return await _ids(await client.get("/api/v1/operations/pending-classification",
                                       headers=headers, params={"limit": 100}))


async def _fila_pendiente(client, headers, evento: int) -> dict:
    """La fila de la bandeja tal como viaja en la respuesta (nombres incluidos)."""
    r = await client.get("/api/v1/operations/pending-classification",
                         headers=headers, params={"limit": 100})
    assert r.status_code == 200, r.text
    filas = r.json()
    filas = filas if isinstance(filas, list) else filas.get("items", [])
    return next(f for f in filas if f["id"] == evento)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-S1-T01 · granja de una sola cadena ⇒ nace con su unidad derivada
# ═══════════════════════════════════════════════════════════════════════════

async def test_t01_granja_de_una_cadena_nace_con_unidad_derivada(auth_headers, client, granjas):
    """`D1` · `spec 015 §5`: la inspección de una granja de una sola cadena **no** queda
    pendiente — se persiste en la unidad de sus lotes (patrón `R-221`).

    Y el lote **cancelado** de otra cadena no impide la derivación: un lote cancelado no
    compone la operación viva de la granja.
    """
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_inspeccion(granjas["una"], granjas["galpon_una"], "UNA"))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    assert r.json()["lot_id"] is None

    unidad = await _unidad_del_evento(granjas["url"], evento)
    assert unidad == granjas["hab_breeder"], (
        "AC-S1-T01: la unidad se deriva de los lotes de la granja (breeder), "
        f"HEAD: {unidad}")

    detalle = await client.get(f"/api/v1/operations/{evento}", headers=auth_headers)
    assert detalle.status_code == 200, detalle.text

    assert evento in await _listado_normal(client, auth_headers, granjas["una"]), (
        "AC-S1-T01: el evento aparece en el listado operativo normal")
    assert evento not in await _pendientes(client, auth_headers), (
        "AC-S1-T01: derivada la unidad, no va a la bandeja de pendientes")


# ═══════════════════════════════════════════════════════════════════════════
#  AC-S1-T02 · sin cadena inequívoca ⇒ pendiente, visible para su autor
# ═══════════════════════════════════════════════════════════════════════════

async def test_t02_granja_sin_lotes_nace_pendiente(auth_headers, client, granjas):
    """Granja sin lotes: no hay cadena que derivar y **no se inventa** una (`AC-S1-T04`)."""
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_inspeccion(granjas["sin"], granjas["galpon_sin"], "SIN"))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    assert await _unidad_del_evento(granjas["url"], evento) is None

    assert evento in await _pendientes(client, auth_headers), (
        "AC-S1-T02: el autor ve su propio pendiente")
    assert evento not in await _listado_normal(client, auth_headers, granjas["sin"]), (
        "AC-S1-T02: el pendiente no se mezcla con el listado operativo normal")

    # `F7` · la bandeja nombra la granja y el galpón: sin nombres el autor no reconocería
    # el registro que debe clasificar.
    fila = await _fila_pendiente(client, auth_headers, evento)
    assert fila["farm_name"] == f"{PREFIJO}GRANJA-SIN", (
        f"F7: la bandeja debe nombrar la granja; HEAD: {fila.get('farm_name')!r}")
    assert fila["house_name"] is not None, "F7: la bandeja debe nombrar el galpón"


async def test_t02_granja_multicadena_nace_pendiente(auth_headers, client, granjas):
    """Dos cadenas vivas en la misma granja: la unidad no es inequívoca."""
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_inspeccion(granjas["multi"], granjas["galpon_multi"], "MULTI"))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]
    assert await _unidad_del_evento(granjas["url"], evento) is None

    assert evento in await _pendientes(client, auth_headers)
    assert evento not in await _listado_normal(client, auth_headers, granjas["multi"])


# ═══════════════════════════════════════════════════════════════════════════
#  Control · el tipo inequívoco previo (`R-221`) sigue naciendo atribuido
# ═══════════════════════════════════════════════════════════════════════════

async def test_control_inspeccion_de_incubadora_sigue_naciendo_atribuida(auth_headers, client, granjas):
    """`R-221` intacto: el cambio de `D1` no toca la derivación por tipo de evento."""
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json={"event_type": "hatchery_inspection",
                                "event_date": recent_event_date(),
                                "hatchery_params": [{"temperature": 37.5}]})
    assert r.status_code == 201, r.text
    assert await _unidad_del_evento(granjas["url"], r.json()["id"]) == granjas["hab_hatchery"]


# ═══════════════════════════════════════════════════════════════════════════
#  D4 · el saldo de aves es por TOTAL, no por sexo
# ═══════════════════════════════════════════════════════════════════════════

async def test_d4_el_saldo_es_por_total_no_por_sexo():
    """`spec 015 §1` `D4`: mortalidad, descarte y salida se miden sobre el **total** vivo.

    Se fija el statu quo para que el saldo por sexo, si algún día se decide, cambie este
    test **a propósito**: ni la firma de la regla recibe el sexo ni su implementación
    consulta el saldo desagregado.
    """
    from app.operations.validators import validate_bird_decrement

    parametros = set(inspect.signature(validate_bird_decrement).parameters)
    assert parametros == {"db", "lot_id", "quantity", "etiqueta"}, (
        f"D4: la regla no distingue sexo; firma actual: {sorted(parametros)}")
    assert "by_sex" not in inspect.getsource(validate_bird_decrement), (
        "D4: el saldo se lee por total, no desagregado por sexo")
