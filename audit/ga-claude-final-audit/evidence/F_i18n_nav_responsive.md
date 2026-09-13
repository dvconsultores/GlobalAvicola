# F · Auditoría estática — I18N · Navegación/Descubribilidad · Responsive

Repositorio: `/home/maria/Proyectos/GlobalAvicola` (solo lectura; sin cambios). Rutas de este informe relativas a esa raíz.
Método: lectura de `frontend/src/**` (159 ficheros TS/TSX), diccionarios `frontend/public/locales/{es,en}/translation.json`, y contraste con enumerados del backend (`backend/app/**`). Análisis de paridad y cobertura con Python one-liners de solo lectura. No se ejecutaron tests ni builds.

---

## 1. I18N

### 1.a Paridad de claves ES ↔ EN

| Métrica | Valor |
|---|---|
| Claves ES (aplanadas) | 1041 |
| Claves EN (aplanadas) | 1041 |
| Solo en ES | **0** |
| Solo en EN | **0** |
| Namespaces | 36, idénticos en ambos |
| Cadenas vacías | `nav.sections.main` = `''` en ambos (intencional: `data/navigationConfig.ts:66`) |
| Valores idénticos ES==EN | 25 (nombres propios/unidades: `Email`, `Error`, `Dashboard`, `KPIs`, `hen-day`…) |

Sospechosos dentro de los 25 idénticos (texto inglés dentro del bundle ES):
- `reports.sapComparisonLink` ES=`'SAP Comparison'` → botón en `pages/reports/ReportsPage.tsx:199` sale en inglés para usuarios ES. *Menor*.
- `users.mobile` ES=`'Mobile'` (debería ser «Móvil») → `pages/users/UsersPage.tsx:108,111,131`. *Menor*.
- `users.emailPlaceholder` = `'Email *'`. *Menor*.

EN con caracteres españoles: solo marca (`Global Avícola`, `Español`) → correcto.

**Conclusión paridad: limpia.** El riesgo no está en la paridad de los JSON sino en claves referenciadas por código que **no existen en ninguno de los dos** (1.b) y en enumerados renderizados sin `t()` (1.c).

### 1.b Claves referenciadas por código que NO existen (ni ES ni EN)

Chequeo: 747 claves literales `t('…')` + 100 claves de datos (`labelKey`/`descKey`) → 16 ausentes. Con `t(key, fallback)` react-i18next devuelve el **fallback en ambos idiomas** (texto español fijo para usuarios EN). Sin fallback devolvería la clave cruda (no ocurre en ninguna de estas 16).

| Clave ausente | Uso (file:line) | Fallback mostrado | Crítico |
|---|---|---|---|
| `process.grandparent.title` / `process.breeder.title` / `process.hatchery.title` / `process.broiler.title` | `pages/dashboard/DashboardPage.tsx:155,160,165,170` | «Progenitoras / Reproductoras / Incubadora / Pollo de Engorde» | **Sí** — cabeceras del home móvil, en español para EN |
| `audit.action` | `pages/audit/AuditPage.tsx:141` | «Tipo de operación» | Sí (etiqueta de filtro) |
| `audit.module` | `pages/audit/AuditPage.tsx:154` | «Módulo» | Sí |
| `kpi.hatchery` | `pages/reports/LotReportPage.tsx:129` | «Incubadora» | Sí (título KPI) |
| `kpi.birthRate` / `kpi.hatchRate` / `kpi.hatcheryYield` / `kpi.chicksBorn` | `LotReportPage.tsx:132-135` | «Nacimiento / Eclosión / Rendimiento / Nacidos» | Sí |
| `kpi.vaccinationEfficiency` / `kpi.transferEfficiency` | `LotReportPage.tsx:144,153` | «Eficiencia de Vacunación / Traslado» | Sí |
| `reports.onlyApproved` / `reports.onlyApprovedDetail` | `LotReportPage.tsx:117,120` | aviso largo en español | Sí (aviso normativo `AC05`) |
| `process.flowDesc.bird_transfer` | `data/processCatalog.ts:351` (dinámica) | — | No: `bird_transfer` no aparece en ningún `STAGE_FLOWS`, nunca se renderiza (latente) |

Claves de `navigationConfig.ts` y `processCatalog.ts`: **todas existen** (los `fallback:` no llegan a usarse). `nav.myPending`, `nav.operations`, `nav.home`, `nav.kpi`, `nav.optionsCount`, `common.options` existen.

### 1.c Cadenas de usuario hardcodeadas en JSX/TSX (flujos críticos)

| file:line | Cadena | Clase |
|---|---|---|
| `pages/lots/LotFormPage.tsx:21-23` | mensajes zod `'Mínimo 2 caracteres'`, `'Requerido'`×2 → renderizados en `:169,:186,:227` | **Crítico** (validación de alta de lote, solo español) |
| `App.tsx:136-165` | `masterEntities[].cols[].labelKey` = `'common.edit'` / `'common.save'` para `tax_id/code/country/capacity/location/laboratory/category/plate/order/description` → `pages/masters/MasterListPage.tsx:122` (cabeceras) y `:196` (labels del modal de alta/edición) | **Crítico** — 21 maestros muestran columnas/campos «Editar» y «Guardar» en lugar del nombre del atributo (clave mal elegida, no cadena literal, pero efecto equivalente) |
| `pages/operations/OperationFormPage.tsx:1243-1244,1327` | `EQUIPMENT_TYPES` `'bebedero','comedero','ventilador','calefactor','nebulizador','iluminación','cortina','extractor','otro'` mostrados capitalizados | **Crítico** (opciones de `farm_inspection`, sin traducir; también viajan como valor) |
| `pages/reports/ReportsPage.tsx:42-52,58` | cabeceras de exportación `'Lote ID','Mortalidad %','Bajas','Conv. Alimento',…`, título PDF `` `KPIs — Lote ${lotId}` `` | Crítico (documento exportado) |
| `utils/export.ts:25,50` | hoja `'Datos'`; fecha `toLocaleString('es-VE')` fijo | Menor |
| `OperationFormPage.tsx:1997,2033` | `searchPlaceholder` `'Buscar transferencia...' / 'Buscar orden de compra...' / 'Buscar orden de traslado...'` | Menor (solo ≥1024 px; en móvil `SearchSelect` usa `<select>` nativo) |
| `OperationFormPage.tsx:657` | `{declaredQty} aves` | Menor |
| `OperationFormPage.tsx:745,798,809,850,861,1269` | `` (cap. ${h.capacity}) `` | Menor |
| `OperationFormPage.tsx:1282` | `` weekLabel={`sem.${lotAgeWeeks}`} `` | Menor |
| `pages/reports/LotReportPage.tsx:174,175` | `g/día`, `días` | Menor |
| `pages/dashboard/DashboardPage.tsx:193` | `user?.first_name \|\| 'Operador'` | Menor |
| `pages/operations/ProcessHubPage.tsx:45` | contador fijo `6` procesos (aunque se filtren por unidad) | Menor |
| `hooks/useOperations.ts:31,59,61,91` | `'Error al cargar operaciones'`, `'Evento no encontrado'`… | Menor — **hook no importado por nadie** (código muerto) |
| `pages/review/CorrectionForm.tsx:93` | `{f.label} ({f.key})` muestra `observations` crudo | Menor |
| `components/layout/Header.tsx:62,192` | `title` `'Switch to English' / 'Cambiar a Español'` | OK (bilingüe a propósito) |
| `pages/operations/OperationDetailPage.tsx:367` | `alt="preview"` | Menor (a11y) |

