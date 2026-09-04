# 20 — ROADMAP MAESTRO

Principio rector (§112): **conservar lo correcto → reparar bloqueadores → cerrar lo parcial → integrar lo desconectado → completar requisitos críticos → recuperar trazabilidad → tests → seguridad → observabilidad → deuda → optimizar.**

**No se recomienda reescritura.** La arquitectura es sólida (ver §"Qué NO debe tocarse").

Complejidad: XS (<2 h) · S (medio día) · M (1-3 días) · L (1-2 semanas) · XL (>2 semanas). **No se estiman horas inventadas**: la complejidad es relativa.

---

## FASE 0 — Contención inmediata (bloqueadores de proceso)

Antes de tocar una sola línea de lógica de negocio: **detener el sangrado**. Hoy cualquier commit llega a producción sin control.

| Orden | ID | Módulo | Trabajo | Problema | Prior. | Depende de | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|---|---|---|
| 1 | GA-TD-010 | DevOps | Activar CI en `push` a `main` además de `pull_request` | ningún commit ha pasado nunca por lint/typecheck/tests | P0 | — | XS | un push con un error de TypeScript falla el workflow y no publica imagen |
| 2 | GA-TD-010 | DevOps | Desacoplar publicación de imagen del despliegue: quitar `pull_policy: always` + Watchtower; desplegar por tag | 171 commits desplegados sin aprobación | P0 | 1 | S | producción solo cambia al promover un tag; existe rollback documentado |
| 3 | GA-TD-008 | Seguridad | Rotar todas las contraseñas sembradas; retirar credenciales de `GUIA_PRUEBAS_EN_VIVO.md` y de los seeds de producción | `admin/admin123` público | P0 | — | XS | ninguna credencial funcional en el repositorio; `admin` con contraseña fuerte |
| 4 | GA-TD-026 | Infra | Inyectar `FEATURE_RATE_LIMIT_ENABLED=true` en producción | login sin protección anti-fuerza bruta | P0 | 3 | XS | 6 intentos de login en 1 min → 429 |
| 5 | GA-TD-007 | SAP | **Decisión ejecutiva**: implementar `RealSapAdapter` o poner `FEATURE_SAP_ENABLED=false` | eventos marcados `sent_to_sap` con id ficticio y bloqueados por BR-15 | P0 | — | XS (desactivar) / L (implementar) | ningún evento se marca `sent_to_sap` sin confirmación real; o el flag está apagado y el circuito manual documentado |
| 6 | GA-TD-006 | Infra | Volumen persistente para `MEDIA_DIR` y para las exportaciones SAP | evidencias perdidas en cada despliegue | P0 | — | S | subir una evidencia, redesplegar, descargarla correctamente |
| 7 | GA-TD-013 | Infra | `alembic upgrade head` automático antes de arrancar | releases con cambio de esquema rompen producción | P0 | 2 | S | despliegue con migración pendiente arranca con el esquema al día |
| 8 | — | Datos | **Auditar el estado real de la BD productiva**: eventos en `sent_to_sap` con `MANUAL-*`, filas de `evidences` con archivo inexistente, usuarios con `company_id` nulo | daño ya causado por P0-6, P0-7 y P1-2 | P0 | 5,6 | M | inventario del daño y plan de saneamiento aprobado |

---

## FASE 1 — Reparar los bloqueadores funcionales P0

