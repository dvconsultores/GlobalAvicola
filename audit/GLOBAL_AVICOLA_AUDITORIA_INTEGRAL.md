# GLOBAL AVÍCOLA — AUDITORÍA INTEGRAL END-TO-END

| | |
|---|---|
| **Fecha de auditoría** | 2026-09-02 |
| **Commit auditado** | `bfccdfb` (HEAD, `main`, 2026-07-08 20:35) |
| **Alcance** | repositorio completo: código, base de datos, API, frontend, infraestructura, CI/CD, specs, historial Git |
| **Restricciones aplicadas** | sin modificar código productivo · sin ejecutar pruebas contra la base de datos en la nube · sin deploy · sin escrituras en Git |
| **Documentos anexos** | `audit/01`…`audit/21` |

---

# 1. Resumen ejecutivo

Global Avícola es una plataforma de gestión operativa avícola construida en 15 días (2026-06-23 → 2026-07-08, 171 commits) y **actualmente desplegada en producción** con actualización automática de contenedores.

El sistema tiene **una arquitectura sólida y un modelo de datos impecable**, y a la vez **doce defectos bloqueantes vivos en producción**, ninguno de los cuales fue detectado porque **el proyecto nunca ha ejecutado su propia integración continua**: los workflows de test están configurados solo para `pull_request` y el repositorio tiene **0 pull requests y 0 merges** en 171 commits, mientras cada `push` a `main` publica una imagen que Watchtower despliega en menos de 60 segundos.

La distancia entre lo declarado y lo verificable es el hallazgo transversal. Siete documentos del repositorio declaran el sistema "certificado", "aprobado" o "listo para UAT"; la verificación muestra que registrar la mortalidad diaria devuelve un error 500, que las correcciones no modifican el dato corregido, que no existe ningún control de permisos en el backend y que la "integración SAP" escribe un archivo temporal dentro del contenedor.

**Cobertura funcional E2E real: 21,4 % (12 de 56 requerimientos).**
**Spec Compliance Rate: 23,3 % (7 de 30 features auditadas).**

# 2. Veredicto funcional

# `INTEGRACIÓN INCOMPLETA`

Las piezas existen y en su mayoría son correctas —167 endpoints, 47 tablas, 24 pantallas, 25 tipos de operación—, pero la unión entre ellas falla en puntos críticos: 13 desajustes de contrato FE↔BE, 5 pantallas que no cargan, 2 campos del contrato que el frontend nunca envía y una capa entera de servicios que ninguna página utiliza.

No es "prototipo" (hay dominio profundo, reglas de negocio reales y despliegue productivo), ni "beta funcional" (procesos centrales rotos), ni "parcialmente implementado" (la implementación es amplia; lo que falla es la integración).

# 3. Veredicto Spec Development

# `CUMPLIMIENTO PARCIAL` · Disciplina **NIVEL C — INCONSISTENTE**

Existe evidencia forense inequívoca de especificación previa: las 17 tareas de la Fase 8 se escribieron a las 02:55 del 2026-06-24 y se implementaron a partir de las 03:25 del mismo día. También hay decisiones de alcance documentadas antes del código y una reconciliación honesta entre el estado documental y el código real.

Pero la constitución del proyecto —el documento que en Spec Kit fija las reglas vinculantes— **nunca fue ratificada** (sigue siendo la plantilla con marcadores). Un tercio de las features auditadas están fuera de spec, hay una violación explícita de una regla escrita (la spec prohíbe el modo oscuro; se implementó en 24 commits y se revirtió), el design system obligatorio fue sustituido sin decisión documentada, y las specs se cierran mediante auto-informes generados en el mismo hilo que produjo el código.

# 4. Qué es Global Avícola

Capa operativa auxiliar de **SAP S/4HANA** para el ciclo productivo avícola completo. SAP conserva el control administrativo y contable; Global Avícola gestiona la captura en campo, la revisión, la corrección auditada, la aprobación multinivel y el envío consolidado a SAP, con trazabilidad y auditoría.

**Problema que resuelve:** sustituir el sistema legacy "Lider Pollo" (Flutter + Vue + Node, auditado en `docs/01-legacy-audit.md`) por una plataforma que garantice **calidad del dato antes de que llegue a SAP**, con mobile-first real para el operador de campo y vista ejecutiva para supervisión.

**Cadena productiva cubierta:** Progenitoras (abuelas) → Reproductoras (cría → producción) → Incubación → Engorde. Fuera de alcance v1 (declarado): cadena de aves livianas / ponedoras.

# 5. Arquitectura actual

**Monolito modular** con frontend SPA separado.

- **Backend:** FastAPI async, 11 módulos de dominio (`auth`, `masters`, `lots`, `operations`, `review`, `corrections`, `audit`, `reports`, `dashboard`, `integrations/sap`, `integrations/telegram`), patrón `router → service → models`. No hay capa repositorio (el README la anuncia; no existe).
- **Modelo central:** `OperationalEvent` unificado con discriminador `event_type` (25 valores) + 6 tablas de submovimientos. Sustituye 12+ tablas del legacy. **Es el mejor acierto de diseño del proyecto.**
- **Frontend:** React 19 + Vite, 24 páginas, 36 rutas, catálogo de procesos centralizado (`processCatalog.ts`) como fuente única de la taxonomía de etapas y operaciones.
- **Integración SAP:** Adapter pattern con ABC y DTOs desacoplados — correcto en diseño, sin implementación real.

Desviación arquitectónica principal: la capa `services/` + `hooks/` del frontend (21 módulos, ~600 LOC) **está completamente muerta**; todas las páginas llaman a axios directamente con URLs literales. Es la causa raíz de los 13 desajustes de contrato.

# 6. Infraestructura actual

Docker Compose sobre un host único; PostgreSQL **externo** en IP pública (no forma parte del compose); imágenes en Docker Hub; Nginx sirviendo la SPA y proxy `/api/` al backend; Watchtower actualizando contenedores cada 60 s; contenedor adicional para el bot de Telegram. Sin CDN, sin colas, sin workers, sin cron, sin staging, sin backups, sin monitorización.

# 7. Diagrama arquitectónico

```
   Operador de campo (móvil / Telegram Mini App)      Supervisor / Admin (web)
                        │                                        │
                        └──────────────┬─────────────────────────┘
                                       ▼
                          avicola.globaldv.net  (DNS/TLS: no versionado)
                                       │
        ┌──────────────────────────────┴───────────────────────────────┐
        │  HOST DOCKER                                                  │
        │                                                               │
        │  ┌───────────────────────┐    ┌────────────────────────────┐  │
        │  │ globalavicola-frontend│    │ globalavicola-backend      │  │
        │  │ Nginx 1.27 · SPA      │───▶│ Uvicorn · FastAPI          │  │
        │  │ /api/ → backend:8000  │    │ 167 endpoints /api/v1      │  │
        │  │ :3005→80              │    │ :8002→8000                 │  │
        │  └───────────────────────┘    │  /app/media  ⚠ SIN VOLUMEN │  │
        │                               │  /tmp/sap_exports ⚠ IDEM   │  │
        │  ┌───────────────────────┐    └──────────┬─────────────────┘  │
        │  │ globalavicola-telegram│               │                    │
        │  │ bot (misma imagen)    │               │                    │
        │  └───────────────────────┘               │                    │
        │  ┌───────────────────────┐               │                    │
        │  │ watchtower ⚠ docker.sock, poll 60 s   │                    │
        │  └───────────────────────┘               │                    │
        └──────────────────────────────────────────┼────────────────────┘
                                                   ▼
                                    PostgreSQL (IP pública, externo)
                                    47 tablas · 21 migraciones
                                    ⚠ migraciones NO automatizadas

                    SAP S/4HANA  ✘ NO CONECTADO
                    (ManualSapAdapter escribe JSON en /tmp)
```

# 8. Inventario tecnológico

Ver `audit/02_ARCHITECTURE_AND_INFRASTRUCTURE.md §1`. Resumen: React 19 · Vite 8 · TypeScript 6 · Tailwind 4 · Zustand 5 · react-hook-form + zod · axios · react-i18next · recharts · xlsx + jsPDF · lucide-react · @telegram-apps/sdk // FastAPI · Python 3.11 · SQLAlchemy 2 async · asyncpg · Alembic · Pydantic v2 · PyJWT · passlib/bcrypt · slowapi · aiofiles · pyTelegramBotAPI // PostgreSQL · Docker · Nginx · GitHub Actions · Watchtower // Pytest · Vitest · Playwright.

# 9. Inventario documental

**8 067 líneas** de documentación: 16 documentos en `docs/` (5 761 líneas) + 7 artefactos de Spec Kit (2 306 líneas). Más 20 informes de estado en la raíz y 4 prompts versionados. Más 44 archivos de proceso de negocio del cliente en `Imagen de Procesos Documentado/` (XLSX de formatos AVI-*, manuales Ross/Cobb, capturas del legacy) **no trazados a ningún requerimiento**.

