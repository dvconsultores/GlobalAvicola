# Hallazgos UAT — Reproductoras/Cría Sesión 1 (tabla maestra)

| Campo | Valor |
|---|---|
| **Mandato** | `GA-UAT-BREEDER-CRIA-S1-2026-11-10` |
| **Baseline HEAD** | `7ff5451` |
| **Implementación (IMPL)** | `562c346` |
| **Spec** | `specs/015-breeder-cria-uat-s1/spec.md` |
| **Enmiendas** | `GA-REM-006` (correcciones · alcance 2 «mapa campo→destino»), `GA-REM-021` (datos obligatorios `RR-20..RR-23`), `GA-REM-040` (unidad de negocio, aislamiento y pendientes de clasificación) |
| **Fecha del documento** | 2026-11-18 |
| **Alcance** | Solo documentación. No se ejecutaron pruebas en la elaboración de este documento (regresión de backend en curso). |

## Tabla de hallazgos

| ID | Observación UAT | Tipo | Sev | Regresión | Causa raíz | Spec dueña | Disposición | Tests / evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| S1-BU-01 | pestañas de BU en Lotes ignoran unidades | UX/BUG | P2 | NO | LotListPage no consultaba las unidades efectivas; faltaba `hatchery` | GA-REM-040 | FIX (pestañas por unidad efectiva + estado «sin unidades» + `bird_type` en servidor con defensa de cliente) | vitest uatS1.lotTabs; E2E P18C P2/P2b; backend uatS1.identity (d) | FIXED |
| S1-BU-02 | aislamiento por BU / IDOR | EXPECTED | — | NO | el servidor ya era fail-closed (listado por filas, detalle 404, `bird_type` no amplía) | GA-REM-040 | NO-OP backend; prueba nueva | E2E P18C P1 (lista, detalle 404, operaciones 404, reportes 404, POST ajeno 400 «Lote no encontrado»), P2 UI por URL | VERIFIED (sin bypass; P0/P1 = 0) |
| S1-ID-01 | granja/galpón/lote como números en detalles | UX/BUG | P2 | UNKNOWN | el enriquecimiento solo se aplicaba a listados | GA-REM-021/R-189 | FIX (`GET /lots/{id}`, `GET /operations/{id}` con nombres; `house_name` nuevo; detalles de lote/evento/revisión) | backend uatS1.identity (1,2); vitest uatS1.detailNames; E2E P18C P3 | FIXED |
| S1-ID-02 | filtro «Lote ID» | UX | P2 | NO | filtro por id interno | GA-REM-040 / GA-REM-021 | FIX (`lot_code` parcial insensible; UI con debounce) | backend uatS1.identity (3-5); vitest f4.historyLotCodeFilter; E2E P18C P3 | FIXED |
| S1-I18N-01 | estados/acciones crudos | UX/BUG | P2 | NO | faltaban traducciones y la clave `started_review` no coincidía con `review_started` | GA-REM-021 | FIX | vitest uatS1.i18nToast, WeightEvaluation; E2E P18D P4d/P5a | FIXED |
| S1-TRACE-01 | la inspección se guarda y desaparece | MISSING CONTRACT | P1 | NO | `farm_inspection` sin lote nacía sin unidad (fuera de Historial/Revisión/Aprobaciones); GL-OD-13 pendiente | GA-REM-040 §11 (Decisión Owner D1) | FIX (deriva BU si la granja es de una sola cadena; si no, pendiente + bandeja de solo lectura) | backend uatS1.inspection_trace (5); vitest uatS1.pendingClassification; E2E P18A B1/B2 | FIXED (clasificación de pendientes solo por API: O-3) |
| S1-CORR-01 | Correcciones solo «Observaciones»; no se corrige peso promedio/cantidad | MISSING CONTRACT | P1 | NO (brecha desde el origen) | GA-REM-006 alcance 2 (submovimientos) y formulario nunca completados | GA-REM-006 | FIX (`bird_movements[<id>].campo`/`feed_movements[<id>].quantity_kg`, `correctable-fields`, formulario real, historial legible) | backend uatS1.corrections (9); vitest uatS1.correctionForm/reviewDetailCorrections; E2E P18A A | FIXED |
| S1-REP-01 | «Volver» y Producción/Mortalidad dan error | UX/BUG | P2 | UNKNOWN | `ReportsPage` arrancaba con lote fijo 2; «Volver» siempre a /reports | GA-REM-006/R-218 | FIX | vitest uatS1.reports; E2E P18D P4a-P4c | FIXED |
| S1-REP-02 | PDF/Excel incompletos | UX/BUG | P2 | NO | el reporte de lote no traía tipo/cierre/granja/galpón; estado crudo | GA-REM-006 | FIX | backend uatS1.identity (7); vitest uatS1.reports; E2E P18D P4d/P4e | FIXED |
| S1-UX-01 | modal/toast detrás del overlay | UX/BUG | P2 | NO | toast `z-50` dentro del árbol de la app bajo overlay `z-[60]` en portal; además el diálogo de rechazo no tenía campo de motivo (rechazo imposible) | GA-REM-021 | FIX (toast en portal `z-[70]`; motivo dentro del diálogo) | vitest uatS1.toastPortal/rejectReason; E2E P18D P5c | FIXED |
| S1-FLT-01 | filtro de lote con errores en inglés repetidos | UX/BUG | P2 | NO | una petición por tecla y 422 de pydantic en inglés acumulado | GA-REM-021 | FIX (debounce 400 ms, validación, aviso único; toast traduce 422 y evita duplicados) | vitest f4.lotFilterDebounce/toastSpanishDetail; E2E P18D P5b | FIXED |
| S1-VAL-01 | obligatorios por operación | MISSING CONTRACT (Owner D2) | P1/P2 | NO | pesaje, vacunación, medicación y alimento aceptaban eventos vacíos; el cliente no reflejaba BR-01/BR-08/B05 | GA-REM-021 | FIX (RR-20..RR-23 servidor; paridad cliente; «*»; Semana sin valor por defecto; mensajes sin códigos) | backend uatS1.required_data; vitest uatS1.requiredRules/requiredFields; E2E P18B (matriz de 11 operaciones) | FIXED |
| S1-WATER | agua | — | — | — | evidencia insuficiente en el UAT original | GA-REM-021 enm. A | `UAT_EVIDENCE_INSUFFICIENT` (el servidor ya exigía litros > 0; ahora también la interfaz y el mensaje sin código) | E2E P18B agua (vacío/0/mínimo) | NO CERTIFICADO COMO PASS/FAIL DEL UAT |
| S1-MORT | mortalidad (validación de regresión) | EXPECTED | — | NO | mortalidad vacía → 400 BR-01; saldo por TOTAL (D4); sin saldo negativo | GA-REM-005 | NO-OP; pin D4 | backend test_uat_s1_inspection_trace (D4), E2E P18B partes 1 y 3 | VERIFIED |

