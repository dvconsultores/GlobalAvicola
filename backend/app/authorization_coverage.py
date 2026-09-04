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

# Rutas sin permiso, con el motivo por el que no pueden tenerlo.
RUTAS_PUBLICAS: dict[str, str] = {
    "/health": "sonda de disponibilidad, sin datos",
    "/api/v1/login": "es cómo se obtiene la sesión",
    "/api/v1/refresh": "renueva la sesión; se valida el token de refresco",
    "/api/v1/me": "devuelve la identidad del propio titular, nada que no tenga ya",
    "/api/v1/switch-company": "el servicio valida que la compañía sea suya",
    "/api/v1/users/{user_id}/password": (
        "la autorización depende de quién pide qué: el titular con su contraseña "
        "actual, o un administrador. La decide el servicio (GA-REM-012)"
    ),
    "/api/v1/operations/event-types": "catálogo estático, sin datos de ninguna compañía",
    "/openapi.json": "documentación",
    "/docs": "documentación",
    "/docs/oauth2-redirect": "documentación",
    "/redoc": "documentación",
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
        if camino in RUTAS_PUBLICAS:
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
              "ruta a `RUTAS_PUBLICAS` con su motivo."
        )
