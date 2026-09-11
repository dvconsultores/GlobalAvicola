# GA-FE-05 · ACLARACIONES (C01–C20)

Resueltas contra fuentes canónicas del repositorio; sin preguntas al propietario ya respondidas por las fuentes.

| # | Pregunta | Resolución canónica |
|---|---|---|
| C01 | Endpoint real de envío | `POST /operations/{event_id}/submit` (`app/operations/router.py:310`) |
| C02 | Permiso real | `operations:create` (`require_permission("operations","create")`) |
| C03 | Estados iniciales válidos | `registered`, `returned`, `rejected` (`REENVIABLES`) |
| C04 | Estado resultante | `pending_review` |
| C05 | Estados válidos de reenvío | Los mismos (`returned`, `rejected`); es el mismo acto explícito (`OD-17.b`) |
| C06 | Semántica `returned` | Reenviable; editable; tras reenvío vuelve a la cola (`docs/12 §2`) |
| C07 | Semántica `rejected` | **No terminal** (`OD-17.a`): reenviable y corregible |
| C08 | Inmutabilidad aprobado/final | `approved`/`consolidated`/`sent_to_sap`/`sap_confirmed`/`cancelled`/`reversed` no admiten submit (400) |
| C09 | ¿Corrección prerequisito? | No para reenviar un `returned` (reenvío directo); `corrected` NO es reenviable (espera aprobador). La UI no impone corrección previa; el reenvío de `returned`/`rejected` es válido por sí mismo |
| C10 | Ubicación del CTA | Cabecera del detalle `/operations/:id` (`OperationDetailPage`), acción primaria junto al estado |
| C11 | Ubicación del reenvío | Mismo lugar; mismo componente; label «Reenviar a revisión» |
| C12 | Confirmación | **Sin modal**: patrón directo del flujo de revisión (p. ej. `start` en ReviewCenter). Resultado confirmado por toast + estado fresco |
| C13 | Refresh post-envío | `GET /operations/:id` fresco ⇒ chip + CTA recomputados (obligatorio; no toast-only) |
| C14 | Comportamiento en fallo | Toast de error normalizado + refetch; sin estado optimista; sin éxito falso |
| C15 | Doble clic | Botón `disabled` durante el vuelo ⇒ una petición lógica; segunda transición en backend ⇒ 400 documentado |
| C16 | Auditoría | Éxito: `audit_state_transition` «Enviado a revisión» (backend, ya existe). Denegado: sin fila (guarda antes de `db.add`) |
| C17 | Actor global | Puede enviar si comodín ∧ CBU ON ∧ contexto situado (concesión no exigida); CBU OFF ⇒ 403 también para él |
| C18 | Cero unidades | Sin unidades efectivas ⇒ CTA oculto y API 403 (guarda operativa) |
| C19 | Móvil | Mismo componente responsive; CTA en cabecera alcanzable en 390×844; sin desborde ni CTA duplicado |
| C20 | Criterios de cierre R-181 | Reconciliación §5 (10 criterios): CTA submit + resubmit + estado localizado + refresh/relogin + fallo + doble clic + inmutables + seguridad + 0 backend + no regresión |

**Sin nueva decisión del propietario** (OD-17 ya decidida; contrato backend vigente).
