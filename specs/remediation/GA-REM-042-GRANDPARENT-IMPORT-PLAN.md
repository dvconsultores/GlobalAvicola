# GA-REM-042 — PLAN DE IMPORTACIÓN DE ABUELAS (`grandparent_import`)

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-042` · **Tipo** `REQUIRED OPERATIONAL DATA + BUSINESS RULE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P2** · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-10 · WAVE B tranche 12) · evidencia `WAVE_B_TRANCHE_12_PROGENITORAS_IMPORT_EVIDENCE.md` · commits `d3e0e70` · `2323d0c` |
| **Hallazgo** | **`R-152`** (`H360A-02`): «`grandparent_import` sin estructura para el plan de importación (`docs/02 §3.4.1`): país, cantidades comprada/embarcada/recibida, mortalidad en traslado, cuarentena, adjuntos tipados» |
| **Fuente** | `docs/02 §3.4.1` (Plan de importación: 22 campos) · `spec.md §4.4` («Plan de importación (PO SAP, proveedor internacional, docs sanitarios, aduana, cuarentena)»; `grandparent_import` «Registro inicial de importación con documentos»; evento exclusivo de Progenitoras) · `GA-REM-021-B` / `RR-12` (patrón: identidad intra-evento declarada, sin tolerancia; la ausencia no es 0) · `GA-REM-005 E.3` (entradas del saldo) · `GA-REM-040-G/H` (cadena de acceso por unidad, certificada para `grandparent`) · `GA-REM-030`/`R-42` (referencias de la empresa) |
| **Matrices** | `R152_R153_DEPENDENCY_TRACE.md` · `R152_R153_PROGENITORAS_FUNCTIONAL_PARITY_MATRIX.md` · `R152_PROGENITORAS_GAP_MATRIX.md` |
| **Proceso · unidad** | `P-01` Progenitoras — Cría, paso 1 · unidad `grandparent` (`Lot.bird_type = GRANDPARENT`) |
| **Relación con Reproductoras** | `PROGENITORAS_SPECIFIC`: Reproductoras no importan (`§3.5.2` reciben); la recepción de Reproductoras y su cuadre (`BR-20`, `B02`) no cambian; se comparten solo primitivas (`OperationalEvent`, `bird_movements`, `Evidence`, `SapReference`, cadena de acceso, guarda de edición) con la justificación de §3 |
| **Decisión del propietario** | **no requerida** para `R-152` · `R-153` → `AOD-25` |
| **Migración** | **ninguna** (`extra_data` JSONB, `evidence_type String(50)`, columnas existentes) |
| **Fuera de alcance** | `R-153`/`AOD-25` (lote automático) · `R-166` · `R-164` · `R-177`/`AOD-24` · `R-140`/`R-154` residuales · `R-136` SAP · `B03`/`AOD-22` · `B04`/`AOD-14` · `R-156`/`AOD-20` · `AOD-23` · `R-142` · `R-144` · `R-147` · `R-148` · ola C y todo KPI (progenitoras incluidos) · fase 9 · SAP real (`P-08` `BLOCKED_EXTERNAL`) · `BU-D10` · `R-158` · reescrituras genéricas (unidades, dominio, frontend, maestros, motor de eventos) · conciliación de la importación contra la OC (`BR-18` sigue en `bird_reception`) · curva de peso de Progenitoras (sin fuente) · agua en Progenitoras (sin fuente) |

## 1. Problema

`grandparent_import` existe como tipo (`EventType`, catálogo, formulario, flujo) pero es un evento genérico: `extra_data` libre, sin país ni cantidades
del plan, sin identidad alguna, proveedor/transporte sin pertenencia, adjuntos sin clase. Todo lo que `docs/02 §3.4.1` enumera se pierde o se captura
como texto sin tipo; nada es validable. `PROCESS-01` lo certificó como paso «con la orden de compra» (lo único tipado).

## 2. Contrato (`§46` del prompt, 1-30)

