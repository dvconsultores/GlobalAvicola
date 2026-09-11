# GA-BU-D10 · TRAZABILIDAD DE LA DECISIÓN

| Eslabón | Referencia |
|---|---|
| Nacimiento de la decisión | `audit/remediation/BUSINESS_UNIT_OWNER_DECISION_MATRIX.md` §1 (2026-09-07): `BU-D10` «La empresa deja de tener una línea» |
| Régimen de concesiones (base) | `OD-09` (`specs/remediation/OD-09-CONTROL-PLANE-VS-BUSINESS-UNIT.md`): `.d` empresa-scoped · `.e` marca-no-borra + transferencia |
| Registro pendiente | `audit/remediation/AUDIT_OWNER_DECISIONS_REQUIRED.md`: `BU-D10` «no se toca» · `PENDING_RATIFICATION` |
| Redacción canónica provisional | `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md` §7 + `GLOBAL_AVICOLA_MASTER_360_ADDENDUM_PRODUCT_SCOPE_AND_COMPANY_BU.md` §6: «provisional = opción A (GA-REM-040 §6.3 · AC-A06)… opción B NO elegida · NO descartada» |
| Reserva expresa | `OD-16` `.e`: deja BU-D10 separada a propósito |
| Conducta probada | `backend/tests/test_business_unit_admin.py:318` · `test_business_units.py:491/509` · runtime GA-FE-02-D/E |
| Implementación vigente | `admin.py` (`fijar_habilitacion` `:137`; `conceder` `:286`; `revocar` `:363`) · `service.py` (`unidades_efectivas_por_id` `:97`; `revocar_concesiones` `:321`) |
| Paquete de decisión (esta tranche) | `audit/ga-bu-d10/` (C1; solo gobernanza) |
| Próximo ID OD (línea GA) | **OD-23 — ASIGNADA** (verificada libre el 2026-09-11; a distinguir de la familia `AOD-*` de Wave B) |
| **DECISIÓN DEL PROPIETARIO** | **B — RE-AUTORIZACIÓN** (respuesta explícita, 2026-09-11) · `OD-23` RATIFIED · finding **R-188** (P2 · OPEN) |
