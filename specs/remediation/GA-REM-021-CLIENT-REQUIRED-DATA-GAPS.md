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

---

# Enmienda B · `B01` cuadre de recepción + `B02` pesos en rango en la recepción (2026-09-10 · WAVE B tranche 7)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-021-B` · `REQUIRED OPERATIONAL DATA` + `BUSINESS RULE ACTIVATION` · **Estado** `SPEC_READY` |
| **Subrequisitos** | **`B01`** = `H360-B01` (P2): «hembras + machos + mortalidad + rechazo cuadren contra recibido» · **`B02`** = `H360-B02` (P2): «los pesos estén dentro de rango esperado» |
| **Fuente** | `Recomendación central.pdf` §6 «Proceso recomendado: recepción de reproductoras» (p.9-10), validación en «administración web intermedia» |
| **Matrices previas** | `GA_REM_021_B01_RECEPTION_RECONCILIATION_MATRIX.md` · `GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md` |
| **Trazas** | `B01` ≠ `OD-04`/`GA-TD-014` (viñeta distinta del mismo §6; la OC sigue en `BR-18` sin cambio) · `B02` gobernado por `GA-REQ-037` + `OD-06` + `GA-REM-037` (referente = curva estándar del lote; `RR-13`) |
| **Reglas resueltas por evidencia** | **`RR-12`** (identidad del cuadre y sus datos; aves alojadas = Σ movimientos = entradas del saldo; mortalidad al arribo y rechazo fuera del saldo; sin tolerancia) · **`RR-13`** (referente del rango = curva del lote; consecuencia = alerta, no bloqueo; evaluación por fila contra la curva sin sexo) — ninguna exigió escalado |
| **Composición** | `B01` y `B02` son independientes (mismo evento, distintas reglas, distintos datos); mismo `POST /operations`; **CASO A**: se implementan ambos |
| **Decisión del propietario** | **no requerida** |
| **Excluido** | `B03` · `B04` (`AOD-14`) · `B13` · `R-156` (`AOD-20`) · `R-152`/`R-153` · `R-161` · `R-164` · `R-166` · `R-140`/`R-154` residuales · `R-136` SAP · `R-142` · `R-144` · `R-147` · `R-148` · ola C (KPI, FCR, AFCR, mortalidad, vacunación, agua, peso/uniformidad) · fase 9 · SAP · `BU-D10` · `R-158` · motor genérico de recepción · motor genérico de genética · cierre de OC · tolerancias · estado de recepción · instantánea de curva · desviación % · estándar por sexo |

## B.1 `B01` · contrato del cuadre