Huecos: `docs/14` no existe; `docs/17-production-checklist.md` está referenciado por la spec y por las tareas y **no existe**; `docs/18-production-runbook.md` (entregable T-090) tampoco.

# 10. Inventario de specs

23 documentos catalogados como `GA-SPEC-001`…`GA-SPEC-023` en `audit/04_SPECS_INVENTORY.md`. **20 de 23 entraron en el mismo "first commit"** junto con el sistema completo.

Calidad: 1 EXCELENTE (`docs/02-functional-spec.md`) · 7 ADECUADAS · 3 INCOMPLETAS · 1 DEFICIENTE (los contratos de API). **Ninguna spec contiene criterios de aceptación verificables por funcionalidad** → `SPEC_PROCESS_DEBT`.

# 11. Requerimientos consolidados

El proyecto **no tenía identificadores de requerimiento**. Se reconstruyeron **56** (`GA-REQ-001`…`GA-REQ-056`) desde los 14 módulos funcionales, los dominios de la spec, las 16 reglas de negocio y los NFR. Tabla completa en `audit/03_REQUIREMENTS_TRACEABILITY.md`.

```
COMPLETO (E2E) ....... 12   (21,4 %)
PARCIAL .............. 28   (50,0 %)
ROTO .................  7   (12,5 %)
DOC_NO_IMPL ..........  5   ( 8,9 %)
BACKEND_ONLY .........  3   ( 5,4 %)
NO_VERIFICABLE .......  1   ( 1,8 %)
MOCK / FRONTEND_ONLY .  0
```

# 12. Matriz maestra de trazabilidad

`audit/03_REQUIREMENTS_TRACEABILITY.md §3`. **Traceability Rate: 16,7 %.**

# 13. Mapa funcional

`audit/07_FUNCTIONAL_MAP.md` — 98 funcionalidades: 33 COMPLETAS · 30 PARCIALES · 16 ROTAS · 1 MOCK · 18 NO IMPLEMENTADAS.

# 14. Mapa de módulos

| Módulo | Estado funcional | Estado Spec Development |
|---|---|---|
| i18n | 🟢 VERDE | 🟢 VERDE |
| Canal Telegram | 🟢 VERDE | 🔴 ROJO (sin spec) |
| Operaciones (captura) | 🟡 AMARILLO | 🟡 AMARILLO |
| Revisión y aprobación | 🟡 AMARILLO | 🟢 VERDE |
| Maestros | 🟡 AMARILLO | 🟢 VERDE |
| Reportes / KPIs | 🟡 AMARILLO | 🟡 AMARILLO |
| Dashboard | 🟡 AMARILLO | 🟡 AMARILLO |
| Auditoría | 🟡 AMARILLO | 🟡 AMARILLO |
| Lotes | 🔴 ROJO | 🟡 AMARILLO |
| Integración SAP | 🔴 ROJO | 🟡 AMARILLO |
| Seguridad / RBAC | 🔴 ROJO | 🔴 ROJO |
| Administración (usuarios/roles) | 🔴 ROJO | 🟡 AMARILLO |
| Trazabilidad generacional | 🔴 ROJO | 🔴 ROJO (code-before-spec) |
| Notificaciones | 🔴 ROJO | 🔴 ROJO (no implementado) |
| Design system | 🟡 AMARILLO | 🔴 ROJO (spec violada) |

# 15. Mapa de procesos

15 procesos identificados (`audit/06_PROCESS_COVERAGE.md`).

```
Procesos identificados ......... 15
100 % cubiertos ................  0
Parcialmente cubiertos ......... 12
Manuales .......................  2
No implementados ...............  1
```

# 16. Procesos 100 % cubiertos

# NINGUNO

Ningún proceso satisface la cadena `Entrada → ejecución → persistencia → salida → estado final` sin un defecto confirmado. La lista se deja deliberadamente vacía: incluir procesos parciales falsearía el resultado.

Los cuatro más cercanos, con el paso exacto que los bloquea:

| Proceso | Pasos correctos | Paso bloqueante |
|---|---|---|
| Revisión → Aprobación | 8/10 | la corrección no aplica el valor; BR-14 eludible |
| Engorde | 10/11 | `mortality_recording` → 500; cierre de lote en pantalla rota |
| Consolidación → SAP | 5/6 | el "envío" escribe un archivo efímero en `/tmp` |
| Incubación | 7/8 | trazabilidad generacional auto-referencial |

# 17. Procesos parciales

P-01 Progenitoras Cría · P-02 Progenitoras Producción · P-03 Reproductoras Cría · P-04 Reproductoras Producción · P-05 Incubación · P-06 Engorde · P-07 Revisión/Aprobación · P-08 Consolidación SAP · P-09 Auditoría · P-10 Trazabilidad generacional · P-12 Maestros · P-13 Usuarios/roles · P-15 Reportes.

# 18. Procesos manuales

1. **Activación manual de lotes / saldos iniciales** (P-11): endpoint completo, `opening_balances` con 22 columnas, **sin ninguna pantalla**. Requisito de implantación crítico —dar de alta los lotes en curso— hoy solo ejecutable por API o SQL.
2. **Registro efectivo en SAP**: el sistema produce un archivo JSON que nadie transporta; el asiento en SAP sigue siendo manual y no hay procedimiento documentado.

# 19. Procesos no implementados

**P-14 Notificaciones y alertas.** De los 6 tipos exigidos por `docs/02 §3.14`, ninguno está implementado como notificación. Existen 3 alertas en base de datos (mortalidad, temperatura, humedad), de las cuales la de mortalidad **falla con 500**. No hay canal de envío (correo, push, Telegram) en ninguna parte del código, pese a que hay credenciales SMTP configuradas.

# 20. Frontend

`audit/08_FRONTEND_AUDIT.md`. 108 fuentes, 15 226 LOC, 24 pantallas.

```
Integradas sin defecto confirmado .. 10
Parciales .......................... 9
Rotas .............................. 5   (LotDetailPage, ReviewDetail, CorrectionForm, UsersPage, MyPendingPage)
Mock / datos falsos ................ 0
```

TypeScript compila sin errores. ESLint: 5 errores, 431 avisos. 0 `console.log`, 0 mocks, 0 TODO. i18n con paridad total. Archivo mayor: `OperationFormPage.tsx` con 1 973 LOC y un `switch` de 25 casos.

# 21. Backend

`audit/09_BACKEND_AUDIT.md`. 11 módulos, 14 796 LOC, **168 operaciones** de API. Un solo `TODO` en todo el backend — y es el que decide si el producto se integra con SAP.

12 hallazgos, de los cuales 6 son P0: `NameError` en mortalidad, correcciones que no aplican, RBAC no aplicado, refresh que degrada la identidad, BR-14 eludible, trazabilidad auto-referencial.

# 22. Integración FE ↔ BE

`audit/10_FRONTEND_BACKEND_MATRIX.md`.

```
Endpoints backend ........................ 167
Consumidos por el frontend ............... 133  (79,6 %)
Huérfanos ................................  34  (20,4 %)
Llamadas a rutas inexistentes ............   0
Llamadas con contrato incompatible .......  13
   · límite fuera de rango (422) .........   6
   · parámetro inexistente (silencioso) ..   7
Campos del contrato nunca enviados .......   2  (sap_document_ref, idempotency_key)
```

**Ninguna pantalla llama a una ruta que no exista.** Todos los fallos son de forma del contrato — exactamente lo que un *contract testing* habría impedido.

# 23. APIs

`audit/11_API_INVENTORY.md` — las 168 operaciones, una por fila, con módulo, autenticación, permiso exigido (**ninguno en las 168**), consumidor y estado.

Módulo con más huérfanos: **Approval Steps, 5 de 5 (100 %)** — la configuración de aprobación multinivel, diferenciador declarado del producto, no tiene interfaz ni se aplica.

# 24. Base de datos

`audit/12_DATABASE_MODEL.md`. 47 tablas, 21 migraciones, 66 índices, 105 claves foráneas.

**Verificación programática: 0 tablas y 0 columnas de deriva entre los modelos SQLAlchemy y las migraciones Alembic.** Cadena íntegra con un único head. Es el punto más sólido del proyecto.

Problemas: `reversals` huérfana (BR-16 sin implementar), `approval_steps` sin enforcement, `opening_balances` sin UI, `egg_storage` solo de escritura, 2 restricciones únicas en 47 tablas, 0 `CHECK` constraints, riesgo de N+1 por 8 relaciones `selectin` en `OperationalEvent`.

**9 de 21 migraciones (43 %) modifican el esquema sin requisito ni spec** → `UNTRACED_SCHEMA_CHANGE`. Una de ellas relaja una restricción de integridad sin decisión documentada.

