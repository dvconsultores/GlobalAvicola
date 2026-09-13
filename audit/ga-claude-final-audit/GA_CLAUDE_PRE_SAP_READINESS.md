# GA-CLAUDE · PREPARACIÓN PRE-SAP Y COMPUERTAS FINALES (§59–§69)

Auditoría independiente Claude · 2026-09-13 · HEAD `c0b4afc` (== `origin/main`) · runtime `avicola.globaldv.net` (`index-DDCcWL76.js` == build local de HEAD). Documentos base: `GA_CLAUDE_FINAL_AUDIT_CURRENT_STATE.md`, `GA_CLAUDE_OPEN_FINDING_RECONCILIATION.md`, `GA_CLAUDE_OWNER_ACCEPTANCE_GAP_MATRIX.md`, `GA_CLAUDE_OWNER_DECISION_RECONCILIATION.md`, `GA_CLAUDE_FINAL_E2E_PROCESS_MATRIX.md`, `GA_CLAUDE_SAP_EVENT_READINESS_MATRIX.md`, `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md`.

## 1 · Compuertas de la decisión (§59–§61)

### 1.1 Seguridad (§59)

| Compuerta | Veredicto | Motivo (evidencia) |
|---|---|---|
| Inquilino | **PARTIAL** | Sólido en auth/masters/lots/operations/review/audit/notifications; huecos registrados: SAP sin contexto (R-201), estructurales del lote (R-203), password reset sin contexto (R-202), `company_id` de maestros (R-50/GAP-05) |
| Company BU (habilitación) | **PASS** | OD-16.e/f en lectura y escritura, incluida la autoridad global (`9ffc5ec`; runtime 21/21) — **excepción registrada**: eventos sin lote de tipos inequívocos (**R-221**, P2) |
| User BU (concesión) | **PASS** | Evaluada de BD por petición; revocación/apagado inmediatos (OD-23; GA-UAT-08 técnica) |
| RBAC | **PARTIAL** | Cobertura total de rutas; **FAIL puntual P1**: autoridad global fabricable desde rol de inquilino (**R-199**) y batch con permiso débil (**R-208**) |
| OD-16 | **PASS** (con R-221) | Fail-closed verificado en runtime; 17 tests obsoletos pendientes de actualizar (GA-GOV-03) |
| OD-23 (ciclo BU) | **PASS** (técnica) | Código + UI verificados; suite certificada roja por fixture (GA-GOV-03/R-213), causa explicada |
| Access Admin (OD-15) | **PASS** | Self-grant/cross-company/candidatos/«administrar ≠ acceder» verificados |
| Actor global (OD-14) | **PARTIAL** | Contextual en dato productivo/maestros; **FAIL** en SAP (R-201) y password reset (R-202) |
| Cruce de empresa | **PARTIAL** | Bloqueado en superficies certificadas; residuos R-203/R-50 y oráculos de unicidad (GAP-15, P3) |
| Sesión | **PARTIAL** | Recarga por petición ✔; refresh como access (**R-200**, P2) y sin logout/rotación (`GA-REM-003` AC04 abierto, P1) |
| Evidencia accesible a terceros | **PASS** (R-139 cerrado) | Descarga con empresa+unidad |
| **No hay P0** | — | — |
| **P1 de seguridad conocido: R-199** (+ `GA-REM-003` AC04) | **FAIL** | Bloqueantes de la puerta §59 |

**Veredicto de seguridad: FAIL** (por R-199 P1 y R-200/`GA-REM-003` P1-P2; correcciones con paquete listo).

### 1.2 Integridad de datos (§60)

| Compuerta | Veredicto | Motivo |
|---|---|---|
| Población | **PASS** (ledger) / **FAIL en consumidores** | Invariante y bloqueos probados; BR-18 tras reverso (**R-193**), cierre con `REVERSED` (**R-192**) |
| Saldos huevo/incubación | **PASS** | R-161 cerrado (bloqueo de fila) |
| Referencias foráneas | **FAIL** | R-203 (galpón/línea/curva del lote sin verificar) |
| Consistencia de aprobación | **PARTIAL** | R-208 (lote), R-142/AOD-17 (CRM), E-09 |
| Atomicidad | **PASS** | Frontera por ruta verificada; aprobación+lote, reverso y notificaciones en la misma transacción; excepciones documentadas (evidencias, login fallido) |
| Sin evento duplicado | **PARTIAL** | Idempotencia de alta (R-146 backend) y SAP con defecto de re-enlace (GAP-14); sin clave en cliente |
| Idempotencia | **PARTIAL** | R-146 vertical incompleta; GAP-14/15 |
| Concurrencia | **PASS** | `FOR UPDATE` en saldos/decisión/reverso; lock asesor del lote GP; consolidación SAP sin bloqueo (P3, fase SAP) |
| Auditabilidad | **PARTIAL** | Duplicada e incompleta (**P1-12 reabierta**); inmutabilidad solo aplicativa (R-148) |
| Consistencia de reverso | **PARTIAL** | R-192/R-193; auditoría de contrapartida en P1-12 |

**Veredicto de integridad: FAIL** (R-192/R-193/P1-12; correcciones con paquete listo).

### 1.3 Base de datos (§61)

Alembic: 38 revisiones, cabeza única `y5z6a7b8c9d0` (código y base de pruebas); entrada ejecuta `alembic upgrade head`; sin drift detectado; restrictivas presentes (unicidades globales de `lot_code`/`username`/`email`/`idempotency_key` → oráculo P3 GAP-15). Dos guardas de test fijadas a `x4y5z6a7b8c9` (GA-GOV-03 grupo C). **Sin blocker de esquema**; `R-164` (`lots.company_id` nulable) queda condicional a una consulta de datos no ejecutada (UNKNOWN).

