"""
SAP Integration Adapter — Abstract Base Class + Concrete Implementations.
Domain code never imports concrete adapters directly.
"""
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


# ============================================================
# Data Transfer Objects (domain-facing, no SAP coupling)
# ============================================================

class SapExportPayload(BaseModel):
    """Normalized payload that the domain produces for any SAP adapter."""
    idempotency_key: str
    event_type: str
    lot_id: int
    company_id: int
    event_date: str
    quantity: float
    unit: str
    sap_reference: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None


class SapExportResult(BaseModel):
    """Result returned by any SAP adapter after export attempt."""
    success: bool
    sap_document_id: Optional[str] = None
    message: Optional[str] = None
    status_code: Optional[int] = None
    raw_response: Optional[dict[str, Any]] = None


class SapImportData(BaseModel):
    """Normalized import data from SAP."""
    ref_type: str
    sap_code: str
    description: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None


# ============================================================
# Abstract Base Class
# ============================================================

class SapIntegrationAdapter(ABC):
    """Abstract interface for SAP integration.

    The domain calls these methods without knowing which SAP mechanism is used.

    GA-REM-010 — Semántica de entrega
    ---------------------------------
    `delivers_to_sap` declara si el adaptador realiza una **entrega verificada**
    a SAP. Un adaptador manual o simulado devuelve False, y en ese caso el
    dominio NO puede marcar los eventos como enviados a SAP.

        NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap
    """

    #: True solo si el adaptador obtiene confirmación real del sistema SAP.
    delivers_to_sap: bool = False

    @abstractmethod
    async def export_consolidated(self, payload: SapExportPayload) -> SapExportResult:
        """Send a consolidated movement to SAP. Returns result."""
        ...

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if SAP is reachable."""
        ...

    @abstractmethod
    async def get_adapter_name(self) -> str:
        """Return human-readable adapter name."""
        ...


# ============================================================
# Concrete: ManualSapAdapter (File-based import/export)
# ============================================================

class ManualSapAdapter(SapIntegrationAdapter):
    """
    Manual mode: generates JSON files for export, accepts JSON/CSV for import.
    Does NOT connect to SAP directly. The analyst handles file transfer manually.
    """

    #: GA-REM-010 — el modo manual NO entrega a SAP: genera un artefacto que
    #: un analista debe cargar. No puede producir estado "enviado a SAP".
    delivers_to_sap = False

    def __init__(self, export_dir: str | None = None):
        import os
        # GA-REM-009 — el artefacto debe sobrevivir a la recreación del contenedor.
        self.export_dir = export_dir or os.environ.get(
            "SAP_EXPORT_DIR", "/app/media/sap_exports"
        )
        self._exported: list[SapExportPayload] = []  # in-memory for dev

    async def export_consolidated(self, payload: SapExportPayload) -> SapExportResult:
        """Generate export file and return success. In manual mode, always succeeds."""
        import os
        os.makedirs(self.export_dir, exist_ok=True)

        file_path = f"{self.export_dir}/{payload.idempotency_key}.json"
        with open(file_path, "w") as f:
            f.write(payload.model_dump_json(indent=2))

        self._exported.append(payload)

        # GA-REM-010: NO se devuelve ningún sap_document_id. Un identificador
        # ficticio haría que el sistema aparentase una confirmación de SAP que
        # no existe, y BR-15 bloquearía el registro sin contrapartida real.
        return SapExportResult(
            success=True,
            message=f"Artefacto generado para carga manual: {file_path}",
            sap_document_id=None,
            status_code=200,
            raw_response={"artifact_path": file_path, "delivery": "manual_pending"},
        )

    async def check_connection(self) -> bool:
        """GA-REM-010: el modo manual no tiene conexión con SAP. No la finge."""
        return False

    async def get_adapter_name(self) -> str:
        return "ManualSapAdapter (archivo, sin entrega verificada a SAP)"


# ============================================================
# Concrete: MockSapAdapter (Development & Testing)
# ============================================================

class MockSapAdapter(SapIntegrationAdapter):
    """
    Mock adapter for development and testing.
    Simulates SAP responses including errors, latency, and idempotency.
    """

    #: GA-REM-010 — simulación: nunca entrega realmente a SAP.
    delivers_to_sap = False

    def __init__(self, simulate_errors: bool = False, error_rate: float = 0.0):
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        self._confirmed_ids: set[str] = set()  # track idempotency

    async def export_consolidated(self, payload: SapExportPayload) -> SapExportResult:
        """Simulate SAP export with configurable error rate."""
        import random

        # Idempotency: if already confirmed, return duplicate
        if payload.idempotency_key in self._confirmed_ids:
            return SapExportResult(
                success=True,
                sap_document_id=f"SAP-DUP-{payload.idempotency_key[:8]}",
                message="Documento ya confirmado (idempotencia)",
                status_code=200,
            )

        # Simulate error
        if self.simulate_errors and random.random() < self.error_rate:
            return SapExportResult(
                success=False,
                message="Error simulado: SAP no disponible",
                status_code=503,
            )

        # Success
        sap_id = f"SAP-{payload.idempotency_key[:8].upper()}"
        self._confirmed_ids.add(payload.idempotency_key)

        return SapExportResult(
            success=True,
            sap_document_id=sap_id,
            message=f"Documento {sap_id} creado en SAP",
            status_code=201,
            raw_response={"sap_doc_id": sap_id, "status": "CONFIRMED"},
        )

    async def check_connection(self) -> bool:
        import random  # GA-REM-010: faltaba el import a nivel de función
        return not self.simulate_errors or random.random() > self.error_rate

    async def get_adapter_name(self) -> str:
        return f"MockSapAdapter (errors={self.simulate_errors}, rate={self.error_rate})"


# ============================================================
# Idempotency Helper
# ============================================================

def generate_idempotency_key(lot_id: int, event_type: str, event_date: str, sap_ref: str, data: str) -> str:
    """Generate SHA-256 idempotency key from event data."""
    raw = f"{lot_id}|{event_type}|{event_date}|{sap_ref}|{data}"
    return hashlib.sha256(raw.encode()).hexdigest()
