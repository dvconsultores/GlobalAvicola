"""Adaptador inbound — SPEC 005 `§10`. Interfaz **separada** de la de export.

`SapIntegrationAdapter` (export) declara `delivers_to_sap`; añadirle `fetch_*` obligaría a los
adaptadores manual y mock a fingir capacidades inbound y diluiría esa semántica. El inbound es
otro contrato: lee, entrega filas crudas al pipeline y no sabe nada del dominio.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .client import SapHanaReadOnlyClient
from .errors import ErrorCode, SapInboundError
from .registry import HanaObject, get_definition
from .settings import ENTORNOS_SIMULABLES, HanaSettings


class SapInboundAdapter(ABC):
    """Lectura de objetos SAP. No existe —ni debe existir— un método de escritura."""

    name: str = "inbound"
    simulated: bool = False

    @abstractmethod
    async def check_connection(self) -> dict[str, Any]:
        """Consulta de humo. Devuelve su resultado o lanza `SapInboundError`."""

    @abstractmethod
    async def fetch_page(self, objeto: HanaObject, params: dict[str, Any], *,
                         limit: int, offset: int) -> list[dict[str, Any]]:
        """Una página de filas crudas del objeto, ya normalizadas a JSON."""


class HanaCloudReadOnlyAdapter(SapInboundAdapter):
    name = "SAP_HANA_CLOUD_READ_ONLY_V2"

    def __init__(self, cfg: HanaSettings, client: SapHanaReadOnlyClient | None = None,
                 *, simulated: bool = False) -> None:
        self._cfg = cfg
        self._client = client or SapHanaReadOnlyClient(cfg)
        self.simulated = simulated

    async def check_connection(self) -> dict[str, Any]:
        return await self._client.ping()

    async def fetch_page(self, objeto: HanaObject, params: dict[str, Any], *,
                         limit: int, offset: int) -> list[dict[str, Any]]:
        return await self._client.fetch_page(
            get_definition(objeto), params, limit=limit, offset=offset)


#: Doble compartido por el proceso cuando `SAP_HANA_DRIVER=fake` (desarrollo y E2E local).
_FAKE = None


def build_adapter(cfg: HanaSettings | None = None) -> SapInboundAdapter:
    """El adaptador que corresponde a la configuración. El simulado, solo fuera de entornos reales."""
    cfg = cfg or HanaSettings.from_settings()
    if cfg.driver == "fake":
        if cfg.environment not in ENTORNOS_SIMULABLES:
            raise SapInboundError(
                ErrorCode.SAP_CONFIG_MISSING,
                "SAP_HANA_DRIVER=fake solo se admite con ENVIRONMENT=development o test.")
        global _FAKE
        from .fake_hana import FakeHana, default_dataset
        if _FAKE is None or _FAKE.schema != cfg.schema or _FAKE.client != cfg.client:
            _FAKE = FakeHana(default_dataset(client=cfg.client or "100"),
                             schema=cfg.schema or "SAPFAKE", client=cfg.client or "100")
        return HanaCloudReadOnlyAdapter(
            cfg, client=SapHanaReadOnlyClient(cfg, connect_factory=_FAKE.connect),
            simulated=True)
    if cfg.driver != "hdbcli":
        raise SapInboundError(ErrorCode.SAP_CONFIG_MISSING,
                              "SAP_HANA_DRIVER debe ser hdbcli.")
    return HanaCloudReadOnlyAdapter(cfg)


def driver_available() -> bool:
    """¿Está instalado `hdbcli`? Se comprueba sin importarlo."""
    import importlib.util
    try:
        return importlib.util.find_spec("hdbcli") is not None
    except Exception:  # noqa: BLE001
        return False
