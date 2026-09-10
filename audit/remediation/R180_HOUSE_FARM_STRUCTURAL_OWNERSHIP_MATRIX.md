# `R-180` — matriz de pertenencia estructural de las referencias de los submovimientos (galpón → granja → empresa)

**Pre-flight** WAVE B tranche 14 · 2026-09-10 · baseline `main` · `6ffd73c` · limpio · local == remoto · Alembic `x4y5z6a7b8c9` · rutas 211.

## 1. Hallazgo, con su significado exacto

Un evento operativo correctamente acotado a la empresa A puede contener **submovimientos** que referencian recursos estructurales de la empresa B.
El evento pasa la cadena de inquilino porque **sus propias** columnas (`lot_id`, `farm_id`, `house_id`, `destination_farm_id`) sí se verifican; sus hijos, no.

`UNA CLAVE FORÁNEA VÁLIDA NO PRUEBA QUE EL GALPÓN SEA DE LA EMPRESA DEL EVENTO.`

## 2. La cadena autoritativa real (leída del modelo, no supuesta)

```
House(id, farm_id, name, capacity, house_type, is_active)          ← NO declara company_id
   └─ farm_id → Farm(id, company_id, name, code, farm_type, is_active)
                    └─ company_id → Company(id)

Lot(id, company_id, farm_id, house_id, …)                          ← SÍ declara company_id (directo)
```

El galpón pertenece a la empresa **a través de su granja**. Esta cadena **ya está implementada** en `tenancy.verificar_pertenencia`, que la
recorre con un `JOIN` explícito cuando el modelo no declara `company_id` pero sí `farm_id`. `R-180` no necesita inventar la cadena: necesita
**recorrerla también para los hijos**.

Ni `House` ni `Farm` declaran unidad de negocio (`grep business_unit` sobre `masters/models.py` no devuelve nada en esas clases): la unidad se
**deriva del lote** (`OperationsService._unidad_del_lote`). Por tanto no existe atributo de unidad en la cadena estructural y la pregunta de
`OD-10` (traspaso entre unidades) **no se plantea en este eje**: ver `§7`.

## 3. Inventario completo de referencias estructurales en los submovimientos

Búsqueda exhaustiva sobre los seis esquemas de submovimiento (`SUBMOVEMENT_FIELDS`), no solo sobre los dos campos que el alta de `R-180` nombró.

| # | Campo | Tabla hija | Esquema | Recurso | Cadena autoritativa | Declarado en el alta de `R-180`? |
|---|---|---|---|---|---|---|
| 1 | `source_house_id` | `bird_movements` | `BirdMovementSchema` | galpón origen | `House → Farm → Company` | sí |
| 2 | `target_house_id` | `bird_movements` | `BirdMovementSchema` | galpón destino | `House → Farm → Company` | sí |
| 3 | `house_id` | `inspection_details` | `InspectionDetailSchema` | galpón inspeccionado | `House → Farm → Company` | **no — hallado en este pre-flight** |
| 4 | `lot_id` | `egg_storage` | `EggStorageSchema` | lote del almacenamiento | `Lot.company_id` (directo) | **no — hallado en este pre-flight** |

Referencias de submovimiento **ya gobernadas**, sin cambio en este tranche: `feed_type_id`, `hatchery_id`, `incubator_id`, `hatcher_id` (catálogos,
`R-179` · `GA-REM-002-D`) y `breed_id` (`PLATFORM_GLOBAL`: la raza no es dato de inquilino). `egg_movements` no declara ninguna clave foránea.

## 4. Superficies escritoras — inventario y clasificación

