# GA · PRE-SAP — T13 · RESULTADOS DE LA UAT TÉCNICA — LOTES U3–U8

Fecha de ejecución: **2026-09-16** · Árbol: `90c6679`+ (árbol final de
certificación) · Runtime: `https://avicola.globaldv.net` (compartido UAT) ·
Backend desplegado: digest `sha256:5c4824bd…` (`d122e04`) · Frontend:
`index-r36pBbNX.js`.

> **Atribución.** `OWNER_UAT_HUMAN_EXECUTION = WAIVED_BY_OWNER_DECISION` ·
> `TECHNICAL_FUNCTIONAL_UAT_AUTHORITY = DEEPSEEK_AGENT` ·
> `OWNER_DID_NOT_EXECUTE_UAT = TRUE` · `AUTOMATED_TECHNICAL_UAT = TRUE`. Sin
> lenguaje de aceptación del propietario.

## Restricción transversal (documentada, no un defecto)

La cuenta del canal seguro UAT-09 es **«Operador de abuelas»**: BU efectiva
`grandparent` **única** y permisos `lots:create/read`, `masters:read`,
`operations:create/read/update`, `sap:read`. Consecuencias (verificadas por
sonda real):

- El **X-BU (por diseño)** rechaza montar escenarios fuera de su unidad:
  `POST /lots` con `bird_type=breeder|broiler` ⇒ **403 «sin acceso operativo a
  la unidad de negocio»**; ídem granjas/galpones/curvas (403 por
  `masters:create` ausente).
- `reports:read` y `audit:read` no están en el rol ⇒ **403 por rol** en esas
  sondas.

Por lo anterior, las sondas runtime de **U3/U4/U5/U8** quedan
`DEGRADED_BY_CERT_ACCOUNT_SCOPE`, y la verificación funcional de esos procesos se
ejecuta por **suites de pila completa** (E2E Playwright + backend, fixtures
multi-BU/admin) sobre el árbol final — con evidencia en
`evidence/t13-final/` (corrida §14). Los pasos que **sí** habilita el canal se
ejecutan en runtime real (U6, U7-lite, cierre BR-18 del ciclo GP).

---

## U3 · Reproductoras (P-03)

| Campo | Valor |
|---|---|
| **UAT_ID** | U3 |
| **PROCESS** | P-03 (cría de reproductoras: curvas §4.5 · distribución BR-17 · recepción BR-20) |
| **OBJECTIVE** | Verificar curvas de peso y alerta por desviación, distribución por galpón y cuadre BR-20 de la recepción |
| **PRECONDITIONS** | Escenario breeder con línea genética + curva activa (fixtures de pila completa); runtime desplegado |
| **ROLE** | Runtime: cuenta UAT-09 (BU `grandparent` → **403 X-BU por diseño** para breeder) · Funcional: fixtures admin multi-BU de la suite |
| **COMPANY** | Compañía 1 (fixture del entorno compartido; empresa activa del token) |
| **BUSINESS_UNIT** | `grandparent` (cuenta) / `breeder` (proceso — fuera del alcance de la cuenta) |
| **FIXTURE** | Suite: granja/galpón/línea `P03*` + curva `TABLA` (10 d: 90-110; 20 d: 180-220; edad al pesar 15 d ⇒ 135-165 interpolado) + lote `breeder` de 15 días; recepción BR-20 (Σ = recibidas + mortalidad arribo + rechazo) |
| **STEPS_EXECUTED** | 1) Sonda runtime de montaje: `POST /masters/farms|houses|genetic-lines` ⇒ **403**; `POST /lots` breeder ⇒ **403 «sin acceso operativo a la unidad de negocio 'breeder'»** (X-BU por diseño; ver `u3-u8-runtime-flow.log` y `u3-u8-data-inventory.log`) · 2) Ejecución funcional por suite en pila completa: cadena completa inspección→salida, §4.5 control (150 g sin alerta), §4.5 tratamiento (100 g ⇒ alerta `weight_deviation`, umbral interpolado 135 ≈ testigo exacto), borde superior (165 = OK; 166 ⇒ alerta), sin curva ⇒ sin umbral inventado, y conservación de versión de curva del lote; BR-20: cuadre exacto en recepción de reproductoras |
| **EXPECTED_RESULT** | Todos los casos de P-03 verdes en la suite; montaje runtime bloqueado por X-BU (documentado) |
| **ACTUAL_RESULT** | Runtime: 403 X-BU por diseño (sin acceso operativo «breeder») — comportamiento esperado del aislamiento. Funcional: suite E2E `proceso-p03-reproductoras-cria.spec.ts` (5 casos) + `proceso-p03-curvas-ui.spec.ts` + `proceso-p04-*` y backend `test_genetic_curves.py` verdes en la corrida final (contadores exactos en `evidence/t13-final/`) |
| **EVIDENCE** | `evidence/t13-uat/u3-u8-runtime-flow.log` · `u3-u8-data-inventory.log` · `evidence/t13-final/e2e-full.log` · `backend-full-suite.log` |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