### 1.d Enumerados renderizados en crudo (sin `t()`)

| file:line | Campo | Impacto |
|---|---|---|
| `pages/operations/OperationListPage.tsx:85` | `ev.status` (badge) | **Crítico**: es la lista a la que aterriza todo usuario tras guardar (`OperationFormPage.tsx:455`) |
| `pages/operations/OperationDetailPage.tsx:196` | `event.event_type` («Tipo: bird_reception») | **Crítico** (pantalla de envío/reenvío) |
| `OperationDetailPage.tsx:221` | `bm.sex` (`male/female/mixed`) — existen `operations.male/female/mixed` pero no se usan aquí | Crítico |
| `OperationDetailPage.tsx:240` | `em.egg_type` — existen `operations.fertile/dirty/…` pero no se usan | Crítico |
| `pages/review/ReviewDetail.tsx:95` | `event.status` | **Crítico** (revisión) |
| `ReviewDetail.tsx:125,153,198` | `bm.sex`, `em.egg_type`, `a.action_type` | Crítico |
| `pages/lots/LotDetailPage.tsx:319,326` | `ev.event_type`, `ev.status` (últimos registros) | Alto |
| `pages/reports/LotReportPage.tsx:85,105` | `report.lot?.status`, claves de `by_type` | Medio |
| `pages/reports/SapComparisonPage.tsx:43` | `ev.event_type` | Medio |
| `pages/sap/SapManagerPage.tsx:188,296` / `:192,292` / `:217,241` | `j.direction` / `j.status` / `p.status` | Medio |
| `components/TraceabilityTree.tsx:62` | `lot.status` en `LotChip` | Medio |
| `OperationFormPage.tsx:2085` | `` · ${l.status} `` en selector de lote | Menor |
| `pages/audit/AuditPage.tsx:216`, `components/ui/StatusTimeline.tsx:74` | `log.action` crudo (`review_started`…) | Alto (auditoría) |
| `pages/admin/UnitAccessPage.tsx`, `UserBusinessUnitsButton.tsx` | unidades vía `businessUnitName()` → `businessUnits.*` 4/4 | OK |

**Cobertura de claves dinámicas** (contrastada con enumerados reales):

| Familia | Uso | Claves i18n | Enumerado real | Resultado |
|---|---|---|---|---|
| `events.*` | tiles, hubs, detalle | 26 | 25 `EventType` + `egg_reception_classification` (`processCatalog.ts:181`) | ✅ 26/26 |
| `eventsShort.*` | listas, review, approvals | 26 | ídem | ✅ |
| `status.*` | badges | 14 | 13 `EventStatus` (`types/domain.types.ts:20-33`) | ✅ (+`reversed` extra) |
| `birdTypes.*` | 4 | 4 | ✅ |
| `lotStatus.*` | 3 | `active/closed/cancelled` | ✅ |
| `process.stages/stagesDesc/categories` | 6/6/7 | ✅ |
| `process.flowDesc.*` | `StageTimeline.tsx:138` | 25 | 26 | ⚠ falta `bird_transfer` (no se renderiza hoy) |
| `notifications.types.*` (**sin fallback**, `NotificationBell.tsx:105`) | 6 | backend emite 6 (`record_rejected, sap_send_failed, mortality_over_threshold, weight_out_of_standard, review_pending_24h, lot_near_close`) | ✅ (nota: el tipo TS `NotificationType` en `services/notifications.ts:14-19` omite `lot_near_close`) |
| `alerts.severity.*` | 3 | `critical/warning/info` | ✅ |
| `alerts.type.*` (`DashboardPage.tsx:52`) | 3 | backend también emite `weight_deviation` (`backend/app/operations/service.py:729`) | ❌ se muestra «weight deviation» |
| `kpi.${uniformity_status}` | 5 | `excellent/acceptable/poor/insufficient_data` (`reports/service.py:719-741`) | ✅ |
| `evidence.types.*` (`OperationDetailPage.tsx:283,321`) | 7 | backend `CLASES_DE_ADJUNTO` = 9 (`validators.py:617`: + `signature`, `audio`) | ⚠ latente (la UI no las genera) |
| `audit.actions.*` (`AuditPage.tsx:150`) | **0** | 22 `AuditAction` (`backend/app/audit/models.py:24-48`); la lista del front (`AuditPage.tsx:23-27`) tiene 19 y omite `reversed, logout, context_switched, config_change` | ❌ todo crudo |
| `audit.modules.*` (`AuditPage.tsx:162`) | **0** | 11 `AuditModule` (front omite `config`) | ❌ todo crudo |
| `roles.actions.*` (`RolesPage.tsx:205`) | **0** | 9 (`PermissionAction`, `auth/models.py:50-59`) | ❌ matriz de permisos cruda |
| `roles.modules.*` (`RolesPage.tsx:213`) | **0** | 13 (`AuthService.MODULOS`, `auth/service.py:546-553`) | ❌ |
| `sex` / `egg_type` en detalle | — | existen `operations.male…`, `operations.fertile…` | ❌ no se aplican (ver 1.d) |
| `t(errors.username.message)` (`LoginPage.tsx:101,131`), `t(errors.lot_id.message)` (`OperationFormPage.tsx:2089`) | claves `auth.usernameMinLength`, `auth.passwordMinLength`, `operations.selectLot` | ✅ |
| `t(clave)` `WeightEvaluation.tsx:80` (`curves.below/above/within/noReference`), `t(st.key)` `UserBusinessUnitsButton.tsx:162`, `t(tab.labelKey)` `AuditPage.tsx:133` / `SapManagerPage.tsx:163` | ✅ |
| `` t(`operations.${clave}`) `` `OperationDetailPage.tsx:254` | 11 claves `import*` | ✅ todas existen |