# 25. Modelo de dominio

Diagrama ER en `audit/12_DATABASE_MODEL.md §4`. Entidades centrales: `Company → Farm → House`, `Lot → LotPhase / OpeningBalance`, `OperationalEvent` + 6 submovimientos, cadena de revisión (`ReviewBatch`, `ApprovalAction`, `CorrectionLog`), cadena SAP (`SapReference`, `ConsolidatedMovement`, `SapSyncJob`, `SapPayload`, `SapResponse`), trazabilidad (`EggBatch`, `ChickBatch`) y `AuditLog`.

**Máquina de estados** de 13 valores, con 3 estados inalcanzables (`DRAFT`, `SAP_CONFIRMED`, `SAP_ERROR`) y dos saltos indebidos (`IN_REVIEW → APPROVED` sin segregación; aprobación admitida desde `IN_REVIEW`).

**Nomenclatura de estados coherente** entre spec, backend, base de datos y frontend. La divergencia real está en la **taxonomía de etapas**: la spec define 5 dominios y el frontend implementa 6 `StageKey`.

# 26. Roles y permisos

`audit/13_ROLES_AND_SECURITY.md`. La spec define 11 roles; los seeds crean 6 (+7 de pruebas). Faltan Administrador de Empresa, Veterinario y Consulta/Reportes.

**La matriz de permisos es puramente documental.** El modelo `Permission` con 9 acciones se puebla y **no se consulta en ningún endpoint**, salvo para deducir `is_super_admin`. El frontend solo distingue móvil/web. El prop `roles` de `ProtectedRoute` contiene lógica sin sentido y nunca se usa.

# 27. Seguridad

```
P0 CRÍTICO ....  5
P1 ALTO .......  8
P2 MEDIO ......  5
P3 BAJO .......  3
```

P0: ausencia total de autorización · escalada de privilegios por refresh · fuga de aislamiento multi-compañía · credenciales de administrador publicadas con rate limiting apagado · elusión de la segregación de funciones.

**Vectores evaluados y NO encontrados** (resultado positivo): inyección SQL (100 % ORM, 0 SQL crudo), XSS (0 `dangerouslySetInnerHTML`, 0 `eval`), secretos en el historial de Git (ninguno), path traversal en subidas (mitigado), secretos por defecto (el arranque aborta si detecta `change_me`). Cabeceras de seguridad completas.

# 28. Integraciones externas

`audit/14_EXTERNAL_INTEGRATIONS.md`.

```
CONFIGURADA ...... 4   (Telegram bot, Telegram SDK, Docker Hub, PostgreSQL)
PARCIAL .......... 1   (SAP: modelo y bitácora sí, transporte no)
MOCK ............. 1   (SAP connection-check siempre true)
NO CONFIGURADA ... 1   (SAP real)
NO IMPLEMENTADA .. 1   (SMTP / notificaciones)
ROTA ............. 1   (mock_adapter.py no compila)
```

La "integración SAP a nivel de operación" declarada en `CERTIFICACION_FUNCIONAL.md` (14 operaciones) es **`FRONTEND_ONLY`**: el selector guarda la orden en un JSONB libre y el campo tipado `sap_document_ref` nunca se envía, dejando inertes BR-11, BR-18 y el reporte comparativo.

# 29. Deployment

`push` a `main` → GitHub Actions construye y publica `:latest` en Docker Hub → Watchtower detecta el cambio en ≤ 60 s y recrea los contenedores. **Sin tests, sin lint, sin aprobación, sin migraciones, sin rollback documentado, sin volúmenes persistentes.**

# 30. Ambientes

`development` (compose de desarrollo con HMR y autoreload) y `production`. **No existe staging**, pese a que T-084 lo exige antes de producción. El `.env` de desarrollo apunta a la misma base de datos en la nube.

# 31. CI/CD

5 workflows. Los 2 de calidad (`backend-ci`, `frontend-ci`) solo se disparan en `pull_request`; **el repositorio tiene 0 pull requests**. Los 2 de publicación se disparan en `push` a `main`. El quinto es manual.

Además, aunque se ejecutaran: el job de backend levanta un Postgres vacío **sin migraciones ni seeds** (todos los tests fallarían) y el de lint fallaría por los 5 errores de ESLint.

# 32. Testing

`audit/15_TESTING_STATUS.md`.

```
Tests encontrados ................ 217
Tests ejecutados ................. 61
PASS ............................. 61
FAIL ............................. 0
FAIL confirmado estáticamente .... 1   (test_operations.py espera 24 tipos de evento; hay 25)
BLOCKED_EXTERNAL ................. 76  (backend: requiere BD desechable)
NO EJECUTADOS .................... 80  (E2E Playwright)
```

**Ninguno de los 12 bloqueadores P0 está cubierto por un test que se ejecute.** `test_f8c_business_rule_mortality_exceeds_balance` habría detectado el fallo de mortalidad — si alguna vez se hubiera ejecutado.

1 065 LOC de tests E2E en `tests/` de la raíz **no tienen configuración de Playwright** que los ejecute: código muerto.

# 33. Calidad de código

| Dimensión | Evaluación |
|---|---|
| Modularidad | **buena** en backend (11 módulos de dominio); **débil** en frontend (`OperationFormPage` de 1 973 LOC) |
| Cohesión | media: `OperationsService.create_event` crea, valida, alerta, traza y audita en un solo flujo |
| Acoplamiento | bajo entre módulos de backend; **alto** entre páginas de frontend y URLs literales |
| Duplicación | **61 filtros `company_id` idénticos** en 7 servicios |
| Complejidad | `switch` de 25 casos en el formulario; método `create_event` de ~70 líneas con 5 responsabilidades |
| Lógica de negocio en el frontend | validación ±10 % contra orden SAP calculada en el cliente y **volcada a un campo de texto libre** |
| Consultas directas en controladores | sí, en `lots/router.py` (traceability) y `operations/router.py` (evidencias) |
| Tipado | backend fuerte (Pydantic v2 + Mapped); frontend débil (**393 `any`**) |
| Naming | consistente y en inglés en el código; mensajes de negocio en español fijo |
| Estilo | **incoherente**: gran parte de `src/pages` con indentación de 1 espacio por ediciones mecánicas masivas; sin Prettier |
| Manejo de errores | correcto en backend (`HTTPException` con detalle); en frontend, varios `catch` silenciosos |

**No se recomienda microservicios ni reescritura.** La arquitectura actual es adecuada al problema.

# 34. Código muerto

~1 800 LOC identificadas:

| Elemento | LOC | Motivo |
|---|---|---|
| `frontend/src/services/` (11 módulos) + `hooks/` (9) | ~600 | ninguna página los importa |
| `tests/` de la raíz (4 archivos) | 1 065 | sin `playwright.config.ts` en la raíz |
| `SignaturePad.tsx` + su test | 224 | 0 usos en páginas |
| `SidebarSubmenu.tsx` | 145 | 0 usos |
| `theme.store.ts` + `DarkModeToggle.tsx` + lectura de `theme-storage` | ~70 | funcionalidad eliminada, restos vivos |
| `mock_adapter.py` | 101 | **no compila** (`ModuleNotFoundError`) |
| `MockSapAdapter` en `adapter.py` | ~50 | nunca instanciado |
| Tabla `reversals` | — | 0 referencias |
| `ProcessFlowVisualizer`, `OperationActionCard`, `ProcessCard` | ~240 | solo exportados por el barrel |
| Endpoints huérfanos | 34 | sin consumidor |

**Nada se eliminó durante la auditoría.**

# 35. Hardcoding y mocks

**0 mocks de datos y 0 arrays falsos** en todo el código — hallazgo positivo y poco habitual.

Hardcoding real, clasificado:

| Elemento | Clasificación |
|---|---|
| Curvas térmicas Ross/Cobb (`thermalCurves.ts`) | **legítimo** — datos técnicos de referencia |
| Rangos de incubadora y nacedora | **legítimo** |
| Umbrales de alerta 3 % / 8 %, temperatura 18-35 °C, humedad 40-90 % | **deuda** — `docs/02 §3.14` exige umbral configurable |
| `lotId = 2` por defecto en `ReportsPage` | **deuda** — inusable |
| `ALL_EVENT_TYPES`: 25 etiquetas en español fijo en el backend | **deuda** (rompe i18n) |
| `quick_actions` del dashboard con texto español y emojis | **deuda** (rompe i18n y el design system) |
| Cabeceras de exportación Excel/PDF en español fijo | **deuda** |
| Contraseñas de seeds (`admin123`, etc.) | **riesgo P0** |
| Credenciales de BD y SMTP en `.env` locales | **secreto potencial** (no versionado) |
| Ventana de período cerrado (90 días) | **config** — debería ser parámetro de compañía |

# 36. Observabilidad

