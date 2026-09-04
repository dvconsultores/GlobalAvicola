# 19 — BRECHAS PARA PRODUCCIÓN

> Esta sección contiene **exclusivamente** lo que impide o pone en riesgo la operación en producción.
> Nota de contexto: el sistema **ya está desplegado** en `avicola.globaldv.net` con despliegue automático. Las brechas P0 no son "pendientes antes de salir": son **defectos vivos en producción**.

---

## 1. Bloqueadores P0 — impiden operar o comprometen la integridad

### P0-1 · Registrar mortalidad devuelve HTTP 500

| | |
|---|---|
| **Evidencia** | `backend/app/operations/service.py:242` invoca `get_current_bird_balance(self.db, event.lot_id, self.company_id)`. La función **no está importada** en el módulo (verificado por análisis del AST: no aparece en ningún `ImportFrom`, ni a nivel de módulo ni dentro de la función) y su firma real tiene **2 parámetros**, no 3 (`backend/app/operations/validators.py:21`). |
| **Disparador** | cualquier `mortality_recording` con cantidad > 0 — es decir, **la mortalidad diaria de todo lote** |
| **Efecto** | excepción no capturada → 500 → rollback → **el evento no se persiste** |
| **Introducido** | `bdb5cde` (2026-06-27 03:12) |
| **Detección** | ninguna: sin CI, sin logging de errores |
| **Corrección** | XS — importar la función y pasar 2 argumentos |

### P0-2 · Las correcciones no modifican el dato

| | |
|---|---|
| **Evidencia** | `backend/app/corrections/service.py:37-58` crea el `CorrectionLog`, cambia `event.status = CORRECTED` y audita. **Nunca escribe el valor corregido** sobre el evento ni sobre sus submovimientos. |
| **Efecto** | el dato erróneo es el que se aprueba, se consolida y se envía a SAP; los KPIs se calculan sobre el valor incorrecto |
| **Impacto de negocio** | rompe el propósito central del producto: "nada va a SAP sin revisión y corrección" |
| **Corrección** | M — aplicar el valor en la misma transacción, con mapeo campo→destino |

### P0-3 · No existe control de autorización en el backend

| | |
|---|---|
| **Evidencia** | ninguna dependencia `require_permission` en `backend/app/`. Los 165 endpoints autenticados usan `Depends(get_current_user)` a secas. La tabla `permissions` solo se lee para deducir `is_super_admin` (`auth/security.py:107-118`). |
| **Efecto** | cualquier usuario autenticado puede aprobar registros, borrar maestros, crear usuarios, modificar roles, exportar a SAP y leer la auditoría completa |
| **Violación** | `spec.md §4.1`, `docs/02 §6.2`, y el espíritu de BR-13/BR-14 |
| **Corrección** | L |

### P0-4 · Escalada de privilegios por refresh de token

| | |
|---|---|
| **Evidencia** | `backend/app/auth/service.py:72` emite `{"sub","username"}`; el login emitía además `company_id`, `role_id` y `view_type`. `frontend/src/stores/auth.store.ts:85-101` reconstruye el usuario desde los claims con `view_type: claims?.view_type \|\| 'web'`. `App.tsx` solo llama a `fetchMe()` cuando `isLoading` es true, y `setTokens` no lo restaura. |
| **Efecto** | a los 30 minutos, un operador móvil pasa a ser tratado como usuario web y accede a `/users`, `/approvals`, `/sap`, `/audit`, `/review`, `/masters`, `/lots/new`. Con P0-3, esas acciones **se ejecutan**. |
| **Corrección** | S |

### P0-5 · Cinco pantallas rotas por incompatibilidad de contrato