**Observaciones U3**: verificación runtime degradada por alcance de la cuenta
(§Restricción); la lógica de curvas/alertas y BR-20 quedó cubierta por la suite
funcional completa y por los tests backend de curvas.

---

## U4 · Incubadora (P-04 + P-05)

| Campo | Valor |
|---|---|
| **UAT_ID** | U4 |
| **PROCESS** | P-04 (huevo fértil) + P-05 (incubación) |
| **OBJECTIVE** | Recolección/clasificación/despacho dentro del saldo (BR-02) · recepción en incubadora, carga (BR-03), ovoscopía, transferencia, nacimiento (BR-21) y despacho |
| **PRECONDITIONS** | Escenario `hatchery` (fixtures de pila completa); runtime desplegado |
| **ROLE** | Runtime: UAT-09 ⇒ montaje `hatchery` **403 X-BU por diseño** · Funcional: fixtures admin |
| **COMPANY** | Compañía 1 |
| **BUSINESS_UNIT** | `grandparent` (cuenta) / `hatchery` (proceso) |
| **FIXTURE** | Suite: lote `hatchery`; huevos 1000 ♀fértil; carga 800/900; ovoscopía; transferencia 850; nacimiento 800 = 780 sanos + 20 débiles (BR-21); despacho 700; negativos BR-03 (501 sobre 500) y sin recepción |
| **STEPS_EXECUTED** | 1) Sonda runtime: lotes `hatchery` ⇒ **403 X-BU por diseño** (misma evidencia que U3) · 2) Suite: happy path (saldo 0→1000→200 derivado), cadena completa de 8 pasos, BR-03 exceso rechazado sin consumir (detalle cita 500), sin recepción ⇒ rechazo, BR-02 en despacho de huevos, nacimiento Σ ≤ nacidos, RBAC/sin sesión |
| **EXPECTED_RESULT** | Casos de P-04/P-05 verdes; montaje runtime bloqueado por X-BU (documentado) |
| **ACTUAL_RESULT** | Runtime: 403 X-BU por diseño. Funcional: `proceso-p04-reproductoras-huevo-fertil.spec.ts` + `proceso-p05-incubacion.spec.ts` + `test_birth_classification.py`, `test_egg_*` verdes en la corrida final |
| **EVIDENCE** | `evidence/t13-uat/u3-u8-runtime-flow.log` · `evidence/t13-final/e2e-full.log` · `backend-full-suite.log` |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

---

## U5 · Engorde y cierre (P-06, OD-19)

| Campo | Valor |
|---|---|
| **UAT_ID** | U5 |
| **PROCESS** | P-06 (engorde hasta cierre) + mecánica de cierre verificada además en el ciclo GP real |
| **OBJECTIVE** | Cadena de engorde completa (inspección→recepción→distribución→ciclo→cierre), resumen del cierre correcto, fecha persistida, R7 (no cerrar con registros sin aprobar), FCR canónico Wave C (UNKNOWN≠0) |
| **PRECONDITIONS** | Escenario `broiler` (suites); runtime desplegado; lote GP 67 activo con eventos aprobados (para la mecánica de cierre real) |
| **ROLE** | Runtime: UAT-09 (GP) para la mecánica de cierre; aprobador R-153 para las cadenas · Funcional: fixtures admin |
| **COMPANY** | Compañía 1 |
| **BUSINESS_UNIT** | `grandparent` (cuenta) / `broiler` (proceso en suite) |
| **FIXTURE** | Runtime GP: lote 67 (recepción 100, alimento 380 kg aprobado). Suite broiler: 5.000 recibidas, 40 mortalidad, 15 descartes, 850,5 kg, pesaje 2.400 g, 9 eventos aprobados |
| **STEPS_EXECUTED** | 1) Runtime (GP, mecánica de cierre): primer cierre ⇒ **400** con regla legítima («sin registro de consumo de alimento (requerido para calcular FCR)») → alimento 380 kg registrado y **aprobado por cadena P-07 completa** → cierre ⇒ **200** con resumen `{total_feed_kg: 380.0, approved_events: 4, status: closed}` y `end_date=2026-09-16` **persistido en relectura** · 2) Suite: cadena completa 9 pasos + aprobaciones ⇒ cierre 200 con resumen (mortalidad 40, alimento 850.5, 9 eventos, `closed`), fecha del día (R-75), negativa R7 (sin aprobar ⇒ 400 `rule=R7`, lote sigue operativo), cierre tras reverso (R-192) y Wave C FCR |
| **EXPECTED_RESULT** | Mecánica de cierre real OK (GP) y cadena broiler completa verde con R7/FCR canónicos |
| **ACTUAL_RESULT** | Runtime GP: ciclo completo cerrado con resumen correcto y persistencia verificada. Funcional: `proceso-p06-pollo-de-engorde.spec.ts` + `proceso-p16-cutover-cargas-iniciales.spec.ts` + `test_lot_close_approval.py`, `test_lot_closure.py`, `test_lot_planned_close.py`, `test_r192_lot_close_after_reversal.py`, `test_ga_rem_022_wave_c_kpi.py`, `test_ga_rem_022_r131_r141.py` verdes en la corrida final |
| **EVIDENCE** | `evidence/t13-uat/gp-cierre-runtime.log` · `evidence/t13-final/e2e-full.log` · `backend-full-suite.log` · `kpi-regression.log` |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

