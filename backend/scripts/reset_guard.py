"""Guarda FAIL-CLOSED para operaciones destructivas sobre una base de datos.

Entregable de `GA-REM-025` `AC15` (§50 y §51 del encargo).

Hermana de `tests/environment_guard.py`, pero **no** la misma: aquella protege la
ejecución de la suite; ésta protege el borrado de datos, que es irreversible.

Principio, idéntico al de `GA-REM-014`:

    Si existe cualquier duda sobre la identidad del destino, NO SE BORRA.

Nunca se avisa y se continúa. Ante duda, se aborta.

Cinco señales independientes; **todas** deben ser favorables:

    1. `ENVIRONMENT` declarado y perteneciente al conjunto permitido.
    2. Marcador explícito de intención destructiva (`GA_ALLOW_DESTRUCTIVE_RESET=1`).
    3. El destino `host/base` figura en una lista blanca explícita del operador.
    4. La base no se autodeclara productiva (comentario `COMMENT ON DATABASE`).
    5. El operador reescribe el nombre exacto de la base en la línea de órdenes.

§51 es deliberado: la señal 3 **no** es un `hostname != X`. Una comparación negativa
protege contra el host que ya conocemos y deja pasar todos los que aún no existen —
incluida la futura instalación real de un cliente. Una lista blanca positiva falla al
revés, que es como debe fallar una guarda.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

#: Entornos donde el borrado es admisible.
ENTORNOS_PERMITIDOS = {"development", "test", "testing", "certification", "shared_test"}

#: Entornos donde jamás lo es. La comprobación es redundante con la lista permitida
#: —nada fuera de ella pasa— y se conserva porque un error tipográfico en la lista
#: permitida no debe abrir la puerta a `production`.
ENTORNOS_PROHIBIDOS = {"production", "prod", "real_production", "staging", "pre", "preprod"}

#: Marcador de intención. No tiene valor por defecto a propósito.
MARCADOR_INTENCION = "GA_ALLOW_DESTRUCTIVE_RESET"

#: Lista blanca de destinos, `host/base` separados por comas.
LISTA_BLANCA = "GA_RESET_ALLOWED_TARGETS"

#: Texto que, presente en el comentario de la base, la declara productiva.
MARCA_PRODUCCION = "REAL_PRODUCTION"


class ResetBloqueado(RuntimeError):
    """El destino no superó la guarda. El borrado no se ejecuta."""


@dataclass(frozen=True)
class Destino:
    host: str
    base: str

    @property
    def identidad(self) -> str:
        return f"{self.host}/{self.base}"


def _leer_destino(dsn: str) -> Destino:
    u = urlparse(dsn)
    host = (u.hostname or "").strip().lower()
    base = (u.path or "").lstrip("/").strip()
    if not base:
        raise ResetBloqueado("La cadena de conexión no nombra ninguna base de datos.")
    # Una conexión por socket unix no tiene host; es local por construcción.
    return Destino(host=host or "local", base=base)


def verificar(
    dsn: str,
    *,
    base_confirmada: str | None,
    entorno: str | None = None,
    comentario_base: str | None = None,
) -> Destino:
    """Valida las cinco señales. Devuelve el destino o lanza `ResetBloqueado`.

    `comentario_base` es el `COMMENT ON DATABASE` ya leído por el llamador; se pasa como
    argumento en lugar de consultarlo aquí para que la guarda sea comprobable sin una
    base de datos delante.
    """
    destino = _leer_destino(dsn)

    # ── Señal 1: entorno declarado y permitido ────────────────────────────────
    declarado = (entorno if entorno is not None else os.environ.get("ENVIRONMENT", "")).strip().lower()
    if not declarado:
        raise ResetBloqueado(
            "ENVIRONMENT no está declarado. Un entorno desconocido se trata como productivo."
        )
    if declarado in ENTORNOS_PROHIBIDOS:
        raise ResetBloqueado(f"ENVIRONMENT={declarado!r} prohíbe cualquier borrado.")
    if declarado not in ENTORNOS_PERMITIDOS:
        raise ResetBloqueado(
            f"ENVIRONMENT={declarado!r} no está en la lista de entornos donde se admite "
            f"borrar: {sorted(ENTORNOS_PERMITIDOS)}."
        )

    # ── Señal 2: intención explícita ──────────────────────────────────────────
    if os.environ.get(MARCADOR_INTENCION) != "1":
        raise ResetBloqueado(
            f"Falta {MARCADOR_INTENCION}=1. El borrado nunca ocurre por omisión."
        )

    # ── Señal 3: lista blanca positiva de destinos ────────────────────────────
    crudo = os.environ.get(LISTA_BLANCA, "")
    permitidos = {p.strip().lower() for p in crudo.split(",") if p.strip()}
    if not permitidos:
        raise ResetBloqueado(
            f"{LISTA_BLANCA} está vacía. El destino debe autorizarse uno a uno, "
            "en formato host/base."
        )
    if destino.identidad.lower() not in permitidos:
        raise ResetBloqueado(
            f"El destino {destino.identidad!r} no figura en {LISTA_BLANCA}."
        )

    # ── Señal 4: la base no se autodeclara productiva ─────────────────────────
    if comentario_base and MARCA_PRODUCCION in comentario_base.upper():
        raise ResetBloqueado(
            f"La base {destino.base!r} lleva la marca {MARCA_PRODUCCION} en su comentario. "
            "Se considera instalación real de cliente."
        )

    # ── Señal 5: confirmación escrita por el operador ─────────────────────────
    if base_confirmada != destino.base:
        raise ResetBloqueado(
            "La confirmación no coincide con el nombre de la base. "
            f"Se esperaba --confirm-database {destino.base!r}."
        )

    return destino
