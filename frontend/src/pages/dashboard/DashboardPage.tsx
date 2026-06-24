import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { Bird, FileText, Clock, CheckCircle, TrendingDown, Wheat, Skull, Scale, Egg, Sparkles, AlertCircle } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Card, CardHeader, CardBody, Badge, statusToVariant } from '../../components/ui'
import { PROCESS_STAGES, flowForStage } from '../../data/processCatalog'

const BIRD_TYPE_COLORS: Record<string, string> = {
  grandparent: 'bg-purple-100 text-purple-700 border-purple-200',
  breeder:     'bg-blue-100 text-blue-700 border-blue-200',
  hatchery:    'bg-amber-100 text-amber-700 border-amber-200',
  broiler:     'bg-emerald-100 text-emerald-700 border-emerald-200',
}

export default function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const isMobileUser = user?.view_type === 'mobile'
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  useEffect(() => {
    const endpoint = isMobileUser ? '/dashboard/mobile' : '/dashboard/admin'
    api.get(endpoint)
      .then(r => setData(r.data))
      .catch((e: any) => {
        const msg = getErrorMessage(e, t('dashboard.errorLoading'))
        setError(msg)
        toast.error(msg)
      })
      .finally(() => setLoading(false))
  }, [isMobileUser])

  if (loading) {
    return (
      <div className="p-4 sm:p-6 max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 h-24 animate-pulse bg-slate-100" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-600 mb-3">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
          >
            {t('common.retry', 'Reintentar')}
          </button>
        </div>
      </div>
    )
  }

  // ── MOBILE OPERATOR DASHBOARD (REDESIGNED) ──────────────────────────────
  if (isMobileUser) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white pb-24">
        {/* Welcome header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={20} />
            <h1 className="text-2xl font-bold">{t('nav.home', 'Inicio')}</h1>
          </div>
          <p className="text-blue-100 text-sm">
            {t('dashboard.welcome')} {user?.first_name || 'Operador'}
          </p>
        </div>

        <div className="p-4 space-y-6">
          {/* KPI Section */}
          <div className="space-y-2">
            <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wide">
              {t('dashboard.todayMetrics', 'Hoy')}
            </h2>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-white rounded-xl border-2 border-blue-200 p-3 text-center shadow-sm">
                <div className="text-2xl font-bold text-blue-600">{data?.today_events ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold">
                  {t('dashboard.todayEvents', 'Operaciones')}
                </div>
              </div>
              <div className="bg-white rounded-xl border-2 border-amber-200 p-3 text-center shadow-sm">
                <div className="text-2xl font-bold text-amber-600">{data?.pending_corrections ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold">
                  {t('dashboard.pendingCorrections', 'Por revisar')}
                </div>
              </div>
              <div className="bg-white rounded-xl border-2 border-green-200 p-3 text-center shadow-sm">
                <div className="text-2xl font-bold text-green-600">{data?.approved_today ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold">
                  {t('dashboard.approvedToday', 'Aprobados')}
                </div>
              </div>
            </div>
          </div>

          {/* Alerts/Info */}
          {data?.pending_corrections && data.pending_corrections > 0 && (
            <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-3 flex items-start gap-2">
              <AlertCircle size={18} className="text-amber-600 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-amber-900">{t('dashboard.hasPendingCorrections', 'Tienes correcciones pendientes')}</p>
                <p className="text-xs text-amber-700 mt-1">{t('dashboard.checkAndReview', 'Revisa tus operaciones rechazadas')}</p>
              </div>
            </div>
          )}

          {/* 6 Procesos Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wide">
                {t('process.hub.title', '6 Procesos')}
              </h2>
              <Link to="/poultry" className="text-xs font-bold text-[#2563EB]">
                {t('common.viewAll', 'Ver todos')} →
              </Link>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {PROCESS_STAGES.map((stage, idx) => {
                const count = flowForStage(stage.key).length
                return (
                  <Link
                    key={stage.key}
                    to={`/poultry/${stage.key}`}
                    className={`group relative overflow-hidden rounded-3xl bg-gradient-to-br ${stage.gradient} p-4 text-white shadow-sm active:scale-[0.97] transition-all`}
                  >
                    <span className="absolute -top-2 -right-1 text-white/25 text-5xl font-black select-none">{idx + 1}</span>
                    <span className="inline-flex w-12 h-12 rounded-2xl bg-white/25 backdrop-blur items-center justify-center ring-1 ring-white/30 shadow-inner">
                      <stage.Icon size={26} strokeWidth={2.2} />
                    </span>
                    <h3 className="mt-3 text-sm font-extrabold leading-tight">{t(stage.labelKey, stage.fallback)}</h3>
                    <p className="text-[11px] font-semibold text-white/80 mt-0.5">{count} {t('process.hub.steps', 'pasos')}</p>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Quick actions section */}
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wide">
              {t('dashboard.quickActions', 'Acciones Rápidas')}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <Link
                to="/operations/new?type=feed_registration"
                className="flex flex-col items-center justify-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 border-2 border-yellow-300 rounded-xl hover:shadow-md transition-all active:scale-95"
              >
                <Wheat size={24} className="text-yellow-600 mb-2" />
                <span className="text-xs font-bold text-yellow-900 text-center">{t('events.feed_registration', 'Alimento')}</span>
              </Link>
              <Link
                to="/operations/new?type=weight_recording"
                className="flex flex-col items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl hover:shadow-md transition-all active:scale-95"
              >
                <Scale size={24} className="text-blue-600 mb-2" />
                <span className="text-xs font-bold text-blue-900 text-center">{t('events.weight_recording', 'Pesaje')}</span>
              </Link>
              <Link
                to="/operations/new?type=mortality_recording"
                className="flex flex-col items-center justify-center p-4 bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 rounded-xl hover:shadow-md transition-all active:scale-95"
              >
                <Skull size={24} className="text-red-600 mb-2" />
                <span className="text-xs font-bold text-red-900 text-center">{t('events.mortality_recording', 'Mortalidad')}</span>
              </Link>
              <Link
                to="/operations/new?type=egg_collection"
                className="flex flex-col items-center justify-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 border-2 border-orange-300 rounded-xl hover:shadow-md transition-all active:scale-95"
              >
                <Egg size={24} className="text-orange-600 mb-2" />
                <span className="text-xs font-bold text-orange-900 text-center">{t('events.egg_collection', 'Huevos')}</span>
              </Link>
            </div>
          </div>

          {/* Go to all processes */}
          <Link
            to="/operations"
            className="block w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-xl text-center hover:shadow-lg transition-all active:scale-95"
          >
            {t('nav.operations', 'Ver Todas las Operaciones')} →
          </Link>
        </div>
      </div>
    )
  }

  // ── ADMIN / WEB DASHBOARD ──────────────────────────────────

  const lotsByType: Record<string, number> = data?.lots_by_type ?? {}
  const totalActiveLots = Object.values(lotsByType).reduce((a, b) => a + (b as number), 0)
  const mortalityTrend: { week: string; mortality: number }[] = data?.mortality_trend ?? []

  const summaryCards = [
    {
      label: t('dashboard.totalEvents'),
      value: data?.total_events ?? 0,
      icon: <FileText size={18} />,
      color: 'text-blue-600 bg-blue-50',
    },
    {
      label: t('dashboard.pendingReview'),
      value: data?.pending_review ?? 0,
      icon: <Clock size={18} />,
      color: 'text-amber-600 bg-amber-50',
    },
    {
      label: t('dashboard.pendingApproval'),
      value: data?.pending_approval ?? 0,
      icon: <CheckCircle size={18} />,
      color: 'text-teal-600 bg-teal-50',
    },
    {
      label: t('dashboard.last7Days'),
      value: data?.last_7_days ?? 0,
      icon: <TrendingDown size={18} />,
      color: 'text-emerald-600 bg-emerald-50',
    },
  ]

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('nav.dashboard')}</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          {t('dashboard.welcome')}{user?.first_name ? `, ${user.first_name}` : ''}
        </p>
      </div>

      {/* Summary KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {summaryCards.map((card, i) => (
          <Card key={i}>
            <CardBody>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${card.color}`}>
                {card.icon}
              </div>
              <p className="text-2xl font-bold text-slate-800">{card.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{card.label}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Active lots by stage */}
      <Card>
        <CardHeader
          title={t('dashboard.activeLotsByStage', 'Lotes activos por etapa')}
          subtitle={`${totalActiveLots} ${t('dashboard.totalActive', 'lotes activos')}`}
          action={
            <Bird size={18} className="text-slate-400" />
          }
        />
        <CardBody>
          {totalActiveLots === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">{t('lots.noLots', 'Sin lotes activos')}</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {['grandparent', 'breeder', 'hatchery', 'broiler'].map(bt => (
                <div
                  key={bt}
                  className={`rounded-xl border p-4 ${BIRD_TYPE_COLORS[bt] ?? 'bg-slate-100 text-slate-600 border-slate-200'}`}
                >
                  <p className="text-2xl font-bold">{lotsByType[bt] ?? 0}</p>
                  <p className="text-xs font-medium mt-0.5">{t(`birdTypes.${bt}`, bt)}</p>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Mortality trend chart */}
      {mortalityTrend.length > 0 && (
        <Card>
          <CardHeader title={t('dashboard.mortalityTrend', 'Tendencia de mortalidad')} subtitle={t('dashboard.last8Weeks', 'Últimas 8 semanas')} />
          <CardBody>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mortalityTrend} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="week" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Line
                  type="monotone"
                  dataKey="mortality"
                  stroke="#DC2626"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#DC2626' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      )}

      {/* Status distribution + top event types */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Status distribution */}
        {data?.by_status && Object.keys(data.by_status).length > 0 && (
          <Card>
            <CardHeader title={t('dashboard.statusDistribution')} />
            <CardBody>
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center gap-1.5">
                    <Badge variant={statusToVariant(status)} dot>
                      {t(`status.${status}`, status)}: {count as number}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {/* Top event types */}
        {data?.top_event_types && Object.keys(data.top_event_types).length > 0 && (
          <Card>
            <CardHeader title={t('dashboard.topEventTypes')} />
            <CardBody>
              <div className="space-y-2">
                {Object.entries(data.top_event_types).map(([etype, count]) => {
                  const max = Math.max(...Object.values(data.top_event_types) as number[])
                  const pct = Math.round(((count as number) / max) * 100)
                  return (
                    <div key={etype}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600">{t(`events.${etype}`, etype)}</span>
                        <span className="font-semibold text-slate-800">{count as number}</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#2563EB] rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  )
}
