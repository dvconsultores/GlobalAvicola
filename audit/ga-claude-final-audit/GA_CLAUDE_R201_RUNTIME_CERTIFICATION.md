# GA-CLAUDE · R-201 — CERTIFICACIÓN (predicado SAP fail-closed sin contexto)

Fecha: 2026-09-13 · Hallazgo **R-201** (P2 · bloquea fase SAP · GAP-02) · Paquete `specs/R-201/` · Commits: C1 `8a442ec` · C2 `4050eef`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `red_c1.log` — **5F/18P**: global sin contexto veía referencias (3), payloads/errores/jobs/consolidados de A y B; `consolidate` sin eventos respondía **201 []** (la guarda vivía dentro del bucle de grupos); `retry` reenviaba payloads de ambas empresas (retry_count y estado cambiaban); transversal `test_ac_sap02b` rojo. Controles verdes: situada en A opera solo A; actor de empresa intacto |
| **C2 · Implementación** | ✅ | `green_c2.log` — **32/32** (R-201 7 + `test_sap_transversal` 16 + `test_sap.py` 9); **suite completa conjunta `1278 passed / 0 failed / 49 skipped`** (`full_suite_close.log`, 20:14) · commit `4050eef` |
| **C2-nota** | ✅ | La primera suite completa conjunta marcó **1F en la guarda de determinismo** (`test_time_determinism t028_04`) por una fecha ISO literal en el fixture R-201 (`payload_data.event_date`); remediada con `iso_days_ago(1)` (guarda + R-201: **17/17**) |
| **C2s · Sensibilidad** | ✅ S1·S2 | **S1** (restaurar `true()`): 3F — RED-01/02 + transversal caen (`mutations/S1_true_restaurado.log`); **S2** (retry sin guarda): RED-04 cae (`mutations/S2_retry_sin_guarda.log`). Nota honesta: con las guardas tempranas puestas, S1 **no** derriba RED-03/04 (los protege la guarda, no el filtro) — por eso S2 existe. Mutaciones revertidas |
| **C3 · Runtime** | ⏸ **pendiente G-06** | Las sondas clave (`R201-RT-01/02`: global **sin contexto** ⇒ ∅ / 4xx) requieren un actor **sin contexto** (super) — no disponible en UAT-09; misma clase que R-199/R-202. `R201-RT-05/06` (situada/empresa) no distinguen pre/post y no aportan |

## 2 · Implementación

`integrations/sap/service.py`:
- `_company_filter` ⇒ **`false()`** sin contexto (patrón `_acotar_a_empresa`; `OD-14.d`). La autoridad global **situada** opera su empresa como siempre.
- `consolidate_approved` · `export_to_sap` · `retry_failed`: `_require_company_id()` **al inicio** — fallo cerrado **antes de leer** (y antes de cualquier reacción externa en el reintento).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R201-01 (referencias ⇒ ∅) | ✅ RED-01 (C2 verde) · S1 |
| AC-R201-02 (jobs/consolidados/errores/payloads ⇒ ∅) | ✅ RED-02 · S1 · transversal |
| AC-R201-03 (consolidate ⇒ 4xx sin leer; hoy 201 con lista vacía) | ✅ RED-03 (C2 verde) · control 03b (evento sigue `approved`) |
| AC-R201-04 (retry ⇒ 4xx; cero reenvíos) | ✅ RED-04 · **S2** |
| AC-R201-05 (global situada opera A, control) | ✅ verde en C1 y C2 |
| AC-R201-06 (actor de empresa intacto, control) | ✅ verde en C1 y C2 |
| AC-R201-07 (fixtures A/B cruzadas) | ✅ transversal + RED-01/02 |
| AC-R201-08 (sin migración/endpoint/permiso/modelo) | ✅ diff (1 fichero de servicio) |
| AC-R201-09 (`get_company_filter` legado retirado) | ✅ ya retirado en `R-199` C2 (`62cd0e1`) — verificado por ausencia (el test CTL-10 de R-199 lo fija) |
| AC-R201-10 (regresión SAP) | ✅ 32/32 dirigidas · suite completa `1278/0/49` |

## 4 · Veredicto

**R-201 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos con evidencia local. **C3 runtime pendiente de G-06** (actor sin contexto); la ruta de sondeo (`R201-RT-01…04`) queda lista para ejecutarse cuando el gate se provea. Sin cambio de contrato para usuarios de empresa; la autoridad global sin contexto pasa de «todas» a «ninguna» (corrección, no ruptura).
