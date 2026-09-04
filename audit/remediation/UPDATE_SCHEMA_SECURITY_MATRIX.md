# UPDATE SCHEMA SECURITY MATRIX

**Fecha** 2026-09-04 · **Wave** 2.5 · **Origen** `R-32` · **Método** introspección de los
49 esquemas de escritura (`*Create`, `*Update`, `*Patch`) de la aplicación

---

## 1. Por qué esta auditoría

`R-32` permitía aprobar cualquier evento con un `PUT`: `OperationalEventUpdate` declaraba
`status` y el servicio lo aplicaba con `setattr`. Se corrigió en la Wave 2, pero un defecto
así rara vez es único. Aquí se comprueba, esquema por esquema, si algún otro contrato de
escritura expone campos que el usuario no debería poder fijar.

---

## 2. Clasificación de campos sensibles

| Clasificación | Significado | Campos |
|---|---|---|
| `WORKFLOW_MANAGED` | Solo cambian por transiciones del flujo | `status`, `approved_by_id`, `reviewed_by_id` |
| `SYSTEM_MANAGED` | Los fija el servidor | `id`, `version`, `created_at`, `updated_at`, `registered_by_id`, `hashed_password` |
| `ADMIN_ONLY` | Requieren permiso administrativo | `company_id`, `role_id`, `is_active` |
| `IMMUTABLE` | No cambian tras la creación | `event_type`, `idempotency_key` |
| `USER_EDITABLE` | El usuario los aporta legítimamente | el resto |

---

## 3. Resultado

```
Esquemas de escritura analizados ............... 49
Que exponen algún campo sensible ............... 34
De ellos, con exposición INDEBIDA ..............  1   (R-50)
`WORKFLOW_MANAGED` expuesto en algún esquema ...  0   ← la clase de R-32 está cerrada
`SYSTEM_MANAGED` expuesto en algún esquema .....  0
Contraseñas expuestas en esquemas de edición ...  0   ← P0-13 cerrado por contrato
```

### 3.1 · Lo que ya no aparece en ninguna parte

| Campo | Antes | Ahora |
|---|---|---|
| `status` | `OperationalEventUpdate` (`R-32`) | **ningún esquema** |
| `approved_by_id`, `reviewed_by_id` | — | ningún esquema |
| `registered_by_id`, `version`, `id` | — | ningún esquema |
| `password` en edición de usuario | `UsersPage` lo enviaba y se descartaba (`P0-13`) | `UserUpdate` con `extra="forbid"`: **rechaza con 422** |

---

## 4. Matriz por esquema

| Schema | `extra` | Campos sensibles | Clasificación | Veredicto |
|---|---|---|---|---|
| `operations.OperationalEventUpdate` | **`forbid`** | `sap_document_ref` | `USER_EDITABLE` — es la referencia al documento SAP que el operador aporta (`BR-10`) | ✅ correcto |
| `operations.OperationalEventCreate` | `ignore` | `event_type`, `idempotency_key`, `sap_document_ref` | los dos primeros son `IMMUTABLE` **tras** la creación; fijarlos al crear es su propósito | ✅ correcto |
| `review.ApprovalStepCreate` / `Update` | `ignore` | `role_id` | `ADMIN_ONLY` — designar qué rol aprueba es el objeto del endpoint; exige `review:create/update`, exclusivo del Super Admin | ✅ correcto |
| 12 × `masters.*Update` | `ignore` | `is_active` | `ADMIN_ONLY` — activar y desactivar maestros es una operación administrativa normal; exige `masters:update` | ✅ correcto |
| **19 × `masters.*Create` / `*Update`** | `ignore` | **`company_id`** | `ADMIN_ONLY` | ⚠ **`R-50`** |
| Los 15 restantes | `ignore` | ninguno | — | ✅ correcto |

---

## 5. `R-50` — la compañía se puede fijar desde el cliente

`MasterService.create` (`app/masters/service.py:100-113`) solo asigna la compañía **cuando
el cliente no la envía**:

```python
if item_data["company_id"] is None and self.user_company_id:
    item_data["company_id"] = self.user_company_id
```

Si el cliente **sí** la envía, se respeta tal cual. Y `update` (`:115-123`) hace un
`setattr` sobre todo lo recibido, de modo que un maestro podría **cambiar de compañía**.

### Exposición real hoy

| Vector | Estado |
|---|---|
| `create` con `company_id` ajeno | requiere `masters:create`, **exclusivo del Super Admin**, que está facultado para operar sobre cualquier compañía |
| `update` con `company_id` ajeno | además, `get_by_id` aplica el filtro de compañía (`:89`), de modo que un usuario no puede ni siquiera recuperar un maestro ajeno para modificarlo |

**No es explotable por ningún rol que no sea Super Admin**, precisamente porque el RBAC de
la Wave 2 dejó esas rutas en sus manos. Pero es un defecto latente: el día que exista un
rol administrativo por debajo del Super Admin (`OD-04`), se convierte en una escritura
entre inquilinos.

### Disposición

**P2 · no se corrige en esta Wave.** Corregirlo es cambiar el contrato de 19 esquemas y el
servicio de maestros, y la Wave 2.5 es de compatibilidad, no de funcionalidad. Se traza a
**`GA-REM-019`** con una condición explícita: **debe resolverse antes de crear cualquier rol
administrativo por debajo del Super Admin**.

No es un bloqueante de publicación: el estado actual es seguro con el catálogo de roles
vigente.

---

## 6. Hallazgos

| ID | Hallazgo | Sev. | Destino |
|---|---|---|---|
| `R-50` | `company_id` es fijable desde el cliente en 19 esquemas de maestros; `MasterService` solo lo impone cuando llega nulo | P2 (mitigado por RBAC) | `GA-REM-019` — **prerrequisito de `OD-04`** |

**Cero hallazgos de la clase de `R-32`.** Ningún esquema de escritura expone campos
gestionados por el flujo o por el sistema.