**Riesgo de clave cruda visible**: solo `NotificationBell.tsx:105` carece de fallback y está cubierto hoy; el resto usa fallback (→ español fijo). `types/i18next.d.ts` no tipa las claves, así que nada de esto lo detecta `tsc`.

### 1.e Mensajes de error del backend (español) mostrados a usuarios EN

`components/Toast.tsx:134-140` `getErrorMessage()` devuelve `response.data.detail` **tal cual**. El backend tiene 110 `detail=` y todos son español (p. ej. `backend/app/auth/security.py:227` «Permiso requerido: {modulo}:{accion}», «El evento requiere lote», «Lote no encontrado», «Mortalidad acumulada machos no puede exceder población inicial»). Superficies: `OperationFormPage.tsx:458` (fallo al guardar), `OperationDetailPage.tsx:68,101,112,138,154`, `LoginPage.tsx:41`, `LotFormPage.tsx:137`, `MasterListPage.tsx:99`, `TraceabilityTree.tsx:95,114`, `UsersPage.tsx:85` (`alert(detail)`), `ProfilePage.tsx:38`, `DashboardPage.tsx:101` (home). Los 422 de Pydantic (lista) se aplanan en `Toast.tsx:100-123` como `campo: msg` en **inglés** → mezcla de idiomas en el mismo toast. No existe mapeo código→clave i18n. *Medio* (el español es idioma primario; para EN es sistemático).

### 1.f Formato de fechas/números

| Patrón | Dónde | Problema |
|---|---|---|
| ISO crudo `YYYY-MM-DD` | `OperationDetailPage.tsx:197`, `OperationListPage.tsx:87`, `ReviewCenter.tsx:312,407`, `ApprovalPanel.tsx:234,303`, `ReviewDetail.tsx:108`, `LotDetailPage.tsx:209,297,320,342`, `LotListPage.tsx:88,117`, `LotReportPage.tsx:86` | consistente pero sin localizar (nunca `dd/mm/aaaa`) |
| `toLocaleDateString()` / `toLocaleString()` **sin locale** | `MyPendingPage.tsx:102`, `TraceabilityTree.tsx:180,214,233,267`, `ReviewDetail.tsx:183,200`, `AuditPage.tsx:88`, `SapManagerPage.tsx:239,297` | usa locale del navegador, no del app → UI ES con fechas `9/13/2026` si el navegador está en en-US |
| Locale del app | solo `DashboardPage.tsx:467` (`es-VE`/`en-US`) | única implementación correcta |
| Locale fijo | `utils/export.ts:50` `'es-VE'` | ignora idioma UI |
| Números | `toFixed(1)` (`LotDetailPage.tsx:296`, `LotReportPage.tsx:195-218`, `OperationDetailPage.tsx:30-31`) siempre `.`; `toLocaleString()` en `TraceabilityTree.tsx:181,215…` según navegador | separadores mixtos en una misma pantalla; sin `Intl.NumberFormat` |

### 1.g Claves reutilizadas con semántica divergente (los fallbacks delatan la intención; el JSON gana)

| file:line | Clave (valor JSON ES) | Fallback escrito | Efecto |
|---|---|---|---|
| `OperationListPage.tsx:89` | `common.edit` («Editar») | — | el enlace abre el **detalle** (pantalla de envío a revisión); CTA engañoso |
| `ApprovalPanel.tsx:339`, `MasterListPage.tsx:167` | `common.back` («Volver») | «Anterior» | paginación etiquetada como «Volver» |
| `OperationListPage.tsx:65`, `DashboardPage.tsx:365` | `process.hub.title` («Elige un Proceso») | «Etapas de producción» / «Procesos» | optgroup y cabecera muestran «Elige un Proceso» |
| `OperationFormPage.tsx:1218` | `operations.quantity` («Cantidad») | «Huevos recibidos» | etiqueta pierde especificidad |
| `OperationFormPage.tsx:1262` | `operations.selectHouse` («Seleccionar galpón...») | «Galpón» | un `<label>` que dice «Seleccionar galpón...» |
| `OperationFormPage.tsx:894,939,956,965,1006…` | `operations.selectType` («Seleccionar tipo...») | «Seleccionar planta...» / «Seleccionar...» | placeholders de planta/jaulas/ventilación dicen «tipo» |
| `OperationFormPage.tsx:470,1703` | `operations.avgWeight` («Peso prom. (g)») | «Peso prom. (kg)» / «Peso final prom. (kg)» con `step="0.001"` | JSON («g») coincide con backend (`WeightEvaluation.tsx:82`); los fallbacks/`step` son restos «kg» — solo confusión de mantenimiento |

---

## 2. NAVEGACIÓN / DESCUBRIBILIDAD

Fuentes: `App.tsx:206-284` (rutas), `data/navigationConfig.ts:78-292` (`NAV_ITEMS`, `MOBILE_TOP_LEVEL_KEYS`), `auth/navigation.ts:91-154`, `components/layout/{AppLayout,Header,Sidebar,MobileNav}.tsx`, `pages/operations/{MenuHubPage,ProcessHubPage,ProcessStagePage,MyPendingPage}.tsx`, `pages/dashboard/DashboardPage.tsx`.

