# GA-R153 · EVIDENCIA DE CONTRATO DE RED (runtime)

Fecha: 2026-09-12 · Runtime `https://avicola.globaldv.net` · empresa 1 · BU `grandparent` ON solo durante el ejercicio.

| # | Método y ruta | Cuerpo (extracto) | Resultado |
|---|---|---|---|
| 1 | `PATCH /api/v1/business-units/grandparent/enable` | — | 200 (catalogo 4×OFF → gp ON) |
| 2 | `POST /api/v1/operations` | `grandparent_import` **sin lot_id**, plan `arrival=HOY`, ♂40/♀60, OC/transporte/proveedor | **201**, `lot_id: null` |
| 3 | `GET /api/v1/operations/{id}` (operador) | — | 200, `lot_id: null` |
| 4 | `GET /api/v1/lots?search=L-GP` | — | 200, sin lote nuevo |
| 5 | `POST /api/v1/operations/{id}/submit` → `POST /api/v1/review/start/{id}` → `POST /api/v1/review/complete` → `POST /api/v1/approvals/approve` | — | 200×4 (`approve` explícito: niveles > 1 en empresa 1) |
| 6 | `GET /api/v1/operations/{id}` | — | 200, `lot_id: 62` |
| 7 | `GET /api/v1/lots/62` | — | 200 `L-GP-2026-09` · grandparent · mixed · active · `start_date=2026-09-12` · granja 1 |
| 8 | `POST /api/v1/operations` `bird_reception` | `lot_id=62`, granja/galpón, ♀10 (**sin totales** — los totales son del contrato de reproductoras) | 201 |
| 9 | cadena P-07 de la recepción | — | 200×4 → población +10 |
| 10 | `POST /api/v1/operations` `mortality_recording` x9 (lote 61) | — | aprobada 200 (saldo 9) |
| 11 | `POST /api/v1/operations` `mortality_recording` x10 (lote 61) | — | **400 BR-01** (el import no aportó población — ver invariante) |
| 12 | `POST /api/v1/operations` `grandparent_import` con `lot_id` manual | OC-02 | 201 + cadena P-07 → **no** crea segundo lote |
| 13 | `POST /api/v1/operations` importación sin concesión (actor negativo) | — | **403** «sin acceso operativo a la unidad 'grandparent'» |
| 14 | `POST /api/v1/operations/{id}/cancel` (limpieza) | — | 200 · 6 eventos; 1 rechazo legítimo por saldo (evento 87, se deja registrado) |
| 15 | `DELETE /users/{id}/business-units/grandparent` ×8 y `DELETE /users/{id}` ×21 | — | 200/204 |
| 16 | `PATCH /api/v1/business-units/grandparent/disable` | — | 200 → catálogo restaurado **4×OFF** |

Sin `idempotency_key` en los registros; sin endpoints nuevos; la creación del lote **no** emite llamada adicional (ocurre dentro de la transacción de aprobación).