## 2 · Scorecard basado en evidencia (§68)

```
Frontend (visibles requeridas) ......... 38/38 reconciliadas · 9 DEGRADADAS por esta auditoría
Frontend internas ...................... 7/7 evaluadas · 4 degradadas (FIA-01/02/05/07)
Auth-bloqueadas ........................ 15/15 sin bloqueo hoy (9 re-ejercitadas con sesión real)
Frontend ↔ backend integración ......... 31 brechas INT (17 bloqueantes + 1 condicional + 1 UNKNOWN)
Formularios auditados .................. 70 · CORRECTOS 47 · WRONG-FIELD 10 · 422/RENDER 12 · MALFORMED 1
Backend (rutas) ........................ 212 · CERTIFIED 107 · PARTIAL 91 · MISSING 11 · UNKNOWN 3
Backend huérfanas requeridas ........... 7 rutas sin frontend (INT-09/10/16/15/08)
Procesos pre-SAP CERTIFICADOS E2E ...... 0/17  (PARTIAL 5 · BROKEN 8 · BACKEND_ONLY 2 · UAT_PENDING 1 · UNKNOWN 1)
Decisiones del propietario (alcance actual) .. 14 pendientes/contradictorias (§57 NO cumplido)
Owner UAT requerida .................... 4 PENDING (GA-UAT-09, GA-F01/R-189, 19-VNC path C, OD-19) · 11 ACCEPTED · 6 NOT_REQUIRED
P0 ..................................... 0
P1 (local) ............................. 9  (R-190, R-191, R-192, R-194, R-195, R-196, R-199, R-205, GA-GOV-03)
P2 bloqueantes ......................... 15 (R-193, R-197, R-198, R-200, R-201*, R-203, R-204, R-207, R-208, R-209, R-210, R-211, R-215, R-221, P1-12)
Contratos FE↔BE rotos .................. 25 formularios/reglas (registro B-01…B-41 §5.3)
UI/UX funcional ........................ FAIL (manejo de errores FAIL; navegación con huérfanas; móvil sin logout; web <1024 sin nav)
Seguridad .............................. FAIL (R-199; GA-REM-003 AC04/R-200)
Integridad de datos .................... FAIL (R-192/R-193/P1-12)
Atomicidad ............................. PASS
Idempotencia ........................... PARTIAL (R-146 FE; GAP-14)
Concurrencia ........................... PASS (consolidación SAP P3 diferida)
Paridad de runtime (repo↔desplegado) ... PASS
Suite backend en HEAD .................. 1201 ✔ / 25 ✘ / 49 omitidos (25 TEST_DEFECT)
Playwright de procesos ................. 117 ✔ / 12 ✘ (12 TEST_DEFECT; 6 certificaciones no reproducibles)
Vitest / tsc / build ................... 314/314 · 0 errores · OK
Runtime E2E autenticado (esta auditoría) ✔ ejecutado (nube + local) sobre generación congelada
Desconocidos ........................... P-10 (trazabilidad, proceso), R-164 (datos), UNKNOWNs menores listados por informe
```

## 3 · Condiciones §69 para GO (evaluación)

| Condición | Estado |
|---|---|
| Todos los procesos pre-SAP certificados E2E | **NO** (0/17) |
| Frontend completo | **NO** (31 brechas INT; 4 superficies roto/degradadas) |
| Backend completo | **NO** (11 rutas requeridas sin frontend; huecos de integridad) |
| Integración FE↔BE completa | **NO** (17 bloqueantes) |
| UI/UX crítico completo | **NO** (error handling FAIL; navegación) |
| Sin capacidades backend-only requeridas | **NO** (reverso, activación manual, cancelación, edición, clasificación) |
| Sin frontend-only requerido | n/a (no encontrado) |
| Sin despliegue obsoleto | **SÍ** (paridad PASS) |
| Sin flujo roto | **NO** |
| Sin decisión pendiente de alcance actual | **NO** (14) |
| Sin UAT requerida pendiente | **NO** (4) |
| Sin P0 | **SÍ** (0) |
| Sin P1 bloqueante | **NO** (9) |
| Sin P2 funcional/seguridad/integridad bloqueante | **NO** (15) |
| Sin desconocidos | **NO** (P-10; R-164) |
| Eventos fuente SAP suficientemente definidos | **NO** (matriz §55: 0 READY) |

## 4 · Veredicto

- `PRE_SAP_FUNCTIONAL_CERTIFICATION` = **FAIL**
- `READY_TO_BEGIN_SAP_INTEGRATION` = **NO** (ni siquiera `PREPARATION_ONLY`: la aplicación local no está certificada; las condiciones de §69.B tampoco se cumplen)
- `FINAL VERDICT` = **NO_GO_SAP_FUNCTIONAL_GAPS**
- `SAP_IMPLEMENTATION_STARTED` = **NO**

El veredicto no descansa en una carencia de funcionalidad bruta (la mayoría de capacidades existe y una parte está probada de verdad — R-153/R-190 cadena, OD-16/OD-23, R-184/186/187), sino en: **flujos de proceso rotos por la UI** (R-190/R-191/R-194/R-205), **integridad** (R-192/R-193/P1-12), **autoridad** (R-199 y familia), **capacidades requeridas solo-backend** (R-207/P-15) y **gobernanza no reproducible** (GA-GOV-03) con **UAT del propietario pendiente** (GA-UAT-09). Todo bloqueante tiene **paquete Spec Development listo** (§70: cola en `GA_CLAUDE_FINAL_PROJECT_STATUS.md §5`).