Hechos estructurales:
- **El sidebar no despliega hijos**: `Sidebar.tsx:23-35` convierte todo contenedor en un enlace al hub `/menu/:key`; `SidebarSubmenu.tsx` y `MobileDrawer.tsx` **no están importados por nadie** (código muerto; `ui.store.ts` `openDrawer` tampoco).
- `AppLayout.tsx:13-20`: `Sidebar` solo si `view_type!=='mobile'` (y solo visible `lg:`), `MobileNav` solo si `view_type==='mobile'` (y solo `<lg`). No hay hamburguesa ni drawer montado.
- Guardas: `ProtectedRoute` (sesión), `WebOnlyRoute` (móvil → `/`), `CapabilityRoute` (permiso+unidad → mensaje `common.noPermission`), `PermissionRoute` (solo permiso → mensaje `admin.forbidden`). `ProtectedRoute` tiene un parámetro `roles` nunca usado (`App.tsx:58-64`, lógica sospechosa `role_id ? '' : 'super_admin'`).

### 2.a Matriz de rutas

Leyenda: Nav = entrada en `NAV_ITEMS`/`MobileNav`; Enlace = botón/link in-app; Móvil = alcanzable con `view_type='mobile'`; Guard = ruta vs nav; Deep-link = comportamiento sin autorización; Activo = resaltado de menú.

| Ruta | Nav | Enlace in-app | Móvil | Guard ruta vs nav | Deep-link no autorizado | Activo |
|---|---|---|---|---|---|---|
| `/login` | — | redirect `ProtectedRoute` | sí | — | — | — |
| `/` | `dashboard` (`dashboard:read`) | `MenuHubPage.tsx:100,107`, `Breadcrumbs.tsx:42`, `LoginPage.tsx:39`, todos los `Navigate to="/"` | móvil → `/menu/poultry` (`App.tsx:112`) | **ruta sin guard**, nav exige `dashboard:read` → ver 2.f | n/a | sí (`isPathActive('/')`) |
| `/kpi` | solo `MobileNav` (`dashboard:read`) | ninguno web | sí | sin guard | — | MobileNav sí; Sidebar no |
| `/menu/:menuKey` | Sidebar → contenedores `poultry, review, sap, reports, settings`; MobileNav → `poultry` | `OperationListPage.tsx:55`, `ProcessStagePage.tsx:56` | sí (`poultry` únicamente, `MenuHubPage.tsx:83`) | interno: raíz no visible → `Navigate "/"` (`:82`) | redirect silencioso | sí (`pathname.startsWith(hubPath)`) |
| `/masters` → `/masters/farms` | `masters` | — | no (WebOnly) | paridad OK | web: mensaje; móvil: redirect `/` | sí |
| `/masters/:entity` (21) | **solo `farms`** vía redirect | **ninguno** (ni tabs ni sub-nav en `MasterListPage.tsx`; grep de `/masters/` solo halla `App.tsx:244` y `WeightCurvesPage.tsx:151`) | no | OK | mensaje | sí (prefijo `/masters`) |
| `/masters/genetic-lines/:id/weight-curves` | — | `App.tsx:242-245` (rowAction) | no | OK | mensaje | sí |
| `/poultry` (hub legado) | — | ninguno (`ProcessStagePage.tsx:56` enlaza a `/menu/poultry`) | redirect (`PoultryHubLegacyRoute`) | OK | mensaje | MobileNav sí |
| `/poultry/:birdType/:phase?` | hijos `gp_rearing…broiler` | `DashboardPage.tsx:391,416` (móvil), `MenuHub` | sí | OK (`operations:read`+unidad) | mensaje; birdType inválido → `/menu/poultry` | Sidebar (vía `isAnyChildActive`) y MobileNav sí |
| `/processes*` | — | — | redirect | — | — | — |
| `/operations` | **ninguna** | `ProcessStagePage.tsx:120` (**solo web**, `!isMobileUser`), `OperationFormPage.tsx:455` (tras guardar), `OperationDetailPage.tsx:172` | sí (llega tras guardar) | `operations:read` | mensaje | **ninguno** (ni Sidebar ni MobileNav) |
| `/operations/new` | — | `OperationTile.tsx:60-62`, `StageTimeline`→`ProcessStagePage.tsx:49`, `LotDetailPage.tsx:234` | sí | `operations:create`; tiles/timeline **no** gatean por `operations:create` (`OperationTile.tsx`, `StageTimeline.tsx` sin `useCan`; `LotDetailPage.tsx:228` sí) | mensaje `common.noPermission` | ninguno |
| `/operations/:id` | — | `OperationListPage.tsx:89`, `MyPendingPage.tsx:89`, `NotificationBell`→`notifications.ts:57` | sí | `operations:read` | mensaje | ninguno |
| `/my-pending` | **ninguna** | **ninguno** (grep exhaustivo: solo `App.tsx:262`) | teóricamente | **sin guard** | — | ninguno |
| `/lots` | `lots` (hijo de `poultry`) | `LotDetailPage.tsx:152`, `LotFormPage.tsx:148,299` | sí (hub poultry) | ruta `lots:read`; nav `lots:read`+`requiresUnits` | mensaje | Sidebar sí; MobileNav **no** |
| `/lots/new` | — | `LotListPage.tsx:53-56` (web ∧ `lots:create`) | no | OK | mensaje / móvil redirect | sí |
| `/lots/:id` | — | `LotListPage.tsx:79,119`, `DashboardPage.tsx:55`, `TraceabilityTree.tsx:57`, `OperationDetailPage.tsx:202` | sí | OK | mensaje | Sidebar sí; MobileNav no |
| `/admin/unit-access` | `settings_unit_access` | — | no | `PermissionRoute` (sin unidad) ≡ nav | mensaje **`admin.forbidden`** (texto distinto de las demás) | sí |
| `/reports` | `rpt_production`, `rpt_mortality` (**ambos → `/reports`**) | `LotReportPage.tsx:68`, `SapComparisonPage.tsx:21` | sí | ruta `reports:read`; nav además `requiresUnits` | mensaje | sí |
| `/reports/lot/:id` | — | **solo `ReportsPage.tsx:193` con `id=2` fijo** (ignora `lotId`); `LotDetailPage` no enlaza | sí | OK | mensaje | sí |
| `/reports/sap` | `rpt_sap` | `ReportsPage.tsx:197` | no | OK (+`requiresUnits` solo nav) | mensaje/redirect | sí |
| `/review` (+`?status=`) | `review_pending/approved/returned` | `ApprovalPanel.tsx:156`, `ReviewDetail.tsx:90`, `CorrectionForm.tsx:79` | no | ruta `review:read`; nav +`requiresUnits` | mensaje/redirect | sí |
| `/review/:id` | — | `ReviewCenter.tsx:335,433`, `ApprovalPanel.tsx:246,319` | no | OK | ídem | sí |
| `/review/:id/correct` | — | `ReviewDetail.tsx:232,255` (gate `corrections:correct`) | no | OK | ídem | sí |
| `/approvals` | `approvals` | `ReviewCenter.tsx:171` | no | nav +`requiresUnits` | ídem | sí |
| `/audit` | `audit` | — | no | OK | ídem | sí |
| `/sap` | `sap_pending/sent/errors/log` (**los 4 → `/sap`**, sin `?tab`; `SapManagerPage.tsx:31` arranca en `overview` e ignora la URL) | — | no | OK | ídem | sí |
| `/users` / `/roles` | `settings_users`, `settings_roles` | — | no | OK | ídem | sí |
| `/profile` | `settings_profile` + `Sidebar.tsx:143` | — | **ruta permitida pero sin ningún enlace móvil** | sin guard | — | sí (web) |
| `*` | — | — | → `/` | — | — | — |