| | |
|---|---|
| **Evidencia** | seis llamadas con `limit=200` contra endpoints que declaran `le=100` → **HTTP 422** |
| **Afectadas** | `LotDetailPage:45` (detalle de lote completo: KPIs, fases, cierre, alertas, trazabilidad) · `ReviewDetail:32` · `CorrectionForm:27` · `UsersPage:21` · `ReportsPage:19` (gráficas) · `company.store:38` (selector de compañía) |
| **Efecto** | el detalle de lote, el detalle de revisión, el formulario de corrección y la gestión de usuarios **no cargan**; el selector de compañía queda siempre vacío |
| **Corrección** | S — usar `GET /lots/{id}` y `GET /operations/{id}`, y unificar el tope de paginación |

### P0-6 · Pérdida de evidencias en cada despliegue

| | |
|---|---|
| **Evidencia** | `backend/app/operations/router.py:19,166` escribe en `MEDIA_DIR` (`/app/media` por defecto). `docker-compose.yml` **no define ningún volumen** para el servicio `backend`. Watchtower recrea el contenedor cada vez que se publica una imagen (`WATCHTOWER_POLL_INTERVAL=60`). |
| **Efecto** | todas las fotos y PDF adjuntos a los eventos operativos se pierden; las filas de `evidences` quedan apuntando a rutas inexistentes |
| **Alcance añadido** | lo mismo ocurre con `/tmp/sap_exports/*.json` |
| **Corrección** | S — volumen nombrado o almacenamiento de objetos |

### P0-7 · No existe integración SAP real, y está activada en producción

| | |
|---|---|
| **Evidencia** | `backend/app/integrations/sap/service.py:34-38` — `# TODO: read from config/env which adapter to use`; devuelve siempre `ManualSapAdapter`. `docker-compose.yml:28` fija `FEATURE_SAP_ENABLED=true` desde `bfccdfb` (2026-07-08). |
| **Efecto** | `POST /sap/export` escribe un JSON efímero en `/tmp`, marca los eventos como `SENT_TO_SAP` con `sap_document_ref = "MANUAL-<hex>"` (identificador inexistente en SAP) y a partir de ahí **BR-15 impide editarlos**. `GET /sap/connection-check` devuelve siempre `connected: true`. Ningún evento puede alcanzar `SAP_CONFIRMED`. |
| **Tarea pendiente** | T-085 `RealSapAdapter`, marcada "🔴 Crítica (bloquea prod)" en `tasks.md` |
| **Corrección** | L — implementar T-085, o **desactivar el flag** y documentar el circuito manual real |

### P0-8 · Credenciales de administrador públicas sin rate limiting

| | |
|---|---|
| **Evidencia** | `GUIA_PRUEBAS_EN_VIVO.md:13-40` publica 15 pares usuario/contraseña, incluido `admin / admin123` (Super Administrador). Los mismos valores están en `backend/seeds/dev_seeds.py:154` e `integration_seeds.py:174-203`. `docker-compose.yml` **no inyecta `FEATURE_RATE_LIMIT_ENABLED`**, cuyo valor por defecto es `False` (`backend/app/config.py:96`), por lo que `@rate_limit("5/minute")` en el login es un *no-op*. |
| **Efecto** | si esos seeds se ejecutaron contra la base que sirve el dominio público, el sistema es accesible con credenciales conocidas y sin protección anti-fuerza bruta |
| **Corrección** | XS — rotar contraseñas, activar el flag, retirar credenciales del repositorio |

### P0-9 · El cambio de contraseña no funciona y anuncia éxito

| | |
|---|---|
| **Evidencia** | `backend/app/auth/schemas.py:42-49` — `UserUpdate` **no declara `password`**. Pydantic descarta las claves desconocidas, así que `update_user` (`auth/service.py:130-142`) recibe un diccionario vacío. `ProfilePage.tsx:24-26` envía `{password}`, recibe 200 y muestra "Contraseña actualizada". |
| **Efecto** | ningún usuario puede cambiar su contraseña después del alta, y **cree que lo ha hecho** |
| **Corrección** | S — endpoint dedicado con verificación de la contraseña actual |

### P0-10 · Elusión de la segregación de funciones (BR-14)

