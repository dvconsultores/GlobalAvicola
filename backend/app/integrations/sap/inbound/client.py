"""Cliente SAP HANA READ ONLY — SPEC 005 `§10`, `§11`, `FR-01`…`FR-06`.

`hdbcli` es síncrono y su `threadsafety` es 1: los hilos pueden compartir el módulo, no una
conexión. De ahí las tres decisiones de este fichero:

    cada llamada abre su conexión y su cursor   y los cierra en `finally`, también al fallar
    todo ocurre en `asyncio.to_thread`          el bucle de FastAPI no espera a HANA
    la concurrencia está acotada                un semáforo de hilo, no cientos de conexiones

El cliente no ofrece ejecutar SQL: solo `ping` y `fetch_page(definición del registry)`.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import decimal
import logging
import threading
from typing import Any, Callable

from .errors import ErrorCode, SapInboundError
from .registry import PAGINACION, PING_SQL, REGISTRY, QueryDefinition, render_sql
from .settings import HanaSettings

logger = logging.getLogger("ga.sap.inbound")

#: Códigos del driver → clasificación. Lo que no esté aquí ni se deduzca del texto es interno.
_POR_CODIGO = {
    10: ErrorCode.SAP_AUTH_ERROR,
    258: ErrorCode.SAP_AUTHORIZATION_ERROR,
    259: ErrorCode.SAP_OBJECT_NOT_FOUND,
    257: ErrorCode.SAP_QUERY_CONTRACT_ERROR,
    260: ErrorCode.SAP_QUERY_CONTRACT_ERROR,
    613: ErrorCode.SAP_QUERY_TIMEOUT,
}
_CONEXION = (-10709, -10806, -10807, -10808)
_DNS = ("getaddrinfo", "name or service not known", "cannot resolve", "unknown host",
        "no address associated")
_TLS = ("ssl", "tls", "certificate")


def _normalizar(valor: Any) -> Any:
    """Valor apto para JSON: RAW guarda la respuesta normalizada, no objetos del driver."""
    if valor is None or isinstance(valor, (bool, int, float)):
        return valor
    if isinstance(valor, decimal.Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    if isinstance(valor, (_dt.datetime, _dt.date, _dt.time)):
        return valor.isoformat()
    if isinstance(valor, (bytes, bytearray, memoryview)):
        return bytes(valor).hex()
    return str(valor).rstrip()


class SapHanaReadOnlyClient:
    def __init__(self, cfg: HanaSettings,
                 connect_factory: Callable[..., Any] | None = None) -> None:
        self._cfg = cfg
        self._connect_factory = connect_factory
        self._semaforo = threading.BoundedSemaphore(max(1, int(cfg.max_concurrency)))

    def __repr__(self) -> str:
        return f"<SapHanaReadOnlyClient driver={self._cfg.driver} configured={self._cfg.configured}>"

    # ── API ───────────────────────────────────────────────────────────────────

    async def ping(self) -> dict[str, Any]:
        """`SELECT 1 FROM DUMMY`: la primera consulta contra un sistema real, y la única de humo."""
        opciones = self._cfg.connect_options()
        columnas, filas = await asyncio.to_thread(self._ejecutar, opciones, PING_SQL, {}, 1)
        return dict(zip(columnas, (_normalizar(v) for v in filas[0]))) if filas else {}

    async def fetch_page(self, definition: QueryDefinition, params: dict[str, Any], *,
                         limit: int, offset: int) -> list[dict[str, Any]]:
        """Una página de una definición del registry. Los valores viajan como bind."""
        if (not isinstance(definition, QueryDefinition)
                or REGISTRY.get(definition.object_type) is not definition):
            raise SapInboundError(ErrorCode.SAP_QUERY_CONTRACT_ERROR,
                                  "Solo se ejecutan definiciones del query registry.")
        esperados = set(definition.required_params) | set(definition.optional_params)
        recibidos = set(params)
        faltan = set(definition.required_params) - recibidos
        sobran = recibidos - esperados
        if faltan or sobran:
            raise SapInboundError(
                ErrorCode.SAP_QUERY_CONTRACT_ERROR,
                f"Parámetros de {definition.query_id} no conformes "
                f"(faltan: {sorted(faltan)}; no declarados: {sorted(sobran)}).")

        opciones = self._cfg.connect_options()
        sql = render_sql(definition, self._cfg.schema)
        limite = max(1, min(int(limit), definition.max_page_size))
        binds = {k: params[k] for k in esperados if k in params}
        binds[PAGINACION[0]] = limite
        binds[PAGINACION[1]] = max(0, int(offset))

        columnas, filas = await asyncio.to_thread(self._ejecutar, opciones, sql, binds, limite)

        ausentes = [c for c in definition.required_columns if c not in columnas]
        if ausentes:
            raise SapInboundError(
                ErrorCode.SAP_SCHEMA_MISMATCH,
                f"{definition.query_id}: la respuesta no trae columnas obligatorias: "
                + ", ".join(ausentes))
        return [{c: _normalizar(v) for c, v in zip(columnas, fila)
                 if c in definition.expected_columns} for fila in filas]

    # ── Interno (se ejecuta en un hilo, nunca en el bucle) ────────────────────

    def _fabrica(self) -> Callable[..., Any]:
        if self._connect_factory is not None:
            return self._connect_factory
        try:
            from hdbcli import dbapi  # import lazy: el backend arranca sin el driver
        except Exception as exc:  # noqa: BLE001
            raise SapInboundError(
                ErrorCode.SAP_DRIVER_UNAVAILABLE,
                f"El driver hdbcli no está disponible: {type(exc).__name__}.") from None
        return dbapi.connect

    def _ejecutar(self, opciones: dict[str, Any], sql: str, binds: dict[str, Any],
                  limite: int) -> tuple[list[str], list[tuple]]:
        conexion = cursor = None
        with self._semaforo:
            try:
                conexion = self._fabrica()(**opciones)
                cursor = conexion.cursor()
                if hasattr(cursor, "setquerytimeout"):
                    cursor.setquerytimeout(int(self._cfg.query_timeout))
                cursor.execute(sql, binds)
                columnas = [d[0] for d in (cursor.description or ())]
                return columnas, list(cursor.fetchmany(limite))
            except SapInboundError:
                raise
            except Exception as exc:  # noqa: BLE001 — todo fallo del driver se clasifica
                raise self._clasificar(exc) from None
            finally:
                for recurso in (cursor, conexion):
                    if recurso is not None:
                        try:
                            recurso.close()
                        except Exception:  # noqa: BLE001
                            pass

    def _clasificar(self, exc: Exception) -> SapInboundError:
        codigo = getattr(exc, "errorcode", None)
        texto = str(getattr(exc, "errortext", None) or exc)
        minusculas = texto.lower()
        if codigo in _POR_CODIGO:
            clase = _POR_CODIGO[codigo]
        elif any(p in minusculas for p in _DNS):
            clase = ErrorCode.SAP_DNS_ERROR
        elif any(p in minusculas for p in _TLS):
            clase = ErrorCode.SAP_TLS_ERROR
        elif "timeout" in minusculas or "timed out" in minusculas:
            clase = ErrorCode.SAP_QUERY_TIMEOUT
        elif codigo in _CONEXION or isinstance(exc, (ConnectionError, OSError)):
            clase = ErrorCode.SAP_TEMPORARY_UNAVAILABLE
        else:
            clase = ErrorCode.SAP_INTERNAL_ERROR
        secretos = (*self._cfg.secrets(), self._cfg.user, self._cfg.host)
        error = SapInboundError(clase, f"[{codigo}] {texto}", secretos=secretos)
        logger.warning("SAP HANA %s: %s", clase.value, error.message)
        return error