1. **Hallazgo**: `R-152` (§Metadata).
2. **Fuente**: `docs/02 §3.4.1`; `spec.md §4.4`.
3. **Proceso**: `P-01` paso 1. La cadena (inspecciones, recepción, distribución, …) no cambia; el lote **sigue existiendo antes** de la importación (contrato vigente; `R-153` es otra cosa).
4. **Unidad**: `grandparent`. **Regla de tipo**: `grandparent_import` solo sobre un lote con `bird_type = GRANDPARENT`; sobre otro tipo → `400 BR-22`.
5. **Relación con Reproductoras** y **6. clasificación**: matriz de paridad §2-§4. Reproductoras: sin cambio.
7. **Modelo** (sin migración): el plan vive en `OperationalEvent.extra_data["import_plan"]` (objeto validado en el servidor, esquema `PlanDeImportacion`), las cantidades por sexo en `bird_movements` (`sex ∈ {male, female}`, `quantity ≥ 0`), la OC en `sap_document_ref`, el proveedor en `supplier_id`, el transporte en `transport_id`, la línea genética y el tipo de ave en el **lote** (no se recapturan), los adjuntos en `evidences.evidence_type`.
   ```
   import_plan = { origin_country: str (no vacío)          purchased_total: int ≥ 1        shipped_total: int ≥ 1
                   received_total: int ≥ 0                 transit_mortality: int ≥ 0      departure_date: date        arrival_date: date
                   reception_condition: str | null         quarantine_days: int ≥ 0 | null quarantine_end_date: date | null
                   initial_health_inspection: str | null }
   ```
8. **Servicio**: `validate_import_plan(event_type, bird_type, plan, filas, sap_document_ref, supplier_id)` en `operations/validators.py` (pura), llamada desde `_apply_business_rules` y desde la guarda central de edición/corrección; pertenencia de `supplier_id`/`transport_id` con `verificar_pertenencia` (existente).
9. **Ruta**: `POST /operations` (sin cambio de contrato de error) · `PUT /operations/{id}` · `POST /corrections` · `POST /operations/{id}/evidences` (nuevo campo de formulario opcional `evidence_type`).
10. **Frontend**: caso `grandparent_import` del formulario con los campos del plan (claves `extra_data.import_plan.*`), OC, proveedor, transporte y filas ♂/♀; detalle con el plan y la clase de cada adjunto; selector de clase al adjuntar en importaciones; i18n ES/EN; sin texto fijo. Sin rediseño.
11. **Campos** (matriz de paridad §3): **obligatorios** `origin_country`, `purchased_total`, `shipped_total`, `received_total`, `transit_mortality`, `departure_date`, `arrival_date`, `sap_document_ref`, `supplier_id`, al menos una fila ♂/♀ (la ausencia no es 0: `RR-12`); **opcionales** `transport_id`, `reception_condition`, `quarantine_days`, `quarantine_end_date`, `initial_health_inspection`, `avg_weight` de las filas (sin evaluación de curva). `dead_on_arrival`/`rejected_on_arrival`/`received_total` de columna: **prohibidos** (`BR-20`, sin cambio).
12. **Estados**: `P-07` sin cambio (`REGISTERED` → revisión → aprobación; `EDITABLES`; correcciones).
13. **Reglas** — **`BR-22`** («plan de importación de abuelas»): (a) lote `grandparent`; (b) plan presente y tipado; (c) **identidades**: `shipped_total == received_total + transit_mortality` · `received_total == Σ bird_movements.quantity` (♂ + ♀) · `arrival_date ≥ departure_date` · si hay `quarantine_end_date`: `≥ arrival_date`; (d) OC y proveedor declarados; proveedor y transporte de la empresa (`BR-07`, anti-enumeración). Sin tolerancia. `purchased_total` vs `shipped_total`: **sin regla** (`OD-04`: entregas parciales; sobre-embarque sin fuente) → dato informativo. Resto de reglas: `BR-06`, `BR-19`, `BR-11` (una importación por OC y lote), cadena de acceso; `BR-17`/`BR-18`: N/A (documental).
14. **Saldo**: la importación **no** puebla (`GA-REM-005 E.3`: entradas `bird_reception`, `birth_registration`); la población entra en `P-01` paso 4 con `BR-17`/`BR-18`; sin doble conteo; la importación no acumula contra la OC.
15. **Corrección**: `field_name ∈ {extra_data, supplier_id, transport_id}` pasa por la guarda central (`R-176`): `BR-22` sobre el candidato con las filas persistidas; identidad rota → `400 BR-22`; `bird_movements` siguen sin ser corregibles.
16. **Anulación**: genérica (`R-173`): sin efecto en saldo; segunda → `400`.
17. **Linaje**: N/A (la importación no crea `egg_batches`/`chick_batches`; `R-178` intacto).
18. **Auditoría**: la existente (`created`, `UPDATED` con valores, `CORRECTED`, `CANCELLED`); la denegada no audita.
19. **Inquilino**: lote, proveedor y transporte de la empresa efectiva; lote de otra empresa → `400 BR-07`.
20. **Empresa · unidad**: `grandparent` OFF → actor de empresa `400 BR-07` (concesión no efectiva); global situada → `403`. Empresa con `grandparent` ON y `breeder` OFF: la importación funciona (unidad de primera clase).
21. **Usuario · concesión**: solo `breeder` → `400 BR-07`; solo `grandparent` → `201` (sin exigir `breeder`); `grandparent` no autoriza `breeder` (recepción en lote `breeder` → `400 BR-07`).
22. **RBAC**: `operations:create` (alta, adjuntos, anulación), `operations:update` (edición), `corrections:correct`; sin permiso nuevo; nada por nombre de rol.
23. **Actor global**: sin empresa → `400 BR-07`; situada en A → `201` sobre unidad habilitada (semántica certificada, `AC-W14`); no opera unidad apagada (`403`).
24. **Administrador de Accesos**: `403` en la importación (plano de control).
25. **Contraloría** (lectura): `403` al escribir; lectura según `OD-09` (sin cambio).
26. **SAP**: la OC es `SapReference` (réplica); sin envío ni conector; «diferencias vs OC» → `P-08` diferido; **la importación no concilia contra la OC** (fuera; `BR-18` en la recepción).
27. **Rojo**: §4. 28. **Sensibilidad**: §5. 29. **Regresión**: §6. 30. **Cierre**: §7.

