import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from './stores/auth.store'
import { ToastProvider } from './components/Toast'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import MasterListPage from './pages/masters/MasterListPage'
import OperationListPage from './pages/operations/OperationListPage'
import OperationFormPage from './pages/operations/OperationFormPage'
import OperationDetailPage from './pages/operations/OperationDetailPage'
import ProcessHubPage from './pages/operations/ProcessHubPage'
import ProcessStagePage from './pages/operations/ProcessStagePage'
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
import LotListPage from './pages/lots/LotListPage'
import LotDetailPage from './pages/lots/LotDetailPage'
import LotFormPage from './pages/lots/LotFormPage'
import ProfilePage from './pages/users/ProfilePage'

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

const masterEntities = [
  { entity: 'companies', title: 'masters.companies', cols: [{ key: 'name', labelKey: 'masters.companies' }, { key: 'tax_id', labelKey: 'common.edit' }, { key: 'country', labelKey: 'common.save' }] },
  { entity: 'farms', title: 'masters.farms', cols: [{ key: 'name', labelKey: 'masters.farms' }, { key: 'code', labelKey: 'common.edit' }, { key: 'location', labelKey: 'common.save' }] },
  { entity: 'houses', title: 'masters.houses', cols: [{ key: 'name', labelKey: 'masters.houses' }, { key: 'capacity', labelKey: 'common.edit' }] },
  { entity: 'hatcheries', title: 'masters.hatcheries', cols: [{ key: 'name', labelKey: 'masters.hatcheries' }, { key: 'code', labelKey: 'common.edit' }] },
  { entity: 'suppliers', title: 'masters.suppliers', cols: [{ key: 'name', labelKey: 'masters.suppliers' }, { key: 'sap_code', labelKey: 'common.edit' }] },
  { entity: 'genetic-lines', title: 'masters.geneticLines', cols: [{ key: 'name', labelKey: 'masters.geneticLines' }, { key: 'code', labelKey: 'common.edit' }] },
  { entity: 'breeds', title: 'masters.breeds', cols: [{ key: 'name', labelKey: 'masters.breeds' }] },
  { entity: 'feed-types', title: 'masters.feedTypes', cols: [{ key: 'name', labelKey: 'masters.feedTypes' }, { key: 'code', labelKey: 'common.edit' }] },
  { entity: 'vaccines', title: 'masters.vaccines', cols: [{ key: 'name', labelKey: 'masters.vaccines' }, { key: 'laboratory', labelKey: 'common.edit' }] },
  { entity: 'mortality-causes', title: 'masters.mortalityCauses', cols: [{ key: 'name', labelKey: 'masters.mortalityCauses' }, { key: 'category', labelKey: 'common.edit' }] },
  { entity: 'transports', title: 'masters.transports', cols: [{ key: 'name', labelKey: 'masters.transports' }, { key: 'plate', labelKey: 'common.edit' }] },
  { entity: 'processing-plants', title: 'masters.processingPlants', cols: [{ key: 'name', labelKey: 'masters.processingPlants' }, { key: 'location', labelKey: 'common.save' }] },
]

export default function App() {
  const { token, isLoading, fetchMe } = useAuthStore()

  // Restore full session on app load — fetchMe always runs when token exists
  useEffect(() => {
    if (token && isLoading) {
      fetchMe()
    }
  }, [token, isLoading, fetchMe])

  return (
    <ToastProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          {/* Web-only: Masters */}
          <Route path="/masters" element={<WebOnlyRoute><Navigate to="/masters/farms" replace /></WebOnlyRoute>} />
          {masterEntities.map((m) => (
            <Route
              key={m.entity}
              path={`/masters/${m.entity}`}
              element={
                <WebOnlyRoute>
                  <MasterListPage
                    entity={m.entity}
                    titleKey={m.title}
                    columns={m.cols}
                    searchFields={['name']}
                  />
                </WebOnlyRoute>
              }
            />
          ))}
          {/* Shared: Processes, Operations, Lots, Reports — accessible by both web and mobile */}
          <Route path="/processes" element={<ProcessHubPage />} />
          <Route path="/processes/:stage" element={<ProcessStagePage />} />
          <Route path="/operations" element={<OperationListPage />} />
          <Route path="/operations/new" element={<OperationFormPage />} />
          <Route path="/operations/:id" element={<OperationDetailPage />} />
          <Route path="/my-pending" element={<MyPendingPage />} />
          <Route path="/lots" element={<LotListPage />} />
          <Route path="/lots/new" element={<WebOnlyRoute><LotFormPage /></WebOnlyRoute>} />
          <Route path="/lots/:id" element={<LotDetailPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/reports/lot/:id" element={<LotReportPage />} />
          <Route path="/reports/sap" element={<WebOnlyRoute><SapComparisonPage /></WebOnlyRoute>} />
          {/* Web-only: Review, Approvals, Audit, SAP, Users */}
          <Route path="/review" element={<WebOnlyRoute><ReviewCenter /></WebOnlyRoute>} />
          <Route path="/review/:id" element={<WebOnlyRoute><ReviewDetail /></WebOnlyRoute>} />
          <Route path="/review/:id/correct" element={<WebOnlyRoute><CorrectionForm /></WebOnlyRoute>} />
          <Route path="/approvals" element={<WebOnlyRoute><ApprovalPanel /></WebOnlyRoute>} />
          <Route path="/audit" element={<WebOnlyRoute><AuditPage /></WebOnlyRoute>} />
          <Route path="/sap" element={<WebOnlyRoute><SapManagerPage /></WebOnlyRoute>} />
          <Route path="/users" element={<WebOnlyRoute><UsersPage /></WebOnlyRoute>} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </ToastProvider>
  )
}