1. **Recepción**: `bird_reception` de un lote `Lot.bird_type = BREEDER` (§6 «recepción de reproductoras»). Engorde: solo `dead_on_arrival` opcional (`spec.md §4.8:213`). Otros tipos de evento, otras cadenas y lote sin cadena: los tres campos **prohibidos** (`400`).
2. **Fuente**: nivel 2 (§6). `OD-04`: solo el principio «sin tolerancia». `GA-TD-014`: intacto (`validate_oc_limit`, `BR-18`).
3. **Cantidad esperada / recurso padre**: no participa (es la OC, ya certificada).
4. **Recibido**: `received_total` (`int ≥ 1`), dato declarado por el operador (§6 «Cantidad recibida»).
5. **Alojadas**: Σ `bird_movements[].quantity` del evento (§6 «Distribución de hembras/machos»), **derivado por el servidor**, nunca del cuerpo.
6. **Mortalidad al arribo**: `dead_on_arrival` (`int ≥ 0`, explícito). **Rechazo**: `rejected_on_arrival` (`int ≥ 0`, explícito).
7. **Identidad** (`BR-20`): `received_total == Σ alojadas + dead_on_arrival + rejected_on_arrival`; igualdad exacta; sin tolerancia; el mensaje nombra los cuatro números.
8. **Entregas parciales**: cada entrega cuadra por sí misma; la acumulación contra la OC sigue siendo `BR-18`.
9. **Sobre/bajo-recepción, cierre, estado**: no son `B01`; no se introduce estado ni cierre.
10. **Unidad**: aves, entero (`422` si no entero o negativo).
11. **Fecha**: `event_date`; sin regla propia (`BR-06`, `BR-19`/`R-30`).
12. **Duplicado/idempotencia**: `idempotency_key` existente; sin número de recibo nuevo.
13. **Corrección**: los tres campos entran en `OperationalEventUpdate` (edición por `PUT`, con revalidación de la identidad) pero **no son corregibles uno a uno**: `campos_corregibles()` los excluye explícitamente (`NO_CORREGIBLES_POR_IDENTIDAD`, excepción documentada a la derivación de `RR-01`), porque cualquier corrección de un solo sumando descuadra un registro cuadrado y devolvería siempre `400`. La vía es la edición con los sumandos afectados en un estado editable, o la devolución (`R-135`). *Corrección de redacción en la implementación: la versión inicial decía «corregibles; la identidad se revalida en corrección», lo que es aritméticamente imposible de satisfacer.*
14. **Concurrencia**: N/A (identidad intra-evento). **Transacción**: la regla corre antes de `db.add`; rechazo = cero filas, cero saldo, cero auditoría, cero alerta.
15. **Inquilino / unidad / RBAC**: cadena certificada (`OD-14`, `OD-16`, `R-160`, `B05`); `operations:create`/`update`, `corrections:correct`; sin permiso nuevo.
16. **Auditoría**: la del alta (`registered`); la denegada no audita.
17. **`R-130`**: entradas del saldo = Σ alojadas (sin cambio); mortalidad al arribo y rechazo nunca entran (`RR-12`). Riesgo `R-167` registrado.
18. **SAP**: no participa; «Diferencias» hacia SAP es `P-08` diferido.

## B.2 `B02` · contrato de «pesos en rango»

1. **Medida**: promedio de muestra por sexo/galpón en la recepción (`BirdMovement.avg_weight`, gramos).
2. **Fuente**: nivel 2 (§6) para el qué/cuándo; `docs/02 §3.12.1/§3.14` y `spec.md §4.5` para el estándar; `OD-06` para el origen del rango; `GA-REM-037` para la regla, los bordes y la alerta (`RR-13`).
3. **Unidades**: reproductoras **sí**; engorde, progenitoras, incubadora **no** (§4.8 sin alertas; sin fuente).
4. **Línea y curva**: las del lote (`genetic_line_id`, `weight_curve_id` fijado); nunca del cuerpo.
5. **Edad**: `event_date − Lot.start_date` en días (`GA-REM-028`, `service.py:750-753`); anterior al inicio → `NO_REFERENCE`.
6. **Unidad de peso**: gramos; sin conversión.
7. **min / target / max, interpolación, bordes, fuera de tabla**: exactamente `GA-REM-037 §5-§6` por el **mismo motor** (`weight_curve.py`); día 0 sin punto → `NO_REFERENCE` declarado.
8. **Clasificación**: `BELOW` / `WITHIN` (inclusivo) / `ABOVE` / `NO_REFERENCE`; una fila por muestra ♀/♂.
9. **Desviación %**: no gobernada → no se añade.
10. **Guardar / bloquear**: se persiste siempre; fuera de rango → `OperationalAlert` `weight_deviation` (mismo mensaje, umbral y puente de notificación que `AC20`); dentro y sin referencia → sin alerta; **no bloquea** alta ni aprobación.
11. **Versionado histórico**: versión fijada al lote (`AC23`); sin instantánea.
12. **Inquilino / unidad / RBAC / auditoría**: cadena certificada; alerta con `company_id`/`lot_id`/`event_id` del evento; la lectura `AC26` filtra por empresa (`AC28`).
13. **Frontend**: el detalle de una recepción muestra la evaluación del backend (`AC-FE11` análogo); sin cálculo en cliente (`AC-FE14`).
14. **Autoridad**: enmienda B de `GA-REM-037` (puerta de la alerta + montaje del detalle); motor, modelos y migración intactos.