## 3. Primitivas reutilizadas y por qué son válidas para Progenitoras (`§47`)

| Primitiva | Por qué vale |
|---|---|
| `OperationalEvent` + `bird_movements` + `extra_data` | la importación es un evento operativo de `P-07` como cualquier otro (`spec.md §4.4` lo lista como `event_type`); las cantidades por sexo son el mismo dato (`sex`, `quantity`) que en toda recepción |
| `exigir_unidad_operativa` (unidad derivada de `lot.bird_type`) | certificada para `grandparent` (`AC-W05`, `AC-W15`, `AC-L14`); no se usa `bird_type` como autorización: empresa habilitada + concesión + RBAC siguen siendo la cadena |
| `verificar_destino_de_edicion` + `_reglas_puras_del_candidato` (`R-173`/`R-176`) | la importación es editable y corregible en los mismos estados; `BR-22` es una regla pura más sobre el candidato |
| `validate_event_date`, `validate_period_open`, `validate_sap_document_unique` | reglas de fecha y de documento SAP de todo evento (`GA-REM-023`) |
| `verificar_pertenencia(Supplier/Transport)` | mismo mecanismo que granja/galpón (`GA-REM-030`, `R-42`): un maestro de otra empresa es «inexistente» |
| `Evidence` + `upload_evidence` | los adjuntos del plan son evidencias del evento (`spec.md §4.4` «con documentos»); solo se añade la clase |
| `cancel_event` (`R-173`) | sin efecto en saldo, sin semántica especial |
| **no** se reutilizan | `validate_reception_reconciliation` (`BR-20`, Reproductoras), `validate_house_capacity`/`validate_oc_limit` (alojamiento y OC: paso 4), evaluación de curva (`B02`), agua (`RR-11`) |

## 4. Criterios de aceptación y rojo

