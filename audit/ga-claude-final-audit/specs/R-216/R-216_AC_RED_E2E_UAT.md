# R-216 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-216/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R216-01 | `lots_by_type` devuelve claves `'grandparent'|'breeder'|'hatchery'|'broiler'` | `test_r216_01` (rojo: `BirdTypeEnum.*`) |
| AC-R216-02 | Suma de valores = total de lotes activos (control) | `test_r216_02` (verde) |
| AC-R216-03 | FE: las 4 tarjetas muestran los recuentos | E2E (rojo: 0) |
| AC-R216-04 | Contrato documentado (claves exactas) con test que falla si cambian | `test_r216_01` |
| AC-R216-05 | Sin migración/endpoint/permiso | revisión |
| AC-R216-06 | Regresión: `test_kpi_scope.py` (ajustado), `test_kpi_hatchery.py` verdes | suites |

## 2 · Diseño RED

`backend/tests/test_r216_lots_by_type_contract.py`: empresa con lotes por tipo; aserción de claves exactas (rojo). Ajuste del test obsoleto por substring. Salida `evidence/red/`.

## 3 · E2E

`R216-RT-01`: `/dashboard/admin` con lotes de dos tipos ⇒ tarjetas correctas (captura). Artefacto `evidence/r216/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida.** Verificación informativa: captura del panel con tarjetas correctas.
