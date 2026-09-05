"""Saldo de apertura como fuente del balance de aves — `GA-REM-005`, enmienda `R-67`.

Cubre `AC-R67-01`…`AC-R67-12`.

El defecto: `POST /lots/activate-manual` guardaba la población del lote y
`get_current_bird_balance` no la consultaba, de modo que un lote incorporado quedaba con
saldo 0 y `BR-01` le rechazaba toda mortalidad, descarte y salida. Como la activación
manual es el mecanismo previsto para incorporar lotes ya en marcha al instalar el sistema
(`docs/02 §3.9`), el efecto recaía justo sobre el primer cliente real.

Todos los escenarios crean sus propias precondiciones. Ninguno se apoya en el lote
sembrado, que ya tiene historia y mediría otra cosa.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# SQLAlchemy configura todos los mappers de golpe.
import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.lots.models import LotPhase, OpeningBalance
from app.masters.models import Lot, ProductivePhase
from app.operations.validators import get_current_bird_balance
from tests.time_reference import days_ago, iso_days_ago, recent_event_date, reference_today

PREFIJO = "OB-TEST-"

MACHOS = 1_000
HEMBRAS = 4_000
APERTURA = MACHOS + HEMBRAS


@pytest_asyncio.fixture
async def motor(test_database_url):
    """Motor de la suite. Su desmontaje retira **todo** lo que el escenario creó.

    La limpieza vive aquí, y no repartida entre fixtures, porque el orden importa: las
    fases productivas y los lotes tienen dependientes (`audit_logs`, `opening_balances`)
    que deben borrarse antes. Este fixture es el último en desmontarse.
    """
    e = create_async_engine(test_database_url)
    yield e

    from app.audit.models import AuditLog
    from app.operations.models import BirdMovement, OperationalEvent

    async with e.begin() as c:
        ids = (
            await c.execute(select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))
        ).scalars().all()
        if ids:
            eventos = (
                await c.execute(
                    select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(ids))
                )
            ).scalars().all()
            if eventos:
                await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        # Después de los lotes: las fases que el escenario tuvo que crear.
        await c.execute(delete(ProductivePhase).where(ProductivePhase.code.like(f"{PREFIJO}%")))
    await e.dispose()


@pytest_asyncio.fixture
async def fase_inicial(motor):
    """Fase productiva inicial. Se crea si no existe: el escenario no supone nada.

    La siembra de la suite no crea fases productivas, así que dar por hecho que hay una
    convertiría este test en una prueba de la siembra y no del saldo de apertura. Su
    retirada la hace `motor`, que se desmonta después.
    """
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        fase = (
            await s.execute(select(ProductivePhase).where(ProductivePhase.is_initial.is_(True)))
        ).scalars().first()
        if fase is not None:
            return fase.id

        creada = ProductivePhase(
            name=f"{PREFIJO}Cría", code=f"{PREFIJO}CRIA", order=1,
            duration_days=140, is_initial=True, is_final=False,
        )
        s.add(creada)
        await s.commit()
        await s.refresh(creada)
        return creada.id


async def _crear_lote(client, auth_headers, seeded_ids) -> int:
    """Lote nuevo y sin historia. Sus precondiciones son suyas."""
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:10]}"
    r = await client.post(
        "/api/v1/lots",
        headers=auth_headers,
        json={
            "company_id": seeded_ids["company_id"],
            "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"],
            "lot_code": codigo,
            "bird_type": "breeder",
            "sex": "mixed",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _activar(client, auth_headers, lot_id, fase, **extra):
    cuerpo = {
        "lot_id": lot_id,
        "activation_date": iso_days_ago(60),
        "phase_at_activation_id": fase,
        "initial_male_count": MACHOS,
        "initial_female_count": HEMBRAS,
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots/activate-manual", headers=auth_headers, json=cuerpo)


async def _saldo(motor, lot_id: int) -> int:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return await get_current_bird_balance(s, lot_id)


def _hoy() -> str:
    """Fecha de hoy.

    `BR-06` exige que el evento no preceda a la activación del lote, y un lote recién
    creado arranca hoy. Los escenarios que **no** activan manualmente deben registrar sus
    eventos con la fecha de hoy; los que sí activan retrasan el inicio 60 días y pueden
    usar fechas recientes.
    """
    return reference_today().isoformat()


async def _mortalidad(client, auth_headers, seeded_ids, lot_id, cantidad, fecha=None):
    return await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "lot_id": lot_id,
            "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"],
            "event_type": "mortality_recording",
            "event_date": fecha or recent_event_date(),
            "bird_movements": [{"sex": "male", "quantity": cantidad}],
        },
    )


# ── AC-R67-01 / 02 ────────────────────────────────────────────────────────────

async def test_t_067_01_la_activacion_produce_saldo_inmediato(
    client, auth_headers, seeded_ids, motor, fase_inicial
):
    """`AC-R67-01` · activar con N produce saldo N; y `AC-R67-02` sin inventar historia."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    assert await _saldo(motor, lot_id) == 0, "un lote recién creado no tiene saldo"

    r = await _activar(client, auth_headers, lot_id, fase_inicial)
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == APERTURA

    # `AC-R67-02`: el saldo no se establece fabricando un evento histórico falso.
    from app.operations.models import OperationalEvent

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        eventos = (
            await s.execute(select(OperationalEvent.id).where(OperationalEvent.lot_id == lot_id))
        ).scalars().all()
    assert eventos == [], "la activación manual no debe crear ningún evento operativo"


