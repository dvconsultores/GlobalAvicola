"""Clasificación de todo dato persistente del entorno compartido.

Entregable de `GA-REM-025` (§11 del encargo). Es la **fuente única**: la usan el
inventario, la herramienta de reset y la documentación publicada, de modo que las tres
no pueden discrepar.

Regla de oro: una tabla que no aparezca aquí se trata como `UNKNOWN` y **no se borra**.
Ante duda, se conserva y se reporta.
"""
from __future__ import annotations

from enum import Enum


class Categoria(str, Enum):
    """Categorías del encargo §11."""

    SYSTEM_REQUIRED = "SYSTEM_REQUIRED"
    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"
    REFERENCE_MASTER_REQUIRED = "REFERENCE_MASTER_REQUIRED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    CLIENT_MASTER_DATA = "CLIENT_MASTER_DATA"
    TEST_BUSINESS_DATA = "TEST_BUSINESS_DATA"
    SIMULATED_SAP_DATA = "SIMULATED_SAP_DATA"
    UNKNOWN = "UNKNOWN"


#: Categorías que la herramienta de reset puede vaciar.
BORRABLES = {
    Categoria.CLIENT_MASTER_DATA,
    Categoria.TEST_BUSINESS_DATA,
    Categoria.SIMULATED_SAP_DATA,
}


# ── Clasificación ─────────────────────────────────────────────────────────────
#
# `SYSTEM_REQUIRED`         metadatos del propio motor/migraciones. Jamás se tocan.
# `AUTH_REQUIRED`           sin esto nadie puede entrar y el sistema es inutilizable.
# `CONFIGURATION_REQUIRED`  configuración del sistema, no historia de negocio.
# `REFERENCE_MASTER_REQUIRED`
#                           catálogo invariante del dominio avícola, sin `company_id`.
# `CLIENT_MASTER_DATA`      maestros que **cada cliente crea**: los del entorno compartido
#                           son inventados. Todos tienen CRUD completo por API
#                           (`app/masters/router.py:88-106`), así que borrarlos no impide
#                           que un usuario los vuelva a crear.
# `TEST_BUSINESS_DATA`      historia operativa ficticia. Es el objetivo del encargo.
# `SIMULATED_SAP_DATA`      envíos SAP simulados. Nunca hubo SAP real (`GA-REM-017`).

CLASIFICACION: dict[str, tuple[Categoria, str]] = {
    # ── Sistema ──────────────────────────────────────────────────────────────
    "alembic_version": (
        Categoria.SYSTEM_REQUIRED,
        "Revisión de esquema. Borrarla haría que Alembic reaplicase toda la cadena.",
    ),
    # ── Autenticación y autorización ─────────────────────────────────────────
    "roles": (
        Categoria.AUTH_REQUIRED,
        "Catálogo de roles. La migración `l2m3n4o5p6q7` los busca por nombre y NO los crea.",
    ),
    "permissions": (
        Categoria.AUTH_REQUIRED,
        "Asociaciones rol→permiso. No existe API que las cree: solo el seed o la migración.",
    ),
    "users": (
        Categoria.AUTH_REQUIRED,
        "Se conservan las cuentas autorizadas; las obsoletas se retiran con criterio, no en bloque.",
    ),
    "companies": (
        Categoria.AUTH_REQUIRED,
        "Tenants. Se conservan los dos de certificación exigidos por R-42/R-48/R-59.",
    ),
    # ── Configuración ────────────────────────────────────────────────────────
    "approval_steps": (
        Categoria.CONFIGURATION_REQUIRED,
        "Flujo de aprobación por empresa. Recreable con POST /approval-steps/seed-defaults.",
    ),
    # ── Catálogo invariante del dominio ──────────────────────────────────────
    "productive_phases": (
        Categoria.REFERENCE_MASTER_REQUIRED,
        "Ciclo productivo avícola. Sin `company_id`; `lot_phases` depende de él. "
        "Ningún código referencia sus `code`, luego es dato puro, pero es dato del dominio.",
    ),
    # ── Maestros que crea el cliente ─────────────────────────────────────────
    **{
        tabla: (
            Categoria.CLIENT_MASTER_DATA,
            "Maestro de cliente con CRUD completo por API. Los actuales son inventados.",
        )
        for tabla in (
            "farms", "houses", "hatcheries", "incubators", "hatchers",
            "genetic_lines", "breeds", "suppliers", "feed_types", "vaccines",
            "medications", "mortality_causes", "cull_causes", "transports",
            "processing_plants", "rejection_reasons", "correction_types",
        )
    },
    # ── Historia operativa ficticia ──────────────────────────────────────────
    **{
        tabla: (Categoria.TEST_BUSINESS_DATA, motivo)
        for tabla, motivo in (
            ("lots", "Lotes demo."),
            ("lot_phases", "Fases de lotes demo."),
            ("opening_balances", "Saldos de apertura de lotes demo."),
            ("operational_events", "Eventos operativos sintéticos. Núcleo de la historia ficticia."),
            ("consolidated_movements", "Movimientos consolidados derivados de eventos ficticios."),
            ("bird_movements", "Submovimiento de eventos ficticios."),
            ("egg_batches", "Submovimiento de eventos ficticios."),
            ("egg_movements", "Submovimiento de eventos ficticios."),
            ("egg_storage", "Submovimiento de eventos ficticios."),
            ("chick_batches", "Submovimiento de eventos ficticios."),
            ("feed_movements", "Submovimiento de eventos ficticios."),
            ("hatchery_params", "Submovimiento de eventos ficticios."),
            ("inspection_details", "Submovimiento de eventos ficticios."),
            ("operational_alerts", "Alertas generadas por eventos ficticios."),
            ("correction_logs", "Correcciones sobre eventos ficticios."),
            ("approval_actions", "Aprobaciones de eventos ficticios."),
            ("review_batches", "Lotes de revisión de certificaciones antiguas."),
            ("reversals", "Reversos de eventos ficticios."),
            ("evidences", "Evidencias de prueba. Sus ficheros ya se pierden hoy por R-52."),
            ("audit_logs", "Auditoría de actividad ficticia. Se retira con ella."),
        )
    },
    # ── SAP simulado ─────────────────────────────────────────────────────────
    **{
        tabla: (
            Categoria.SIMULATED_SAP_DATA,
            "Envío SAP simulado. Nunca hubo integración real (GA-REM-017 = BLOCKED_EXTERNAL); "
            "conservarlo con estado «confirmado» representa como real algo que no lo es.",
        )
        for tabla in ("sap_payloads", "sap_responses", "sap_references", "sap_sync_jobs")
    },
}


def clasificar(tabla: str) -> tuple[Categoria, str]:
    """Categoría de una tabla. Lo desconocido se conserva, nunca se borra."""
    return CLASIFICACION.get(
        tabla,
        (Categoria.UNKNOWN, "No clasificada. Se conserva por precaución y se reporta."),
    )


def borrable(tabla: str) -> bool:
    return clasificar(tabla)[0] in BORRABLES
