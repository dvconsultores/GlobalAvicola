"""Clasificación de rutas por su relación con la unidad de negocio.

`GA-REM-040` `T-040-06` y `T-040-07` · `AC-C15`.

Toda ruta autenticada declara a qué se enfrenta, y **la que no lo declare impide el arranque**.
Es la misma idea que `authorization_coverage`: un olvido en una ruta nueva reproduce el estado
anterior en silencio, y esto lo convierte en un fallo ruidoso.

**Clasificar no es proteger.** Que `/api/v1/lots` figure aquí como `MULTI_UNIDAD` no significa
que sus filas estén acotadas: significa que sabemos que hay que acotarlas. El filtro por fila es
la fase 3, y hasta entonces devuelve lotes de todas las unidades de la empresa.

La clave es el **camino**, no el método. Un `GET` y un `POST` sobre `/api/v1/lots` se enfrentan a
la misma cadena productiva; lo que cambia entre ellos es el permiso, y de eso ya se ocupa `RBAC`.
"""
from __future__ import annotations

import enum
from collections import defaultdict

from fastapi import FastAPI

from ..authorization_coverage import enumerar_rutas


class Alcance(str, enum.Enum):
    """Las cinco clases de `GA-REM-040` enmienda B, más la superficie anónima."""

    PUBLICA = "PUBLICA"            # sin sesión; ya la gobierna `authorization_coverage`
    CORE = "CORE"                  # autenticada y ajena a toda unidad
    CONTROL = "CONTROL"            # plano de control de la empresa (`OD-09.b`)
    UNIDAD_UNICA = "UNIDAD_UNICA"  # pertenece a una cadena concreta
    MULTI_UNIDAD = "MULTI_UNIDAD"  # puede tocar varias; sus filas, la fase 3
    CONTRATO = "CONTRATO"          # traspaso entre unidades; sus campos, la fase 5


class AlcanceNoDeclarado(RuntimeError):
    """Hay rutas sin alcance de unidad de negocio declarado."""


#: Maestros, por su recurso. La clasificación **no se inventa aquí**: viene de
#: `audit/remediation/MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX.md`, donde los veintidós se
#: clasificaron por alcance semántico del dato y no por dónde está el menú.
MAESTROS: dict[str, tuple[Alcance, str | None, str]] = {
    "companies": (Alcance.CONTROL, None, "el inquilino mismo"),
    "areas": (Alcance.CONTROL, None, "organigrama de la empresa (`GA-REM-039`)"),
    "productive-phases": (Alcance.CORE, None, "invariante del dominio, sin empresa"),
    "farms": (Alcance.MULTI_UNIDAD, None, "una granja aloja galpones de varias unidades"),
    "houses": (Alcance.MULTI_UNIDAD, None, "hereda de la granja"),
    "hatcheries": (Alcance.UNIDAD_UNICA, "hatchery", "su razón de ser es incubar"),
    "incubators": (Alcance.UNIDAD_UNICA, "hatchery", "vía incubadora"),
    "hatchers": (Alcance.UNIDAD_UNICA, "hatchery", "vía incubadora"),
    "processing-plants": (Alcance.UNIDAD_UNICA, "broiler", "destino del engorde"),
    "breeds": (Alcance.MULTI_UNIDAD, None, "lleva `bird_type`; la fila dice de cuál es"),
    "genetic-lines": (Alcance.MULTI_UNIDAD, None, "una línea cruza la cadena entera"),
    "weight-curves": (Alcance.MULTI_UNIDAD, None, "cuelgan de la línea genética"),
    "feed-types": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
    "vaccines": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
    "medications": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
    "mortality-causes": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
    "cull-causes": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
    "transports": (Alcance.MULTI_UNIDAD, None, "el mismo camión sirve a varias"),
    "rejection-reasons": (Alcance.MULTI_UNIDAD, None, "del flujo de revisión"),
    "correction-types": (Alcance.MULTI_UNIDAD, None, "del flujo de corrección"),
    "suppliers": (Alcance.MULTI_UNIDAD, None, "transversal a la empresa"),
}

