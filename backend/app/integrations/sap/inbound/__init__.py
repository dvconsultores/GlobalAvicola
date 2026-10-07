"""SAP HANA Cloud READ ONLY inbound — SPEC 005.

    SYNC → HANA READ ONLY CONNECTOR (SELECT) → RAW → VALIDATION → MAPPING
         → STAGING → CONTROLLED PROMOTION → sap_references

Este paquete solo lee de SAP. No contiene, ni debe contener, ninguna ruta de escritura.
"""