Sin logging estructurado, sin correlation ID, sin captura de errores, sin métricas, sin dashboards, sin alertas, sin tracing, sin backups. Solo `GET /health` y el `AuditLog` de negocio.

**¿Se puede diagnosticar una falla productiva? No.** El error 500 de mortalidad lleva meses en producción y solo sería visible como un mensaje genérico en el teléfono del operador.

# 37. Performance

| Hallazgo | Detalle |
|---|---|
| N+1 potencial | `OperationalEvent` con **8 relaciones `lazy="selectin"`**: `GET /operations?limit=100` dispara ~9 consultas y materializa todos los submovimientos |
| Consulta pesada | `_get_mortality_trend` agrupa 8 semanas con `extract()` sin índice funcional |
| Bucles con consultas | `batch_approve`/`batch_reject` ejecutan `approve()` en bucle (1 SELECT + 2 INSERT por evento) |
| Paginación | presente en todos los listados; **falta el total** en maestros, lots, operations y users |
| Filtro por cliente | `OperationListPage` trae 100 eventos y filtra por etapa en el navegador |
| Bundle | code splitting dinámico correcto para `xlsx` y `jspdf`; `chunkSizeWarningLimit` elevado a 2000 |
| Fuentes | Inter autoalojada (@fontsource) — bien |
| Caché de datos | **ninguna**: cada pantalla refetch en `useEffect` |

# 38. Deuda técnica

`audit/16_TECHNICAL_DEBT.md` — **60 elementos** (`GA-TD-001`…`GA-TD-060`).

```
P0 ..... 12
P1 ..... 16
P2 ..... 21
P3 ..... 11
```

# 39. Auditoría Spec Development

`audit/05_SPEC_DEVELOPMENT_COMPLIANCE.md`. 30 features auditadas con marcas temporales de Git.

# 40. Código sin spec

**12 funcionalidades con cero menciones** en `spec.md` y en los 16 documentos de `docs/`: `egg_reception_classification`, `hatchery_purpose`, `egg_storage`, motor de alertas, evidencias adjuntas, `SearchSelect` (34 instancias), Telegram Mini App y bot, tabla `reversals`, `bird_transfer`, `SignaturePad`, reglas BR-17/18/19, selector de compañía.

# 41. Code-before-spec

**Trazabilidad generacional**: implementada el 2026-06-24 a las 03:51 (`2d06024`); la sección `spec.md §4.9` aparece el mismo día a las **18:38** (`ac125b2`). Delta: 14 h 47 min. Documentada por segunda vez 3 días después.
**Sistema de auditoría automática**: el *qué* estaba especificado desde el inicio; el *cómo* (listeners + helpers) se documentó tras implementarlo el 2026-06-29.

# 42. Out-of-spec

| # | Regla escrita | Qué se hizo |
|---|---|---|
| 1 | `spec.md §6.3`: "**Sin dark mode** — diseño corporativo claro siempre" | 24 commits de modo oscuro (2026-06-25 → 06-28) y reversión total |
| 2 | `spec.md §6.3`: paleta `#1E3A5F` / `#2563EB` / `#3B82F6` | sustituida por una paleta teal "Atenea" copiada de otro proyecto; spec nunca actualizada |
| 3 | `spec.md §6.3`: "lucide-react exclusivamente, **sin emojis** en UI de producción" | emojis en 3 archivos de frontend y 1 de backend |
| 4 | `spec.md §6.1`: bottom navigation de 5 elementos | implementados 3 |
| 5 | `spec.md §7`: "sin hardcodear textos" | 25 etiquetas de evento y las acciones rápidas en español fijo desde el backend |
| 6 | `spec.md §4.4/§4.6/§4.7`: `egg_classification` como operación propia | fusionada en `egg_collection` sin actualizar la spec |

**Out-of-Spec Rate: 33,3 %.**

# 43. Spec drift

| Artefacto | Nivel |
|---|---|
| Contratos de API (`specs/.../api-contract.md`, `docs/06`) | **CRITICAL_DRIFT** |
| Design system (`docs/11`, `spec.md §6.3`) | **CRITICAL_DRIFT** |
| `README.md` (estado del proyecto y estructura del backend) | **CRITICAL_DRIFT** |
| `data-model.md` | HIGH_DRIFT |
| Taxonomía de etapas y tipos de evento | HIGH_DRIFT |
| Numeración de reglas BR | MEDIUM_DRIFT |

# 44. Specs incompletas

`data-model.md` (desactualizada), `api-contract.md` y `docs/06` (fracción de 167 endpoints), `07-qa-plan.md` (nunca aplicado), `quickstart.md` (comandos rotos).

# 45. Specs no implementadas

RBAC granular · reverso post-SAP (BR-16) · notificaciones (6 tipos) · aprobación multinivel con `ApprovalStep` · alerta de peso fuera de curva · cobertura de tests >80/70 % · recuperación de contraseña, MFA y revocación · `RealSapAdapter` (T-085) · `docs/17` y `docs/18`.

# 46. Specs contradictorias

`docs/11-ui-ux-design-system.md` + `spec.md §6.3` frente a la implementación (paleta y dark mode) → `REQUIREMENT_CONFLICT` resuelto de facto por el código, sin decisión documentada. Segundo caso: la numeración BR entre `spec.md §5` y `validators.py`.

# 47. Specs obsoletas

`GA-SPEC-004` (data-model), `GA-SPEC-006` (quickstart), `GA-SPEC-007` y `GA-SPEC-014` (contratos de API), `GA-SPEC-019` (design system, en su parte de paleta y dark mode).

# 48. Specs cerradas sin validación

6 casos documentados en `audit/05 §3.7`: "16/16 hallazgos cerrados, APROBADO" · "96/100" · "71 ops al 100 %, listo para UAT" · "29/29 rutas funcionales" (dos de ellas inexistentes) · "Dark Mode entregado" (eliminado 4 días después) · "todos los tests pasando" (nunca ejecutados en CI). → `SPEC_CLOSED_WITHOUT_VERIFICATION`.

# 49. Desviaciones de base de datos y arquitectura

9 migraciones sin spec (`UNTRACED_SCHEMA_CHANGE`), una de ellas relajando integridad (`operational_events.lot_id` → nullable). 5 refactores mayores sin spec (`UNSPECIFIED_REFACTOR`): identidad visual, modo oscuro, navegación móvil, `SearchSelect`, reorganización de rutas.

**No se detectó ninguna `ARCHITECTURAL_SPEC_VIOLATION` del tipo "la spec dice PostgreSQL y se usó localStorage".** La arquitectura implementada coincide con la especificada; `localStorage` solo guarda tema, idioma, estado del sidebar y —justificadamente— el token dentro de la Mini App de Telegram.

# 50. Deuda Spec Development

`audit/17_SPEC_DEVELOPMENT_DEBT.md` — **16 elementos** (`GA-SPD-DEBT-001`…`016`): 4 P0, 7 P1, 5 P2.

# 51. Discrepancias documentación vs realidad

13 discrepancias tabuladas en `audit/19_PRODUCTION_GAPS.md §4`. La más grave: `README.md` afirma que "no se ha iniciado codificación funcional" con el sistema desplegado en producción.

# 52. Implementaciones sin documentación

11 grupos clasificados en `audit/19_PRODUCTION_GAPS.md §5`: features no documentadas en uso (5), canal de producto nuevo (Telegram), tipos y campos de dominio (3), datos capturados sin uso (`egg_storage`), código abandonado (6 elementos) y reglas de negocio sin requisito (BR-17/18/19).

# 53. Estado por módulo