## Decisiones Owner 2026-11-18

- **D1** — Inspección de granja sin lote: se deriva la unidad de negocio si es inequívoca (todos los lotes no cancelados de la granja en una única cadena y unidad efectiva para el actor); si no, el evento nace pendiente de clasificar con bandeja de solo lectura. Resuelve `GL-OD-13`/`C-02` (opción A con respaldo B).
- **D2** — Regla mínima «no vacío» para pesaje, vacunación, medicación y alimento: valor requerido, sin rangos ni catálogos nuevos (servidor `RR-20..RR-23` + paridad de cliente).
- **D3** — El transporte en la salida de aves sigue siendo OPCIONAL (sin cambio); destino también opcional en el cliente.
- **D4** — El saldo de mortalidad/descarte/salida se mantiene por TOTAL de aves vivas, no por sexo; se documenta y se fija con un test.

## Observaciones no bloqueantes

- **O-1** — El detalle de evento no publica `id` por fila de submovimiento: las correcciones usan `row_id` de `correctable-fields`, sin cambio de contrato.
- **O-2** — Los `422` de validación estructural de pydantic llegan en inglés desde la API: la interfaz los traduce a español (límite documentado).
- **O-3** — **FUNCTIONAL GAP**: la clasificación no es utilizable ni por UI ni por API (el `company_business_unit_id` no se expone); decisión Owner pendiente (ver `POSTMERGE_CERTIFICATION.md` §6). *actualizado en el ciclo post-merge*
- **O-4** — Las correcciones de campos de catálogo (`cause_id`, `vaccine_id`, …) se hacen por código numérico: funcional pero poco ergonómico.
- **O-5** — El usuario sembrado `test_approver` no tiene `review:read`: dato de pruebas, no de producto; se ajusta en el seed si se automatiza el UAT.
- **O-6** — `POST /operations` sobre un lote de otra unidad responde 400 «Lote no encontrado»: anti-enumeración, comportamiento previo que se mantiene.
- **O-7** — **CERRADA:** `WATER_UAT=PASS` en el ciclo post-merge (agua bloqueada con valor vacío y con 0, 120.5 → 201 y visible en Historial). *actualizado en el ciclo post-merge*
- **O-8** — **P-17-G · operator**: defecto del TEST (el fixture P-16 concede `cutover:*` a todos los roles y el operador es perfil móvil con `WebOnlyRoute`), CORREGIDO en `proceso-p17d…`; no afecta saldo ni operación. *actualizado en el ciclo post-merge*
- **O-9** — Ejecutar la suite E2E con `--workers=1`; el CI oficial solo construye imágenes (no ejecuta E2E). *actualizado en el ciclo post-merge*

## Hallazgos adicionales descubiertos por E2E y corregidos

1. **Toast con `z-index` no bastaba** — subir el `z-index` del toast no lo sacaba de debajo del overlay del `ConfirmDialog` (otro contexto de apilamiento); la solución fue montar el contenedor de toasts en un portal sobre `document.body` (`AC-S1-U02`).
2. **Rechazo sin campo de motivo** — el diálogo de rechazo de Aprobaciones no incluía el campo de motivo, por lo que el rechazo era imposible de completar; se añadió el motivo (≥ 10 caracteres, validación inline con mensaje único) (`AC-S1-U03`).
3. **Mensajes de agua con código interno** — los mensajes de `water_consumption` exponían el código `RR-11`; se reescribieron los 4 mensajes sin códigos internos, viajando la regla en el campo `rule` (`AC-S1-M01`).
