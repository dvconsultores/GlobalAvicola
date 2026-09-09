# GA-REM-021 — BRECHAS DE CAPTURA EXIGIDAS POR EL CLIENTE

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-021` · **Tipo** `REQUIREMENT GAP SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** **`PARTIAL`** (2026-09-09: `B05` cerrado técnico por la enmienda A; `B01…B04`, `B13`, `R-156` abiertos; E2E `BLOCKED_RUNTIME`) |
| **Dependencias** | `GA-REM-001` · **informada por** `GA-REM-020` (validación de cobertura) |
| **Hallazgo** | **R-13** — descubierto en la revalidación, **no estaba en la auditoría** |
| **Fuente** | `Imagen de Procesos Documentado/Bases Consideradas en el Desarrollo de la App Avicola.pdf` |

## Problema
El documento de requerimientos original del cliente exige el **consumo diario de agua** como dato obligatorio en tres de las cuatro etapas productivas. **No existe ningún campo de agua en el backend.** El frontend contiene una gráfica que lee `e.water_liters`, un campo inexistente, por lo que muestra una serie permanentemente en cero.

Este requisito **no aparece en `spec.md` ni en ninguno de los 16 documentos de `docs/`**: se perdió en la transcripción del requerimiento del cliente a la especificación del proyecto.

## Evidencia

### Exigencia del cliente
| Etapa | Cita textual | Página |
|---|---|---|
| Reproductora Fase Cría | «8. Consumo de Agua: Cantidad de agua consumida por los pollitos durante el día» | 2 |
| Reproductora Fase Producción | «11. Consumo de Agua: Cantidad de agua consumida por las gallinas durante el día» | 4 |
| Pollo de Engorde | «9. Consumo de Agua: Cantidad de agua consumida por los pollos durante el día» | 12 |
| Todas | «Optimización de Recursos: Ayuda a optimizar el uso de alimento, **agua** y otros recursos» | varias |

### Estado en la implementación
| Verificación | Resultado |
|---|---|
| `grep -rn "water\|agua" backend/app --include=*.py` | **0 resultados** |
| Campo en el modelo de eventos o submovimientos | **no existe** |
| `frontend/src/pages/reports/ReportsPage.tsx:30` | `if (e.water_liters) byDate[d].water_l += e.water_liters` — el campo nunca llega |
| `ReportsPage.tsx:127` | comentario: «matching old app: water, mortality, weight» — el sistema legacy **sí lo tenía** |
| Único «agua» en el frontend | `vaccination_route = "water"` («Agua de bebida») — una vía de vacunación, no consumo |

**El comentario del código confirma que el sistema legacy capturaba agua y que la nueva implementación lo perdió.**

## Comportamiento actual
La gráfica de consumo de agua existe en la interfaz de reportes y **siempre está vacía**. El operador no tiene dónde registrar el dato.

## Comportamiento esperado
El consumo de agua se registra a diario junto con el consumo de alimento y alimenta los KPI de optimización de recursos.

## Alcance
1. Confirmar, con la validación de `GA-REM-020`, en qué etapas de la taxonomía propia debe capturarse el dato.
2. Decidir dónde vive: campo en `feed_movements`, submovimiento propio, o campo en `operational_events`.
3. Captura en el formulario de las etapas donde el cliente lo exige.
4. Exposición en el reporte, sustituyendo la serie vacía.
5. Revisar si existen **otras** brechas del mismo tipo entre el documento del cliente y la implementación.

## Fuera de alcance
Sensores o telemetría automática · KPI de eficiencia hídrica avanzados · la cadena LIVIANAS.

## Revisión sistemática exigida
Esta spec debe verificar, punto por punto, la lista completa de datos diarios que el cliente exige por etapa, y no solo el agua. Hallazgos preliminares:

| Dato exigido por el cliente | Estado en la implementación |
|---|---|
| Consumo de agua | **AUSENTE** — objeto de esta spec |
| Condiciones ambientales (temperatura y humedad del galpón) | presente (`inspection_details`) |
| Alimento consumido | presente (`feed_movements`) |
| Peso de muestra representativa | presente (`bird_movements.avg_weight`, `sample_size`) |
| Mortalidad diaria | presente — **bloqueada por P0-1** |
| Incidencias de salud (enfermedad, tratamiento, vacunación) | presente |
| Huevos puestos / fértiles / infértiles / descartados | presente (`egg_movements.egg_type`) |
| Peso promedio de huevos | presente (`egg_movements.avg_weight`) |
| Almacenamiento de huevos: fecha, condiciones, duración | presente (`egg_storage`) — **sin spec del proyecto** → `SPEC_GAP`, ver `GA-REM-018` |
| Condiciones de transporte | presente (en `extra_data`) |
| Identificación de lote para trazabilidad | presente — **el emparejamiento está roto**, ver `GA-REM-008` |
| Pollitos nacidos: sanos / débiles | presente (`birth_registration` con filas viables y «Débiles») |
| Tasa de eclosión | **devuelve texto en lugar de número** → `GA-REM-022` |

