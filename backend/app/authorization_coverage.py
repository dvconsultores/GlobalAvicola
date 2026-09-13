"""Cobertura de autorización — `GA-REM-002 AC08`.

Toda ruta de `/api/v1` debe declarar explícitamente el permiso que exige, o figurar en la
lista de rutas públicas con su motivo. Una ruta que no haga ninguna de las dos cosas
**impide el arranque**.

La regla no es formalismo. Antes de la Wave 2 las 78 rutas del backend se limitaban a
comprobar que hubiera sesión: cualquier usuario autenticado podía aprobar, exportar a SAP
o desactivar maestros, y el único control efectivo era que la interfaz no mostrara el
botón. Un olvido en una ruta nueva reproduce ese estado en silencio; esta comprobación
convierte el olvido en un fallo de arranque.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute

# Rutas **sin sesión**: cualquiera puede llamarlas. Es la lista que debe permanecer corta,
# porque cada entrada es superficie expuesta a internet.
RUTAS_PUBLICAS: dict[str, str] = {
    "/health": "sonda de disponibilidad, sin datos",
    "/api/v1/login": "es cómo se obtiene la sesión",
    "/api/v1/refresh": "renueva la sesión; se valida el token de refresco",
    "/openapi.json": "documentación",
    "/docs": "documentación",
    "/docs/oauth2-redirect": "documentación",
    "/redoc": "documentación",
}

# Rutas que **exigen sesión** y autorizan por **titularidad**: no por permiso de módulo, sino
# porque el dato es de quien pregunta.
#
# `GA-REM-038` obligó a separarlas de `RUTAS_PUBLICAS`, donde estaban mezcladas. Meterlas en el
# mismo saco tenía dos consecuencias malas a la vez: `/me` figuraba como «pública» cuando exige
# token, y la guarda que limita las públicas a seis contaba contra ese cupo rutas que no son
# superficie anónima. Separarlas hace la lista pública **más** estricta, no menos: de seis
# entradas de `/api` pasa a dos.
#
# Cada una debe declarar por qué la titularidad basta y **dónde** se impone. Ninguna delega la
# decisión en el frontend.
RUTAS_DE_TITULAR: dict[str, str] = {
    "/api/v1/me": "la identidad del propio titular; `get_current_user` la resuelve del token",
    "/api/v1/switch-company": "el servicio valida que la compañía sea suya",
    # `GA-REM-003` · AC04: exige sesión y solo revoca el refresh **del propio
    # titular** — el servicio compara el `sub` del refresh con el actor. Entrar como
    # pública habría roto `AC08b` (la superficie anónima son login y refresh, y son
    # dos): cerrar sesión no es un acto anónimo.
    "/api/v1/logout": "revoca el refresh del propio titular; el servicio compara el `sub`",
    "/api/v1/operations/event-types": "catálogo estático, sin datos de ninguna compañía",
    "/api/v1/users/{user_id}/password": (
        "el titular con su contraseña actual, o un administrador. Lo decide el servicio "
        "(`GA-REM-012`)"
    ),
    # `GA-REM-038` / `OD-07`. La bandeja es de una persona. Un módulo de permiso nuevo lo
    # tendrían que llevar todos los roles que puedan recibir un aviso —hoy dos, mañana otros—,
    # de modo que gatearía por ceremonia mientras la protección real seguiría siendo la misma:
    # `recipient_user_id`. El servicio filtra por destinatario **y** por empresa, y a quien no
    # lo es le responde `404`, no `403`: un `403` confirmaría que hay algo ahí.
    "/api/v1/notifications": "bandeja propia; `service._mias` filtra por destinatario y empresa",
    "/api/v1/notifications/unread-count": "cuenta solo lo propio, con el mismo filtro",
    "/api/v1/notifications/{notification_id}": "propia; a un tercero le responde 404",
    "/api/v1/notifications/{notification_id}/read": "solo el destinatario marca la suya",
}


class AuthorizationCoverageError(RuntimeError):
    """Hay rutas sin decisión de autorización declarada."""


def enumerar_rutas(app: FastAPI) -> list[tuple[str, list[str], APIRoute]]:
    """Aplana las rutas reales de la aplicación, incluidos los routers incluidos."""
    encontradas: list[tuple[str, list[str], APIRoute]] = []

    def recorrer(objetos, prefijo: str = "") -> None:
        for ruta in objetos:
            if isinstance(ruta, APIRoute):
                metodos = sorted(ruta.methods - {"HEAD", "OPTIONS"})
                encontradas.append((prefijo + ruta.path, metodos, ruta))
                continue
            incluido = getattr(ruta, "original_router", None)
            if incluido is not None:
                contexto = getattr(ruta, "include_context", None)
                recorrer(incluido.routes, prefijo + (getattr(contexto, "prefix", "") or ""))

    recorrer(app.routes)
    return encontradas


def permiso_declarado(ruta: APIRoute) -> tuple[str, str] | None:
    """Permiso que exige la ruta, o `None` si no declara ninguno."""
    for dependencia in ruta.dependant.dependencies:
        marca = getattr(dependencia.call, "__ga_permission__", None)
        if marca is not None:
            return marca
    return None


def rutas_sin_autorizacion(app: FastAPI) -> list[str]:
    """Rutas que ni declaran permiso ni figuran como públicas."""
    huerfanas = []
    for camino, metodos, ruta in enumerar_rutas(app):
        if camino in RUTAS_PUBLICAS or camino in RUTAS_DE_TITULAR:
            continue
        if permiso_declarado(ruta) is None:
            huerfanas.append(f"{'/'.join(metodos)} {camino}")
    return sorted(huerfanas)


def verificar(app: FastAPI) -> None:
    """Aborta el arranque si alguna ruta no ha decidido su autorización."""
    huerfanas = rutas_sin_autorizacion(app)
    if huerfanas:
        raise AuthorizationCoverageError(
            "Rutas sin permiso declarado ni motivo de exención "
            f"({len(huerfanas)}):\n  " + "\n  ".join(huerfanas)
            + "\n\nDeclare el permiso con `require_permission(modulo, accion)` o añada la "
              "ruta a `RUTAS_PUBLICAS` (sin sesión) o a `RUTAS_DE_TITULAR` (autoriza la\n"
              "titularidad) con su motivo."
        )
