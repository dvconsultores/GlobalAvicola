# EL CONTRATO DE TRASPASO, CAMPO POR CAMPO

`GA-REM-040` fase 5 · `T-040-13` · `OD-10.a` · 2026-09-07

```
A  propio            dato de la unidad, acceso completo según RBAC
B  traspaso          lo mínimo para crear, ejecutar, recibir, confirmar, auditar,
                     revertir y trazar el traspaso. Solo lectura, ambos lados.
C  interno ajeno     todo lo demás del otro lado. DENEGADO.
D  agregado          se calcula sobre A ∪ B. Nunca sobre C.
```

**Regla de mínimo privilegio.** Un campo que no haga falta para una de esas siete cosas, y que
ninguna fuente mande compartir, es `C`. No se marca `B` por si acaso.

---

## 1. Los siete flujos, de `CROSS_MODULE_FLOW_MATRIX.md`

| # | Origen → Destino | Entidad puente | Estado del contrato |
|:--:|---|---|:--:|
| 1 | Progenitoras → *(Incubadora)* → Reproductora | `egg_batches` + `chick_batches` | **IMPLEMENTADO** |
| 2 | Reproductora → Incubadora | `egg_batches` | **IMPLEMENTADO** |
| 3 | Incubadora → Engorde | `chick_batches` | **IMPLEMENTADO** |
| 4 | Transferencia entre granjas | `bird_movements` | **APLAZADO** · fase 6 |
| 5 | Consolidación a SAP | `consolidated_movements` | **EXCEPCIÓN DECLARADA** · `BU-D04` |
| 6 | Revisión y aprobación | `operational_events` | **APLAZADO** · fase 6 |
| 7 | Trazabilidad generacional | `egg_batches` + `chick_batches` | **IMPLEMENTADO** |

```
IMPLEMENTADOS          4 / 7
APLAZADOS A LA FASE 6  2 / 7   dependen de eventos cuyo `lot_id` es nulable
EXCEPCIÓN DECLARADA    1 / 7   la consolidación agrupa las cuatro por definición
```

**Los flujos 4 y 6 no se aplazan por comodidad.** Ambos se apoyan en `operational_events`, cuya
cadena se deriva de `lot_id`, que es **nulable a propósito**: las inspecciones de granja no
tienen lote. Acotarlos hoy los haría desaparecer para todos, incluida la persona que acaba de
registrarlos. `OD-10.c` manda eso a «pendiente de clasificar», que es la fase 6.

**El flujo 5 no se acota, y es correcto.** La consolidación agrupa el movimiento de las cuatro
cadenas por definición; filtrarla la rompería y con ella `P-08`. `BU-D04` sigue `PENDIENTE` y su
resolución dirá si `Analista SAP` es una excepción declarada o recibe concesiones como cualquiera.

---

## 2. `egg_batches` · flujos 1, 2 y 7

| Campo | Origen | Destino | Cat. | Por qué |
|---|:--:|:--:|:--:|---|
| `id` | ve | ve | **B** | identidad del traspaso |
| `source_lot_id` | ve | ve | **B** | procedencia: `P-10` la necesita, y el destino su antecedente sanitario |
| `hatchery_lot_id` | ve | ve | **B** | destino: sin él nadie sabe a quién va (`OD-10.b`) |
| `generation` | ve | ve | **B** | discrimina la cadena; `P-10` reconstruye con ella |
| `quantity_dispatched` | ve | ve | **B** | conciliación |
| `quantity_received` | ve | ve | **B** | la merma mide al origen |
| `dispatch_date` · `reception_date` | ve | ve | **B** | conciliación y trazabilidad |
| `source_lot` → `LotRef` | ve | ve | **B** | `id`, `lot_code`, `bird_type`, `status`; **nada más** |
| `hatchery_lot` → `LotRef` | ve | ve | **B** | ídem |
| **`notes`** | ve | **NO** | **C** | anotación interna de quien despacha |
| `dispatch_event_id` · `reception_event_id` | — | — | **C** | apuntan al evento operativo, que es interno |
| `created_at` | — | — | **C** | metadato, no contractual |

