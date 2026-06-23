import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  useEffect(() => {
    api.get('/dashboard/admin')
      .then(r => setData(r.data))
      .catch((e: any) => {
        const msg = getErrorMessage(e, t('dashboard.errorLoading'))
        setError(msg)
        toast.error(msg)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-6 text-slate-500">{t('common.loading')}</div>
  }

  if (error) {
    return <div className="p-6 text-red-600 bg-red-50 rounded-lg">{error}</div>
  }

  if (!data || data.total_events === 0) {
    return (
      <div className="p-4 sm:p-6 max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">{t('nav.dashboard')}</h1>
        <p className="text-slate-500 mt-2">{t('dashboard.noData')}</p>
      </div>
    )
  }

  const cards = [
    { label: t('dashboard.totalEvents'), value: data?.total_events ?? '—', color: 'bg-blue-500' },
    { label: t('dashboard.pendingReview'), value: data?.pending_review ?? '—', color: 'bg-amber-500' },
    { label: t('dashboard.pendingApproval'), value: data?.pending_approval ?? '—', color: 'bg-teal-500' },
    { label: t('dashboard.last7Days'), value: data?.last_7_days ?? '—', color: 'bg-emerald-500' },
  ]

  const statusLabels: Record<string, string> = {
    registered: t('dashboard.registered'),
    pending_review: t('dashboard.pendingReview'),
    in_review: t('status.in_review'),
    returned: t('status.returned'),
    corrected: t('status.corrected'),
    approved: t('dashboard.approved'),
    rejected: t('status.rejected'),
    consolidated: t('status.consolidated'),
    sent_to_sap: t('status.sent_to_sap'),
    sap_confirmed: t('status.sap_confirmed'),
    cancelled: t('status.cancelled'),
  }

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">
        {t('nav.dashboard')}
      </h1>
      <p className="text-slate-500 mb-6">
        {t('dashboard.welcome')}{user?.first_name ? `, ${user.first_name}` : ''}
      </p>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {cards.map((card, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className={`w-9 h-9 rounded-lg ${card.color} flex items-center justify-center text-white text-sm mb-2`}>
              {i + 1}
            </div>
            <p className="text-xl sm:text-2xl font-bold text-slate-800">{card.value}</p>
            <p className="text-xs text-slate-500">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Status Distribution */}
      {data?.by_status && Object.keys(data.by_status).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">
          <h2 className="text-base font-semibold text-[#1E3A5F] mb-3">{t('dashboard.statusDistribution')}</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.by_status).map(([status, count]) => (
              <span key={status} className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                {statusLabels[status] || status}: {count as number}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Top Event Types */}
      {data?.top_event_types && Object.keys(data.top_event_types).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h2 className="text-base font-semibold text-[#1E3A5F] mb-3">{t('dashboard.topEventTypes')}</h2>
          <div className="space-y-2">
            {Object.entries(data.top_event_types).map(([etype, count]) => (
              <div key={etype} className="flex justify-between items-center text-sm">
                <span className="text-slate-600">{etype}</span>
                <span className="font-semibold text-slate-800">{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
