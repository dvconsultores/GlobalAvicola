# Matriz de predecesores de proceso — respuesta a QA-009

**Documento**: respuesta a **QA-009** («¿se valida que los procesos se registren en orden?»)
**Fecha**: 2026-10-18 · **Baseline de código**: `83c9cd8` · **Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md` (FR-08 / AC-08.5)
**Carácter**: inventario del estado **actual** + propuesta de regla mínima

> ## La columna **PROPUESTA** no está implementada: requiere decisión Owner **OD-QA2-04**
>
> Hoy el backend **no tiene catálogo de predecesores**. Solo aplica reglas de saldo, de lote activo, de
> fecha/periodo, de capacidad y de unicidad de documento. La **secuencia** de los procesos vive
> únicamente en el frontend (`frontend/src/data/processCatalog.ts`, `STAGE_OPERATIONS`): es una guía
> de UI, no una guarda. Nada de la columna PROPUESTA se implementa en esta ronda.

Reglas generales que aplican a (casi) todos los tipos, en `backend/app/operations/service.py:889`
(`_apply_business_rules`):

- **BR-07 / BR-06** — el lote debe ser de la empresa de quien registra y estar **activo**; la **fecha
  del evento** no puede ser futura (`validate_lot_active`, `validate_event_date`, `validators.py:573-646`).
- **BR-19** — la fecha debe caer en un periodo **abierto** (`validate_period_open`, `validators.py:1090`).
- **BR-08** — granja/galpón cuando el tipo lo exige (`validate_farm_house`, `validators.py:1118`).
- **BR-10 / BR-11** — un documento SAP no se duplica, **salvo en la recepción de aves** (entregas
  parciales, `OD-04`).
- Alcance de empresa/unidad y habilitación de la unidad en toda escritura productiva.

Lote obligatorio salvo en `LOT_OPTIONAL_EVENTS` = `farm_inspection`, `hatchery_inspection`,
`grandparent_import` (`operations/service.py:64-71`).

**Columnas**: *HOY* = lo que el backend comprueba hoy · *PROPUESTA* = regla mínima propuesta (no
implementada) · *Estado* = `CUBIERTO` (la propuesta ya está cubierta por una regla equivalente) o
`PROPUESTO_PENDIENTE_OWNER`.

---

## 1. Progenitoras — cría y producción

| Evento | Precondición HOY | Precondición PROPUESTA | Estado |
|---|---|---|---|
| `grandparent_import` | **BR-22** plan de importación tipado (identidades, OC, proveedor) `validate_import_plan` (`validators.py:736`); admite registrarse **sin lote** — el lote nace al aprobar (`OD-25 (B)`) | ninguna adicional | CUBIERTO |
| `bird_reception` | capacidad por fila (`validate_house_capacity_by_rows`, `validators.py:840`), **BR-18** límite acumulado de la OC (`validate_oc_limit`, `validators.py:876`), **BR-23** cadena OC↔lote (`validate_oc_business_unit`, `validators.py:1061`), **BR-20** cuadre recibidas/muertas/rechazadas/alojadas (`validators.py:648`) | es el alta de la población: no exige población previa | CUBIERTO |
| `feed_registration` | lote activo, fecha, periodo, catálogo de alimento de la empresa — **sin** saldo de aves | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `weight_recording` | lote activo, fecha, periodo | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `mortality_recording` | **BR-01** descuento contra saldo `validate_mortality` (`validators.py:291`), rechaza cero y negativos | población viva > 0 | CUBIERTO |
| `cull_recording` | **BR-01 / E.3** `validate_bird_decrement` (`validators.py:268`) | población viva > 0 | CUBIERTO |
| `vaccination` · `medication` | lote activo, fecha, periodo, catálogo (vacuna/medicamento) de la empresa | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `water_consumption` | `validate_water_consumption` (`validators.py:782`): solo su evento, `> 0`, etapa válida | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `egg_collection` | lote activo, fecha, periodo — **sin** saldo de huevo | fase de producción iniciada (lote con aves en edad productiva) | PROPUESTO_PENDIENTE_OWNER |
| `egg_classification` | lote activo, fecha, periodo | recolección de huevo previa con saldo > 0 | PROPUESTO_PENDIENTE_OWNER |
| `egg_dispatch` | **BR-02** saldo de huevo `validate_egg_dispatch` (`validators.py:296`) + solo huevo fértil `validate_egg_dispatch_types` (`validators.py:145`) | clasificación previa + fase de producción | PROPUESTO_PENDIENTE_OWNER |
| `bird_exit` | **BR-01** salida `validate_bird_decrement` | población viva > 0 | CUBIERTO |
| `lot_closure` | `validate_lot_closure` (`validators.py:419`) | cierre solo con saldo cero o justificado | CUBIERTO |
| `farm_inspection` · `transport_inspection` | lote **opcional**; fecha, periodo, galpón/estructura de la empresa | ninguna (observacional) | CUBIERTO |

## 2. Reproductoras — cría y producción

| Evento | Precondición HOY | Precondición PROPUESTA | Estado |
|---|---|---|---|
| `bird_reception` | como en progenitoras, **más** **BR-20** cuadre de reproductoras (`validators.py:648`) y **BR-23**; capacidad y **BR-18** | alta de población: no exige población previa | CUBIERTO |
| `bird_distribution` | capacidad por fila + **BR-18** + **BR-23** (mismas guardas que la recepción, `service.py:963-985`) | población viva > 0 y recepción previa del lote origen | PROPUESTO_PENDIENTE_OWNER |
| `bird_transfer` | lote activo, fecha, periodo, ubicaciones de la empresa (`verificar_ubicacion`/`verificar_estructurales_del_submovimiento`) | población viva > 0 en origen | PROPUESTO_PENDIENTE_OWNER |
| `feed_registration` · `weight_recording` · `vaccination` · `medication` · `water_consumption` | idéntico a §1 | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `mortality_recording` · `cull_recording` | **BR-01** (saldo) | población viva > 0 | CUBIERTO |
| `egg_collection` · `egg_classification` · `egg_dispatch` | como en §1 (**BR-02** en el despacho) | fase de producción / carga previa | PROPUESTO_PENDIENTE_OWNER |
| `farm_inspection` | lote opcional; fecha, periodo, galpón | ninguna | CUBIERTO |

## 3. Incubadora (planta)

| Evento | Precondición HOY | Precondición PROPUESTA | Estado |
|---|---|---|---|
| `hatchery_inspection` | lote **opcional**; unidad **`hatchery` inequívoca** (`UNIDAD_POR_TIPO_INEQUIVOCO`, `service.py:78-81`) y persistida al nacer | ninguna | CUBIERTO |
| `egg_reception_hatchery` | lote activo, fecha, periodo, planta/almacenamiento de la empresa | despacho desde granja con saldo > 0 | PROPUESTO_PENDIENTE_OWNER |
| `egg_reception_classification` | lote activo, fecha, periodo (clasificación en planta) | recepción en incubadora previa | PROPUESTO_PENDIENTE_OWNER |
| `incubation_load` | **BR-03** carga contra saldo de huevo `validate_incubation_load` (`validators.py:316`) + parámetros de máquina (incubadora/nacedora de la empresa) | recepción + clasificación previas | **CUBIERTO** (hay saldo) / PROPUESTO_PENDIENTE_OWNER (orden) |
| `ovoscopy` | lote activo, fecha, periodo — **sin** carga previa verificada | carga de incubación previa | PROPUESTO_PENDIENTE_OWNER |
| `transfer_to_hatcher` | lote activo, fecha, periodo — sin carga previa verificada | carga de incubación previa + ovoscopia | PROPUESTO_PENDIENTE_OWNER |
| `birth_registration` | **BR-21** una sola contabilidad de nacimientos `validate_birth_registration` (`validators.py:689`) | transferencia a nacedora previa | PROPUESTO_PENDIENTE_OWNER |
| `chick_dispatch` | **BR-04** saldo de pollitos viables `validate_chick_dispatch` (`validators.py:334`) | nacimiento previo con saldo > 0 | **CUBIERTO** (hay saldo) / PROPUESTO_PENDIENTE_OWNER (orden) |
| `lot_closure` | `validate_lot_closure` | cierre de lote de incubadora con saldo cero | CUBIERTO |

## 4. Engorde

| Evento | Precondición HOY | Precondición PROPUESTA | Estado |
|---|---|---|---|
| `bird_reception` | capacidad + **BR-18** + **BR-23** (la OC de engorde no vale en reproductoras y viceversa) | no exige población previa (alta) | CUBIERTO |
| `bird_distribution` · `bird_transfer` | capacidad por fila / ubicaciones de la empresa | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `feed_registration` · `weight_recording` · `vaccination` · `medication` · `water_consumption` | lote activo, fecha, periodo, catálogos de la empresa | población viva > 0 | PROPUESTO_PENDIENTE_OWNER |
| `mortality_recording` · `cull_recording` · `bird_exit` | **BR-01** saldo de aves | población viva > 0 | CUBIERTO |
| `farm_inspection` · `transport_inspection` | lote opcional; fecha, periodo, galpón | ninguna | CUBIERTO |
| `lot_closure` | `validate_lot_closure` | cierre con saldo cero o justificado | CUBIERTO |

---

## 5. Resumen para la decisión Owner (OD-QA2-04)

1. **Lo que ya existe**: 11 tipos tienen una guarda de **cantidad** (saldo/capacidad/OC) que en la
   práctica impide registrar en vacío (mortalidad, descarte, salida, despacho de huevo, carga de
   incubación, despacho de pollitos, recepción, distribución, cierre, importación, cuadre BR-20).
2. **Lo que no existe**: ninguna comprobación de **orden**. Se puede registrar alimento, vacuna o
   inspección en un lote sin aves; ovoscopia y transferencia sin carga; nacimiento sin transferencia;
   despacho de pollitos sin nacimiento; recolección de huevo sin fase productiva.
3. **Coste de implementarlo**: un catálogo de predecesores por tipo + cadena, con lectura de saldos
   existentes. No requiere datos nuevos; requiere **decidir la severidad** (¿error bloqueante o aviso
   que exige justificación?) y qué hacer con los registros históricos ya cargados fuera de orden
   (cargas iniciales / cutover), que **no** deben quedar inválidos.
4. **Riesgo de activarlo sin decisión**: bloquearía la corrección de registros históricos y las cargas
   de cutover (`MIGRATED`).
