# 08 — AUDITORÍA DEL FRONTEND

## 1. Stack

| Aspecto | Valor | Evidencia |
|---|---|---|
| Framework | React 19.2.6 | `package.json:20` |
| Build | Vite 8.0.12 | `vite.config.ts` |
| Lenguaje | TypeScript ~6.0.2, `tsc -b` sin errores | verificado hoy: `tsc -b --noEmit` → exit 0 |
| Router | react-router-dom 7.18 (BrowserRouter) | `main.tsx:31`, `App.tsx` |
| Estado | Zustand 5 — 5 stores (`auth`, `ui`, `company`, `theme`, `i18n`) | `src/stores/` |
| UI | TailwindCSS 4 (plugin Vite) + 16 componentes propios | `tailwind.config.ts`, `components/ui/` |
| Formularios | react-hook-form 7.80 + zod 4.4 vía `@hookform/resolvers` | `OperationFormPage.tsx:2-4` |
| i18n | react-i18next 17 + `i18next-http-backend` cargando `/locales/{lng}/translation.json` | `src/i18n/index.ts` |
| HTTP | axios 1.18 con interceptores de request (Bearer) y response (refresh 401) | `services/api.ts` |
| Caché de datos | **ninguna** (sin React Query/SWR) — cada pantalla hace su fetch en `useEffect` | — |
| Gráficas | recharts 3.9 | `ReportsPage`, `DashboardPage` |
| Build de producción | Nginx sirviendo `dist/` | `frontend/Dockerfile` |
| Testing | Vitest 4 + Testing Library (4 archivos, 61 tests) · Playwright 1.61 (4 specs, sin CI) | verificado |

Métricas: **108 archivos fuente, 15 226 LOC**. Fichero mayor: `pages/operations/OperationFormPage.tsx` con **1 973 LOC**.

## 2. Inventario de pantallas

24 componentes de página · 40 entradas de ruta (36 funcionales + 4 redirecciones/comodín).

