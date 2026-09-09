# `R-130` · EL SALDO DE AVES NUNCA ES NEGATIVO — EVIDENCIA

**WAVE B · tranche 1** · 2026-09-09 · spec `GA-REM-005` enmienda B (`ed2c61f`) · implementación
`07f71d7` · origen `H360-P01` · requisito raíz: invariante del propietario «la población nunca es
negativa» · `spec.md BR-01` · `docs/02 §5 R1` · Recomendación central §17 · `GA-REM-005 E.3`

```
R-130   CERRADO (técnicamente)   descarte · salida · despacho de pollitos validados contra el saldo real, bajo bloqueo de fila
        21/21 objetivo · rojo previo 11/21 · sensibilidad 6 válidas + 1 N/A · relacionadas 407/407
        certificación de proceso (P-01/P-03/P-05/P-06): BLOCKED_RUNTIME (E2E no disponible) — no se reclama
```

## 1. Causa raíz y comportamiento previo

`_apply_business_rules` validaba una sola de las cuatro salidas del saldo (`E.3`): la mortalidad
(`BR-01`). `cull_recording` y `bird_exit` no tenían rama; `chick_dispatch` se validaba contra un
«viable» = nacidos − despachados, que ignoraba mortalidad y descartes. `BirdMovementSchema.quantity`
admite `0`. El saldo se leía sin bloqueo (sesión por petición, `READ COMMITTED`).

Rojo previo (`scratchpad/r130_red.txt`, contra `ed2c61f`): **11 FAIL · 10 PASS**.

| Prueba | `AC` | Esperado | Observado | Por qué es un rojo válido |
|---|---|---|---|---|
| `ac02` exacto + 1 | `AC-R130-02` | `400 BR-01` | `201` | descarte con saldo 0 aceptado |
| `ac03` descarte 101 / salida 101 sobre 100 | `AC-R130-03` | `400 BR-01` | `201` (×2) | población negativa |
| `ac04` descarte 0 / salida 0 | `AC-R130-04` | `400 BR-01` | `201` (×2) | dato sin significado admitido |
| `ac05` sin rastro | `AC-R130-05` | rechazo | `201` | la fila y el movimiento se escribieron |
| `ac06` secuencia → salida 1 con saldo 0 | `AC-R130-06` | `400` | `201` | saldo −1 |
| `ac08` progenitoras (×2) | `AC-R130-08` | `400` | `201` | verificado sobre `grandparent`, no inferido |
| `ac09` despacho 90 con viable real 85 | `AC-R130-09` | `400 BR-04` | `201` | saldo del lote de incubación −5 |
| `ac10` tres descartes concurrentes de 60 sobre 100 | `AC-R130-10` | `[201, 400, 400]` · saldo 40 | **`[201, 201, 201]` · saldo −80** | carrera real reproducida |
| controles (10) | `AC-R130-01/07/11/12/13/14` | — | **PASS** | mortalidad ya rechazada · negativo por esquema · cancelación · idempotencia · lote ajeno `400 BR-07` · cerrado · ubicación ajena · RBAC `403` · sin migración |

Ninguno de los 11 cayó por fixture, autenticación, ruta, permiso o excepción ajena.

## 2. Implementación (`07f71d7`)

| Archivo | Cambio |
|---|---|
| `operations/validators.py` | `bloquear_saldo_del_lote` (`SELECT lots.id … FOR UPDATE`) · `validate_bird_decrement(db, lot_id, quantity, etiqueta)` (`> 0`, bloqueo, `≤ saldo`, `BR-01`) · `validate_mortality` delega en él (mensajes intactos) · `get_viable_chick_balance` resta mortalidad y descartes · `validate_chick_dispatch` bloquea antes de leer |
| `operations/service.py` | ramas `CULL_RECORDING` / `BIRD_EXIT` → `validate_bird_decrement("descarte" \| "salida")`; import |
| migración | **ninguna** (`s9t0u1v2w3x4`) · rutas: 208, sin cambio · frontend: ninguno · SAP: ninguno |

Invariante en el código: `cantidad > 0 ∧ cantidad ≤ SALDO(lote)` con `SALDO = apertura + recepción +
nacimientos − mortalidad − descarte − salida − despacho` (eventos no cancelados), evaluado tras el
bloqueo de la fila del lote. La validación precede a `db.add`: un rechazo no escribe evento,
movimiento, alerta ni auditoría (`AC-R130-05`, verificado por recuento antes/después).

## 3. Verde

```
tests/test_population_invariant.py ............ 21 passed
relacionadas (mortalidad · KPI incubadora · flujo completo · saldo de apertura · cierre de lote ·
trazabilidad · linaje · aislamiento multiempresa · filas por unidad · unidades · guarda · admin ·
OD-14 superficies · smoke · KPI por unidad · alertas de peso · operaciones · persistencia P0-14 ·
notificaciones · clasificación pendiente · traspasos) ........ 407 passed · 0 ajustes
```