### 2.b Rutas DIRECT_URL_ONLY (sin entrada de menú ni enlace in-app)

| Ruta | ¿Legítimamente interna? | Juicio |
|---|---|---|
| `/my-pending` | **No** — página funcional («Mis Pendientes», `nav.myPending` existe) sin ninguna vía de acceso; el hook `useMyPending` tampoco se usa | **GAP** funcional móvil (ver 2.c) |
| `/masters/{20 entidades ≠ farms}` | **No** — el único enlace de Maestros aterriza en `farms` y `MasterListPage` no ofrece cambio de entidad | **GAP crítico**: 20 de 21 maestros solo por URL escrita |
| `/reports/lot/:id` (id≠2) | **No** — `ReportsPage.tsx:193` enlaza `lot/2` fijo; el detalle de lote no enlaza a su reporte | GAP medio |
| `/kpi` (web) | Sí — concepto móvil; en web renderiza el mismo dashboard | aceptable |
| `/poultry` (hub legado) | Sí — compatibilidad; móvil redirige | aceptable (pero contador «6» fijo, `ProcessHubPage.tsx:45`) |
| `/processes*` | Sí — redirects legados | aceptable |
| `/masters/genetic-lines/:id/weight-curves` | Sí — desde fila (rowAction) | correcto |
| `/operations` (web) | Parcial — solo desde pie de `ProcessStagePage` y tras guardar; no hay entrada «Operaciones/Historial» en menú | GAP medio |
| `/profile` (móvil) | No — accesible por ruta, inalcanzable por UI | GAP (ver 2.c) |

### 2.c Móvil (`view_type='mobile'`)

`MOBILE_TOP_LEVEL_KEYS = {'poultry'}` (`navigationConfig.ts:264`): en móvil solo sobrevive el contenedor `poultry` con **todos** sus hijos (el filtro solo actúa a profundidad 0, `:268`): Lotes ✔, Progenitoras/Reproductoras (Cría/Producción), Incubadora, Engorde. `MobileNav.tsx:18-22`: `poultry` (`operations:read`+unidades), `home` y `kpi` (`dashboard:read`). Cabecera móvil (`Header.tsx:158-198`): marca, empresa (solo badge), campana, idioma. **Sin logout, sin perfil, sin selector de empresa.**

| Flujo | ¿Completable en móvil? | Evidencia |
|---|---|---|
| Registrar operación (6 etapas según unidad) | **Sí**: `/menu/poultry` → drill → `/poultry/:bu/:phase` → tile → `/operations/new?type=` → guardar → `/operations` | `MenuHubPage`, `ProcessStagePage.tsx:47-50`, `OperationFormPage.tsx:455` |
| Ver «mis pendientes» | **No**: `/my-pending` inalcanzable; `/operations` lista todo (no filtra `registered_by_me`) | `App.tsx:262`, grep |
| Ver detalle de lote | Sí (hub poultry → Lotes → tarjeta) | `LotListPage.tsx:79` |
| Enviar/reenviar a revisión | Sí, si se llega al detalle: `/operations` → «Editar» → detalle → botón (gate `operations:create`+unidad) | `OperationDetailPage.tsx:120-125,183-193` |
| Subir evidencia | Sí (área de subida) | `OperationDetailPage.tsx:326-350` |
| Descargar/previsualizar evidencia | **Degradado**: botones `opacity-0 group-hover:opacity-100` invisibles sin hover | `OperationDetailPage.tsx:287` |
| Ver notificaciones | Sí (campana en cabecera móvil), panel recortado a la izquierda (ver 3) | `Header.tsx:184`, `NotificationBell.tsx:142` |
| Cambiar idioma | Sí | `Header.tsx:188-196` |
| Cerrar sesión | **No** (`<lg`): logout solo en cabecera desktop `hidden lg:flex` (`Header.tsx:50,147-152`) y en `Sidebar` (no montado para móvil) y en `MobileDrawer` (no montado) | `AppLayout.tsx:13-20` |
| Perfil / cambiar contraseña | **No** (sin enlace) | — |
| Cambiar empresa (super admin móvil) | No (selector solo desktop, `Header.tsx:76-89`) | edge |
| Web-only por diseño | review, approvals, masters, users, roles, audit, sap, unit-access, `/lots/new`, `/reports/sap`; `WebOnlyRoute` → `/` → `/menu/poultry` **sin mensaje** | `App.tsx:68-72` |

Telegram Mini App (`hooks/useTelegram.ts`, `App.tsx:183-202`): back nativo → `navigate(-1)` salvo en raíces `/`, `/login`, `/kpi`, `/menu/poultry`; confirmación de cierre siempre activa; token en `localStorage` en TMA (`auth.store.ts:60-66`). Impacto: coherente con el flujo móvil; tras guardar (`/operations`) el back nativo vuelve al formulario ya enviado (historial no reemplazado, `OperationFormPage.tsx:455` usa `navigate` sin `replace`). Menor.