#: El resto, por camino exacto. Cada entrada es una decisión, no un patrón que se hereda.
RUTAS: dict[str, tuple[Alcance, str | None, str]] = {
    # ── Sin sesión ────────────────────────────────────────────────────────────
    "/api/v1/login": (Alcance.PUBLICA, None, "es cómo se obtiene la sesión"),
    "/api/v1/refresh": (Alcance.PUBLICA, None, "renueva la sesión"),
    # ── Identidad y contexto ──────────────────────────────────────────────────
    "/api/v1/me": (Alcance.CORE, None, "la identidad del titular"),
    "/api/v1/switch-company": (
        Alcance.CORE, None,
        "fija el CONTEXTO de empresa, que no es acceso a unidad (`OD-11 §5`)"),
    # ── Plano de control ──────────────────────────────────────────────────────
    "/api/v1/users": (Alcance.CONTROL, None, "administrar el acceso, `OD-09.b`"),
    "/api/v1/users/{user_id}": (Alcance.CONTROL, None, "administrar el acceso"),
    "/api/v1/users/{user_id}/password": (Alcance.CONTROL, None, "credencial, no producción"),
    "/api/v1/roles": (Alcance.CONTROL, None, "`RBAC`, no unidad"),
    "/api/v1/roles/{role_id}": (Alcance.CONTROL, None, "`RBAC`, no unidad"),
    "/api/v1/roles/permissions-catalog": (Alcance.CONTROL, None, "catálogo de permisos"),
    # `GA-REM-040` fase 7. Administrar el acceso por unidad **es** plano de control, y por eso
    # no se filtra por unidad: si administrar Incubadora exigiera tener Incubadora, nadie
    # podría concederla la primera vez y la capacidad sería inservible (`OD-09.b`).
    "/api/v1/business-units": (
        Alcance.CONTROL, None, "configuración de la empresa, no producción"),
    "/api/v1/business-units/{code}/enable": (Alcance.CONTROL, None, "habilitar, `T-040-18`"),
    "/api/v1/business-units/{code}/disable": (Alcance.CONTROL, None, "deshabilitar"),
    "/api/v1/business-units/{code}/grant-candidates": (
        Alcance.CONTROL, None, "a quién conceder, sin `users:read` · `R-129`"),
    "/api/v1/users/{user_id}/business-units": (
        Alcance.CONTROL, None, "conceder y consultar el acceso, `T-040-19`"),
    "/api/v1/users/{user_id}/business-units/{code}": (
        Alcance.CONTROL, None, "revocar el acceso"),
    # ── CORE ──────────────────────────────────────────────────────────────────
    "/api/v1/operations/event-types": (Alcance.CORE, None, "catálogo estático"),
    "/api/v1/notifications": (
        Alcance.CORE, None,
        "el canal es CORE; **qué** avisa se filtra en la fase 10 (`OD-09.a`)"),
    "/api/v1/notifications/unread-count": (Alcance.CORE, None, "cuenta la bandeja propia"),
    "/api/v1/notifications/{notification_id}": (Alcance.CORE, None, "bandeja propia"),
    "/api/v1/notifications/{notification_id}/read": (Alcance.CORE, None, "bandeja propia"),
    # ── Auditoría · CORE con visibilidad de control (`OD-09.a`) ───────────────
    "/api/v1/audit": (Alcance.CORE, None, "historia; su visibilidad la decide `BU-D03`"),
    "/api/v1/audit/{log_id}": (Alcance.CORE, None, "ídem"),
    "/api/v1/audit/timeline/{entity_type}/{entity_id}": (Alcance.CORE, None, "ídem"),
    # ── Operación · multi-unidad ──────────────────────────────────────────────
    "/api/v1/lots": (Alcance.MULTI_UNIDAD, None, "el lote lleva su cadena; filas en fase 3"),
    "/api/v1/lots/{lot_id}": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/lots/{lot_id}/close": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/lots/{lot_id}/opening-balance": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/lots/{lot_id}/phases": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/lots/activate-manual": (Alcance.MULTI_UNIDAD, None, "`P-11`, las cuatro"),
    "/api/v1/operations": (Alcance.MULTI_UNIDAD, None, "el evento hereda la del lote"),
    "/api/v1/operations/{event_id}": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/operations/{event_id}/submit": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/operations/{event_id}/cancel": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/operations/{event_id}/evidences": (Alcance.MULTI_UNIDAD, None, "del evento"),
    "/api/v1/operations/{event_id}/evidences/{evidence_id}": (
        Alcance.MULTI_UNIDAD, None, "del evento"),
    "/api/v1/operations/{event_id}/evidences/{evidence_id}/download": (
        Alcance.MULTI_UNIDAD, None, "del evento"),
    "/api/v1/operations/{event_id}/weight-evaluation": (
        Alcance.MULTI_UNIDAD, None, "del lote del evento"),
    "/api/v1/operations/alerts": (Alcance.MULTI_UNIDAD, None, "alertas de sus lotes"),
    # `GA-REM-040` fase 6. La bandeja de pendientes es **plano de control**: decide a qué
    # cadena pertenece un registro, no opera sobre ninguna. Su alcance no es «una unidad»
    # porque lo que la llena es justamente lo que todavía no tiene ninguna.
    "/api/v1/operations/pending-classification": (
        Alcance.CONTROL, None, "bandeja de clasificación pendiente (`OD-10.c`)"),
    "/api/v1/operations/{event_id}/classify": (
        Alcance.CONTROL, None, "acto de configuración, no de operación"),
    "/api/v1/operations/{event_id}/reclassify": (
        Alcance.CONTROL, None, "corrección de alto control (`OD-10.d`)"),
    "/api/v1/operations/alerts/{alert_id}/resolve": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/corrections": (Alcance.MULTI_UNIDAD, None, "corrige eventos de cualquier cadena"),
    "/api/v1/corrections/event/{event_id}": (Alcance.MULTI_UNIDAD, None, "ídem"),
    # ── Reverso interno · `GA-REM-041` · `OD-19` ─────────────────────────────
    "/api/v1/reversals": (Alcance.MULTI_UNIDAD, None, "reversa eventos de cualquier cadena; la contrapartida hereda la del original"),
    "/api/v1/reversals/event/{event_id}": (Alcance.MULTI_UNIDAD, None, "ídem"),
    # ── Revisión y aprobación · `P-07`, flujo 6 ───────────────────────────────
    "/api/v1/review/pending": (Alcance.MULTI_UNIDAD, None, "cola de las cuatro"),
    "/api/v1/review/batches": (Alcance.MULTI_UNIDAD, None, "cola de las cuatro"),
    "/api/v1/review/start/{event_id}": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/review/complete": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/review/return": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approvals/pending": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approvals/approve": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approvals/reject": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approvals/batch-approve": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approvals/batch-reject": (Alcance.MULTI_UNIDAD, None, "ídem"),
    "/api/v1/approval-steps": (Alcance.CONTROL, None, "configura el flujo, no lo ejecuta"),
    "/api/v1/approval-steps/{step_id}": (Alcance.CONTROL, None, "ídem"),
    "/api/v1/approval-steps/seed-defaults": (Alcance.CONTROL, None, "ídem"),
    # ── Agregados · fase 4 ────────────────────────────────────────────────────
    "/api/v1/dashboard/admin": (Alcance.MULTI_UNIDAD, None, "agregado; acotarlo es la fase 4"),
    "/api/v1/dashboard/mobile": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/lot/{lot_id}": (Alcance.MULTI_UNIDAD, None, "del lote"),
    "/api/v1/reports/kpi/ipe/{lot_id}": (Alcance.MULTI_UNIDAD, None, "del lote"),
    "/api/v1/reports/kpi/weight-uniformity/{lot_id}": (Alcance.MULTI_UNIDAD, None, "del lote"),
    "/api/v1/reports/kpis/mortality": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/feed-conversion": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/afcr": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/production-index": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/animal-welfare": (Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/vaccination-efficiency": (
        Alcance.MULTI_UNIDAD, None, "agregado; fase 4"),
    "/api/v1/reports/kpis/egg-production": (
        Alcance.MULTI_UNIDAD, None, "reproductoras y progenitoras; fase 4"),
    "/api/v1/reports/kpis/hatchery": (
        Alcance.UNIDAD_UNICA, "hatchery", "indicadores de incubación"),
    "/api/v1/reports/kpis/transfer-efficiency": (
        Alcance.CONTRATO, None, "mide el traspaso entre cadenas; fase 5"),
    "/api/v1/reports/sap-comparison": (Alcance.CONTRATO, None, "consolidado; flujo 5"),
    # ── Trazabilidad y traspasos · flujos 1, 2, 3, 7 ──────────────────────────
    "/api/v1/lots/egg-batches": (
        Alcance.CONTRATO, None, "entidad de traspaso: origen y destino (`OD-10.a`)"),
    "/api/v1/lots/chick-batches": (Alcance.CONTRATO, None, "entidad de traspaso"),
    "/api/v1/lots/{lot_id}/traceability": (
        Alcance.CONTRATO, None, "`P-10`: la cadena entera, el interior no"),
    # ── SAP · flujo 5, excepción declarada de `OD-09.a` ───────────────────────
    "/api/v1/sap/consolidate": (Alcance.CONTRATO, None, "agrupa las cuatro; `BU-D04`"),
    "/api/v1/sap/consolidated": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/export": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/payloads": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/errors": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/retry": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/sync/jobs": (Alcance.CONTRATO, None, "ídem"),
    "/api/v1/sap/references": (Alcance.CONTROL, None, "configuración de la integración"),
    "/api/v1/sap/references/import": (Alcance.CONTROL, None, "ídem"),
    "/api/v1/sap/connection-check": (Alcance.CONTROL, None, "diagnóstico, sin datos de lote"),
}


