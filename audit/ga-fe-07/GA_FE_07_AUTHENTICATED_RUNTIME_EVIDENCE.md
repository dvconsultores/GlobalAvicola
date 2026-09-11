# GA-FE-07 · EVIDENCIA RUNTIME AUTENTICADO (E2E-01…12)

Generación congelada: frontend **`index-BUthrUt9.js`** (LM 2026-09-11 15:46:08 GMT · ETag `"6aa42240-13cfdb"`) + backend **`5a5bb3f`** (despliegue observado: 201/201 → 502 → **400 «Área inactiva»**). Actor **C2** `ga7.operador`. Corrida **autocontenida con sufijo único** (`155019ujgc`), crudo en `evidence/green/runtime-green.json`.

## Matriz de resultados

| E2E | Caso | Resultado |
|---|---|---|
| 01 | Alta activa (área 11) | **PASS** — 201 · lote 49 · fresh `area_id:11` · PLD `2026-11-11T00:00:00Z` exacta |
| 02 | Selector inactivas ausentes (desktop/móvil) | **PASS** — activas presentes; H(12)/retirada(8)/históricas anteriores ausentes; sin IDs crudos |
| 03 | Alta directa con inactiva | **PASS (DENY)** — 400 «Área inactiva»/BR-07 · **persistencia 0** (búsqueda) · auditoría de éxito **0** |
| 04 | Edición activa→inactiva | **PASS (DENY)** — 400 · fresh conserva área 11 |
| 05 | Histórica preservada | **PASS** — lote 48 legible con `area_id:12` (inactiva) |
| 06 | Update no relacionado del histórico | **PASS** — 200 · área 12 intacta |
| 07 | Histórica→activa | **PASS** — 200 · fresh área 11 |
| 08 | Inactiva→inactiva | **PASS (DENY)** — 400 «Área inactiva» · fresh 12 |
| 09 | Mismo id inactivo explícito | **PASS** — 200 · área 12 (sin falsa invalidación) |
| 10 | Área ajena (activa, empresa 3) | **PASS (DENY)** — alta 400 «Área no encontrado» · edición 400 · fresh sin cambio |
| 11 | NULL | **PASS** — 201 · `area_id:null` |
| 12 | Carrera de baja | **PASS** — seleccionada el área activa y dada de baja antes de enviar ⇒ 400 «Área inactiva» · error visible · persistencia 0 |

## Regresiones en la misma corrida

| Sujeto | Resultado |
|---|---|
| Auditoría | activa: 1 entrada de creación; intento inactivo: **0** |
| Masters admin | área inactiva **visible** en el listado administrativo (control-plane intacto) |
| BU OFF (C2) | 403 «sin acceso operativo…» |
| Global + BU OFF | 403 «sin empresa efectiva…» |
| Usuario rol sin concesión | 403 |
| RBAC sin `lots:create` | 403 «Permiso requerido» |
| Consola desktop | 1 entrada — **la denegación esperada de la carrera** (`400`), no fatal; 0 errores propios |
| Móvil | selector con activas; inactivas ausentes |

## Declaraciones de alcance

- **SLA**: `planned_close_date` exacta en fresh GET (E2E-01); suite canónica (`test_lot_planned_close.py`) **sin cambios** (skipped local / CI); escáner horario no forzado — sin regresión de lógica.
- **GA-FE-05** (submit/resubmit): superficie **no tocada** (diff aislado a lots/tenancy/LotForm); muestra representativa cubierta por la suite vitest (incluye `gaFe05.submitGates`), 280/280.
- **R-182**: permanece CLOSED_OWNER_ACCEPTED (tenencia, PLD, SLA fuente intactos; verificado por E2E-01/10).
- **R-184 / OBS-UAT-01 / BU-D10**: sin cambio.