## Base de datos afectada
**Sí.** Requiere columna nueva. Migración Alembic con docstring citando `GA-REM-021` y su AC (Art. 19 de la constitución).

## Acceptance Criteria
**AC01 — El dato se captura**
```
Given un operador en el formulario de registro diario de una etapa que lo exige
When  registra el consumo de agua del día
Then  el valor se persiste y es recuperable
```
**AC02 — La gráfica deja de estar vacía**
```
Given eventos con consumo de agua registrado
When  se consulta el reporte del lote
Then  la serie de consumo de agua muestra los valores registrados
```
**AC03 — Cobertura por etapa**
```
Given las etapas donde el cliente exige el dato
When  se abre el formulario correspondiente
Then  el campo de consumo de agua está disponible en todas ellas
```
**AC04 — Revisión sistemática completada**
```
Given la lista de datos diarios exigidos por el cliente
When  se contrasta contra la implementación
Then  cada elemento tiene estado documentado
And   las brechas encontradas están registradas como hallazgos
```
**AC05 — Trazabilidad al requerimiento del cliente**
```
Given el campo implementado
When  se consulta su spec
Then  cita la fuente del cliente que lo exige, con página
```

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Añadir un campo obligatorio rompe la captura actual | el campo es opcional en la primera iteración |
| La revisión sistemática revela más brechas de las previstas | es el objetivo: mejor descubrirlas ahora que en producción |

## Definition of Done
- [ ] Revisión sistemática completa documentada · [ ] AC01–AC05 verificados · [ ] Migración con docstring trazado · [ ] Certification report

---

# Enmienda A · `B05` consumo diario de agua — contrato de captura (2026-09-09 · WAVE B tranche 6)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-021-A` · `REQUIRED OPERATIONAL DATA` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-09; E2E `BLOCKED_RUNTIME`) · evidencia `GA-REM-021-B05-WATER-CAPTURE-EVIDENCE.md` · commits `c8447de` · `72600f1` |
| **Subrequisito** | **`B05`** = `R-13` = `H360-B05` (P1): consumo diario de agua exigido por el cliente en tres etapas y ausente |
| **Fuente** | `Bases Consideradas en el Desarrollo de la App Avicola.pdf` p.2 («8. Consumo de Agua: Cantidad de agua consumida por los pollitos durante el día»), p.4 («11. … por las gallinas …»), p.12 («9. … por los pollos …»); ausente en p.7-11 (incubadora) |
| **Matriz previa** | `GA_REM_021_B05_WATER_CAPTURE_MATRIX.md` (aplicabilidad §3, contrato de datos §4, resolución por niveles §2) |
| **Reglas resueltas por evidencia** | **`RR-10`** unidad = litros (`water_liters`), nivel 5 precisado por nivel 6 · **`RR-11`** consumo `> 0`, decimales, «sin dato» ≠ `0`, nivel 5 (misma regla que `quantity_kg`) — ninguna cambia el comportamiento de negocio; ninguna exigió escalado (`REQUIREMENT_CONFLICT_RESOLUTION §1`) |
| **Excluido** | `B04` (`AOD-14`) · resto de `GA-REM-021` · KPI de agua y umbrales (ola C) · sensores · SAP · reverso del dato (`GA-REM-041 §3.5` no lo lista) |

## A.1 Aplicabilidad y no aplicabilidad

`breeder` (Reproductoras, cría y producción) y `broiler` (Engorde): **aplica**. `hatchery`: **no** (el cliente no lo pide).
`grandparent`: **no por fuente** (no es etapa del documento del cliente; `OD-16.a` la incorpora sin dato de agua). Lote sin
cadena: **no** (aplicabilidad indeterminable). La ruta rechaza con `400` lo no aplicable: no acepta en silencio.

## A.2 Modelo

- `EventType.WATER_CONSUMPTION = "water_consumption"` (enumerado nativo `eventtype` → migración `u1v2w3x4y5z6`).
- `OperationalEvent.water_liters: Float, nullable` (columna nueva; `Float` es la convención del repositorio para consumos).
- `OperationalEventBase.water_liters: Optional[float]` (alta y lectura) · `OperationalEventUpdate.water_liters` (edición y
  **corrección** por `campos_corregibles`, `RR-01`).
