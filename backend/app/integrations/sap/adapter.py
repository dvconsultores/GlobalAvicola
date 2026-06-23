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
    """

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

    def __init__(self, export_dir: str = "/tmp/sap_exports"):
        self.export_dir = export_dir
        self._exported: list[SapExportPayload] = []  # in-memory for dev

    async def export_consolidated(self, payload: SapExportPayload) -> SapExportResult:
        """Generate export file and return success. In manual mode, always succeeds."""
        import os
        os.makedirs(self.export_dir, exist_ok=True)

        file_path = f"{self.export_dir}/{payload.idempotency_key}.json"
        with open(file_path, "w") as f:
            f.write(payload.model_dump_json(indent=2))

        self._exported.append(payload)

        return SapExportResult(
            success=True,
            message=f"Archivo generado: {file_path}",
            sap_document_id=f"MANUAL-{payload.idempotency_key[:12]}",
            status_code=200,
        )

    async def check_connection(self) -> bool:
        """Manual mode is always 'connected'."""
        return True

    async def get_adapter_name(self) -> str:
        return "ManualSapAdapter (File-based)"


# ============================================================
# Concrete: MockSapAdapter (Development & Testing)
# ============================================================

class MockSapAdapter(SapIntegrationAdapter):
    """
    Mock adapter for development and testing.
    Simulates SAP responses including errors, latency, and idempotency.
    """

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
