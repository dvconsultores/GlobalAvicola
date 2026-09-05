# `GA-REM-030` · PERTENENCIA EN LOS VÍNCULOS DE TRAZABILIDAD

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-030` · `TENANCY HARDENING SPEC` |
| **Prioridad** | **P2** · **Estado** `SPEC_READY` |
| **Hallazgo** | `R-60` |
| **Proceso** | `P-10` · Trazabilidad generacional — paso 11 |
| **Dependencias** | `GA-REM-002` (`verificar_pertenencia`) · `GA-REM-008` `CERTIFIED` |
| **Antecedente** | `audit/remediation/P10_PROCESS_CHAIN_MATRIX.md` |

> Spec propia y no enmienda de `GA-REM-008`. Aquella cubre el **aislamiento de lectura**
> (`AC06`) y la **disponibilidad** del enlace manual (`AC07`); ninguno de sus criterios
> autoriza tocar la escritura. `GA-REM-008` queda `CERTIFIED` y sin modificar.

---

## 1. Problema

`POST /lots/egg-batches` y `POST /lots/chick-batches` construyen la entidad directamente
desde el cuerpo de la petición:

```python
batch = EggBatch(**data.model_dump())
```

Sin comprobar pertenencia, sin comprobar existencia. El único filtro es `lots:create`.

`EggBatch` y `ChickBatch` **no declaran `company_id`**: su dueño es derivado de los lotes que
enlazan. Un vínculo entre lotes de compañías distintas produce por tanto un registro **sin
dueño posible** — y hace insatisfacible `GA-REM-008 AC06`, ya certificado, que promete que un
usuario nunca obtiene un lote de trazabilidad que referencie lotes de otra compañía.

`R-60` es la puerta de escritura capaz de fabricar el estado que un criterio certificado
declara imposible.

## 2. La regla

Son **dos** reglas, y conviene no fundirlas:

```
A · PERTENENCIA DEL ACTOR
    Quien no es Super Admin solo puede referenciar lotes de su compañía efectiva.
    Semántica existente de `verificar_pertenencia`: el recurso ajeno se comporta como
    inexistente, y un `company_id` nulo —Super Admin sin contexto— no impone filtro.

B · COHERENCIA DEL PAR
    Los dos lotes de un vínculo pertenecen a la MISMA compañía.
    Vincula a todo actor, Super Admin incluido: es integridad del dato, no autorización.
```

`B` no se deriva de una preferencia técnica sino de tres fuentes: el modelo carece de
`company_id` propio; `GA-REM-008 AC06` está certificado; y `spec.md §8.14` exige el
aislamiento entre empresas.

**No se modifica el RBAC.** El Super Admin conserva su autoridad global y no gana la de crear
un registro sin dueño.

## 3. Fuera de alcance

- El enlace **automático**: `GA-REM-008` lo certificó y no se toca.
- El aislamiento de **lectura** del árbol de trazabilidad: es `AC06` de `GA-REM-008`.
- `R-76`, `R-77`, `OD-04`, `GA-TD-014`, `BR-11`, `BR-18`.
- Cambiar el tipo de lote admisible en cada extremo del vínculo: no hay fuente normativa que
  lo exija y sería inventar una regla.

## 4. Criterios de aceptación

### `AC01` · El actor no alcanza lotes ajenos
Un usuario **con `lots:create`** que no es Super Admin recibe **400 `BR-07`** al enlazar un
lote de otra compañía, y **no se crea** ningún vínculo.

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo sujeto, el mismo permiso y la misma
petición; lo único que cambia es de quién es el lote.
- CONTROL — dos lotes **suyos** → 201.
- TRATAMIENTO — un lote ajeno → 400.

Prohibido un `!= 201`: una petición mal formada también lo cumpliría.

### `AC02` · El par es coherente, incluso para el Super Admin
Un **Super Admin** que enlaza un lote de la compañía A con uno de la B recibe **400** y no se
crea el vínculo. Es el criterio que distingue autoridad global de integridad del dato.

### `AC03` · Un lote inexistente se rechaza por contrato
Un identificador que no existe produce **400** con el contrato de error vigente, no un 500
por violación de clave foránea. Cae de suyo: para comparar compañías hay que leer ambos lotes.

### `AC04` · Sin efectos tras la denegación
Tras cualquier rechazo de `AC01`…`AC03`: cero vínculos nuevos, ningún lote modificado, y el
árbol de trazabilidad de ambos lotes queda como estaba.

### `AC05` · El enlace legítimo sigue funcionando
Regresión de `GA-REM-008 AC07`: dos lotes de la misma compañía se enlazan y el vínculo
aparece en el árbol. Ni el automático ni el manual pierden funcionalidad.

### `AC06` · Las dos puertas reciben el mismo trato
`AC01`…`AC05` valen igual para `/egg-batches` y para `/chick-batches`. Una regla aplicada en
una puerta y ausente en la otra no es una regla.

### `AC07` · La guarda vive en un solo sitio
La comprobación se añade a `app/tenancy.py`, donde ya vive la pertenencia. No se duplica la
regla en el router ni en el servicio.

## 5. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC06` | `backend/tests/test_traceability_ownership.py` | integración HTTP |
| `AC07` | revisión del diff | estructural |
| cadena de `P-10` | `e2e/proceso-p10-trazabilidad-generacional.spec.ts` | `API_E2E` |

## 6. Definición de terminado

- Los siete criterios pasan.
- Existe una prueba que **falla contra el código actual** antes de la corrección.
- Sensibilidad demostrada por mutación controlada y revertida.
- La cadena de `P-10` (12 pasos, `P10_PROCESS_CHAIN_MATRIX §3`) se recorre entera.
- Regresión completa sin fallos nuevos.
