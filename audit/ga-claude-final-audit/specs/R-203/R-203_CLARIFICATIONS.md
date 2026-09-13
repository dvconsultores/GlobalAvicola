# R-203 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. Ninguna decisión del propietario requerida; supuestos verificados en código.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿404 o 403 para referencia ajena? | **404 fail-closed** («<X> no encontrado»), patrón I.4/`tenancy.py:39-70`; la granja usa 403 hoy en un punto (`lots/service.py:320-329`) — no se cambia ese contrato, los nuevos siguen el patrón dominante. | informe D I.4 | técnica |
| C-02 | `genetic_line_id` con `company_id NULL` (compartida) | Se acepta (semántica R-179 `verificar_catalogo_de_empresa`: nulo = compartida). | `tenancy.py:114` | técnica |
| C-03 | `weight_curve_id` de línea compartida | Aceptable si el lote declara esa línea (o ninguna): la curva cuelga de la línea, no de la empresa; se exige coherencia línea↔curva (regla ya existente) **y** que la línea sea alcanzable por la empresa. | `lots/service.py:275-307` | técnica |
| C-04 | ¿Qué hacer con filas históricas cruzadas si el inventario §12 las encuentra? | Registrar y decidir en tranche aparte (no se sanea en este paquete); el AC09 solo exige medición. | encargo §61 (no modificar esquema) | técnica |
| C-05 | `breed_id` | Fuera de alcance de R-203 (pertenece a la línea; R-146-like si se decide). No se toca. | registro G-14 | técnica |
| C-06 | ¿La edición pasa por `MasterService.update` o gana su propio camino? | Mantener `MasterService.update` para campos genéricos; las verificaciones de tenencia viven **antes** en `lots/service.update_lot`. | `masters/service.py:187,248-254` | técnica |
| C-07 | Relación con R-50 (company_id de maestros) | Independientes; pueden ir en la misma tranche de seguridad pero con paquetes/commits separados. | registro §3 orden 2 | técnica |

Sin decisiones abiertas.