| # | Ruta | Pantalla | Rol / acceso | Datos | Fuente | Acciones | API | Estado |
|---|---|---|---|---|---|---|---|---|
| 1 | `/login` | LoginPage | público | credenciales | — | login, ver/ocultar contraseña, idioma | `POST /login` | **FUNCIONAL** |
| 2 | `/` | DashboardPage (web) / redirect `/menu/poultry` (móvil) | autenticado | KPIs | API | navegar | `/dashboard/admin` o `/mobile` | PARCIAL |
| 3 | `/kpi` | DashboardPage | autenticado | KPIs | API | — | `/dashboard/admin` | PARCIAL |
| 4 | `/menu/:menuKey` | MenuHubPage | autenticado | config estática | `navigationConfig.ts` | navegar | — | FUNCIONAL |
| 5 | `/poultry` | ProcessHubPage | web | catálogo estático | `processCatalog.ts` | navegar | — | FUNCIONAL |
| 6 | `/poultry/:birdType/:phase?` | ProcessStagePage | autenticado | catálogo estático | `processCatalog.ts` | abrir formulario | — | FUNCIONAL |
| 7-18 | `/masters/{12 entidades}` | MasterListPage | **web** | catálogo | API | crear, editar, borrar, buscar | `/masters/{e}` CRUD | **PARCIAL** — editar da 405 en 8 de 12; total de paginación incorrecto |
| 19 | `/operations` | OperationListPage | autenticado | eventos | API | filtrar por lote/tipo | `GET /operations?limit=100` | FUNCIONAL |
| 20 | `/operations/new` | OperationFormPage | autenticado | 14 catálogos + lotes + refs SAP | API | registrar operación | `POST /operations` | **PARCIAL** — no envía `sap_document_ref` ni `idempotency_key`; `mortality_recording` → 500 |
| 21 | `/operations/:id` | OperationDetailPage | autenticado | evento + evidencias | API | subir/descargar/borrar evidencia | `/operations/{id}` + `/evidences` | PARCIAL |
| 22 | `/my-pending` | MyPendingPage | autenticado | eventos propios | API | abrir | `GET /operations?registered_by_me=true&status=draft,registered` | **ROTA** |
| 23 | `/lots` | LotListPage | autenticado | lotes | API | abrir, crear | `GET /lots?limit=100` | FUNCIONAL |
| 24 | `/lots/new` | LotFormPage | **web** | granjas, galpones, líneas, razas | API | crear lote | `POST /lots` | FUNCIONAL |
| 25 | `/lots/:id` | LotDetailPage | autenticado | lote, KPIs, fases, eventos, alertas, trazabilidad | API | cerrar lote, cambiar fase, resolver alerta, enlazar generaciones | 7 llamadas | **ROTA** |
| 26 | `/reports` | ReportsPage | autenticado | KPIs + serie de eventos | API | exportar Excel/PDF | `/reports/kpis`, `/operations?limit=200` | **PARCIAL** |
| 27 | `/reports/lot/:id` | LotReportPage | autenticado | reporte + 3 KPIs | API | exportar | `/reports/lot/{id}` + 3 | PARCIAL |
| 28 | `/reports/sap` | SapComparisonPage | **web** | comparativo | API | — | `/reports/sap-comparison` | **PARCIAL** — siempre vacío |
| 29 | `/review` | ReviewCenter | **web** | pendientes, granjas, usuarios | API | iniciar, devolver, completar, crear lote de revisión | `/review/*` | **PARCIAL** — filtros de estado y operador inertes |
| 30 | `/review/:id` | ReviewDetail | **web** | evento, correcciones, lotes | API | revisar, aprobar, rechazar | varias | **ROTA** |
| 31 | `/review/:id/correct` | CorrectionForm | **web** | evento, tipos de corrección | API | registrar corrección | `POST /corrections` | **ROTA** |
| 32 | `/approvals` | ApprovalPanel | **web** | pendientes de aprobación | API | aprobar/rechazar individual y masivo | `/approvals/*` | FUNCIONAL |
| 33 | `/audit` | AuditPage | **web** | logs | API | filtrar por fecha | `GET /audit?limit=50` | **PARCIAL** — búsqueda y 2 pestañas inertes |
| 34 | `/sap` | SapManagerPage | **web** | referencias, jobs, payloads, conexión | API | consolidar, exportar | `/sap/*` | PARCIAL |
| 35 | `/users` | UsersPage | **web** | usuarios, roles, compañías | API | crear, editar, activar/desactivar, borrar | `/users`, `/roles`, `/masters/companies?limit=200` | **ROTA** |
| 36 | `/profile` | ProfilePage | autenticado | usuario | store | cambiar contraseña | `PUT /users/{id}` | PARCIAL |
| — | `/masters`, `/processes`, `/processes/:stage`, `*` | redirecciones | — | — | — | — | — | FUNCIONAL |

### Resumen

| Clasificación | Nº | Pantallas |
|---|---|---|
| Integradas sin defecto confirmado | **10** | LoginPage, MenuHubPage, ProcessHubPage, ProcessStagePage, OperationListPage, LotListPage, LotFormPage, ApprovalPanel, OperationDetailPage*, SapManagerPage* |
| Parciales (operan con defectos confirmados) | **9** | DashboardPage, MasterListPage, OperationFormPage, ReportsPage, LotReportPage, SapComparisonPage, ReviewCenter, AuditPage, ProfilePage |
| **Rotas** | **5** | **LotDetailPage, ReviewDetail, CorrectionForm, UsersPage, MyPendingPage** |
| Mock / datos falsos | **0** | — |
| Desconectadas / inaccesibles | **0** rutas; 2 componentes sin ruta (`DarkModeToggle`, `SignaturePad`) | — |

