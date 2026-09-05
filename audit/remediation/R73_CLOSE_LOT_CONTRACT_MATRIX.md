# `R-73` · QUÉ DEBE DEVOLVER EL CIERRE DE LOTE

Matriz de contrato previa a tocar código. Sirve para responder una pregunta y solo una:
**¿cuál es la respuesta correcta de `POST /lots/{lot_id}/close`?** No «cómo evitar el 500».

---

## 1. El fallo, medido

```
POST /lots/{id}/close  →  500 SIEMPRE
```

`backend/app/lots/router.py:86`

```python
lot = await _service(db, current_user).close_lot(lot_id)
return schemas.LotRead.model_validate(lot)
```

`close_lot` está anotado `-> dict` y devuelve el **resumen** (`service.py:220`). La ruta lo
valida como `LotRead`, que exige `farm_id`, `created_at`, `updated_at` y demás columnas del
lote. El resumen no los trae, así que la validación revienta con `ValidationError`.

El endpoint **no tiene `response_model`**: nadie declaró nunca el contrato, y por eso el
desajuste jamás se detectó en arranque.

> `R-73` tenía **dos** causas. La primera —`age_days` restaba un `datetime` de un `date`—
> se corrigió en `GA-REM-028 AC07`, porque la edad es la única consumidora alcanzable de
> `start_date`. Queda la segunda, que es esta y es la que gobierna el contrato.

## 2. Las fuentes, por jerarquía

| # | Fuente | Qué dice | Nivel |
|---|---|---|---|
| 1 | `specs/global-avicola/spec.md:266` | `BR-05` · «Cierre de lote requiere **resumen final**» | **spec** |
| 2 | `docs/02-functional-spec.md:545` | `R5` · «No permitir cierre de lote sin **resumen final**» | proceso |
| 3 | `docs/15-cross-reference:445` | `G-09` · «Cierre de lote **con resumen final**» — Alta | proceso |
| 4 | `frontend/.../LotDetailPage.tsx:197-208` | pinta un panel de resumen con 7 campos | implementación |
| 5 | `backend/.../service.py:202-213` | calcula y devuelve exactamente esos campos | implementación |

**Las cinco coinciden.** El contrato es el resumen; la ruta es lo que está mal. No hay
conflicto que elevar: es un error de una línea contra cuatro fuentes concordantes.

## 3. Campos, uno a uno

Cotejo de lo que calcula el servicio contra lo que consume la interfaz:

| Campo | Servicio | `LotDetailPage` | Veredicto |
|---|:--:|:--:|---|
| `age_days` | sí | `:201` | contrato |
| `total_mortality` | sí | `:202` | contrato |
| `total_feed_kg` | sí | `:203` | contrato |
| `total_eggs` | sí | `:204` | contrato |
| `total_events` | sí | `:205` | contrato |
| `approved_events` | sí | `:206` | contrato |
| `end_date` | sí | `:207` | contrato |
| `lot_id` · `lot_code` · `status` | sí | no se pintan | contrato — identifican la respuesta |

Ninguno sobra y ninguno falta. El resumen que ya se calcula **es** el contrato; lo único
que no existe es su declaración tipada.

## 4. Un hallazgo nuevo: `BR-05` guarda la puerta equivocada

Hay **dos** caminos de cierre, y `BR-05` está escrito dos veces:

| Camino | Qué es | ¿Aplica `validate_lot_closure`? | ¿Cierra el lote? |
|---|---|:--:|:--:|
| Evento `lot_closure` (`EventType.LOT_CLOSURE`) | un evento operativo más | **sí** — `operations/service.py:462` | **no** |
| `POST /lots/{id}/close` | el endpoint de cierre | **no** | **sí** — `service.py:215` |

Verificado: `status = "closed"` se asigna en **un solo sitio** de todo el backend
(`lots/service.py:215`). El evento `lot_closure` valida y se archiva, pero no cambia el
estado del lote.

De modo que la precondición de `BR-05` —«al menos un pesaje y un registro de alimento, sin
los cuales no se puede calcular el FCR ni el peso final»— **protege un camino que no cierra
nada, y falta en el único que sí cierra**.

El propio audit lo daba por hecho al revés: sobre `P-06` escribe *«BR-05 exige al menos un
pesaje y un registro de alimento antes de cerrar — implementado (`validate_lot_closure`)»*.
No es cierto para el cierre real.

```
R-74 · BR-05 se aplica al evento lot_closure y no al endpoint que cierra el lote.
       Un lote puede cerrarse hoy sin pesaje ni alimento, con un resumen sin base para FCR.
```

### Por qué se corrige aquí y no se aparta

Podría objetarse que aplicar `BR-05` al endpoint es un cambio de comportamiento, como el que
mantiene diferido a `GA-TD-014`. No es el mismo caso, y la diferencia importa:

| | `GA-TD-014` | `R-74` |
|---|---|---|
| La regla hoy | **inerte en todas partes** | **ya activa** en el camino hermano |
| El cambio | activar `BR-11` y `BR-18` por primera vez | mover una guarda existente a la puerta que sí cierra |
| Depende de | `RC-07`, decisión abierta del propietario | nada |
| Lo que creía el equipo | que estaba diferido, y lo estaba | que ya se aplicaba — el audit lo afirma |

No se está inventando una regla ni activando uno dormida: se corrige dónde vive una guarda
que el proyecto ya escribió, ya probó y ya daba por vigente. Aun así queda anotado como
cambio de comportamiento en el informe, porque un lote sin pesaje dejará de poder cerrarse.

## 5. Contrato resultante

```
POST /lots/{lot_id}/close

200  LotClosureSummary   el lote queda status=closed con end_date, y se devuelve el resumen
400  BR-05               falta pesaje o registro de alimento
400                      el lote no está activo (ya cerrado o cancelado)
404                      el lote no existe o es de otra empresa
403                      sin permiso lots:create
```

## 6. Lo que este contrato no decide

- **No** se toca el evento `lot_closure`: sigue siendo un registro operativo válido de `P-06`.
- **No** se convierte el cierre en un evento ni al revés. Son dos cosas y así estaban.
- **No** se altera `LotRead` ni ningún otro endpoint de lotes.
