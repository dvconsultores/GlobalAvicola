# MATRIZ DE VALIDACIÓN DE COBERTURA FUNCIONAL

> Entregable de **`GA-REM-020`** · Fecha: 2026-09-03 · Commit base: `bfccdfb`
> **La documentación del cliente es fuente de validación (`RA-05`). La taxonomía del proyecto se conserva.**
> Ningún archivo de `backend/app/`, `frontend/src/`, `alembic/versions/` ni `processCatalog.ts` fue modificado.

Estados: `COVERED` · `PARTIAL` · `ABSENT` · `OUT_OF_SCOPE` · `NOT_VERIFIABLE` · `REQUIREMENT_CONFLICT`
Tipos: `DATA` · `KPI` · `PROCESS` · `PROCEDURE` · `BUSINESS_RULE` · `TECHNICAL_STANDARD` · `LEGACY_FUNCTION`

---

## 0. Fuentes analizadas y su nivel

| Nivel | Fuente | Utilidad | Estado |
|---|---|---|---|
| **1** | `Bases Consideradas en el Desarrollo de la App Avicola.pdf` (13 pág.) — **documento de requerimientos original**, Ing. María E. Arévalo | datos diarios y KPI por etapa | **explotada** |
| **2** | `Recomendación central.pdf` (29 pág.) — arquitectura funcional SAP ↔ app | qué puede y no puede hacer la app · 17 reglas de validación · 11 estados · datos por proceso | **explotada** |
| **2** | `Control de Codificación de Procesos Avicolas PROTINAL.xlsx` | inventario de 30 procesos — **lista de comprobación**, no estructura | **explotada** |
| **2** | `Sap y App Proceso Avícola Software primera version.pdf` (34 pág.) | contexto de negocio avícola y compra de reproductoras | explotada parcialmente — **contexto, no requisitos de software** |
| **2** | `Incubadora.pdf` | procedimiento operativo de incubación | contexto |
| **3** | Manuales Ross y Cobb (5 PDF) | estándares técnicos de línea genética | referencia |
| **4** | `Sistema avicola administrativo - capture pantallas.pdf` · `App mobile avicola - capture pantallas.docx` | funcionalidad del sistema anterior | **NOT_VERIFIABLE** — capturas de imagen sin texto extraíble |
| **5** | 30 × `Formato Especificaciones - AVI-*.xlsx` | **plantillas vacías** — solo estructura de formulario, sin contenido | **`RA-04` EMPTY SOURCE TEMPLATE** — no se infiere nada |

---

## 1. DATOS DIARIOS EXIGIDOS — Nivel 1

Fuente: `Bases Consideradas en el Desarrollo de la App Avicola.pdf`

