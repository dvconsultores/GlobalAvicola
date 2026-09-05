# CERTIFICACIÓN · `R-60`

**`GA-REM-030` · Pertenencia en los vínculos de trazabilidad** · 2026-09-05

| | |
|---|---|
| `R-60` | **`CERTIFIED`** |
| `P-10` | **sigue `PARTIAL`** — bloqueado por `R-78`, hallazgo nuevo (§8) |

---

## 1. El hallazgo, en su forma real

El registro lo describía como «las claves de trazabilidad no comprueban pertenencia». Al ir
al código resulta ser más ancho: `POST /lots/egg-batches` y `/chick-batches` construían la
entidad **directamente desde el cuerpo de la petición**.

```python
batch = EggBatch(**data.model_dump())      # lots/router.py:199
```

Sin comprobar pertenencia, sin comprobar existencia. El único filtro era `lots:create`.

> No confundirlo con el auto-enlace: aquel defecto era `RC-04` y `GA-REM-008` lo cerró.

## 2. Por qué importa, dicho con precisión

`EggBatch` y `ChickBatch` **no declaran `company_id`**. Su dueño es derivado de los lotes que
enlazan, de modo que un vínculo entre compañías produce un registro que **ninguna compañía
puede reclamar**.

Y hay una consecuencia concreta, no teórica: `GET /lots/{id}/traceability` valida la compañía
del lote **raíz** y devuelve después los vínculos sin comprobar la de los lotes referenciados
(`router.py:167-183`). Un vínculo cruzado hace que un usuario de la compañía A vea, en su
propio árbol, un nodo que apunta a un lote de la B.

```
R-60 es la puerta de escritura capaz de fabricar exactamente el estado que
GA-REM-008 AC06 —ya certificado— promete imposible.
```

## 3. Severidad

**P2, mantenida.** Llegar exige `lots:create`, que las semillas solo conceden al Super Admin.

Conviene precisar el motivo, porque el registro lo decía de forma que invitaba a leerlo como
una garantía: es una propiedad **de las semillas**, no de la estructura. El permiso es
concedible a cualquier rol —así se hizo en `GA-REM-029 AC07`—, y en cuanto un cliente lo
conceda, la puerta queda abierta a un usuario corriente.

No se eleva a P1 por haber bloqueado una certificación.

## 4. La regla, resuelta por norma

`§15` pedía decidir la semántica del Super Admin entre cuatro opciones. Ninguna encajaba,
porque la pregunta correcta no es sobre el actor sino sobre el par:

> ¿Puede un vínculo generacional unir lotes de compañías distintas?

Las fuentes dicen que no: el modelo carece de `company_id` propio; `GA-REM-008 AC06` está
certificado; `spec.md §8.14` exige el aislamiento. Y sobre el Super Admin, las fuentes hablan
de **ver** todas las compañías (`spec.md:337`, `docs/02:77`), con `scope all`.

De ahí **dos** reglas, deliberadamente separadas:

| | Regla | A quién vincula |
|---|---|---|
| `A` | pertenencia del actor: solo lotes de su compañía efectiva | a todos menos al Super Admin sin contexto (exención ya existente y documentada) |
| `B` | coherencia del par: los dos lotes, de la misma compañía | a **todos**, Super Admin incluido |

`B` no es autorización sino integridad del dato. **No se modificó el RBAC**: el Super Admin
conserva su autoridad global y solo pierde la de crear un registro sin dueño.

## 5. Implementación

Una función en `app/tenancy.py`, donde ya vive la pertenencia (`AC07`), y la misma llamada en
las dos puertas (`AC06`). No se duplica la regla en el router ni en el servicio.

## 6. Evidencia

### El hallazgo, reproducido antes de corregir

Con el código vulnerable, **6 de 8** pruebas fallaban, y por la causa correcta:

| Prueba | Resultado previo |
|---|---|
| `AC01` un usuario ajeno enlaza lote de otra compañía | **201** — el vínculo se creó |
| `AC02` el Super Admin cruza compañías | **201** |
| `AC03` lote inexistente | **500** `ForeignKeyViolationError` |

Los tramos de CONTROL pasaban, así que los rechazos posteriores no vienen de una petición mal
formada.

### Después

| `AC` | Prueba | Resultado |
|---|---|---|
| `AC01` `AC06` | `test_t_060_01_...` ×2 rutas | PASS |
| `AC02` | `test_t_060_02_...` ×2 rutas | PASS |
| `AC03` | `test_t_060_03_...` ×2 rutas | PASS |
| `AC04` | comprobación de efectos en las anteriores | PASS |
| `AC05` | `test_t_060_04_...` + 4 pruebas de `GA-REM-008` | PASS |
| `AC01` aislado | `test_t_060_06_...` | PASS |
| `AC02` cara complementaria | `test_t_060_05_...` | PASS |

### Puerta de validez — y lo que descubrió

La primera pasada de mutación **no rompió nada** al quitar dos de las tres reglas. El motivo
era mío: los sujetos de las pruebas tenían empresa, de modo que la regla `A` rechazaba antes
y las otras dos podían desaparecer sin que nada lo notara.

Se rehicieron con un **Super Admin sin contexto** (`company_id = None`), creado por la API —
`docs/02 §76` lo contempla—, que es el único actor para el que `A` se abstiene. Con eso:

| Mutación | Fallan | Restaurado |
|---|:--:|:--:|
| se retira la coherencia del par | **2** | 9/9 |
| se retira la pertenencia del actor | **1** | 9/9 |
| se retira la comprobación de existencia | **2** | 9/9 |

`git diff` tras revertir: limpio, solo la corrección prevista.

Merece decirse porque es el caso que justifica la puerta: sin ella, tres reglas habrían
quedado con pruebas verdes que no probaban dos de ellas.

### Aislamiento

El sujeto de `AC01` se provisiona **con `lots:create`** —sin ese permiso el 403 llegaría antes
que la pertenencia—, y nunca es un Super Admin cuando lo que se mide es la pertenencia del
actor. CONTROL y TRATAMIENTO comparten sujeto, permiso y forma de la petición.

`test_t_060_06` cierra el solapamiento: los **dos** lotes son de la compañía 2, así que el par
es coherente y solo la regla `A` puede rechazarlo.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 321 · 49 omitidas | **330 · 49 omitidas · 0 fallos** |
| E2E | 80/80 | **85/85** |
| Frontend | — | **no reejecutado: ningún cambio de frontend** |

Las 4 pruebas de `GA-REM-008` siguen pasando: el enlace manual y el automático no perdieron
funcionalidad.

## 7. Veredicto

```
R-60 = CERTIFIED
```

Los siete criterios de `GA-REM-030` con evidencia válida y sensible.

## 8. Lo que apareció al certificar el proceso

Cerrar `R-60` **no certificó `P-10`**. Al ejercitar la cadena completa apareció un defecto
mayor, detallado en `PROCESS-10-CERTIFICATION.md`:

```
R-78 · P1 · el vínculo generacional automático NO se crea en el orden natural
             (despacho → recepción). Las dos ramas de recepción solo actualizan un
             vínculo previo; la creación vive únicamente en la rama del despacho,
             que exige que la recepción ya exista.

R-79 · P2 · la prueba que certificaba `GA-REM-008 AC01` no puede fallar:
             `"egg_batch" in crudo.lower()` es cierto siempre, porque la respuesta
             siempre contiene la clave `egg_batches_sent`.
```

`R-78` no se corrige aquí: es otra causa, y `GA-REM-016 AC11` exige que un desajuste
descubierto genere un hallazgo y no una corrección dentro del mismo cambio.