\* `OperationDetailPage` y `SapManagerPage` funcionan; su deuda es de infraestructura (evidencias efímeras, SAP manual), no de la pantalla.

## 3. Hallazgos de frontend

### FE-01 · La capa de servicios y hooks está muerta (P1)

`src/services/` contiene 12 módulos y `src/hooks/` contiene 10. **Ninguna página importa un servicio de dominio ni un hook de datos.** Los servicios solo son importados por los hooks; los hooks (salvo `useTelegram`) no son importados por nadie.

```
audit.service.ts        → 0 importadores
dashboard.service.ts    → 0
corrections.service.ts  → 0
auth.service.ts         → 0
sap/reports/operations/masters/lots/review/approvals.service.ts → solo por su hook homónimo
useOperations, useMasters, useLots, useSap, useReview, useReports,
useApprovals, useSidebar, useMediaQuery → 0 importadores (useMediaQuery solo en su test)
```

Consecuencia directa: no hay un punto único donde definir límites de paginación, filtros o formas de payload — de ahí los defectos FE-02 y FE-03. ~600 LOC de código muerto.

### FE-02 · Seis llamadas exceden el límite máximo del backend → HTTP 422 (P0)

Los endpoints declaran `limit: int = Query(20, ge=1, le=100)`. Seis llamadas piden `limit=200`.

| Archivo:línea | Llamada | Efecto |
|---|---|---|
| `stores/company.store.ts:38` | `/masters/companies?limit=200` | selector de compañía siempre vacío → multi-compañía inutilizable en UI |
| `pages/users/UsersPage.tsx:21` | `/masters/companies?limit=200` dentro de `Promise.all` | **toda** la carga falla → sin usuarios ni roles |
| `pages/lots/LotDetailPage.tsx:45` | `/lots?limit=200` fuera del `Promise.allSettled` | aborta el resto: KPIs, fases, eventos, alertas, trazabilidad |
| `pages/review/ReviewDetail.tsx:32` | `/operations?limit=200` | "Evento no encontrado" |
| `pages/review/CorrectionForm.tsx:27` | `/operations?limit=200` | "Evento no encontrado" |
| `pages/reports/ReportsPage.tsx:19` | `/operations?lot_id=..&limit=200` | gráficas vacías |

### FE-03 · Parámetros que el backend no acepta (P1)

| Pantalla | Parámetro enviado | ¿Existe en el backend? | Efecto |
|---|---|---|---|
| `MyPendingPage:33` | `registered_by_me=true` | **No** | se ignora → muestra eventos de toda la compañía, no los propios |
| `MyPendingPage:33` | `status=draft,registered` | acepta `status` pero lo compara contra un `Enum` | valor inválido → error de conversión → **500** |
| `ReviewCenter:86` | `status=<pestaña>` | **No** en `GET /review/pending` | las pestañas de estado no filtran nada |
| `ReviewCenter:91` | `operator_id` | **No** | filtro de operador inerte |
| `AuditPage:44` | `search` | **No** | buscador inerte |
| `AuditPage:47` | `action_contains` | **No** | pestaña "Correcciones" inerte |
| `AuditPage:48` | `group_by` | **No** | pestaña "Por usuario" inerte |

### FE-04 · Campos del contrato nunca enviados (P0)

- **`sap_document_ref`**: el formulario guarda la orden SAP elegida en `extra_data.sap_order_ref` (JSONB libre). El campo tipado `sap_document_ref` de `OperationalEventCreate` nunca se rellena. Consecuencias: BR-11 (documentos SAP no duplicados) y BR-18 (cantidad ≤ OC) nunca se disparan; `GET /reports/sap-comparison` siempre vacío; el detalle de operación nunca muestra la referencia.
  Evidencia: búsqueda de `sap_document_ref` en `frontend/src` → solo 2 usos, ambos de **lectura** (`ReviewDetail.tsx:163`, `OperationDetailPage.tsx:145`).
