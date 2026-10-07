# SAP-HANA-CLOUD · 07_SYNC_WATERMARK_IDEMPOTENCY

Fecha: 2026-10-06 · SPEC 005 · `inbound/service.py`, `inbound/scheduler.py`

---

## 1 · Ciclo

```text
INITIAL_SNAPSHOT → DELTA_SYNC → PERIODIC_RECONCILIATION
```

| Estrategia | Objetos | Cómo lee |
|---|---|---|
| `SNAPSHOT` | company, plant, storage_location, vendor, material, batch, movement_type | todas las filas de la sociedad, paginadas |
| `BOUNDED_RECONCILIATION_WINDOW` | purchase_order (+ item, history), production_order, transfer_order, outbound_order, material_movement | ventana de fechas obligatoria sobre el campo de la definición |

No hay watermark universal. Ningún campo de cambio está verificado contra el sistema real, así que el delta se resuelve releyendo una ventana acotada y dejando que el hash absorba lo repetido. Los candidatos (`AEDAT`, `BUDAT`, `ERDAT`, `LAEDA`) se confirman en P5.

## 2 · Ventana

| Caso | Ventana |
|---|---|
| petición con fechas | la pedida; `date_from ≤ date_to`; máximo 366 días (más ⇒ 422, antes de tocar HANA) |
| primera sincronización | `hoy − SAP_HANA_DEFAULT_LOOKBACK_DAYS … hoy` |
| sincronizaciones siguientes | `última marca − lookback … hoy`, nunca más de 366 días |

Carga inicial más profunda o reconciliación periódica: peticiones explícitas por tramos de hasta 366 días.

## 3 · Paginación y volumen

| Límite | Valor |
|---|---|
| Tamaño de página | `min(SAP_HANA_PAGE_SIZE, max_page_size de la definición, filas restantes)` |
| Orden | `ORDER BY` estable por la clave de origen |
| Tope por objeto y petición | `SAP_HANA_MAX_ROWS_PER_SYNC` ⇒ job `partial`, watermark intacto |
| Timeout | `SAP_HANA_QUERY_TIMEOUT_SECONDS` por sentencia |

Prohibido el scan abierto: no existe forma de leer `MATDOC`, `EKBE`, `EKKO/EKPO` ni órdenes de producción sin ventana.

## 4 · Idempotencia

```text
misma clave + mismo hash   = NO-OP        (rows_noop; ni fila ni UPDATE)
misma clave + hash nuevo   = NUEVA VERSIÓN (la anterior queda is_current=false, SUPERSEDED)
misma página dos veces     = SIN DUPLICADOS
```

La clave es `(empresa, sistema, objeto, source_key)`; no depende del identificador de la petición. Contabilidad por job: `rows_read = rows_raw + rows_noop + rows_rejected`.

## 5 · Watermark

`sap_inbound_watermarks`, una fila por `(empresa, objeto, ámbito)` con ámbito `client:<MANDT>|bukrs:<BUKRS>`.

```text
batch persistido  ⇒ watermark avanza   (dentro del mismo savepoint)
batch fallido     ⇒ WATERMARK = UNCHANGED
tope alcanzado    ⇒ WATERMARK = UNCHANGED (job partial)
```

Cada objeto se sincroniza en un savepoint: extracción, RAW, validación, mapping, promoción y watermark se confirman juntos o no se confirma ninguno. El job fallido queda registrado fuera del savepoint, con su error saneado.

## 6 · Atomicidad entre objetos

Un objeto que falla no arrastra a los demás. La composición de órdenes de compra corre después de su grupo y solo si cabecera y posiciones no fallaron: una OC armada con la mitad de sus datos tendría una cantidad que BR-18 tomaría por buena.

## 7 · Concurrencia

| Nivel | Mecanismo |
|---|---|
| Mismo objeto y empresa | `pg_try_advisory_xact_lock`; si está tomado, el job queda `skipped` |
| Scheduler en el proceso | `asyncio.Lock`: una pasada a la vez |
| Conexiones a HANA | semáforo `SAP_HANA_MAX_CONCURRENCY` |

## 8 · Scheduler

| Regla | Implementación |
|---|---|
| Apagado por defecto | `SAP_HANA_SYNC_ENABLED=false` |
| No corre en pruebas | el `lifespan` no lo lanza con `GA_TEST_ENV=1` |
| Sin credenciales no hace nada | `run_scheduled_sync` devuelve `PENDING_CREDENTIALS` sin crear jobs ni reintentar |
| Alcance | cada empresa con una sociedad mapeada, una a una, con su propia transacción |
| Sin actor | `initiated_by_id` nulo, `trigger = scheduled` |
| Logs | saneados |

## 9 · Límite conocido

El sync manual es síncrono dentro de la petición HTTP. Está acotado por ventana, página, tope de filas y timeouts; un volumen mayor se reparte en peticiones por tramos o se deja al scheduler.