- Reglas de negocio en `_apply_business_rules`: (1) `water_consumption` exige `lot_id` (no está en `LOT_OPTIONAL_EVENTS`);
  (2) exige `water_liters > 0` (`RR-11`); (3) el lote debe ser `breeder` o `broiler` (`A.1`), con cadena declarada; (4) cualquier
  **otro** tipo de evento con `water_liters` → `400` (un dato, un registro). Ubicación opcional (`validate_farm_house` no lo
  lista como evento de ubicación), como el alimento.
- Cadena de escritura productiva **sin cambio**: `exigir_unidad_operativa(lot_id)` (empresa y unidad del lote; `403` global sobre
  unidad apagada; `BR-07` anti-enumeración), `verificar_ubicacion`, `BR-06`, `BR-19`.
- Flujo `P-07`, corrección, auditoría: los existentes. Reverso: no elegible (`400 BR-16`).

## A.3 Criterios de aceptación

### Captura (`AC-W`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-W01` | operador con `operations:create` y unidad efectiva `breeder` registra `water_consumption` sobre su lote con `water_liters = 123.5` | `201` |
| `AC-W02` | el valor persistido es exactamente el enviado (`SELECT water_liters`) | — |
| `AC-W03` | `company_id` de la fila = empresa efectiva del actor, aunque el cuerpo diga otra (se ignora) | — |
| `AC-W04` | la unidad se deriva del lote (`bird_type`), no del cuerpo | — |
| `AC-W05` | `event_date` se guarda tal cual (`2026-09-02` → `2026-09-02`) | — |
| `AC-W06` | la unidad de medida es litros por contrato: el dato viaja como `water_liters` en alta, lectura y edición; ningún campo de unidad libre | — |
| `AC-W07` | `GET /operations/{id}` y `GET /operations?lot_id` devuelven `water_liters` (la serie del reporte deja de estar vacía) | `200` |

### Validación (`AC-V`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-V01` | `water_consumption` sin `water_liters` → denegado | `400` |
| `AC-V02` | `water_liters` no numérico → denegado | `422` |
| `AC-V03` | `water_liters = 0` → denegado (`RR-11`) | `400` |
| `AC-V04` | negativo → denegado | `400` |
| `AC-V05` | `12.345` se persiste y devuelve sin redondeo inventado | — |
| `AC-V06` | fecha futura: **sin regla propia del agua**; rige la regla genérica ya vigente para todo evento (`validate_event_date`, `R-30`, código `BR-19`: futura más allá de un día de holgura → `400`); se documenta, no se inventa. *Corrección de redacción en la implementación: la versión inicial atribuía el veto a `BR-06`, que solo cubre fechas anteriores a la activación; el veto de fecha futura existía ya en `R-30`* | — |
| `AC-V07` | lote cerrado → `400 BR-07`; lote sin cadena → `400`; `hatchery` → `400`; `grandparent` → `400` | `400` |
| `AC-V08` | dos registros del mismo lote y fecha → ambos `201`, ambos listados (modelo aditivo, como alimento) | `201` |
| `AC-V09` | `water_liters` en un `feed_registration` → `400` | `400` |

### Seguridad (`AC-S`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-S01` | actor de `B` sobre lote de `A` → `400 BR-07` (convención vigente, anti-enumeración) · cero filas | `400` |
| `AC-S02` | unidad `broiler` **apagada** en `A`: operador con concesión histórica → `400 BR-07`; autoridad global situada → `403` | — |
| `AC-S03` | operador sin la unidad del lote (habilitada, no concedida) → `400 BR-07` | `400` |
| `AC-S04` | sin `operations:create` → `403` | `403` |
| `AC-S05` | autoridad global sin contexto → `400 BR-07` (fallo cerrado; sin fila, sin `company_id NULL`) | `400` |
| `AC-S06` | autoridad global situada en `B` sobre lote de `A` → `400 BR-07` | `400` |
| `AC-S07` | Administrador de Accesos → `403` | `403` |
| `AC-S08` | control-lectura (Contraloría representada) → `403` | `403` |
| `AC-S09` | `company_id`/`business_unit_id` en el cuerpo no cambian la atribución (se ignoran; la fila es de la empresa efectiva y de la unidad del lote) | — |

### Cobertura por unidad (`AC-BU`)

| AC | Criterio |
|---|---|
| `AC-BU01` | `breeder`: positivo independiente (`= AC-W01`) |
| `AC-BU02` | `broiler`: positivo independiente en una empresa con `broiler` habilitado y concedido |
| `AC-BU03` | `hatchery`: `400` (no aplica) |
| `AC-BU04` | `grandparent`: `400` (no aplica por fuente) — Progenitoras **N/A con evidencia** |

### Corrección y auditoría (`AC-C`, `AC-AU`)

