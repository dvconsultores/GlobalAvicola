# SPEC 015 — UAT Gestión Avícola · Reproductoras/Cría · Sesión 1
**Identificador:** `GA-UAT-BREEDER-CRIA-S1-2026-11-10` · **Fecha:** 2026-11-18
**Tipo:** enmienda mínima a `GA-REM-006` (correcciones), `GA-REM-040` (unidad de negocio y pendientes) y `GA-REM-021` (datos obligatorios). No es arquitectura nueva.
**Entrada:** UAT de Yolinel del 10-11-2026 (empresa QA `Avícola Integral`, usuarios `qa.admin` y `qa.pruebas.unidades`). Baseline HEAD `7ff5451`.

## 1. Decisiones Owner (2026-11-18)
| ID | Decisión |
|---|---|
| **D1** | **Inspección de granja sin lote:** derivar la unidad de negocio (BU) de la granja cuando sea **inequívoca** y, si no, dejar el evento **pendiente de clasificar** con **bandeja visible en la UI** (el autor y el control autorizado la ven siempre). Resuelve `GL-OD-13` / `C-02` con la **opción A** y el respaldo de la opción B. «Inequívoca» = **todos los lotes no cancelados de esa granja pertenecen a una única cadena** (`Lot.bird_type`) **y esa unidad está efectiva para el actor**; **no** se deriva por nombre de granja ni por rol (`GA-REM-040 §11.4`). |
| **D2** | **Regla mínima «no vacío»** para pesaje, vacunación, medicación y alimento: el dato requerido debe tener valor, sin exigir rangos ni catálogos nuevos. |
| **D3** | El **transporte en salida de aves sigue OPCIONAL** (sin cambio). |
| **D4** | El saldo de mortalidad/descarte/salida se mantiene por **TOTAL de aves vivas**, **no por sexo**: se documenta y se fija con un test. |

## 2. Hallazgos y disposición
| ID | Tipo | Sev | Disposición |
|---|---|---|---|
| **S1-BU-01** | UX/BUG | P2 | FIX — las pestañas de BU en Lotes ignoran las unidades efectivas. |
| **S1-BU-02** | EXPECTED | — | NO-OP — el aislamiento por BU ya es *fail-closed*; se prueba por **E2E API/IDOR**. |
| **S1-ID-01** | UX/BUG | P2 | FIX — el detalle de lote/evento/revisión muestra identificadores numéricos. |
| **S1-ID-02** | UX/BUG | P2 | FIX — falta el filtro por **código de lote**. |
| **S1-I18N-01** | UX/BUG | P2 | FIX — estados y acciones crudos: `active`, `registered`, `approved`, `corrected`, `no_curve_assigned` y los 5 códigos restantes de curva, `start`, `return`, `started_review`. |
| **S1-TRACE-01** | MISSING CONTRACT | P1 | FIX por **D1** — `farm_inspection` sin lote desaparece de la trazabilidad. |
| **S1-CORR-01** | MISSING CONTRACT | P1 | FIX — el formulario de corrección solo ofrece «Observaciones» y los submovimientos no son corregibles. |
| **S1-REP-01** | UX/BUG | P2 | FIX — `ReportsPage` arranca con el lote fijo `2` y «Volver» lleva siempre a `/reports`. |
| **S1-REP-02** | UX/BUG | P2 | FIX — exportes PDF/Excel con `bird_type` y `end_date` vacíos y estado crudo. |
| **S1-UX-01** | UX/BUG | P2 | FIX — el *toast* se muestra bajo el *overlay*. |
| **S1-FLT-01** | UX/BUG | P2 | FIX — el filtro de lote dispara una petición por tecla y muestra el `422` en inglés repetido. |
| **S1-VAL-01** | MISSING CONTRACT | P1 | FIX — obligatorios (ver §4). |
| **S1-WATER** | UAT_EVIDENCE_INSUFFICIENT | — | El servidor ya exige `water_liters > 0`; **no** se declara PASS/FAIL del UAT. |

## 3. Correcciones (enmienda a GA-REM-006 · alcance 2 «mapa campo→destino»)
**Sin migración.** El campo corregido de un **submovimiento** se identifica en `CorrectionLog.field_name` con la forma `bird_movements[<id>].<campo>` o `feed_movements[<id>].<campo>`, donde `<id>` es el **id de la fila destino** (sin ambigüedad).

**Campos corregibles de submovimiento:** `bird_movements.avg_weight`, `bird_movements.quantity`, `bird_movements.week_number` y `feed_movements.quantity_kg`. La **cantidad de `bird_movements` de `bird_reception` en lotes breeder NO es corregible** (identidad `BR-20`; mismo criterio que `NO_CORREGIBLES_POR_IDENTIDAD`).

**Revalidación:** se revalidan las reglas con el valor corregido (`BR-01` para mortalidad/descarte/salida **excluyendo el propio evento**; cantidad > 0).

**Endpoint nuevo de lectura:** `GET /corrections/events/{event_id}/correctable-fields` devuelve la lista de campos **corregibles reales de ESE evento** (campo, clave de etiqueta, valor actual, id de fila si aplica). El formulario consume ese endpoint (no `observations` fijo). Mensajes en español, **sin `alert()`**.

