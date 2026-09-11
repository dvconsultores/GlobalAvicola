# GA-FE-07 · TRAZA DE CICLO DE VIDA DEL ÁREA

Lectura directa del código en `69d0c95` (backend) y `23ca59a` (frontend). Sin supuestos.

## Campos y mecanismo

| Elemento | Verdad verificada |
|---|---|
| Campo canónico de estado | `Area.is_active: bool` (default true) — **no** hay `deleted_at` ni `status` |
| Alta | `POST /masters/areas` (`AreaCreate`: name/code/description/company_id) → `is_active` nace `true` |
| Edición | `PUT /masters/areas/{id}` (`AreaUpdate` incluye `is_active`) — «Sin borrado: un área con usuarios, lotes o avisos históricos se da de baja» (docstring) |
| **Baja lógica oficial** | `DELETE /masters/areas/{id}` → `MasterService.deactivate` → `is_active=False` + auditoría (`AuditAction.DELETED`); la fila **permanece** |
| UI de administración | `MasterListPage` ejecuta `api.delete('/masters/{entity}/{id}')` con confirmación («¿Eliminar registro?») — mismo mecanismo canónico |
| Listado (`GET /masters/areas`) | `register_crud` sin filtro de estado (solo `skip/limit/search`; `X-Total-Count`); **devuelve también inactivas**; `AreaRead` **incluye** `is_active` |
| Área compartida | `company_id` nulo = global (R-179); fijo = de empresa |
| Consumidores de estado | **Ninguno** hasta hoy: validadores de tenencia ignora `is_active`; `LotForm` consulta el listado completo y no filtra; el detalle de lote no muestra área (decisión aceptada) |

## Qué cambió GA-FE-06-A (y qué no)

- Añadió validación de **pertenencia** (`verificar_catalogo_de_empresa`) en alta y edición del lote. **No** añadió regla de estado (explícitamente declarado «no se inventa» en su §29).
- Su matriz runtime probó: área ajena DENY; inexistente BR-07; **área propia inactiva: sin regla** (comportamiento indefinido hasta OD-21).

## Consecuencia para GA-FE-07

El estado existe, es consultable (respuesta del listado incluye `is_active`) y la baja es oficial vía `DELETE`. Falta exclusivamente la **elegibilidad para referencia nueva** — objeto de esta tranche, sin cambios al ciclo de vida en sí.
