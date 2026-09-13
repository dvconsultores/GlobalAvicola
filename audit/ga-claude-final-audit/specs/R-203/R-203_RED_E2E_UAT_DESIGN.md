# R-203 · DISEÑO DE PRUEBAS RED · E2E API · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED (integración backend)

Fichero nuevo: `backend/tests/test_r203_lot_reference_tenancy.py` (patrón `test_lot_area_ownership.py`: empresa A con grandparent/breeder ON, granja+galpón+línea+curva propios; empresa B con granja+galpón+línea+curva propios; actor A).

| Nombre exacto del test | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r203_01_galpon_ajeno_es_404` | `POST /lots {farm_id: A, house_id: B, ...}` | `status == 404` y `count(lots)==0` — HEAD: 201 |
| `test_r203_02_linea_ajena_es_404_y_nula_es_201` | línea B ⇒ 404; `genetic_line_id: null` ⇒ 201 | HEAD: 201 en ajeno |
| `test_r203_03_curva_de_linea_ajena_rechazada` | lote A con `weight_curve_id` de curva de B | `status in (400,404)` y sin curva aplicada — HEAD: 201 |
| `test_r203_04_edicion_por_put_no_cruza` | `PUT /lots/{id}` `{house_id: B}` ⇒ 404; `{house_id: A2}` ⇒ 200 | HEAD: 200 en ajeno |
| `test_r203_05_weight_evaluation_sin_fuga` (control) | lote A con curva propia; `GET /operations/{id}/weight-evaluation` | rangos = curva A (verde) |
| `test_r203_06_alta_legitima_intacta` (control) | alta completa A | 201 (verde) |

Ampliación `test_lot_area_ownership.py`: `test_ga06a_03…05` para galpón/línea/curva.

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r203_lot_reference_tenancy.py tests/test_lot_area_ownership.py` ⇒ 4 rojos exactos + controles; salida a `evidence/red/`.

### 1.1 RED del inventario (§12)

Consulta de solo lectura (no test): `SELECT count(*) FROM lots l JOIN houses h ON … WHERE h.farm_id → farms.company_id != l.company_id;` ídem para `genetic_line_id` (no nulo y `company_id != l.company_id`); registrar en `evidence/inventory.txt`. Esperado en entorno de pruebas: 0/0.

## 2 · Diseño E2E API (C3)

Pila local; dos empresas A/B con geometría completa.

| Caso | Llamadas | Esperado |
|---|---|---|
| R203-RT-01 | POST lote A con `house_id` B | 404; sin fila |
| R203-RT-02 | POST lote A con línea B / línea null | 404 / 201 |
| R203-RT-03 | POST lote A con curva B | rechazo; sin curva |
| R203-RT-04 | PUT lote A a galpón B / a galpón A2 | 404 / 200 |
| R203-RT-05 | weight-evaluation lote A (curva A) | rangos A |
| R203-RT-06 | Alta de lote por UI (local, viewport estándar y 390×844) | 201; 0 fatales |

Artefactos: `evidence/r203/runtime-{red,c3}.json`, captura de UI del alta legítima. Invariantes: 0 `5xx`; conteos de `lots` por empresa verificados.

## 3 · Plan UAT

**No requerida.** Endurecimiento invisible en el flujo legítimo. Verificación informativa si el propietario la pide: RT-01 (referencia ajena rechazada) + RT-06 (alta normal intacta); 5 minutos.
