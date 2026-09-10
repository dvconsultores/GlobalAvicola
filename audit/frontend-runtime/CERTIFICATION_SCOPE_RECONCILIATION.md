# CERTIFICATION SCOPE RECONCILIATION

**2026-09-10** · base `3808ed5` · capa de reconciliación **añadida**, sin reescribir un solo cierre histórico (§74 del encargo).

Regla: los cierres técnicos previos **siguen siendo válidos en su frontera**. Este documento declara esa frontera y la confronta con la realidad de producto de hoy.

## 1. Marco de capas (§119)

```
TECHNICAL_BACKEND        CERTIFIED / PARTIAL / NOT TESTED
FRONTEND_INTEGRATION     PASS / FAIL / NOT APPLICABLE
DEPLOYED_RUNTIME         PASS / FAIL / NOT VERIFIED
AUTHENTICATED_E2E        PASS / FAIL / BLOCKED
USER_ACCEPTANCE          PASS / FAIL / NOT TESTED
```

## 2. Certificaciones con afirmación de frontend — reconciliación (§120)

| Capacidad / tranche | Qué se certificó | ¿Frontend en el AC? | Frontend repo hoy | Runtime compartido | Veredicto de frontera |
|---|---|---|---|---|---|
| `GA-REM-034` Roles y permisos (`R-92/93/94`) | pantalla + API; "ui" en el informe | sí (pantalla) | ✅ implementada (`fd5a389`) | ❌ **no desplegada** (ruta ausente del bundle) | **SCOPE-LIMITED**: certificación válida en entorno aislado; producto en shared **no** |
| `GA-REM-033` Maestros (`R-89/90/91`) | gestión de 19 | sí | ✅ | ⚠️ parcial (13/20 entidades) | scope-limitado |
| `GA-REM-037` Curvas (`R-96/97`) | carga de tabla "capacidad de producto" | sí | ✅ | ❌ no desplegada | scope-limitado (el cierre exigía UI; la UI existe local; falta runtime) |
| `GA-REM-038/039` Notificaciones/Áreas | canal interno + área | sí | ✅ | ❌ no desplegadas | scope-limitado |
| `GA-REM-042` Importación abuelas (`R-152`) | plan tipado + frontend | sí | ✅ | ❌ + **runtime rechaza BR-22** | scope-limitado; además ruptura vigente |
| `GA-REM-021-B/-C` B01/B02/B13 | reglas + datos + formulario | sí (form) | ✅ | ❌ + **400 BR-20/BR-21** | scope-limitado; ruptura vigente |
| `GA-REM-005-C/E/F` R-170/172/173/174 | conteo, saldos, guardas | frontend en R-170/R-172 (form) | ✅ | ❌ | scope-limitado |
| `GA-REM-040` fases 1–8 | backend completo (catálogo→sesión) | no (fase 9 aparte) | fase 9 **no iniciada** (FROZEN) | backend ✅ vivo | **correcto como backend**; producto de unidades **no existe** aún |
| `GA-REM-041` reverso interno | servicio+ruta+roles | **excluido** («frontend … fase 9») | no | backend ✅ vivo | frontera ya declarada por el propio programa |
| `GA-REM-032` Auditoría (`R-81/82/84`) | cobertura y filtros | sí | ✅ | ⚠️ runtime sirve la versión con filtros falsos | scope-limitado |
| `GA-REM-002`/`-007-B`/`-023-B` (WAVE B) | backend | no | n/a | backend ✅ | válido, frontera backend |

Precedente relevante ya escrito por el programa: `PROCESS-13`/`PROCESS-14` declararon «runtime compartido `NOT VERIFIED` mientras `R-99` siga abierto». Esta auditoría **confirma** esa frontera y la cuantifica: **15 entregas** de frontend posteriores al 2026-09-05 no están en el shared.

## 3. Certificaciones de proceso (P-xx) — estado de conformidad de producto

| Proceso | Certificación técnica | Frontend en runtime 09-05 | Producto hoy |
|---|---|---|---|
| P-01 Recepción | sí (aislado) | generación vieja | reprod.: **roto (BR-20)**; general: pendiente auth |
| P-02 Control diario | sí | viejo pero funcional al nivel 09-05 | pendiente auth |
| P-03 Curvas | sí (tras R-96/97) | ❌ capacidad no desplegada | producto parcial |
| P-05 Incubación | sí | nacimiento **roto (BR-21)**; catálogo viejo | parcial |
| P-06 Lotes | sí | presente | pendiente auth |
| P-07 Revisión/corrección | sí | presente; sin reenvío UI (R-181) | parcial |
| P-09 Auditoría | sí | filtros viejos | parcial |
| P-12 Maestros | sí | 13/20 | parcial |
| P-13 Usuarios/roles | sí | roles no desplegado | parcial |
| P-14 Notificaciones | sí (aislado) | no desplegado | no disponible |
| P-15 Reportes/KPI | sí | viejo | parcial |
| Acceso por unidad (15 criterios) | `0/15` declarado | fase 9 | no disponible |

Ningún proceso se re-certifica ni se des-clasifica aquí; la columna «producto hoy» es la reconciliación de frontera que faltaba.

## 4. Hallazgos históricos reexaminados (sin reabrir)

| ID | Cierre previo | Verdad hoy | Acción |
|---|---|---|---|
| `R-96/R-97` | cerrados con pantalla | pantalla existe; **no desplegada** | no se reabre; se registra en R-99 como consecuencia |
| `R-120` | cerrado (5 estados en `/users`) | fix sólo local; **runtime persiste F-E** | ídem (R-99) |
| `R-135` | cerrado (técnico) | backend sí; **reenvío sin UI en ninguna generación** | **R-181 (nuevo)** — no lo cubría R-135 |
| `R-82` | cerrado (filtros) | runtime sirve la versión previa | consecuencia de R-99 |
| `R-127` | cerrado (A1) | backend seguro desplegado; selector super_admin intacto | vigente |
| `R-158` | P2, "preexistente" | **es el mecanismo de R-99**: rompe `npm run build` del Dockerfile | propuesta de normalización de impacto (se documenta; no se reescribe severidad) |
| `R-99` | P1 `BLOCKED_BY_OUT_OF_SCOPE_DEPLOYMENT` | **causa raíz demostrada dentro del alcance de código** (`4386f87` + `R-158`) | addendum fechado en el backlog |

## 5. La frase que esta reconciliación deja escrita

```
BACKEND CERTIFIED  ≠  FEATURE AVAILABLE  ≠  PRODUCT COMPLETE
La frontera de los cierres 001–042 es: servicio y contrato, en entorno aislado.
El producto en el entorno compartido es la generación 2026-09-05 + los faltantes de fase 9.
Nada de esto invalida el trabajo técnico: se re-clasifica su alcance (§73).
```

## 6. Fuentes

`BUSINESS_PROCESS_CERTIFICATION_MATRIX_360.md` · informes `PROCESS-0x` · `GA-REM-0xx-CERTIFICATION-REPORT.md` · `MASTER_REMEDIATION_MATRIX.md` · `POST_PUSH_PRODUCTION_STATE_REPORT.md` (addenda R-99) · `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` · evidencia propia (`DEPLOYMENT_FRONTEND_FINGERPRINT.md`).