# ── AC-R67-03 · la mortalidad posterior descuenta ─────────────────────────────

async def test_t_067_02_la_mortalidad_reduce_el_saldo(
    client, auth_headers, seeded_ids, motor, fase_inicial
):
    """`AC-R67-03` y `AC-R67-09` · `BR-01` acepta la mortalidad y el saldo baja."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    await _activar(client, auth_headers, lot_id, fase_inicial)

    r = await _mortalidad(client, auth_headers, seeded_ids, lot_id, 10)
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == APERTURA - 10


# ── AC-R67-09 · BR-01 con el saldo correcto ───────────────────────────────────

async def test_t_067_03_br01_rechaza_por_encima_del_saldo(
    http_client, auth_headers, seeded_ids, motor, fase_inicial, client
):
    """`AC-R67-09` · una mortalidad mayor que el saldo de apertura se rechaza con su cifra."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    await _activar(client, auth_headers, lot_id, fase_inicial)

    r = await _mortalidad(http_client, auth_headers, seeded_ids, lot_id, APERTURA + 1)
    assert r.status_code == 400, r.text
    cuerpo = r.json()
    assert cuerpo.get("rule") == "BR-01"
    assert str(APERTURA) in cuerpo["detail"], (
        f"el mensaje debe indicar el saldo real: {cuerpo['detail']}"
    )
    assert await _saldo(motor, lot_id) == APERTURA


# ── AC-R67-04 · las entradas posteriores suman ────────────────────────────────

async def test_t_067_04_una_recepcion_posterior_suma(
    client, auth_headers, seeded_ids, motor, fase_inicial
):
    """`AC-R67-04` · las aves recibidas después son aves nuevas y se suman."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    await _activar(client, auth_headers, lot_id, fase_inicial)

    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "lot_id": lot_id,
            "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"],
            "event_type": "bird_reception",
            "event_date": recent_event_date(),
            "bird_movements": [{"sex": "male", "quantity": 500}],
        },
    )
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == APERTURA + 500


# ── AC-R67-05 · sin doble conteo ──────────────────────────────────────────────

async def test_t_067_05_los_acumulados_no_se_restan(
    client, auth_headers, seeded_ids, motor, fase_inicial
):
    """`AC-R67-05` · `accumulated_*` es histórico y no toca el saldo (`RR-08`).

    Restarlos sería el doble conteo que `docs/02 §3.9.2` prohíbe: la mortalidad previa a la
    implantación ya está descontada de los saldos iniciales que el usuario declara.
    """
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    r = await _activar(
        client, auth_headers, lot_id, fase_inicial,
        accumulated_mortality_male=300,
        accumulated_mortality_female=700,
        accumulated_culls_male=50,
        accumulated_culls_female=60,
    )
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == APERTURA, (
        "el histórico acumulado no puede descontarse del saldo de apertura"
    )


async def test_t_067_06_no_se_activa_un_lote_con_historia(
    http_client, auth_headers, seeded_ids, motor, fase_inicial, client
):
    """`AC-R67-05` · activar un lote que ya opera contaría dos veces las mismas aves.

    `docs/02 §3.9.2` exige «Se evita doble conteo» y nada lo implementaba.
    """
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    recepcion = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "lot_id": lot_id,
            "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"],
            "event_type": "bird_reception",
            "event_date": _hoy(),
            "bird_movements": [{"sex": "male", "quantity": 800}],
        },
    )
    assert recepcion.status_code == 201, recepcion.text

    r = await _activar(http_client, auth_headers, lot_id, fase_inicial)
    assert r.status_code == 409, r.text
    assert "dos veces" in r.json()["detail"]
    assert await _saldo(motor, lot_id) == 800, "el saldo no debe haberse alterado"


# ── AC-R67-06 · el flujo normal no cambia ─────────────────────────────────────

async def test_t_067_07_lote_normal_sin_apertura_no_cambia(
    client, auth_headers, seeded_ids, motor
):
    """`AC-R67-06` · un lote creado por el flujo normal se comporta igual que antes."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    assert await _saldo(motor, lot_id) == 0

    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "lot_id": lot_id,
            "farm_id": seeded_ids["farm_id"],
            "house_id": seeded_ids["house_id"],
            "event_type": "bird_reception",
            "event_date": _hoy(),
            "bird_movements": [{"sex": "female", "quantity": 2_000}],
        },
    )
    assert await _saldo(motor, lot_id) == 2_000

    r = await _mortalidad(client, auth_headers, seeded_ids, lot_id, 25, fecha=_hoy())
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == 1_975