| ID | Elemento | Fuente · pág. | Tipo | Etapa | Cobertura | Evidencia | Hallazgo |
|---|---|---|---|---|---|---|---|
| CV-D01 | Número de aves al inicio del día | p.2, 4, 12 | DATA | todas | `COVERED` | calculado por `validators.py:21 get_current_bird_balance` | — |
| CV-D02 | Número de aves muertas | p.2, 4, 12 | DATA | todas | `PARTIAL` | `bird_movements` + `mortality_recording`; **la ruta devuelve 500** | **P0-1** → `GA-REM-005` |
| CV-D03 | Peso de muestra representativa | p.2, 12 | DATA | Cría · Engorde | `COVERED` | `bird_movements.avg_weight`, `sample_size` | — |
| CV-D04 | Cantidad de alimento consumido | p.2, 4, 12 | DATA | todas | `COVERED` | `feed_movements.quantity_kg` | — |
| CV-D05 | Número de aves nuevas ingresadas | p.2, 12 | DATA | Cría · Engorde | `COVERED` | `bird_reception` | — |
| CV-D06 | Incidencias de salud | p.2, 4, 12 | DATA | todas | `COVERED` | `vaccination`, `medication`, `vaccine_id`, `medication_id` | — |
| CV-D07 | Condiciones ambientales: temperatura y humedad | p.2, 4, 12 | DATA | todas | `COVERED` | `inspection_details` | — |
| **CV-D08** | **Consumo de agua** | **p.2, 4, 12** | **DATA** | **Cría · Producción · Engorde** | **`ABSENT`** | `grep -rn "water" backend/app` → **0**. `ReportsPage.tsx:30` lee `e.water_liters`, inexistente | **R-13** → `GA-REM-021` |
| CV-D09 | Observaciones generales | p.2, 4, 12 | DATA | todas | `COVERED` | `operational_events.observations` | — |
| CV-D10 | Número de huevos puestos | p.4 | DATA | Producción | `COVERED` | `egg_movements.quantity` | — |
| CV-D11 | Huevos fértiles / infértiles / descartados | p.4, 6 | DATA | Producción | `COVERED` | `egg_movements.egg_type` | — |
| CV-D12 | Peso promedio de los huevos | p.4, 6 | DATA | Producción | `COVERED` | `egg_movements.avg_weight` | — |
| CV-D13 | Fecha de recolección | p.6 | DATA | Producción | `COVERED` | `operational_events.event_date` | — |
| CV-D14 | Condiciones de almacenamiento | p.6, 8 | DATA | Producción · Incubadora | `COVERED` | `egg_storage.storage_temp_c`, `storage_humidity_pct` | **`SPEC_GAP`** — §5 |
| CV-D15 | Fecha de traslado · nº trasladados | p.6 | DATA | Producción | `COVERED` | `egg_dispatch` + `egg_movements` | — |
| CV-D16 | Identificación de lote para trazabilidad | p.6, 9 | DATA | traslados | `PARTIAL` | `lots.lot_code` existe; **emparejamiento auto-referencial** | **P0-11** → `GA-REM-008` |
| CV-D17 | Condiciones de transporte | p.6, 8 | DATA | traslados | `COVERED` | `extra_data.transport_*` (5 campos) | — |
| CV-D18 | Duración del almacenamiento | p.8 | DATA | Incubadora | `COVERED` | `egg_storage.storage_start_date`/`storage_end_date` | — |
| CV-D19 | Inicio de incubación · nº incubados | p.8 | DATA | Incubadora | `COVERED` | `incubation_load` + `hatchery_params.quantity_loaded` | — |
| CV-D20 | Temperatura y humedad de incubación | p.8 | DATA | Incubadora | `COVERED` | `hatchery_params.temperature`, `humidity`, `co2` | — |
| **CV-D21** | **Rotación de huevos: frecuencia y ángulo** | **p.8** | **DATA** | **Incubadora** | **`PARTIAL`** | `hatchery_params.turning` es **booleano**: registra si se voltea, no frecuencia ni ángulo | **R-16 (nuevo)** |
| CV-D22 | Control de calidad diario de la incubadora | p.8 | DATA | Incubadora | `COVERED` | `hatchery_inspection` + `observations` | — |
| CV-D23 | Nacimiento: fecha · nacidos · sanos · débiles | p.8 | DATA | Incubadora | `COVERED` | `birth_registration`; `OperationFormPage.tsx:1521-1523` (viables M/H + Débiles) | — |
| CV-D24 | Vacunación en incubadora | p.9 | DATA | Incubadora | `COVERED` | sección de vacunación en `birth_registration` (commit `b5af363`) | — |
| CV-D25 | Traslado a engorde | p.9 | DATA | Incubadora | `COVERED` | `chick_dispatch` | — |
| CV-D26 | Aves vendidas o sacrificadas | p.12 | DATA | Engorde | `COVERED` | `bird_exit` + `destination_plant_id` | — |

**Subtotal:** 26 · `COVERED` 22 · `PARTIAL` 3 · `ABSENT` 1

---

## 2. KPI EXIGIDOS — Nivel 1