**Lo que el `LotRef` deliberadamente no lleva**: granja, galpón, línea genética, curva, área,
fechas de ciclo, estado sanitario detallado. Todo eso es `C`.

## 3. `chick_batches` · flujos 1, 3 y 7

| Campo | Origen | Destino | Cat. | Por qué |
|---|:--:|:--:|:--:|---|
| `id` · `hatchery_lot_id` · `destination_lot_id` | ve | ve | **B** | identidad y los dos lados |
| `broiler_lot_id` | ve | ve | **B** | nombre heredado del destino; se sincroniza |
| `egg_batch_id` | ve | ve | **B** | el eslabón anterior de la cadena · `P-10` |
| `quantity_dispatched` · `quantity_received` | ve | ve | **B** | conciliación |
| `dispatch_date` · `reception_date` | ve | ve | **B** | ídem |
| `hatchery_lot` · `destination_lot` · `broiler_lot` → `LotRef` | ve | ve | **B** | proyección mínima |
| **`notes`** | ve | **NO** | **C** | interno |
| `dispatch_event_id` · `reception_event_id` · `created_at` | — | — | **C** | internos |

## 4. Categoría `D` · lo que el traspaso **no** concede

```
paneles ajenos · KPI ajenos · contadores ajenos · analítica ajena
```

Ningún campo del contrato es un agregado, y la fase 4 ya acota los que existen. Participar en un
traspaso **no** amplía el conjunto de unidades efectivas: se mide antes y después, y no cambia.

## 5. Antes, durante y después

| Momento | El origen ve | El destino ve |
|---|---|---|
| **antes del traspaso** | su lote (`A`) | nada de él |
| **al crearse** | el traspaso completo en `B` | el traspaso dirigido a él, en `B` |
| **al recibirse** | cantidad recibida y fecha (`B`) | lo mismo |
| **después** | la cadena, no el interior del destino | la procedencia, no el interior del origen |

**Ningún momento concede el objeto completo del otro lado.** El identificador del lote ajeno es
`B` para trazar, y **no es una llave**: pedir su detalle sigue devolviendo `404`.

## 6. Anulación y reversión

El producto distingue `RETURNED`, `CORRECTED`, `REJECTED` y permite anular **el evento
operativo**. Las entidades puente no tienen hoy endpoint de anulación propio.

```
ANULACIÓN DEL TRASPASO COMO TAL     no existe superficie · nada que acotar
ANULACIÓN DEL EVENTO ASOCIADO       fase 6, con el resto de `operational_events`
```

Se registra como **hueco de superficie**, no como contrato incumplido: no se inventa un endpoint
para poder acotarlo.

## 7. Quién puede crear un traspaso

```
HANDOFF ACCESS  =  empresa concreta
              +  origen al alcance del que despacha
              +  destino de la misma empresa y válido para el flujo
              +  RBAC
              +  proyección B explícita
```

Y explícitamente **no**:

```
CADENA ORIGEN  ↔  CADENA DESTINO   =   lectura mutua general
```

El destino **no** exige tener su cadena concedida. Eso es lo que hace que sea un contrato y no
un permiso: se dirige el traspaso a una incubadora sin obtener acceso a ella.

## 8. Cambiar el destino después de crearlo

```
SUPERFICIE DE EDICIÓN     no existe: `egg_batches` y `chick_batches` solo tienen `POST`
```

La pregunta que `GA-REM-040 §10.3` dejó como `SPEC DECISION REQUIRED` **sigue sin decidirse**, y
no se resuelve aquí inventando una regla: hoy no hay por dónde cambiarlo, de modo que el
comportamiento es el conservador —crear de nuevo— sin necesidad de legislarlo.

Cuando la fase 7 traiga administración, habrá que contestarla antes de abrir esa puerta.
