import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { Bird, FileText, Clock, CheckCircle, TrendingDown, Wheat, Skull, Scale, Egg, Sparkles, AlertCircle, AlertTriangle, X } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Card, CardHeader, CardBody, Badge, statusToVariant } from '../../components/ui'
import { PROCESS_STAGES, flowForStage } from '../../data/processCatalog'

// ── Alert severity styles ───────────────────────────────────────────────────
const ALERT_STYLE: Record<string, { bar: string; bg: string; text: string; badge: string }> = {
  critical: { bar: 'bg-red-500',    bg: 'bg-red-50',    text: 'text-red-800',    badge: 'bg-red-100 text-red-700 border-red-200' },
  warning:  { bar: 'bg-amber-400',  bg: 'bg-amber-50',  text: 'text-amber-800',  badge: 'bg-amber-100 text-amber-700 border-amber-200' },
  info:     { bar: 'bg-blue-400',   bg: 'bg-blue-50',   text: 'text-blue-800',   badge: 'bg-blue-100 text-blue-700 border-blue-200' },
}

function AlertsWidget({ alerts, onResolve }: {
  alerts: any[]
  onResolve: (id: number) => void
}) {
  const { t } = useTranslation()
  if (!alerts || alerts.length === 0) return null
  return (
    <Card>
      <CardHeader
        title={t('alerts.activeTitle', 'Alertas activas')}
        subtitle={`${alerts.length} ${t('alerts.unresolved', 'sin resolver')}`}
        action={<AlertTriangle size={18} className="text-amber-500" />}
      />
      <CardBody>
        <div className="space-y-2">
          {alerts.map((a: any) => {
            const s = ALERT_STYLE[a.severity] ?? ALERT_STYLE.info
            return (
              <div key={a.id} className={`flex items-start gap-3 rounded-xl border p-3 ${s.bg}`}>
                <div className={`w-1 self-stretch rounded-full shrink-0 ${s.bar}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-0.5">
                    <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${s.badge}`}>
                      {String(t(`alerts.severity.${a.severity}`, a.severity))}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {String(t(`alerts.type.${a.alert_type}`, a.alert_type.replace(/_/g, ' ')))}
                    </span>
                    {a.lot_id && (
                      <Link to={`/lots/${a.lot_id}`} className="text-[10px] text-blue-600 hover:underline">
                        {t('lots.lot', 'Lote')} #{a.lot_id}
                      </Link>
                    )}
                  </div>
                  <p className={`text-xs leading-snug ${s.text}`}>{a.message}</p>
                </div>
                <button
                  onClick={() => onResolve(a.id)}
                  className="shrink-0 text-slate-400 hover:text-slate-600 p-1 rounded"
                  title={t('alerts.resolve', 'Marcar como resuelta')}
                >
                  <X size={14} />
                </button>
              </div>
            )
          })}
        </div>
      </CardBody>
    </Card>
  )
}

