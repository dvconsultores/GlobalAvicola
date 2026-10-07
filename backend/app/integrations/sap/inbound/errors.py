"""Errores del conector inbound — SPEC 005 `§41`, `FR-13`.

La lista es cerrada: un fallo que no encaje en ninguno es `SAP_INTERNAL_ERROR`, nunca un
código nuevo improvisado. Y el mensaje sale **saneado**: el texto del driver puede traer la
cadena de conexión o la contraseña, y ese texto acaba en un job, en un log y en la pantalla
del analista.
"""
from __future__ import annotations

import enum
import re
from typing import Iterable


class ErrorCode(str, enum.Enum):
    SAP_CONFIG_MISSING = "SAP_CONFIG_MISSING"
    SAP_DRIVER_UNAVAILABLE = "SAP_DRIVER_UNAVAILABLE"
    SAP_DNS_ERROR = "SAP_DNS_ERROR"
    SAP_TLS_ERROR = "SAP_TLS_ERROR"
    SAP_AUTH_ERROR = "SAP_AUTH_ERROR"
    SAP_AUTHORIZATION_ERROR = "SAP_AUTHORIZATION_ERROR"
    SAP_QUERY_TIMEOUT = "SAP_QUERY_TIMEOUT"
    SAP_QUERY_CONTRACT_ERROR = "SAP_QUERY_CONTRACT_ERROR"
    SAP_SCHEMA_MISMATCH = "SAP_SCHEMA_MISMATCH"
    SAP_OBJECT_NOT_FOUND = "SAP_OBJECT_NOT_FOUND"
    SAP_MAPPING_PENDING = "SAP_MAPPING_PENDING"
    SAP_VALIDATION_ERROR = "SAP_VALIDATION_ERROR"
    SAP_TEMPORARY_UNAVAILABLE = "SAP_TEMPORARY_UNAVAILABLE"
    SAP_INTERNAL_ERROR = "SAP_INTERNAL_ERROR"


_REDACTADO = "[REDACTADO]"
#: `clave=valor` y URLs con credenciales, aunque el secreto no se conozca de antemano.
_PATRONES = (
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token)\s*[=:]\s*\S+"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@"),
)
_MAXIMO = 500


def sanitize(texto: object, secretos: Iterable[str] = ()) -> str:
    """Texto apto para persistir y mostrar: sin secretos conocidos ni con forma de secreto."""
    limpio = "" if texto is None else str(texto)
    for secreto in secretos:
        if secreto:
            limpio = limpio.replace(secreto, _REDACTADO)
    limpio = _PATRONES[0].sub(lambda m: f"{m.group(1)}={_REDACTADO}", limpio)
    limpio = _PATRONES[1].sub(f"{_REDACTADO}@", limpio)
    limpio = " ".join(limpio.split())
    return limpio[:_MAXIMO]


class SapInboundError(Exception):
    """Fallo clasificado del conector. Su mensaje ya está saneado."""

    def __init__(self, code: ErrorCode, message: str, *, secretos: Iterable[str] = ()):
        self.code = code
        self.message = sanitize(message, secretos)
        super().__init__(f"{code.value}: {self.message}")

    def __repr__(self) -> str:
        return f"SapInboundError({self.code.value!r}, {self.message!r})"
