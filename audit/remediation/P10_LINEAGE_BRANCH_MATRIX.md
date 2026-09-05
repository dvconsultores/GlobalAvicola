# `P-10` · LAS DOS RAMAS DEL VÍNCULO GENERACIONAL

`R-78` · 2026-09-05 · comparación antes de tocar código

El vínculo puede establecerse desde dos lados, porque un despacho y su recepción son dos
eventos que llegan en cualquier orden. Esta matriz compara lo que hace cada rama.

---

## 1. Las cuatro ramas reales

`operations/service.py:_auto_create_traceability_batches`

| Rama | Evento | Qué hace hoy |
|---|---|---|
| Despacho de huevo | `EGG_DISPATCH` `:239-258` | busca la recepción y **crea** el `EggBatch` |
| Recepción de huevo | `EGG_RECEPTION_HATCHERY` `:259-271` | busca el despacho y **solo actualiza** un vínculo previo |
| Despacho de pollito | `CHICK_DISPATCH` `:273-294` | busca la recepción y **crea** el `ChickBatch` |
| Recepción de aves | `BIRD_RECEPTION` `:295-307` | busca el despacho y **solo actualiza** un vínculo previo |

## 2. Comparación

| Comportamiento | Recepción | Despacho | ¿Exigido? |
|---|:--:|:--:|---|
| Encuentra la contraparte | **sí** — `_despacho_dirigido_a_este_lote` | **sí** — `_recepcion_en_el_destino_declarado` | sí |
| **Crea el vínculo si no existe** | **NO** | **sí** | **sí** — `spec.md §4.9` |
| Completa cantidad y fecha recibidas | **sí** | no (no las conoce aún) | sí |
| Evita duplicar | implícito: solo actualiza | **por evento**: cada despacho crea el suyo | ver §4 |
| Pertenencia de compañía | **sí** — `company_id == self.company_id` en la consulta | **sí** — ídem | sí |
| Excluye el mismo lote | **sí** — `lot_id != recepcion.lot_id` | **sí** — `lot_id != despacho.lot_id` | sí (`RC-04`) |
| Excluye cancelados | **sí** | **sí** | sí |
| Señal de emparejamiento | `destination_farm_id` del despacho = granja del lote receptor | ídem | sí |
| Origen / destino | los toma del despacho y de la recepción | ídem | sí |
| Registro de auditoría | ninguna de las dos lo emite | — | no lo exige `§4.9` |

**La única diferencia material es la fila en negrita.** Todo lo demás —pertenencia, exclusión
del mismo lote, cancelados, señal de emparejamiento— ya está resuelto **igual** en las dos.

## 3. Por qué eso basta y por qué no basta

La simetría de las demás filas es la evidencia de que el invariante **es el mismo** en los dos
lados: ambas ramas ya saben encontrar su contraparte con los mismos filtros y la misma
semántica de pertenencia. Lo que falta en la recepción no es criterio, es la acción.

Pero `§17` del encargo tiene razón en la advertencia: código parecido no es negocio
equivalente. Lo que autoriza a extender la creación a la recepción no es el parecido sino la
spec, que **no menciona orden alguno**:

> Un `EggBatch` se crea **automáticamente** al registrar `egg_dispatch` +
> `egg_reception_hatchery`. — `spec.md §4.9`

La conjunción es simétrica. Nada dice «primero la recepción».

## 4. Duplicados — la parte que sí difiere

El despacho crea **un vínculo por evento de despacho**, identificado por `dispatch_event_id`.
Dos despachos al mismo destino producen dos vínculos, y eso es correcto: son dos envíos.

Si la recepción pasa a crear, hay que evitar que el par produzca **dos** vínculos —uno por
cada lado— cuando ambos eventos existen. La clave natural ya está en el modelo:

```
dispatch_event_id  identifica el vínculo de forma única por envío
```

De ahí el invariante de `§18`, expresado sobre esa clave y no sobre un recuento.

## 5. Lo que la recepción debe hacer

```
CUANDO   una recepción válida encuentra su despacho
Y        no existe todavía vínculo para ese despacho
ENTONCES lo crea exactamente una vez, con el mismo origen, destino y pertenencia
         que habría creado la rama del despacho

Y CUANDO ya existe
ENTONCES lo completa, como hace hoy — sin crear un segundo
```

## 6. Lo que **no** cambia

- La rama del despacho: `GA-REM-008` la certificó y no se toca.
- El contrato de la API: ni esquema de petición, ni de respuesta, ni ruta.
- La señal de emparejamiento (`destination_farm_id`): sigue siendo la única inequívoca.
- El enlace manual y su guarda de pertenencia (`GA-REM-030`).
