# GA-F01d · SUBSANACIÓN ANEXA — R-189 (serializador de alimento/incubadora y contrato de lectura del detalle)

Fecha: 2026-09-12 · Tranche: remediación F-01 (GA-UAT-09) · Autoridad: mandato del propietario
(«REMEDIATE F-01 COMPLETELY AND REPEAT GA-UAT-09. NO OTHER RESIDUAL AUTHORIZED»).
Entrada: E2E de aceptación post-C2 → UAT-02 bloqueado por `GET /api/v1/operations/{id}` → **500**.

## 1 · Hecho observado (runtime, nube)

- Eventos creados por la UI con el payload real del asistente: `GET /operations/{id}` ⇒ **500** de forma
  determinista (ids 112, 115, 116, 117; repetido ×2 para descartar azar). Controles: sin las claves
  ⇒ 200; con `egg_movements: []` ⇒ 200; con `hatchery_params: [{}]` ⇒ 200; `SUBMIT` y `evidences` del
  mismo evento ⇒ 200 (el defecto es **solo del detalle**).
- El payload capturado en el walkthrough demuestra la forma enviada:

```json
"feed_movements": [{}],
"hatchery_params": [{}],
```

  (mientras `egg_movements: []` y `egg_storage_records: []` ya salían canónicos por el arreglo C2).

## 2 · Repro local determinista (PostgreSQL de pruebas en espacio de usuario)

Matriz ejecutada contra la app local (`scripts/run_tests.sh`, evidencia en `evidence/f01d/`):

| caso | POST | GET detalle |
|---|---|---|
| sin claves de submovimiento | 201 | 200 |
| `feed_movements: []` | 201 | 200 |
| `egg_movements: []` | 201 | 200 |
| **`feed_movements: [{}]`** | 201 | **500** |
| `hatchery_params: [{}]` | 201 | 200 (fila basura persistida) |
| `feed_movements: [{}]` + `hatchery_params: [{}]` | 201 | **500** |

Excepción raíz capturada con cliente estricto (`RED_local_traceback_exception.txt`):

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for FeedMovementSchema
quantity_kg
  Input should be greater than 0 [type=greater_than, input_value=0.0, input_type=float]