| Orden | ID | Módulo | Trabajo | Problema | Prior. | Depende de | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|---|---|---|
| 9 | GA-TD-001 | Backend | Importar `get_current_bird_balance` y llamarla con 2 argumentos | registrar mortalidad → 500 | P0 | 1 | XS | test: `POST /operations` con `mortality_recording` devuelve 201 y genera alerta si supera el 3 % |
| 10 | GA-TD-009 | Backend | Invocar `validate_segregation` también en `complete_review` | BR-14 eludible | P0 | 1 | XS | test: el autor de un evento recibe 403 al intentar aprobarlo por cualquier ruta |
| 11 | GA-TD-005 | Frontend | Sustituir los 6 `limit=200` por `GET /lots/{id}` y `GET /operations/{id}`; unificar el tope de paginación en el backend | 5 pantallas rotas | P0 | 1 | S | las 5 pantallas cargan; ninguna llamada devuelve 422 |
| 12 | GA-TD-002 | Backend | Aplicar el valor corregido al evento en la misma transacción, con mapeo campo→destino | el dato erróneo se aprueba y se envía a SAP | P0 | 1 | M | test: tras corregir `quantity`, el evento y sus KPIs reflejan el nuevo valor y el `CorrectionLog` conserva el original |
| 13 | GA-TD-012 | Backend+FE | Endpoint `POST /me/password` con verificación de la contraseña actual; conectar `ProfilePage` | el cambio de contraseña no hace nada y anuncia éxito | P0 | 1 | S | cambiar la contraseña e iniciar sesión con la nueva; la antigua deja de funcionar |
| 14 | GA-TD-004 | Backend+FE | Replicar todos los claims en el refresh **y** volver a llamar a `/me` tras `setTokens` | escalada de privilegios a los 30 min | P0 | 1 | S | tras un refresh, `view_type`, `company_id`, `role_id` e `is_super_admin` se conservan |
| 15 | GA-TD-011 | Backend | Emparejar la trazabilidad por documento de despacho o por par explícito (lote origen, lote destino) | vínculos auto-referenciales o inexistentes | P0 | 1 | M | despachar huevo del lote A y recibirlo en el lote B crea un `EggBatch` A→B |
| 16 | GA-TD-019 | Backend | Implementar `registered_by_me` y aceptar listas de estados en `GET /operations` | Mis Pendientes → 500 | P0 | 1 | S | Mis Pendientes muestra solo los registros propios en estado borrador/registrado |

---

## FASE 2 — Autorización y aislamiento (seguridad estructural)

| Orden | ID | Módulo | Trabajo | Problema | Prior. | Depende de | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|---|---|---|
| 17 | GA-TD-003 | Backend | Dependencia `require_permission(module, action)` que consulte la tabla `permissions` | RBAC decorativo | P0 | 9-16 | M | un Operador recibe 403 en `/approvals/approve`, `/users`, `/sap/export` y `DELETE /masters/*` |
| 18 | GA-TD-003 | Backend | Aplicar la dependencia a los 165 endpoints, agrupados por módulo | idem | P0 | 17 | L | matriz de permisos verificada por test para los 6 roles sembrados |
| 19 | GA-TD-017 | Backend | `_apply_company_filter` devuelve un filtro imposible cuando `company_id` es nulo y el usuario no es super admin; exigir compañía al crear usuarios | fuga entre compañías | P0 | 17 | XS | un usuario sin compañía no ve ningún maestro ni lote |
| 20 | GA-TD-016 | Backend | Extraer `_company_filter()` (como el de `SapService`) y aplicarlo a los 61 filtros crudos | Super Admin ciego en 6 módulos | P1 | 19 | M | el Super Admin ve datos en Reportes, Revisión, Aprobaciones, Auditoría, Dashboard y Correcciones |
| 21 | GA-TD-003 | Frontend | Guard de ruta por rol y menú filtrado por permisos; eliminar el prop `roles` inservible de `ProtectedRoute` | acceso visual sin restricción | P1 | 18 | M | el menú y las rutas coinciden con los permisos efectivos del rol |
| 22 | GA-TD-022 | Backend | Endpoint de logout + denylist de `jti` | sesión no invalidable | P1 | 17 | M | tras logout, el refresh token deja de funcionar |
| 23 | GA-TD-057 | Backend | Auditar login, logout, login fallido, cambios de permisos y de maestros; escribir `last_login` | trazabilidad incompleta | P1 | 17 | M | los 6 eventos aparecen en `audit_logs` |

---

## FASE 3 — Cerrar features parciales e integrar lo desconectado