export default function DashboardPage() {
  const { t, i18n } = useTranslation()
  const { user } = useAuthStore()
  const isMobileUser = user?.view_type === 'mobile'
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeAlerts, setActiveAlerts] = useState<any[]>([])
  const toast = useToast()

  useEffect(() => {
    const endpoint = isMobileUser ? '/dashboard/mobile' : '/dashboard/admin'
    api.get(endpoint)
      .then(r => {
        setData(r.data)
        setActiveAlerts(r.data?.active_alerts ?? [])
      })
      .catch((e: any) => {
        const msg = getErrorMessage(e, t('dashboard.errorLoading'))
        setError(msg)
        toast.error(msg)
      })
      .finally(() => setLoading(false))
  }, [isMobileUser])

  const handleResolveAlert = async (alertId: number) => {
    try {
      await api.patch(`/operations/alerts/${alertId}/resolve`)
      setActiveAlerts(prev => prev.filter(a => a.id !== alertId))
      toast.success(t('alerts.resolvedOk', 'Alerta resuelta'))
    } catch (e: any) {
      toast.error(getErrorMessage(e, t('alerts.resolveError', 'Error al resolver la alerta')))
    }
  }

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
      <div className="min-h-screen bg-[#F4F6F9] dark:bg-dark-bg pb-24">
        {/* Welcome header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4"
        style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 60%, #1A6DCC 100%)' }}
      >
        <div className="flex items-center gap-2 mb-1">
          <Sparkles size={18} />
          <h1 className="text-xl font-bold">{t('nav.home', 'Inicio')}</h1>
        </div>
        <p className="text-blue-100 text-sm opacity-90">
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
              <div className="bg-white rounded-2xl border border-slate-100 p-3 text-center shadow-card accent-bar accent-bar-blue">
                <div className="text-2xl font-bold text-brand-700 pt-2">{data?.today_events ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold uppercase tracking-wide">
                  {t('dashboard.todayEvents', 'Operaciones')}
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-slate-100 p-3 text-center shadow-card accent-bar accent-bar-amber">
                <div className="text-2xl font-bold text-amber-600 pt-2">{data?.pending_corrections ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold uppercase tracking-wide">
                  {t('dashboard.pendingCorrections', 'Por revisar')}
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-slate-100 p-3 text-center shadow-card accent-bar accent-bar-green">
                <div className="text-2xl font-bold text-emerald-600 pt-2">{data?.approved_today ?? 0}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-semibold uppercase tracking-wide">
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
                    className="group relative overflow-hidden rounded-2xl p-4 text-white active:scale-[0.97] transition-all"
                    style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 100%)', boxShadow: '0 4px 12px -2px rgba(11,35,64,0.35)' }}
                  >
                    <span className="absolute -top-1 -right-1 text-white/10 text-6xl font-black select-none leading-none">{idx + 1}</span>
                    <span className="inline-flex w-10 h-10 rounded-xl bg-white/15 backdrop-blur items-center justify-center ring-1 ring-white/20">
                      <stage.Icon size={22} strokeWidth={2} />
                    </span>
                    <h3 className="mt-2.5 text-[13px] font-bold leading-tight">{t(stage.labelKey, stage.fallback)}</h3>
                    <p className="text-[10px] font-medium text-white/70 mt-0.5">{count} {t('process.hub.steps', 'pasos')}</p>
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
                className="flex flex-col items-center justify-center p-4 bg-white border border-amber-200 rounded-2xl shadow-card hover:shadow-card-md transition-all active:scale-95"
              >
                <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center mb-2">
                  <Wheat size={20} className="text-amber-600" />
                </div>
                <span className="text-xs font-semibold text-slate-700 text-center">{t('events.feed_registration', 'Alimento')}</span>
              </Link>
              <Link
                to="/operations/new?type=weight_recording"
                className="flex flex-col items-center justify-center p-4 bg-white border border-blue-200 rounded-2xl shadow-card hover:shadow-card-md transition-all active:scale-95"
              >
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center mb-2">
                  <Scale size={20} className="text-blue-600" />
                </div>
                <span className="text-xs font-semibold text-slate-700 text-center">{t('events.weight_recording', 'Pesaje')}</span>
              </Link>
              <Link
                to="/operations/new?type=mortality_recording"
                className="flex flex-col items-center justify-center p-4 bg-white border border-red-200 rounded-2xl shadow-card hover:shadow-card-md transition-all active:scale-95"
              >
                <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center mb-2">
                  <Skull size={20} className="text-red-600" />
                </div>
                <span className="text-xs font-semibold text-slate-700 text-center">{t('events.mortality_recording', 'Mortalidad')}</span>
              </Link>
              <Link
                to="/operations/new?type=egg_collection"
                className="flex flex-col items-center justify-center p-4 bg-white border border-orange-200 rounded-2xl shadow-card hover:shadow-card-md transition-all active:scale-95"
              >
                <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center mb-2">
                  <Egg size={20} className="text-orange-600" />
                </div>
                <span className="text-xs font-semibold text-slate-700 text-center">{t('events.egg_collection', 'Huevos')}</span>
              </Link>
            </div>
          </div>

          {/* Go to all processes */}
          <Link
            to="/operations"
            className="block w-full py-3 px-4 text-white font-bold rounded-2xl text-center transition-all active:scale-95 text-sm"
            style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 100%)', boxShadow: '0 4px 12px -2px rgba(11,35,64,0.35)' }}
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
    { label: t('dashboard.totalEvents'),    value: data?.total_events    ?? 0, icon: <FileText size={16} /> },
    { label: t('dashboard.pendingReview'),  value: data?.pending_review  ?? 0, icon: <Clock size={16} /> },
    { label: t('dashboard.pendingApproval'),value: data?.pending_approval ?? 0, icon: <CheckCircle size={16} /> },
    { label: t('dashboard.last7Days'),      value: data?.last_7_days     ?? 0, icon: <TrendingDown size={16} /> },
  ]

  const CARD_ACCENT_COLORS = [
    { dot: 'bg-blue-500',    icon: 'text-blue-600 bg-blue-50' },
    { dot: 'bg-amber-500',   icon: 'text-amber-600 bg-amber-50' },
    { dot: 'bg-teal-500',    icon: 'text-teal-600 bg-teal-50' },
    { dot: 'bg-emerald-500', icon: 'text-emerald-600 bg-emerald-50' },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-slate-900 dark:text-white">{t('nav.dashboard')}</h1>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-0.5">
          {t('dashboard.welcome')}{user?.first_name ? `, ${user.first_name}` : ''} · {new Date().toLocaleDateString(i18n.language === 'es' ? 'es-VE' : 'en-US', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {/* Summary KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {summaryCards.map((card, i) => {
          const ac = CARD_ACCENT_COLORS[i]
          return (
            <div key={i} className="bg-white dark:bg-dark-card rounded-xl border border-slate-200/80 dark:border-dark-border p-4">
              <div className="flex items-center gap-1.5 mb-2">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ac.dot}`} />
                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 leading-none truncate">{card.label}</p>
              </div>
              <div className="flex items-end justify-between gap-2">
                <p className="text-2xl font-semibold text-slate-900 dark:text-white stat-value">{card.value}</p>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${ac.icon}`}>
                  {card.icon}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Active lots by stage */}
      <Card>
        <CardHeader
          title={t('dashboard.activeLotsByStage', 'Lotes activos por etapa')}
          subtitle={`${totalActiveLots} ${t('dashboard.totalActive', 'lotes activos')}`}
          action={<Bird size={16} />}
        />
        <CardBody>
          {totalActiveLots === 0 ? (
            <p className="text-sm text-slate-400 text-center py-3">{t('lots.noLots', 'Sin lotes activos')}</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { key: 'grandparent', dot: 'bg-purple-400', text: 'text-purple-700', bg: 'bg-purple-50' },
                { key: 'breeder',     dot: 'bg-blue-400',   text: 'text-blue-700',   bg: 'bg-blue-50' },
                { key: 'hatchery',    dot: 'bg-amber-400',  text: 'text-amber-700',  bg: 'bg-amber-50' },
                { key: 'broiler',     dot: 'bg-emerald-400',text: 'text-emerald-700',bg: 'bg-emerald-50' },
              ].map(({ key, dot, text, bg }) => (
                <div key={key} className={`${bg} rounded-lg p-3 flex items-center gap-3`}>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
                  <div className="min-w-0">
                    <p className={`text-xl font-semibold stat-value ${text}`}>{lotsByType[key] ?? 0}</p>
                    <p className="text-[10px] font-medium text-slate-500 truncate">{t(`birdTypes.${key}`, key)}</p>
                  </div>
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

      {/* Active operational alerts */}
      <AlertsWidget alerts={activeAlerts} onResolve={handleResolveAlert} />
    </div>
  )
}