## B.3 Criterios de aceptación

### `B01` (`AC-B01`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-B01-01` | recepción de reproductoras con `received_total == Σ alojadas + dead + rejected` → `201`; los tres campos se persisten y se leen | `201` |
| `AC-B01-02` | dos entregas parciales contra la misma OC, cada una cuadrada → `201` ambas; `BR-18` intacto (control) | `201` |
| `AC-B01-03` | las alojadas se calculan desde los movimientos persistidos: dos filas ♀/♂ por galpón suman | servidor |
| `AC-B01-04` | `received_total ≠ Σ + dead + rejected` (uno de más **y** uno de menos) → `400 BR-20` con los cuatro números | `400` |
| `AC-B01-05` | identidad exacta con `dead > 0` y `rejected > 0` → `201`; distingue `==` de `>=`/`<=` | `201` |
| `AC-B01-06` | recepción denegada: cero eventos, cero `bird_movements`, saldo intacto, sin auditoría, sin alerta | 0 filas |
| `AC-B01-07` | concurrencia **N/A** (sin agregado compartido); control: dos recepciones cuadradas consecutivas suman al saldo | control |
| `AC-B01-08` | el cliente no puede aportar el total alojado: `extra_data.placed_total`/`declared_quantity` coherentes con `received_total` pero movimientos que no cuadran → `400 BR-20` | `400` |
| `AC-B01-09` | `company_id`/`business_unit_id` en el cuerpo se ignoran (control certificado, una aserción) | control |
| `AC-B01-10` | otra empresa → `400 BR-07` (lote inexistente para quien pide) | `400` |
| `AC-B01-11` | unidad apagada: operador con concesión histórica → `BR-07`; autoridad global situada → `403` | `400`/`403` |
| `AC-B01-12` | sin la unidad del lote → `BR-07` | `400` |
| `AC-B01-13` | sin `operations:create` → `403` | `403` |
| `AC-B01-14` | autoridad global sin contexto → `BR-07` (fallo cerrado) | `400` |
| `AC-B01-15` | el alta cuadrada deja auditoría `registered`; la denegada no deja ninguna | auditoría |
| `AC-B01-16` | reproductoras sin `received_total`, sin `dead_on_arrival` o sin `rejected_on_arrival` → `400` (cada ausencia por separado; `0` explícito sí vale) | `400` |
| `AC-B01-17` | `received_total`/`rejected_on_arrival` en engorde → `400`; `dead_on_arrival` en engorde → `201` y **no** entra al saldo; los tres en `feed_registration`, en lote de progenitoras y en lote sin cadena → `400` | `400`/`201` |
| `AC-B01-18` | `PUT` que descuadra → `400 BR-20`; `PUT` que recuadra (dos campos) → `200`; una corrección uno a uno de cualquiera de los tres sumandos → `400` (campo no corregible) y **ninguna vía deja la recepción descuadrada**; `correction_logs` sin filas | edición/corrección |
| `AC-B01-19` | `R-130`: tras la recepción el saldo es Σ alojadas (no `received_total`); una mortalidad posterior sigue acotada por ese saldo | saldo |
| `AC-B01-20` | negativo o no entero → `422` | `422` |