| AC | Criterio | Rojo en `5e9bbee` |
|---|---|---|
| `AC-R152-01` | control: importación completa (plan + OC + proveedor + transporte + ♂/♀) por actor con **solo** `grandparent` → `201`; el plan se persiste tal cual; saldo del lote 0 | verde |
| `AC-R152-02` | sin `import_plan` (el cuerpo de hoy: `sap_document_ref` + `extra_data: {supplier: 'Internacional'}`) → `400 BR-22`, sin fila, sin auditoría | **rojo** (`201`) |
| `AC-R152-03` | identidades: `shipped ≠ received + transit_mortality` → `400 BR-22` · `received ≠ Σ ♂/♀` → `400 BR-22` · `arrival < departure` → `400 BR-22` · `quarantine_end < arrival` → `400 BR-22` · `purchased_total = 0` → `422`/`400` (registrado) | rojo |
| `AC-R152-04` | importación sobre lote `breeder` (actor con ambas unidades) → `400 BR-22` | rojo |
| `AC-R152-05` | sin OC o sin proveedor → `400 BR-22`; proveedor de otra empresa → `400 BR-07`; transporte de otra empresa → `400 BR-07` | rojo |
| `AC-R152-06` | `POST /operations/{id}/evidences` con `evidence_type=import_permit` → `201` y ese tipo persistido; cada una de las cinco clases | rojo (hoy `document`) |
| `AC-R152-07` | `evidence_type` fuera del conjunto → `400`; sin parámetro → derivado del MIME (control) | rojo / verde |
| `AC-R152-08` | tras la importación (recibidas 100) el saldo del lote es **0**; `bird_reception` de 100 con la misma OC → `201` y saldo 100; `BR-18` cuenta solo la recepción | control (verde) |
| `AC-R152-09` | `dead_on_arrival` en la importación → `400 BR-20` (control, sin cambio) | verde |
| `AC-R152-10` | actor con solo `breeder` → importación en lote `grandparent` → `400 BR-07`, cero filas | verde |
| `AC-R152-11` | actor con solo `grandparent` → `201` sin concesión `breeder`; el mismo actor → `bird_reception` en lote `breeder` → `400 BR-07` | verde |
| `AC-R152-11b` | empresa con `grandparent` ON y `breeder` OFF: su actor importa (`201`) | verde |
| `AC-R152-12` | empresa con `grandparent` OFF: actor de empresa con concesión histórica → `400 BR-07`; global situada → `403` | verde |
| `AC-R152-13` | global sin empresa → `400 BR-07`; global situada en A → `201` (unidad habilitada, `AC-W14`) | verde |
| `AC-R152-14` | actor de A sobre lote `grandparent` de B → `400 BR-07` (anti-enumeración) | verde |
| `AC-R152-15` | Administrador de Accesos → `403`; sin permiso → `403` | verde |
| `AC-R152-16` | Contraloría (lectura) → `403` | verde |
| `AC-R152-17` | `PUT extra_data` con identidad rota → `400 BR-22`, evento intacto; `PUT lot_id` → lote `breeder` → `400 BR-22`; edición válida → `200` sin repetir el alta (`AC-R176-09`) | rojo |
| `AC-R152-18` | `POST /corrections` `extra_data` con identidad rota → `400 BR-22`; válida → `201` `CORRECTED`; `supplier_id` de otra empresa → `400 BR-07` | rojo |
| `AC-R152-19` | anular → `200`, saldo 0 antes y después; segunda → `400` | verde |
| `AC-R152-20` | contrato estático del formulario: el caso `grandparent_import` registra `extra_data.import_plan.{origin_country, purchased_total, shipped_total, received_total, transit_mortality, departure_date, arrival_date, reception_condition, quarantine_days, quarantine_end_date, initial_health_inspection}`, ya no `extra_data.sanitary_cert`/`import_doc`; claves i18n ES/EN presentes | rojo (vitest) |
| `AC-R152-21` | el detalle muestra el plan y la clase de cada adjunto (contrato estático + i18n); el selector de clase se ofrece en importaciones | rojo (vitest) |

