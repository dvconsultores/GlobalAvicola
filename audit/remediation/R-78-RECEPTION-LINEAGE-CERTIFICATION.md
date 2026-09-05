# CERTIFICACIÓN · `R-78` y `R-79`

**`GA-REM-031`** (dominio) · **`GA-REM-016` enmienda F** (evidencia) · 2026-09-05

| | |
|---|---|
| `R-78` · el vínculo generacional no se creaba desde la recepción | **`CERTIFIED`** |
| `R-79` · la evidencia de `GA-REM-008 AC01` no podía fallar | **`CERTIFIED`** |
| `R-80` · marcos horarios mezclados | **abierto** (§8) |

---

## 1. `R-78` · el hallazgo

`spec.md §4.9` dice que el vínculo se crea automáticamente al registrar despacho **+**
recepción. La conjunción es simétrica y **no impone orden**.

La creación vivía solo en la rama del despacho, que busca una recepción ya registrada. Las
dos ramas de recepción se limitaban a actualizar un vínculo previo:

```python
batch = ...where(EggBatch.dispatch_event_id == dispatch.id)...
if batch:                       # ← si no existe, se ignora en silencio
    batch.quantity_received = ...
```

En el orden natural de la operación —se despacha antes de recibir— no se creaba **ninguno**.
Medido: la cadena de tres generaciones producía 0 vínculos.

**Severidad P1**: el requisito central del proceso `P-10` no funcionaba en su único orden
realista.

## 2. `R-79` · por qué sobrevivió a una certificación

`test_traceability.py:67` afirmaba:

```python
assert str(destino) in crudo or "egg_batch" in crudo.lower()
```

El segundo término es cierto **siempre**: la respuesta de trazabilidad contiene la clave
`egg_batches_sent` haya vínculos o no. El primero tampoco servía — el identificador de un
lote es un número corto que aparece en cualquier parte del JSON.

Esa prueba era **la evidencia de `GA-REM-008 AC01`**. Una afirmación que no puede fallar
convierte un `PASS` en falsa evidencia, y por eso `R-78` atravesó una certificación intacto.

`AC12` de `GA-REM-016` exigía no-vacuidad, pero su letra se ciñe a las afirmaciones
**recuperadas** del tramo de Playwright. Esta prueba no era heredada: la escribió
`GA-REM-008`. De ahí la **enmienda F** y su `AC13`, que generaliza el principio a toda prueba
invocada como evidencia de un criterio, de cualquier spec.

## 3. Comparación de ramas

`P10_LINEAGE_BRANCH_MATRIX.md` compara las cuatro ramas reales. Pertenencia, exclusión del
mismo lote, cancelados, señal de emparejamiento y orientación ya estaban resueltos **igual**
en los dos lados; la única diferencia material era la acción.

Eso documenta que el invariante es el mismo, pero **no** es lo que autoriza el cambio: código
parecido no es negocio equivalente. Quien autoriza es `spec.md §4.9`, que no menciona orden.

## 4. Fase roja — el hallazgo reproducido antes de tocar la aplicación

Primero se corrigió **la prueba, no el código** (§12 del encargo):

| Prueba | Resultado con el código defectuoso | Causa |
|---|---|---|
| `test_rc04_...` con la aserción reparada | **FAIL** | `AC01 exige un vínculo entre lotes distintos; hay 0: []` |
| `test_t_078_01` huevo | **FAIL** | `la recepción debe crear el vínculo ausente: []` |
| `test_t_078_02` pollito | **FAIL** | ídem |
| `test_t_078_03` exactamente uno | **FAIL** | ídem |

No por autenticación, ni permiso, ni fixture, ni esquema, ni compañía. `R-78` **reproducido**.

Las dos que pasaban en rojo —orden inverso y su control— son justamente las que recorren la
rama del despacho, que ya funcionaba.

## 5. Implementación

Las dos ramas de recepción crean el vínculo cuando no existe, con la misma orientación,
pertenencia y clave de par (`dispatch_event_id`) que habría producido el despacho.