## 4. Sensibilidad

| Mutación | Retira | Instalada / ejecutada | Rojas | Motivo | Validez |
|---|---|:--:|---|---|:--:|
| `S1` | la cota superior (`if quantity > balance` → `if False`) | sí / sí | **9**: `ac02`, `ac03` ×3 (incluida la mortalidad, que delega), `ac05`, `ac06`, `ac08` ×2, `ac10` | decrementos por encima del saldo aceptados con `201`; saldo negativo observado | válida |
| `S2` | `CULL_RECORDING` de las salidas del saldo | sí / sí | **8**: `ac01` (saldo 60 ≠ 50), `ac02`, `ac06`, `ac07`, `ac08`, `ac09`, `ac10`, `ac11` | saldo sobrestimado: el resultado real queda negativo | válida |
| `S3` | el bloqueo (`FOR UPDATE` retirado, misma consulta) | sí / sí | **1**: `ac10` | tres descartes concurrentes de 60 aceptados: carrera reproducida sin el bloqueo | válida |
| `S4` | puerta de unidad | — | `N/A` | la creación no está acotada por unidad (`R-160`, tranche 2): no hay propiedad que retirar | n/a |
| `S5` | el filtro de empresa en `validate_lot_active` | sí / sí | **1**: `ac12` lote ajeno | el actor de B descarta sobre el lote de A | válida |
| `S6` | el rechazo de cero (`<= 0` → `< 0`) | sí / sí | **2**: `ac04` ×2 | descarte y salida de cero aves aceptados | válida |
| `S7` | mortalidad y descartes del «viable» (cálculo anterior) | sí / sí | **1**: `ac09` | despacho de 90 con 85 viables aceptado | válida |

```
intentadas 6 · inválidas 0 · reconstruidas 0 · válidas 6 · N/A 1 · reversión git diff --quiet · residuo MUTACION 0
```

## 5. Regresión

Backend **851 passed · 49 skipped · 0 failed** (589 s; 830 previas + 21 de `test_population_invariant.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Primera pasada: 850/49/**1** — `test_master_management.py::test_t_090_06` descartaba 3 aves sobre el lote sembrado con saldo 0 (fixture que dependía del defecto); ajustada con recepción previa (`T-130-01b`, aserción intacta) y regresión repetida entera hasta leerla en verde. Vitest 87 passed / 8 archivos. `tsc -b --noEmit`: 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y ficheros que la línea base `R-158`. Seguridad y unidad dentro de la suite: `test_od14_productive_surfaces` 35 · aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15) · clasificación pendiente 35 · `test_mortality` 18 · KPI incubadora 7 · flujo completo 23 · multiempresa 5 + 12 — todo verde. E2E: `BLOCKED_RUNTIME`.

## 6. Inquilino · unidad · RBAC · decisiones

- **Inquilino**: `validate_lot_active(company_id)` y `verificar_ubicacion` intactos (`ac12` ×2; `S5`). `OD-14`: `test_od14_productive_surfaces` 35 verdes en las relacionadas.
- **Unidad** (`OD-16`): habilitaciones sembradas explícitamente (`is_enabled=True` asertado); el invariante no depende de `BU-D10`. La creación de eventos **no** está acotada por unidad hoy: `R-160` (P1, tranche 2), fuera de este alcance y registrado; esta tranche no lo empeora ni lo mejora.
- **RBAC**: `require_permission("operations","create")` intacto (`ac12` sin permiso → `403`).
- **Progenitoras**: `AC-R130-08` sobre un lote `grandparent` propio, no inferido de `breeder`.
- **Administrador de Accesos / Contraloría / SAP transversal**: sin superficie afectada (`test_access_administration`, `test_session_payload` verdes en la regresión).
- **Auditoría**: un rechazo no deja `audit_logs`; un descarte aceptado sí (`audit_event_created`, sin cambio).
- **Concurrencia**: dentro del alcance (mismo invariante) y probada (`AC-R130-10`, `S3`); los saldos de huevos e incubación (`BR-02`/`BR-03`) siguen sin bloqueo → `R-161` (P2, registrado).

## 7. Cierre

`AC-R130-01…14` verdes · `AC-R130-15` `N/A` con evidencia (`R-160`) · rojo previo válido · `S1–S7`
según `§4` · relacionadas y regresión completa verdes · sin migración · sin rutas · sin frontend ·
sin SAP → **`R-130 CERRADO`** en su frontera técnica. La certificación de los procesos afectados
(`P-01`, `P-03`, `P-05`, `P-06`, `P-11`) como **procesos de negocio** sigue exigiendo E2E válida:
`BLOCKED_RUNTIME`, no se reclama.