| Superficie | ¿Puede fijar estos campos? | Prueba | Entra al arreglo |
|---|---|---|---|
| `POST /api/v1/operations` (alta) | **sí** | `operations/service.py:247-260` construye los seis hijos desde el cuerpo | **sí** |
| `PUT /api/v1/operations/{id}` | **no** | `OperationalEventUpdate` no declara ninguna lista de submovimientos; `update_event` no escribe filas hijas | N/A con prueba |
| `POST /api/v1/corrections` | **no** | los campos corregibles se derivan de `OperationalEventUpdate.model_fields` (`corrections/service.py:181`), y la corrección hace `setattr(event, field_name, …)` sobre el **evento** | N/A con prueba |
| reverso (contrapartida) | derivada | `reversals/service.py:138-144` copia las columnas de las filas **originales**; no acepta entrada del cliente, luego hereda una referencia ya validada | N/A (derivada) |
| aprobación / revisión / lote / importación / masivas | no | ninguna construye submovimientos | N/A |

`R-180` es, por tanto, un hallazgo **de una sola superficie escritora**. Esto no lo hace menor: es la superficie por la que entra todo dato productivo.

## 5. Reproducción real por API (sonda temporal sobre `6ffd73c`, ejecutada y retirada)

Empresa A (granjas `A1`, `A2`; galpones `A1H`=3, `A2H`=4) · empresa B (granja `B1`; galpón `B1H`=5) · lote de A = 3 · lote de B = 4 · actor de A con
unidad concedida y permisos correctos. Todo lo demás legítimo: el único elemento ajeno es la referencia del hijo.

| Caso | Cuerpo | HTTP | Verdad persistida en la base |
|---|---|---|---|
| destino ajeno | `bird_transfer` · `target_house_id = 5` | **`201`** | `bird_movements = (3, 5)` — evento de A con galpón destino de B |
| origen ajeno | `bird_transfer` · `source_house_id = 5` | **`201`** | `bird_movements = (5, 4)` |
| ambos ajenos | `bird_transfer` · `source = target = 5` | **`201`** | `bird_movements = (5, 5)` |
| **positivo** entre granjas de la misma empresa | `A1H → A2H` | `201` | `(3, 4)` — **debe seguir aceptándose** |
| hijos mixtos | hijo 1 `A1H→A2H` válido · hijo 2 `A1H→B1H` ajeno | **`201`** | `[(3, 4), (3, 5)]` — **ambos** hijos persistidos: no hay atomicidad porque no hay validación |
| inspección con galpón ajeno | `farm_inspection` · `inspection_details[0].house_id = 5` | **`201`** | `inspection_details = (5,)` |
| almacenamiento con lote ajeno | `egg_collection` · `egg_storage_records[0].lot_id = 4` | **`201`** | `egg_storage = (4,)` |

Las cuatro referencias del `§3` se reproducen en las cuatro. El defecto es real, actual y persistente en dato productivo.

## 6. Autoridad — el requisito ya está escrito

`GA-REM-002` · **ADDENDUM Wave 3**, «Alcance de la ampliación»:

> «La ampliación cubre las referencias **estructurales**, aquellas cuya pertenencia **define de quién es el dato**» — y su tabla nombra
> `lot_id` (granja), `farm_id`, `house_id` («ubica el registro; una granja ajena lo asocia a otra empresa»), `destination_farm_id`, `event_id`.

`AC10` del mismo addendum ya dice el contrato exacto: «un recurso estructural que pertenece a la compañía B … la operación se rechaza; no se crea ni
modifica ninguna fila; no se registra auditoría». Y `AC12` (enmienda A) dice que **el sub-recurso hereda la pertenencia de su padre**.

Lo que faltó no fue la regla, sino su **alcance de aplicación**: el addendum la implementó sobre las columnas del evento y no sobre las de sus hijos.
La enmienda D (`R-179`, tranche 13) declaró explícitamente `R-180` fuera de su alcance y lo dejó clasificado: «galpones origen/destino de los
submovimientos: clase **estructural**, regla **sin caso compartido**».

**Nivel de corte:** 4 (spec vigente). **No hay decisión del propietario pendiente**: la regla está escrita, es la misma clase que `R-42`/`R-59`, y no
se propone ninguna semántica nueva.