```
MÓDULO: OPERACIONES (captura de campo)
Requerimientos: 8   E2E completos: 3   Parciales: 4   Rotos: 1   Mocks: 0
Frontend 85 % · Backend 90 % · Integración 70 % · DB 100 % · Testing 15 % · E2E 38 %
Specs: 5   Spec compliant: 2   Out-of-spec: 2   Code-before-spec: 0   Drift: 1
Estado funcional: AMARILLO   ·   Estado Spec Development: AMARILLO

MÓDULO: REVISIÓN Y APROBACIÓN
Requerimientos: 6   E2E completos: 2   Parciales: 2   Rotos: 2   Mocks: 0
Frontend 60 % · Backend 85 % · Integración 55 % · DB 100 % · Testing 20 % · E2E 33 %
Specs: 3   Spec compliant: 2   Out-of-spec: 0   Code-before-spec: 0   Drift: 0
Estado funcional: AMARILLO   ·   Estado Spec Development: VERDE

MÓDULO: LOTES Y TRAZABILIDAD
Requerimientos: 5   E2E completos: 0   Parciales: 2   Rotos: 2   No implementados: 1
Frontend 40 % · Backend 90 % · Integración 30 % · DB 100 % · Testing 0 % · E2E 0 %
Specs: 2   Spec compliant: 1   Out-of-spec: 0   Code-before-spec: 1   Drift: 0
Estado funcional: ROJO   ·   Estado Spec Development: AMARILLO

MÓDULO: INTEGRACIÓN SAP
Requerimientos: 6   E2E completos: 1   Parciales: 3   Rotos: 2   Mocks: 1
Frontend 70 % · Backend 75 % · Integración 20 % · DB 100 % · Testing 0 % · E2E 17 %
Specs: 2   Spec compliant: 0   Out-of-spec: 0   Retro-documentadas: 1   Drift: 1
Estado funcional: ROJO   ·   Estado Spec Development: AMARILLO

MÓDULO: SEGURIDAD Y ACCESO
Requerimientos: 6   E2E completos: 1   Parciales: 1   Rotos: 1   No implementados: 3
Frontend 40 % · Backend 35 % · Integración 40 % · DB 100 % · Testing 10 % · E2E 17 %
Specs: 2   Spec compliant: 0   No implementadas: 1   Drift: 0
Estado funcional: ROJO   ·   Estado Spec Development: ROJO

MÓDULO: MAESTROS
Requerimientos: 2   E2E completos: 0   Parciales: 2   Rotos: 0
Frontend 63 % (12/19 entidades) · Backend 85 % · Integración 67 % · DB 100 % · Testing 10 % · E2E 0 %
Specs: 1   Spec compliant: 1   Out-of-spec: 0   Drift: 0
Estado funcional: AMARILLO   ·   Estado Spec Development: VERDE

MÓDULO: REPORTES, KPI Y DASHBOARD
Requerimientos: 5   E2E completos: 1   Parciales: 3   Rotos: 1
Frontend 65 % · Backend 90 % · Integración 60 % · DB 100 % · Testing 5 % · E2E 20 %
Specs: 2   Spec compliant: 1   Out-of-spec: 1   Drift: 0
Estado funcional: AMARILLO   ·   Estado Spec Development: AMARILLO

MÓDULO: AUDITORÍA
Requerimientos: 2   E2E completos: 0   Parciales: 2   Rotos: 0
Frontend 60 % · Backend 80 % · Integración 55 % · DB 100 % · Testing 15 % · E2E 0 %
Specs: 2   Spec compliant: 0   Code-before-spec: 1   Drift: 0
Estado funcional: AMARILLO   ·   Estado Spec Development: AMARILLO

MÓDULO: NOTIFICACIONES Y ALERTAS
Requerimientos: 2   E2E completos: 0   Parciales: 1   No implementados: 1
Frontend 30 % · Backend 40 % · Integración 30 % · DB 100 % · Testing 0 % · E2E 0 %
Specs: 1   Spec compliant: 0   Implementado sin spec: 1
Estado funcional: ROJO   ·   Estado Spec Development: ROJO

MÓDULO: i18n Y EXPERIENCIA DUAL
Requerimientos: 3   E2E completos: 2   No verificables: 1
Frontend 100 % · Backend n/a · Integración 100 % · Testing 25 % · E2E 67 %
Specs: 3   Spec compliant: 2   Out-of-spec: 1 (design system)
Estado funcional: VERDE   ·   Estado Spec Development: AMARILLO
```

# 54. Estado por spec

`audit/04_SPECS_INVENTORY.md §2` — 23 specs con fecha de primer commit, última modificación, estado documental y estado de implementación.

# 55. Estado por requerimiento

`audit/03_REQUIREMENTS_TRACEABILITY.md §1` — los 56 requerimientos, uno por fila.

# 56. Métricas funcionales

```
Cobertura funcional E2E ................ 12/56 = 21,4 %
Implementación sustancial .............. 40/56 = 71,4 %
Endpoints consumidos ................... 133/167 = 79,6 %
Pantallas sin defecto confirmado ....... 10/24 = 41,7 %
Procesos 100 % cubiertos ...............  0/15 = 0 %
Deriva ORM ↔ migraciones ............... 0 %
Paridad i18n ........................... 865/865 = 100 %
Tests ejecutados que pasan ............. 61/61 = 100 %
Cobertura de tests frontend ............ ~4 %
```

# 57. Métricas Spec Development

```
Spec Compliance Rate ...... 7/30  = 23,3 %
Traceability Rate ......... 5/30  = 16,7 %
AC Coverage Rate .......... 12/30 = 40,0 %
Spec Test Coverage Rate ... 2/30  =  6,7 %
Out-of-Spec Rate .......... 10/30 = 33,3 %
Disciplina ................ NIVEL C — INCONSISTENTE
```

# 58. Bloqueadores P0

12, detallados en `audit/19_PRODUCTION_GAPS.md §1`:
mortalidad → 500 · correcciones que no aplican · sin RBAC · escalada por refresh · 5 pantallas rotas por 422 · evidencias efímeras · SAP simulado activado en producción · credenciales públicas sin rate limit · cambio de contraseña que no funciona · BR-14 eludible · trazabilidad auto-referencial · ninguna puerta de calidad.

# 59. Riesgos P1

16, en `audit/19_PRODUCTION_GAPS.md §2`: migraciones no automatizadas · fuga multi-compañía · Super Admin ciego · sin logout · observabilidad nula · sin backups · CI de backend inejecutable · BR-11/BR-12 inertes · BR-06 anulada · 8 catálogos sin edición · rate limit apagado · auditoría duplicada · multinivel no operativo · BD pública con superusuario · activación manual sin UI · filtros inertes.

# 60. Deuda P2 / P3

21 elementos P2 y 11 P3 en `audit/16_TECHNICAL_DEBT.md`.

# 61. Quick wins

12 acciones de alto impacto y baja complejidad en `audit/20_MASTER_ROADMAP.md`. Ninguna es cosmética. Las tres primeras: importar `get_current_bird_balance` (desbloquea la operación diaria más frecuente), añadir `validate_segregation` a `complete_review` (cierra la elusión de BR-14) y activar CI en `push` (primera puerta de calidad del proyecto).

# 62. Baseline vigente recomendado

**Baseline documental vigente:** `specs/global-avicola/spec.md` @ `cd64a17` (478 líneas) complementado por `docs/02-functional-spec.md`.
**Pero no gobierna la implementación actual.**

**Recomendación:** publicar un **baseline v1.1** que absorba, mediante retro-specs justificadas y fechadas (marcadas `RETROSPECTIVE SPEC`, §108), las 12 funcionalidades sin spec y las 6 desviaciones out-of-spec — **sin reescribir la historia**. El baseline v1.1 debe incluir:
1. Taxonomía canónica de etapas y tipos de evento (reconciliando los 6 `StageKey` con los 5 dominios de la spec y resolviendo `egg_classification` / `egg_reception_classification`).
2. Tabla única de reglas de negocio BR-01…BR-19 con identificadores coherentes.
3. Design system real (ADR de cambio de identidad).
4. Alcance del canal Telegram.
5. Contrato de API generado (`openapi.json` versionado).
6. Constitución ratificada.

# 63. Roadmap maestro

`audit/20_MASTER_ROADMAP.md` — 76 pasos en 9 fases, cada uno con ID de deuda, prioridad, dependencia, complejidad y criterio de aceptación.

# 64. Orden recomendado de implementación

```
FASE 0  Contención        pasos 1-8    CI, despliegue, credenciales, SAP, volúmenes, migraciones, auditoría de datos
FASE 1  Bloqueadores P0   pasos 9-16   mortalidad, BR-14, 422, correcciones, contraseña, refresh, trazabilidad
FASE 2  Autorización      pasos 17-23  RBAC, aislamiento, logout, auditoría de seguridad
FASE 3  Cierre funcional  pasos 24-36  SAP ref, idempotencia, maestros, filtros, multinivel, activación manual
FASE 4  Spec Development  pasos 37-47  constitución, AC, retro-specs, baseline v1.1
FASE 5  Testing           pasos 48-54  CI backend, regresión P0, contract testing, E2E
FASE 6  Seguridad         pasos 55-60
FASE 7  Observabilidad    pasos 61-67
FASE 8  Deuda             pasos 68-76
```

# 65. Criterios para declarar Global Avícola completo

17 criterios verificables, uno por línea, en `audit/19_PRODUCTION_GAPS.md §6`. **Ninguno se cumple hoy.**

# 66. Política futura Spec Development

```
                    NO SPEC = NO DEVELOPMENT

REQUIREMENT → SPEC → REVIEW → AC → TASKS → IMPLEMENTATION → TEST → VALIDATION → CLOSE
```

Controles que deben impedir cambios futuros sin spec:

1. **Constitución ratificada** con la regla y sus excepciones explícitas.
2. **Rama `main` protegida**: prohibida la escritura directa; PR obligatorio.
3. **CI en `push` y en `pull_request`**, bloqueante: lint + typecheck + tests + contract testing.
4. **Plantilla de PR** que exija el identificador de spec y de AC que autoriza el cambio.
5. **Migraciones con la spec citada en el docstring**; CI que rechace las que no la citen.
6. **Cierre de spec solo con evidencia**: test verde en CI + revisión por una persona distinta de quien implementó.
7. **Prohibida la auto-certificación** por el mismo agente o hilo que produjo el código.
8. **Excepción de hotfix**: permitida con spec retroactiva en menos de 24 h, marcada `RETROSPECTIVE SPEC` con fecha real y motivo.
9. **`openapi.json` y ERD regenerados en cada release** y versionados, para que los contratos no puedan derivar en silencio.

# 67. Conclusión técnica

Global Avícola es **un buen sistema mal terminado, y peor gobernado**.

Lo construido es sustancialmente correcto: el modelo de evento unificado es un acierto de diseño que resuelve la fragmentación del legacy; el esquema de base de datos no tiene ni una sola desviación respecto a sus migraciones sobre 47 tablas; las reglas de negocio están implementadas con cálculos de saldo correctos; la internacionalización es completa; el adapter de SAP está bien aislado; no hay mocks, ni datos falsos, ni SQL crudo, ni un solo `console.log`.

Lo que falla no es el diseño sino **el cierre y la verificación**. Doce defectos bloqueantes conviven en producción con siete documentos que declaran el sistema certificado. La causa raíz es única y está fechada: el 2026-06-24, el commit `9004f3a` movió la integración continua a `pull_request` en un repositorio que nunca ha tenido un pull request. Desde ese momento, todo commit llegó a producción sin lint, sin typecheck y sin tests, y la única verificación disponible pasó a ser la auto-certificación del propio agente que escribía el código.

Metodológicamente, el proyecto **sí supo hacer Spec Development** —la Fase 8 lo demuestra con un delta de 30 minutos entre la tarea y su implementación— y **dejó de hacerlo** cuando el trabajo pasó a guiarse por prompts de rediseño de interfaz. La constitución vacía es el símbolo exacto del problema: se instaló el marco, se usaron sus plantillas, y nunca se ratificó la regla que lo hacía vinculante.

La recomendación es inequívoca: **no reescribir**. Restablecer primero la puerta de calidad, reparar los doce bloqueadores —la mayoría de complejidad XS o S—, implementar la autorización, y solo entonces regularizar la trazabilidad metodológica. Con eso, Global Avícola pasa de "integración incompleta" a un producto operable en un plazo corto, porque **la parte difícil ya está construida**.

# 68. Anexos de evidencia

`audit/21_EVIDENCE_INDEX.md` — 27 comandos ejecutados, comandos deliberadamente no ejecutados y su motivo, e índice de evidencia por hallazgo con ruta y línea.

---
---

# DASHBOARD NUMÉRICO

```
GLOBAL AVÍCOLA — ESTADO REAL
Commit auditado: bfccdfb (2026-07-08)   ·   Auditoría: 2026-09-02

================================
REQUERIMIENTOS
================================

Requerimientos consolidados:            56
E2E completos:                          12
Parciales:                              28
No implementados:                        5
Rotos:                                   7
Mocks:                                   0
No verificables:                         1
Solo backend:                            3

Cobertura funcional E2E:              21,4 %   (12/56)
Implementación sustancial:            71,4 %   (40/56)

================================
PROCESOS
================================

Procesos identificados:                 15
Procesos 100 % cubiertos:                0
Procesos parciales:                     12
Procesos manuales:                       2
Procesos no implementados:               1

================================
FRONTEND
================================

Pantallas encontradas:                  24   (36 rutas funcionales)
Pantallas integradas:                   10
Pantallas parciales:                     9
Mocks/hardcoded:                         0
Pantallas rotas:                         5

Archivos fuente:                       108
Líneas de código:                   15 226
Typecheck:                            PASS
ESLint:              5 errores / 431 avisos

================================
BACKEND
================================

Endpoints encontrados:                 167   (+1 /health)
Endpoints utilizados:                  133
Endpoints huérfanos:                    34
Endpoints con defecto confirmado:       14
Endpoints con control de permisos:       0

Módulos de dominio:                     11
Líneas de código:                   14 796
TODO / FIXME / HACK:                 1 / 0 / 0

================================
DATABASE
================================

Entidades:                              47
Migraciones:                            21   (1 head, 1 base, cadena íntegra)
Deriva ORM ↔ migraciones:                0
Tablas sin uso:                          1   (reversals)
Tablas de uso parcial:                   3   (permissions, approval_steps, egg_storage)
Índices:                                66
Restricciones únicas:                    2
CHECK constraints:                       0
Migraciones sin spec:                    9   (43 %)

================================
TESTING
================================

Tests encontrados:                      217
Tests ejecutados:                        61
PASS:                                    61
FAIL:                                     0
FAIL confirmado estáticamente:            1
BLOCKED_EXTERNAL:                        76
NO EJECUTADOS:                           80
Cobertura frontend estimada:            ~4 %
Ejecuciones históricas en CI:             0

================================
SPEC DEVELOPMENT
================================

Specs encontradas:                       23
Specs vigentes:                          17
Specs obsoletas:                          5
Specs contradictorias:                    1
Specs referenciadas inexistentes:         2

Features auditadas:                      30
SPEC_COMPLIANT:                           7
SPEC_PARTIAL:                             9
Sin spec (IMPLEMENTED_WITHOUT_SPEC):      7
Code-before-spec:                         1
Spec retro-documentada:                   1
Out-of-spec:                              3
Sin trazabilidad (commit inicial):        2
Spec drift:                               7
Specs cerradas sin validación:            6

Spec Compliance Rate:                 23,3 %
Traceability Rate:                    16,7 %
AC Coverage Rate:                     40,0 %
Spec Test Coverage Rate:               6,7 %
Out-of-Spec Rate:                     33,3 %

Disciplina Spec Development:        NIVEL C

================================
DEUDA
================================

Deuda técnica P0:                        12
Deuda técnica P1:                        16
Deuda técnica P2:                        21
Deuda técnica P3:                        11
Deuda técnica TOTAL:                     60

Deuda Spec Development:                  16
   P0: 4   ·   P1: 7   ·   P2: 5

Hallazgos de seguridad:                  21
   P0: 5   ·   P1: 8   ·   P2: 5   ·   P3: 3

Código muerto estimado:            ~1 800 LOC

================================
GIT
================================

Commits:                                171
Rango:              2026-06-23 → 2026-07-08
Merges:                                   0
Pull requests:                            0
Tags:                                     0
Ramas:                                    1
Autores:                                  2
Commits "fix":                           51   (30 %)
Commits "feat":                          37   (22 %)

================================
VEREDICTO
================================

Madurez producto:                   NIVEL 3 — INTEGRACIÓN
Veredicto funcional:                INTEGRACIÓN INCOMPLETA
Veredicto metodológico:             CUMPLIMIENTO PARCIAL
```

## Madurez del producto — justificación

| Nivel | ¿Aplica? | Razón |
|---|---|---|
| 0 CONCEPTO | no | hay 30 000 LOC y un dominio profundo implementado |
| 1 PROTOTIPO | no | hay reglas de negocio reales, migraciones, workflow de aprobación y despliegue productivo |
| 2 DESARROLLO | no | la mayoría de los módulos están construidos, no en construcción |
| **3 INTEGRACIÓN** | **sí** | las piezas existen y en su mayoría son correctas; **lo que falla es la unión**: 13 desajustes de contrato, 5 pantallas rotas, 2 campos nunca enviados, una capa de servicios sin usar, SAP sin transporte real |
| 4 BETA OPERATIVA | no | requeriría que los procesos centrales funcionaran E2E; la mortalidad diaria devuelve 500 y las correcciones no aplican el dato |
| 5 PRODUCCIÓN | no | 12 bloqueadores P0 vivos, sin RBAC, sin observabilidad, sin backups, sin puerta de calidad |

---
---

# GLOBAL AVÍCOLA EN LENGUAJE EJECUTIVO

*Una página, sin tecnicismos.*

**1. ¿Cuánto está realmente construido?**
Mucho más de lo que funciona. Se construyó el 100 % de las pantallas previstas, la base de datos completa y prácticamente toda la lógica del negocio avícola. Pero solo **1 de cada 5 funcionalidades se puede usar de principio a fin hoy**. La comparación honesta: el edificio está levantado y bien cimentado; faltan conexiones entre plantas y algunas puertas no abren.

**2. ¿Qué puede utilizarse hoy?**
Entrar al sistema, registrar la mayoría de las operaciones de campo (alimento, pesaje, huevos, vacunación, despachos), enviarlas a revisión, devolverlas al operador, aprobarlas o rechazarlas, consolidarlas y exportar indicadores a Excel y PDF. Todo bilingüe español/inglés, en móvil y en escritorio.