| ID | Elemento | pág. | Etapa | Cobertura | Evidencia | Hallazgo |
|---|---|---|---|---|---|---|
| CV-K01 | Ganancia Diaria de Peso | 3, 12 | Cría · Engorde | `PARTIAL` | derivable de `weight_recording`; **sin endpoint** | backlog |
| CV-K02 | Conversión Alimenticia (FCR) | 3, 12 | Cría · Engorde | `COVERED` | `GET /reports/kpis/feed-conversion` | — |
| CV-K03 | Tasa de Mortalidad | 3, 5, 12 | todas | `COVERED` | `GET /reports/kpis/mortality` | — |
| CV-K04 | Índice de Bienestar Animal | 3 | Cría | `PARTIAL` | implementado, **sin consumidor** | `GA-REM-022` |
| CV-K05 | Tasa de Fertilidad | 5, 7 | Producción | `PARTIAL` | no expuesta como ratio | `GA-REM-022` |
| CV-K06 | % Huevos Infértiles | 5, 7 | Producción | `PARTIAL` | dato sí, KPI no | `GA-REM-022` |
| CV-K07 | % Huevos Descartados | 5, 7 | Producción | `PARTIAL` | dato sí, KPI no | `GA-REM-022` |
| CV-K08 | Peso Promedio de los Huevos | 5, 7 | Producción | `COVERED` | `egg-production` | — |
| CV-K09 | Consumo de Alimento por Huevo | 5 | Producción | `ABSENT` | ambos datos existen; KPI no calculado | `GA-REM-022` |
| CV-K10 | Eficiencia de Traslado | 7, 10 | traslados | `PARTIAL` | implementado, **sin consumidor** | `GA-REM-022` |
| **CV-K11** | **Tasa de Eclosión** | **10** | **Incubadora** | **`PARTIAL`** | `reports/service.py:145` devuelve el **texto** `"N/A (requiere datos de carga de incubación)"`; los datos **sí existen** | **R-14** → `GA-REM-022` |
| CV-K12 | Tasa de Mortalidad de Pollitos | 10 | Incubadora | `PARTIAL` | derivable; sin endpoint | `GA-REM-022` |
| CV-K13 | Eficiencia de Vacunación | 10 | Incubadora | `PARTIAL` | implementado, **sin consumidor** | `GA-REM-022` |
| CV-K14 | % Pollitos Sanos | 10 | Incubadora | `PARTIAL` | dato sí, KPI no | `GA-REM-022` |
| CV-K15 | AFCR | 12 | Engorde | `COVERED` | `GET /reports/kpis/afcr` | — |
| CV-K16 | Índice de Producción | 12 | Engorde | `PARTIAL` | implementado, **sin consumidor** | `GA-REM-022` |
| CV-K17 | Peso Promedio al Sacrificio | 12 | Engorde | `PARTIAL` | derivable; sin endpoint | backlog |
| CV-K18 | Uniformidad | Recom. §13 | Engorde | `COVERED` | `GET /reports/kpi/weight-uniformity/{lot_id}` | — |

**Subtotal:** 18 · `COVERED` 5 · `PARTIAL` 12 · `ABSENT` 1

**Patrón:** el problema dominante de los KPI **no es de cálculo sino de exposición**. Cinco están implementados sin consumidor; siete son derivables de datos ya capturados y nunca se calcularon.

---

## 3. REGLAS DE NEGOCIO OBLIGATORIAS — Nivel 2

Fuente: `Recomendación central.pdf §17` — «Antes de enviar a SAP, la app debe bloquear»

| ID | Regla exigida | Cobertura | Evidencia | Hallazgo |
|---|---|---|---|---|
| CV-R01 | Cantidad recibida mayor a OC sin autorización | `PARTIAL` | `validators.py:313 validate_oc_limit` existe pero **nunca se dispara**: el FE no envía `sap_document_ref` | **BR-18** → `GA-REM-011` |
| CV-R02 | Galpón con capacidad excedida | `COVERED` | `validators.py:296 validate_house_capacity` | — |
| CV-R03 | Galpón inexistente en SAP | `OUT_OF_SCOPE` | requiere maestro SAP; la app usa maestros propios | `GA-REM-017` |
| CV-R04 | Material inexistente en SAP | `OUT_OF_SCOPE` | ídem | `GA-REM-017` |
| CV-R05 | Lote inexistente o cerrado | `COVERED` | `validators.py:266 validate_lot_active` (BR-07) | — |
| CV-R06 | Almacén inválido | `OUT_OF_SCOPE` | requiere maestro SAP | `GA-REM-017` |
| CV-R07 | Centro inválido | `OUT_OF_SCOPE` | requiere maestro SAP | `GA-REM-017` |
| CV-R08 | Unidad de medida inválida | `ABSENT` | sin validación de unidad | **R-19** backlog |
| CV-R09 | Consumo mayor al stock disponible | `OUT_OF_SCOPE` | requiere inventario SAP | `GA-REM-017` |
| CV-R10 | Mortalidad superior a población actual | `PARTIAL` | `validators.py:138 validate_mortality` correcto; **la ruta muere antes** | **P0-1** → `GA-REM-005` |
| CV-R11 | Vacuna sin material válido | `OUT_OF_SCOPE` | requiere stock sanitario SAP | `GA-REM-017` |
| CV-R12 | Consumo sanitario sin stock | `OUT_OF_SCOPE` | ídem | `GA-REM-017` |
| CV-R13 | Fecha en período SAP cerrado | `COVERED` | `validators.py:332 validate_period_open` (BR-19, 90 días) | — |
| CV-R14 | Registro sin usuario responsable | `COVERED` | `operational_events.registered_by_id` **NOT NULL + FK** — imposible estructuralmente | — |
| CV-R15 | Registro sin aprobación | `COVERED` | la consolidación filtra `status == APPROVED` (BR-13) | — |
| CV-R16 | Duplicidad de envío | `PARTIAL` | `idempotency_key` con índice único **existe y el FE nunca lo envía**; `validate_sap_document_unique` inerte por la misma causa | **BR-11/12** → `GA-REM-011` |
| CV-R17 | Corrección sobre registro aprobado sin versión/reverso | `PARTIAL` | `validate_sap_edit_lock` bloquea tras SAP; **el reverso (BR-16) no existe**: tabla `reversals` huérfana | backlog |

