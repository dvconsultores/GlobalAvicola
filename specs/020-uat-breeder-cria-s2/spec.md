# SPEC 020 — UAT Gestión Avícola · Reproductoras/Cría · Sesión 2
**Identificador:** `GA-UAT-BREEDER-CRIA-S2-2026-11-24` · **Fecha:** 2026-11-24
**Tipo:** enmienda mínima a `GA-REM-006` (correcciones), `GA-REM-021` (datos de operación) y a los filtros del Centro de Revisión. No es arquitectura nueva. Sin migración (cabeza Alembic `h3c4d5e6f7a8`).
**Entrada:** UAT de Yolinel del 24-11-2026 (empresa `QA Avícola Integral. C.A.`, usuarios `qa.admin` y `qa.pruebas.unidades`) sobre lo entregado en la Sesión 1 (SPEC 015).
**Baseline:** `develop` = `00fd162` (= runtime UAT, build del 22-11-2026 23:09Z); `main` = `1587073` (merge del PR #2, contiene develop).
**Fuera de alcance:** Cargas Iniciales, Progenitoras V3, Incubadora V4, O-19, SAP, workflows, ramas, PR y producción.

## 1. Gate 0 — runtime probado
El PDF no trae marca de versión (`YOLINEL_BACKEND_SHA` / `YOLINEL_FRONTEND_SHA` = `NOT_ACCESSIBLE`, inferido y no medido). Su historial de corrección está sellado 22/11/2026 15:22 (hora Caracas), antes del build `00fd162`: probó un build intermedio entre `8531d95` y `00fd162`, todos descendientes de la entrega de la Sesión 1 (`562c346`). Sus capturas muestran funciones de la Sesión 1 (campos corregibles por fila, código de lote en las listas, mínimos de pesaje, vacunación y alimento).

```
DEPLOYMENT_MISMATCH = NO · SESSION2_FINDINGS_VALID_FOR_CODE = YES · SESSION1_REGRESSION = NO
```
Cierre incompleto de la Sesión 1: `S1-ID-02` (filtro por código de lote) solo llegó al Historial, no a Revisión ni a Aprobaciones.

## 2. Hallazgos y disposición
| ID | Hallazgo | Clasificación | Disposición |
|---|---|---|---|
| **S2-A1/A2** | Corrección: el campo de maestro muestra el ID y no hay selector (8 campos: `supplier_id`, `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `destination_farm_id`, `destination_plant_id`, `transport_id`) | UX / NEW_REQUIREMENT (observación O-4 de la Sesión 1) | FIX (P2) |
| **S2-A3** | Corrección acepta tamaño de muestra negativo | **BUG P1** | FIX |
| S2-A3b | Corrección de peso promedio negativo | EXPECTED (ya da 400; solo falla el nombre técnico, ver A5) | NO-OP + test pin |
| S2-A4 | Corrección con peso promedio vacío se guarda | EXPECTED (`avg_weight` es opcional en recepción) | FIX parcial: campos no vaciables explícitos |
| **S2-A5** | Mensajes con nombre técnico (`bird_movements[642].avg_weight`) | UX P2 | FIX |
| S2-A6 | Corrección sin Tipo de corrección | OWNER_DECISION_REQUIRED (nullable en BD y esquema; ningún SPEC lo exige) | `OD-S2-01` |
| **S2-B1** | Filtro de lote de Revisión y Aprobaciones pide ID | UX P2 · cierre incompleto de S1-ID-02 | FIX |
| **S2-B2** | Cualquier rango de fechas en Revisión da error y no filtra | **BUG P2** | FIX |
| S2-C1 | Inspección de granja se guarda sin ningún valor | OWNER_DECISION_REQUIRED (contrato vigente S1 §4.2: granja + galpón + fecha) | `OD-S2-02` |
| S2-C2 | Inspección aprobada sigue sin lote | EXPECTED (decisión D1) + **BUG de UX P2**: la lista muestra «Se creará al aprobar» a cualquier evento sin lote | FIX del texto |
| S2-D1 | Recepción se guarda con proveedor, línea, galpón por fila y peso vacíos | EXPECTED (opcionales; `BR-08` y `BR-20` vigentes) | NO-OP |
| **S2-D2** | Recepción acepta muestra mayor que lo recibido | **BUG P1** | FIX |
| S2-E | Distribución se guarda con cero aves | OWNER_DECISION_REQUIRED (mortalidad, descarte, salida y despachos rechazan el cero; la distribución no tiene regla) | `OD-S2-03` |
| S2-F | Alimento sin Fase ni Tipo de alimento | EXPECTED (D2 de S1: solo kg > 0, `RR-23`) | NO-OP |
| S2-G | Pesaje sin Semana | OWNER_DECISION_REQUIRED | `OD-S2-04` |
| S2-H | Vacunación sin lote de vacuna | OWNER_DECISION_REQUIRED | `OD-S2-05` |
| S2-I/J | Mortalidad y descarte sin causa ni semana | OWNER_DECISION_REQUIRED | `OD-S2-06` y `OD-S2-04` |
| S2-I/J-b | Mortalidad/descarte «con todos los campos vacíos» | NOT_REPRODUCED (las capturas muestran cantidades cargadas; la mortalidad vacía sigue dando 400, `S1-MORT`) | NO-OP |

## 3. Criterios de aceptación
### 3.1 Validación de escritura (alta, edición y corrección comparten las mismas funciones)
| AC | Enunciado |
|---|---|
| **AC-S2-V01** | `RR-24` · `sample_size`, si se declara, es entero ≥ 1 (vacío = ausente; 0 y negativos ⇒ 400: «El tamaño de muestra debe ser mayor a cero»). Alta, edición y corrección; `bird_reception` y `weight_recording`. |
| **AC-S2-V02** | `RR-25` · En `bird_reception`, `sample_size` ≤ población recibida. Población = `received_total` si está declarado; si no, Σ `quantity` de `bird_movements` + `dead_on_arrival` (si se declaró). Igual ⇒ permitido; menor ⇒ permitido; mayor ⇒ 400 «La muestra tomada no puede superar las aves recibidas (N)»; población 0 con muestra declarada ⇒ 400. En `weight_recording` solo rige V01. La corrección revalida contra el estado persistido; el `PUT` evalúa el estado candidato. |
| **AC-S2-V03** | `RR-26` · `dosage_per_bird` ≥ 0 y `treatment_days` ≥ 0 en alta, edición y corrección. `chicks_healthy` / `chicks_weak` negativos ⇒ 400 también al corregir. |
| **AC-S2-V04** | Restricción de diseño: estas restricciones viven en las rutas de escritura (validadores y esquemas Create/Update), **no** en `OperationalEventBase` ni `OperationalEventRead`: hay filas históricas inválidas (p. ej. el evento 1115 de UAT con `sample_size = -1`) que deben seguir leyéndose. Ese dato no se toca. |

### 3.2 Correcciones
| AC | Enunciado |
|---|---|
| **AC-S2-C01** | La corrección de un campo del evento hereda el contrato del campo: el valor corregido se valida con las mismas reglas que el alta/edición (restricciones de `OperationalEventUpdate` y V01..V03), de modo que VALID(original) == VALID(corregido). |
| **AC-S2-C02** | Campos no vaciables: vaciar `event_date` ⇒ 400 en español; los que el contrato del tipo exige (`water_liters`, `vaccine_id`, `medication_id`, peso del pesaje) siguen sin poder vaciarse; los opcionales (p. ej. `avg_weight` de recepción, `sample_size`, `observations`, proveedor) sí. |
| **AC-S2-C03** | Todo error de una corrección usa el nombre funcional del campo en español (`sample_size` ⇒ «Tamaño de muestra», `avg_weight` ⇒ «Peso promedio», `week_number` ⇒ «Semana», `quantity` ⇒ «Cantidad», `quantity_kg` ⇒ «Cantidad de alimento (kg)», `water_liters` ⇒ «Litros de agua», `event_date` ⇒ «Fecha del evento», …) y nunca `bird_movements[..]`, `feed_movements[..]` ni nombres de columna. Excepción: el 400 de campo no corregible conserva los identificadores técnicos (contrato de API de la Sesión 1, `AC-S1-C03`; la UI no puede provocarlo). |
| **AC-S2-C04** | `GET /corrections/events/{id}/correctable-fields` añade, para los 8 campos de maestro, `master` (clave del catálogo: `suppliers`, `mortality-causes`, `cull-causes`, `vaccines`, `medications`, `farms`, `processing-plants`, `transports`) y `current_display` (nombre del registro actual); `current_value` sigue siendo el id (auditoría). |
| **AC-S2-C05** | `CorrectionRead` añade `original_display` y `corrected_display` (opcionales, calculados al leer) para que el historial muestre nombres y no ids en los campos de maestro. |
| **AC-S2-C06** | La referencia de maestro corregida debe pertenecer a la empresa (`BR-07`, ya garantizado por `verificar_destino_de_edicion`): un test lo fija. |
| **AC-S2-C07** | El formulario de corrección muestra un selector controlado (lista del catálogo) para los campos de maestro, con el valor actual por nombre; nunca un campo libre de ids. |

### 3.3 Filtros de Revisión
| AC | Enunciado |
|---|---|
| **AC-S2-R01** | `GET /review/pending` y `GET /approvals/pending` aceptan `lot_code` (parcial, insensible a mayúsculas, con escape de `%` y `_`, mismo patrón que `GET /operations`) dentro del alcance de empresa y unidad; `lot_id` se conserva. |
| **AC-S2-R02** | `date_from` y `date_to` de `GET /review/pending` se tipan como fecha; límites inclusivos; solo inicio, solo fin, mismo día y rango válido ⇒ 200 y filtran; inicio > fin ⇒ 400 «La fecha inicial no puede ser posterior a la fecha final». `/approvals/pending` no declara fechas y no las gana en este ciclo. |
| **AC-S2-R03** | `ReviewCenter` y `ApprovalPanel` filtran por **código** de lote (texto, debounce 400 ms, sin validación numérica); el rango de fechas valida inicio ≤ fin en el cliente con un único mensaje en español. |

### 3.4 UX de inspección
| AC | Enunciado |
|---|---|
| **AC-S2-U01** | En la lista de Operaciones la celda Lote muestra el código; sin lote: «Se creará al aprobar» solo para `grandparent_import`; para cualquier otro evento «Sin lote (nivel granja)» (claves i18n `es` y `en` en `frontend/public/locales/{es,en}/translation.json`). |

## 4. Decisiones Owner pendientes
| ID | Decisión | Recomendación |
|---|---|---|
| **OD-S2-01** | Tipo de corrección obligatorio | Sí, solo para correcciones nuevas, en cliente y servidor |
| **OD-S2-02** | Contenido mínimo de la inspección de granja | A definir por la Owner |
| **OD-S2-03** | Distribución: suma de aves > 0 | Sí, como el resto de movimientos de aves |
| **OD-S2-04** | Semana: obligatoria vs derivada de la fecha y el inicio del lote (pesaje, mortalidad, descarte) | Derivada y editable |
| **OD-S2-05** | Lote de vacuna obligatorio | No hasta definir la trazabilidad sanitaria |
| **OD-S2-06** | Causa de mortalidad/descarte obligatoria | Sí, con valor desconocido/otra válido |

## 5. Pruebas esperadas
Backend: `CORR-S2-01..10` (proveedor por descripción, selector de proveedor, selector de medicamento, muestra negativa DENY, peso negativo DENY, vaciar requerido DENY, vaciar anulable ALLOW, nombres funcionales, auditoría original→corregido preservada, referencia de otra empresa DENY), `REV-S2-01..05` (código de lote, rango válido, un solo día, rango inválido, Aprobaciones con el contrato de lote) y `OPS-S2-01..11` (pines del contrato vigente: inspección mínima, inspección sin contenido permitida hasta decisión, recepción mínima, muestra mayor DENY / igual / menor ALLOW, distribución vacía permitida hasta decisión, alimento mínimo, pesaje con semana manual o vacía, vacunación sin lote de vacuna, mortalidad mínima, descarte mínimo).
Frontend: selector de maestro y nombres en el formulario de corrección, filtros por código y rango de fechas, texto de la celda Lote.
E2E: Recepción → Revisión → Corrección → Aprobación (maestro original, cambio de maestro por selector, campo numérico, error de rango, auditoría) y los eventos operativos con mínimos válidos y negativos.
Cierre: regresión completa sin tests relajados, sensibilidad tras el commit de implementación y restauración explícita por SHA.