- **`idempotency_key`**: el backend implementa deduplicación por clave de idempotencia (`operations/service.py:50-60`, columna única, migración `f6a7b8c9d0e1`). El frontend **nunca la genera**. Un doble toque en "Guardar" con red lenta crea dos eventos. BR-12 inoperante en la práctica.

### FE-05 · Errores de ESLint y calidad (P2)

`eslint .` → **5 errores, 431 avisos** (ejecutado hoy).

| Regla | Nº | Comentario |
|---|---|---|
| `react-hooks/refs` (**error**) | 5 | "Cannot access refs during render" — `SignaturePad`, `SearchSelect`, `OperationFormPage:251` |
| `@typescript-eslint/no-explicit-any` | 393 | tipado efectivo muy bajo pese a que `tsc` compila |
| `react-hooks/set-state-in-effect` | 19 | en los hooks muertos |
| `react-hooks/exhaustive-deps` | 6 | — |
| `react-refresh/only-export-components` | 5 | — |
| `no-unused-vars` | 6 | — |

El job `lint` del CI ejecuta `npm run lint` sin `--max-warnings`, por lo que **fallaría** por los 5 errores — pero nunca se ha ejecutado (0 PRs).

### FE-06 · Restos de funcionalidades eliminadas (P2)

Tras `8940d9e` ("Remove dark mode… Light mode only") permanecen:
`tailwind.config.ts:4` `darkMode: 'class'`; `src/stores/theme.store.ts` (37 LOC); `src/components/DarkModeToggle.tsx` (25 LOC, 0 usos); `src/main.tsx:19` lee `theme-storage` y aplica la clase `dark`.

Otros elementos muertos: `SignaturePad.tsx` (133 LOC + 91 LOC de test, 0 usos en páginas), `SidebarSubmenu.tsx` (145 LOC, 0 usos), `ProcessFlowVisualizer.tsx`, `OperationActionCard.tsx`, `ProcessCard.tsx` (solo exportados por el barrel).

### FE-07 · Estilo de código incoherente (P3)

Gran parte de `src/pages/**` y varios componentes usan **indentación de un solo espacio**, resultado de ediciones mecánicas masivas (campañas de dark mode e i18n). `src/data/`, `src/services/` y `src/i18n/` conservan 2 espacios. No hay Prettier ni formateo en CI.

### FE-08 · Buenas prácticas verificadas (positivo)

- **0 `console.log`** en `src/`.
- **0 arrays de datos falsos / mocks**; los catálogos vienen siempre de la API.
- **0 `TODO`/`FIXME`/`HACK`** en el frontend.
- `localStorage` **no** se usa como backend: solo para tema, idioma y estado del sidebar.
- Tokens en `sessionStorage` (web) y `localStorage` (Telegram Mini App, justificado para conservar sesión al cerrar la mini app).
- i18n con **paridad total** ES/EN (865 claves cada uno, 0 faltantes en ambos sentidos; 37 valores idénticos, todos legítimos como "Email", "Dashboard", "SAP", "ID").
- Interceptor de refresh con protección contra bucle (`_retry`) y contra refrescos concurrentes (`isRefreshing`/`refreshPromise`).

### FE-09 · Permisos solo visuales (P0 — ver `13_ROLES_AND_SECURITY.md`)

El único control de acceso del frontend es `WebOnlyRoute`, que compara `user.view_type === 'mobile'`. **No existe ningún guard por rol**: `ProtectedRoute` acepta un prop `roles` cuyo cuerpo es `const userRoleName = user?.role_id ? '' : 'super_admin'` —lógica sin sentido— y **nunca se le pasa ese prop**. Cualquier usuario con `view_type='web'` puede abrir `/users`, `/approvals`, `/sap`, `/audit` y `/review`. Como el backend tampoco valida permisos, las acciones funcionan.
Evidencia: `frontend/src/App.tsx:35-60`.