**Subtotal:** 17 · `COVERED` 6 · `PARTIAL` 4 · `ABSENT` 1 · `OUT_OF_SCOPE` 6

Las 6 `OUT_OF_SCOPE` dependen de consumir maestros e inventario de SAP: **no son defectos independientes**, son consecuencia de que la integración real no existe.

---

## 4. CAPACIDADES FUNCIONALES — Nivel 2

Fuente: `Recomendación central.pdf §2` — «Qué debe poder hacer la app avícola»

| ID | Capacidad permitida | Cobertura | Evidencia |
|---|---|---|---|
| CV-F01 | Consultar órdenes de compra abiertas | `COVERED` | `GET /sap/references?ref_type=purchase_order` |
| CV-F02 | Consultar órdenes de transferencia abiertas | `COVERED` | `GET /sap/references?ref_type=transfer_order` |
| CV-F03 | Consultar materiales disponibles | `PARTIAL` | maestros propios; **no** los materiales de SAP |
| CV-F04 | Consultar inventario disponible | `ABSENT` | no se consume inventario SAP → `GA-REM-017` |
| CV-F05 | Consultar granjas, galpones y capacidad | `COVERED` | `masters/farms`, `houses.capacity` |
| CV-F06 | Consultar equipos esperados por galpón | `PARTIAL` | la inspección captura equipos ad hoc; **sin maestro de equipos esperados** |
| CV-F07 | Capturar recepción real de aves | `COVERED` | `bird_reception` con distribución multi-galpón y validación ±10 % |
| CV-F08 | Distribuir aves por galpón, sexo y lote | `COVERED` | `bird_distribution` + `bird_movements.sex` |
| CV-F09 | Registrar peso promedio | `COVERED` | `bird_movements.avg_weight` |
| CV-F10 | Registrar temperatura, humedad y hora | `COVERED` | `inspection_details`, `operational_events.event_time` |
| CV-F11 | Registrar mortalidad | `PARTIAL` | **P0-1** |
| CV-F12 | Registrar consumo de alimento | `COVERED` | `feed_movements` |
| CV-F13 | Registrar aplicación de vacunas/medicinas | `COVERED` | `vaccination`, `medication` |
| CV-F14 | Registrar inspección de granja/equipos | `COVERED` | `farm_inspection` con ítems por equipo (commit `e156a6e`) |
| CV-F15 | **Levantar banderas operativas** | `PARTIAL` | `OperationalAlert` existe (mortalidad, temperatura, humedad); **el generador de mortalidad falla** y **no hay bandera de riesgo manual** → **R-22** |
| CV-F16 | Adjuntar evidencias | `PARTIAL` | `evidences` funciona; **se pierden en cada despliegue** → `GA-REM-009` |
| CV-F17 | Enviar datos aprobados a SAP | `PARTIAL` | consolidación correcta; **el envío es simulado** → `GA-REM-010` |

### Prohibiciones del cliente — verificación de que la app NO las hace

| Prohibición | ¿Respetada? | Evidencia |
|---|---|---|
| Crear OC desde la app | **SÍ** | no existe endpoint de creación de OC |
| Crear materiales desde la app | **SÍ** | los maestros son propios, no de SAP |
| Crear almacenes desde la app | **SÍ** | no existe |
| Cambiar costos desde la app | **SÍ** | no hay módulo de costos |
| Ajustar inventario sin documento SAP | **SÍ** | no hay ajuste de inventario |
| Cerrar órdenes desde la app | **SÍ** | no existe |
| Modificar datos aprobados sin reverso | **PARCIAL** | `validate_sap_edit_lock` bloquea tras SAP, pero **el reverso no existe** |