### 2.d Paridad de guardas nav ↔ ruta

- `/reports`, `/reports/lot/:id`, `/review*`, `/approvals`: nav exige `requiresUnits`, ruta no (`App.tsx:267-274`). Ruta más permisiva que menú; el backend sigue siendo autoridad. *Bajo*.
- `/operations/new` exige `operations:create`, pero los accesos (`OperationTile`, `StageTimeline`) se muestran con solo `operations:read` → tile → «No tiene permiso» (callejón). `LotDetailPage.tsx:228` sí gatea. *Medio*.
- Dos textos de denegación distintos: `common.noPermission` (`CapabilityRoute`) vs `admin.forbidden` (`PermissionRoute`, `/admin/unit-access`). *Bajo*.
- `ProtectedRoute` no conserva `returnTo`: tras login siempre `/`. *Bajo*.
- `WebOnlyRoute` redirige en silencio a móvil. *Bajo*.

### 2.e Estado activo

- `SidebarItem.tsx:42` clase activa `bg-white[0.12]` es **inválida en Tailwind** (debería ser `bg-white/[0.12]`) → el ítem activo solo se distingue por `text-white font-medium` frente a `text-white/55`. *Cosmético*.
- Sin ítem activo durante el flujo principal (`/operations*`), `/kpi`, `/my-pending`; en MobileNav tampoco en `/lots*` (`MobileNav.tsx:39-44`). *Bajo*.

### 2.f Home para roles operativos sin `dashboard:read` (nota N-1 de `audit/ga-uat-08/GA_OWNER_UAT_R188_OBSERVATIONS.md:21`)

`HomeRoute` (`App.tsx:110-114`) renderiza `DashboardPage` **sin guard** para web. `DashboardPage.tsx:94-105` pide `/dashboard/admin` → 403 → `error` = «Permiso requerido: dashboard:read» (`security.py:227`) → pantalla con solo «Reintentar» (`window.location.reload()`, `:135-141`). El ítem `dashboard` desaparece del menú (`navigationConfig.ts:88`), pero **todo** converge en `/`: `LoginPage.tsx:39` (primera pantalla tras login), `MenuHubPage.tsx:82,100` (botón «Atrás» en raíz de hub), `Breadcrumbs.tsx:42` (icono casa), `PoultryHubLegacyRoute`, `WebOnlyRoute`, `*`. **No hay landing utilizable**: el usuario ve un error como primera pantalla y tras cada «volver». Confirmado y de alcance mayor que «pre-existente informativo». Propuesta: `HomeRoute` con fallback a `/menu/poultry` (o primer hub visible de `filterNavItemsBySession`) cuando `!hasPermission(user,'dashboard:read')`.

---

## 3. RESPONSIVE (estático, referencia 390×844)

Contexto global: `index.css:44-46` fuerza `font-size:16px` en inputs (evita zoom iOS ✔); shell con padding 12 px móvil (`index.css:107-119`); `main` `pb-24 lg:pb-0` (`AppLayout.tsx:15`) para la barra inferior; `SearchSelect` usa `<select>` nativo `<1024px` (`SearchSelect.tsx:38-39,99-121`) ✔; `Modal` `max-h-[90dvh]` + `items-end sm:items-center` ✔; tablas de listado con alternativa en tarjetas (`LotListPage:75/94`, `ReviewCenter:276/345`, `ApprovalPanel:203/256`, `UsersPage:108/110`) ✔; `DataTable.tsx:49`, `LotDetailPage.tsx:275`, `WeightCurvesPage.tsx:183,330`, `RolesPage.tsx:120,199` con `overflow-x-auto` ✔.

