# MULTITENANT WRITE ISOLATION MATRIX

**Fecha** 2026-09-04 · **Wave** 3 · Gate obligatorio previo a la certificación de procesos

```
LIST FILTERING  DOES NOT GUARANTEE  TENANT DATA INTEGRITY
```

`R-42` lo demostró en producción de la peor manera posible: los filtros de listado
funcionaban y la escritura no comprobaba nada. Este gate audita la escritura.

---

## 1. Modelo del defecto

```
USUARIO EMPRESA A
  → payload lot_id = LOTE DE LA EMPRESA B
  → event.company_id = A
  → event.lot_id     = B
  → operación persistida
  → el saldo se calcula por lot_id
  → SALDO DE LA EMPRESA B CONTAMINADO
```

No es una fuga de lectura. Es una **violación de integridad por escritura entre
inquilinos**, y es peor: corrompe datos ajenos en lugar de solo mostrarlos.

---

## 2. Alcance auditado

```
Endpoints que mutan estado (POST/PUT/PATCH/DELETE) ...... 90
Claves foráneas enviables por el cliente ................ 26
De ellas, tenant-scoped ................................. 22
Que exigen pertenencia según la clasificación ...........  6
```

Descubiertas por introspección de los esquemas Pydantic cruzada con las claves foráneas de
SQLAlchemy — no por lectura ni por lista escrita a mano, que es exactamente como `R-42`
sobrevivió a la Wave 2.

---

## 3. Matriz

| Endpoint | Mutation | Resource | FK | FK Scope | Ownership Validated | Cross-Tenant Test | Result |
|---|---|---|---|---|---|---|---|
| `POST /operations` | crear evento | `operational_events` | `lot_id` | `TENANT_SCOPED` | ✅ `R-42` (Wave 2) | ✅ | **PASS** |
| `POST /operations` | ídem | ídem | `farm_id` | `TENANT_SCOPED` | ✅ **Wave 3** | ✅ | **PASS** |
| `POST /operations` | ídem | ídem | `house_id` | `TENANT_SCOPED` vía granja | ✅ **Wave 3** | ✅ | **PASS** |
| `POST /operations` | ídem | ídem | `destination_farm_id` | `TENANT_SCOPED` | ✅ **Wave 3** | — | protegido |
| `POST /corrections` | corregir | `correction_logs` | `event_id` | `TENANT_SCOPED` | ✅ servicio | ✅ | **PASS** |
| `POST /review/start/{id}` | revisar | evento | `event_id` | `TENANT_SCOPED` | ✅ servicio | ✅ | **PASS** |
| `POST /approvals/approve` | aprobar | evento | `event_id` | `TENANT_SCOPED` | ✅ servicio | ✅ | **PASS** |
| `POST /masters/houses` | crear galpón | `houses` | `farm_id` | `TENANT_SCOPED` | ✅ **Wave 3** (`R-59`) | ✅ | **PASS** |
| `PUT /masters/{...}` | mover maestro | maestros | `farm_id`, `hatchery_id` | `TENANT_SCOPED` | ✅ **Wave 3** | — | protegido |
| `POST /lots` | crear lote | `lots` | `farm_id` | `TENANT_SCOPED` | ✅ vía `MasterService` | ✅ | **PASS** |
| `POST /lots/egg-batches` | enlazar | `egg_batches` | `source_lot_id`, `hatchery_lot_id` | `TENANT_SCOPED` | ❌ | — | ⚠ `R-60` |
| `POST /lots/chick-batches` | enlazar | `chick_batches` | `hatchery_lot_id`, `destination_lot_id`, `egg_batch_id` | `TENANT_SCOPED` | ❌ | — | ⚠ `R-60` |
| `POST /operations` | ídem | ídem | catálogos (`cause_id`, `vaccine_id`…) | compartible | n/a por diseño | — | por diseño |

---

## 4. Lo que el gate encontró

`R-42` había resuelto **una** clave foránea. La lección no se había extendido:

```
POST /operations {farm_id:  <granja de la empresa B>}    -> 201   ← aceptado
POST /operations {house_id: <galpón de la empresa B>}    -> 201   ← aceptado
POST /masters/houses {farm_id: <granja de la empresa B>} -> 201   ← aceptado
```

Tres escrituras entre inquilinos que la certificación de la Wave 2 no vio porque `AC05` se
había verificado sobre **lecturas**.

Corregido bajo `GA-REM-002 AC10`, activada formalmente desde `GA-REM-016`. La comprobación
vive en `app/tenancy.py`, en un único sitio: una regla de aislamiento aplicada en un sitio
y ausente en otro no es una regla, es una casualidad.

---

## 5. Pruebas

`backend/tests/security/test_multitenant_isolation.py` — **12 PASS**

| Prueba | Verifica |
|---|---|
| Inyección de `lot_id`, `farm_id`, `house_id` ajenos | los tres rechazados |
| Corregir, revisar y aprobar un evento ajeno | los tres rechazados |
| Crear un galpón bajo una granja ajena | rechazado (`R-59`) |
| **El saldo del lote ajeno no se contamina** | medido antes y después: intacto |
| **Un rechazo no deja rastro** | ni fila, ni auditoría |
| Lectura de lote, evento y maestro ajenos | 403/404 |

El penúltimo es el que importa: **no basta con el código HTTP**. Se comprueba que no se
creó fila y que no se escribió auditoría, porque un rechazo que deja rastro sigue siendo
una escritura.

---

## 6. Datos derivados

`R-42` demostró que una relación incorrecta contamina cálculos. El gate mide el saldo de
aves del lote ajeno antes y después del intento: **no cambia**.

Los demás derivados —huevos, alimento, KPI, informes— se calculan sobre eventos, y el
evento ya no puede referenciar un lote ajeno. La protección es de origen, no por
enumeración de cada cálculo.

---

## 7. Hallazgos

| ID | Hallazgo | Sev. | Estado |
|---|---|---|---|
| `R-59` | Un maestro hijo admitía un padre de otra empresa (`houses.farm_id`) | P1 | **corregido** |
| `R-60` | Las claves de trazabilidad no comprueban pertenencia | P2 | abierto → `GA-REM-008`; solo alcanzable por Super Admin |
