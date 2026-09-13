# GA · PRE-SAP — MATRIZ DE READINESS DE SPECS (TRANCHE 0 · §13/§14)

Validación de **33 paquetes** en `audit/ga-claude-final-audit/specs/` (24 completos ×6 ficheros + 9 compactos ×2; R-214 sin paquete). Método: inventario de ficheros (verificado: 162 ficheros), y checklist §14 (hallazgo/spec/AC/plan/tests/E2E/UAT/dependencias/clarificaciones). Leyenda columnas sección: **H**=hallazgo · **S**=spec · **C**=clarificaciones · **P**=plan/checklist/tareas · **A**=AC matrix · **R**=diseño RED/E2E/UAT.

## 1 · Matriz

| ID | Prio | Paquete | H·S·C·P·A·R | Decisión propietario pendiente | Depende de | Solapes/servicios compartidos | Seguro en solitario | Toca seguridad | Servicio/FE compartida | Cambia comportamiento de proceso | Estado | Acción requerida |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GA-GOV-03 | P1 | 6f | ✓✓✓✓✓✓ | OD-16, OD-23 | ninguna (inicio) | CI común; no toca producto | Sí | No | No (tests/docs) | No | **SPEC_READY** | Ejecutar T1 |
| R-199 | P1 | 6f | ✓✓✓✓✓✓ | OD-13.c (semántica de alcance) | ninguna | `auth/service.py` con R-200/202; `security.py` con R-200 | Sí (con orden auth) | **Sí — fundación** | `auth` | Permisos plataforma | **SPEC_READY** (+decisión antes de merge) | T2 |
| R-200 | P2 | 6f | ✓✓✓✓✓✓ | — | R-199 (mismo fichero) | `security.py` con R-199 | Con R-199 | **Sí — fundación** | `auth` | Sesión | **SPEC_READY** | T2 |
| R-202 | P2 | 2f | ✓✓–✓✓✓ | — | R-199 (mismo fichero) | `auth/service.py` | Con R-199/200 | **Sí** | `auth` | Reset de contraseñas | **READY (compacto, §14 mínimo cumplido)** | T2 (rider) |
| R-208 | P2 | 6f | ✓✓✓✓✓✓ | — | — | `review/router.py` con R-197 | Sí | **Sí (permisos)** | `review` | Aprobación en lote | **SPEC_READY** | T2 |
| R-201 | P2 | 6f | ✓✓✓✓✓✓ | — | R-204 (patrón de alcance BU) | `integrations/sap/service.py` | Sí | **Sí** | `sap` | Alcance retro-SAP | **SPEC_READY** | T3 |
| R-203 | P2 | 6f | ✓✓✓✓✓✓ | — | — | `lots/service.py` con R-192; `masters` | Con cuidado (T7 posterior) | Sí (tenencia) | `lots`/`masters` | Validación de lote | **SPEC_READY** | T3 |
| R-204 | P2 | 6f | ✓✓✓✓✓✓ | — | — | `reports/service.py` + `dashboard/service.py` con R-216 | Con R-216 | Sí (alcance) | `reports`/`dashboard` | KPIs incubadora | **SPEC_READY** | T3 (fusionar R-216) |
| R-216 | P2 | 2f | ✓✓–✓✓✓ | — | R-204 (mismo fichero) | `dashboard/service.py` | Con R-204 | No | `dashboard` | Tarjetas dashboard | **READY (compacto)** | T3 (rider de R-204) |
| R-221 | P2 | 6f | ✓✓✓✓✓✓ | AOD-13 (¿módulos por empresa?) | R-203/204 (alcance) | `operations/service.py` | Sí | **Sí (alcance)** | `operations` | Eventos sin lote | **READY** (+decisión AOD-13) | T3 (rider) |
| R-190 | P1 | 6f | ✓✓✓✓✓✓ | — | R-205 (misma familia de ubicación) | `OperationFormPage.tsx`/`operationPayload.ts` (familia) | Con R-205 | No | FE captura | Registro de eventos | **SPEC_READY** | T4 |
| R-205 | P1 | 6f | ✓✓✓✓✓✓ | — | R-190 | ídem | Con R-190 | No | FE navegación | Recepción reproductoras | **SPEC_READY** | T4 |
| R-191 | P1 | 6f | ✓✓✓✓✓✓ | — | — | `lots.service.ts`/`LotDetailPage.tsx` | Sí | No | FE lotes | Transición de fase | **SPEC_READY** | T5 |
| R-206 | P2 | 2f | ✓✓–✓✓✓ | — | R-209/210 (misma serialización) | `operationPayload.ts` | Con R-209/210 | No | FE captura | Payload de eventos | **READY (compacto)** | T5 (rider) |
| R-209 | P2 | 6f | ✓✓✓✓✓✓ | — | — | `operations/service.py` | Sí | No | `operations` | Snapshot SAP | **SPEC_READY** | T5 |
| R-210 | P2 | 6f | ✓✓✓✓✓✓ | — | R-206 (payload) | `OperationFormPage.tsx`/`operationPayload.ts` | Con R-206 | No | FE captura | Unidad de peso | **SPEC_READY** | T5 |
| R-146 (rider) | P2 | sin paquete propio | GA-REM-011 enm. | AOD-16 | R-206/209 | `operationPayload.ts` | Con T5 | Integridad | FE captura | Duplicados móviles | **RIDER de T5** | incluir en T5 si el propietario aprueba AOD-16 (idempotency_key FE) |
| R-194 | P1 | 6f | ✓✓✓✓✓✓ | — | R-190 (helper ubicación) | `OperationFormPage.tsx` (familia) | Con R-190/205 hechas | No | FE captura + `operations` | Cadena de incubadora | **SPEC_READY** | T6 |
| R-192 | P1 | 6f | ✓✓✓✓✓✓ | OD-19 §1 (ya resuelto en spec) | — | `validators.py` con R-193/211; `lots/service.py` | Con orden T7 | No | `lots`/`operations` | Cierre con reversos | **SPEC_READY** | T7 |
| R-193 | P2 | 6f | ✓✓✓✓✓✓ | OD-19 §3 | R-192 (validadores) | `validators.py` | Con R-192/211 | No | `operations` | BR-18 neto | **SPEC_READY** | T7 |
| R-211 | P2 | 6f | ✓✓✓✓✓✓ | — | R-192/193 (validadores) | `validators.py` | Con orden | No | `operations` | BR-17 distribución | **SPEC_READY** | T7 |
| P1-12-REOPEN | P2 | 6f | ✓✓✓✓✓✓ | — | R-198 (evidencias auditadas) | `audit/*` con R-219; `lots/service.py` (productores) | Con R-198/219 | Integridad auditoría | `audit` | Trazabilidad | **SPEC_READY** | T8 |
| R-198 | P2 | 6f | ✓✓✓✓✓✓ | AOD-14 (obligatoriedad de evidencia) | P1-12 (auditoría) | `operations` evidencias | Con P1-12 | Integridad | `operations` | Evidencias | **READY** (+decisión AOD-14 antes de diseño final) | T8 |
| R-219 | P2 | 2f | ✓✓–✓✓✓ | — | P1-12 (contrato de auditoría) | `AuditPage.tsx` | Con P1-12 | No | FE auditoría | Vista de auditoría | **READY (compacto)** | T8 (rider) |
| R-196 | P1 | 6f | ✓✓✓✓✓✓ | — | R-215 (ErrorBoundary global) | `MasterListPage.tsx` | Con R-215 (o antes) | No | FE maestros | Alta de maestros | **SPEC_READY** | T9 |
| R-195 | P1 | 6f | ✓✓✓✓✓✓ | — | R-122 (columna Empresa — rider), R-202 | `UsersPage.tsx` + `auth` | Sí | No | FE usuarios | Edición de usuario | **SPEC_READY** | T9 (rider R-122) |
| R-215 | P2 | 6f | ✓✓✓✓✓✓ | — | — | Boundary global + R-196 | Sí | No | FE app shell | Estabilidad | **SPEC_READY** | T9 (rider de R-196) |
| R-197 | P2 | 6f | ✓✓✓✓✓✓ | — | R-208 (router), R-142 (estados) | `review/service.py` + `router.py` | Con R-208 | No | `review` | Bandejas de revisión | **SPEC_READY** | T10 |
| R-207 | P2 | 6f | ✓✓✓✓✓✓ | **OD-19 §18** (UI de reverso sí/no y alcance) | R-192 (estado REVERSED), R-197 | `reversals` + FE nueva | Sí (después de R-192) | Autoridad de anulación | FE nueva | Reverso interno | **OWNER_DECISION_REQUIRED** | T10 (confirmar OD-19 §18) |
| R-142 (rider) | P2 | sin paquete | GA-REM-006 enm. | AOD-17 | R-197 (estados) | `review/service.py` | Con T10 | Estado | `review` | `CORRECTED` semántica | **RIDER de T10** | decidir AOD-17 antes de T10 |
| R-212 | P3 | 2f | ✓✓–✓✓✓ | — | R-213 (datos de /me) | `PermissionRoute`/layout | Sí | No | FE guardas | Denegado≠vacío | **READY (compacto)** | T11 |
| R-213 | P3 | 2f | ✓✓–✓✓✓ | — | — | `auth` `/me` | Sí | No | `auth` lectura | Robustez /me | **READY (compacto)** | T11 (antes que 212 ideal) |
| R-218 | P2 | 2f | ✓✓–✓✓✓ | — | — | `reports` FE | Sí | No | FE reportes | Vista semanal | **READY (compacto)** | T11 |
| R-220 | P3 | 2f | ✓✓–✓✓✓ | — | ítems A-D itemizados | varios | Por ítem | No | varias | Varios | **READY (compacto itemizado)** | T11 (por lotes A→D) |
| R-217 | P2 | 2f | ✓✓–✓✓✓ | dependiente de fase SAP | fase SAP | `SapManagerPage.tsx` | Sí | No | FE SAP | Panel SAP | **SAP_PHASE** | no ejecutar pre-SAP (registro) |