**Resultado destacable: la app respeta las 6 primeras prohibiciones arquitectónicas del cliente.** No invade el ámbito mandante de SAP.

---

## 5. TRAZABILIDAD DE `egg_storage` — reclasificación

| Aspecto | Valor |
|---|---|
| Clasificación en la auditoría | `IMPLEMENTED_WITHOUT_SPEC` |
| **Clasificación correcta** | **`CLIENT_REQUIREMENT_PRESENT` + `SPEC_GAP`** |
| Fuente original | `Bases Consideradas…pdf` p.8 — «2. Almacenamiento de Huevos: Fecha · Condiciones (temperatura y humedad) · Duración · Observaciones» |
| Fuente secundaria | `Recomendación central.pdf §11` — «La app debe capturar: … Condiciones de almacenamiento» |
| Implementación | `backend/app/operations/models.py:231-247` — 12 columnas |
| Migración | `4396a2b7e7d6_add_egg_storage_and_weekly_tracking_` |
| Deficiencia real | **no existe spec del proyecto** que lo autorice, y **ningún endpoint la lee** (solo se escribe en `create_event`) |
| Acción | **no modificar la implementación**: es correcta y cubre el requisito. Producir la spec en `GA-REM-018`; exponer la lectura queda en backlog |

---

## 6. VALIDACIÓN DE LOS 30 PROCESOS DEL CLIENTE — Nivel 2

Uso: **lista de comprobación de cobertura**, no estructura a adoptar (`RA-05`).

### Cadena PESADAS — dentro del alcance v1

| Código del cliente | Proceso | Cobertura | Realizado en el proyecto por |
|---|---|---|---|
| `AVI-ABU-PES-01` | Recepción de Pollitos Reproductores (Abuelas) | `COVERED` | `grandparent_rearing`: `grandparent_import`, `farm_inspection`, `bird_reception`, `bird_distribution`, `transport_inspection` |
| `AVI-ABU-PES-02` | Control de Producción Cría y Levante (Abuelas) | `PARTIAL` | ciclo diario — **bloqueado por P0-1** |
| `AVI-ABU-PES-03` | Desalojo Cría y Levante (Abuelas) | `COVERED` | `bird_exit` |
| `AVI-ABU-PES-04` | Recepción de Reproductores (Abuelas) | `COVERED` | `grandparent_production`: `bird_reception` |
| `AVI-ABU-PES-05` | Control de Producción de Huevo Fértil (Abuelas) | `COVERED` | `egg_collection`, `egg_dispatch` |
| `AVI-ABU-PES-06` | Desalojo HF (Abuelas) | `COVERED` | `bird_exit` |
| `AVI-INC-REP-01` | Incubación de Reproductoras | `PARTIAL` | 9 eventos de `hatchery` — trazabilidad rota (P0-11) |
| `AVI-REP-PES-01` | Recepción de Pollitos Reproductores | `COVERED` | `breeder_rearing` |
| `AVI-REP-PES-02` | Control de Producción Cría y Levante | `PARTIAL` | **bloqueado por P0-1** |
| `AVI-REP-PES-03` | Desalojo Reproductores CYL | `COVERED` | `bird_exit` |
| `AVI-REP-PES-04` | Recepción de Reproductores | `COVERED` | `breeder_production` |
| `AVI-REP-PES-05` | Control de Producción de Huevo Fértil | `COVERED` | `egg_collection`, `egg_dispatch` |
| `AVI-REP-PES-06` | Desalojo Reproductores HF | `COVERED` | `bird_exit` |
| `AVI-INC-ENG-02` | Incubación de Pollos de Engorde | `PARTIAL` | ídem `AVI-INC-REP-01` |
| `AVI-GRA-ENG-01` | Recepción de Pollitos Bebé | `COVERED` | `broiler`: `bird_reception`, `bird_distribution` |
| `AVI-GRA-ENG-02` | Control de Producción de Pollo de Engorde | `PARTIAL` | **bloqueado por P0-1** |
| `AVI-GRA-ENG-03` | Desalojo de Pollo de Engorde | `COVERED` | `bird_exit`, `lot_closure` |

**17 procesos · `COVERED` 12 · `PARTIAL` 5 · `ABSENT` 0**