Para no dejar dos implementaciones del mismo vínculo —el riesgo real de extender la creación
a la recepción— el mapeo de campos vive en un solo sitio (`_vincular_generaciones`), con dos
ayudantes: la lectura de cantidades desde los movimientos ya persistidos —única diferencia
de información entre las ramas— y la generación del lote.

**No se cambió** el contrato de la API, ni la señal de emparejamiento, ni la rama del
despacho.

## 6. Fase verde

| `AC` | Prueba | Resultado |
|---|---|---|
| `AC01` `AC03` `AC04` `AC08` | `test_t_078_01` | PASS |
| `AC01` `AC03` `AC05` | `test_t_078_02` | PASS |
| `AC02` orden natural | `test_t_078_03` | PASS |
| `AC02` `AC09` orden inverso | `test_t_078_04` | PASS |
| `AC06` `AC07` pertenencia | `test_t_078_05` | PASS |
| `AC09` regresión de `GA-REM-008` | `test_traceability.py` 4/4 | PASS |

`AC04` y `AC05` cubren los pasos 4 y 7 de la cadena, que **no tenían cobertura ninguna**: la
cantidad recibida que completa el vínculo y la referencia `egg_batch_id` a la generación
anterior.

### Sobre `AC06`

La API impide declarar como destino una granja ajena (`verificar_ubicacion`), de modo que el
caso no puede construirse por HTTP — buena noticia que conviene dejar dicha. La prueba
ejercita la **segunda línea**: inserta el despacho ajeno directamente en la base, saltándose
esa guarda, y comprueba que el filtro por compañía de la consulta de emparejamiento lo ignora
igualmente. CONTROL con un despacho propio: el vínculo sí se crea.

## 7. Puerta de sensibilidad

Mutación controlada: las dos ramas de recepción vuelven a no crear.

| Suite | Bajo mutación | Restaurado |
|---|:--:|:--:|
| recepción (`R-78`) | **3 fallan** | 5/5 |
| despacho (`test_traceability`) | **1 falla** ← `AC01`, ya no vacua | 4/4 |
| pertenencia (`GA-REM-030`, ajena) | 9 pasan | 9/9 |

`git diff` tras revertir: solo la corrección prevista.

El fallo en la suite de despacho **es la certificación de `R-79`**: esa misma afirmación
pasaba antes con el comportamiento ausente, y ahora lo detecta. No hizo falta una segunda
mutación artificial.

Que las 9 pruebas de pertenencia siguieran verdes confirma que la mutación era específica.

## 8. Un hallazgo nuevo, aparecido al cruzar la medianoche

```
R-80 · P2 · abierto
```

El producto mezcla dos marcos temporales: la fecha de negocio se ancla al **día local del
servidor** (`date.today()` en `BR-06`, `BR-19` y `_inicio_declarado`) mientras `created_at` se
fija con `func.now()` y se guarda como **instante UTC**.

Entre la medianoche local y la UTC los dos difieren, y entonces un lote recién creado tiene
`start_date` **posterior** a su propio `created_at`: dice haber empezado en el futuro.

Se manifestó como fallos de suite —dos en backend y uno en E2E, todos por comparar un
instante UTC con un día local—. **Verificado que no los causa este cambio**: reproducen con
el código anterior. Las pruebas se repararon en el marco de lo que cada una mira, sin tocar
el producto; la inconsistencia del producto queda abierta como `R-80`.

## 9. Regresión

| | Antes | Después |
|---|---|---|
| Backend | 330 · 49 omitidas | **335 · 49 omitidas · 0 fallos** |
| E2E | 85/85 | **85/85** |
| Frontend | — | **sin cambios: no reejecutado** |

## 10. Veredicto

```
R-78 = CERTIFIED       R-79 = CERTIFIED
GA-REM-008 AC01 = EVIDENCED (afirmación capaz de fallar, demostrado por mutación)
```
