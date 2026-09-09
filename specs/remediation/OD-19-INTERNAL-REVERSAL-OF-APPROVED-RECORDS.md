# `OD-19` · REVERSO INTERNO DE REGISTROS APROBADOS PRE-SAP

Decisión de propietario · resuelve `AOD-21` (`R-136` componente interno · `H360-P05` · `G-R09`) · 2026-09-09 · **VIGENTE**
Alias: **`AOD-21 → OD-19`**.

```
UN REVERSO NO BORRA LA HISTORIA.
UN REVERSO CREA UNA COMPENSACIÓN TRAZABLE, APROBADA Y EXACTAMENTE ÚNICA
DE UN EFECTO DE NEGOCIO YA APROBADO.
```

## Alcance

Registros operativos **aprobados** dentro de Global Avícola que **todavía no** han sido enviados ni contabilizados en
SAP. **No gobierna**: `SENT_TO_SAP`, contabilizado en SAP, rechazado por SAP, reverso de documentos SAP, `R-161`,
consolidados (hasta resolver su contrato) ni `BU-D10`.

## Las cláusulas (texto del propietario, numerado como en `AOD-21`)

| # | Cláusula |
|---|---|
| **1** | **Estado del original**: se crea un estado semánticamente distinto, **`REVERSED`**. No se reutiliza `CANCELLED` (flujo detenido sin efecto aprobado). `REVERSED` = el registro fue válido y aprobado, produjo o podía producir efecto, y ese efecto fue neutralizado por un proceso formal. `CANCELLED ≠ REVERSED`. Si el enumerado persistido exige migración, queda **autorizada conceptualmente**, con SPEC + AC + plan de migración primero |
| **2** | **El original es inmutable**: un `APPROVED` no vuelve a `DRAFT`, `RETURNED`, `CORRECTED` ni se edita. El reverso no modifica retrospectivamente los datos originales. Mientras la solicitud está pendiente, `original.status = APPROVED`; solo cuando el reverso queda aprobado y la contrapartida aplicada, `original.status = REVERSED`; si se rechaza, sigue `APPROVED` |
| **3** | **Compensación** mediante **contrapartida / evento inverso explícito y trazable**. No: eliminar el original, editar sus cantidades, marcar `CANCELLED` para que desaparezca de las sumas, ni excluirlo retroactivamente como si nunca hubiese existido. `t0` X ocurrió · `t2` X fue neutralizado · efecto neto 0; la historia conserva ambos |
| **4** | **Contrapartida generada por el servidor**: cantidad y naturaleza se derivan exclusivamente del original. El cliente no envía como autoridad cantidad, saldo, unidad, empresa, estado objetivo ni efecto inverso |
| **5** | **Exactamente una contrapartida** por original: `EFECTO ORIGINAL + EFECTO DEL REVERSO = EFECTO NETO GOBERNADO`; segundo reverso = denegado o idempotente sin efecto nuevo; nunca doble compensación, doble restauración, doble decremento ni dos reversos concurrentes efectivos |
| **6** | **Aprobación del reverso**: no se hace efectivo por la sola solicitud. `APPROVED → REVERSAL REQUEST → PENDING REVIEW → APPROVED REVERSAL → APPLY COMPENSATION → REVERSED`; rechazo: `REVERSAL REQUEST → REJECTED`, el original sigue `APPROVED`. Usar el **mecanismo de aprobación existente** cuando sea compatible; **no crear un segundo motor** |
| **7** | **Separación de actores**: quien solicita **no** aprueba su propio reverso. No se exige que el solicitante sea distinto del registrador original. `REVERSAL REQUESTER ≠ REVERSAL APPROVER` |
| **8** | **Permiso**: capacidad explícita y **distinta** de corrección, aprobación ordinaria y administración de accesos. No reutilizar `corrections:correct`. Nombre según la convención del repositorio (conceptualmente `operations:reverse` o `reversals:create`). Sin lógica por nombre de rol |
| **9** | **Motivo obligatorio**: no `null`, no `""`, no espacios. Se preservan motivo, solicitante, aprobador, fecha/hora, original, contrapartida, estado anterior y final |
| **10** | **Elegibilidad**: `APPROVED` · pre-SAP · no revertido · no consolidado · inquilino válido · unidad operativa · permiso válido. **No** elegibles: `DRAFT`, `PENDING_REVIEW`, `RETURNED`, `REJECTED`, `CORRECTED`, `CANCELLED`, `REVERSED`, anulados, `SENT_TO_SAP`, contabilizados, rechazados por SAP y todo estado posterior a la integración |
| **11** | **Consolidados**: **no elegibles** en esta etapa (`CONSOLIDATED REVERSAL = DEFERRED`); sin descomposición automática |
| **12** | **SAP**: enviado o contabilizado → deja de ser interno; contrato SAP futuro (`P-08`). Nunca simular un reverso SAP solo dentro de la app |
| **13** | **Unidad de negocio**: el reverso es operación productiva: empresa efectiva + `CompanyBusinessUnit` habilitada + autoridad de unidad del actor donde aplique + capacidad de reverso + propiedad del recurso + estado elegible. `CompanyBusinessUnit OFF → REVERSAL DENIED` para usuario ordinario, Contraloría, Administrador de Accesos y **Super Admin / autoridad global** (no evita `is_enabled = false`) |
| **14** | **Inquilino**: `TENANT_SCOPED`; Super Admin sin empresa efectiva → fallo cerrado; situado en `A` no reversa `B` (`OD-14`) |
| **15** | **Administrador de Accesos**: `business_units:update` no concede autoridad de reverso |
| **16** | **Contraloría**: control transversal ≠ autoridad de reverso; requeriría la capacidad explícita; no se infiere del rol |
| **17** | **Saldos**: la compensación neutraliza el efecto exacto; para población de aves preserva `R-130` (sin saldo negativo, sobre-restauración ni doble compensación); el backend usa los datos autoritativos del original |
| **18** | **Huevos / incubación**: si la seguridad concurrente depende de `R-161`, **no implementar** ese subtipo todavía: `BLOCKED_BY_R-161`; no cerrar por transitividad |
| **19** | **Concurrencia**: dos solicitudes concurrentes no producen dos reversos efectivos; protección atómica (bloqueo de fila, transición atómica, restricción); `MAX EFFECTIVE REVERSALS PER ORIGINAL = 1` |
| **20** | **Transacción** atómica: validar original → bloquear → validar aún reversible → derivar compensación → escribir compensación → marcar/vincular reverso → marcar original `REVERSED` → auditar → commit; si algo falla, `ROLLBACK ALL`; nunca `REVERSED` sin compensación ni compensación sin `REVERSED` |
| **21** | **Trazabilidad**: vínculo permanente `REVERSAL → ORIGINAL`; reutilizar la tabla `reversals` si satisface el contrato; sin esquema nuevo si el modelo lo representa; si falta una pieza indispensable: SPEC → AC → migración |
| **22** | **`R-136`**: interno pasa de `OWNER_DECISION_REQUIRED` a `READY_FOR_SPEC / IMPLEMENTATION`; post-SAP sigue `SAP_DEFERRED`. Resultado esperado: `R-136 INTERNAL = CLOSED` · `R-136 OVERALL = PARTIAL` · `SAP = DEFERRED` |
| **23** | **Otros hallazgos** no absorbidos: `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-165` OPEN · `R-166` OPEN · `R-140` PARTIAL · `R-154` PARTIAL |
| **24** | **Principio final**: el reverso no borra la historia; crea una compensación trazable, aprobada y exactamente única de un efecto aprobado |

