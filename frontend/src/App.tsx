import { Routes, Route, Navigate, useParams, useNavigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from './stores/auth.store'
import { hasPermission } from './auth/permissions'
import { canAccessCapability, PRODUCTIVE_UNITS } from './auth/navigation'
import { useTelegram, useTelegramBackHandler } from './hooks/useTelegram'
import { normalizeLanguage } from './i18n'
import { ToastProvider } from './components/Toast'
import AppLayout from './components/layout/AppLayout'
import MastersHubPage from './pages/masters/MastersHubPage'
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import MasterListPage from './pages/masters/MasterListPage'
import WeightCurvesPage from './pages/masters/WeightCurvesPage'
import RolesPage from './pages/users/RolesPage'
import OperationListPage from './pages/operations/OperationListPage'
import OperationFormPage from './pages/operations/OperationFormPage'
import OperationDetailPage from './pages/operations/OperationDetailPage'
import PoultryHubPage from './pages/operations/PoultryHubPage'
import PoultryStagePage from './pages/operations/PoultryStagePage'
import MenuHubPage from './pages/operations/MenuHubPage'
import MyPendingPage from './pages/operations/MyPendingPage'
import ReviewCenter from './pages/review/ReviewCenter'
import ReviewDetail from './pages/review/ReviewDetail'
import CorrectionForm from './pages/review/CorrectionForm'
import ApprovalPanel from './pages/approvals/ApprovalPanel'
import ReportsPage from './pages/reports/ReportsPage'
import LotReportPage from './pages/reports/LotReportPage'
import SapComparisonPage from './pages/reports/SapComparisonPage'
import AuditPage from './pages/audit/AuditPage'
import SapManagerPage from './pages/sap/SapManagerPage'
import UsersPage from './pages/users/UsersPage'
import UnitAccessPage from './pages/admin/UnitAccessPage'
import LotListPage from './pages/lots/LotListPage'
import LotDetailPage from './pages/lots/LotDetailPage'
import LotFormPage from './pages/lots/LotFormPage'
import ProfilePage from './pages/users/ProfilePage'
import { STAGE_PATH_MAP } from './data/processCatalog'

function ProtectedRoute({ children, roles, webOnly }: { children: React.ReactNode; roles?: string[]; webOnly?: boolean }) {
 const { t } = useTranslation()
 const { isAuthenticated, isLoading, user } = useAuthStore()
 
 // Show nothing while restoring session
 if (isLoading) {
 return <div className="min-h-screen flex items-center justify-center bg-slate-50">
 <p className="text-slate-500 text-lg">{t('common.loading')}</p>
 </div>
 }
 
 if (!isAuthenticated) return <Navigate to="/login" replace />
 
 // Mobile users cannot access admin/web-only routes
 if (webOnly && user?.view_type === 'mobile') {
 return <Navigate to="/" replace />
 }
 
 // Role check: if roles specified, user must have one of them (or be super admin)
 if (roles && roles.length > 0) {
 const userRoleName = user?.role_id ? '' : 'super_admin'
 if (!roles.includes(userRoleName) && !user?.is_super_admin) {
 return <Navigate to="/" replace />
 }
 }
 return <>{children}</>
}

function WebOnlyRoute({ children }: { children: React.ReactNode }) {
 const { user } = useAuthStore()
 if (user?.view_type === 'mobile') return <Navigate to="/" replace />
 return <>{children}</>
}

/** GA-FE-02 · Guard por PERMISO (nunca por nombre de rol). El backend sigue siendo la
 * autoridad final; esto solo evita mostrar una pantalla sin capacidad real. */
function PermissionRoute({ permission, children }: { permission: string; children: React.ReactNode }) {
 const { t } = useTranslation()
 const { user } = useAuthStore()
 if (!hasPermission(user, permission)) {
 return <div role="alert" className="py-8 text-center text-sm font-medium text-slate-600">{t('admin.forbidden')}</div>
 }
 return <>{children}</>
}

/** GA-FE-03 · Guarda de ruta por CAPACIDAD — misma política que la navegación
 * (`auth/navigation`): permiso canónico + unidad productiva. Independiente del estado del
 * menú y del backend (que sigue denegando por su cuenta). Nunca por nombre de rol. */
function CapabilityRoute({ permission, businessUnit, requiresUnits, children }: { permission?: string; businessUnit?: string; requiresUnits?: boolean; children: React.ReactNode }) {
 const { t } = useTranslation()
 const { user } = useAuthStore()
 if (!canAccessCapability({ permission, businessUnit, requiresUnits }, user)) {
 return <div role="alert" className="py-8 text-center text-sm font-medium text-slate-600">{t('common.noPermission')}</div>
 }
 return <>{children}</>
}

/** `/poultry/:birdType/:phase?` — la URL NOMBRA la unidad: la guarda exige elegibilidad real
 * (efectiva normal / habilitada global con contexto). Un `birdType` desconocido se delega a la
 * página (que redirige), sin inventar unidad. */
function PoultryStageRoute() {
 const { birdType } = useParams<{ birdType?: string }>()
 const bu = birdType && (PRODUCTIVE_UNITS as readonly string[]).includes(birdType) ? birdType : undefined
 return (
 <CapabilityRoute permission="operations:read" businessUnit={bu}>
 <PoultryStagePage />
 </CapabilityRoute>
 )
}

function HomeRoute() {
 const { user } = useAuthStore()
 if (user?.view_type === 'mobile') return <Navigate to="/menu/poultry" replace />
 return <DashboardPage />
}

/**
 * ProcessStageRedirect — mapea rutas legacy /processes/:stage a /poultry/:birdType/:phase
 * Si no existe mapeo, vuelve al menú jerárquico de Gestión Avícola.
 */
const STAGE_ROUTE_MAP: Record<string, string> = { ...STAGE_PATH_MAP }

function ProcessStageRedirect() {
 const { stage } = useParams<{ stage: string }>()
 const target = stage ? STAGE_ROUTE_MAP[stage] : null
 if (target) return <Navigate to={target} replace />
 return <Navigate to="/menu/poultry" replace />
}

function PoultryHubLegacyRoute({ children }: { children: React.ReactNode }) {
 const { user } = useAuthStore()
 if (user?.view_type === 'mobile') return <Navigate to="/menu/poultry" replace />
 return <>{children}</>
}

const masterEntities = [
 { entity: 'companies', title: 'masters.companies', cols: [{ key: 'name', labelKey: 'masters.companies' }, { key: 'tax_id', labelKey: 'common.edit' }, { key: 'country', labelKey: 'common.save' }] },
 { entity: 'farms', title: 'masters.farms', cols: [{ key: 'name', labelKey: 'masters.farms' }, { key: 'code', labelKey: 'common.edit' }, { key: 'location', labelKey: 'common.save' }] },
 { entity: 'houses', title: 'masters.houses', cols: [{ key: 'name', labelKey: 'masters.houses' }, { key: 'capacity', labelKey: 'common.edit' }] },
 { entity: 'hatcheries', title: 'masters.hatcheries', cols: [{ key: 'name', labelKey: 'masters.hatcheries' }, { key: 'code', labelKey: 'common.edit' }] },
 { entity: 'suppliers', title: 'masters.suppliers', cols: [{ key: 'name', labelKey: 'masters.suppliers' }, { key: 'sap_code', labelKey: 'common.edit' }] },
 // `GA-REM-039` / `OD-08`. El área es dato maestro configurable: se administra con la misma
 // pantalla parametrizada que los otros veintiuno, no con un módulo nuevo.
 { entity: 'areas', title: 'masters.areas', cols: [{ key: 'name', labelKey: 'masters.areas' }, { key: 'code', labelKey: 'common.edit' }] },
 { entity: 'genetic-lines', title: 'masters.geneticLines', cols: [{ key: 'name', labelKey: 'masters.geneticLines' }, { key: 'code', labelKey: 'common.edit' }] },
 { entity: 'breeds', title: 'masters.breeds', cols: [{ key: 'name', labelKey: 'masters.breeds' }] },
 { entity: 'feed-types', title: 'masters.feedTypes', cols: [{ key: 'name', labelKey: 'masters.feedTypes' }, { key: 'code', labelKey: 'common.edit' }] },
 { entity: 'vaccines', title: 'masters.vaccines', cols: [{ key: 'name', labelKey: 'masters.vaccines' }, { key: 'laboratory', labelKey: 'common.edit' }] },
 { entity: 'mortality-causes', title: 'masters.mortalityCauses', cols: [{ key: 'name', labelKey: 'masters.mortalityCauses' }, { key: 'category', labelKey: 'common.edit' }] },
 { entity: 'transports', title: 'masters.transports', cols: [{ key: 'name', labelKey: 'masters.transports' }, { key: 'plate', labelKey: 'common.edit' }] },
 { entity: 'processing-plants', title: 'masters.processingPlants', cols: [{ key: 'name', labelKey: 'masters.processingPlants' }, { key: 'location', labelKey: 'common.save' }] },
 // `GA-REM-033 AC04` / `R-90`. Siete maestros que `docs/02 §3.2` exige no tenían ninguna
 // forma de gestionarse: no estaban en esta lista, que es la única fuente de rutas de
 // maestros, así que solo podían poblarse por API o por SQL. `productive-phases` gobierna la
 // fase de un lote, `cull-causes` es obligatoria al registrar un descarte y
 // `correction-types` al corregir.
 //
 // Se añaden como entradas, no como pantallas: la administración está parametrizada sobre
 // `MasterListPage` y sus claves i18n ya existían para los diecinueve.
 { entity: 'incubators', title: 'masters.incubators', cols: [{ key: 'name', labelKey: 'masters.incubators' }, { key: 'capacity', labelKey: 'common.edit' }] },
 { entity: 'hatchers', title: 'masters.hatchers', cols: [{ key: 'name', labelKey: 'masters.hatchers' }, { key: 'capacity', labelKey: 'common.edit' }] },
 { entity: 'productive-phases', title: 'masters.productivePhases', cols: [{ key: 'name', labelKey: 'masters.productivePhases' }, { key: 'code', labelKey: 'common.edit' }, { key: 'order', labelKey: 'common.save' }] },
 { entity: 'medications', title: 'masters.medications', cols: [{ key: 'name', labelKey: 'masters.medications' }, { key: 'laboratory', labelKey: 'common.edit' }] },
 { entity: 'cull-causes', title: 'masters.cullCauses', cols: [{ key: 'name', labelKey: 'masters.cullCauses' }, { key: 'category', labelKey: 'common.edit' }] },
 { entity: 'rejection-reasons', title: 'masters.rejectionReasons', cols: [{ key: 'name', labelKey: 'masters.rejectionReasons' }, { key: 'category', labelKey: 'common.edit' }] },
 { entity: 'correction-types', title: 'masters.correctionTypes', cols: [{ key: 'name', labelKey: 'masters.correctionTypes' }, { key: 'description', labelKey: 'common.edit' }] },
]

export default function App() {
 const { t, i18n } = useTranslation()
 const { token, isLoading, fetchMe } = useAuthStore()
 const navigate = useNavigate()
 const location = useLocation()
 const { enableClosingConfirmation } = useTelegram()
 const appLanguage = normalizeLanguage(i18n.resolvedLanguage || i18n.language)

 // Restore full session on app load — fetchMe always runs when token exists
 useEffect(() => {
 if (token && isLoading) {
 fetchMe()
 }
 }, [token, isLoading, fetchMe])

 // Telegram Mini App: enable native closing confirmation so the user is
 // alerted before exiting the app (swipe down or hardware back at root).
 useEffect(() => {
   enableClosingConfirmation()
 }, [enableClosingConfirmation])

 // Determine if we are at a root/home route where the back button
 // should remain hidden so Telegram shows the native close icon.
 const normalizedPath = location.pathname.replace(/\/+$/, '') || '/'
 const isAtRoot =
   normalizedPath === '/' ||
   normalizedPath === '/login' ||
   normalizedPath === '/kpi' ||
   normalizedPath === '/menu/poultry'

 // Telegram Mini App:
 // - On sub-routes: native back routes within SPA (navigate -1).
 // - On root routes: hide native back so Telegram close UI is visible,
 //   and closing confirmation remains managed natively.
 useTelegramBackHandler(() => { navigate(-1) }, !isAtRoot)

 return (
 <ToastProvider>
 <Routes key={appLanguage}>
 <Route path="/login" element={<LoginPage />} />
 <Route
 element={
 <ProtectedRoute>
 <AppLayout />
 </ProtectedRoute>
 }
 >
 <Route path="/" element={<HomeRoute />} />
 <Route path="/kpi" element={<DashboardPage />} />
 {/* Menu hubs — grilla de opciones por área (capa de presentación) */}
 <Route path="/menu/:menuKey" element={<MenuHubPage />} />
 {/* Web-only: Masters */}
 {/* `R-196` (AC-07). Antes: `Navigate` fijo a `farms` — las demás entidades solo por URL. */}
 <Route path="/masters" element={<WebOnlyRoute><CapabilityRoute permission="masters:read"><MastersHubPage entities={masterEntities} /></CapabilityRoute></WebOnlyRoute>} />
 {/*
 `R-96` / `OD-06`. Las curvas de peso cuelgan de la línea genética: se llega a ellas
 desde su fila, no desde un módulo nuevo de primer nivel. La capacidad es lo que el
 propietario exige; una página aparte habría sido decisión nuestra.
 */}
 <Route
 path="/masters/genetic-lines/:id/weight-curves"
 element={<WebOnlyRoute><CapabilityRoute permission="masters:read"><WeightCurvesPage /></CapabilityRoute></WebOnlyRoute>}
 />
 {masterEntities.map((m) => (
 <Route
 key={m.entity}
 path={`/masters/${m.entity}`}
 element={
 <WebOnlyRoute>
 <CapabilityRoute permission="masters:read">
 <MasterListPage
 entity={m.entity}
 titleKey={m.title}
 columns={m.cols}
 searchFields={['name']}
 rowActions={m.entity === 'genetic-lines' ? [{
 label: t('curves.manage'),
 onClick: (item: any) => navigate(`/masters/genetic-lines/${item.id}/weight-curves`),
 }] : undefined}
 />
 </CapabilityRoute>
 </WebOnlyRoute>
 }
 />
 ))}
 {/* Shared: Poultry (new) + Processes (legacy redirects) */}
 <Route path="/poultry" element={<PoultryHubLegacyRoute><CapabilityRoute permission="operations:read" requiresUnits><PoultryHubPage /></CapabilityRoute></PoultryHubLegacyRoute>} />
 <Route path="/poultry/:birdType/:phase?" element={<PoultryStageRoute />} />
 {/* Legacy redirects — keep for backward compatibility */}
 <Route path="/processes" element={<Navigate to="/menu/poultry" replace />} />
 <Route path="/processes/:stage" element={<ProcessStageRedirect />} />
 {/* Operations, Lots, Reports — accessible by both web and mobile */}
 <Route path="/operations" element={<CapabilityRoute permission="operations:read"><OperationListPage /></CapabilityRoute>} />
 <Route path="/operations/new" element={<CapabilityRoute permission="operations:create"><OperationFormPage /></CapabilityRoute>} />
 <Route path="/operations/:id" element={<CapabilityRoute permission="operations:read"><OperationDetailPage /></CapabilityRoute>} />
 <Route path="/my-pending" element={<MyPendingPage />} />
 <Route path="/lots" element={<CapabilityRoute permission="lots:read"><LotListPage /></CapabilityRoute>} />
 <Route path="/lots/new" element={<WebOnlyRoute><CapabilityRoute permission="lots:create"><LotFormPage /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/lots/:id" element={<CapabilityRoute permission="lots:read"><LotDetailPage /></CapabilityRoute>} />
 <Route path="/admin/unit-access" element={<WebOnlyRoute><PermissionRoute permission="business_units:read"><UnitAccessPage /></PermissionRoute></WebOnlyRoute>} />
 <Route path="/reports" element={<CapabilityRoute permission="reports:read"><ReportsPage /></CapabilityRoute>} />
 <Route path="/reports/lot/:id" element={<CapabilityRoute permission="reports:read"><LotReportPage /></CapabilityRoute>} />
 <Route path="/reports/sap" element={<WebOnlyRoute><CapabilityRoute permission="reports:read"><SapComparisonPage /></CapabilityRoute></WebOnlyRoute>} />
 {/* Web-only: Review, Approvals, Audit, SAP, Users */}
 <Route path="/review" element={<WebOnlyRoute><CapabilityRoute permission="review:read"><ReviewCenter /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/review/:id" element={<WebOnlyRoute><CapabilityRoute permission="review:read"><ReviewDetail /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/review/:id/correct" element={<WebOnlyRoute><CapabilityRoute permission="corrections:correct"><CorrectionForm /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/approvals" element={<WebOnlyRoute><CapabilityRoute permission="approvals:approve"><ApprovalPanel /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/audit" element={<WebOnlyRoute><CapabilityRoute permission="audit:read"><AuditPage /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/sap" element={<WebOnlyRoute><CapabilityRoute permission="sap:read"><SapManagerPage /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/users" element={<WebOnlyRoute><CapabilityRoute permission="users:read"><UsersPage /></CapabilityRoute></WebOnlyRoute>} />
 {/* `GA-REM-034 AC04` / `R-92`. `docs/02 §3.1.3` exige administrar roles con permisos
 granulares y no había ninguna superficie: ni ruta ni componente. */}
 <Route path="/roles" element={<WebOnlyRoute><CapabilityRoute permission="users:read"><RolesPage /></CapabilityRoute></WebOnlyRoute>} />
 <Route path="/profile" element={<ProfilePage />} />
 <Route path="*" element={<Navigate to="/" replace />} />
 </Route>
 </Routes>
 </ToastProvider>
 )
}
