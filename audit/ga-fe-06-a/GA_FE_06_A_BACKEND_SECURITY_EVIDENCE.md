# GA-FE-06-A · EVIDENCIA DE SEGURIDAD DE BACKEND

## 1 · Cambio implementado (C6 `69d0c95`)

Único archivo de producto: `backend/app/lots/service.py` (+24 líneas). Cero migración · cero permiso · cero endpoint · SLA intacto · frontend intacto (0 cambios de producto).

| Endpoint | Ruta | Método | Esquema | Servicio | Validador | Contexto de inquilino | Resultado de contrato |
|---|---|---|---|---|---|---|---|
| Alta | `/api/v1/lots` | POST | `LotCreate` (`area_id: int?`) | `LotsService.create_lot` | `tenancy.verificar_catalogo_de_empresa(db, Area, area_id, self.company_id, "Área")` **antes de `db.add`** | empresa efectiva del actor (`self.company_id`) | `400 {"detail":"Área no encontrado","rule":"BR-07"}` |
| Edición | `/api/v1/lots/{id}` | PUT | `LotUpdate` (`area_id: int?`, `extra=forbid`) | `LotsService.update_lot` → `MasterService.update` | íd. **antes de `MasterService.update`** (sin `setattr`/`flush`/auditoría previos) | íd. (el lote ya se resuelve con `404` por unidad) | íd. |

Semántica del validador (ya existente, `R-179`): `company_id` nulo = **catálogo compartido** (aceptado); fijado = debe coincidir con la empresa efectiva; el ajeno **se comporta como inexistente**; sin empresa efectiva ⇒ **fail-closed** (`R-139`). No se añadió regla de granja/BU/activa — el área es un catálogo **por empresa** y nada más.

## 2 · Seguridad transaccional (§17)

- Alta: la guarda corre antes de construir/`add` el `Lot` ⇒ negación = **ningún INSERT**, sin auditoría.
- Edición: la guarda corre antes de `MasterService.update` ⇒ negación = **ningún `setattr`, sin `flush`, sin auditoría**; no hay mutación parcial que revertir.
- Verificado en runtime por fresh GET (el área permanece) y por auditoría (0 éxitos para los intentos ajenos).

## 3 · Gates locales (declarados)

| Gate | Resultado |
|---|---|
| `python -m py_compile app/lots/service.py` | OK |
| `tests/test_lot_area_ownership.py` + `test_lot_planned_close.py` + `test_areas.py` (local) | **24 skipped** — requieren PostgreSQL (mismo comportamiento que toda la familia de lotes; corren en CI) |
| Gate PG-libre (`test_od16_global_read_boundary` + `test_migration_bu_catalog`, filtro canónico) | **7 passed** |
| Vitest completo | **278/278** (36 archivos) |
| `npx tsc -b --noEmit` | **0 errores** |
| `npm run build` | **PASS** |

## 4 · Anti-enumeración (comprobado)

La denegación es idéntica para «no existe» (999999) y «es de otra empresa» (Área X): `400 {"detail":"Área no encontrado","rule":"BR-07"}` — sin nombrar empresas, sin distinguir los dos casos, sin metadatos del inquilino (la suite canónica `_assert_negativa_propia` verifica además la ausencia de «empresa/company/ajena» en el cuerpo).
