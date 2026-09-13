# R-219 · FINDING + SPEC (COMPACTO) — `AuditPage` LEE CAMPOS INEXISTENTES (`user_name/old_value/new_value`)

| Campo | Valor |
|---|---|
| **ID** | **R-219** · P2 · **no bloquea** · Estado `SPEC_READY` |
| **Origen** | C#11 (informe C); E §3.3 (E-17) · Registro G-31 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/permiso · UAT: no |

## 1 · Contexto y evidencia

`AuditPage.tsx:90,94-95` usa `log.user_name`, `log.old_value`, `log.new_value`; el esquema real (`audit/schemas.py:8-30`) expone `user_id`, `previous_values`, `new_values`, `previous_state`, `new_state`, `change_reason`, `comments` ⇒ usuario como id numérico; la pestaña «Correcciones» nunca muestra el diff; estados/comments ignorados. Además `limit=50` fijo sin paginar mientras el contador muestra `total` (`:61,109`); enumerados crudos (`:150,162,216`; acciones/módulos sin i18n → G-08 de F, cubierto aquí como parte del render); filtros del backend (`user_id`, `lot_id`, `farm_id`, `state`, `sap_reference_id`) no ofrecidos en UI (E-17).

## 2 · Causa raíz

La página quedó con el contrato de la primera iteración del modelo de auditoría; R-82/GA-REM-032 cerraron filtros backend sin actualizar la vista.

## 3 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Usuario | id | nombre (resolver por `/users` si hay permiso o incluir nombre en la lectura — C-01) |
| Diff | `old/new_value` inexistentes | `previous_values/new_values` y `previous_state/new_state` |
| Motivo | ignorado | `change_reason`/`comments` visibles |
| Paginación | 50 fijo | paginador con total |
| Enumerados | crudos | i18n `audit.actions/modules` (claves nuevas) |
| Filtros | 4 de 12 | usuario/lote/estado/SAP si se decide (mínimo: los existentes documentados) |

## 4 · Secciones §47 (resumen)

- **Alcance FE**: `AuditPage.tsx` (+`audit.service.ts`); i18n acciones/módulos (22/11 valores).
- **BE**: sin cambio por defecto; opcional C-01=B añadir `user_name` a la proyección de lectura (una línea, sin migración).
- **Fuera**: `sap_reference_id`/`ip/user_agent` (E-17: no poblados; GA-REM-032; requieren productores), inmutabilidad (R-148).
- **Contrato**: mismos endpoints; la página consume los campos reales.
- **Seguridad/BU**: `audit:read` sin cambio.
- **AC/cierre**: ver `R-219_AC_RED_E2E_UAT.md`.

## 5 · Dedup

C#11 + E-17; GA-REM-032 cubrió los filtros backend. **Nuevo** como paquete de vista (G-31).

## 6 · Interdependencias

P1-12-REOPEN (calidad de la traza) · R-212 (estados de error) · R-220 (i18n de enumerados afines).