| AC | Enunciado |
|---|---|
| **AC-S1-C01** | Corregir `avg_weight` de un pesaje en revisión aplica el valor y conserva original, corregido, motivo, usuario y fecha. |
| **AC-S1-C02** | Corregir la cantidad de mortalidad por encima del saldo ⇒ **400** y nada cambia. |
| **AC-S1-C03** | Campo no corregible ⇒ **400** con la lista de campos corregibles. |
| **AC-S1-C04** | El detalle de revisión muestra campo (etiqueta traducida), original→corregido y motivo. |
| **AC-S1-C05** | Requiere permiso `review:correct`, estado corregible y empresa/BU del evento. |

## 4. Obligatorios (enmienda a GA-REM-021)
### 4.1 Servidor — nuevas reglas `RR-20`..`RR-23`
| Regla | Requisito |
|---|---|
| **RR-20** | Pesaje: al menos una fila con `avg_weight > 0`. |
| **RR-21** | Vacunación: `vaccine_id` presente. |
| **RR-22** | Medicación: `medication_id` presente. |
| **RR-23** | Alimento: al menos una fila con `quantity_kg > 0`. |

*(Verificado: `RR-20` en adelante no existían; el máximo vigente era `RR-19`.)* Mensajes en **español**, orientados al campo, **sin código interno**.

### 4.2 Cliente
- **Inspección de granja:** el galpón sigue siendo obligatorio (`BR-08`, ya en servidor) **y el cliente debe exigirlo**.
- **Agua:** el cliente exige litros > 0. **Mortalidad/descarte/salida:** el cliente exige cantidad total > 0.
- **Sin autorrellenar `0`:** vacío = ausente, `0` = cero conocido.
- **NO** se hace obligatorio **Orden SAP**. **«Semana»** no lleva valor por defecto (el `1` es solo *placeholder* y se rotula como ayuda).
- **Pesaje:** el cliente **no descarta en silencio** un peso sin cantidad.

### 4.3 Matriz por operación
| Operación | Servidor | Cliente | Decisión |
|---|---|---|---|
| Inspección | granja + galpón | exigir galpón | Paridad cliente-servidor (`BR-08`) |
| Recepción | `BR-08` + `BR-20` (breeder) | sin cambio | Sin cambio |
| Distribución | ubicación | ya exige galpón | Sin cambio |
| Alimento | +`RR-23` | marcar y exigir | D2 |
| Agua | litros > 0 | exigir | D2 (servidor ya cumple) |
| Pesaje | +`RR-20` | exigir peso | D2 |
| Vacunación | +`RR-21` | — | D2 |
| Medicación | +`RR-22` | — | D2 |
| Mortalidad / Descarte | `BR-01` | exigir cantidad | D2 |
| Salida | `BR-01` + `BR-08` | transporte y destino **OPCIONALES** | D3 |

## 5. Trazabilidad de inspección (enmienda a GA-REM-040 §11)
Al crear una `farm_inspection` **sin lote**:
- Si la unidad se **deriva** por **D1**, se persiste en `operational_events.business_unit_id` (patrón `R-221` `hatchery_inspection`) con la **guarda de unidad operativa**.
- Si **no es inequívoca**, el evento **nace pendiente de clasificar**.

La UI expone la **bandeja de pendientes** (`/operations/pending-classification`, **solo lectura**) consumiendo `GET /operations/pending-classification` (ahora con nombres de granja/galpón/registrado por) y enlazada desde el Historial; el **autor ve sus propios pendientes** y el control autorizado los de su empresa. La **clasificación** sigue por el endpoint existente `POST /operations/{id}/classify` (permiso `masters:update`); **no** se añade un selector de unidad en la UI porque la API de unidades no expone el id interno de la habilitación (decisión de seguridad `GA-REM-040`); exponerlo o clasificar por código queda como **decisión de diseño pendiente del Owner** (observación O-3).

| AC | Enunciado |
|---|---|
| **AC-S1-T01** | Inspección con granja de **una sola cadena** nace con BU derivada y aparece en Historial, detalle, Revisión y Aprobaciones. |
| **AC-S1-T02** | Inspección con granja **multicadena** nace pendiente, aparece en la bandeja del **autor** y del **control autorizado**, y **NO** en listados de otra unidad. |
| **AC-S1-T03** | Clasificarla (por API) deja **rastro auditado** (cobertura previa `test_pending_classification.py`). |
| **AC-S1-T04** | **No** se crea una unidad falsa «SIN ASIGNAR». |

