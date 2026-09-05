# `GA-REM-032` · COBERTURA DE AUDITORÍA Y CONTRATO DE CONSULTA

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-032` · `DOMAIN + CONTRACT SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgos** | `R-81` (emisiones ausentes) · `R-82` (deriva de contrato en la consulta) |
| **Proceso** | `P-09` · Auditoría interna |
| **Dependencias** | `GA-REM-002` (permisos) · `GA-REM-026` (frontera transaccional) |
| **Antecedentes** | `P09_AUDIT_ACTION_COVERAGE_MATRIX.md` · `P09_AUDIT_QUERY_CONTRACT_MATRIX.md` · `P09_PROCESS_CHAIN_MATRIX.md` |

> **Dos hallazgos, una spec.** `R-81` y `R-82` tienen causas distintas —ausencia de emisores
> frente a deriva de contrato entre capas— y por eso se registran por separado. Comparten
> spec porque comparten sección normativa (`docs/02 §3.11`) y un único criterio de
> terminado: certificar `P-09`. Sus criterios van en grupos separados.

---

## 1. Requisito

`docs/02 §3.11.1`, prioridad **Crítica**:

> **Cada acción en el sistema** genera un registro de auditoría inmutable.

`docs/02 §3.11.2`, prioridad **Alta**:

> **Filtros:** por usuario, lote, fecha, tipo de operación, módulo, estado, documento SAP.

## 2. `R-81` · seis módulos sin un solo registro

Los listeners vigilan **tres** tipos —`OperationalEvent`, `CorrectionLog`,
`ApprovalAction`—. De los once módulos declarados en `AuditModule`, seis no producen nada:
`auth`, `masters`, `lots`, `users`, `config`, `reports`.

Ocho acciones obligatorias nunca se escriben, entre ellas **el inicio de sesión fallido** y
**el cambio de permisos**, que son las primeras que un auditor busca.

## 3. `R-82` · una vista que aparenta filtrar

`AuditPage` envía `search`, `action_contains` y `group_by`. FastAPI descarta en silencio los
parámetros no declarados, así que la caja de búsqueda no busca, la pestaña «Correcciones»
muestra todo y la de «Por usuario» no agrupa.

Ninguno de los tres aparece en fuente normativa alguna: los inventó la interfaz. Mientras
tanto, cuatro filtros que la norma exige y **el backend ya implementa** —usuario, lote, tipo
de operación, módulo— no se ofrecen, y otros dos —estado y documento SAP— faltan en ambos
lados.

## 4. Fuera de alcance

- `CONFIG_CHANGE`: no existe superficie de configuración que auditar. Se documenta y no se
  implementa; si algún día la hay, vuelve a la lista.
- Rediseñar la vista más allá de los filtros normativos.
- `R-76`, `R-77`, `R-80`, `OD-04`, `GA-TD-014`, SAP real.
- La trazabilidad generacional (`P-10`): es otro proceso.

## 5. Criterios de aceptación — grupo A · emisiones (`R-81`)

### `AC01` · El acceso al sistema deja rastro
Un inicio de sesión correcto escribe `LOGIN`; uno fallido escribe `LOGIN_FAILED` con el
usuario intentado; el cierre escribe `LOGOUT`. Módulo `auth`.

Un intento fallido **no puede** registrar una sesión válida ni exponer la contraseña.

### `AC02` · Los cambios de maestros y lotes dejan rastro
Alta, edición y baja lógica de un maestro o de un lote escriben `CREATED`, `UPDATED` y
`DELETED` en los módulos `masters` y `lots`, con la entidad afectada identificada.

### `AC03` · Los cambios de permisos dejan rastro
Crear un rol o modificar sus permisos escribe `PERMISSION_CHANGE`, módulo `users`, con el rol
afectado y el actor.

### `AC04` · La importación y la exportación dejan rastro
Importar referencias SAP escribe `IMPORT`; exportar un informe escribe `EXPORT`.

### `AC05` · El cierre de revisión deja rastro
`POST /review/complete` escribe `REVIEW_COMPLETED`.

### `AC06` · El registro dice quién, qué, cuándo y dónde
Todo registro nuevo lleva actor, acción, marca temporal, módulo y la entidad afectada, según
`§3.11.1`. **Un registro sin actor no es auditoría.**

### `AC07` · Cada registro pertenece a su empresa
La empresa del registro es la del actor que ejecutó la acción.

> Para acciones sin empresa —un login fallido de un usuario inexistente— el registro se
> escribe igualmente y la empresa queda nula. **Un fallo de acceso no auditado por no saber
> a quién atribuirlo es exactamente el caso que más importa.**

### `AC08` · Fallar al auditar no rompe la operación de acceso
Se respeta el patrón vigente: las emisiones existentes participan de la transacción del
negocio (`GA-REM-026`). Las nuevas siguen ese mismo patrón, sin inventar uno alternativo.

## 6. Criterios de aceptación — grupo B · consulta (`R-82`)

### `AC09` · Los filtros normativos existen y filtran
`GET /audit` admite y **aplica** los siete de `§3.11.2`: usuario, lote, fecha, tipo de
operación, módulo, **estado** y **documento SAP**.

**Puerta de validez.** Cada filtro se prueba con un conjunto deliberadamente distinguible y
se comprueba el **subconjunto exacto**. Prohibido `count >= 0`, prohibido «la respuesta no
es 500».

### `AC10` · El filtrado ocurre en el servidor
El subconjunto se calcula en la consulta, antes de paginar. Un filtro que solo recortara la
página ya recuperada no cumple.

### `AC11` · La interfaz deja de pedir lo que nadie atiende
`AuditPage` no envía `search`, `action_contains` ni `group_by`. Lo que ofrezca al usuario se
corresponde con lo que el backend aplica: **ningún control que aparente filtrar sin filtrar**.

### `AC12` · Aislamiento entre empresas
Un auditor de la empresa A no obtiene registros de la B.

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo sujeto y la misma consulta; lo
único que cambia es de quién son los registros. Prohibido usar un Super Admin como sujeto
negativo.

### `AC13` · Sin permiso no se consulta
`audit:read` es obligatorio; sin él, `403`.

## 7. Criterio transversal

### `AC14` · La evidencia puede fallar
`GA-REM-016 AC13`. Cada prueba de este tramo demuestra por mutación controlada y revertida
que detecta la ausencia del comportamiento. Una prueba que pasa con la emisión desactivada no
es evidencia.

## 8. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC08` | `backend/tests/test_audit_coverage.py` | integración HTTP |
| `AC09` `AC10` `AC12` `AC13` | `backend/tests/test_audit_query.py` | integración HTTP |
| `AC11` | revisión del diff + `tsc` | contrato |
| cadena de `P-09` | `e2e/proceso-p09-auditoria-interna.spec.ts` | `API_E2E` |
| `AC14` | informe de certificación | mutación |

## 9. Definición de terminado

- Los catorce criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta —el registro
  esperado no existe; el filtro no acota— y no por autenticación, permiso o fixture.
- Sensibilidad demostrada y revertida.
- Los 14 pasos de `P09_PROCESS_CHAIN_MATRIX §2` se recorren.
- Regresión completa sin fallos nuevos.