| Orden | ID | Módulo | Trabajo | Prior. | Depende de | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|---|---|
| 24 | GA-TD-014 | FE+BE | Mapear el selector de orden SAP al campo tipado `sap_document_ref`; migrar los datos ya guardados en `extra_data` | P1 | 11 | S | BR-11 y BR-18 se disparan; el comparativo SAP muestra filas |
| 25 | GA-TD-015 | Frontend | Generar `idempotency_key` (UUID) por envío de formulario | P1 | 11 | XS | dos envíos idénticos crean un solo evento |
| 26 | GA-TD-018 | Backend | Añadir `update_schema` a los 15 maestros que carecen de `PUT` | P1 | — | S | editar funciona en las 12 pantallas de catálogo |
| 27 | GA-TD-019 | Backend | Implementar `status`/`operator_id` en `/review/pending` y `search`/`action_contains`/`group_by` en `/audit` (o retirarlos de la UI) | P1 | — | M | las pestañas y el buscador filtran de verdad |
| 28 | GA-TD-021 | Backend | Conservar un solo mecanismo de auditoría (recomendado: helpers explícitos) y desactivar los listeners | P1 | 23 | M | una acción genera exactamente una entrada de auditoría |
| 29 | GA-TD-025 | Backend | Reescribir la condicional de BR-06 | P1 | — | XS | test: evento con fecha anterior a la activación → 400 |
| 30 | GA-TD-024 | BE+FE | Aplicar `ApprovalStep` en `approve()` y crear la UI de configuración de niveles | P1 | 18 | L | una compañía con 2 niveles exige dos aprobaciones de roles distintos |
| 31 | GA-TD-029 | Frontend | Pantalla de activación manual de lotes / saldos iniciales | P2 | 11 | M | un lote en curso se da de alta con población, edad y mortalidad acumulada |
| 32 | GA-TD-049 | Frontend | `SearchSelect` de lotes en `ReportsPage` (eliminar el ID numérico y el `2` codificado) | P2 | 11 | S | el usuario elige el lote por código |
| 33 | GA-TD-031 | BE+FE | Envoltorio `{items, total}` uniforme en los listados | P2 | 11 | S | la paginación de maestros muestra el total real |
| 34 | GA-TD-027 | Infra | `client_max_body_size 12m;` en Nginx | P2 | 6 | XS | se sube una evidencia de 8 MB |
| 35 | GA-TD-054 | Backend | Definir e implementar la semántica de `bird_transfer` en el saldo de aves | P2 | — | S | el traslado entre galpones no altera el saldo del lote; el traslado entre lotes sí |
| 36 | GA-TD-028 | BE+FE | Flujo de reverso post-SAP (BR-16) — **requiere spec previa** | P2 | 43 | L | un evento enviado a SAP se ajusta mediante reverso auditado |

---

## FASE 4 — Recuperar Spec Development

| Orden | ID | Trabajo | Prior. | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|
| 37 | GA-SPD-DEBT-001 | Ratificar la constitución (`/speckit.constitution`) con la regla **NO SPEC = NO DEVELOPMENT** y sus excepciones explícitas | P0 | S | `.specify/memory/constitution.md` sin marcadores, versionado y fechado |
| 38 | GA-SPD-DEBT-005 | Documentar la política de ramas, PR obligatorio y gates de CI | P0 | XS | ninguna escritura directa a `main` |
| 39 | GA-SPD-DEBT-003 | Reescribir los AC como `Given/When/Then` por funcionalidad, cada uno con el test que lo verifica | P0 | L | matriz AC↔test publicada |
| 40 | GA-SPD-DEBT-006 | **Retro-specs justificadas** (§108, marcadas `RETROSPECTIVE SPEC` con fecha real y motivo) para: evidencias, alertas, SearchSelect, inspección por galpón, selector de compañía, Telegram, `egg_reception_classification`, `hatchery_purpose`, `bird_transfer` | P1 | L | 9 retro-specs publicadas; ninguna reescribe la historia |
| 41 | GA-SPD-DEBT-008 | ADR de cambio de identidad visual + actualización de `docs/11` y `spec.md §6.3` (paleta y dark mode) | P1 | S | la spec describe la paleta realmente implementada |
| 42 | GA-SPD-DEBT-010 | Generar y versionar `openapi.json` en CI; regenerar el ERD desde `Base.metadata` | P1 | M | los contratos coinciden con el código en cada release |
| 43 | GA-SPD-DEBT-014 | Tabla única de reglas de negocio con identificadores coherentes entre spec, código y mensajes; incorporar BR-17/18/19 | P2 | S | `validators.py` y `spec.md §5` usan los mismos identificadores |
| 44 | GA-SPD-DEBT-011 | Reescribir `README.md`; archivar los informes históricos en `docs/history/` | P2 | S | el README describe el estado real |
| 45 | GA-SPD-DEBT-013 | Crear `docs/17-production-checklist.md` y `docs/18-production-runbook.md` | P2 | M | las referencias de la spec y de las tareas resuelven |
| 46 | GA-SPD-DEBT-012 | Reabrir la Fase 9 como puerta obligatoria; cerrar T-084…T-090 con evidencia | P1 | M | las 7 casillas marcadas con enlace a la evidencia |
| 47 | — | Publicar el **baseline v1.1** consolidando specs, retro-specs y desviaciones regularizadas | P1 | M | un único documento gobierna la implementación actual |