async def test_t_067_08_el_lote_sembrado_conserva_su_saldo(motor, seeded_ids):
    """`AC-R67-06` · sin saldo de apertura, el cálculo es exactamente el de antes."""
    lot_id = seeded_ids["lot_id"]
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        apertura = (
            await s.execute(select(OpeningBalance.id).where(OpeningBalance.lot_id == lot_id))
        ).scalar_one_or_none()
        saldo = await get_current_bird_balance(s, lot_id)
    assert apertura is None, "el lote sembrado no debe tener saldo de apertura"
    assert saldo >= 0


# ── AC-R67-08 / AC-R67-10 ─────────────────────────────────────────────────────

async def test_t_067_09_saldo_de_apertura_cero(
    http_client, auth_headers, seeded_ids, motor, fase_inicial, client
):
    """`AC-R67-08` · un saldo de apertura de 0 es válido y `BR-01` rechaza coherentemente."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    r = await _activar(
        client, auth_headers, lot_id, fase_inicial,
        initial_male_count=0, initial_female_count=0,
    )
    assert r.status_code == 201, r.text
    assert await _saldo(motor, lot_id) == 0

    rechazo = await _mortalidad(http_client, auth_headers, seeded_ids, lot_id, 1)
    assert rechazo.status_code == 400
    assert rechazo.json().get("rule") == "BR-01"


async def test_t_067_10_la_auditoria_de_la_activacion_se_conserva(
    client, auth_headers, seeded_ids, motor, fase_inicial
):
    """`AC-R67-10` · la activación sigue siendo auditable: quién, cuándo y con qué datos."""
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    await _activar(client, auth_headers, lot_id, fase_inicial)

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        ob = (
            await s.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lot_id))
        ).scalar_one()
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()

    assert ob.is_manual_activation is True
    assert ob.activated_by_id is not None
    assert ob.activation_reason
    assert ob.activation_date == days_ago(60)
    assert lote.activation_type == "manual"
    # `lot.start_date` es un instante con zona: comparar su `.date()` en UTC contra una
    # fecha local falla por el desfase horario. La fecha normativa es `activation_date`,
    # que es una columna `Date`.
    assert lote.start_date is not None


# ── AC-R67-11 · aislamiento entre empresas ────────────────────────────────────

async def test_t_067_11_no_se_activa_un_lote_ajeno(
    http_client, seeded_ids, fase_inicial, client, auth_headers, motor
):
    """`AC-R67-11` · una empresa no puede activar manualmente el lote de otra.

    El lote se crea en la empresa A dentro de la propia prueba, de modo que su
    identificador es nuevo y no puede coincidir con restos de nadie.
    """
    from app.auth.security import create_access_token

    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    ajeno = {
        "Authorization": "Bearer "
        + create_access_token(data={"sub": str(seeded_ids["user_other_company_id"])})
    }

    r = await _activar(http_client, ajeno, lot_id, fase_inicial)
    assert r.status_code in (400, 403, 404), (
        f"una empresa ajena obtuvo {r.status_code} al activar un lote que no es suyo"
    )
    assert await _saldo(motor, lot_id) == 0, "no debe haberse creado saldo de apertura"


async def test_t_067_12_el_permiso_no_es_lo_unico_que_protege(
    http_client, seeded_ids, fase_inicial, client, auth_headers, motor
):
    """`AC-R67-11` · lo que impide activar un lote ajeno es la **pertenencia**, no el permiso.

    Sin esta comprobación el test anterior sería engañoso: el usuario de la empresa B
    carece de `lots:create`, así que recibía un 403 por una razón que no tiene nada que ver
    con el aislamiento. Aquí se le concede el permiso y debe seguir sin poder.
    """
    from sqlalchemy import select as _select

    from app.auth.models import Permission, PermissionAction, User
    from app.auth.security import create_access_token

    lot_id = await _crear_lote(client, auth_headers, seeded_ids)

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        usuario = (
            await s.execute(
                _select(User).where(User.id == seeded_ids["user_other_company_id"])
            )
        ).scalar_one()
        concedido = Permission(
            role_id=usuario.role_id, module="lots",
            action=PermissionAction.CREATE, scope_type="all",
        )
        s.add(concedido)
        await s.commit()
        await s.refresh(concedido)
        permiso_id = concedido.id

    try:
        ajeno = {
            "Authorization": "Bearer "
            + create_access_token(data={"sub": str(seeded_ids["user_other_company_id"])})
        }
        r = await _activar(http_client, ajeno, lot_id, fase_inicial)
        assert r.status_code != 201, (
            "con el permiso concedido, la pertenencia dejó pasar la activación de un lote ajeno"
        )
        assert r.status_code in (400, 403, 404), r.text
        assert await _saldo(motor, lot_id) == 0
    finally:
        async with fabrica() as s:
            await s.execute(
                Permission.__table__.delete().where(Permission.id == permiso_id)
            )
            await s.commit()
