"""
Mock SAP S/4HANA Adapter — simulates SAP integration for development and testing.

Implements the same SapAdapter interface as the real adapter but returns
predefined mock responses. Useful for:
- Local development without SAP access
- Integration tests
- CI/CD pipelines
- Demo environments
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .interface import SapAdapter


class MockSapAdapter(SapAdapter):
    """
    Mock adapter that simulates SAP S/4HANA responses.
    All operations succeed with generated SAP document numbers.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._sent: list[dict[str, Any]] = []  # Track all sent payloads

    async def send_goods_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate a Goods Receipt (MIGO 101) in SAP MM."""
        doc_number = f"GR-{uuid4().hex[:8].upper()}"
        self._sent.append({"type": "goods_receipt", "payload": payload, "doc": doc_number})
        return {
            "success": True,
            "sap_document": doc_number,
            "sap_document_year": datetime.now(timezone.utc).year,
            "message": f"Goods Receipt {doc_number} posted successfully (MOCK)",
        }

    async def send_goods_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate a Goods Issue (MIGO 201) in SAP MM."""
        doc_number = f"GI-{uuid4().hex[:8].upper()}"
        self._sent.append({"type": "goods_issue", "payload": payload, "doc": doc_number})
        return {
            "success": True,
            "sap_document": doc_number,
            "message": f"Goods Issue {doc_number} posted successfully (MOCK)",
        }

    async def send_material_movement(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate a material movement in SAP MM."""
        doc_number = f"MV-{uuid4().hex[:8].upper()}"
        self._sent.append({"type": "material_movement", "payload": payload, "doc": doc_number})
        return {
            "success": True,
            "sap_document": doc_number,
            "message": f"Movement {doc_number} posted (MOCK)",
        }

    async def send_production_confirmation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate production confirmation in SAP PP."""
        doc_number = f"PC-{uuid4().hex[:8].upper()}"
        self._sent.append({"type": "production_confirmation", "payload": payload, "doc": doc_number})
        return {
            "success": True,
            "sap_document": doc_number,
            "message": f"Production confirmation {doc_number} posted (MOCK)",
        }

    async def check_connection(self) -> dict[str, Any]:
        """Simulate connectivity check."""
        return {
            "connected": True,
            "mode": "mock",
            "sap_system": "MOCK-S4H-001",
            "client": self.config.get("sap_client", "100"),
        }

    async def get_material_stock(self, material_code: str, plant: str) -> dict[str, Any]:
        """Simulate stock query in SAP MM."""
        return {
            "material": material_code,
            "plant": plant,
            "stock_quantity": 9999,
            "unit": "KG",
            "mode": "mock",
        }

    def compute_idempotency_hash(self, payload: dict[str, Any]) -> str:
        """SHA-256 of payload for idempotency check."""
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get_sent_payloads(self) -> list[dict[str, Any]]:
        """Return all payloads sent through this mock (for test assertions)."""
        return self._sent

    def reset(self) -> None:
        """Clear sent payloads history."""
        self._sent.clear()
