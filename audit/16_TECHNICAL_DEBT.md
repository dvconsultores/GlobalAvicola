# 16 — REGISTRO DE DEUDA TÉCNICA

Prioridades: **P0** impide operar o compromete la integridad · **P1** riesgo alto · **P2** necesario para consolidar · **P3** mejora no bloqueante.
Complejidad: XS · S · M · L · XL.

## 1. Registro

| ID | Categoría | Hallazgo | Evidencia | Impacto | Riesgo | Prior. | Compl. | Acción |
|---|---|---|---|---|---|---|---|---|
| GA-TD-001 | backend | `mortality_recording` lanza `NameError`: `get_current_bird_balance` no importado y llamado con 3 args frente a firma de 2 | `operations/service.py:242` vs `validators.py:21` | la operación diaria más frecuente no se puede registrar | operación paralizada | **P0** | XS | importar la función y pasar 2 argumentos; añadir test de regresión |
| GA-TD-002 | backend | Las correcciones no aplican el valor al evento | `corrections/service.py:37-58` | el dato erróneo se aprueba y se consolida a SAP | integridad de datos | **P0** | M | aplicar el valor sobre el evento/submovimiento en la misma transacción, con mapeo campo→destino |
| GA-TD-003 | security | RBAC modelado y **no aplicado** en ningún endpoint | ausencia de `require_permission` en `backend/app/` | cualquier usuario aprueba, borra maestros y exporta a SAP | control interno | **P0** | L | dependencia `require_permission(module, action)` + aplicarla a los 165 endpoints |
| GA-TD-004 | security | El refresh emite un token sin `view_type`/`company_id`/`role_id`; el frontend degrada al usuario a `web` | `auth/service.py:72`; `auth.store.ts:85-101` | escalada de privilegios a los 30 min | control de acceso | **P0** | S | replicar todos los claims en el refresh **y** volver a llamar a `/me` tras `setTokens` |
| GA-TD-005 | integration | 6 llamadas con `limit=200` contra endpoints `le=100` → 422 | `LotDetailPage:45`, `ReviewDetail:32`, `CorrectionForm:27`, `UsersPage:21`, `ReportsPage:19`, `company.store:38` | 5 pantallas rotas | funcionalidad | **P0** | S | usar `GET /lots/{id}` y `GET /operations/{id}`; unificar el tope de paginación |
| GA-TD-006 | infrastructure | Evidencias y exportaciones SAP en el filesystem del contenedor sin volumen | `operations/router.py:19,166`; `docker-compose.yml` | pérdida de datos en cada despliegue | pérdida de datos | **P0** | S | volumen nombrado o almacenamiento de objetos |
| GA-TD-007 | integration | `RealSapAdapter` inexistente; `get_adapter()` devuelve siempre `ManualSapAdapter`; `FEATURE_SAP_ENABLED=true` en producción | `sap/service.py:34-38`; `docker-compose.yml:28` | los eventos se marcan `sent_to_sap` con id ficticio y quedan bloqueados por BR-15 | integridad + operación | **P0** | L | implementar T-085 o desactivar el flag y documentar el modo manual real |
| GA-TD-008 | security | Credenciales de Super Admin publicadas + rate limiting apagado en producción | `GUIA_PRUEBAS_EN_VIVO.md:13-40`; `docker-compose.yml` sin `FEATURE_RATE_LIMIT_ENABLED` | acceso total no autorizado | seguridad | **P0** | XS | rotar todas las contraseñas, activar el flag, retirar credenciales del repositorio |
| GA-TD-009 | backend | BR-14 eludible por `POST /review/complete` | `review/service.py:196-234` | el operador aprueba su propio registro | control interno | **P0** | XS | invocar `validate_segregation` también en `complete_review` |
| GA-TD-010 | DevOps | CI solo en `pull_request` + 0 PRs ⇒ nunca ejecutado; `push` a `main` despliega a producción vía Watchtower en 60 s | `.github/workflows/*`; `git log --merges` → 0 | ningún control de calidad antes de producción | proceso | **P0** | S | ejecutar CI también en `push`; sustituir `:latest`+Watchtower por despliegue etiquetado y aprobado |
| GA-TD-011 | backend | Trazabilidad generacional auto-referencial: empareja despacho y recepción por el mismo `lot_id` | `operations/service.py:127-176, 190-228` | no se crea la cadena entre generaciones | trazabilidad | **P0** | M | emparejar por documento/orden de despacho o por par (lote origen, lote destino) explícito |
| GA-TD-012 | frontend | El cambio de contraseña no hace nada y muestra éxito (`UserUpdate` no declara `password`) | `auth/schemas.py:42-49`; `ProfilePage.tsx:24` | los usuarios no pueden cambiar su contraseña; falso positivo | seguridad + confianza | **P0** | S | endpoint `POST /me/password` con verificación de la contraseña actual |
| GA-TD-013 | infrastructure | No hay `alembic upgrade head` en el despliegue | `backend/Dockerfile:52`; `docker-compose.yml` | cada release con cambio de esquema rompe producción | disponibilidad | **P1** | S | job de migración previo al arranque (init container o entrypoint) |
| GA-TD-014 | integration | El frontend nunca envía `sap_document_ref` (usa `extra_data.sap_order_ref`) | `frontend/src` (2 usos, ambos de lectura) | BR-11 y BR-18 inertes; comparativo SAP vacío | trazabilidad SAP | **P1** | S | mapear el selector al campo tipado y migrar los datos existentes |
| GA-TD-015 | integration | El frontend nunca envía `idempotency_key` | `frontend/src` (0 usos) | BR-12 inerte; duplicados posibles | integridad | **P1** | XS | generar un UUID por envío de formulario |
| GA-TD-016 | backend | 61 filtros `company_id == self.company_id` sin soporte de Super Admin en 7 servicios | `reports`(19), `review`(12), `dashboard`(11), `lots`(5), `operations`(5), `audit`(4), `corrections`(4) | el Super Admin no ve nada en 6 módulos | funcionalidad | **P1** | M | extraer un helper `_company_filter()` como el de `SapService` y aplicarlo |
| GA-TD-017 | security | `MasterService._apply_company_filter` no filtra cuando `company_id` es nulo y el usuario no es super admin | `masters/service.py:35-41` | fuga de datos entre compañías | seguridad | **P1** | XS | devolver un filtro imposible (`false()`) en ese caso y exigir compañía al crear usuarios |
| GA-TD-018 | backend | 15 de 19 maestros sin `PUT`, con la UI ofreciendo "Editar" en 12 → 405 en 8 pantallas | `masters/router.py:88-107` | edición imposible en 8 catálogos | funcionalidad | **P1** | S | añadir los `update_schema` que faltan |
| GA-TD-019 | frontend | 7 parámetros de filtro enviados y no soportados (`registered_by_me`, `status` en review, `operator_id`, `search`, `action_contains`, `group_by`) | `MyPendingPage:33`, `ReviewCenter:86,91`, `AuditPage:44-48` | filtros y pestañas inertes; `MyPendingPage` responde 500 | funcionalidad | **P1** | M | implementar los parámetros en el backend o retirarlos de la UI |
| GA-TD-020 | architecture | Capa `services/` + `hooks/` completamente muerta (~600 LOC, 12 servicios, 9 hooks) mientras las páginas llaman axios directamente | `frontend/src/services/`, `frontend/src/hooks/` | duplicación, causa raíz de GA-TD-005 y GA-TD-019 | mantenibilidad | **P1** | L | decidir: adoptar la capa en todas las páginas **o** eliminarla; no ambas |
| GA-TD-021 | backend | Doble mecanismo de auditoría activo (listeners + helpers) | `main.py:33-37` + 9 llamadas en servicios | entradas duplicadas; bitácora poco fiable | auditabilidad | **P1** | M | conservar uno solo (recomendado: helpers explícitos) y desactivar el otro |
| GA-TD-022 | security | Sin logout ni revocación; refresh token de 7 días | inventario de rutas | sesión no invalidable | seguridad | **P1** | M | denylist de `jti` en BD o Redis + endpoint de logout |
| GA-TD-023 | testing | Los 76 tests de backend no pueden pasar en CI (sin migraciones ni seeds; dependen de `lot_id=2`) | `backend-ci.yml`; `tests/conftest.py` | ninguna red de seguridad | calidad | **P1** | M | `alembic upgrade head` + seeds de test en el job; independizar las fixtures |
| GA-TD-024 | backend | `approval_steps` con CRUD y **sin enforcement**: la aprobación multinivel no secuencia | `review/service.py:412-470` vs `approve()` | el diferenciador de producto no funciona | funcionalidad | **P1** | L | aplicar los pasos en `approve()` + UI de configuración |
| GA-TD-025 | backend | BR-06 con una condicional mal formada que la anula | `validators.py:250` | se pueden registrar eventos anteriores a la activación del lote | integridad | **P1** | XS | reescribir la condición |
| GA-TD-026 | infrastructure | Rate limiting desactivado en producción (variable no inyectada) | `docker-compose.yml`; `config.py:96` | fuerza bruta sobre el login | seguridad | **P1** | XS | añadir `FEATURE_RATE_LIMIT_ENABLED=true` |
| GA-TD-027 | infrastructure | Nginx sin `client_max_body_size` (1 MB por defecto) frente a 10 MB del backend | `frontend/nginx.conf` | 413 en evidencias > 1 MB | funcionalidad | **P2** | XS | `client_max_body_size 12m;` |
| GA-TD-028 | DB | Tabla `reversals` huérfana: BR-16 sin implementación | 0 referencias fuera del modelo | ajuste post-SAP imposible | funcionalidad | **P2** | L | implementar el flujo de reverso o retirar la tabla del alcance |
| GA-TD-029 | frontend | `opening_balances` sin interfaz: la activación manual de lotes solo por API | sin ruta en `App.tsx` | implantación de lotes en curso inviable desde la UI | funcionalidad | **P2** | M | pantalla de activación manual |
| GA-TD-030 | performance | `OperationalEvent` con **8 relaciones `lazy="selectin"`**; `GET /operations?limit=100` dispara ~9 consultas y materializa todos los submovimientos | `operations/models.py` (8 `selectin`) | latencia y memoria en listados | rendimiento | **P2** | M | esquema de listado ligero sin relaciones; `selectin` solo en el detalle |
| GA-TD-031 | backend | Listados sin `total` en maestros, lots, operations y users → paginación falsa | `masters/router.py:40`; `MasterListPage:43` | UX incorrecta | funcionalidad | **P2** | S | envoltorio `{items, total}` uniforme |
| GA-TD-032 | code quality | 393 avisos `no-explicit-any` y 5 errores `react-hooks/refs` | `eslint .` → 436 problemas | tipado efectivo bajo | mantenibilidad | **P2** | L | tipar respuestas de API; corregir los 5 errores |
| GA-TD-033 | code quality | `OperationFormPage.tsx` con **1 973 LOC** y un `switch` de 25 casos | archivo | riesgo alto al modificar | mantenibilidad | **P2** | L | extraer un componente por tipo de evento |
| GA-TD-034 | dead code | `mock_adapter.py` no compila (`from .interface import SapAdapter`, módulo inexistente) | `ModuleNotFoundError` verificado | entregable declarado e inexistente | fiabilidad | **P2** | XS | eliminar o crear `interface.py` |
| GA-TD-035 | dead code | 1 065 LOC de tests E2E en `tests/` sin `playwright.config` en la raíz | `ls playwright*` en la raíz → nada | falsa sensación de cobertura | calidad | **P2** | S | mover a `frontend/tests/` o añadir configuración |
| GA-TD-036 | dead code | Restos de dark mode tras su eliminación: `darkMode:'class'`, `theme.store.ts`, `DarkModeToggle.tsx`, lectura de `theme-storage` en `main.tsx` | `tailwind.config.ts:4`; `main.tsx:19` | confusión | mantenibilidad | **P3** | XS | eliminar |
| GA-TD-037 | dead code | `SignaturePad` (133 LOC + 91 de test) y `SidebarSubmenu` (145 LOC) sin uso | 0 importadores | peso muerto | mantenibilidad | **P3** | XS | eliminar o integrar |
| GA-TD-038 | backend | Backoff de reintento `(minute + n) % 60` puede producir una fecha pasada | `sap/service.py:317-319, 398-400` | reintentos inmediatos en bucle | fiabilidad | **P2** | XS | usar `timedelta` |
| GA-TD-039 | observability | Sin logging estructurado, sin correlation ID, sin captura de errores, sin métricas, sin alertas | ninguna dependencia ni configuración | fallo productivo no diagnosticable | operabilidad | **P1** | M | logging JSON + request id + Sentry o equivalente |
| GA-TD-040 | infrastructure | Sin backups ni procedimiento de restauración documentado | ninguna evidencia | pérdida catastrófica | continuidad | **P1** | M | backups automáticos + prueba de restauración |
| GA-TD-041 | docs | `README.md` afirma "No se ha iniciado codificación funcional" y describe una estructura de backend inexistente | `README.md:107,60-75` | desorienta a cualquier incorporación | docs | **P2** | XS | reescribir |
| GA-TD-042 | docs | `docs/17-production-checklist.md` referenciado por la spec y las tareas, **no existe** | `spec.md §14.5`; `tasks.md` Fase 9 | checklist de producción inexistente | docs | **P2** | S | crearlo |
| GA-TD-043 | docs | Contratos de API (`specs/.../api-contract.md`, `docs/06`) describen una fracción de los 167 endpoints | comparación con OpenAPI | contrato no confiable | docs | **P2** | M | versionar `openapi.json` generado |
| GA-TD-044 | testing | `test_operations.py:19` afirma `len(data) == 24`; el endpoint devuelve 25 | verificado en runtime | test roto | calidad | **P2** | XS | actualizar |
| GA-TD-045 | backend | Sin restricción única `(company_id, lot_code)`; la validación es global y en código | `lots/service.py:53`; 2 uniques en 47 tablas | colisiones y enumeración entre compañías | integridad | **P2** | S | `UniqueConstraint` + validación por compañía |
| GA-TD-046 | backend | Sin `CHECK` constraints (0 en 47 tablas): cantidades negativas solo se frenan en la capa de aplicación | metadata | integridad débil | integridad | **P3** | M | `CHECK (quantity >= 0)` en los movimientos |
| GA-TD-047 | i18n | Textos en español fijo servidos por el backend (`ALL_EVENT_TYPES`, `quick_actions`) y cabeceras de exportación | `operations/schemas.py:180`; `dashboard/service.py:48`; `ReportsPage:38` | rompe el bilingüismo en esos puntos | producto | **P3** | S | devolver claves i18n |
| GA-TD-048 | frontend | Emojis en UI, prohibidos por `spec.md §6.3` | `OperationFormPage:60-65`; `dashboard/service.py:48-53` | incoherencia con el design system | producto | **P3** | XS | sustituir por iconos lucide |
| GA-TD-049 | frontend | `ReportsPage` selecciona el lote escribiendo su **ID numérico**, con valor por defecto `2` codificado | `ReportsPage:11` | inusable | UX | **P2** | S | `SearchSelect` de lotes |
| GA-TD-050 | code quality | Indentación de 1 espacio en gran parte de `src/pages` por ediciones mecánicas masivas; sin Prettier | inspección | legibilidad | **P3** | S | Prettier + formateo en CI |
| GA-TD-051 | infrastructure | `make db-seed` apunta a `app.seeds` (los seeds están en `backend/seeds/`); `make backend-lint`/`typecheck` fallan (ruff y mypy no instalados) | `Makefile`; `ls backend/.venv/bin` | comandos documentados que no funcionan | DevOps | **P3** | XS | corregir el Makefile y las dependencias dev |
| GA-TD-052 | infrastructure | Divergencia entre `.env` raíz y `backend/.env` (puerto, `SAP_ENABLED`) | ambos archivos | configuración ambigua | DevOps | **P3** | XS | fuente única |
| GA-TD-053 | infrastructure | `FEATURE_TELEGRAM_ENABLED` inyectada y no declarada en `Settings` | `docker-compose.yml:29`; `config.py` | flag inerte | DevOps | **P3** | XS | declararla y usarla o retirarla |
| GA-TD-054 | backend | `bird_transfer` no participa en ningún cálculo de saldo de aves | `validators.py:26-33` | los traslados no afectan al inventario | integridad | **P2** | S | decidir e implementar su semántica |
| GA-TD-055 | backend | `egg_storage` solo se escribe; ningún endpoint la lee | 1 referencia | datos capturados sin uso | funcionalidad | **P3** | S | exponerla o retirarla |
| GA-TD-056 | backend | Estados `DRAFT`, `SAP_CONFIRMED` y `SAP_ERROR` inalcanzables | `operations/service.py:76`; `sap/service.py` | máquina de estados con ramas muertas | modelo | **P2** | M | implementar la confirmación de SAP o depurar el enum |
| GA-TD-057 | security | Auditoría sin cobertura de autenticación, permisos ni maestros; `last_login` nunca escrito | `audit/listeners.py:88-113` | trazabilidad incompleta | auditabilidad | **P1** | M | ampliar la auditoría a esos eventos |
| GA-TD-058 | infrastructure | Watchtower con el socket de Docker montado | `docker-compose.yml:87-99` | superficie de escalada en el host | seguridad | **P2** | S | retirar o restringir |
| GA-TD-059 | testing | Cobertura frontend ~4 % (4 archivos de test / 108 fuentes), 2 de ellos sobre componentes muertos | inventario | sin red de seguridad | calidad | **P1** | L | tests de páginas críticas y de contrato |
| GA-TD-060 | frontend | Sin capa de caché de datos (React Query/SWR): cada pantalla refetch manual en `useEffect`, con `set-state-in-effect` señalado por ESLint 19 veces | `src/pages/**` | duplicación y re-renders | mantenibilidad | **P3** | L | adoptar React Query si se conserva la capa de servicios |