## 6. Identidad, i18n, reportes, UX
| AC | Enunciado |
|---|---|
| **AC-S1-I01** | `GET /lots/{id}` y `GET /operations/{id}` devuelven `farm_name`, `house_name` y `lot_code` (**nuevo `house_name` en el evento**) y las pantallas de detalle/revisión los muestran en lugar de identificadores numéricos. |
| **AC-S1-I02** | `GET /operations` acepta `lot_code` (coincidencia **parcial** e **insensible a mayúsculas**) dentro del alcance de empresa/BU. |
| **AC-S1-I03** | Todos los estados (`lotStatus.*`, `status.*`), los **6** códigos de evaluación de curva (`no_curve_assigned`, `lot_without_start_date`, `lot_without_genetic_line`, `curve_without_points`, `event_before_lot_start`, `age_outside_curve_table`) y las acciones `start`, `return`, `started_review` se muestran traducidos en **es** y en **en**. |
| **AC-S1-R01** | La pantalla de reportes **no** arranca con un lote fijo: selecciona el primero visible o muestra estado vacío, y «Volver» del reporte de lote regresa a la **pantalla de origen**. |
| **AC-S1-R02** | `GET /reports/lot/{id}` añade `bird_type`, `end_date`, `farm_name` y `house_name`, y los exportes **PDF/Excel** los usan con estados traducidos. |
| **AC-S1-U01** | El *toast* se ve **por encima** de cualquier modal o `ConfirmDialog`. |
| **AC-S1-F01** | Los filtros de lote (Revisión, Aprobaciones, Historial) esperan **400 ms** antes de pedir, validan formato en el cliente y muestran **como máximo un** mensaje en español. |
| **AC-S1-B01** | La lista de lotes muestra solo las pestañas de las **unidades efectivas** del usuario (incluida incubadora si es efectiva) y un **estado explícito en español** si no tiene ninguna; el servidor acepta `bird_type` **opcional** en `GET /lots` sin ampliar el alcance de BU. |
| **AC-S1-U02** | El contenedor de *toasts* se monta en un **portal sobre `document.body`** (el `z-index` por sí solo no basta: el overlay del `ConfirmDialog` está en otro contexto de apilamiento). |
| **AC-S1-U03** | El diálogo de **rechazo** de Aprobaciones incluye el **campo de motivo** (≥ 10 caracteres, validado en el cliente con un único mensaje inline); antes el rechazo era imposible de completar. |
| **AC-S1-M01** | Los mensajes de las operaciones de la matriz (§4) no contienen códigos internos (`BR-`, `RR-`, nombres de campo técnicos); la regla viaja en el campo `rule`. Se reescribieron los 4 mensajes de `water_consumption`. Los `422` de validación estructural de pydantic siguen en inglés en la API; la interfaz los muestra en español («Valor no válido en «campo»» / «Falta el dato obligatorio «campo»»). |

## 7. Fuera de alcance
Saldo por sexo (**D4**), transporte obligatorio (**D3**), SAP real, **migraciones**, otras BU salvo infraestructura compartida.

## 8. Pruebas y certificación
| Ámbito | Suites / casos esperados | Estado |
|---|---|---|
| Backend | Correcciones por submovimiento + `correctable-fields` · `RR-20..RR-23` de obligatorios · trazabilidad de `farm_inspection` (derivación y pendiente) · `GET /lots/{id}`, `GET /operations` (`lot_code`), `GET /reports/lot/{id}` · aislamiento por BU **fail-closed** (S1-BU-02) · D4 saldo por total con test | *a rellenar en la certificación* |
| Frontend (`vitest`) | i18n de estados/acciones y códigos de curva · formulario de corrección dinámico · filtro con *debounce* y mensaje único · *toast* sobre modal · reportes sin lote fijo y «Volver» al origen · pestañas de unidades efectivas | *a rellenar en la certificación* |
| E2E | Circuito **reproductoras 18 pasos** · corrección con **peso promedio** · **inspección** (derivada y pendiente + bandeja) · **obligatorios por operación** | *a rellenar en la certificación* |
| Cierre | Regresión completa sin rojos y sin tests relajados | *a rellenar en la certificación* |

## 9. Observaciones no bloqueantes
| ID | Observación | Tratamiento |
|---|---|---|
| **O-1** | El detalle de evento no publica `id` por fila de submovimiento. | Las correcciones usan `row_id` de `correctable-fields`; no requiere cambio de contrato. |
| **O-2** | Los `422` de validación estructural de pydantic llegan en inglés desde la API. | La UI los traduce a español; límite documentado. |
| **O-3** | La clasificación de pendientes solo está disponible por API (`POST /operations/{id}/classify`). | Ver §5: la UI expone la bandeja en solo lectura; el selector de unidad queda pendiente de decisión del Owner. |
| **O-4** | Las correcciones de campos de catálogo (`cause_id`, `vaccine_id`, …) se hacen por código numérico. | Sin selector en el formulario; funcional pero poco ergonómico. |
| **O-5** | El usuario sembrado `test_approver` no tiene `review:read`. | Dato de pruebas, no de producto; se ajusta en el seed si se automatiza el UAT. |
| **O-6** | `POST /operations` sobre un lote de otra unidad responde 400 «Lote no encontrado». | Anti-enumeración, comportamiento previo; se mantiene. |
| **O-7** | AC-S1-WATER: sin evidencia suficiente en el UAT original (`UAT_EVIDENCE_INSUFFICIENT`). | El servidor ya exigía litros > 0 y ahora la interfaz también. |

