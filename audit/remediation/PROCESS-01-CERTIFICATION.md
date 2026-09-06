# `P-01` · PROGENITORAS — CRÍA — INFORME DE CERTIFICACIÓN

`spec.md §4.4` · `GA-REM-035` · 2026-09-06

```
P-01 = CERTIFIED
```

---

## 1. Alcance

`§4.4` define la fase de **cría** de un lote de abuelas: doce tipos de operación, de la
importación a la salida. Las operaciones de huevo —`egg_collection`, `egg_classification`,
`egg_dispatch`— pertenecen a la fase de **producción**, que es `P-02` y está certificado desde
la Wave 3. El frontend ya las movió allí.

## 2. La cadena

| # | Paso | Estado |
|:--:|---|:--:|
| 1 | `grandparent_import` con la orden de compra | **PASS** |
| 2 | `farm_inspection` | **PASS** |
| 3 | `transport_inspection` | **PASS** |
| 4 | `bird_reception` con control de OC | **PASS** |
| 5 | `bird_distribution` | **PASS** |
| 6 | `feed_registration` | **PASS** |
| 7 | `weight_recording` | **PASS** |
| 8 | `mortality_recording` | **PASS** — `GA-REM-005` cerró el 500 |
| 9 | `cull_recording` | **PASS** |
| 10 | `vaccination` | **PASS** |
| 11 | `medication` | **PASS** |
| 12 | `bird_exit` | **PASS** |

```
12 pasos · PASS 12 · FAIL 0
```

Comprobado por **conjunto exacto** de tipos registrados, no por recuento aproximado: si
faltara un paso, la aserción lo detectaría.

## 3. Qué lo bloqueaba y qué no

**Lo que lo bloqueaba:** `GA-TD-014`. La orden de compra no llegaba al campo tipado, de modo
que `validate_oc_limit` nunca se disparaba y el paso 4 quedaba `PARCIAL`. Cerrado por
`GA-REM-035` tras la resolución de `OD-04`.

**Lo que no lo bloquea, y conviene decir por qué:** `GA-REQ-037` —la alerta de peso fuera de
curva— **no aparece en `§4.4`**. Es `§4.5` quien la exige, y por eso bloquea a `P-03` y no a
este proceso. Se verificó leyendo ambas secciones en lugar de arrastrar la anotación del
blocker matrix, que las trataba juntas.

## 4. `OD-04` en la cadena

El E2E comprueba la decisión del propietario sobre la cadena real: tres mil aves, luego dos
mil contra **la misma orden** —aceptadas— y una más —rechazada con `BR-18`, y el mensaje habla
de cantidad, no de duplicidad—.

## 5. Evidencia

`e2e/proceso-p01-progenitoras-cria.spec.ts` · 3 casos · `API_E2E`. `§4.4` no exige
comportamiento visible en ninguna de sus reglas, así que no se fabricaron pruebas de interfaz.

Backend: `test_purchase_order_receipt.py` 7/7, más la suite completa en 384/0.

## 6. Veredicto

```
P-01 = CERTIFIED   ·   12 de 12 pasos
```
