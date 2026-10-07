"""Configuración del conector HANA — SPEC 005 `§12`, `§13`, `FR-01`, `FR-04`.

Tres reglas:

    la ausencia de credenciales no es un error   es un estado: `PENDING_CREDENTIALS`
    el TLS no es una opción                      cifrado y validación de certificado, siempre
    el secreto no sale de aquí                   ni en `repr`, ni en un error, ni en la API
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import Any

from .errors import ErrorCode, SapInboundError

#: Identificador SQL admitido para el schema. Viene de `Settings`, nunca de una petición, y aun
#: así se valida: es el único fragmento del SQL que no es un parámetro bind.
_IDENTIFICADOR = re.compile(r"^[A-Z_][A-Z0-9_]{0,126}$")

#: Entornos donde se acepta el driver simulado (`Q10`).
ENTORNOS_SIMULABLES = ("development", "test")

_REQUERIDAS = (
    ("host", "SAP_HANA_HOST"),
    ("user", "SAP_HANA_USER"),
    ("password", "SAP_HANA_PASSWORD"),
    ("schema", "SAP_HANA_SCHEMA"),
    ("client", "SAP_HANA_CLIENT"),
)


def validate_identifier(nombre: str) -> str:
    """Devuelve el identificador si es seguro para interpolarlo; si no, falla cerrado."""
    if not isinstance(nombre, str) or not _IDENTIFICADOR.match(nombre):
        raise SapInboundError(
            ErrorCode.SAP_CONFIG_MISSING,
            "SAP_HANA_SCHEMA no es un identificador válido (A-Z, 0-9, _).")
    return nombre


def _lista(valor: Any) -> tuple[str, ...]:
    if not valor:
        return ()
    if isinstance(valor, str):
        return tuple(p.strip() for p in valor.split(",") if p.strip())
    return tuple(str(p).strip() for p in valor if str(p).strip())


@dataclass(frozen=True)
class HanaSettings:
    host: str = ""
    port: int = 443
    user: str = ""
    password: str = field(default="", repr=False)
    schema: str = ""
    client: str = ""
    encrypt: bool = True
    validate_certificate: bool = True
    trust_store: str = ""
    connect_timeout: int = 10
    query_timeout: int = 60
    page_size: int = 500
    max_rows: int = 20_000
    lookback_days: int = 30
    max_concurrency: int = 2
    sync_enabled: bool = False
    sync_interval: int = 3600
    company_codes: tuple[str, ...] = ()
    plants: tuple[str, ...] = ()
    language: str = "S"
    driver: str = "hdbcli"
    environment: str = "development"
    outbound_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "company_codes", _lista(self.company_codes))
        object.__setattr__(self, "plants", _lista(self.plants))
        object.__setattr__(self, "driver", (self.driver or "hdbcli").strip().lower())

    @classmethod
    def from_settings(cls, cfg: Any = None) -> "HanaSettings":
        """Vista del conector sobre `app.config.settings` (leída en cada uso, sin caché)."""
        if cfg is None:
            from ....config import settings as cfg
        return cls(
            host=cfg.SAP_HANA_HOST, port=cfg.SAP_HANA_PORT, user=cfg.SAP_HANA_USER,
            password=cfg.SAP_HANA_PASSWORD, schema=cfg.SAP_HANA_SCHEMA,
            client=cfg.SAP_HANA_CLIENT, encrypt=cfg.SAP_HANA_ENCRYPT,
            validate_certificate=cfg.SAP_HANA_SSL_VALIDATE_CERTIFICATE,
            trust_store=cfg.SAP_HANA_SSL_TRUST_STORE,
            connect_timeout=cfg.SAP_HANA_CONNECT_TIMEOUT_SECONDS,
            query_timeout=cfg.SAP_HANA_QUERY_TIMEOUT_SECONDS,
            page_size=cfg.SAP_HANA_PAGE_SIZE, max_rows=cfg.SAP_HANA_MAX_ROWS_PER_SYNC,
            lookback_days=cfg.SAP_HANA_DEFAULT_LOOKBACK_DAYS,
            max_concurrency=cfg.SAP_HANA_MAX_CONCURRENCY,
            sync_enabled=cfg.SAP_HANA_SYNC_ENABLED,
            sync_interval=cfg.SAP_HANA_SYNC_INTERVAL_SECONDS,
            company_codes=cfg.SAP_HANA_COMPANY_CODES, plants=cfg.SAP_HANA_PLANTS,
            language=cfg.SAP_HANA_LANGUAGE, driver=cfg.SAP_HANA_DRIVER,
            environment=cfg.ENVIRONMENT, outbound_enabled=cfg.SAP_OUTBOUND_ENABLED,
        )

    # ── Estado ────────────────────────────────────────────────────────────────

    def missing(self) -> list[str]:
        """Nombres de las variables obligatorias ausentes. Nunca sus valores."""
        return [variable for atributo, variable in _REQUERIDAS
                if not str(getattr(self, atributo) or "").strip()]

    def tls_violations(self) -> list[str]:
        violaciones = []
        if self.encrypt is not True:
            violaciones.append("SAP_HANA_ENCRYPT debe ser true")
        if self.validate_certificate is not True:
            violaciones.append("SAP_HANA_SSL_VALIDATE_CERTIFICATE debe ser true")
        return violaciones

    @property
    def configured(self) -> bool:
        """Completa **y** conforme a la política TLS. Configurado no es conectado."""
        return not self.missing() and not self.tls_violations()

    @property
    def simulated(self) -> bool:
        return self.driver == "fake"

    def secrets(self) -> tuple[str, ...]:
        return tuple(s for s in (self.password,) if s)

    def redact(self, texto: object) -> str:
        from .errors import sanitize
        return sanitize(texto, self.secrets())

    # ── Conexión ──────────────────────────────────────────────────────────────

    def connect_options(self) -> dict[str, Any]:
        """Opciones para `hdbcli.dbapi.connect`. Falla cerrado si falta algo o si no hay TLS."""
        faltan = self.missing()
        if faltan:
            raise SapInboundError(
                ErrorCode.SAP_CONFIG_MISSING,
                "Configuración SAP HANA incompleta. Faltan: " + ", ".join(faltan))
        violaciones = self.tls_violations()
        if violaciones:
            raise SapInboundError(
                ErrorCode.SAP_TLS_ERROR,
                "TLS obligatorio para SAP HANA Cloud: " + "; ".join(violaciones))
        validate_identifier(self.schema)
        opciones: dict[str, Any] = {
            "address": self.host,
            "port": int(self.port),
            "user": self.user,
            "password": self.password,
            "encrypt": True,
            "sslValidateCertificate": True,
            "connectTimeout": int(self.connect_timeout) * 1000,
            "communicationTimeout": int(self.query_timeout) * 1000,
        }
        if self.trust_store:
            # CA propia: se añade confianza, no se quita validación.
            opciones["sslTrustStore"] = self.trust_store
        return opciones

    def __str__(self) -> str:
        return repr(self)


assert "password" in {f.name for f in fields(HanaSettings) if not f.repr}