## 2 · Validación §14 de paquetes compactos (9)

Los 9 compactos (R-202, R-206, R-212, R-213, R-216, R-217, R-218, R-219, R-220) contienen: hallazgo+spec (con contrato y ficheros), AC verificables y diseño RED/E2E/UAT comprimido. **Declarados suficientes** para su severidad (P2/P3 no-estructurales) — ninguno requiere expansión a 6 ficheros antes de implementar; si la implementación descubre ambigüedad, se abre `CLARIFICATIONS` ad-hoc por el propio equipo (regla §14: el autor del spec no puede ser el único aprobador — en el programa de remediación la aprobación es del propietario para cambios de comportamiento).

## 3 · Gaps de cobertura de specs detectados en la validación

| Gap | Detalle | Relevancia | Propuesta |
|---|---|---|---|
| **Wave C KPIs** (R-131…R-134 P1, R-141) | Sin spec (GA-REM-022 «no redactada»); bloquean P-15 | Alta (nota del IPE aceptado) | Decisión AOD-10/AOD-10.e; si «corregir» → redactar specs antes de T12 |
| R-144 (FCR/cierre), R-164 (tenencia datos), R-140 (cancelación UI), P1-13 (multinivel), P1-15/RES-02 (activación/clasificación UI), R-149/GA-REM-016 (certificación real), P1-5 (observabilidad) | Bloqueantes heredados sin paquete propio | Media-alta | Resolver por decisión del propietario (lote IA) o rider en la tranche correspondiente (ya mapeado en la matriz de hallazgos §B) |
| R-52/RES-05, GA-REM-004 AC03/AC07, P1-6 | Acciones de operaciones (no código) | Alta (evidencias/respaldos) | **Pista OPS** en el roadmap |

## 4 · Veredicto

**SPECS_VALIDATION: 33/33 paquetes consisten; 0 expansiones obligatorias; 3 familias de decisión del propietario condicionan diseño (R-199/OD-13.c, R-207/OD-19 §18, R-198/AOD-14, R-221/AOD-13) y existe 1 gap de cobertura real (Wave C KPI) que requiere decisión AOD-10 antes de la certificación final de P-15.**
