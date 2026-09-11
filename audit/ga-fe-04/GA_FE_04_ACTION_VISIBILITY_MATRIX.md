# GA-FE-04 · MATRIZ DE VISIBILIDAD DE ACCIONES

Fuente de verdad para E2E. `VISIBLE` = presente y accionable · `HIDDEN` = no renderizado ·
`N/A` = no aplica a ese actor (página no alcanzable o self) · `DISABLED` = visible no
accionable (solo donde ya existía patrón). Condiciones por columna: empresa efectiva (CTX),
Company BU (BUON), concesión de usuario (UGRANT), RBAC del permiso de la acción.

| Acción (permiso) | E | A | B | C | D | Z | P | R |
|---|---|---|---|---|---|---|---|---|
| Alta usuario (`users:create`) | V | H | H | H | H | H | H | **H** |
| Editar/contraseña/toggle usuario (`users:update`) | V | H | H | H | H | H | H | **H** |
| Desactivar usuario (`users:delete`) | V | H | H | H | H | H | H | **H** |
| Alta/edición rol (`users:create|update`) | V | H | H | H | H | H | H | **H** |
| Desactivar rol (`users:update`) | V | H | H | H | H | H | H | **H** |
| Maestro alta (`masters:create`) | V | H | H | H | H | H | H | **H** |
| Maestro edición (`masters:update`) | V | H | H | H | H | H | H | **H** |
| Maestro borrado (`masters:delete`) | V | H | H | H | H | H | H | **H** |
| Cargar curva (`masters:create`) | V | H | H | H | H | H | H | **H** |
| Activar curva (`masters:update`) | V | H | H | H | H | H | H | **H** |
| Conceder/revocar unidad (U8) | V | H* | **V** | H | H | H | H | H |
| CBU activar/desactivar (A1) | V | **V** | V | H | H | H | H | H |
| CTA «Nuevo lote» (`lots:create`) | V | H | H | **V**† | H | H | H | H |
| Guardar lote `/lots/new` (ruta `lots:create`) | V | H | H | **V**† | H | H | H | H |
| Cerrar lote (`lots:create`) | V | H | H | **V**† | H | H | H | H |
| Añadir fase (`lots:create`) | V | H | H | **V**† | H | H | H | H |
| Resolver alerta (`operations:update`) | V | H | H | **V**† | H | H | H | H |
| Guardar operación `/operations/new` (`operations:create`) | V | H | H | **V**† | H | H | H | H |
| Subir evidencia (`operations:create`) | V | H | H | **V**† | H | H | H | H |
| Borrar evidencia (`operations:delete`) | V | H | H | H‡ | H | H | H | H |
| Revisar (`review:review`) | V | H | H | H | H | H | H | H |
| Corregir (`corrections:correct`) | V | H | H | H | H | H | H | H |
| Aprobar (`approvals:approve`) | V | H | H | H | H | H | H | H |
| Rechazar (`approvals:reject`) | V | H | H | H | H | H | H | H |
| Batch revisión (`review:review`) | V | H | H | H | H | H | H | H |
| SAP mutaciones (`sap:send_sap`) | V | H | H | H | H | H | H | H |
| Auditoría/reportes (lectura) | V | H | H | H | H | H | H | H |
| Self (perfil/contraseña/campana) | V | V | V | V | V | V | V | V |

`*` A no tiene `business_units:create/delete` (solo read/update): concesiones ocultas — **esa
es la separación P13-AC18**.
`†` C: **condición compuesta** — permiso ✓ ∧ `broiler ∈ effective_business_units` (grant viva)
∧ Company BU ON. Cualquiera de las tres en falta ⇒ HIDDEN (3D §68).
`‡` C no tiene `operations:delete` en el rol 41: borrado de evidencia oculto — refuerza el
principio PAGE≠ACTION en la misma pantalla.

**Condiciones de la matriz 3D (C):**
```
CASO 1  OFF / UGRANT SÍ / RBAC SÍ  → HIDDEN + API DENY   (C con BU apagada)
CASO 2  ON  / UGRANT NO / RBAC SÍ  → HIDDEN + API DENY   (C sin concesión)
CASO 3  ON  / UGRANT SÍ / RBAC NO  → HIDDEN + API DENY   (P)
CASO 4  ON  / UGRANT SÍ / RBAC SÍ  → VISIBLE + ALLOW     (C con BU y concesión)
```

**Estado de carga (P13-AC22):** ninguna acción de esta matriz se evalúa antes de hidratar
`/me` (el layout solo se pinta cuando `isLoading=false`; el evaluador es síncrono sobre `user`).
**Switch de empresa:** `switchCompany` reemplaza tokens y refetchea `/me` ⇒ la matriz se
recalcula con el mismo render (probado en runtime).
