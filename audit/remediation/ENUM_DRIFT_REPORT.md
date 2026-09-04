# ENUM DRIFT REPORT

**Fecha** 2026-09-04 · **Wave** 2.5 · **Origen** `R-40`, `R-41`
**Método** introspección de `Base.metadata` contrastada con `pg_type` / `pg_enum`

---

## 1. Por qué existe este informe

`R-40` y `R-41` compartían escondite. La comprobación de deriva de esquema comparaba
**tablas y columnas**, y ambos defectos vivían en un plano que no miraba: los **valores de
los tipos enumerados**.

- `EGG_RECEPTION_CLASSIFICATION` estaba en el enum de Python desde junio y no en
  `eventtype`. El 25.º tipo de evento era inutilizable.
- `birdtypeenum` tenía `'hatchery'` en minúscula mientras SQLAlchemy persiste el **nombre**
  del miembro, `'HATCHERY'`. Ningún lote de incubadora podía crearse.

Ninguno de los dos alteraba una tabla ni una columna. La comprobación decía `deriva=0` y
tenía razón sobre lo que miraba.

**No basta con auditar los dos conocidos.** Aquí se auditan los 16.

---

## 2. Resultado — los 16 enums

| Enum | Python | PostgreSQL | Estado |
|---|---:|---:|---|
| `actiontype` | 5 | 5 | `MATCH` |
| `auditaction` | 21 | 21 | `MATCH` |
| `auditmodule` | 11 | 11 | `MATCH` |
| `batchstatus` | 3 | 3 | `MATCH` |
| **`birdtypeenum`** | 4 | 5 | **`UNUSED_VALUE`** — `'hatchery'` histórico, conservado a propósito |
| `eventstatus` | 13 | 13 | `MATCH` |
| **`eventtype`** | 25 | 25 | `MATCH` — era `DB_VALUE_MISSING`, corregido por `j0k1l2m3n4o5` |
| `farmtype` | 4 | 4 | `MATCH` |
| `housetype` | 3 | 3 | `MATCH` |
| `lotstatus` | 3 | 3 | `MATCH` |
| `payloadstatus` | 5 | 5 | `MATCH` |
| `permissionaction` | 9 | 9 | `MATCH` |
| `sapreferencetype` | 9 | 9 | `MATCH` |
| `sexenum` | 3 | 3 | `MATCH` |
| `syncdirection` | 2 | 2 | `MATCH` |
| `syncstatus` | 4 | 4 | `MATCH` |

```
MATCH ............... 15
UNUSED_VALUE .........  1   (birdtypeenum → 'hatchery', deliberado)
DB_VALUE_MISSING .....  0
CODE_VALUE_MISSING ...  0
CASE_MISMATCH ........  0   (era 1: birdtypeenum, resuelto añadiendo la forma correcta)
```

**Ninguna deriva nueva.** Los dos defectos conocidos eran los únicos.

---

## 3. Sobre `birdtypeenum`

Queda con cinco valores: `GRANDPARENT`, `BREEDER`, `BROILER`, `HATCHERY` y `'hatchery'`.

El último es inerte —la aplicación escribe el nombre del miembro y nunca pudo escribir la
minúscula— pero **no se elimina**. PostgreSQL no permite quitar valores de un tipo
enumerado; hacerlo exigiría recrear el tipo y reescribir todas las columnas que lo usan,
con riesgo sobre datos existentes, para retirar un valor que no molesta.

Se clasifica `UNUSED_VALUE` y se documenta, en lugar de arreglarlo por pulcritud.

---

## 4. La comprobación es ahora permanente

En dos sitios, a propósito:

| Dónde | Qué hace |
|---|---|
| `backend/scripts/verify.sh` (paso 3/8) | contrasta cada enum del modelo con lo que declaran las migraciones. Falla el *quality gate* si un valor del código no tiene migración |
| `tests/test_mortality.py::test_los_enums_de_python_existen_en_postgresql` | contrasta contra la **base real**, no contra las migraciones. Detecta también una base a la que le falten migraciones |

La primera evitaría que el defecto entrara; la segunda, que pasara inadvertido en una
instalación concreta. `R-41` lo encontró la primera **un minuto después** de corregir
`R-40`.

---

## 5. Hallazgos

Ninguno nuevo. Los dos conocidos quedan certificados por ambos caminos —instalación nueva
y actualización— en `PRODUCTION_UPGRADE_COMPATIBILITY_MATRIX.md`.