## Trazabilidad

| Fuente | Relación |
|---|---|
| `BR-16` · `docs/02 R16` | el ajuste post-SAP sigue exigiendo reverso/corrección/nuevo movimiento: **no cambia**; esta decisión define el reverso **pre-SAP** |
| `OD-17.a` | el reverso era clase terminal nombrada sin definir: **se define** (`REVERSED`) |
| `docs/12 §2/§4` fila 13 · `docs/02 §4` | `Anulado` (`CANCELLED`) sigue siendo distinto; no se abre desde `Aprobado` |
| `R136_INTERNAL_REVERSAL_PREFLIGHT.md` · `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md` | evidencia del vacío y de los efectos; las columnas `OWNER_DECISION_REQUIRED` quedan resueltas por esta decisión |
| `GA-REM-041` | spec que la implementa |

## Aclaración A · asignación de la capacidad de reverso a los roles sembrados (2026-09-09 · propietario · WAVE B tranche 6)

Precisa `§8` (capacidad explícita) sin cambiar ninguna semántica de `§1-§24`. Es gobierno de **semillas/catálogo**, no lógica
de autorización por nombre (`OD-09.a §3.1`): en tiempo de ejecución decide el permiso, nunca el nombre del rol.

| Rol sembrado (nombre real del repositorio) | `reversals:create` | `reversals:read` | Nota |
|---|:--:|:--:|---|
| **Supervisor Avícola** (`dev_seeds`, `test_seeds`) | **sí** | **sí** | solicita y lee; **no** aprueba (`approvals:*` no se le concede; `BR-14`: solicitante ≠ aprobador) |
| **Contralor Avícola** (`integration_seeds`; función «contraloría» de `OD-08`) | no | **sí** | lectura bajo su alcance transversal; no solicita por defecto |
| **Administrador de Accesos** | no | no | plano de control (`OD-15`) |
| **Operador de Granja** y demás roles operativos | no | no | por defecto |
| **Super Administrador / autoridad global** | conserva la autoridad ya gobernada (capacidad comodín) | ídem | — |

Reglas: `reversals:create` ≠ autoridad de aprobación · el motor de aprobación existente sigue gobernando la decisión ·
**no** se crea `reversals:approve` · ningún rol gana comodín ni alcance entre empresas · `dev_seeds` **no** tiene un rol
de Contraloría (el «Auditor» es otra figura: consulta de auditoría) y **no se inventa uno**: la asignación de Contraloría vive
donde la figura existe (`integration_seeds`). Implementación: `GA-REM-041` enmienda A.