```

## 3 · Causa raíz (mecánica exacta)

1. El formulario arranca con `feed_movements: [{}]` y `hatchery_params: [{}]` por omisión
   (`OperationFormPage` · valores iniciales) y el C2 solo normalizó `egg_storage_records` y las filas de
   aves ⇒ **una fila vacía viaja en alimento e incubadora** (el payload nube lo confirma).
2. `FeedMovementSchema.quantity_kg = Field(default=0.0, gt=0)`: en **alta**, la fila `{}` toma el
   default **sin validarse** (Pydantic v2 no valida defaults) ⇒ 201 y fila `feed_movements` con
   `quantity_kg=0.0` y demás campos NULL — almacenamiento accidental de `{}` (prohibido por el encargo).
3. En **lectura** (`router.get_event` → `FeedMovementSchema.model_validate(fm)`), el valor `0.0` llega
   presente ⇒ `gt=0` falla ⇒ **500**. Asimetría alta/lectura: el mismo esquema acepta por default lo
   que rechaza por valor.
4. `HatcheryParamsSchema` no tiene restricciones: la fila vacía persiste y se lee sin error ⇒ basura
   silenciosa (misma clase de defecto, sin síntoma visible).

**Corrección de diagnóstico previo**: la dependencia observada «`feed_movements` presente ⇒ 500» era en
realidad «**fila vacía `[{}]` en alimento ⇒ 500**»; las claves con `[]` son inocuas. La interpretación se
corrige en la traza del hallazgo.

## 4 · Alcance de la subsanación (extensión de R-189)

| # | Pieza | Cambio |
|---|---|---|
| D1 | Frontend · serializadores | `serializarMovimientosDeAlimento` y `serializarParamsDeIncubadora`: limpian `NaN`/vacíos y descartan filas sin contenido; se aplican en el `onSubmit` compartido (import y recepción). |
| D2 | Backend · esquemas de **escritura** estrictos | `FeedMovementCreateSchema` (`quantity_kg gt=0` con validación de default) y `HatcheryParamsCreateSchema` (al menos un campo declarado) usados por Create/Update ⇒ un cliente que envíe `[{}]` recibe **422**; nunca se persiste la fila. |
| D3 | Backend · **lectura** tolerante | El esquema de lectura de alimento deja de imponer `gt=0` ⇒ los detalles de eventos históricos con filas 0.0 (sondas, E2E y cualquier alta previa por UI) vuelven a ser legibles. No se alteran datos. |

Compatibilidad: la UI corregida no envía filas vacías; un cliente con caché antigua recibe 422 y el
error se muestra de forma segura (S3 ya corregido). No hay borrado ni reescritura de datos históricos.
Consistencia de contrato: igual que el almacenamiento (`[{}]` ⇒ 422), el fallo es **ruidoso**, no
silencioso.

## 5 · Criterios de aceptación (AC-F01D)

- **AC-F01D-01** payload de importación por UI: `feed_movements: []` y `hatchery_params: []` (sin `{}`).
- **AC-F01D-02** payload de recepción por UI: idem.
- **AC-F01D-03** API: `POST` con `feed_movements:[{}]` ⇒ 422 y **cero** filas persistidas.
- **AC-F01D-04** API: `POST` con `hatchery_params:[{}]` ⇒ 422 y cero filas persistidas.
- **AC-F01D-05** fila válida (`quantity_kg>0`) ⇒ 201; el detalle la muestra.
- **AC-F01D-06** detalle de evento **histórico** con fila 0.0 ⇒ 200 (lectura tolerante).
- **AC-F01D-07** detalle general: 0 respuestas 500 en el walkthrough E2E-01…13.
- **AC-F01D-08** vitest + tsc + build verdes; suite backend (nueva + R-153 ejecutable) verde.
- **AC-F01D-09** R-153 recertificada sobre la nueva generación (addendum).
- **AC-F01D-10** GA-UAT-09 re-ejecutado (7/7) tras el arreglo.

## 6 · Pruebas previstas

- Frontend: unit de los dos serializadores + extensión del contrato de payload (import/recepción) en
  `frontend/src/pages/operations/__tests__/f01.*`.
- Backend: `backend/tests/test_f01d_filas_vacias.py` — API real + verificación SQL (conteo de filas),
  incluido el caso histórico (fila 0.0 insertada y detalle 200).
- Suites completas: vitest, tsc, build (frontend); suite backend íntegra (PostgreSQL de pruebas en
  espacio de usuario).
- Runtime: E2E-01…13 con aserciones de payload (`feed/hatchery []`), detalle del evento histórico
  (id 100) legible tras el despliegue, y walkthrough UAT-01…07.

## 7 · Hallazgo colateral de suite (R-153) — se corrige en este anexo

Al ejecutar por primera vez la suite R-153 en el PostgreSQL de pruebas local, **11/11 casos fallan en
el fixture**: `tests/test_r153_import_lot_auto.py` usa `FarmType.GRANDPARENT` — miembro **inexistente**
(enum real: `BREEDING/PRODUCTION/FATTENING/MIXED`) — y su teardown no limpia `feed_movements`
(violación de FK al borrar eventos). La afirmación de C2b «suite R-153 a 11 casos» era *declarada-CI* y
**nunca se ejecutó**. Corrección: valor válido en el fixture + limpieza de tablas hijas en el teardown;
la suite pasa a ejecutarse verde localmente y se incorpora como evidencia de recertificación.

## 8 · Fuera de alcance

F-01b, F-01c, OBS-2/3, cualquier otro residual, AOD-06/AOD-24, Wave B/C, SAP.