**3. ¿Qué procesos están completos?**
**Ninguno al 100 %.** Los cuatro más cercanos —Revisión/Aprobación, Engorde, Consolidación e Incubación— están al 80-90 %, cada uno bloqueado por un único defecto puntual.

**4. ¿Qué procesos están a medias?**
Los seis procesos productivos (abuelas, reproductoras cría y producción, incubación, engorde), la revisión y aprobación, la integración con SAP, la auditoría, la trazabilidad entre generaciones, los maestros, los usuarios y los reportes. Doce de quince.

**5. ¿Qué falta?**
Cuatro cosas grandes: **(a)** el control de quién puede hacer qué —hoy cualquier usuario con clave puede aprobar registros, borrar catálogos o crear usuarios—; **(b)** la conexión real con SAP —lo que hoy se "envía" es un archivo que se borra solo—; **(c)** el aviso automático de desviaciones; **(d)** el registro de lotes que ya estaban en marcha antes de implantar el sistema.

**6. ¿Qué debe corregirse antes de seguir desarrollando?**
Ocho problemas graves están **hoy en producción**. Los tres más urgentes:
- **Registrar la mortalidad diaria da error.** Es la operación más frecuente de una granja y lleva meses fallando.
- **Las correcciones del supervisor no cambian el dato.** Se guarda quién corrigió y por qué, pero el valor equivocado es el que se aprueba y se usa para los indicadores.
- **La contraseña de administrador está publicada** en un documento del propio proyecto, y el sistema no limita los intentos de acceso.

**7. ¿Cuál es la deuda más importante?**
No es técnica, es **de proceso**: el sistema de control de calidad automático existe, está bien escrito, y **nunca se ha ejecutado ni una sola vez**. Está configurado para activarse cuando alguien propone un cambio para revisión, y en 171 cambios nadie lo hizo nunca. En su lugar, cada cambio se publicó solo en producción, en menos de un minuto, sin ninguna verificación. Eso explica por qué los ocho problemas graves llevan meses activos sin que nadie los detecte.

**8. ¿La arquitectura actual puede continuar?**
**Sí, sin dudas.** Es una buena arquitectura. La base de datos —47 tablas— no tiene ni una sola inconsistencia. La forma de modelar las operaciones avícolas es el mayor acierto del proyecto. La preparación para conectar con SAP está bien hecha; solo falta escribir la conexión.

**9. ¿Hace falta reconstruir o cerrar brechas?**
**Cerrar brechas.** Reconstruir sería un error costoso: lo difícil ya está hecho. La mitad de los problemas graves se corrigen con cambios de menos de dos horas cada uno.

**10. ¿Se respetó la metodología Spec Development?**
**A medias, y de forma desigual.** Hay una prueba clara de que se hizo bien: un bloque de 17 tareas se especificó a las 2:55 de la madrugada y se implementó a partir de las 3:25 del mismo día. Pero el documento que hace obligatoria la metodología —la "constitución" del proyecto— **nunca se llegó a escribir**: sigue siendo la plantilla en blanco.

**11. ¿Hubo desarrollo fuera de spec?**
Sí. **Un tercio del trabajo auditado.** Doce funcionalidades se construyeron sin que ninguna especificación las pidiera —entre ellas el canal de Telegram y los archivos adjuntos—. Y hay un caso de contradicción directa: la especificación dice literalmente "sin modo oscuro"; se implementó en 24 cambios durante cuatro días y luego se eliminó por completo.

**12. ¿Cuál debe ser el siguiente orden de trabajo?**
```
1º  Poner el freno: activar el control de calidad y dejar de publicar
    automáticamente en producción.
2º  Cambiar todas las contraseñas y limitar los intentos de acceso.
3º  Decidir sobre SAP: conectarlo de verdad o apagarlo y documentar
    el circuito manual.
4º  Reparar los ocho problemas graves (la mayoría, cambios pequeños).
5º  Implementar el control de permisos por rol.
6º  Cerrar lo que quedó a medias.
7º  Poner al día la documentación y regularizar la metodología.
```

---
---

# 106. RESPUESTAS A LAS PREGUNTAS OBLIGATORIAS

**1. ¿Qué es Global Avícola?** Plataforma web y móvil de gestión operativa avícola que actúa como capa auxiliar de SAP S/4HANA, cubriendo abuelas → reproductoras → incubación → engorde con captura en campo, revisión, corrección, aprobación y envío consolidado a SAP.

**2. ¿Qué problema resuelve?** Sustituir el legacy "Lider Pollo" y garantizar la calidad, trazabilidad y control del dato operativo **antes** de que llegue a SAP.

**3. ¿Cómo está construido?** Monolito modular: backend FastAPI async con 11 módulos de dominio y modelo de evento unificado; frontend React SPA; PostgreSQL; contenedores Docker.

**4. ¿Qué arquitectura utiliza?** `router → service → models` en backend; SPA con acceso directo a axios en frontend; adapter pattern para SAP; sin capa repositorio (aunque el README la anuncia).

**5. ¿Qué infraestructura utiliza?** Docker Compose sobre un host único, imágenes en Docker Hub, Nginx como proxy, Watchtower para auto-actualización, PostgreSQL externo. Sin CDN, colas, workers, staging, backups ni monitorización.

**6. ¿Dónde se ejecuta?** `avicola.globaldv.net`, en un host cloud (inferido DigitalOcean por la IP de la base de datos). También accesible como Telegram Mini App.

**7. ¿Qué frontend utiliza?** React 19 · Vite 8 · TypeScript 6 · TailwindCSS 4 · Zustand · react-hook-form + zod · react-i18next · recharts.

**8. ¿Qué backend utiliza?** FastAPI · Python 3.11 · SQLAlchemy 2 async · asyncpg · Alembic · Pydantic v2 · PyJWT · passlib/bcrypt · slowapi.

**9. ¿Qué base de datos utiliza?** PostgreSQL. 47 tablas, 21 migraciones, cadena íntegra, cero deriva respecto a los modelos.

**10. ¿Qué integraciones utiliza?** SAP S/4HANA (diseñada, **no conectada**), Telegram (bot + Mini App, funcional), Docker Hub. SMTP configurado y sin usar.

**11. ¿Qué módulos existen?** Auth/Usuarios, Maestros (19 catálogos), Lotes, Operaciones (25 tipos de evento), Revisión, Aprobación, Correcciones, Auditoría, Reportes/KPI, Dashboard, Integración SAP, Telegram.

**12. ¿Qué módulos están completos?** Ninguno al 100 %. En verde funcional: i18n y el canal Telegram.

**13. ¿Qué módulos están parciales?** Operaciones, Revisión/Aprobación, Maestros, Reportes/KPI, Dashboard, Auditoría, Design system.

**14. ¿Qué módulos están rotos?** Lotes y trazabilidad · Integración SAP · Seguridad/RBAC · Administración de usuarios y roles · Trazabilidad generacional · Notificaciones.

**15. ¿Qué requerimientos existen?** No existían identificadores. Se reconstruyeron **56** (`GA-REQ-001`…`056`) desde los 14 módulos funcionales, los dominios de la spec, las 16 reglas de negocio y los NFR.

**16. ¿Qué porcentaje está completo E2E?** **21,4 %** (12 de 56). Con implementación sustancial: 71,4 %.

**17. ¿Qué procesos están 100 % cubiertos?** **Ninguno de los 15.**

**18. ¿Qué procesos están parcialmente cubiertos?** 12: los seis productivos, revisión/aprobación, consolidación SAP, auditoría, trazabilidad, maestros, usuarios y reportes.

**19. ¿Qué procesos siguen manuales?** La activación manual de lotes existentes (sin interfaz) y el asiento efectivo en SAP (el sistema solo genera un archivo).

**20. ¿Qué procesos nunca se implementaron?** Notificaciones y alertas proactivas (6 tipos exigidos, 0 implementados como notificación).

**21. ¿Frontend y backend están realmente integrados?** Parcialmente: 133 de 167 endpoints se consumen y ninguna pantalla llama a una ruta inexistente, pero hay **13 desajustes de contrato** que rompen 5 pantallas y dejan inertes 7 filtros.

**22. ¿Existen pantallas sin backend?** No. Todas las pantallas tienen backend; 5 no cargan por errores de contrato.

**23. ¿Existen endpoints sin frontend?** Sí: **34 huérfanos**, incluidos los 5 de configuración de aprobación multinivel y 4 de KPI.

**24. ¿Existen mocks?** No hay mocks de datos. Sí hay un adaptador SAP simulado activo en producción (`ManualSapAdapter`) y un `mock_adapter.py` muerto que ni siquiera compila.

**25. ¿Existen datos hardcodeados?** Sí, clasificados en la §35: legítimos (curvas Ross/Cobb), configuración (umbrales), deuda (`lotId=2`, etiquetas en español) y riesgo (contraseñas de seeds).