**Observaciones U5**: la corrida runtime de la cadena broiler completa no es
posible con la cuenta del canal (BU `grandparent`; §Restricción); la mecánica de
cierre (el paso crítico histórico R-73/R-75/R-76) quedó verificada **en runtime
real** sobre el ciclo GP, y la cadena broiler por suite.

---

## U6 · Revisión y reverso (P-07)

| Campo | Valor |
|---|---|
| **UAT_ID** | U6 |
| **PROCESS** | P-07 (revisión, corrección, aprobación; OD-19 reverso interno) |
| **OBJECTIVE** | Bandejas (`in_review`/`returned`) · reverso con observaciones · historial de acciones · reenvío tras corrección · aprobación completa · notificación al operador |
| **PRECONDITIONS** | Lote GP 67 activo; operador + aprobador R-153 |
| **ROLE** | Operador (registro/submit/reenvío) + Aprobador (start/return/complete/approve) |
| **COMPANY** | Compañía 1 |
| **BUSINESS_UNIT** | `grandparent` |
| **FIXTURE** | Evento `weight_recording` (id 132, 10 aves, 150 g) sobre lote 67 |
| **STEPS_EXECUTED** | 1) Registro ⇒ **201** · 2) submit ⇒ **200** `pending_review` · 3) review/start ⇒ **200** `in_review` · 4) bandeja `status=in_review` ⇒ **200** (contiene el evento) · 5) `review/return` con observaciones ⇒ **200** `returned` · 6) bandeja `status=returned` ⇒ contiene · 7) historial `/review/events/132/actions` ⇒ **200** (2 acciones) · 8) reenvío (submit) ⇒ **200** `pending_review` · 9) start/complete/approve ⇒ **200/200/200** ⇒ estado final `approved` · 10) notificaciones del operador ⇒ `record_rejected` visible |
| **EXPECTED_RESULT** | Ciclo reverso→reenvío→aprobación completo (OD-17/R153-AC28/29); notificación emitida |
| **ACTUAL_RESULT** | Todos los pasos con el resultado exacto. Multinivel (AOD-17/R-142) y cancelación con motivo (AOD-18) **no aplican hoy** por decisión del propietario (`SCHEDULED`) |
| **EVIDENCE** | `evidence/t13-uat/u6-u7-runtime-flow.log` · suite: `proceso-03-revision-correccion-aprobacion.spec.ts` (heredada) + `test_r192_lot_close_after_reversal.py`, `test_internal_reversal.py`, `test_review_bu_enforcement.py` (corrida final) |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS** |

---

## U7 · Reportes y trazabilidad (P-15, P-10, P-09)

