# GA-FE-06-A · EVIDENCIA RED (pre-implementación)

Generación de entrada: backend desplegado desde `23ca59a` + bundle `index-DcqmSs-R.js` (sin cambios de frontera). Actor **F** `ga6a.operador` (empresa 1 · rol 54 · BU `broiler` efectiva) por **API oficial**.

## 1 · RED runtime (ejecutado y capturado)

Datos crudos: `evidence/red/runtime-red.json` (+ cuerpos individuales).

| Caso | Petición | Resultado observado | Lectura |
|---|---|---|---|
| **Alta con área ajena** | `POST /api/v1/lots` `area_id=5` (área de la empresa 3) | **HTTP 201** · lote `GA6A-RED-FOREIGN-…` con `area_id: 5` persistido | El defecto: la relación ilegal se crea y se guarda |
| Alta control (área propia) | `POST` `area_id=4` (empresa 1) | 201 | Camino legítimo funcionando (control) |
| **Edición con área ajena** | `PUT /api/v1/lots/27` `area_id=5` | **HTTP 200** · fresh GET con `area_id: 5` | El defecto también en la edición |
| Edición control (restaurar 4) | `PUT` `area_id=4` | 200 | La edición funciona (control) |
| **Área inexistente** | `POST` `area_id=999999` | **HTTP 500** (cuerpo no-JSON) | Sin validación, el FK revienta en el flush — tampoco fail-closed |

Los lotes RED de esta corrida quedan en el ledger de GA-FE-06-A (retenidos como evidencia).

## 2 · RED de suite (canónico, PG)

`backend/tests/test_lot_area_ownership.py` — escrito contra el contrato **posterior** a la corrección:

- Con el código actual: `test_ga06a_01` falla en `assert r.status_code == 400` (recibe **201**); `test_ga06a_02` falla (el `PUT` responde **200** y muta); `test_ga06a_05` falla (recibe **500**).
- En local sin PostgreSQL la suite completa queda `skipped` (igual que el resto de lotes — declarado); se ejecuta en CI y será el gate de regresión permanente.

La combinación —evidencia runtime ejecutada hoy + suite canónica escrita— es la misma doctrina de RED usada en GA-FE-06 (§RED) y se declara aquí tal cual, sin forzar un entorno PG inexistente en la máquina del agente.
