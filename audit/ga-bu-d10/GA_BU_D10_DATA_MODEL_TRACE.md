# GA-BU-D10 · TRAZA DEL MODELO DE DATOS

Fuente: `backend/app/business_units/models.py` (+ migraciones `p6q7r8s9t0u1`, `q7r8s9t0u1v2`).

## 1 · Las tres tablas (fundamento GA-REM-040 §6)

```
business_units           qué unidades existen EN EL PRODUCTO (catálogo; 4 filas; sin CRUD de cliente)
company_business_units   cuáles tiene HABILITADAS una empresa       (decisión comercial)
user_business_units      cuáles se le han CONCEDIDO a un usuario    (decisión operativa)
```

## 2 · `business_units` (catálogo de plataforma)

| Campo | Tipo | Nota |
|---|---|---|
| `id` | PK int | |
| `code` | str(30) único, indexado | `grandparent · breeder · broiler · hatchery` |
| `name_key` | str(100) | clave i18n |
| `bird_type` | str(20) nullable | correspondencia, **no** autoridad |
| `is_active` | bool | disponibilidad de plataforma; retirar ≠ borrar historia |
| `created_at` | tz datetime | |

## 3 · `company_business_units` (habilitación por empresa)

| Campo | Tipo | Nota |
|---|---|---|
| `id` | PK int | |
| `company_id` | FK companies, indexado | |
| `business_unit_id` | FK business_units, indexado | |
| `is_enabled` | bool | **campo, no ausencia de fila**: «apagada explícitamente» ≠ «nunca configurada»; apagar es distinguible y deshacible |
| `created_at` / `updated_at` | tz datetime | `updated_at` con `onupdate` ⇒ **el modelo ya conserva cuándo cambió el estado** |
| unique | | `uq_company_business_unit (company_id, business_unit_id)` |

**Nada más.** Apagar/encender **solo** toca `is_enabled` (+ `updated_at`). No hay columnas de ciclo, ni borrados, ni cascadas.

## 4 · `user_business_units` (concesión usuario↔empresa)

| Campo | Tipo | Nota |
|---|---|---|
| `id` | PK int | |
| `user_id` | FK users, indexado | |
| `company_business_unit_id` | FK **company_business_units**, indexado | la concesión es «dentro de UNA empresa» (OD-09.d): dice de quién viene |

**La concesión NO apunta al catálogo**, apunta a la **habilitación de una empresa concreta**: una concesión no dice «puede ver reproductora», dice «la empresa A le concedió reproductora **dentro de A**». Ese detalle es de `OD-09.d` y es lo que hace que una concesión de una empresa anterior exista sin ser efectiva.
| `created_at` | tz datetime | cuándo se otorgó |
| `revoked_at` | tz datetime nullable | **cuándo dejó de valer** (OD-09.e: se **marca**, no se borra) |
| índice único | | `uq_user_company_business_unit (user_id, company_business_unit_id) unique WHERE revoked_at IS NULL` ⇒ **única entre las VIVAS**; revocar permite volver a otorgar |

`esta_viva = (revoked_at is None)`.

## 5 · Semántica de borrado / historial

- **No hay borrado de concesiones en ningún camino**: `revocar_unidad` y `revocar_concesiones` marcan `revoked_at` (fecha). La fila queda auditable con «quién tuvo qué y hasta cuándo» (AC-B11).
- **Sin cascadas**: la transferencia de empresa **no borra**; marca (OD-09.e) — «si se borrara, volvió-a-A sería indistinguible de nunca-salió».
- **Auditoría** (no en estas tablas): concesión/revocación ⇒ `AuditLog` `PERMISSION_CHANGE` (users) con `target_user_id` + `business_unit`, `previous_state`/`new_state`; habilitación de empresa ⇒ `CONFIG_CHANGE` (config) con `previous_state`/`new_state` de `is_enabled`. Ambos extremos del ciclo BU-D10 quedan auditados.

## 6 · ¿Puede el modelo representar elegir A o B sin migración? (§25)

| Política | Representación |
|---|---|
| **A (vigente)** | Ya representada: la concesión vive; `is_enabled` modula efectividad; re-encender restaura. **Cero cambios de esquema.** |
| **B (re-autorización)** | «La concesión terminó para este ciclo de habilitación» es representable **con las columnas actuales** — p. ej. marcar `revoked_at` al apagar (o una regla de ciclo derivada de `company_business_units.updated_at` vs la concesión). No exige columnas nuevas ni migración de datos; el **mecanismo exacto se fija en la SPEC post-decisión** (cambia `AC-A04`/`AC-A06` provisionales y sus pruebas). |

**Sin migración destructiva en ningún caso**: las filas históricas se conservan; ningún escenario borra concesiones masivamente.

## 7 · Restricciones de integridad relevantes

- `uq_company_business_unit`: una sola fila (empresa, unidad) ⇒ «habilitada» no depende de cuál fila se lea.
- Único-entre-vivas en concesiones: revocar y volver a conceder = fila nueva (historia completa de otorgamientos).
- FKs sin cascada ⇒ imposible perder historia por borrado en cascada.