| | |
|---|---|
| **Evidencia** | `backend/app/review/service.py:196-234` — `complete_review()` con `company.approval_levels <= 1` asigna `APPROVED` y `approved_by_id = current_user["id"]` **sin llamar a `validate_segregation`**, que sí se aplica en `ApprovalService.approve()` (`:301-309`). |
| **Ruta explotable** | `POST /operations` → `POST /review/batches` → `POST /review/start/{id}` → `POST /review/complete` |
| **Efecto** | el propio autor aprueba su registro; con P0-3 no hace falta ningún permiso especial |
| **Corrección** | XS |

### P0-11 · Trazabilidad generacional inoperante

| | |
|---|---|
| **Evidencia** | `backend/app/operations/service.py:127-176` y `:190-228` — la creación automática de `EggBatch`/`ChickBatch` busca el evento complementario **con el mismo `lot_id`** y luego asigna el lote destino como `reception.lot_id`, es decir, **el mismo lote**. |
| **Efecto** | en operación normal (despacho en el lote origen, recepción en el lote destino) la coincidencia nunca ocurre → no se crea ningún vínculo; si coincidiera, se crearía un lote enlazado consigo mismo |
| **Impacto** | la trazabilidad generacional —diferenciador declarado en `docs/00 §6.5`— no funciona |
| **Corrección** | M |

### P0-12 · Ninguna puerta de calidad entre commit y producción

| | |
|---|---|
| **Evidencia** | `backend-ci.yml:8-12` y `frontend-ci.yml:11-15` se disparan **solo** en `pull_request`; el repositorio tiene **0 merges y 0 pull requests** en 171 commits. `docker-push-backend.yml` y `docker-push-frontend.yml` se disparan en `push` a `main` y publican `:latest`; Watchtower actualiza en ≤ 60 s. |
| **Efecto** | ningún commit ha pasado nunca por lint, typecheck ni tests, y todos llegaron a producción automáticamente |
| **Consecuencias observadas** | 31 errores de TypeScript en `main` (`fcb57a7`), 9 commits de "fix build", 12 defectos P0 vivos |
| **Corrección** | S |

---

## 2. Riesgos P1 — alto

| ID | Riesgo | Evidencia |
|---|---|---|
| P1-1 | **Migraciones no automatizadas.** No hay `alembic upgrade head` en el Dockerfile, el compose ni ningún workflow. Con despliegue automático, cualquier release con cambio de esquema rompe producción. Precedente: `AUDITORIA_FUNCIONAL_E2E.md` H1 (4 migraciones sin aplicar → `UndefinedColumnError`). | `backend/Dockerfile:52`; `docker-compose.yml` |
| P1-2 | **Fuga de aislamiento multi-compañía.** `masters/service.py:35-41`: un usuario **no** super admin con `company_id = NULL` ve los maestros y lotes de **todas** las compañías. `User.company_id` es nullable y no se valida en el alta. | `masters/service.py` |
| P1-3 | **Super Admin ciego en 6 módulos.** 61 filtros `company_id == self.company_id` sin soporte de `NULL` en `reports`(19), `review`(12), `dashboard`(11), `lots`(5), `operations`(5), `audit`(4), `corrections`(4). El fix de `bfccdfb` se aplicó solo a `SapService`. | 7 servicios |
| P1-4 | **Sin logout ni revocación de sesión.** Refresh tokens de 7 días imposibles de invalidar. | inventario de rutas |
| P1-5 | **Observabilidad nula.** Sin logging estructurado, sin correlation ID, sin captura de errores, sin métricas, sin alertas. Un fallo como P0-1 solo se ve como un 500 genérico en el móvil del operador. | ninguna dependencia ni configuración |
| P1-6 | **Sin backups ni procedimiento de restauración.** Ninguna evidencia en el repositorio. La base de datos está fuera del compose. | — |
| P1-7 | **La suite de backend no puede pasar en CI.** El job levanta un Postgres vacío sin migraciones ni seeds; la fixture `auth_headers` exige login 200 y los tests dependen de `lot_id=2`. | `backend-ci.yml`; `tests/conftest.py` |
| P1-8 | **BR-11 y BR-12 inertes.** El frontend nunca envía `sap_document_ref` ni `idempotency_key`, así que ni la unicidad de documento SAP ni la idempotencia se aplican jamás. | `frontend/src` |
| P1-9 | **BR-06 anulada por una condicional mal formada.** Se pueden registrar eventos con fecha anterior a la activación del lote. | `validators.py:250` |
| P1-10 | **Edición imposible en 8 catálogos maestros** (405): 15 de 19 entidades carecen de `PUT` mientras la UI ofrece "Editar" en 12. | `masters/router.py:88-107` |
| P1-11 | **Rate limiting apagado en producción.** | `docker-compose.yml`; `config.py:96` |
| P1-12 | **Auditoría duplicada e incompleta.** Dos mecanismos escriben a la vez; no se auditan login, logout, cambios de permisos ni cambios de maestros. | `main.py:33-37` + 9 llamadas |
| P1-13 | **Aprobación multinivel no operativa.** `approval_steps` tiene CRUD y ningún enforcement; solo se distingue "1 nivel" vs ">1". | `review/service.py` |
| P1-14 | **BD en IP pública con rol `postgres` y sin SSL obligatorio**, usada además como entorno de desarrollo. | `backend/.env`; `.env.example:30` |
| P1-15 | **Activación manual de lotes sin interfaz.** Requisito de implantación crítico (migrar lotes en curso) solo accesible por API. | sin ruta en `App.tsx` |
| P1-16 | **Filtros de UI inertes.** 7 parámetros enviados y no soportados: pestañas de estado y filtro de operador en Revisión, buscador y 2 pestañas en Auditoría, `registered_by_me` en Mis Pendientes. | `ReviewCenter`, `AuditPage`, `MyPendingPage` |

