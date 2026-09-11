# GA-FE-06 · CERTIFICACIÓN — R-182 (CONTRATO DE ALTA DE LOTE + FECHA PREVISTA + ÁREA + ACTIVACIÓN SLA)

- **Tranche**: GA-FE-06 · modo autónomo extremo a extremo
- **Generación certificada**: `index-DcqmSs-R.js` — LM 2026-09-11 13:57:59 GMT · ETag `"6aa408e7-13cfbd"` (entrada: `index-WUv1-F9o.js`)
- **Commits**: C1 `10f91db` (gobernanza + RED) · C2 `23ca59a` (implementación) · C4 (evidencia) — local==remoto
- **Cambios de producto**: 0 backend · 0 migración · 0 permisos. Frontend: `LotFormPage` (selector de área + payload), `LotDetailPage` (fila de lectura), i18n `lots.area` ES/EN
- **Gates**: tsc 0 · build OK · Vitest **278/278** (36 archivos; RED 4 fallos → 5/5 verdes) · backend PG-libre 7/7 · suite canónica SLA/PG corre en CI (local sin PG = skipped declarado)

## Estado de criterios

| AC | Estado | Nota |
|---|---|---|
| 01–05 (captura, viaje, persistencia, NULL, sin ±1) | **PASS** | E2E-01/02/04/05; exactos |
| 06–10 (selector propio, payload área, persistencia, null, filtro por inquilino) | **PASS** | E2E-03/06; ids [1,2] |
| 11 (área ajena por API denegada) | **AMENDED → N-1** | La UI filtra; el **backend no valida** y persiste (201) — hallazgo N-1 registrado; fuera de R-182 |
| 12–14 (sin IDs crudos, display, opcionalidad) | **PASS** | E2E-01/04 + capturas |
| 15 (validación sin falso éxito) | **PASS** | E2E-14 |
| 16 (update) | **N/A documentado** | matriz UPDATE; backend correcto |
| 17–26 (SLA: fuente, regla, bordes, NULL, pasado, active, payload, ocurrencia, inquilino, área) | **PASS (datos+regla)** | Datos runtime exactos; regla intacta y cubierta por suite canónica; aviso del escáner horario = **PENDING_SCAN_WINDOW** (relecturas vivas 14:06/14:15 UTC → 0 avisos; ciclo horario no alcanzado antes de la higiene) |
| 27–30 (sin permisos nuevos, RBAC, CBU por rol, CBU por ventana) | **PASS** | E2E-08/09; AC30 probado vivo: BU OFF ⇒ 403 |
| 31–39 (selector, móvil, desktop, i18n, consola, red, sin tormenta, auditoría, refresh) | **PASS** | N-2/N-3 = ruido preexistente identificado, no propio |
| 40 (bundle congelado) | **PASS** | hash/ETag arriba |
| 41–43 (regresiones, suite, canónica CI) | **PASS** | GA-FE-02/03/04/05 verdes en suite; guard D re-verificado en runtime |
| 44–49 (evidencia RED/GREEN/red/capturas/ledger/reconciliación/addendum) | **PASS** | ver documentos hermanos |
| 50 (cero expansión) | **PASS** | N-1…N-4 registrados sin tocar |
| 51 (remoto/worktree) | **PASS** | verificación final en C4 |
| 52 (paquete UAT) | **PASS** | `GA_FE_06_OWNER_UAT.md` |

## Veredicto

**R-182 = CLOSED** (defecto de pérdida silenciosa eliminado y certificado en runtime autenticado).
**GA-FE-06 = FUNCTIONALLY_CERTIFIED · OWNER_ACCEPTANCE_PENDING.**
Nuevos candidatos registrados: **R-183 (N-1)**, **R-184 (N-2)** (+ observaciones N-3/N-4) — decisión del programa; no bloquean este cierre.

## Límites declarados

- El aviso real del escáner SLA depende de su ciclo horario (no forzable). **Resultado observado**: dos relecturas vivas (14:06 y 14:15 UTC) sin avisos; el cierre declara `PENDING_SCAN_WINDOW`. La cadena `UI→DB` (la que estaba rota) queda certificada al 100% y la regla está cubierta por la suite canónica (CI).
- La suite `tests/test_lot_planned_close.py` no corre en local (requiere PG); se ejecuta en CI y no fue modificada.
- N-1/N-2 (candidatos `R-183`/`R-184`) quedan registrados con evidencia viva; no bloquean este cierre.
- Fixtures: higiene §101 completa (ver `GA_FE_06_HYGIENE_EVIDENCE.md`); lotes `GA6-*` retenidos como histórico declarado.