| AC | Criterio |
|---|---|
| `AC-C01` | corrector autorizado corrige `water_liters` de un registro `REGISTERED` → `201`, valor nuevo aplicado, original en `correction_logs` (`RR-01`) |
| `AC-C02` | sin `corrections:correct` → `403`; sobre `APPROVED` → `400` (inmutable; `AC-S10` del tranche 4) |
| `AC-C03` | la corrección rechaza `0` y negativos (`RR-11` también en corrección) |
| `AC-AU01` | el alta deja auditoría `CREATED` del evento con empresa, lote y actor (contrato existente) |
| `AC-AU02` | un alta denegada no deja fila ni auditoría de éxito |
| `AC-RV` | reverso de un `water_consumption` aprobado → `400 BR-16` (no elegible; `GA-REM-041 §3.5`) — N/A documentado |

## A.4 Frontend (vertical mínima, no fase 9)

`AC01`/`AC03` de la spec original exigen que el operador **tenga dónde registrar** el dato: se añade la operación
`water_consumption` al grupo «Registros Diarios» del catálogo (`processCatalog.ts`) **solo** en `breeder_rearing`,
`breeder_production` y `broiler`; un campo numérico `water_liters` (L, paso 0.1) en `OperationFormPage.tsx` para ese tipo;
etiquetas `es`/`en` en `public/locales` (sin texto fijo); tipos en `domain.types.ts`. Prueba `vitest` del catálogo (presencia
por etapa y ausencia en `grandparent_*`/`hatchery`). Sin rediseño, sin navegación nueva, sin KPI.

## A.5 Migración

`u1v2w3x4y5z6_water_consumption.py` · revises `t0u1v2w3x4y5` · `upgrade`: `ALTER TYPE eventtype ADD VALUE IF NOT EXISTS
'WATER_CONSUMPTION'` (`autocommit_block`, patrón `j0k1l2m3n4o5`) + `op.add_column("operational_events",
sa.Column("water_liters", sa.Float(), nullable=True))` · `downgrade`: `drop_column`; el miembro del enumerado permanece
(PostgreSQL no lo elimina) y la bajada se detiene si existen eventos `WATER_CONSUMPTION`. Filas existentes: `NULL` (sin dato,
**no** `0`). Sin tablas nuevas (`RQ-03` sin cambio). Guardianes: cabeza `t0u1v2w3x4y5 → u1v2w3x4y5z6`; rutas **211** (sin cambio).

## A.6 Tareas

`T-021-A1` pruebas rojas `backend/tests/test_water_capture.py` + `frontend/src/data/__tests__/processCatalog.test.ts` ·
`T-021-A2` migración, enum, columna, esquemas · `T-021-A3` reglas en `_apply_business_rules` · `T-021-A4` frontend mínimo ·
`T-021-A5` sensibilidad, regresión, evidencia `GA-REM-021-B05-WATER-CAPTURE-EVIDENCE.md`, cierre de `B05` (`GA-REM-021` queda
**PARTIAL**: `B01…B04`, `B13`, `R-156` siguen abiertos).

## A.7 Sensibilidad

| Mut. | Retira | Debe caer |
|---|---|---|
| `S1` | la persistencia de `water_liters` (el alta responde `201` sin guardar el valor) | `AC-W02`/`W07` |
| `S2` | la regla `> 0` | `AC-V03`/`V04` |
| `S3` | la empresa (tres capas: `get_event`/`validate_lot_active` no aplican al alta → `_unidad_del_lote` + `lotes_alcanzables` + `validate_lot_active(company)`) | `AC-S01` con fila observada |
| `S4` | la habilitación en la guarda compartida | `AC-S02` (global) |
| `S5` | la concesión del actor (`no_concedida` no se lanza) | `AC-S03` |
| `S6` | `operations:create` en la ruta | `AC-S04` |
| `S7` | confiar en `company_id` del cuerpo | **`N/A`**: el contrato de alta no declara `company_id`/`business_unit_id` (se ignoran); no hay campo que mutar |
| `S8` | unicidad | **`N/A`**: el modelo es aditivo (`AC-V08` es control) |
| `S9` | asignación de roles (a/b/c, `GA-REM-041-A`) | `REV-R01/R04/R05/R08` |
| `S10` | la aplicabilidad por unidad (`bird_type`) | `AC-BU03`/`BU04` |

## A.8 Definición de terminado

`AC-W01…07`, `AC-V01…09`, `AC-S01…09`, `AC-BU01…04`, `AC-C01…03`, `AC-AU01…02` verdes · rojo válido · `S1–S6`, `S9`, `S10`
válidas, `S7`/`S8` `N/A` · `R-130` 21/21 · tranches 2-5 · `R-139` 35/35 · guardianes exactos · regresión completa · `vitest` ·
migración aplicada por `upgrade` · `B05` cerrado (técnico) · `GA-REM-021` **PARTIAL** · certificación de proceso `BLOCKED_RUNTIME`.