---

## 3. Necesario para consolidar — P2 (selección)

Volumen de evidencias · `client_max_body_size` en Nginx · totales de paginación · tabla `reversals` (BR-16) · N+1 por 8 relaciones `selectin` · `ReportsPage` con ID de lote numérico · `mock_adapter.py` que no compila · tests E2E de la raíz sin runner · restricción única `(company_id, lot_code)` · estados `DRAFT`/`SAP_CONFIRMED`/`SAP_ERROR` inalcanzables · `bird_transfer` sin efecto en el saldo · Watchtower con socket de Docker · `docs/17-production-checklist.md` inexistente.
Detalle completo en `16_TECHNICAL_DEBT.md`.

---

## 4. Discrepancias documentación vs realidad

| Declaración | Documento | Realidad verificada |
|---|---|---|
| "⚠️ El proyecto está en fase de especificación. **No se ha iniciado codificación funcional**" | `README.md:107` | 171 commits, 30 000 LOC, sistema desplegado en producción |
| Estructura del backend con `routers/`, `schemas/`, `services/`, `repositories/`, `models/`, `domain/`, `workflows/`, `migrations/` | `README.md:60-75` | **ninguna** de esas carpetas existe; la estructura es modular por dominio |
| "**29/29 rutas definidas y funcionales**" | `CERTIFICACION_FUNCIONAL.md §2` | lista `/approval-steps` y `/corrections` como rutas: **no existen** en `App.tsx`. De las que sí existen, 5 están rotas |
| "71 operaciones al 100 %, **14 integraciones SAP**, multi-compañía certificado, listo para UAT" | `CERTIFICACION_FUNCIONAL.md` | la "integración SAP" es solo de interfaz: el valor se guarda en `extra_data`, nunca en `sap_document_ref`; multi-compañía tiene dos agujeros confirmados |
| "Tests unitarios 61/61 passed" | `CERTIFICACION_FUNCIONAL.md §1` | **verdadero** — reconfirmado hoy |
| "34 instancias de SearchSelect, 25 casos de switch" | `CERTIFICACION_FUNCIONAL.md §3` | **verdadero** — verificado |
| "Dark Mode — Theme store con persistencia" como entregable crítico | `IMPLEMENTATION_COMPLETE.md` | eliminado 4 días después (`8940d9e`); además `spec.md §6.3` lo prohibía expresamente |
| "16/16 hallazgos cerrados, resultado **APROBADO**" | commit `e0eed25` (2026-06-24) | 5 días después el propio equipo documenta que la auditoría automática **no existía** y `audit_logs` estaba vacía |
| "re-certificación final V2 — **96/100**" | commit `a84eb2d` (2026-06-27) | RBAC nunca aplicado; auditoría inexistente en esa fecha |
| "AUDITORÍA IMPLEMENTADA · Timeline de 4 pasos" | `AUDITORIA_FUNCIONAL_E2E.md` | implementada **por duplicado**: la secuencia `created → updated → …` que se presenta como evidencia es precisamente el síntoma del doble registro |
| "Nivel AA WCAG" | `WCAG_ACCESSIBILITY_REPORT.md` | **NO VERIFICABLE**: sin herramienta, sin test automatizado, sin CI |
| Checklist de producción `docs/17-production-checklist.md` | citado por `spec.md §14.5` y `tasks.md` Fase 9 | **el archivo no existe** |
| "Production Activation Checklist: ☐ T-084 … ☐ T-090" | `tasks.md` | las 7 casillas siguen sin marcar, y aun así se activó SAP en producción |

