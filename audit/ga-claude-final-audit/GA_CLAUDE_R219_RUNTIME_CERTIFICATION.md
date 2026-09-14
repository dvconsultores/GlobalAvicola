# GA-CLAUDE · CERTIFICACIÓN RUNTIME — R-219: `AuditPage` CONTRA EL CONTRATO REAL

Fecha: 2026-09-14 · Paquete: `specs/R-219/` (compacto) · HEAD de partida: `56d0fcb` (T7 cerrada).

## 1 · Ejecución por ciclos

| Ciclo | Commits | Resultado |
|---|---|---|
| **C1 · RED** | `5b9bde5` | `r219.auditPage.test.tsx`: **FE 5F** — usuario como id (01), sin diff (02), `comments` ignorado (03), `limit=50` sin paginador (04), acciones crudas (05). |
| **C2 · Implementación** | `2f5d52f` | Nombre de usuario resuelto vía `/users` cuando hay `users:read` y `Usuario #id` si no (C-01=A); diff real `previous_values/new_values` + `previous_state/new_state`; `change_reason` y `comments` en el detalle; paginador 50/página sobre `total` (offset real, reset al filtrar); i18n `audit.actions/modules` (22/11) en ES/EN. **FE 5/5** · suite completa **399/399** · `tsc` 0. |
| **C2s · Sensibilidad** | `45acbf8` | S1 (id crudo): 1F. S2 (sin diff): 1F. S3 (sin paginador): 1F. |
| **C3 · Runtime** | — | En ventana (familia G-06): `R219-RT-01…03` (captura `/audit` con nombre, diff y paginación). |

## 2 · Criterios de aceptación

| AC | Estado | Evidencia |
|---|---|---|
| AC-R219-01 nombre de usuario (o id resoluble) | ✅ | test 01 (+ fallback `Usuario #id`); S1 lo rompe |
| AC-R219-02 diff en «Correcciones» | ✅ | test 02; S2 lo rompe |
| AC-R219-03 `change_reason`/`comments` visibles | ✅ | test 03 |
| AC-R219-04 paginación funcional (50 con `total`) | ✅ | test 04 (offset=50 real); S3 lo rompe |
| AC-R219-05 acciones/módulos traducidos ES/EN | ✅ | test 05 + claves nuevas en ambos locales |
| AC-R219-06 sin migración (opcional BE no tomado) | ✅ | C-01=A (resolución FE) |
| AC-R219-07 regresión | ✅ | 399/399 + `tsc` 0 |

## 3 · Límites declarados

- **C3 runtime** en ventana; verificación informativa (pestaña Correcciones con diff) en la captura.
- Sin permiso `users:read` el nombre se degrada a `Usuario #id` (documentado; el auditor sin acceso a usuarios no pierde la fila).
- Filtros de backend adicionales (`lot_id`, `farm_id`, estados SAP) siguen sin exponerse en UI (fuera del alcance del paquete; la ruta los declara).

## 4 · Veredicto

**R-219 = `CLOSED_TECHNICALLY`** — la vista de auditoría consume el contrato real (usuario, diff, motivo/comentarios), pagina de verdad y traduce sus enumerados. **P-09 reparado técnicamente** en su superficie de lectura.
