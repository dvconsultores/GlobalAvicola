# GLOBAL AVÍCOLA — CUTOVER REHEARSAL PLAN (ensayo completo pre Go-Live)

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **PLAN (sin ejecución)**
Regla de oro: el ensayo **jamás compromete datos reales** — corre sobre entorno aislado o clon de QA.

---

## 1 · Objetivo

Probar de punta a punta el proceso canónico del `CUTOVER_MASTER_SPEC.md` (§1): extract → transform → staging → validation → correction → approval → apply → reconciliation → **acta** → operational checks — con métricas PASS/FAIL explícitas, ANTES del cutover real.

## 2 · Entorno del ensayo

| Elemento | Requisito |
|---|---|
| Infraestructura | Instancia aislada (misma imagen/digest del baseline `fef7289`) o clon del entorno QA; **nunca** la BD que se convierta en producción |
| Datos | R1: set **sintético representativo** construido con las plantillas reales (por BU, incl. UNKNOWN deliberados). R2: **muestra real sanitizada** (si el negocio la autoriza; custodia §6 del plan de migración) |
| Usuarios | Cuentas de ensayo con roles reales mapeados (`cutover:*`, aprobador ≠ creador) |
| Acceso | Solo el equipo de rehearsal + responsable funcional |

## 3 · Guion del ensayo (mínimo uno completo; recomendado: R1 y R2)

| # | Paso | Resultado esperado | Criterio PASS | Evidencia |
|---|---|---|---|---|
| 1 | Preparar maestros reales (o equivalentes R1) | Maestros activos por BU | 0 `MASTER_NOT_FOUND` no explicados | capturas/export de validación |
| 2 | **Extract/Transform**: completar plantillas | Archivos por BU con checksum | 100 % filas tienen dueño y checksum | archivos + hashes |
| 3 | **Staging**: subir | Batch `VALIDATING→VALIDATED` | parseo sin `INVALID_FILE`; conteos leídos/válidos coinciden con el guion | `GET …/validation` |
| 4 | **Corrección**: provocar y corregir errores (≥3 tipos: `MASTER_NOT_FOUND`, `INVALID_NUMBER`, `CONSISTENCY_MISMATCH`) | Errores estructurados por fila/campo y corrección por re-subida | Errores exactos y re-validación limpia | journals |
| 5 | **Aprobación**: submit (creador) → approve (aprobador) | `PENDING_APPROVAL → APPROVED`; BR-14 (creador≠aprobador) respetada | 200/200 y bloqueo si mismo usuario | journals + captura |
| 6 | **Apply** | `APPLIED` en una transacción; lotes `MIGRATED` + openings creados | conteos exactos (leídos/válidos/aplicados), aperturas visibles, **sin duplicados**; segundo apply ⇒ 409 | reconciliación API |
| 7 | **Reconciliación** | Opening ↔ Post-Lifetime; UNKNOWN≠0 | igualdad exacta donde todo KNOWN; conteo UNKNOWN correcto; corrección de prueba (AC65: 10.000→35→9.900⇒9.865) reproduce | `GET …/reconciliation` + corrección |
| 8 | **Acta** | Acta generada con hashes encadenados y firmas declaradas | sha256 coincide con archivo/batch/openings; contenido completo `CUT-GL-01` | acta + hashes |
| 9 | **Operational checks** | Registro real post-cutover sobre lote migrado: mortalidad/alimento/peso; guarda de fecha (`CUT-GL-02`) si implementada | eventos aceptados/rechazados según regla; saldos correctos | journals |
| 10 | **Restore drill** | Backup pre-apply + restore sobre copia ⇒ sistema idéntico al pre-apply | RTO medido ≤ objetivo; integridad verificada | log del drill |

## 4 · Métricas y criterios globales

| Métrica | Objetivo |
|---|---|
| Cobertura del guion | 10/10 pasos ejecutados con evidencia |
| Errores no clasificados | 0 |
| Aplicaciones parciales / duplicados | 0 (atomicidad e idempotencia) |
| Reconciliación | 100 % exacta (con UNKNOWN declarados, no fabricados) |
| Tiempo extremo a extremo | Registrado; presupuesto acordado para el día real (p. ej. ≤ 2 h por BU) |
| Incidentes | Todos con causa raíz + acción antes del Go-Live si es BLOQ |

**PASS del ensayo** = todos los criterios anteriores + acta del ensayo firmada por responsable funcional y técnico. Cualquier FAIL bloquea el Go-Live hasta corrección y repetición (solo el paso afectado si el diseño lo permite).

## 5 · Qué NO prueba el ensayo

- No sustituye la aprobación del Owner ni el gate (`GO_LIVE_OWNER_GATE.md`).
- No usa datos reales completos salvo autorización expresa (R2).
- No valida SAP real (fuera de fase).

## 6 · Calendario tipo

T-10: preparar entorno + maestros → T-7: R1 (sintético) → correcciones → T-5: R2 (sanitizado, si aplica) → T-3: restore drill + acta de ensayo → T-2: revisión de gaps con Owner → T-1: freeze de cambios → D0: cutover real con el mismo guion.