---

## FASE 5 — Testing

| Orden | ID | Trabajo | Prior. | Compl. | Criterio de aceptación |
|---|---|---|---|---|---|
| 48 | GA-TD-023 | Añadir `alembic upgrade head` + seeds de test al job de backend; independizar las fixtures de `lot_id=2` | P1 | M | los 76 tests de backend pasan en CI |
| 49 | GA-TD-044 | Corregir `test_operations.py:19` (24 → 25 tipos de evento) | P2 | XS | en verde |
| 50 | — | Test de regresión por cada bloqueador P0 (12) | P0 | M | cada P0 tiene un test que falla antes del fix y pasa después |
| 51 | GA-TD-059 | Tests de las páginas críticas: OperationFormPage, ReviewCenter, ApprovalPanel, LotDetailPage | P1 | L | cobertura frontend > 40 % como paso intermedio hacia el 70 % |
| 52 | — | **Contract testing** FE↔BE (generado desde OpenAPI) | P1 | M | ningún desajuste de límite, parámetro o forma llega a `main` |
| 53 | GA-TD-035 | Mover `tests/` de la raíz a `frontend/tests/` o añadir configuración; añadir un job E2E | P2 | S | los ~80 casos E2E se ejecutan |
| 54 | GA-TD-032 | Corregir los 5 errores de ESLint; plan de reducción de los 393 `any` | P2 | L | `eslint .` en verde |

---

## FASE 6 — Seguridad (resto)

| Orden | ID | Trabajo | Prior. | Compl. |
|---|---|---|---|---|
| 55 | S-08 / GA-TD-014 | BD: rol de aplicación con privilegios mínimos, SSL obligatorio, red restringida | P1 | M |
| 56 | GA-TD-058 | Retirar Watchtower o restringir su acceso al socket de Docker | P2 | S |
| 57 | GA-TD-045 | `UniqueConstraint(company_id, lot_code)` y validación por compañía | P2 | S |
| 58 | S-13 | Filtrar `EggBatch`/`ChickBatch` por compañía en la trazabilidad | P2 | XS |
| 59 | S-17 | Hacer bloqueantes `pip-audit` y `npm audit` (retirar `\|\| true`) | P2 | XS |
| 60 | — | Gestor de secretos en lugar de `.env` en el host | P2 | M |

---

## FASE 7 — Infraestructura y observabilidad

| Orden | ID | Trabajo | Prior. | Compl. |
|---|---|---|---|---|
| 61 | GA-TD-039 | Logging estructurado JSON + correlation ID por request | P1 | M |
| 62 | GA-TD-039 | Captura de errores (Sentry o equivalente) con alertas | P1 | S |
| 63 | GA-TD-040 | Backups automáticos + prueba de restauración documentada | P1 | M |
| 64 | — | Entorno de **staging** (T-084 nunca ejecutada) | P1 | M |
| 65 | — | Métricas básicas y dashboard de salud | P2 | M |
| 66 | GA-TD-051 | Corregir el `Makefile` (`db-seed`, ruff, mypy) | P3 | XS |
| 67 | GA-TD-052 | Fuente única de configuración (`.env` raíz vs `backend/.env`) | P3 | XS |

---

## FASE 8 — Deuda no bloqueante

| Orden | ID | Trabajo | Prior. | Compl. |
|---|---|---|---|---|
| 68 | GA-TD-020 | **Decisión arquitectónica**: adoptar la capa `services/`+`hooks/` en todas las páginas **o** eliminarla (~600 LOC muertas) | P1 | L |
| 69 | GA-TD-033 | Descomponer `OperationFormPage.tsx` (1 973 LOC) en un componente por tipo de evento | P2 | L |
| 70 | GA-TD-030 | Esquema de listado ligero sin relaciones `selectin` | P2 | M |
| 71 | GA-TD-036/037/034 | Eliminar código muerto: restos de dark mode, `SignaturePad`, `SidebarSubmenu`, `mock_adapter.py` | P3 | XS |
| 72 | GA-TD-047/048 | i18n de los textos servidos por el backend; sustituir emojis por iconos lucide | P3 | S |
| 73 | GA-TD-046 | `CHECK` constraints de integridad en los movimientos | P3 | M |
| 74 | GA-TD-050 | Prettier + formateo verificado en CI | P3 | S |
| 75 | GA-TD-055/056 | Resolver `egg_storage` (exponer o retirar) y los estados inalcanzables | P2 | M |
| 76 | GA-TD-060 | React Query si se conserva la capa de servicios | P3 | L |

