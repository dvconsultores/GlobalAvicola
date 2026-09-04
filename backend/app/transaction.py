"""Frontera transaccional de la petición — `GA-REM-026`, hallazgo `R-68`.

El principio que fija la spec:

    Una respuesta HTTP de éxito para una mutación síncrona no puede enviarse antes de que
    la transacción requerida haya sido confirmada satisfactoriamente.

Antes, `get_db` confirmaba en el cierre de la dependencia con `yield`, y FastAPI ejecuta
ese cierre **después** de enviar la respuesta. Medido con una reproducción mínima sobre
FastAPI 0.138 y Starlette 1.3.1, con un commit artificial de 300 ms, la respuesta salía en
1–6 ms y la lectura inmediata no veía el dato. En el sistema real el commit tarda
milisegundos y a veces gana la carrera: de ahí que el defecto fuese intermitente y se
atribuyera a otras causas.

La confirmación pasa aquí, a la capa de ruta, que es el último punto que se ejecuta
**dentro** del manejo de excepciones de FastAPI y **antes** de que la respuesta salga. Eso
da tres cosas a la vez: el dato está confirmado cuando el cliente recibe el `201`; un fallo
al confirmar se convierte en un `500` por el camino normal de errores, en lugar de en un
éxito mentiroso; y el manejo de errores que ya existía —las excepciones se propagan al
generador de `get_db` y revierten— no se toca.

No se modificó ningún servicio. Los 49 `flush()` del proyecto siguen igual: preparan el
trabajo y obtienen los identificadores generados, y la confirmación sigue siendo de la capa
de petición. Lo único que cambia es **cuándo** ocurre.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute


class TransactionCoverageError(RuntimeError):
    """Alguna ruta usa la base de datos fuera de la frontera transaccional."""


class RutaTransaccional(APIRoute):
    """Ruta que confirma la transacción de la petición antes de responder."""

    def get_route_handler(self):
        manejador_original = super().get_route_handler()

        async def manejador(request: Request) -> Response:
            respuesta = await manejador_original(request)

            sesion = getattr(request.state, "db", None)
            # `in_transaction()` evita abrir y cerrar una transacción vacía en las rutas
            # que no llegaron a tocar la base (`AC08`).
            if sesion is not None and sesion.in_transaction():
                try:
                    await sesion.commit()
                except Exception:
                    # La respuesta ya estaba construida, pero no ha salido: al propagar,
                    # el manejo de excepciones de FastAPI la sustituye por un 500. Un
                    # fallo al confirmar no puede terminar en un HTTP de éxito (`AC05`).
                    await sesion.rollback()
                    raise

            return respuesta

        return manejador


def _usa_base_de_datos(dependant) -> bool:
    """¿El árbol de dependencias de la ruta incluye `get_db`?"""
    from .database import get_db

    pendientes = [dependant]
    while pendientes:
        actual = pendientes.pop()
        if actual.call is get_db:
            return True
        pendientes.extend(actual.dependencies)
    return False


def rutas_sin_frontera(app: FastAPI) -> list[str]:
    """Rutas que usan la base de datos sin estar bajo la frontera transaccional."""
    from .authorization_coverage import enumerar_rutas

    huerfanas = []
    for camino, metodos, ruta in enumerar_rutas(app):
        if not _usa_base_de_datos(ruta.dependant):
            continue
        if not isinstance(ruta, RutaTransaccional):
            huerfanas.append(f"{'/'.join(metodos)} {camino}")
    return sorted(huerfanas)


def verificar(app: FastAPI) -> None:
    """Aborta el arranque si alguna ruta usa la base fuera de la frontera.

    Sin esta comprobación, un router nuevo que olvidase `route_class=RutaTransaccional`
    perdería sus escrituras **en silencio**: la petición respondería con éxito y el dato
    no llegaría nunca. Es el mismo razonamiento —y el mismo mecanismo— que
    `authorization_coverage`: convertir un olvido en un fallo de arranque en lugar de en
    un defecto que aparece meses después.
    """
    huerfanas = rutas_sin_frontera(app)
    if huerfanas:
        raise TransactionCoverageError(
            f"Rutas que usan la base fuera de la frontera transaccional ({len(huerfanas)}):"
            "\n  " + "\n  ".join(huerfanas)
            + "\n\nCree su router con `APIRouter(..., route_class=RutaTransaccional)`."
        )