## 5. Sensibilidad (`§88-§97`)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| `R152-S1` | la validación del plan (`validate_import_plan` → `pass`) | `AC-R152-02/03` |
| `R152-S2` | fallback de concesión: `breeder ∈ efectivas` autoriza `grandparent` (en `exigir_unidad_operativa`) | `AC-R152-10` |
| `R152-S3` | acoplamiento: la importación exige `breeder` en efectivas | `AC-R152-11/11b` |
| `R152-S4` | la habilitación de empresa (efectivas ignoran `is_enabled`; global: `unidades_habilitadas` devuelve todas) — capas necesarias (protocolo del tranche 4) | `AC-R152-12` |
| `R152-S5` | la concesión de usuario (`no_concedida` → no se lanza) | `AC-R152-10` (actor sin concesión) |
| `R152-S6` | RBAC (`require_permission("operations","create")` → sin comprobar) | `AC-R152-15` |
| `R152-S7` | inquilino (capas: `validate_lot_active` sin empresa + `_unidad_del_lote` sin acotar + pertenencia) hasta que el actor de A escriba en el lote de B | `AC-R152-14` |
| `R152-S8` | paridad errónea: quitar la regla de tipo de lote (la importación acepta `breeder`) | `AC-R152-04` |
| `R152-S9` | frontend: quitar `origin_country` del caso del formulario | `AC-R152-20` |
| `R152-S10` | saldo: contar `GRANDPARENT_IMPORT` como entrada en `get_current_bird_balance` | `AC-R152-08` (saldo 100 tras la importación; 200 tras la recepción) |
| `R152-S11` | tipología de adjuntos: ignorar `evidence_type` recibido | `AC-R152-06` |

## 6. Tareas y regresión

| Tarea | Descripción |
|---|---|
| `T-042-1` | pruebas rojas `tests/test_grandparent_import.py` (prefijo `ABUE-`; empresas A (`grandparent` ON · `breeder` ON · `hatchery` OFF), B (`grandparent` OFF · `breeder` ON), C (`grandparent` ON · `breeder` OFF); actores `op_gp`, `op_br`, `op_ambos`, `sin_perm`, `acceso`, `lectura`, `actor_b`, `op_c`, `global`; lotes `lg`, `lr` (A), `lgb` (B), `lgc` (C); proveedores y transportes de A y B; OC `ABUE-OC-*`; fechas de `tests.time_reference`) + vitest `grandparentImportContract.test.ts` |
| `T-042-2` | `validators.py`: `PlanDeImportacion` (pydantic) + `validate_import_plan` (`BR-22`) |
| `T-042-3` | `service.py`: rama `GRANDPARENT_IMPORT` en `_apply_business_rules` (tipo de lote, plan, pertenencia de proveedor/transporte); `_reglas_puras_del_candidato` con `extra_data`/`supplier_id`/`transport_id`/`lot_id`; `corrections/service.py`: esos campos por la guarda |
| `T-042-4` | `router.py`: `upload_evidence` con `evidence_type: str = Form("")` validado contra el conjunto cerrado |
| `T-042-5` | frontend: caso del formulario, detalle, selector de clase de adjunto, i18n ES/EN |
| `T-042-6` | `e2e/proceso-p01-progenitoras-cria.spec.ts`: paso 1 con el plan (runtime `BLOCKED_RUNTIME`) |
| `T-042-7` | sensibilidad §5 · regresión: `R-173`, `R-176`, `R-178`, `R-175` (pares), `R-161`, `R-130`, `R-170`/`B13`, `B01`/`B02`/`B05`, `R-136`, `R-135`/`R-143`, `R-159`/`R-160`, `R-162`/`R-163`, `OD-14`/`OD-16`, `test_clean_baseline` (N/A por cambio, ejecutada), `test_time_determinism` · evidencia · cierre |

## 7. Definición de terminado

`AC-R152-01…21` verdes · rojo válido leído en `5e9bbee` · sensibilidad válida · regresión §6 y completa **leída** · `vitest` · `tsc` 6 preexistentes ·
sin migración · `R-152` CERRADO (técnico) · `R-153` OPEN (`AOD-25`) · certificación de proceso `BLOCKED_RUNTIME`.