---

## Quick wins (alto impacto · bajo riesgo · baja complejidad)

Ninguno es cosmético; todos cierran un defecto verificado.

| # | Acción | ID | Compl. | Impacto |
|---|---|---|---|---|
| 1 | Importar `get_current_bird_balance` y corregir la aridad | GA-TD-001 | XS | **desbloquea la operación diaria más frecuente del negocio** |
| 2 | `validate_segregation` en `complete_review` | GA-TD-009 | XS | cierra la elusión de BR-14 |
| 3 | Activar CI en `push` | GA-TD-010 | XS | primera puerta de calidad del proyecto |
| 4 | `FEATURE_RATE_LIMIT_ENABLED=true` | GA-TD-026 | XS | protege el login |
| 5 | Rotar contraseñas y retirarlas del repositorio | GA-TD-008 | XS | cierra el acceso público con `admin/admin123` |
| 6 | `client_max_body_size 12m;` | GA-TD-027 | XS | evidencias > 1 MB dejan de fallar |
| 7 | Corregir la condicional de BR-06 | GA-TD-025 | XS | restablece una regla de integridad |
| 8 | `_apply_company_filter` con filtro imposible si no hay compañía | GA-TD-017 | XS | cierra una fuga entre compañías |
| 9 | Volumen para `MEDIA_DIR` | GA-TD-006 | S | detiene la pérdida de evidencias |
| 10 | Sustituir los 6 `limit=200` | GA-TD-005 | S | **recupera 5 pantallas** |
| 11 | Añadir los `update_schema` faltantes | GA-TD-018 | S | recupera la edición en 8 catálogos |
| 12 | `idempotency_key` en el formulario | GA-TD-015 | XS | activa BR-12 |

---

## Qué NO debe tocarse (§47 del cuestionario obligatorio)

Está correcto y es la base sobre la que construir:

1. **Modelo de datos.** 47 tablas, 21 migraciones, **cero deriva** entre ORM y migraciones (verificado programáticamente). Cadena Alembic íntegra con un único head.
2. **Modelo de evento unificado.** `OperationalEvent` + 6 submodelos sustituyendo 12+ tablas del legacy: es un acierto de diseño.
3. **Adapter pattern de SAP.** ABC + DTOs sin acoplamiento. Solo falta la implementación concreta.
4. **Idempotencia y bitácora SAP.** Clave SHA-256, `SapPayload`/`SapResponse`, reintentos: bien diseñado.
5. **Validadores de reglas de negocio** (`validators.py`), salvo BR-06. Los cálculos de saldo son correctos.
6. **i18n.** 865 claves con paridad total ES/EN.
7. **Cabeceras de seguridad y validación de arranque** (`config.py` aborta con secretos por defecto).
8. **Ausencia de SQL crudo** — 100 % ORM, sin superficie de inyección.
9. **Catálogo de procesos** (`processCatalog.ts`) como fuente única de la taxonomía — necesita reconciliarse con la spec, no reescribirse.
10. **Estructura modular por dominio** del backend.

---

## Orden recomendado de implementación (resumen ejecutable)

```
0. Contención        →  pasos 1-8    (CI, despliegue, credenciales, SAP, volúmenes, migraciones, auditoría de datos)
1. Bloqueadores P0   →  pasos 9-16   (mortalidad, BR-14, 422, correcciones, contraseña, refresh, trazabilidad, pendientes)
2. Autorización      →  pasos 17-23  (RBAC, aislamiento, logout, auditoría de seguridad)
3. Cierre funcional  →  pasos 24-36  (SAP ref, idempotencia, maestros, filtros, multinivel, activación manual)
4. Spec Development  →  pasos 37-47  (constitución, AC, retro-specs, baseline v1.1)
5. Testing           →  pasos 48-54  (CI backend, regresión P0, contract testing, E2E)
6. Seguridad         →  pasos 55-60
7. Observabilidad    →  pasos 61-67
8. Deuda             →  pasos 68-76
```

**Regla de gobierno a aplicar desde el paso 37:**

```
REQUIREMENT → SPEC → REVIEW → AC → TASKS → IMPLEMENTATION → TEST → VALIDATION → CLOSE
```

Excepciones (hotfix de producción) permitidas **solo** con spec retroactiva en menos de 24 h, marcada `RETROSPECTIVE SPEC` con fecha real y motivo.