**Ningún proceso de negocio del cliente está ausente.** Los 5 parciales lo son por dos defectos ya identificados (P0-1 mortalidad, P0-11 trazabilidad), no por funcionalidad faltante.

### Cadena LIVIANAS / Ponedoras — fuera del alcance v1
`AVI-REP-LIV-01..06` · `AVI-INC-PON-03` · `AVI-GRA-PON-01..06` → **13 procesos `OUT_OF_SCOPE`** (`spec.md §9`, `RA-03`).

---

## 7. ESTÁNDARES TÉCNICOS — Nivel 3

| ID | Elemento | Fuente | Cobertura | Evidencia |
|---|---|---|---|---|
| CV-T01 | Curvas de temperatura por semana — Broiler | Ross 308 / Cobb 500 | `COVERED` | `thermalCurves.ts` — `BROILER_TEMP_ZONES`, 9 semanas |
| CV-T02 | Curvas de temperatura — Reproductoras/Abuelas cría | Ross GP / Cobb Breeder | `COVERED` | `BREEDER_REARING_TEMP_ZONES`, 11+ semanas |
| CV-T03 | Rangos de humedad por fase | Ross / Cobb | `COVERED` | `humidMin`/`humidMax` en las curvas |
| CV-T04 | Rangos de incubadora (37,5–38,0 °C · 55–62 %) | práctica de incubación | `COVERED` | `OperationFormPage.tsx:22-25` |
| CV-T05 | Rangos de nacedora (37,0–37,5 °C · 65–75 %) | ídem | `COVERED` | ídem |
| CV-T06 | Curva de peso estándar por línea genética | Ross / Cobb | `ABSENT` | `spec.md §4.5` exige alerta por «peso fuera de curva estándar»; **solo hay curva térmica** → **R-18** |

**Criterio aplicado (§9 del encargo):** los manuales Ross y Cobb son **referencia técnica**, no requisitos de software. `CV-T06` se registra como hallazgo **solo porque la propia spec del proyecto exige esa alerta**.

---

## 8. SISTEMA LEGACY — Nivel 4

| ID | Elemento | Cobertura | Observación |
|---|---|---|---|
| CV-L01 | Captura de consumo de agua en el sistema anterior | `NOT_VERIFIABLE` documentalmente, pero **confirmado por el propio código**: `ReportsPage.tsx:127` comenta «*matching old app: water, mortality, weight*» | refuerza `CV-D08` / R-13 |
| CV-L02 | Resto de funcionalidad del sistema anterior | `NOT_VERIFIABLE` | las capturas son imágenes sin texto extraíble |

**No se infiere funcionalidad a partir de capturas no legibles.** Requiere revisión visual asistida por una persona si se considera necesario.

---

## 9. RESUMEN DE COBERTURA

```
ELEMENTOS EXTRAÍDOS Y VALIDADOS ............. 96

Por tipo:
  DATA .....................................  26
  KPI ......................................  18
  BUSINESS_RULE ............................  17
  Capacidad funcional ......................  17   (+7 prohibiciones verificadas)
  PROCESS (PESADAS, en alcance) ............  17
  TECHNICAL_STANDARD .......................   6
  LEGACY_FUNCTION ..........................   2
  PROCESS fuera de alcance (LIVIANAS) ......  13

Por estado:
  COVERED ..................................  57   (59 %)
  PARTIAL ..................................  25   (26 %)
  ABSENT ...................................   5   ( 5 %)
  OUT_OF_SCOPE .............................   6   ( 6 %)  + 13 procesos LIVIANAS
  NOT_VERIFIABLE ...........................   2   ( 2 %)
  REQUIREMENT_CONFLICT .....................   1   ( 1 %)
```

## 10. HALLAZGOS PRODUCIDOS POR ESTA VALIDACIÓN

