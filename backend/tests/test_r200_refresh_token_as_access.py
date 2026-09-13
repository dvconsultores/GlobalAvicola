"""`R-200` · Sólo un access token autentica una petición.

Diseño: `audit/ga-claude-final-audit/specs/R-200/R-200_RED_E2E_UAT_DESIGN.md §1`.

```
get_current_user   payload["type"] == "access"   → continúa
                   cualquier otro valor o ausente → 401 «Token inválido: no es un token de acceso»
```

`RED-01…RED-04` fijan el defecto (rojas en HEAD: el refresh de 7 días —o un JWT
sin `type`— autentica como `Bearer`); `CTL-05…CTL-08` y `DOC-10` son controles
que ya pasan y deben seguir pasando. `GA-REM-003 AC04` (logout/revocación del
refresh) **no** se cierra aquí: esta spec restaura la frontera de 30 minutos del
access.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.auth.security import decode_token
from app.config import settings

pytestmark = pytest.mark.asyncio


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _jwt(claims: dict) -> str:
    """Un JWT firmado con la clave del producto — sin pasar por `create_*_token`."""
    payload = {**claims, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def _par(client, test_credentials) -> tuple[str, str]:
    """Login real: `(access, refresh)`."""
    username, password = test_credentials
    r = await client.post("/api/v1/login",
                          json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"], r.json()["refresh_token"]


async def _cuenta_auditoria(test_database_url: str) -> int:
    """`AC09`: un token del tipo equivocado no deja asiento."""
    motor = create_async_engine(test_database_url)
    try:
        async with motor.connect() as c:
            return int((await c.execute(text("SELECT count(*) FROM audit_logs"))).scalar_one())
    finally:
        await motor.dispose()


# ── RED-01 … RED-04 · el defecto (rojas en HEAD) ─────────────────────────────

async def test_r200_01_un_refresh_token_no_autentica_una_ruta_protegida(
        http_client, test_credentials, test_database_url):
    """`AC01` · `AC09` — el refresh (7 días) no vale como credencial de acceso."""
    _, refresh = await _par(http_client, test_credentials)
    antes = await _cuenta_auditoria(test_database_url)
    r = await http_client.get("/api/v1/me", headers=_bearer(refresh))
    assert r.status_code == 401, r.text
    assert "acceso" in r.json()["detail"].lower()
    assert await _cuenta_auditoria(test_database_url) == antes, (
        "un token inválido dejó asiento de auditoría")


async def test_r200_02_un_refresh_token_no_autentica_una_ruta_con_permiso(
        http_client, test_credentials):
    """`AC02` — 401 (no autenticado), nunca 403: el refresh no llega a autorizar."""
    _, refresh = await _par(http_client, test_credentials)
    r = await http_client.get("/api/v1/users", headers=_bearer(refresh))
    assert r.status_code == 401, r.text
    assert r.status_code != 403


async def test_r200_03_un_token_firmado_sin_tipo_se_rechaza(http_client, seeded_ids):
    """`AC03` — la marca `type` es obligatoria; un JWT firmado sin ella no autentica."""
    t = _jwt({"sub": str(seeded_ids["user_admin_id"])})
    r = await http_client.get("/api/v1/me", headers=_bearer(t))
    assert r.status_code == 401, r.text


async def test_r200_04_un_token_de_tipo_desconocido_se_rechaza(http_client, seeded_ids):
    """`AC04` — sólo `access` autentica; `type: "session"` no."""
    t = _jwt({"sub": str(seeded_ids["user_admin_id"]), "type": "session"})
    r = await http_client.get("/api/v1/me", headers=_bearer(t))
    assert r.status_code == 401, r.text


# ── CTL-05 … CTL-08 · controles (verdes en HEAD y después) ───────────────────

async def test_r200_05_el_access_token_sigue_autenticando(http_client, test_credentials):
    """`AC05` — el camino legítimo no se toca."""
    access, _ = await _par(http_client, test_credentials)
    r = await http_client.get("/api/v1/me", headers=_bearer(access))
    assert r.status_code == 200, r.text
    assert r.json()["username"] == test_credentials[0]


async def test_r200_06_el_flujo_de_renovacion_sigue_intacto(http_client, test_credentials):
    """`AC06` — refresh → par nuevo; el access nuevo autentica."""
    _, refresh = await _par(http_client, test_credentials)
    r = await http_client.post("/api/v1/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200, r.text
    nuevo = r.json()["access_token"]
    me = await http_client.get("/api/v1/me", headers=_bearer(nuevo))
    assert me.status_code == 200, me.text
    assert decode_token(nuevo).get("type") == "access"


async def test_r200_07_un_access_token_sigue_sin_servir_para_refrescar(
        http_client, test_credentials):
    """`AC07` — el sentido inverso ya estaba cerrado (`R-43`); sigue estándolo."""
    access, _ = await _par(http_client, test_credentials)
    r = await http_client.post("/api/v1/refresh", json={"refresh_token": access})
    assert r.status_code == 401, r.text


async def test_r200_08_el_par_de_switch_company_sigue_siendo_valido(
        http_client, test_credentials, seeded_ids):
    """`AC08` — `switch-company` emite un par válido como siempre."""
    access, _ = await _par(http_client, test_credentials)
    r = await http_client.post("/api/v1/switch-company", headers=_bearer(access),
                               json={"company_id": seeded_ids["company_id"]})
    assert r.status_code == 200, r.text
    par = r.json()
    me = await http_client.get("/api/v1/me", headers=_bearer(par["access_token"]))
    assert me.status_code == 200, me.text
    ren = await http_client.post("/api/v1/refresh",
                                 json={"refresh_token": par["refresh_token"]})
    assert ren.status_code == 200, ren.text


# ── DOC-10 · las ventanas quedan fijadas ─────────────────────────────────────

async def test_r200_10_las_ventanas_de_los_dos_tokens_quedan_fijadas(
        http_client, test_credentials):
    """`AC10` — documental: access ≈30 min · refresh ≈7 d (según `settings`).

    Fija la ventana para que un cambio futuro de duración sea visible como rojo.
    """
    access, refresh = await _par(http_client, test_credentials)
    opciones = {"verify_exp": False}
    a = jwt.decode(access, settings.JWT_SECRET_KEY,
                   algorithms=[settings.JWT_ALGORITHM], options=opciones)
    rr = jwt.decode(refresh, settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM], options=opciones)
    ahora = datetime.now(timezone.utc).timestamp()
    assert abs(a["exp"] - ahora - settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60) <= 120
    assert abs(rr["exp"] - ahora - settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400) <= 3600