### `B02` (`AC-B02`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-B02-01` | recepción de reproductoras con `avg_weight` por fila → `201`; el peso se persiste | `201` |
| `AC-B02-02` | la línea y la curva son las del lote; el cuerpo no las lleva (`breed_id` no es línea) | servidor |
| `AC-B02-03` | edad = `event_date − start_date`: recepción el día de inicio → 0; cinco días después → 5; anterior al inicio → `NO_REFERENCE` (`event_before_lot_start`) | edad |
| `AC-B02-04` | punto exacto (día 0) → `expected_min/target/max` exactos de ese punto | exacto |
| `AC-B02-05` | día 5 entre los puntos 0 y 10 → los tres valores interpolados con el **número exacto** | interpolación |
| `AC-B02-06` | `avg_weight == min` → `WITHIN_STANDARD`, sin alerta | borde |
| `AC-B02-07` | `avg_weight == max` → `WITHIN_STANDARD`, sin alerta | borde |
| `AC-B02-08` | `< min` → `BELOW_STANDARD` + `OperationalAlert` (`weight_deviation`, umbral = `min`, valor real, edad, versión) | alerta |
| `AC-B02-09` | `> max` → `ABOVE_STANDARD` + alerta (umbral = `max`) | alerta |
| `AC-B02-10` | dentro → `WITHIN_STANDARD`, sin alerta | — |
| `AC-B02-11` | suplantación **N/A**: el cuerpo no lleva línea ni edad; `extra_data.declared_avg_weight_*` no participa (control) | N/A |
| `AC-B02-12` | lote sin curva → `NO_REFERENCE` (`no_curve_assigned`); curva que empieza en el día 7 y recepción en el día 0 → `NO_REFERENCE` (`age_outside_curve_table`); en ambos casos `201` y sin alerta | sin inventar |
| `AC-B02-13` | otra empresa no lee la evaluación de la recepción (`404`, control `AC28`) | tenencia |
| `AC-B02-14`…`17` | unidad apagada / sin unidad / RBAC / global sin contexto: **misma ruta** que `B01`; cubiertos por `AC-B01-11…14` (una aserción de referencia) | control |
| `AC-B02-18` | reproductoras: PASS · engorde: recepción con peso fuera de rango de una curva asignada → **sin** alerta (N/A por fuente) · progenitoras/incubadora: N/A | por unidad |
| `AC-B02-19` | fuera de rango **no** bloquea: `201` + alerta; el registro puede enviarse a revisión | no bloqueo |
| `AC-B02-20` | la alerta lleva `company_id`, `lot_id`, `event_id` del evento; el puente `weight_out_of_standard` existente recibe la alerta | auditoría |
| `AC-B02-21` | el detalle de una recepción monta la evaluación del backend (`WeightEvaluation`) | frontend |
| `AC-B02-22` | la evaluación usa la versión **fijada al lote**: activar una versión nueva de la línea después de crear el lote no cambia el veredicto de la recepción (`AC23` en recepción) | versión |

## B.4 Frontend (vertical mínima)

`OperationFormPage.tsx` · caso `bird_reception` con etapa `breeder_rearing`: tres campos numéricos («Cantidad recibida (aves)»,
«Mortalidad al arribo», «Rechazo») ligados a `received_total`, `dead_on_arrival`, `rejected_on_arrival`; una línea informativa de
aritmética (alojadas Σ + mortalidad + rechazo frente a recibidas) **sin regla en el cliente** (la valida el backend). Esquema `zod`:
los tres enteros opcionales ≥ 0. `OperationDetailPage.tsx`: montar `WeightEvaluation` también para `bird_reception`.
`domain.types.ts` y `translation.json` es/en. Sin pantalla nueva; sin tocar la alerta ±10 % existente (`R-169`, fuera).

## B.5 Migración

`w3x4y5z6a7b8_reception_reconciliation.py` (revisa `v2w3x4y5z6a7`): `operational_events.received_total INTEGER NULL`,
`dead_on_arrival INTEGER NULL`, `rejected_on_arrival INTEGER NULL`. Sin relleno: las filas históricas quedan `NULL` (no declarado).
Bajada: se detiene si alguna fila tiene alguno de los tres no nulo; retira las columnas. Sin cambio de enumerados. Guardianes de
cabeza → `w3x4y5z6a7b8`; `test_clean_baseline` (55 tablas, esquema) y `test_time_determinism` en el verde dirigido (regla
permanente del tranche 7 §5). Migración **solo tras este commit de spec**.