---

## 5. Implementaciones sin documentación (§94)

| Feature | Clasificación |
|---|---|
| Motor de alertas (`operational_alerts`) | feature no documentada — en uso |
| Evidencias adjuntas (`evidences`) | feature no documentada — en uso |
| `SearchSelect` (34 campos) | feature no documentada — en uso, mejora real de UX |
| Inspección por galpón con equipos | feature no documentada — en uso |
| Selector de compañía + `switch-company` | feature no documentada — en uso (roto por P0-5) |
| Telegram Mini App + bot | **canal de producto nuevo** sin spec |
| `egg_reception_classification`, `hatchery_purpose`, `bird_transfer` | tipos/campos de dominio sin spec |
| `egg_storage` | datos capturados y nunca leídos — **deuda** |
| Tabla `reversals` | **código abandonado** (0 referencias) |
| `SignaturePad`, `mock_adapter.py`, `DarkModeToggle`, `theme.store`, `SidebarSubmenu` | **código abandonado / experimentos** |
| Reglas BR-17, BR-18, BR-19 | reglas de negocio activas sin requisito escrito |

---

## 6. Criterios para declarar Global Avícola listo para producción

Un criterio verificable por línea. Ninguno se cumple hoy.

```
□  Los 12 bloqueadores P0 cerrados y verificados por un test automatizado
□  CI ejecutándose en cada push a main, en verde, y bloqueando el despliegue si falla
□  Despliegue por tag aprobado (sin :latest + Watchtower)
□  alembic upgrade head ejecutado automáticamente antes de arrancar la aplicación
□  RBAC aplicado en los 165 endpoints autenticados + guard por rol en el frontend
□  Suite de backend ejecutándose en CI contra una BD desechable, en verde
□  Cobertura backend > 80 % y frontend > 70 % (objetivo de spec §7)
□  Volumen persistente para evidencias, con prueba de supervivencia a un redeploy
□  Decisión formal sobre SAP: RealSapAdapter implementado, o flag desactivado y circuito manual documentado
□  Todas las contraseñas de los seeds rotadas y retiradas del repositorio
□  Rate limiting activo y verificado (6 intentos de login → 429)
□  Backups automáticos con restauración probada
□  Logging estructurado + correlation ID + captura de errores
□  docs/17-production-checklist.md y docs/18-production-runbook.md creados y ejecutados
□  Las 7 tareas de la Fase 9 (T-084…T-090) cerradas con evidencia
□  Baseline documental v1.1 publicado: retro-specs de las 12 features sin spec y de las 6 desviaciones
□  Constitución del proyecto ratificada con la regla NO SPEC = NO DEVELOPMENT
```
