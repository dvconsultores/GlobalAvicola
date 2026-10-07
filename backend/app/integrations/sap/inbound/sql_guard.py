"""Guard de solo lectura — SPEC 005 `§15`, `FR-02`.

Es la tercera línea, no la seguridad: antes están el usuario READ ONLY de SAP y el hecho de
que el SQL solo nace en el registry interno. Aun así, si SAP entregara por error un usuario con
privilegios de más, Global Avícola no debe poder aprovecharlos.

Se decide sobre la sentencia **sin comentarios y sin literales**: un `'UPDATE'` dentro de una
cadena no es una mutación, y un comentario no puede esconder una segunda sentencia.
"""
from __future__ import annotations

import re

from .errors import ErrorCode, SapInboundError

#: Palabras que no pueden aparecer como token en una sentencia de lectura.
PROHIBIDAS = frozenset({
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE",
    "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME",
    "GRANT", "REVOKE",
    "CALL", "DO", "EXEC", "EXECUTE",
    "INTO", "SET", "COMMIT", "ROLLBACK", "LOCK", "UNLOAD", "IMPORT", "EXPORT", "LOAD",
})
_INICIOS = ("SELECT", "WITH")
_PALABRA = re.compile(r"[A-Za-z_][A-Za-z0-9_$#]*")


def _despojar(sql: str) -> str:
    """Quita comentarios y vacía literales e identificadores entrecomillados.

    Recorre carácter a carácter para respetar el orden real: un `--` dentro de un literal no
    abre un comentario y una comilla dentro de un comentario no abre un literal.
    """
    salida: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        siguiente = sql[i + 1] if i + 1 < n else ""
        if c == "-" and siguiente == "-":
            fin = sql.find("\n", i)
            i = n if fin == -1 else fin
            salida.append(" ")
        elif c == "/" and siguiente == "*":
            fin = sql.find("*/", i + 2)
            if fin == -1:
                raise SapInboundError(ErrorCode.SAP_QUERY_CONTRACT_ERROR,
                                      "Comentario sin cerrar en la sentencia.")
            i = fin + 2
            salida.append(" ")
        elif c in ("'", '"'):
            j = i + 1
            while True:
                fin = sql.find(c, j)
                if fin == -1:
                    raise SapInboundError(ErrorCode.SAP_QUERY_CONTRACT_ERROR,
                                          "Literal o identificador sin cerrar en la sentencia.")
                if fin + 1 < n and sql[fin + 1] == c:   # comilla escapada por duplicación
                    j = fin + 2
                    continue
                break
            i = fin + 1
            salida.append(c + c)
        else:
            salida.append(c)
            i += 1
    return "".join(salida)


def _rechazar(motivo: str) -> None:
    raise SapInboundError(ErrorCode.SAP_QUERY_CONTRACT_ERROR,
                          f"Sentencia rechazada por el guard de solo lectura: {motivo}.")


def assert_read_only(sql: str) -> str:
    """Devuelve la sentencia si es **una** lectura; en cualquier otro caso, falla."""
    if not isinstance(sql, str) or not sql.strip():
        _rechazar("sentencia vacía")
    esqueleto = _despojar(sql).strip()
    if not esqueleto:
        _rechazar("sentencia vacía")
    if ";" in esqueleto:
        _rechazar("más de una sentencia")

    palabras = [p.upper() for p in _PALABRA.findall(esqueleto)]
    if not palabras or palabras[0] not in _INICIOS:
        _rechazar("debe iniciar en SELECT o WITH")
    mutantes = sorted(set(palabras) & PROHIBIDAS)
    if mutantes:
        _rechazar("contiene " + ", ".join(mutantes))
    if "FOR" in palabras:
        # `FOR UPDATE` ya cae por UPDATE; se cierra también `FOR SHARE LOCK` y afines.
        siguiente = palabras[palabras.index("FOR") + 1:palabras.index("FOR") + 2]
        if siguiente and siguiente[0] in ("SHARE", "JSON", "XML"):
            _rechazar("cláusula FOR no permitida")
    return sql