| # | file:line | Hallazgo | Clase |
|---|---|---|---|
| R1 | `AppLayout.tsx:13-20`, `Sidebar.tsx:73` (`hidden lg:flex`), `Header.tsx:50` (`hidden lg:flex`), `MobileDrawer` no montado | Usuario **web** en pantalla `<1024px` (tablet vertical, teléfono): sin sidebar, sin barra inferior, sin hamburguesa, **sin logout** (solo en cabecera desktop). Navegación imposible salvo URL/atrás | **FUNCIONAL** |
| R2 | `Header.tsx:158-198` + `AppLayout.tsx:20` | Usuario **móvil**: sin logout ni perfil en ninguna superficie `<lg`; en `≥lg` pierde la barra inferior (`MobileNav` `lg:hidden`) y la cabecera desktop no tiene enlaces de navegación | **FUNCIONAL** |
| R3 | `OperationDetailPage.tsx:287` | Acciones de evidencia (descargar/previsualizar/borrar) con `opacity-0 group-hover:opacity-100`: invisibles en táctil | **FUNCIONAL** (móvil) |
| R4 | `OperationFormPage.tsx:1464-1469` | Botón «eliminar máquina» (`hatchery_inspection`, i>0) `absolute top-2 right-2` sin ancestro `relative` (revisado hasta `AppLayout`) → se posiciona respecto al documento, debajo de la cabecera `sticky z-20`: inalcanzable | **FUNCIONAL** (menor: la fila vacía se descarta al serializar, F-01d) |
| R5 | `NotificationBell.tsx:142` con la campana en `Header.tsx:181-196` | Panel `absolute right-0 w-[min(22rem,calc(100vw-2rem))]` anclado a la campana, que está ~66 px a la izquierda del borde (botón idioma) → a 390 px el panel sobresale ~44 px por la izquierda; primeros caracteres de cada aviso recortados | **FUNCIONAL** leve (única superficie de avisos de rechazo, según `NotificationBell.tsx:4-5`) |
| R6 | `pages/review/ReviewDetail.tsx:112` | `max-w-[200px] truncate` en observaciones sin `title`: el revisor no puede leer el texto completo | FUNCIONAL (web-only; información oculta a cualquier ancho) |
| R7 | `ReviewDetail.tsx:224-231,245-252` | `input w-48` + botón en `flex` sin `wrap` → desborda horizontalmente `<420px` | COSMÉTICO (web-only) |
| R8 | `Toast.tsx:67` | `fixed top-4 right-4 max-w-sm` (384 px) → a 390 px sobresale 10 px por la izquierda y tapa la cabecera | COSMÉTICO |
| R9 | `OperationFormPage.tsx:1377-1383` | etiqueta `w-44 shrink-0` (176 px) + input `flex-1` → input ~178 px en 390 px | COSMÉTICO |
| R10 | `DashboardPage.tsx:329` | `grid grid-cols-3` fijo (3 KPI) a 390 px: ~114 px por tarjeta con etiquetas mayúsculas (`To review`, `Registros`) | COSMÉTICO (riesgo de corte en EN) |
| R11 | `LotDetailPage.tsx:151-196` | cabecera `flex` sin `wrap` con título + 2 botones (`Iniciar Producción`, `Cerrar Lote`) → título comprimido | COSMÉTICO (botones gateados por `lots:create`) |
| R12 | `ApprovalPanel.tsx:174-186` | barra de lote `justify-between` con 2 botones sin `wrap` | COSMÉTICO (web-only) |
| R13 | `Header.tsx:188-196` (idioma ~30 px alto), `NotificationBell.tsx:125` (`h-7 w-7`=28 px), `ProcessStagePage.tsx:82-95` (toggle `py-1.5 text-xs`), `ReviewCenter.tsx:449-453` (paginación `px-3 py-1.5`), `SubNavHeader.tsx:54` (`w-8 h-8`), `LotListPage.tsx:62-70` (filtros `py-1.5`) | Objetivos táctiles < 44 px | ACCESIBILIDAD/COSMÉTICO |
| R14 | `OperationFormPage.tsx` (69 `type="number"`) | sin `inputMode="decimal"/"numeric"`: teclado numérico no garantizado en iOS para decimales | COSMÉTICO/usabilidad |
| R15 | `index.css:76-79` | `select { background-image:none }` en `<1024px`: selects sin chevron (parecen inputs de texto) | COSMÉTICO |
| R16 | `Modal.tsx`, `ConfirmDialog.tsx:64`, `UsersPage.tsx:115`, `RolesPage.tsx:160-161`, `OperationDetailPage.tsx:356-368` | modales con `p-4`, `max-h-[90vh/dvh]`, `overflow-y-auto`; sin alturas fijas | OK |
| R17 | `ReviewCenter.tsx:181`, `AuditPage.tsx:116`, `SapManagerPage.tsx:146` | tabs con `overflow-x-auto` + `scrollbar-hide` (clase no definida en `index.css`; inocuo) | OK |
| R18 | `MobileNav.tsx:51-58` | barra inferior `fixed` con `safe-area-bottom`; el CTA «Guardar» (`OperationFormPage.tsx:2113`) queda por encima gracias a `pb-24` | OK |
| R19 | `LoginPage.tsx:53` `max-w-[380px]` + `px-4` | 358 px útiles a 390 | OK |

Sin `hidden md:flex` sobre inputs obligatorios ni CTAs primarios (grep: los únicos `hidden lg:block`/`lg:hidden` alternan tabla↔tarjetas; `ProcessHubPage.tsx:43` oculta solo estadísticas decorativas).

---

## 4. GAP REGISTER

Severidad propuesta: **Crítica** (bloquea flujo o desinforma al usuario en pantalla crítica) · **Alta** · **Media** · **Baja**.

