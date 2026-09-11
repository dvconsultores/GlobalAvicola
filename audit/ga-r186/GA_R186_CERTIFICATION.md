# GA-R186 · CERTIFICACIÓN

```
TRANCH      R-186 — G-05 production-index: semántica temporal + cierre del HTTP 500
ESTADO      FUNCTIONALLY_CERTIFIED
FINDING     R-186 = CLOSED
OWNER UAT   NOT REQUIRED — endpoint API_ONLY (sin superficie de usuario afectada;
            nada visible cambia). Documentado según terminología existente; no se
            inventa estado de gobernanza nuevo y no se fabrica una UAT artificial.
```

## Base de la certificación

- **Causa raíz demostrada**: `TypeError` `date − datetime` en `get_kpi_production_index` (repro local + 500×2 pre-fix capturados).
- **Fix mínimo**: C2 `0309225` — expresión normalizada con `_dia()` (helper canónico reutilizado); fórmula, guarda, `or 1`, fallbacks y redondeos intactos; backend-only; 0 migraciones/permisos/endpoints/frontend.
- **Gates**: backend canónico 7 passed; suite nueva PG/CI (11 casos, skip local declarado); tsc PASS; build PASS; Vitest **280/280**.
- **Runtime E2E-01…13 + R-184**: **14/14 PASS** con valor determinista independiente (5.1) y contrato de esquema verificado.
- **Seguridad**: tenant/ajeno/sin-concesión/BU-OFF → 404 · sin RBAC → 403 · global+BU-OFF → 404 (OD-16) · sin fuga.
- **R-184/G-06 intactos**: `ipe/11` = **556.6** exacto; ninguna banda/fórmula/respuesta tocada.
- **Higiene**: fixtures retirados (roles/usuarios/grant), BU restaurada OFF (4×OFF verificado), credenciales/temporales destruidos, auditoría preservada, humanos intactos.

## Registros y fronteras

- Nota informativa (docstring `×10`) registrada en `GA_R186_CANONICAL_RECONCILIATION.md` §7 — sin ID nuevo, sin acción.
- Observación de escala del IPE (G-06): **`OWNER_DECISION_REQUIRED`, intacta** (paquete A/B/C vigente; no se resuelve aquí).
- OBS-UAT-01 (UX P2) · BU-D10 (PENDING) · Wave B (PAUSED) · Wave C/SAP (NOT_STARTED): sin cambio.

## Límites declarados

- Suite PG corre en CI; en local queda `skipped` (declarado). Evidencia ejecutada de RED/GREEN = runtime + repro determinista.
- E2E-05 (sin `start_date`) y E2E-06/07 (colección) marcados **N/A con prueba** (no creables por API / endpoint de un solo lote); cubiertos por la suite para el fallback 30.