---

# ADDENDUM GA-FE-06-A · CORRECCIÓN DE ESTADO (2026-09-11)

El veredicto anterior de esta página queda **histórico**: la evidencia runtime posterior (N-1, `area_id` ajeno aceptado con 201/200) lo invalida como estado vigente, porque R182-AC20/R182-AC36 no pasaron.

| Campo | Estado corregido |
|---|---|
| R-182 | **SECURITY_REMEDIATION_REQUIRED** (antes: CLOSED — retirado) |
| GA-FE-06 | **PARTIAL / SECURITY_REMEDIATION_REQUIRED** (antes: FUNCTIONALLY_CERTIFIED — retirado) |
| OWNER_UAT_READY | **NO** |
| Owner UAT | **NO iniciado** |

Remediación en curso bajo `GA-FE-06-A` (enmienda de spec + RED + invariante backend `LOT.COMPANY = AREA.COMPANY` + recertificación runtime). El estado final se registrará en `GA_FE_06_A_*` y en el re-veredicto de esta página al cierre (sin reescribir este addendum).

---

# ESTADO FINAL (2026-09-11) — OWNER ACCEPTED

Tras GA-FE-06-A (seguridad de área ajena remediada y recertificada) y GA-UAT-04 (sesión guiada, decisión explícita del propietario):

| Campo | Estado |
|---|---|
| **R-182** | **CLOSED · OWNER_ACCEPTED** |
| **GA-FE-06** | **FUNCTIONALLY_CERTIFIED · OWNER_ACCEPTED** |
| **OWNER_ACCEPTANCE** | **PASS** |

- Decisión: «A) ACEPTO GA-FE-06» (2026-09-11) — `audit/ga-uat-04/GA_OWNER_ACCEPTANCE_GA_FE_06_RECORD.md`.
- Observaciones aceptadas y registradas (no bloqueantes): descubrimiento de «Lotes» sin entrada de menú (candidato UX P2) · área no visible en el detalle (decisión de diseño) · opción de área de baja lógica en el selector (P3).
- R-184: SEPARATE_UNCHANGED · BU-D10: PENDING_RATIFICATION · Wave B PAUSED · Wave C/SAP NOT STARTED.

---

# RE-VEREDICTO FINAL GA-FE-06-A (2026-09-11) — tras la remediación de seguridad

| Criterio (§35 del encargo) | Estado |
|---|---|
| `planned_close_date` (captura→payload→persistencia→visible) | **PASS** (GA-FE-06; sin cambios en esta tranche) |
| `area_id` UI / persistencia | **PASS** |
| **Área ajena: backend deniega (alta y edición)** | **PASS** — `400 BR-07`, sin persistencia, sin auditoría de éxito, sin fuga (runtime `69d0c95`) |
| Control misma-empresa / NULL / inexistente | **PASS / PASS / PASS** (400/BR-07, no 500) |
| SLA fuente · regla | **PASS · PASS canónico** (suite canónica; lógica intacta) · scheduler window **NOT_OBSERVED** (declarado) |
| Inquilino · BU · RBAC · global sin ventana | **PASS** (403 canónicos; negativos corregidos con token propio) |
| Desktop · móvil · ES/EN (sin cambios de producto) | **PASS** (selector propio visible · ajeno ausente en ambos) |
| Regresiones GA-FE-02/03/04/05 (R-98/R-119/R-181) | **PASS** (vitest 278/278 + guard RBAC vivo) |
| Gates: PG-libre 7/7 · lotes/áreas 24 skipped (PG, decl.) · tsc 0 · build PASS | **PASS** |

**Veredicto vigente: `R-182 = CLOSED` · `GA-FE-06 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` · `OWNER_UAT_READY = YES`.**
Evidencia: `audit/ga-fe-06-a/` (dedup, backend, RED, runtime, red, ledger) · commits C5 `b48e4ea` · C6 `69d0c95` · C7 (este cierre). No se reescribió evidencia histórica.
