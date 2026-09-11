# GA-FE-07 · CLARIFICACIONES (C01–C20)

| # | Pregunta | Decisión | Base |
|---|---|---|---|
| C01 | ¿Campo canónico de inactividad del Área? | `is_active: bool` (sin `deleted_at`/`status`) | `Area` model; trace |
| C02 | ¿Mecanismo de baja lógica? | `DELETE /masters/areas/{id}` → `MasterService.deactivate` (is_active=False, fila permanece, auditoría) | código + UI (`api.delete`) |
| C03 | ¿El API de listado expone el estado? | **Sí** — `AreaRead` incluye `is_active`; el listado **no** filtra por estado | `register_crud`; runtime |
| C04 | ¿El selector filtra en cliente o el endpoint debería filtrar? | **Cliente** en el formulario (el endpoint es compartido con administración y no ofrece filtro; no se crea uno nuevo) | spec §12 |
| C05 | ¿El listado genérico debe excluir inactivas? | **No** — es contrato de administración (control-plane ve todo) | spec §12/§22; OD-21 |
| C06 | Regla de alta con inactiva | DENY 400 «Área inactiva» (BR-07) | spec §10 |
| C07 | Regla de edición con inactiva | DENY **solo si hay cambio efectivo de referencia** | spec §11 |
| C08 | Lectura histórica de área inactiva | Sin condiciones; no se bloquea | spec §9 |
| C09 | Update no relacionado con histórica inactiva | ALLOW, área intacta | H1 |
| C10 | Mismo ID inactivo explícito en el payload | ALLOW (no es referencia nueva) | H2; semántica `exclude_unset` + comparación |
| C11 | Reemplazo por activa | ALLOW (valida tenencia+activa) | H4 |
| C12 | Reemplazo por inactiva | DENY | H3/H5 |
| C13 | Referencia ajena inactiva | DENY «no encontrado» (tenencia primero, anti-enumeración) | R-182-A intacto |
| C14 | NULL | Sin cambios (allow; withdraw no es asignación nueva) | contrato R-182 |
| C15 | Semántica de error | Inactiva propia: «Área inactiva»/BR-07; ajena/inexistente: «Área no encontrado»/BR-07 | spec §16 |
| C16 | Auditoría | Denegaciones sin éxito; éxitos normales | spec §17 |
| C17 | Móvil | Mismo contrato que escritorio (regresión E2E) | spec §18 |
| C18 | ES/EN | Sin textos nuevos de UI (mensaje backend por canal existente) → N/A documentado | spec §18 |
| C19 | ID del finding | **R-185** (verificado libre; catálogo ≤ R-184) | `GA_FE_07_FINDING_R185.md` |
| C20 | Criterios de cierre | Denegación alta/edición + selector + históricos + positivos + tenencia + regresiones | spec §19/§23 |
