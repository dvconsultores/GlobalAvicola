# `P-10` · TRAZABILIDAD GENERACIONAL — CADENA COMPLETA

`spec.md §4.9` · `RR-02` · `RR-04` · 2026-09-05

Se levanta antes de escribir una sola prueba, para no repetir la confusión que ya costó una
vez: **certificar una capacidad no es certificar un proceso**.

---

## 1. Nombre normativo

`spec.md §4.9` la llama **Generational Traceability (Trazabilidad Generacional)**. El nombre
del encargo coincide con el de la spec.

> Nota: `spec.md` numera **dos** secciones como `§4.9` —trazabilidad generacional y
> activación manual de lotes—. Defecto documental menor, sin efecto funcional; se registra
> pero no se corrige aquí.

## 2. Entidades y su pertenencia

| Entidad | ¿`company_id` propio? | Relación | Papel generacional |
|---|:--:|---|---|
| `Lot` | **sí** | raíz del inquilino | nodo de la cadena |
| `EggBatch` | **no** | `source_lot_id` → `hatchery_lot_id` | reproductora/progenitora → incubadora |
| `ChickBatch` | **no** | `hatchery_lot_id` → `destination_lot_id` | incubadora → engorde/cría |
| `OperationalEvent` | sí | `dispatch_event_id` · `reception_event_id` | prueba documental del movimiento |

**Ningún lote de trazabilidad declara compañía propia.** Su pertenencia es *derivada* de los
lotes que enlaza. Este dato gobierna todo el análisis de `R-60` (§5).

## 3. La cadena

```
Reproductoras (producción)
  │ egg_dispatch                    ┐
  ↓                                 ├→ EggBatch
Incubadora  · egg_reception_hatchery┘
  │ chick_dispatch                  ┐
  ↓                                 ├→ ChickBatch  ──egg_batch_id──> EggBatch
Engorde     · bird_reception        ┘
```

| # | Paso | Requisito | Actor | Entrada | Estado esperado | Evidencia existente | Falta |
|:--:|---|---|---|---|---|---|---|
| 1 | `egg_dispatch` | `§4.9` | `operations:create` | lote origen, destino declarado, cantidad | evento registrado | `test_traceability` (integración) | E2E de proceso |
| 2 | `egg_reception_hatchery` | `§4.9` | `operations:create` | lote incubadora, cantidad | evento registrado | idem | E2E |
| 3 | `EggBatch` automático entre lotes **distintos** | `§4.9` · `RR-04` | sistema | — | origen, destino, cantidad despachada, fechas | `GA-REM-008 AC01` | E2E |
| 4 | La recepción completa el `EggBatch` | `§4.9` («cantidad recibida») | sistema | — | `quantity_received`, `reception_date` | — | **sin cubrir** |
| 5 | `chick_dispatch` | `§4.9` | `operations:create` | lote incubadora, destino | evento | — | E2E |
| 6 | `bird_reception` | `§4.9` | `operations:create` | lote engorde | evento | — | E2E |
| 7 | `ChickBatch` con `egg_batch_id` de referencia | `§4.9` | sistema | — | back-link a la generación anterior | `GA-REM-008 AC02` (sin el back-link) | **back-link sin cubrir** |
| 8 | Navegación bidireccional | `§4.9` | `lots:read` | `lot_id` | origen y destino visibles | `GA-REM-008 AC05` | E2E |
| 9 | Nunca un vínculo auto-referencial | `RC-04` · `RR-04` | sistema | — | ningún lote consigo mismo | `GA-REM-008 AC03` | — |
| 10 | Despacho sin recepción no inventa vínculo | `§4.9` | sistema | — | sin lote de trazabilidad | `GA-REM-008 AC04` | — |
| 11 | Enlace manual cuando el automático no es posible | `§4.9` | `lots:create` | dos lotes | vínculo creado | `GA-REM-008 AC07` | **pertenencia sin comprobar → `R-60`** |
| 12 | Aislamiento por compañía en la consulta | `GA-REM-008 AC06` | usuario de la compañía A | lote propio | ningún lote de trazabilidad referencia a la compañía B | `GA-REM-008 AC06` | E2E |

**12 pasos.** Cinco ya tienen evidencia de integración certificada (`GA-REM-008`); ninguno
tiene evidencia de proceso de extremo a extremo, que es lo que `GA-REM-016` exige.

## 4. Qué certificó `GA-REM-008` y qué no

| Certificó | No certificó |
|---|---|
| el enlace une lotes **distintos** (`AC01` `AC02`) | la cadena completa de extremo a extremo |
| nunca hay auto-referencia (`AC03`) | la cantidad recibida que completa el `EggBatch` (paso 4) |
| sin destino declarado, no se inventa (`AC04`) | el back-link `egg_batch_id` (paso 7) |
| navegación entre generaciones (`AC05`) | **la pertenencia en la escritura** (paso 11 · `R-60`) |
| aislamiento **de lectura** (`AC06`) | el aislamiento de **escritura** |
| el enlace manual sigue disponible (`AC07`) | que ese enlace sea legítimo |