## B.6 Tareas

| Tarea | Contenido |
|---|---|
| `T-021-B1` | migración + modelo + `Base`/`Update` (tres enteros) |
| `T-021-B2` | `validators.validate_reception_reconciliation` (`BR-20`) y aplicación en alta, edición y corrección; `_tipo_de_lote` ya existe |
| `T-021-B3` | `service.py:586`: puerta de la alerta de peso también para `BIRD_RECEPTION` en lotes `breeder` (`GA-REM-037-B`) |
| `T-021-B4` | frontend §B.4 |
| `T-021-B5` | `tests/test_reception_reconciliation.py` (`AC-B01`) · `tests/test_reception_weight_range.py` (`AC-B02`) · fixtures de recepciones de reproductoras existentes (solo setup) |

## B.7 Sensibilidad

| Mut. | Retira | Debe caer |
|---|---|---|
| `B01-S1` | la identidad (`BR-20`) | `AC-B01-04` |
| `B01-S2` | «ignorar recepciones previas» | **N/A**: `B01` no acumula (la acumulación es `GA-TD-014`, con su propia sensibilidad) |
| `B01-S3` | protección de concurrencia | **N/A**: sin agregado compartido |
| `B01-S4` | el servidor confía en un total alojado enviado por el cliente (`extra_data.placed_total`) | `AC-B01-08` |
| `B01-S5` | la obligatoriedad de los tres campos en reproductoras | `AC-B01-16` |
| `B01-S6` | la aplicabilidad por cadena (identidad y campos admitidos en cualquier lote/tipo) | `AC-B01-17` |
| `B01-S7` | la exclusión de los tres sumandos de la corrección (un corrector puede dejar la recepción descuadrada) | `AC-B01-18` |
| `SEC-S1` | la empresa (cuatro capas del alta: `_unidad_del_lote`, `_tipo_de_lote`, `lotes_alcanzables`, `validate_lot_active`) | `AC-B01-10` con fila observada |
| `SEC-S2` | la habilitación de la unidad (guarda compartida) | `AC-B01-11` (global) |
| `SEC-S3` | la concesión del actor | `AC-B01-11/12` |
| `SEC-S4` | `operations:create` en la ruta | `AC-B01-13` |
| `B02-S1` | la puerta de la alerta para la recepción | `AC-B02-08/09` |
| `B02-S2` | la interpolación del motor (devuelve el punto anterior) — mutación sobre el motor certificado, revertida | `AC-B02-05` |
| `B02-S3` | la clasificación (todo `WITHIN`) | `AC-B02-08/09` |
| `B02-S4` | confiar en línea/edad del cliente | **N/A**: no hay campo |
| `B02-S5` | evaluar con la versión activa de la línea en vez de la fijada al lote | `AC-B02-22` |

## B.8 Definición de terminado

`AC-B01-01…20` y `AC-B02-01…22` verdes · rojo válido · sensibilidad `B01-S1/S4/S5/S6/S7`, `SEC-S1…S4`, `B02-S1/S2/S3/S5` válidas
(`B01-S2/S3`, `B02-S4` N/A) · `R-130` 21/21 · genética/curvas/alertas/evaluación (4 suites) · `B05` 16/16 · reversos · `R-135`/`R-143` ·
`R-159`/`R-160` · `R-162`/`R-163` · `R-139` 35/35 · `R-165` · recepción contra OC 7/7 · linaje de recepción · `test_clean_baseline` ·
`test_time_determinism` · guardianes exactos · regresión completa **leída** · `vitest` · `tsc` 6 · `B01` y `B02` cerrados (técnico) ·
`GA-REM-021` sigue **PARTIAL** (`B03`, `B04`, `B13`, `R-156`) · certificación de proceso `BLOCKED_RUNTIME`.