## 7. Unidad de negocio y traspaso — por qué no se inventa ninguna restricción

`OD-10` gobierna el traspaso **limitado** entre unidades. En este eje no aplica, y la razón es estructural, no una omisión:

- `House` y `Farm` **no declaran** `business_unit_id`. No existe «unidad del galpón» que comparar.
- La unidad se deriva del **lote** del evento (`_unidad_del_lote`), y esa comprobación ya existe y ya está certificada (`R-159`/`R-160`, `R-165`, `OD-16`).

Por tanto `R-180` **no** añade `source_house.unidad == target_house.unidad`, **no** exige que el actor tenga concedida la unidad del galpón destino, y
**no** restringe el movimiento entre granjas de la misma empresa: el control positivo entre `A1` y `A2` del `§5` es obligatorio y debe seguir verde.
La frontera que `R-180` cierra es **la de empresa**, que es absoluta.

## 8. Severidad — normalización

Declarada `P2` en el alta. Reevaluada aquí conforme a la política: una referencia **entre empresas persistida en dato productivo** es la clase de
`R-42`/`R-59`/`R-179`, todas normalizadas a `P1`. Además la referencia estructural es, por la definición del propio addendum, aquella «cuya
pertenencia define de quién es el dato»: es más fuerte que la de catálogo, no más débil. Afecta trazabilidad, asociación de datos entre empresas y
futura correspondencia con SAP.

**`P2` → `P1`.**

## 9. Datos históricos

No se limpia ninguna fila existente. La prevención cierra `R-180` técnicamente; si el recuento de filas históricas con referencia cruzada resultara
distinto de cero, se registra como hallazgo aparte con su propia remediación (`§25` del método: prevención sin reescritura retrospectiva).

## 10. Criterios de aceptación (`AC-R180-01…14`) y sensibilidad prevista

| AC | Contrato |
|---|---|
| `AC-R180-01` | galpones origen y destino de la **misma** empresa: aceptado |
| `AC-R180-02` | galpón **origen** de otra empresa: denegado (`BR-07`), sin fila padre ni hija, sin auditoría de éxito |
| `AC-R180-03` | galpón **destino** de otra empresa: denegado, con las mismas consecuencias |
| `AC-R180-04` | ambos de otra empresa: denegado |
| `AC-R180-05` | `inspection_details.house_id` de otra empresa: denegado |
| `AC-R180-06` | `egg_storage.lot_id` de otra empresa: denegado |
| `AC-R180-07` | hijos mixtos (válido + ajeno): **nada** se persiste; ni el evento ni el hijo válido |
| `AC-R180-08` | movimiento entre **granjas distintas de la misma empresa**: aceptado (no se restringe por granja) |
| `AC-R180-09` | la empresa la deriva el servidor del recurso autoritativo; el cliente no puede autorizar un galpón ajeno declarando otra empresa |
| `AC-R180-10` | autoridad global sin empresa seleccionada: falla cerrado; situada en A, un galpón de B se deniega |
| `AC-R180-11` | unidad de la empresa apagada: denegado (`OD-16`), antes y después del arreglo |
| `AC-R180-12` | sin permiso o sin unidad concedida: denegado; la validación estructural no sustituye el control de acceso |
| `AC-R180-13` | anti-enumeración: el galpón ajeno se comporta como **inexistente** (`BR-07` «no encontrado»), sin revelar que existe en otra empresa |
| `AC-R180-14` | `PUT` y `POST /corrections` no pueden fijar estos campos (N/A con prueba versionada, para que deje de ser una afirmación y pase a ser un guardián) |

Sensibilidad prevista: `S1` origen · `S2` destino · `S3` cadena galpón→granja (aceptar por existencia) · `S4` inspección · `S5` almacenamiento ·
`S6` cortocircuito del primer hijo (atomicidad) · `S7` sobre-bloqueo entre granjas de la misma empresa · `S8` inquilino multicapa.