**26. ¿Existen tablas o modelos huérfanos?** Sí: `reversals` (0 referencias). De uso parcial: `permissions` (solo para deducir super admin), `approval_steps` (CRUD sin enforcement), `egg_storage` (solo escritura).

**27. ¿Existen migraciones no trazadas?** Sí: **9 de 21 (43 %)** modifican el esquema sin requisito ni spec. Una de ellas relaja una restricción de integridad.

**28. ¿Existen riesgos de seguridad?** Sí: 21 hallazgos, 5 de ellos P0. El principal es la ausencia total de control de autorización en los 165 endpoints autenticados.

**29. ¿Qué deuda técnica existe?** 60 elementos catalogados: 12 P0, 16 P1, 21 P2, 11 P3. Más 16 elementos de deuda de proceso Spec Development.

**30. ¿Qué bloquea producción?** Los 12 bloqueadores P0. Nota crítica: **el sistema ya está en producción**, por lo que no son pendientes previos sino defectos vivos.

**31. ¿Cuál es la madurez real?** **NIVEL 3 — INTEGRACIÓN.**

**32. ¿Se desarrolló consistentemente bajo Spec Development?** No de forma consistente. Hubo un tramo con especificación previa demostrable (Fase 8) y un cuerpo mayoritario sin trazabilidad, con spec posterior o sin spec.

**33. ¿Qué porcentaje tiene trazabilidad completa?** **16,7 %** (5 de 30 features con cadena Requisito → Spec → AC → Código).

**34. ¿Cuántas features no tienen spec?** **12 funcionalidades** con cero menciones en spec y docs; 7 de las 30 features auditadas se clasifican `IMPLEMENTED_WITHOUT_SPEC`.

**35. ¿Qué código se creó antes de spec?** La trazabilidad generacional (código a las 03:51, spec a las 18:38 del mismo día) y el diseño del sistema de auditoría.

**36. ¿Qué se desarrolló out-of-spec?** Modo oscuro (prohibido expresamente), sustitución de la paleta corporativa, emojis en UI, navegación de 3 elementos en lugar de 5, textos fijos servidos por el backend y la fusión de `egg_classification`. **Out-of-Spec Rate: 33,3 %.**

**37. ¿Qué specs están incompletas?** `data-model.md`, los dos contratos de API, `07-qa-plan.md` y `quickstart.md`.

**38. ¿Qué specs no se implementaron?** RBAC granular, reverso post-SAP (BR-16), notificaciones, aprobación multinivel real, alerta de peso fuera de curva, objetivos de cobertura, recuperación de contraseña/MFA/revocación, `RealSapAdapter`, y dos documentos referenciados que no existen.

**39. ¿Qué specs fueron cerradas sin evidencia?** Seis casos documentados, incluidas dos "re-certificaciones aprobadas" y una "certificación funcional lista para UAT".

**40. ¿Qué features funcionan pero violaron la metodología?** `SearchSelect` (34 campos, mejora real de UX), inspección por galpón, evidencias adjuntas, selector de compañía y el canal Telegram: todas útiles, todas sin spec.

**41. ¿Qué drift existe?** CRITICAL en contratos de API, design system y README; HIGH en modelo de datos y taxonomía de etapas; MEDIUM en la numeración de reglas.

**42. ¿Qué cambios de BD no tienen spec?** Nueve: `egg_storage`, evidencias/alertas/reversos, campos específicos de operación, `house_id` y `value_numeric` en inspecciones, generalización de `chick_batches`, `hatchery_purpose`, índices de compañía y `lot_id` nullable.

**43. ¿Qué refactores se ejecutaron sin spec?** Cinco mayores: identidad visual completa, modo oscuro, reestructuración de la navegación móvil, sustitución de selectores por `SearchSelect` y reorganización de rutas.

**44. ¿Qué bugs se corrigieron fuera de spec?** 51 commits `fix`. **No se clasifican como incumplimiento formal** porque el proyecto no tiene una regla ratificada que exija spec para bugfix — la constitución está vacía. Se reportan como observación: 9 de ellos corrigen errores de compilación que un CI habría bloqueado.

**45. ¿Qué cambios produjeron regresiones?** Cinco cadenas con evidencia: el commit de alertas (`bdb5cde`) rompió la mortalidad; la fusión de `egg_classification` eliminó una operación exigida por la spec; el cambio de paleta generó dos commits de corrección de contraste; la campaña de dark mode, 15 correcciones y una reversión total; y `fcb57a7` revela 31 errores de TypeScript que estuvieron en `main` sin detectar.

**46. ¿Qué baseline debería considerarse vigente?** `spec.md @ cd64a17` + `docs/02-functional-spec.md`, con la advertencia de que **no gobierna la implementación actual**. Se recomienda publicar un **baseline v1.1** con retro-specs justificadas.

**47. ¿Qué no debe tocarse porque ya está correcto?** El modelo de datos y las migraciones; el modelo de evento unificado; el adapter pattern de SAP; la idempotencia y bitácora SAP; los validadores de reglas (salvo BR-06); la i18n; las cabeceras de seguridad y la validación de arranque; la ausencia de SQL crudo; el catálogo de procesos; la estructura modular del backend.

**48. ¿Qué debe regularizarse?** Ratificar la constitución; escribir AC verificables; publicar 9 retro-specs justificadas; emitir un ADR de identidad visual; regenerar y versionar los contratos de API y el ERD; unificar la numeración de reglas; reescribir el README; crear el checklist y el runbook de producción; reabrir y cerrar la Fase 9.

**49. ¿Cuál debe ser el siguiente orden de ingeniería?** Contención → bloqueadores P0 → autorización → cierre funcional → recuperación de Spec Development → testing → seguridad → observabilidad → deuda. Detalle en `audit/20_MASTER_ROADMAP.md` (76 pasos).

**50. ¿Qué controles deben impedir cambios futuros sin spec?** Los nueve enumerados en la §66: constitución ratificada, rama protegida, CI bloqueante en `push` y `pull_request`, plantilla de PR con identificador de spec y AC, migraciones que citen su spec, cierre solo con evidencia, prohibición de auto-certificación, excepción de hotfix con spec retroactiva en 24 h y regeneración versionada de contratos en cada release.

---
---

# SIGUIENTE CICLO DE INGENIERÍA

```
PASO 1 — CONTENER
   Activar CI en push. Desacoplar publicación de imagen y despliegue
   (retirar :latest + Watchtower). Rotar todas las contraseñas y
   retirarlas del repositorio. Activar rate limiting. Decidir sobre
   SAP: implementar el adaptador real o apagar el flag. Montar
   volúmenes persistentes. Automatizar las migraciones.
   Auditar el daño ya causado en la base de datos productiva.

PASO 2 — REPARAR
   Los 12 bloqueadores P0. Empezar por los cuatro de complejidad XS:
   importar get_current_bird_balance, añadir validate_segregation a
   complete_review, corregir la condicional de BR-06 y cerrar la fuga
   de _apply_company_filter. Después: los seis limit=200, la
   aplicación real de las correcciones, el refresh de token, el
   cambio de contraseña y la trazabilidad generacional.

PASO 3 — AUTORIZAR
   Dependencia require_permission(module, action) sobre la tabla
   permissions ya poblada. Aplicarla a los 165 endpoints. Guard de
   rol y menú filtrado en el frontend. Logout con revocación.
   Auditar los eventos de autenticación y de permisos.

PASO 4 — CERRAR LO PARCIAL
   sap_document_ref e idempotency_key desde el formulario. PUT en los
   15 maestros que faltan. Filtros reales en Revisión y Auditoría.
   Aprobación multinivel efectiva. Pantalla de activación manual de
   lotes. Un solo mecanismo de auditoría.

PASO 5 — REGULARIZAR LA METODOLOGÍA
   Ratificar la constitución con NO SPEC = NO DEVELOPMENT. AC
   verificables por funcionalidad. Nueve retro-specs justificadas y
   fechadas. ADR de identidad visual. Contratos regenerados.
   Publicar el baseline v1.1.

PASO 6 — PROBAR
   Migraciones y seeds en el job de backend: los 76 tests en verde.
   Un test de regresión por cada bloqueador P0. Contract testing
   generado desde OpenAPI. Tests de las cuatro páginas críticas.
   Habilitar el job E2E.

PASO 7 — OBSERVAR
   Logging estructurado con correlation ID. Captura de errores con
   alertas. Backups automáticos con restauración probada. Entorno
   de staging.

PASO 8 — REDUCIR DEUDA
   Decidir sobre la capa de servicios/hooks. Descomponer
   OperationFormPage. Eliminar las ~1 800 LOC de código muerto.
   Optimizar los listados. Solo después: optimizar rendimiento.
```

---

**Regla de gobierno del proyecto, a partir de ahora:**

# NO SPEC = NO DEVELOPMENT
