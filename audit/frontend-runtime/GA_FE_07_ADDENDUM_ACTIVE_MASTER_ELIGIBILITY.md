# GA-FE-07 · ADDENDUM AL MASTER FRONTEND RUNTIME AUDIT — ELEGIBILIDAD POR ESTADO (OD-21)

Complementa: roadmap, catálogo, `GA_GOV_01_ADDENDUM_OBSERVATION_TRIAGE.md`, `GA_FE_06_ADDENDUM_LOT_CONTRACT_SLA.md`.
Fecha: 2026-09-11 · Baseline de entrada `87d090c` · Generación final `index-BUthrUt9.js` / backend `5a5bb3f`.

## 1 · Nueva regla de dominio vigente

- **OD-21**: un maestro dado de baja lógica no puede usarse para **referencias nuevas**; la historia se conserva. Implementación **solo Área→Lote** en esta tranche (principio general documentado).
- Finding **R-185** (P2) **CLOSED** técnicamente (aceptación pendiente). OBS-UAT-04 queda **RESUELTO por OD-21 + GA-FE-07**.

## 2 · Efecto en las entradas del audit

| Entrada | Efecto |
|---|---|
| GA-GOV-01 (`OWNER_DECISION_REQUIRED`) | **Resuelta**: elección C del propietario → implementada |
| R-182 / GA-FE-06-A | Sin cambio (CLOSED_OWNER_ACCEPTED); la elegibilidad por estado es deuda posterior y ya cerrada |
| Navegación (`/lots*` sin menú) | Sin cambio: OBS-UAT-01 sigue `UX_ENHANCEMENT_ONLY P2` |
| R-184 | Sin cambio (SEPARATE_OPEN) |

## 3 · Superficies tocadas

`app/tenancy.py` (validador extendido, default intacto) · `app/lots/service.py` (alta + detección de cambio en edición) · `frontend LotFormPage.tsx` (filtro del selector transaccional; administración intacta). Sin migraciones/permisos/endpoints.

## 4 · Evidencia

`audit/ga-fe-07/` (OD-21, R-185, spec, trazas, RED, evidencias backend/frontend/runtime/red, ledger, cierre, certificación, UAT). **Certificaciones previas preservadas.**
