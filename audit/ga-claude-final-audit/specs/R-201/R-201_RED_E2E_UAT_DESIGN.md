# R-201 · DISEÑO DE PRUEBAS RED · E2E API · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED (integración backend)

Fichero nuevo: `backend/tests/test_r201_sap_no_context.py` (patrón `test_sap_transversal.py`; PG de pruebas; dos empresas A/B con referencias y payloads sembrados; tres identidades: global sin contexto, global situada en A, actor de empresa A).

| Nombre exacto del test | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r201_01_referencias_sin_contexto_es_vacio` | 2 `SapReference` en A + 1 en B; `GET /sap/references` como global sin contexto | `r.json()["references"] == []` — HEAD: devuelve las 3 |
| `test_r201_02_payloads_sin_contexto_es_vacio` | `SapPayload` en A/B; GET jobs/consolidated/errors/payloads | `[]` en las cuatro — HEAD: filas |
| `test_r201_03_consolidate_sin_contexto_no_lee` | evento `APPROVED` en A; POST `/sap/consolidate` como global sin contexto | `status in (400,403,409)` **y** el evento sigue `approved` — HEAD: transiciona o lee y luego falla |
| `test_r201_04_retry_sin_contexto_no_reenvia` | payload `FAILED` en A/B; POST `/sap/retry` sin contexto | 4xx **y** `retry_count` y estado sin cambio en ambos — HEAD: reenvía |
| `test_r201_05_global_situada_opera_su_empresa` | global + `switch-company` A; mismas operaciones | Referencias solo A; consolidate/export operan A (control) |
| `test_r201_06_actor_de_empresa_intacto` | actor A; flujo estándar | Igual que hoy (control) |

Ampliación de `test_sap_transversal.py`: `test_ac_sap02b_global_sin_contexto_no_ve_otra_empresa` (rojo en HEAD).

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r201_sap_no_context.py tests/test_sap_transversal.py` ⇒ 4 rojos exactos + controles verdes; salida a `evidence/red/`.

## 2 · Diseño E2E API (C3)

Pila local (o entorno de pruebas con el mismo backend). Actores: global sin contexto (bootstrap), global situada, actor de empresa. Datos: A con 2 referencias + 1 payload `FAILED`; B con 1+1.

| Caso | Llamadas | Esperado |
|---|---|---|
| R201-RT-01 | GET references/jobs/consolidated/errors/payloads (sin contexto) | `[]` ×5 |
| R201-RT-02 | POST consolidate/export/retry (sin contexto) | 4xx de contexto; contadores de estado sin cambio |
| R201-RT-03 | switch-company A; GET ×5 | solo A |
| R201-RT-04 | consolidate/export como global situada | opera A; B intacta |
| R201-RT-05 | actor de empresa A | comportamiento de hoy |
| R201-RT-06 | actor A intenta retry de payload B por API directa | denegado (referencia inexistente para su empresa) |

Artefactos: `evidence/r201/runtime-{red,c3}.json` (por caso: request, status, diff de estados). Invariantes del run: 0 `5xx`; contadores de `retry_count` verificados antes/después.

## 3 · Plan UAT

**No requerida** (superficie técnica; sin cambio visible para usuarios de empresa). Si el propietario pide verificación: mostrar RT-01/02 (global sin contexto no ve nada) y RT-03 (situada opera su empresa); 5 minutos, informativo.