def clasificar(camino: str) -> tuple[Alcance, str | None]:
    """Alcance de un camino, y la unidad que exige si es de una sola.

    Devuelve `(None, None)` para lo no declarado: lo desconocido no se clasifica solo.
    """
    if camino in RUTAS:
        alcance, unidad, _ = RUTAS[camino]
        return alcance, unidad
    if camino.startswith("/api/v1/masters/"):
        recurso = camino.split("/")[4]
        if recurso in MAESTROS:
            alcance, unidad, _ = MAESTROS[recurso]
            return alcance, unidad
    return None, None  # type: ignore[return-value]


def unidad_requerida(camino: str) -> str | None:
    """El código de unidad que la ruta exige, o `None` si no es de una sola."""
    return clasificar(camino)[1]


def rutas_sin_clasificar(app: FastAPI) -> list[str]:
    """Rutas bajo `/api` sin alcance declarado. Fuera de `/api` no es superficie de negocio."""
    sin = []
    for camino, metodos, _ in enumerar_rutas(app):
        if not camino.startswith("/api/"):
            continue
        if clasificar(camino)[0] is None:
            sin.append(f"{'/'.join(metodos)} {camino}")
    return sorted(sin)


def inventario(app: FastAPI) -> dict[Alcance, list[str]]:
    """Cuántas rutas hay de cada clase. Para la evidencia, y para verlo de un vistazo."""
    por_clase: dict[Alcance, list[str]] = defaultdict(list)
    for camino, _, _ in enumerar_rutas(app):
        if not camino.startswith("/api/"):
            continue
        alcance = clasificar(camino)[0]
        if alcance is not None:
            por_clase[alcance].append(camino)
    return dict(por_clase)


def verificar(app: FastAPI) -> None:
    """Aborta el arranque si alguna ruta no ha declarado su alcance de unidad."""
    sin = rutas_sin_clasificar(app)
    if sin:
        raise AlcanceNoDeclarado(
            f"Rutas sin alcance de unidad de negocio declarado ({len(sin)}):\n  "
            + "\n  ".join(sin)
            + "\n\nDeclárelo en `app/business_units/route_scope.py`. Clasificar una ruta no "
              "la protege: dice qué habrá que proteger y cuándo."
        )