| ID | Hallazgo | Elemento | Sev. | Destino |
|---|---|---|---|---|
| **R-13** | Consumo de agua no capturado | `CV-D08` | **P1** | `GA-REM-021` |
| **R-14** | Tasa de Eclosión devuelve texto | `CV-K11` | **P1** | `GA-REM-022` |
| **R-15** | Documentación del cliente sin usar para validar | — | P1 | **cerrado por esta spec** |
| **R-16** | Rotación de huevos: solo booleano, falta frecuencia y ángulo | `CV-D21` | **P2** | backlog · candidato a `GA-REM-021` |
| **R-17** | 12 KPI del cliente en `PARTIAL`: 5 implementados sin consumidor, 7 nunca calculados | `CV-K01,04,05,06,07,09,10,12,13,14,16,17` | **P1** | `GA-REM-022` (ampliada) |
| **R-18** | No existe curva de peso estándar, pese a que `spec.md §4.5` exige la alerta | `CV-T06` | **P2** | backlog |
| **R-19** | Sin validación de unidad de medida | `CV-R08` | **P3** | backlog |
| **R-20** | No se consume ningún maestro ni inventario de SAP: 6 de las 17 reglas obligatorias del cliente son inaplicables | `CV-R03,04,06,07,09,11,12`, `CV-F04`, `CV-F06` | **P1** | `GA-REM-017` (`BLOCKED_EXTERNAL`) |
| **R-21** | `SapPayload` declara `external_transaction_id`, `source_system` y `sap_reference_item` —los tres campos que `Recomendación central §19` exige contra duplicados— y **ninguno se puebla jamás** | `CV-R16` | **P1** | `GA-REM-010` (ampliada) |
| **R-22** | No existe bandera de riesgo manual en la inspección, exigida en `Recomendación central §7` | `CV-F15` | **P2** | backlog |

**10 hallazgos.** Tres ya tenían spec (`R-13`, `R-14`, `R-15`); dos amplían specs existentes (`R-17`→`022`, `R-21`→`010`); cinco entran al backlog **sin implementarse en esta Wave**.

## 11. NUEVOS REQUERIMIENTOS (`GA-REQ`)

Aplicando §9 del encargo — *una mención documental no constituye automáticamente una feature*.

| Nuevo `GA-REQ` | Elemento | Justificación de que el software debía soportarlo |
|---|---|---|
| **GA-REQ-057** | Registro de consumo diario de agua | figura en **«Datos Diarios a Registrar»** de tres etapas del documento de requerimientos; el sistema anterior lo tenía |
| **GA-REQ-058** | Rotación de huevos con frecuencia y ángulo | figura en **«Datos Diarios a Registrar → Incubación»**, no en un anexo técnico |
| **GA-REQ-059** | Identificador de transacción externa hacia SAP | `Recomendación central §19` lo declara **campo obligatorio para evitar duplicados**; el modelo ya lo previó y no lo usa |
| **GA-REQ-060** | Bandera de riesgo en la inspección de granja | `Recomendación central §7` la lista entre los datos que la app debe capturar |

**No se generan `GA-REQ`** para: manuales Ross/Cobb (referencia técnica), el contexto de negocio del PDF de compra de reproductoras, los formatos vacíos (`RA-04`), ni la funcionalidad legacy no verificable.

## 12. REQUIREMENT CONFLICTS

| ID | Conflicto | Fuentes | Estado |
|---|---|---|---|
| **RC-07** *(nuevo)* | **Política de mortalidad frente a SAP.** `Recomendación central §9` presenta **tres políticas excluyentes** (solo KPI operativo · movimiento de baja/merma · registro estadístico + CO) y afirma «la empresa debe escoger una sola política». La implementación asume implícitamente «solo KPI» al no generar movimiento alguno. **No hay decisión registrada.** | `Recomendación central §9` vs implementación | **abierto** — decisión de negocio; afecta a `GA-REM-017` |

`RC-01` … `RC-05` siguen abiertos sin cambios. `RC-06` quedó cerrado.

## 13. VERIFICACIÓN DE NO MODIFICACIÓN

```
backend/app/           modificados: 0
frontend/src/          modificados: 0
alembic/versions/      modificados: 0
processCatalog.ts      modificado:  no
identificadores AVI-*  introducidos: 0  (el único existente es un placeholder preexistente)
```

`GA-REM-020` es una **validación documental**. No transformó nada en rediseño.

## Correcciones del tranche 8 (2026-09-10)

- `CV-F07` decía «`bird_reception` con distribución multi-galpón y **validación ±10 %**»: el ±10 % era un aviso de cliente sin fuente,
  contrario a `OD-04` (`R-169`); se retira (`GA-REM-035-A`). La validación de cantidades es `BR-18` (backend).
- `CV-D23` daba por «COVERED» sanos/débiles al nacer por las etiquetas del formulario; el modelo no los tenía y el formulario **duplicaba**
  los nacidos (`R-170`). Cobertura real tras `GA-REM-021-C`: `chicks_healthy`/`chicks_weak` en el evento; `B13` cerrado en el tranche 8.
