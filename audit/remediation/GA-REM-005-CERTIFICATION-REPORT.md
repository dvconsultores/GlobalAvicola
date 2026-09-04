# GA-REM-005 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-005` — Mortalidad y balance de aves |
| **Wave** | 2 · **Stage 4** |
| **Fecha** | 2026-09-04 |
| **Hallazgos** | `P0-1` · `R-24` · `R-38` · `R-39` · `R-40` · `R-41` |
| **Estado final** | **`CERTIFIED`** (Wave 2.5) — `AC08` enmendado y satisfecho; 9 de 9 AC verificados |

## Original finding

`P0-1` — `_check_and_create_alerts` llamaba a `get_current_bird_balance` sin importarla y
con tres argumentos cuando acepta dos (`validators.py:21`). **Ninguna mortalidad válida
podía registrarse**: el `NameError` salía como 500 *después* de haber persistido el evento.

La suite no lo detectaba porque su único test de mortalidad usaba `quantity: 999999`, que
`BR-01` rechazaba antes de que el generador de alertas llegara a ejecutarse.

## Evidence

```
app/operations/service.py:246: in _check_and_create_alerts
    balance = await get_current_bird_balance(self.db, event.lot_id, self.company_id)
E   NameError: name 'get_current_bird_balance' is not defined
```

## Implementation

No se hizo el arreglo mínimo. Se reconstruyó el flujo completo —lote → saldo → entrada →
causa → validación → persistencia → efecto en el saldo → alerta → auditoría → respuesta— y
en el camino aparecieron cuatro defectos más, todos confirmados en ejecución.

| Hallazgo | Corrección |
|---|---|
| **`P0-1`** | `get_current_bird_balance` importada y llamada con su firma real |
| **`R-39`** *(nuevo, P1)* | Una mortalidad de **cero aves se aceptaba con 201**: `validate_mortality` —que rechaza el cero por `BR-01`— solo se invocaba `if total_qty > 0`. La guarda se retiró: la regla debe aplicarse siempre |
| **`R-38`** *(nuevo, P1)* | `GET /operations/alerts` era **inalcanzable**: se declaraba después de `/{event_id}`, que lo capturaba e intentaba interpretar `"alerts"` como entero. Rutas reordenadas. El frontend lo usa en `LotDetailPage.tsx:56` y `DashboardPage.tsx:107`, de modo que las alertas nunca se mostraron |
| **`R-40`** *(nuevo, P0)* | `EGG_RECEPTION_CLASSIFICATION` existía en el enum de Python desde `939fd14` (2026-06-27) y **no en el tipo `eventtype` de PostgreSQL**. El 25.º tipo de evento era inutilizable: `InvalidTextRepresentationError` → 500. Migración `j0k1l2m3n4o5` |
| **`R-41`** *(nuevo, P0)* | `birdtypeenum` contenía `'hatchery'` en minúsculas mientras SQLAlchemy persiste el **nombre** del miembro, `'HATCHERY'`. Ningún lote de incubadora podía crearse. Migración `k1l2m3n4o5p6` |
| **`AC05`** | La generación de alertas ya no puede tumbar el registro: se acota con captura explícita **y `logger.exception`**, nunca en silencio. Es la lección de `P0-1` — un defecto en un artefacto derivado se llevó por delante la funcionalidad entera |
| Umbrales | `MORTALITY_WARNING_PCT` y `MORTALITY_CRITICAL_PCT` con nombre, no incrustados |

### Ampliación del comprobador de deriva

`R-40` y `R-41` compartían escondite: **la comprobación de deriva de esquema comparaba
tablas y columnas, no valores de tipos enumerados**. Se amplió `scripts/verify.sh` para
contrastar cada enum del modelo con lo que declaran las migraciones, y se añadió el test
`test_los_enums_de_python_existen_en_postgresql`, que lo verifica contra la base real.