`AC06` es explícito y merece leerse literal: *«un usuario de la compañía 1 consulta la
trazabilidad → **no obtiene ningún batch que referencie lotes de la compañía 2**»*.

## 5. `R-60` · identidad real

### El endpoint

```python
@router.post("/egg-batches")                       # lots/router.py:199
async def create_egg_batch(data, db, current_user=Depends(require_permission("lots","create"))):
    batch = EggBatch(**data.model_dump())          # ← el cuerpo entra tal cual
    db.add(batch)
```

Idéntico en `/chick-batches`. **No hay ninguna comprobación**: ni de pertenencia, ni de
existencia, ni de tipo de lote. El único filtro es el permiso.

### Las ocho preguntas

| # | Pregunta | Respuesta con evidencia |
|:--:|---|---|
| 1 | Endpoint afectado | `POST /lots/egg-batches` · `POST /lots/chick-batches` (`router.py:199,214`) |
| 2 | Actor que llega | cualquiera con `lots:create` |
| 3 | Por qué «solo Super Admin» | por las **semillas**: los roles sembrados no conceden `lots:create` a nadie más. **No es una garantía estructural** — el permiso es concedible, y así se hizo en `GA-REM-029 AC07` |
| 4 | Validación actual | **ninguna** |
| 5 | Validación esperada | §6 |
| 6 | Consecuencia entre compañías | un vínculo con `source_lot_id` de la compañía A y `hatchery_lot_id` de la B. Como el lote de trazabilidad **no tiene compañía propia**, ese registro no tiene dueño coherente |
| 7 | Justificación de P2 | requiere un permiso que hoy solo trae el Super Admin, y el Super Admin opera legítimamente entre compañías. Se mantiene **P2**: no se eleva por bloquear una certificación |
| 8 | `AC` de `P-10` afectado | paso **11**, y a través de él el **12** |

### La consecuencia precisa

`GET /lots/{id}/traceability` valida la compañía **del lote raíz** (`svc.get_lot`), pero
devuelve los lotes de trazabilidad **sin comprobar la compañía de los lotes que referencian**
(`router.py:167-183`).

De modo que un vínculo entre compañías creado por la puerta sin guardas hace que un usuario
de la compañía A vea, en su propio árbol, un lote de trazabilidad que apunta a un lote de la
compañía B.

```
R-60 es la puerta de escritura que puede fabricar exactamente el estado
que GA-REM-008 AC06 —ya certificado— promete imposible.
```

Eso es lo que hay que cerrar, y es la razón de que sea trabajo de `P-10` y no cosmética.

## 6. La regla, resuelta por norma y no por comodidad

`§15` del encargo pide decidir la semántica del Super Admin entre cuatro opciones. Ninguna
encaja tal cual, porque **la pregunta correcta no es sobre el actor**:

> ¿Puede un vínculo generacional unir lotes de **compañías distintas**?

Las fuentes responden que no, y no por preferencia técnica:

1. `EggBatch` y `ChickBatch` **no declaran `company_id`**: su dueño es derivado. Un vínculo
   que cruza compañías no tiene dueño posible.
2. `GA-REM-008 AC06`, **ya certificado**, promete que un usuario nunca obtiene un lote de
   trazabilidad que referencie lotes de otra compañía. Un vínculo cruzado hace ese criterio
   insatisfacible.
3. `spec.md §8.14` — «usuario de Empresa A no ve datos de Empresa B».

Y sobre el Super Admin, las fuentes hablan de **ver**: *«Super Admin ve todas las compañías»*
(`spec.md:337`, `docs/02:77`), con `scope all` (`spec.md:21`).

```
REGLA · dos reglas distintas, no una

A · PERTENENCIA DEL ACTOR   quien no es Super Admin solo referencia lotes de su
                            compañía efectiva.  Patrón existente: verificar_pertenencia.

B · COHERENCIA DEL PAR      los dos lotes de un vínculo son de la MISMA compañía.
                            Vincula a TODO actor, Super Admin incluido, porque es
                            integridad del dato y no autorización.
```

El Super Admin conserva su autoridad global —puede crear vínculos en cualquier compañía— y
**no** gana la de crear un registro sin dueño. No se modifica el RBAC.

## 7. Distancia a la certificación

| Proceso | Qué le falta | Naturaleza |
|---|---|---|
| **`P-10`** | endurecer `R-60` + E2E de proceso | corrección acotada + evidencia |
| `P-12` | 7 pantallas + contador | desarrollo de interfaz |
| `P-13` | 2 pantallas | desarrollo de interfaz |
| `P-14` | canal de notificación | desarrollo nuevo |
| `P-01` `P-03` `P-06` | `OD-04` | **decisión del propietario** |
| `P-09` `P-15` | correcciones acotadas + E2E | comparable a `P-10`, sin defecto de seguridad abierto |
| `P-08` | SAP real | `BLOCKED_EXTERNAL` |

`P-10` se confirma como la menor distancia legítima: sus defectos funcionales ya están
corregidos y certificados, y lo que queda es una guarda pequeña con patrón existente más la
evidencia de proceso que `GA-REM-016` pide.
