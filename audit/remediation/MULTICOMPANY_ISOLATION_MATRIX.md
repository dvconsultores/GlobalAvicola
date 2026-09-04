# MULTICOMPANY ISOLATION MATRIX

**Fecha** 2026-09-04 · **Wave** 2.75 · **Origen** `R-48`

`R-48` cambió cómo se resuelve el contexto de compañía. Si el contexto puede desplazarse,
hay que demostrar que **solo** lo desplaza quien tiene derecho y que ningún identificador
ajeno es alcanzable. Esta matriz es esa demostración.

---

## 1. La regla de resolución — una sola

`get_current_user` (`app/auth/security.py`) determina la compañía efectiva:

| Quién | De dónde sale la compañía | Por qué |
|---|---|---|
| Usuario normal | **la base**, siempre | Un token no puede reclamar una compañía ajena. Es la propiedad que sostiene el aislamiento |
| Super Admin | el claim que `switch-company` emitió, si lo hay; si no, la suya | Ya puede operar sobre cualquier compañía: el claim no le concede nada, solo **acota dónde escribe** |

No hay una segunda fuente. El frontend no decide; el token de un usuario normal tampoco.

---

## 2. Por servicio

| Servicio | Fuente del contexto | Filtrado en consulta | Propiedad al crear | Protección entre compañías |
|---|---|---|---|---|
| `MasterService` | `current_user["company_id"]` | `_apply_company_filter` | auto-asigna si llega nulo ⚠ `R-50` | `get_by_id` filtra: un maestro ajeno es 404 |
| `LotService` | ídem | `company_id ==` | `company_id=self.company_id` | delega en `MasterService.get_by_id` |
| `OperationsService` | ídem | `company_id ==` (fail-closed desde `R-36`) | `company_id=self.company_id` | **`R-42` corregido**: el lote referenciado debe ser de la compañía |
| `ReviewService` · `ApprovalService` | ídem | `company_id ==` | hereda del evento | el evento ya está acotado |
| `CorrectionService` | ídem | `company_id ==` | hereda del evento | ídem |
| `AuditService` | ídem | `company_id ==` | — | solo lectura |
| `ReportsService` | ídem | `company_id ==` | — | solo lectura |

---

## 3. `R-42` — el hueco que había

`validate_lot_active` consultaba el lote **sin filtrar por compañía**. Y como
`create_event` fija `company_id = self.company_id` —la de quien pide— nadie comprobaba que
el `lot_id` fuera suyo.

```
Empresa A  →  POST /operations {lot_id: <lote de la empresa B>}  →  201
```

El evento quedaba archivado bajo A pero ligado a un lote de B. Y como
`get_current_bird_balance` calcula por `lot_id` sin filtro de compañía, **el saldo de aves
de B quedaba contaminado por movimientos de A**.

No era una fuga de lectura: los filtros de listado funcionaban. Era una **escritura entre
inquilinos**, que es peor, porque corrompe datos ajenos en lugar de solo mostrarlos.

**Corregido:** `validate_lot_active(db, lot_id, company_id)` filtra, y un lote ajeno se
comporta como inexistente — que es lo que debe parecerle a quien no tiene derecho a verlo.

En la Wave 2 lo clasifiqué como P1 «no filtra por compañía». La clasificación se quedó
corta: no describí el vector de escritura.

---

## 4. Pruebas

`tests/test_multicompany_isolation.py` — **12 PASS**

| Prueba | Verifica |
|---|---|
| La fuente del contexto es una sola | sobre el código: valor por defecto de la base, excepción acotada |
| Un usuario normal no desplaza su contexto | reclama otra compañía en el token; se ignora |
| Un usuario normal no puede cambiar de empresa | 403 |
| El Super Admin no puede situarse en una empresa inexistente | 404 |
| El contexto determina la propiedad | maestro y lote creados pertenecen a la empresa seleccionada |
| El contexto sobrevive a la renovación | `R-54` |
| **IDOR lectura** × 3 | lote, operación y maestro ajenos → 403/404 |
| **IDOR escritura** | modificar un lote ajeno → denegado |
| **IDOR registro** | registrar contra un lote ajeno → denegado (`R-42`) |
| Los listados no filtran de menos | barrido sobre operaciones, lotes y maestros |

---

## 5. Riesgo residual

| ID | Riesgo | Sev. | Estado |
|---|---|---|---|
| `R-50` | `company_id` es fijable desde el cliente en 19 esquemas de maestros; `MasterService.create` solo lo impone cuando llega nulo | P2 | **mitigado por RBAC**: `masters:create` es exclusivo del Super Admin, que está facultado para operar entre compañías. **Debe resolverse antes de crear cualquier rol administrativo intermedio** (`OD-04`) |

Ningún otro servicio permite fijar la compañía desde el cliente.