El comprobador ampliado encontró `R-41` **inmediatamente después** de corregir `R-40`.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC01` | Registro válido; el saldo baja | ✅ 1000 → mortalidad 10 → 990 |
| `AC02` | Mortalidad > saldo → 400 con `BR-01`, sin persistir | ✅ mensaje con el saldo disponible |
| `AC03` | Cantidad cero o negativa rechazada | ✅ **corregido** (`R-39`) |
| `AC04` | Alerta por umbral: 3 % warning, 8 % critical | ✅ tres casos parametrizados |
| `AC05` | Un fallo en las alertas no pierde el evento | ✅ verificado inyectando un fallo |
| `AC06` | `BR-06` fecha anterior a la activación | ✅ rechazado por regla con identificador |
| `AC07` | Secuencia 1000 −10 −5 −100 = 885 | ✅ · más `AC07b`: `bird_transfer` **neutro** (`RR-02`) |
| `AC08` | Umbral configurable por empresa | ⚠ **`DEFERRED`** — ver abajo |
| `AC09` | Ningún tipo de evento devuelve 500 | ✅ los 25 barridos; **destapó `R-40`** |

### Por qué `AC08` queda diferido

Exige una columna nueva en `companies` y su migración. Ningún hallazgo lo requiere: es una
funcionalidad, no la corrección de un defecto, y la Wave 2 tiene por objeto los P0 de
runtime e integridad. Diferirlo es una decisión de alcance, no un olvido: los umbrales
quedan como constantes con nombre para que el cambio se reduzca a sustituirlas por una
consulta de configuración. Se traslada a **`GA-REM-019`**.

Por eso el estado es `PARTIALLY CERTIFIED` y no `CERTIFIED`.

## Tests

`tests/test_mortality.py` — **13 PASS · 0 FAIL**

| Cobertura | Casos |
|---|---|
| Registro válido, saldo, causa persistida | 1 |
| Mortalidad sobre el saldo | 1 |
| Cantidad 0 y negativa | 2 |
| Umbrales de alerta (1 %, 3 %, 10 %) | 3 |
| Fallo del generador de alertas | 1 |
| `BR-06` | 1 |
| Secuencia completa del saldo · transferencia neutra | 2 |
| Los 25 tipos sin 5xx | 1 |
| Deriva de enums contra PostgreSQL | 1 |

## Files changed

```
backend/app/operations/service.py       P0-1, alertas no fatales, umbrales con nombre, R-39
backend/app/operations/router.py        R-38: rutas de alertas antes de /{event_id}
backend/alembic/versions/j0k1l2m3n4o5…  R-40: EGG_RECEPTION_CLASSIFICATION en eventtype
backend/alembic/versions/k1l2m3n4o5p6…  R-41: HATCHERY en birdtypeenum
backend/scripts/verify.sh               deriva de enums
backend/tests/test_mortality.py         nuevo, 13 tests
frontend/**                             SIN CAMBIOS
```

## DB changes

**Dos migraciones**, ambas necesarias y verificadas antes de escribirlas: los valores
faltaban realmente en los tipos de PostgreSQL. Ambas son aditivas (`ADD VALUE IF NOT
EXISTS`) e idempotentes. `downgrade` no elimina valores porque PostgreSQL no lo permite y
recrear el tipo pondría en riesgo datos existentes.

Cadena Alembic: **1 head** (`k1l2m3n4o5p6`), deriva de tablas 0, deriva de enums 0.

## Regression

| Métrica | Tras Stage 3 | **Tras Stage 4** |
|---|---|---|
| Recolectados | 155 | **168** |
| PASS | 153 | **167** |
| FAIL | 2 | **1** |

El único fallo restante es `test_f4_approve_event`, correspondiente a `BR-14` y asignado al
**Stage 7**. Quality gates **8/8 en verde**, ahora con la comprobación de enums incluida.

## `RC-07`

Sigue abierto y **no bloquea nada de lo hecho aquí**: por `RR-07` la captura de mortalidad,
su validación contra el saldo y su indicador son requisitos firmes con independencia de la
opción contable. Solo el mapeo a documento SAP queda supeditado, y vive en `GA-REM-017`.

## Hallazgos anotados, no corregidos

| ID | Observación | Sev. | Destino |
|---|---|---|---|
| `R-24` | `bird_transfer` no valida población de origen ni capacidad de destino a nivel de galpón | P2 | `GA-REM-019` |
| `R-42` | `get_current_bird_balance` no filtra por compañía: un `lot_id` ajeno devolvería saldo | P1 | `GA-REM-002` (Stage 5) |
| `AC08` | Umbral de mortalidad configurable por empresa | P2 | `GA-REM-019` |

## Final status

**`PARTIALLY CERTIFIED`.** La mortalidad funciona por primera vez: se registra, valida
contra el saldo, conserva su causa, ajusta el balance y genera alertas —que además ahora se
pueden consultar—. Ocho de los nueve AC quedan verificados; el noveno se difiere con motivo
explícito y destino asignado.


---

# ADDENDUM — Wave 2.5 · revisión formal de `AC08`

## La afirmación de la Wave 2 era incorrecta

La Wave 2 difirió `AC08` diciendo que «ningún hallazgo lo requiere». **Eso era falso**, y la
revisión de genealogía que exigía la Wave 2.5 lo demuestra:

| Fuente | Qué dice |
|---|---|
| `docs/02-functional-spec.md:516` (§3.14) | «Mortalidad > umbral **configurable**» |
| `audit/06_PROCESS_COVERAGE.md:259` | «implementado con umbral **fijo** 3 % / 8 % en código» — registrado como hueco de cobertura |

El requisito existía y la auditoría ya lo había señalado. Diferirlo por «falta de fuente»
fue un error de análisis, y se corrige aquí en lugar de dejarlo en pie.

## Lo que sí era sobrealcance

Ninguna fuente pide que el umbral sea configurable **por empresa**. Esa precisión la añadió
la propia spec de remediación al redactar el AC. Implementarla exigiría una columna nueva,
su migración, su pantalla y su modelo de precedencia, para una necesidad que nadie enunció.

**Sobrealcance parcial:** el AC tomó un requisito legítimo y le añadió una dimensión
inventada.

| Elemento | Disposición |
|---|---|
| Umbral **configurable** | **implementado** — `MORTALITY_ALERT_WARNING_PCT` y `MORTALITY_ALERT_CRITICAL_PCT` en `Settings`, el mismo mecanismo que gobierna el resto del sistema. Sin esquema, sin migración, sin modelo nuevo |
| Alcance **por empresa** | **`REMEDIATION_SPEC_OVERREACH`** → `GA-REM-019` como **mejora opcional**, no deuda crítica |

No se sustituyó el AC por otro más fácil: se retiró del alcance obligatorio lo que nunca
debió estar, y se satisfizo por completo lo que la fuente exige. La enmienda formal queda
en la propia spec, con AC original, genealogía, análisis y fecha.

## `AC08` — verificación

| Criterio | Resultado |
|---|---|
| El umbral se lee de la configuración | ✅ |
| No quedan literales en el generador de alertas | ✅ (con límites de palabra: `35.0`, el máximo de temperatura, no es un falso positivo) |
| Cambiar la configuración cambia el comportamiento | ✅ |

`tests/test_mortality.py` — **16 PASS · 0 FAIL** (13 previos + 3 de `AC08`).

## Nota de alcance

`_check_and_create_alerts` conserva umbrales fijos de temperatura (`18.0`/`35.0`) y humedad.
`docs/02 §3.14` no los enumera entre los tipos de alerta exigidos: quedan fuera de alcance y
se registran como `R-49` (P3) en `GA-REM-019`. No se amplía el alcance por simetría estética.

## Estado final

**`CERTIFIED`** — 9 de 9 AC verificados. La mortalidad se registra, valida contra el saldo,
conserva su causa, ajusta el balance y alerta con umbrales configurables.
