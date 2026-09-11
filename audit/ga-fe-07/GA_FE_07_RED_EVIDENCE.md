# GA-FE-07 · EVIDENCIA RED (pre-implementación)

Generación de entrada: backend `69d0c95` + bundle `index-DcqmSs-R.js`. Actor **C2** `ga7.operador` (empresa 1 · rol 57 · BU broiler efectiva). Áreas: **A**=6 «Nave Activa GA-FE-07» (activa) · **X**=7 «Nave Histórica GA-FE-07» (activa → **dada de baja oficialmente** tras crear el lote histórico) · **X2**=8 «Nave Retirada GA-FE-07» (inactiva) · área ajena 5 (empresa 3, activa).

## 1 · RED backend (runtime, capturado)

| Caso | Petición | Resultado observado | Target post-fix |
|---|---|---|---|
| **RED-1 · alta con inactiva** | `POST /lots` `area_id=7` (inactiva propia) | **HTTP 201** · lote 41 `GA7-RED-INACT-01` con `area_id:7` persistido | **400 «Área inactiva»** |
| **RED-2 · edición a inactiva** | `PUT /lots/40` `area_id=7` (lote 40 tenía área A=6) | **HTTP 200** · fresh GET `area_id:7` | **400** + fresh sin cambio |
| **RED-3 · selector** | `/lots/new` como C2 | Opciones con **Nave Histórica (7)** y **Nave Retirada (8)** presentes | Inactivas **ausentes** |

Artefactos: `evidence/red/red1-create-inactive.json` · `red2-update-inactive.json` · `red2-fresh.json` · `selector-red.json` · `selector-red.png`.

## 2 · Controles capturados (deben seguir verdes tras la corrección)

| Control | Resultado pre-fix |
|---|---|
| Histórico: lote 39 `GA7-HIST-01` referencia X inactiva → fresh GET | `area_id:7` legible · PLD `2026-12-01` |
| Update **no relacionado** del histórico (solo `planned_close_date`) | **200** · área permanece 7 · PLD `2026-12-08` |
| Alta sin área (`NULL`) | **201** (`GA7-NULL-01`) |
| Alta con **área ajena activa** (5, empresa 3) | **400** `{"detail":"Área no encontrado","rule":"BR-07"}` |

## 3 · RED de suite (canónico, PG)

`backend/tests/test_lot_area_eligibility.py` — matriz completa (alta/edición/históricos/contratos). Con el código actual: la fila de alta con inactiva espera 400 y recibirá **201** ⇒ **falla** (RED); íd. edición (200). En local sin PostgreSQL la suite queda `skipped` (declarado); corre en CI. Evidencia RED ejecutada = §1 (runtime) — misma doctrina que GA-FE-06/06-A.

## 4 · RED frontend

`frontend/src/pages/lots/__tests__/gaFe07.inactiveAreaEligibility.test.tsx` — con el código actual el selector **incluye** la inactiva ⇒ **falla** (RED); tras el filtro, pasa.
