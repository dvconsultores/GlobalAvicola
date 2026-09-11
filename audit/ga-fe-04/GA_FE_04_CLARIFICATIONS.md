# GA-FE-04 · CLARIFICACIONES

Resueltas contra fuentes canónicas; **0 preguntas al propietario** (`§4`).

| # | Pregunta | Respuesta | Fuente |
|---|---|---|---|
| C01 | ¿Redacción exacta de P-13? | Proceso «Gestión de usuarios, roles y permisos»; residual R-98 = autoridad RBAC en controles de escritura de pantalla | Backlog R-98 · `audit/06` · `P13_*` |
| C02 | ¿Páginas afectadas? | 32 rutas inventariadas; 31 acciones de escritura en 12 pantallas (usuarios, roles, 20 maestros, curvas, lotes×3, operaciones×3, review×3, approvals, SAP) | inventario §13 |
| C03 | ¿Clases de acción? | Taxonomía §14 del encargo; clasificación por recurso (contrato backend), no por texto | contrato acción-API |
| C04 | ¿Relación con R-98? | Es **su** residual; GA-FE-04 es el cierre, individual, con reconciliación por AC | reconciliación canónica |
| C05 | ¿Relación con R-119? | Ya CLOSED (GA-FE-03); aquí solo regresión | `GA_FE_03_R119_RECONCILIATION` |
| C06 | ¿Relación con R-181? | El «submit» no tiene UI: `EXCLUDED_R181`; no se implementa; no cuenta contra R-98 | backlog R-181 |
| C07 | ¿Relación con R-182? | LotForm sin cambios; `EXCLUDED_R182` | backlog R-182 |
| C08 | ¿Helper compartido? | `hasPermission` espejo de `tiene_permiso` (R-121); reutilizado | `auth/permissions.ts` |
| C09 | ¿Reutilización del evaluador GA-FE-03? | Sí: `canAccessCapability` es la primitiva; la capa de acción (`auth/actionAuthority.ts`) la reexpone para pantallas | SPEC §18 |
| C10 | ¿Reglas BU de acciones productivas? | permiso ∧ (global: BU habilitada+contexto / normal: efectiva) ∧ recurso; BU OFF absoluto | OD-16.e/f · D-1 |
| C11 | ¿Reglas de plano de control? | Solo permiso + contexto; sin BU de usuario | OD-09.b · OD-15 |
| C12 | ¿Reglas del actor global? | Mismas de GA-FE-03 para producto; control total gobernado; nunca cruza BU OFF | OD-14 · D-1 |
| C13 | ¿Zero-BU en pantalla? | CORE según RBAC; sin acciones productivas ni CTAs de vacío productivos | OD-09.c · P13-AC14 |
| C14 | ¿Restricciones self? | Verificar existentes (self-grant 403 `OD-15.a`); sin reglas nuevas | OD-15 |
| C15 | ¿Cross-company? | Candidatos no exponen foráneos (certificado); el gate no crea reglas | GA-FE-02-E |
| C16 | ¿Interacción con estado de recurso? | Se **conserva**; autoridad y estado son dimensiones separadas; la UI distingue denegación de estado donde ya lo hacía | §22 |
| C17 | ¿Alternas móvil? | No existen menús de desborde con mutaciones; misma semántica que desktop | inventario §E |
| C18 | ¿CTAs de vacío? | «Nuevo»/«Nuevo lote» gated por su permiso de alta (§38) | §38 |
| C19 | ¿Clasificación de reportes/descargas? | Auditoría/reportes actuales = solo lectura sin export (N/A); descargas de evidencia = `operations:read` (lectura) sin cambio; D-1 sigue aplicando a datos | inventario |
| C20 | ¿Criterio de cierre? | 5 condiciones (reconciliación §6) + P13-AC01…40 con evidencia runtime; decisión individual | SPEC §25 |

**Decisiones de diseño documentadas** (no preguntas al propietario):
1. Los **tiles de secuencia** (`/poultry/:birdType/:phase`) se clasifican `READ_NAVIGATION`:
   navegan al alta; su autoridad se aplica en la **ruta destino** (nueva guarda
   `operations:create`) y en el backend — así no se revierte una UX aceptada en UAT GA-FE-03
   (§6 del encargo).
2. `V10` (batch) se gatea con `review:review` — **el contrato del router**, no la intuición.
3. `L3/L4` (cerrar lote/añadir fase) se gatean con `lots:create` — contrato del router.
4. Aprobar y rechazar son gates **separados** (`approvals:approve`/`approvals:reject`).