| Campo | Valor |
|---|---|
| **UAT_ID** | U7 |
| **PROCESS** | P-15 (reportes/KPIs) + P-10 (trazabilidad generacional) + P-09 (auditoría) |
| **OBJECTIVE** | KPIs corregidos (Wave C) · IPE (R-187 edad congelada) · trazabilidad de lotes · notificaciones propias · auditoría visible/filtrable |
| **PRECONDITIONS** | Lote GP 67 (runtime) · fixtures multi-BU (suites) |
| **ROLE** | Runtime: UAT-09 (notificaciones/trazabilidad sí; reports/audit **403 por rol**) · Funcional: admin |
| **COMPANY** | Compañía 1 |
| **BUSINESS_UNIT** | `grandparent` |
| **FIXTURE** | Runtime: lote 67 · Suite: tres generaciones P10 (repro→incub→engorde), KPIs de lote cerrado |
| **STEPS_EXECUTED** | Runtime: 1) `GET /notifications` + `unread-count` ⇒ **200** (unread=2; tipos `mortality_over_threshold`, `record_rejected`) · 2) `GET /lots/67/traceability` ⇒ **200** (claves `lot`, `egg_batches_*`, `chick_batches_*`) · 3) sondas de rol: `/reports/lot/67` ⇒ **403 `reports:read`**; `/reports/kpi/ipe/67` ⇒ **403**; `/audit` ⇒ **403 `audit:read`** (rol acotado). Suite: `proceso-p15-reportes-e-indicadores.spec.ts` (KPIs corregidos; tarjetas retiradas R-133/134), `proceso-p10-trazabilidad-generacional.spec.ts` (3 generaciones), `proceso-p09-auditoria-interna.spec.ts` (filtros reales), backend `test_r184/r186/r187`, `test_kpi_*`, `test_audit_*`, regresión KPI 142/0/35 |
| **EXPECTED_RESULT** | Notificaciones y trazabilidad en runtime conformes; KPIs/trazabilidad/auditoría completos por suite |
| **ACTUAL_RESULT** | Runtime conforme en lo permitido por el rol (403 por rol documentado). Funcional: conjuntos E2E y backend verdes en la corrida final |
| **EVIDENCE** | `evidence/t13-uat/u6-u7-runtime-flow.log` · `evidence/t13-final/e2e-full.log` · `kpi-regression.log` (`tests/test_ga_rem_022_*`, `test_r184/186/187`, `test_kpi_*`, `test_r204*`, `test_audit_reports.py`, `test_full_workflow_audit.py`) |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

**Observaciones U7**: sondas runtime de reportes/auditoría limitadas por rol del
canal (403 `reports:read`/`audit:read`); cobertura por suites con fixtures admin.

---

## U8 · Maestros y usuarios (P-12, P-13, P-11, P-14)

| Campo | Valor |
|---|---|
| **UAT_ID** | U8 |
| **PROCESS** | P-12 (maestros) · P-13 (administración de acceso) · P-11 (activación manual de lotes) · P-14 (notificaciones) |
| **OBJECTIVE** | Alta de maestros completa · edición/administración de usuarios y roles · activación manual de lote histórico (OD-10.c) · notificaciones internas |
| **PRECONDITIONS** | Fixtures admin (suites); runtime para notificaciones |
| **ROLE** | Runtime: UAT-09 sin `masters:create` (**403**); Funcional: admin |
| **COMPANY** | Compañía 1 |
| **BUSINESS_UNIT** | `grandparent` (cuenta); suite multi-BU |
| **FIXTURE** | Suite: alta de las 8 familias de maestros; roles/permisos; lote histórico breeder + fase inicial + apertura manual (4000 ♂ / 1000 ♀); notificaciones |
| **STEPS_EXECUTED** | Runtime: 1) altas de maestros (feed-types, vaccines, medications, mortality-causes, cull-causes, genetic-lines, suppliers, transports) ⇒ **403** (rol sin `masters:create`) · 2) activación manual ⇒ no ejecutable sin lote propio (BU) → **degradada** · 3) notificaciones ⇒ **200** (U7). Suite: `proceso-p11-activacion-manual-de-lotes.spec.ts` (6 reglas; idempotencia; apertura visible en `/lots/{id}/opening-balance`), `proceso-p12-datos-maestros.spec.ts` (altas/edición de maestros), administración de acceso (`test_access_administration.py`, `test_business_unit_admin.py`) y notificaciones (`proceso-p14-notificaciones.spec.ts`; GA-REM-038) |
| **EXPECTED_RESULT** | Altas/edición/activación/notificaciones verdes por suite; runtime limitado por rol |
| **ACTUAL_RESULT** | Runtime: 403 por rol documentado (alcance del canal). Funcional: suites P-11/P-12/P-13/P-14 verdes en la corrida final; UI de activación manual (OD-10.c) `SCHEDULED` (no exigida; capacidad backend certificada) |
| **EVIDENCE** | `evidence/t13-uat/u3-u8-runtime-flow.log` · `evidence/t13-final/e2e-full.log` · `backend-full-suite.log` |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

**Observaciones U8**: edición de usuario/roles (P-13) es superficie admin (los
fixtures de suite la cubren); el canal seguro del propietario no expone una
cuenta admin (subcasos admin-only `N/A-BY-OWNER-DECISION`, G-04).

---

**Cierre**: cada lote con resultado técnico propio, sin transitividad, sin
lenguaje de aceptación del propietario. Corridas finales sobre este árbol:
**E2E completo 133/133** (111 `procesos` + 22 `heredada`; un locator frágil
heredado corregido con evidencia rojo→verde) · backend **1441/0F/49S** ·
regresión KPI **142/0/35**. Contadores y rutas completas en
`evidence/t13-final/` y en `GLOBAL_AVICOLA_PRE_SAP_FINAL_CERTIFICATION.md` §7.