## 2. Resumen por prioridad

```
P0 ..... 12
P1 ..... 16
P2 ..... 21
P3 ..... 11
────────────
Total ... 60
```

## 3. Resumen por categoría

| Categoría | Nº |
|---|---|
| backend | 16 |
| infrastructure / DevOps | 11 |
| frontend | 7 |
| security | 6 |
| testing | 5 |
| dead code | 4 |
| docs | 3 |
| integration | 3 |
| DB | 2 |
| code quality | 3 |
| architecture | 1 |
| observability | 1 |
| performance | 1 |
| i18n | 1 |

## 4. Zonas frágiles — riesgo de modificación (§96)

| Zona | Por qué es frágil |
|---|---|
| `OperationFormPage.tsx` (1 973 LOC) | `switch` de 25 casos, 34 `SearchSelect`, sin tests, alto acoplamiento con `processCatalog` y con 14 catálogos |
| `operations/service.py` (575 LOC) | crea el evento, aplica reglas, genera alertas, construye trazabilidad y audita, todo en un método; ya contiene dos defectos P0 |
| `audit/listeners.py` + `audit/helpers.py` | dos mecanismos que escriben en la misma tabla; tocar uno altera el comportamiento del otro |
| `processCatalog.ts` | fuente única de la taxonomía del producto, consumida por 5 pantallas y sin tests |
| `masters/router.py` `register_crud` | genera 82 endpoints por metaprogramación; un cambio afecta a 19 entidades a la vez |
| `stores/auth.store.ts` + `services/api.ts` | interceptor de refresh + reconstrucción del usuario: origen de la escalada de privilegios |
| 61 filtros `company_id` duplicados | cualquier cambio de política multi-tenant exige tocar 7 servicios |
