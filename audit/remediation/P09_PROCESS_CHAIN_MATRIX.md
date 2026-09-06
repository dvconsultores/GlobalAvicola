# `P-09` · AUDITORÍA INTERNA — CADENA COMPLETA

`spec.md §4.11` · `docs/02 §3.11` · 2026-09-06

Se levanta antes de escribir nada, para no repetir el error que `P-10` dejó claro:
**certificar una capacidad no es certificar un proceso**.

---

## 1. Nombre normativo y frontera

`spec.md §4.11` la llama **Internal Audit** — Auditoría Interna. `docs/02 §3.11` la
desarrolla como **Módulo 11**.

No confundir con `P-10`:

| | `P-10` Trazabilidad generacional | `P-09` Auditoría interna |
|---|---|---|
| Qué relaciona | lotes entre generaciones | **acciones con quien las hizo** |
| Pregunta | ¿de dónde vino este lote? | **¿quién hizo esto, cuándo y por qué?** |
| Entidades | `EggBatch` · `ChickBatch` | `AuditLog` |
| Fuente | `§4.9` | `§4.11` |

Son procesos distintos y ninguno sustituye al otro.

## 2. La cadena

| # | Paso | Actor | Acción de negocio | Registro esperado | Verificación | Estado |
|:--:|---|---|---|---|---|:--:|
| 1 | Alta de evento operativo | operador | `POST /operations` | `CREATED`, módulo `operations` | consulta de auditoría del evento | **PASS** |
| 2 | Transición de estado | supervisor · aprobador | envío, revisión, aprobación | `REVIEW_STARTED` `RETURNED` `APPROVED` `REJECTED` | línea de tiempo | **PASS** |
| 3 | Corrección | corrector | `POST /corrections` | `CORRECTED` con valor original y corregido | `§3.11.3` | **PASS** |
| 4 | Envío a SAP | analista SAP | consolidación y envío | `CONSOLIDATED` `SENT_TO_SAP` `SAP_CONFIRMED` `SAP_ERROR` | `§3.11.3` | **PASS** |
| 5 | **Acceso al sistema** | cualquiera | login, logout, login fallido | `LOGIN` `LOGOUT` `LOGIN_FAILED`, módulo `auth` | consulta por módulo | **FAIL** — `R-81` |
| 6 | **Cambio de maestros y lotes** | administrador | alta, edición, baja lógica | `CREATED` `UPDATED` `DELETED`, módulos `masters` · `lots` | ídem | **FAIL** — `R-81` |
| 7 | **Cambio de permisos** | administrador | alta de rol, cambio de permisos | `PERMISSION_CHANGE`, módulo `users` | ídem | **FAIL** — `R-81` |
| 8 | **Importación y exportación** | analista · auditor | importar referencias, exportar informe | `IMPORT` `EXPORT` | ídem | **FAIL** — `R-81` |
| 9 | Cierre de revisión | supervisor | `POST /review/complete` | `REVIEW_COMPLETED` | línea de tiempo | **FAIL** — `R-81` |
| 10 | Inmutabilidad | — | ninguna | ningún `UPDATE` ni `DELETE` sobre `audit_logs` | revisión estructural | **PASS** |
| 11 | Visor para roles autorizados | auditor · administrador | `GET /audit` | solo con permiso `audit:read` | control y tratamiento | **PASS** |
| 12 | **Filtros de la vista** | auditor | filtrar por usuario, lote, fecha, acción, módulo, estado, documento SAP | subconjunto correcto | consulta con dataset distinguible | **FAIL** — `R-82` |
| 13 | Aislamiento entre empresas | auditor de la empresa A | `GET /audit` | ningún registro de la empresa B | control y tratamiento | por verificar |
| 14 | Contenido del registro | — | cualquiera de las anteriores | usuario, acción, fecha, módulo, entidad, antes → después, motivo | `§3.11.1` | por verificar |

```
14 pasos · PASS 6 · FAIL 6 · por verificar 2      ← análisis inicial
14 pasos · PASS 14 · FAIL 0                      ← tras GA-REM-032
```

## 3. Los dos hallazgos y por qué son dos

| | `R-81` | `R-82` |
|---|---|---|
| Qué falla | ocho acciones obligatorias no se escriben nunca | la vista aparenta filtrar y no filtra |
| Causa raíz | **no existe el emisor**: los listeners vigilan tres modelos | **deriva de contrato**: la interfaz envía parámetros que nadie declara |
| Capa | dominio y servicios de negocio | frontend ↔ backend |
| Pasos afectados | 5, 6, 7, 8, 9 | 12 |
| Se arregla | añadiendo emisiones | alineando el contrato con la norma |

Comparten sección normativa (`§3.11`) pero **no causa**. Se registran por separado, como
`§19`–`§21` del encargo exige, y comparten spec porque el criterio de terminado —certificar
`P-09`— es uno solo.

## 4. Lo que ya está bien y no se toca

- La inmutabilidad: `audit_logs` es de solo inserción en toda la aplicación.
- Los doce emisores existentes: son el patrón técnico a seguir, no algo a rehacer.
- Los filtros que el backend declara: **se aplican de verdad**, con recuento coherente.
- El permiso `audit:read` que protege la vista.

## 5. Fuera de alcance

- `CONFIG_CHANGE`: no hay superficie de configuración que auditar.
- `R-80`, `R-76`, `R-77`, `OD-04`, `GA-TD-014`.
- Rediseñar la vista de auditoría más allá de lo que la norma pide.
- Cualquier cambio en `P-10`, cuya trazabilidad es otra cosa.
