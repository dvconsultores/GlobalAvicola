# CERTIFICACIÓN · `R-73` · `R-74` · `R-75`

**`GA-REM-029` · Contrato de cierre de lote** · 2026-09-05 · commit `94f6112`

| Hallazgo | Estado |
|---|---|
| `R-73` · el cierre respondía 500 siempre | **`CERTIFIED`** |
| `R-74` · `BR-05` vigilaba el camino que no cierra | **`CERTIFIED`** |
| `R-75` · la fecha de cierre se guardaba desplazada un día | **`CERTIFIED`** |
| `P-06` · Pollo de engorde | **sigue `PARTIAL`** — ver §5 |

---

## 1. Qué estaba roto

`POST /lots/{id}/close` devolvía **500 en todos los casos**. El servicio devuelve un resumen
y la ruta lo validaba como `LotRead`, que exige columnas que el resumen no trae. La ruta no
declaraba `response_model`, así que el desajuste nunca se detectó en arranque y vivió hasta
ejecución.

No es un endpoint más: es **el único punto de todo el backend que asigna `status = "closed"`**
—verificado por búsqueda exhaustiva—. Mientras falló, ningún lote pudo cerrarse nunca.

## 2. Cómo se decidió el contrato

No por conveniencia técnica. Cinco fuentes, y coinciden:

| Fuente | Dice |
|---|---|
| `spec.md:266` | `BR-05` · cierre requiere **resumen final** |
| `docs/02:545` | `R5` · no permitir cierre **sin resumen final** |
| `docs/15:445` | `G-09` · cierre de lote **con resumen final** |
| `LotDetailPage.tsx:197-208` | pinta siete campos de ese resumen |
| `lots/service.py:202-213` | calcula exactamente esos campos |

Una línea equivocada contra cuatro fuentes concordantes. No había conflicto que elevar.

## 3. Los dos hallazgos que aparecieron al reconstruirlo

**`R-74`.** `BR-05` exige pesaje y alimento antes de cerrar —sin ellos no hay FCR ni peso
final—. La guarda colgaba del **evento** `lot_closure`, que no cambia el estado del lote, y
faltaba en el endpoint, que sí lo cambia. Vigilaba una puerta que no lleva a ninguna parte.
El audit la daba por vigente justamente donde no estaba.

**`R-75`.** `end_date` es `DateTime(timezone=True)` y se escribía con `date.today()`, o sea a
medianoche **local**: el lote cerrado hoy se releía como cerrado ayer, y el resumen decía una
fecha mientras el registro decía otra. Es el mismo desfase que `GA-REM-028` corrigió en
`start_date` y que quedó sin aplicar al campo hermano.

### Sobre el cambio de comportamiento de `R-74`

Un lote sin pesaje dejará de poder cerrarse. Se asumió, y conviene que conste por qué no es
el caso de `GA-TD-014`:

| | `GA-TD-014` (diferido) | `R-74` (corregido) |
|---|---|---|
| La regla hoy | inerte en todas partes | **ya activa** en el camino hermano |
| El cambio | activar `BR-11` y `BR-18` por primera vez | mover una guarda existente a la puerta real |
| Depende de | `RC-07`, decisión abierta | nada |

## 4. Evidencia

### Cobertura de los criterios

| `AC` | Prueba | Resultado |
|---|---|---|
| `AC01` `AC03` `AC08` | `test_t_073_01_el_cierre_responde_con_el_resumen` | PASS |
| `AC02` | `test_t_073_02_el_contrato_esta_declarado` | PASS |
| `AC04` | `test_t_073_03_el_lote_queda_cerrado_y_persistido` | PASS |
| `AC05` | `test_t_074_04_br05_bloquea_el_cierre_incompleto` ×2 | PASS |
| `AC06` | `test_t_073_05_el_segundo_cierre_se_rechaza` | PASS |
| `AC07` | `test_t_073_06_no_se_cierra_el_lote_de_otra_empresa` | PASS |
| `AC09` | `test_t_073_07_sin_permiso_no_se_cierra` | PASS |

### Puerta de validez — mutación controlada y revertida

Un PASS no es evidencia si la aserción no puede fallar. Se revirtió cada corrección por
separado y se restauró:

| Mutación | Resultado | Restaurado |
|---|---|---|
| se retira `response_model` y vuelve `LotRead.model_validate` | **5 de 8 fallan** | 8/8 |
| se retira `validate_lot_closure` del cierre | **2 fallan** | 8/8 |
| se retira la normalización de `end_date` | **2 fallan** | 8/8 |

Las tres correcciones tienen pruebas sensibles a su ausencia.

### Aislamiento (`AC07`)

El sujeto se provisionó **con `lots:create`**: sin ese permiso el 403 llegaría antes que el
aislamiento y la prueba no mediría nada. **No** se usó un super admin, exento por diseño
(`R-36`). CONTROL y TRATAMIENTO comparten sujeto y llamada; solo cambia de quién es el lote.

- TRATAMIENTO · lote de otra empresa → **404**, y el lote sigue `active`.
- CONTROL · lote propio, mismo sujeto → **200**.

### Cadena en la pila real

`e2e/proceso-p06-pollo-de-engorde.spec.ts` recorre los nueve pasos operativos y cierra:
**5 de 5 PASS**. Es una prueba por API contra el backend en marcha, no por interfaz.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 313 pasan · 49 omitidas | **321 pasan · 49 omitidas · 0 fallos** |
| E2E | 75/75 | **80/80** |

El cambio de comportamiento de `AC05` no rompió ninguna prueba existente.

## 5. Por qué `P-06` sigue `PARTIAL`

El paso terminal ya funciona, pero la cadena tiene once pasos y dos siguen incompletos:

| Paso | Hueco | Estado |
|---|---|---|
| `bird_reception` | `GA-TD-014` · la OC viaja en `extra_data.sap_order_ref`, de modo que `validate_oc_limit` sale por su primera línea y `BR-18` nunca se aplica | **abierto** — diferido en `C-15`, pendiente de `RC-07` |
| `weight_recording` | `GA-REQ-037` · sin alerta de peso fuera de curva | **abierto** |

```
P-06 = PARTIAL
```

**El bloqueante elegido no certificó ningún proceso por sí solo.** Se dice sin rodeos: la
matriz de alcance ya anticipaba que `R-73` tenía fan-out 1 y que el frente de mayor palanca
era `GA-TD-014`, retenido por una decisión que no me corresponde tomar.

El hueco de `GA-TD-014` queda además **fijado por una prueba** que lo documenta en vez de
esconderlo: si `sap_document_ref` deja de ser nulo, esa prueba falla y obliga a revisar la
certificación de `P-06` en lugar de dejarla obsoleta en silencio.

## 6. Hallazgos que siguen abiertos

Ninguno se cierra por no bloquear:

| Hallazgo | Bloquea | Estado |
|---|---|---|
| `GA-TD-014` | `P-01` `P-03` `P-06` | abierto · `OWNER_DECISION_REQUIRED` (`RC-07`) |
| `GA-REQ-037` | `P-01` `P-06` `P-14` | abierto |
| `R-69` · el saldo de apertura rechaza datos legítimos | ninguno | abierto |
| `R-70` · 500 con fase productiva inexistente | ninguno | abierto |