| # | Clase | ¿Funcional? | Severidad | Evidencia |
|---|---|---|---|---|
| G-01 | DISCOVERABILITY_GAP | Sí | **Crítica** | 20/21 maestros solo por URL: `App.tsx:220` redirige a `/masters/farms`; `MasterListPage.tsx` sin selector de entidad; único ítem `masters` (`navigationConfig.ts:238-247`); enlaces `/masters/*` solo en `App.tsx:244`, `WeightCurvesPage.tsx:151` |
| G-02 | DISCOVERABILITY_GAP | Sí | **Crítica** | Home sin `dashboard:read` = pantalla de error «Permiso requerido» + Reintentar (`App.tsx:110-114`, `DashboardPage.tsx:94-105,130-143`), destino de login (`LoginPage.tsx:39`), Atrás de hub (`MenuHubPage.tsx:100`), migas (`Breadcrumbs.tsx:42`), `*`; N-1 confirmada y ampliada |
| G-03 | RESPONSIVE_GAP | Sí | **Crítica** | Usuario web `<1024px` sin navegación ni logout (R1): `AppLayout.tsx:13-20`, `Sidebar.tsx:73`, `Header.tsx:50`, `MobileDrawer.tsx` no montado |
| G-04 | DISCOVERABILITY_GAP | Sí | **Alta** | Móvil sin logout ni perfil (R2): `Header.tsx:158-198`, `MobileNav.tsx:18-22`, `navigationConfig.ts:264` |
| G-05 | DISCOVERABILITY_GAP | Sí | **Alta** | `/my-pending` inalcanzable (`App.tsx:262`; sin `Link`/`navigate`; `useMyPending` sin uso) → flujo «ver mis pendientes» no completable |
| G-06 | I18N_GAP | Sí (desinforma) | **Alta** | Columnas y labels de 21 maestros = «Editar»/«Guardar»: `App.tsx:136-165` → `MasterListPage.tsx:122,196` |
| G-07 | I18N_GAP | No | **Alta** | Enumerados crudos en pantallas críticas: `OperationListPage.tsx:85` (status), `OperationDetailPage.tsx:196,221,240`, `ReviewDetail.tsx:95,125,153,198`, `LotDetailPage.tsx:319,326` |
| G-08 | I18N_GAP | No | **Alta** | Namespaces vacíos: `audit.actions/modules` (0 vs 22/11), `roles.actions/modules` (0 vs 9/13) → `AuditPage.tsx:150,162,216`, `RolesPage.tsx:205,213` |
| G-09 | I18N_GAP | No | **Alta** | Validación de alta de lote solo en español: `LotFormPage.tsx:21-23,169,186,227` |
| G-10 | I18N_GAP | No | **Media** | 15 claves ausentes con fallback español fijo: `DashboardPage.tsx:155-170` (home móvil), `LotReportPage.tsx:117,120,129-135,144,153`, `AuditPage.tsx:141,154` |
| G-11 | I18N_GAP | No | **Media** | Errores del backend en español (110 `detail=`) mostrados tal cual a EN + 422 Pydantic en inglés: `Toast.tsx:100-140`; superficies listadas en 1.e |
| G-12 | I18N_GAP | No | **Media** | `alerts.type.weight_deviation` ausente (`backend/app/operations/service.py:729`) → «weight deviation» en `DashboardPage.tsx:52` |
| G-13 | I18N_GAP | No | **Media** | Fechas con locale del navegador en vez del app (`MyPendingPage.tsx:102`, `ReviewDetail.tsx:183,200`, `AuditPage.tsx:88`, `SapManagerPage.tsx:239,297`, `TraceabilityTree.tsx:180-267`); ISO crudo en el resto; `export.ts:50` fijo `es-VE`; números `toFixed` vs `toLocaleString` mezclados |
| G-14 | I18N_GAP | No | **Media** | `EQUIPMENT_TYPES` español fijo: `OperationFormPage.tsx:1243-1244,1327`; cabeceras/título de exportación: `ReportsPage.tsx:42-52,58` |
| G-15 | I18N_GAP | Sí (CTA engañoso) | **Media** | `common.edit` («Editar») sobre enlace a detalle: `OperationListPage.tsx:89`; `common.back` como «Anterior»: `ApprovalPanel.tsx:339`, `MasterListPage.tsx:167`; `process.hub.title` como cabecera/optgroup: `OperationListPage.tsx:65`, `DashboardPage.tsx:365` |
| G-16 | RESPONSIVE_GAP | Sí (móvil) | **Media** | Acciones de evidencia invisibles en táctil: `OperationDetailPage.tsx:287` (R3) |
| G-17 | RESPONSIVE_GAP | Sí (leve) | **Media** | Panel de notificaciones recortado a 390 px: `NotificationBell.tsx:142` + `Header.tsx:181-196` (R5) |
| G-18 | DISCOVERABILITY_GAP | Sí | **Media** | `/reports/lot/:id` solo para lote 2 (`ReportsPage.tsx:193` fijo; `lotId` ignorado); `LotDetailPage` no enlaza su reporte |
| G-19 | DISCOVERABILITY_GAP | No | **Media** | Sin entrada de menú para `/operations` (historial); acceso solo web desde `ProcessStagePage.tsx:120` y tras guardar; sin ítem activo en `/operations*` |
| G-20 | DISCOVERABILITY_GAP | No | **Media** | Tiles de operación sin gate `operations:create` → callejón «No tiene permiso»: `OperationTile.tsx:60-72`, `StageTimeline.tsx:155-164` vs `LotDetailPage.tsx:228` |
| G-21 | DISCOVERABILITY_GAP | No | **Baja** | 4 tarjetas SAP → mismo destino `/sap` sin tab (`navigationConfig.ts:203-206`, `SapManagerPage.tsx:31`); 2 tarjetas de reportes → `/reports` (`:221-222`) |
| G-22 | RESPONSIVE_GAP | Sí (menor) | **Baja** | Botón eliminar máquina mal posicionado: `OperationFormPage.tsx:1464-1469` (R4) |
| G-23 | ACCESSIBILITY_GAP | No | **Baja** | Observaciones truncadas sin `title`: `ReviewDetail.tsx:112` (R6); objetivos táctiles <44 px (R13); `alt="preview"` `OperationDetailPage.tsx:367`; checkboxes nativos en matriz de permisos `RolesPage.tsx:217` |
| G-24 | I18N_GAP | No | **Baja** | Texto inglés en bundle ES: `reports.sapComparisonLink`, `users.mobile`; unidades sueltas (`aves`, `cap.`, `sem.`, `g/día`, `días`); `searchPlaceholder` español (`OperationFormPage.tsx:1997,2033`); `'Operador'` (`DashboardPage.tsx:193`) |
| G-25 | I18N_GAP | No | **Baja** | Latentes: `process.flowDesc.bird_transfer` ausente (`processCatalog.ts:351`); `evidence.types.signature/audio` ausentes vs `validators.py:617`; `NotificationType` TS omite `lot_near_close` (`services/notifications.ts:14-19`); hook `useOperations.ts` con textos español (muerto) |
| G-26 | DISCOVERABILITY_GAP | No | **Baja** | Paridad guardas: nav `requiresUnits` sin equivalente en ruta (`App.tsx:267-274`); dos textos de denegación (`common.noPermission` / `admin.forbidden`); `WebOnlyRoute` redirige sin mensaje; sin `returnTo` tras login; `ProtectedRoute.roles` muerto (`App.tsx:58-64`) |
| G-27 | RESPONSIVE_GAP | No | **Baja** | Cosméticos R7–R12, R14, R15; clase activa inválida `bg-white[0.12]` (`SidebarItem.tsx:42`); clases residuales `hover:bg-slate-100:bg-dark-card` (`Header.tsx:61`, `MobileDrawer.tsx:117`…) |
| G-28 | DISCOVERABILITY_GAP | No | **Baja** | Código muerto de navegación: `MobileDrawer.tsx`, `SidebarSubmenu.tsx`, `ui.store` drawer, `getSectionKeyForPath`, `hooks/use*.ts` (ninguno importado) — riesgo de que se crea que existe un drawer móvil |

Incidental (fuera de alcance, detectado de paso): `pages/users/UsersPage.tsx:115-132` duplica los campos nombre/apellido/email/teléfono/contraseña dentro del mismo modal (líneas 117-120 y 127-130).

---

## 5. Resumen de conteos

- I18N: paridad 0/0; 16 claves ausentes (15 con fallback español, 1 latente); 4 namespaces dinámicos vacíos; ~15 puntos de enumerado crudo; 1 enum backend sin clave (`weight_deviation`); 110 mensajes backend en español sin mapeo; fechas: 1 correcto / 10 con locale de navegador / resto ISO.
- Navegación: 37 rutas; DIRECT_URL_ONLY ilegítimas: `/my-pending`, `/masters/{20}`, `/reports/lot/:id`, `/profile` (móvil); home sin `dashboard:read` = error.
- Responsive: 5 FUNCIONALES (R1–R5), 1 funcional web-only (R6), 9 cosméticos/a11y.
