# R-194 · FINDING — CADENA DE INCUBADORA BLOQUEADA POR UI (BR-08 · SALDO BR-03 · `arrival_date` · DOSIS · `hatchery_id`)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-194** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | La recepción de huevos en incubadora no puede registrarse por UI (BR-08 por `farm_id` ausente; `arrival_date` 422; el saldo BR-03 no recibe los fértiles porque el formulario no escribe `egg_movements[fertile]`), el nacimiento se bloquea en silencio (`dosage_per_bird` sin `valueAsNumber`) y el despacho de pollitos cae en BR-08 |
| **Severidad** | **P1** (§49: cadena P-05 completa inalcanzable por UI; traspaso X-BU roto aguas arriba) |
| **Clase** | `REQUEST_CONTRACT` / `BROKEN_FLOW` (familia F-01) |
| **Proceso** | P-05 (incubación), P-10 (trazabilidad, aguas abajo), X-BU (traspaso), P-15 (KPI incubadora) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | B-01/B-02/B-03/B-05/B-22/B-33 (informe B); F-01b (documentó `arrival_date` sin hallazgo); suites `p05`/`p10` no reproducibles (GA-GOV-03) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-194/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (cadena de incubadora entera: nacimientos/despachos = datos de origen) |
| **UAT del propietario** | sí (cadena visible; agrupable con R-190/R-205) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- **B-01 · granja/galpón**: `OperationFormPage.tsx:274-278` (`HATCHERY_EVENTS`) y `:438` — en etapa incubadora `farm_id` se fuerza a `undefined`; `egg_reception_hatchery` y `chick_dispatch` están en `location_events` (`validators.py:828-832`) ⇒ BR-08 exige granja/galpón y la UI nunca los envía ⇒ **400 siempre**.
- **B-02 · saldo BR-03**: `:1219` — «Huevos recibidos» viaja en `egg_storage_records.0.eggs_received`; el saldo de incubadora lee `egg_movements[egg_type='fertile'].quantity` (`validators.py:149-175,156-164`; `service.py:956-960`) ⇒ `incubation_load` siempre «disponibles (0)» ⇒ **400 BR-03**.
- **B-03 · `arrival_date`**: `:170-177,1218-1236` — no se captura; `EggStorageSchema.arrival_date` es **requerido** (`schemas.py:85-87`) ⇒ 422 en cuanto se rellena cualquier campo de almacenamiento (F-01b).
- **B-05 · dosis**: `:1651` — `register('dosage_per_bird')` **sin `valueAsNumber`** ⇒ `''` ⇒ `z.number().optional()` falla y `handleSubmit` no llama a `onSubmit` sin renderizar error ⇒ **envío silencioso** en `birth_registration` (clase F-01d; contraste correcto en vacunación `:581`).
- **B-22 · `hatchery_id`**: `:139-149,2044-2056` — selector de incubadora local que **nunca viaja**; `schemas.py:101` con tenencia `service.py:873-877`.
- **B-33**: `egg_dispatch` usa `hatchery_params.0.incubator_id` como «incubadora destino» (uso semántico dudoso; se documenta, no se rompe).

### 1.2 Evidencia runtime local (2026-09-13, `ui-e2e-local-pass2.json`, PNG `P2-C0x`)

| Caso | Resultado |
|---|---|
| `HAT2-00` alta de lote incubadora | 201 |
| `HAT2-01` `hatchery_inspection` | 201 |
| `HAT2-02` `egg_reception_hatchery` | **422** `egg_storage_records.0.arrival_date Field required` |
| `HAT2-02b` recepción sin almacenamiento | **400 BR-08** «requiere una granja asignada» (`farm_id` forzado a `undefined`) |
| Sonda API sin storage | 201, pero `HAT2-02-saldo-tras-recepcion-ui`: carga ⇒ **400 BR-03 … disponibles (0)** (la UI no escribió fértiles) |
| `HAT2-03` clasificación | 201 |
| `HAT2-04` `incubation_load` | **sin petición** (bloqueo cliente) |
| `HAT2-05/06` ovoscopía / transferencia | 201 |
| `HAT2-07` nacimiento | **envío silencioso** (con y sin dosis) — sonda API 201 |
| `HAT2-08` `chick_dispatch` | **400 BR-08** |

### 1.3 Suites

`e2e/proceso-p05-incubacion.spec.ts` falla en HEAD por BR-21 (fixture obsoleto; GA-GOV-03) y BR-04 en cascada ⇒ la certificación P-05 no es reproducible; el defecto de UI es independiente y persiste tras la corrección de fixtures.

## 2 · Causa raíz

Cinco defectos de contrato del asistente en la etapa incubadora, acumulados por tranches: (a) derivación de ubicación excluida de la etapa sin exención BR-08; (b) el saldo de incubadora lee movimientos de huevo que el formulario no escribe; (c) campo requerido no capturado; (d) input sin `valueAsNumber` que bloquea la validación en silencio; (e) selector de incubadora sin camino al payload.

## 3 · Impacto

- **P-05 completa cortada**: sin recepción válida no hay saldo fértil, carga, ovoscopía con sentido, nacimiento ni despacho; X-BU (traspaso a engorde/reproductoras) imposible por UI.
- P-10 (trazabilidad) sin eventos que produzcan vínculos; P-15 incubadora sin datos reales de UI.
- Los operadores no tienen rodeo legítimo (API/SQL fuera de norma).

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | F-01b documentó `arrival_date` como observación sin hallazgo; R-189 dejó «etapa incubadora: sin cambio». No existe hallazgo de la cadena. |
| GA-REM-001…042 | `GA-REM-021` (datos del cliente) no cubre B-01/B-02/B-03/B-05/B-22. |
| Informes B/E | B-01…B-33 + `E_domain_ledger` concuerdan; registro G-05 lo eleva a P1. |

Conclusión: **nuevo**; ID asignado **R-194**.

## 5 · Propietario sugerido

Frontend (asistente) + dominio para C-01 (granja/galpón de la etapa incubadora) y C-02 (`arrival_date` capturada vs derivada). Tranche conjunta con R-190/R-205 (misma familia) o inmediatamente después.

## 6 · Bloquea SAP y por qué

**SÍ.** Incubadora produce nacimientos y pollitos despachados (eventos de origen para SAP y para el traspaso interno). Una cadena inalcanzable por UI rompe P-05/P-10/X-BU y la certificación pre-SAP.

## 7 · Interdependencias

- **R-190/R-205** (familia del asistente): misma tranche o contigua; comparten `onSubmit`/serializadores.
- **R-204** (KPI incubadora sin unidad): mismo dominio, paquete aparte.
- **GA-GOV-03**: fixtures p05/p10; la corrección de R-194 habilita la recertificación real de P-05.
- **OD-19/§18**: huevos no reversibles (intacto).
