# GA-R153 · LEDGER DE DATOS DE PRUEBA (runtime)

Fecha: 2026-09-12 · Empresa 1 · runtime producción `avicola.globaldv.net`. Los actores sintéticos quedaron **dados de baja** y las concesiones **revocadas**; el catálogo volvió a **4×OFF**. Los datos de negocio siguientes **se conservan** (no hay borrado de eventos/lotes en el producto) y quedan etiquetados:

## 1 · Lotes

| Lote | Origen | Estado | Nota |
|---|---|---|---|
| `L-GP-2026-01`, `L-GP-2026-06` | **preexistentes** (antes de esta tranche; no creados por GA-R153) | active | observados en el preflight; la secuencia partió de ellos (07) |
| `L-GP-2026-07` (id 60) | corrida E2E intermedia (evento 85) | active | aprobación válida; sin recepción aprobada |
| `L-GP-2026-08` (id 61) | corrida E2E intermedia (evento 86) | active | recepción 87 registrada sin aprobar; mortalidad 1 y 9 aprobadas (global 10 consumido) |
| `L-GP-2026-09` (id 62) | **corrida final** (evento 88) | active | recepción 89 aprobada (10) − mortalidad 2 (95) |
| `E2E-MAN-153-{semilla}` (id 63) | manual (E2E-17) | active | usada por el import legado 90 |

## 2 · Eventos

| Ids | Tipo | Estado final |
|---|---|---|
| 79, 81–84, 91 | importaciones de sondas/E2E | **cancelled** (limpieza) |
| 85, 86, 88 | importaciones aprobadas (E2E) | approved (crearon 60/61/62) |
| 90 | importación legada con lote | approved (lote 63, sin lote nuevo) |
| 87 | recepción de sonda (lote 61) | **registered** — cancelación rechazada: «dejaría el saldo… (R-130)»; se conserva |
| 89 | recepción E2E (lote 62) | approved |
| 94, 95, 96 | mortalidad (brackets de saldo) | approved |
| 97 | mortalidad x9 (lote 61) | approved |

## 3 · Higiene

- Usuarios `e2e-r153-*` (21): baja lógica 204. Roles `e2e-r153-*` (29): `is_active=false`. Concesiones: revocadas (200) antes de la baja.
- Catálogo de unidades: `{breeder: false, broiler: false, grandparent: false, hatchery: false}` (verificado).
- Incidencia de roles legítimos: desactivados por el `search` ignorado de `/roles` → **reactivados y verificados** (ver evidencia runtime §3).
- Suites y sondas reutilizaron maestros existentes (supplier 1, transport 1, farm 1, house 1); no se crearon maestros nuevos.
