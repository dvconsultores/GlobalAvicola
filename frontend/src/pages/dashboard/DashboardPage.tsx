import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { Bird, FileText, Clock, CheckCircle, TrendingDown, Egg, Sparkles, AlertCircle, AlertTriangle, X, Sprout, Feather, ChevronRight, ChevronDown, Building2 } from 'lucide-react'
import {
 LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Card, CardHeader, CardBody, Badge, statusToVariant } from '../../components/ui'
import { PROCESS_STAGES, flowForStage, stagePathForKey } from '../../data/processCatalog'

// ── Alert severity styles ───────────────────────────────────────────────────
const ALERT_STYLE: Record<string, { bar: string; bg: string; text: string; badge: string }> = {
 critical: { bar: 'bg-red-500', bg: 'bg-red-50', text: 'text-red-800', badge: 'bg-red-100 text-red-700 border-red-200' },
 warning: { bar: 'bg-amber-400', bg: 'bg-amber-50', text: 'text-amber-800', badge: 'bg-amber-100 text-amber-700 border-amber-200' },
 info: { bar: 'bg-blue-400', bg: 'bg-blue-50', text: 'text-blue-800', badge: 'bg-blue-100 text-blue-700 border-blue-200' },
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
 <span className={`text-xs font-bold uppercase px-1.5 py-0.5 rounded border ${s.badge}`}>
 {String(t(`alerts.severity.${a.severity}`, a.severity))}
 </span>
 <span className="text-xs text-slate-500">
 {String(t(`alerts.type.${a.alert_type}`, a.alert_type.replace(/_/g, ' ')))}
 </span>
 {a.lot_id && (
 <Link to={`/lots/${a.lot_id}`} className="text-xs text-blue-600 hover:underline">
 {t('lots.lot', 'Lote')} #{a.lot_id}
 </Link>
 )}
 </div>
 <p className={`text-xs leading-snug ${s.text}`}>{a.message}</p>
 </div>
 <button
 onClick={() => onResolve(a.id)}
 className="shrink-0 text-slate-400 hover p-1 rounded"
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
 const location = useLocation()
 const { user } = useAuthStore()
 const { activeCompanyName } = useCompanyStore()
 const isMobileUser = user?.view_type === 'mobile'
 const isKpiRoute = location.pathname === '/kpi'
 const [data, setData] = useState<any>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState('')
 const [activeAlerts, setActiveAlerts] = useState<any[]>([])
 const [expandedBird, setExpandedBird] = useState<string | null>(null) // For mobile bird-type → phase expansion
 const toast = useToast()

 useEffect(() => {
 const endpoint = isMobileUser && !isKpiRoute ? '/dashboard/mobile' : '/dashboard/admin'
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
 }, [isMobileUser, isKpiRoute])

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

 const lotsByType: Record<string, number> = data?.lots_by_type ?? {}
 const totalActiveLots = Object.values(lotsByType).reduce((a, b) => a + (b as number), 0)
 const mortalityTrend: { week: string; mortality: number }[] = data?.mortality_trend ?? []

 // ── MOBILE OPERATOR DASHBOARD — BIRD TYPE → PHASE → OPERATIONS ─────────────
 if (isMobileUser) {
 // Group stages by bird type for hierarchical navigation
 const birdTypeGroups = [
 { 
 id: 'grandparent', labelKey: 'process.grandparent.title', fallback: 'Progenitoras',
 icon: Sprout, color: 'from-indigo-500 to-indigo-700',
 stages: PROCESS_STAGES.filter(s => s.key.startsWith('grandparent')),
 },
 { 
 id: 'breeder', labelKey: 'process.breeder.title', fallback: 'Reproductoras',
 icon: Feather, color: 'from-blue-500 to-blue-700',
 stages: PROCESS_STAGES.filter(s => s.key.startsWith('breeder')),
 },
 { 
 id: 'hatchery', labelKey: 'process.hatchery.title', fallback: 'Incubadora',
 icon: Egg, color: 'from-teal-500 to-teal-700',
 stages: PROCESS_STAGES.filter(s => s.key === 'hatchery'),
 },
 { 
 id: 'broiler', labelKey: 'process.broiler.title', fallback: 'Pollo de Engorde',
 icon: Bird, color: 'from-orange-500 to-orange-700',
 stages: PROCESS_STAGES.filter(s => s.key === 'broiler'),
 },
 ]

 return (
 <div className="min-h-screen bg-slate-100 pb-24">
 {/* Welcome header — slim, corporate */}
 <div className="bg-gradient-to-r from-[#264c5f] to-[#3d748f] text-white px-4 py-4">
 <div className="flex items-center gap-2">
 <Sparkles size={16} className="text-blue-300" />
 <div className="min-w-0 flex-1">
 <h1 className="text-base font-bold leading-tight">{isKpiRoute ? t('nav.kpi', 'KPI') : t('nav.home', 'Inicio')}</h1>
 <div className="flex items-center gap-2">
 <p className="text-sm text-blue-200/80">
 {isKpiRoute
 ? t('dashboard.todayMetrics', 'Hoy')
 : `${t('dashboard.welcome')}, ${user?.first_name || 'Operador'}`}
 </p>
 {(activeCompanyName || user?.company_name) && (
 <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1" style={{ background: 'rgba(255,255,255,0.15)', color: 'rgba(180,210,230,0.95)' }}>
 <Building2 size={10} />
 {activeCompanyName || user?.company_name}
 </span>
 )}
 </div>
 </div>
 </div>
 </div>

 <div className="pt-6 pb-4 space-y-5">
 {isKpiRoute ? (
 <>
 {/* KPI summary for poultry processes */}
 <div className="space-y-2">
 <h2 className="text-sm font-bold uppercase text-slate-400 tracking-wider">
 {t('dashboard.processKpi', 'KPIs de Procesos Avicolas')}
 </h2>
 <div className="grid grid-cols-2 gap-2.5">
 <div className="bg-white rounded-lg border border-slate-200/60 p-3">
 <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">{t('dashboard.totalEvents', 'Total eventos')}</p>
 <p className="text-xl font-bold text-slate-800 mt-1">{data?.total_events ?? 0}</p>
 </div>
 <div className="bg-white rounded-lg border border-slate-200/60 p-3">
 <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">{t('dashboard.last7Days', 'Ultimos 7 dias')}</p>
 <p className="text-xl font-bold text-blue-700 mt-1">{data?.last_7_days ?? 0}</p>
 </div>
 <div className="bg-white rounded-lg border border-slate-200/60 p-3">
 <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">{t('dashboard.pendingReview', 'Pendientes de revision')}</p>
 <p className="text-xl font-bold text-amber-600 mt-1">{data?.pending_review ?? 0}</p>
 </div>
 <div className="bg-white rounded-lg border border-slate-200/60 p-3">
 <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">{t('dashboard.pendingApproval', 'Pendientes de aprobacion')}</p>
 <p className="text-xl font-bold text-emerald-600 mt-1">{data?.pending_approval ?? 0}</p>
 </div>
 </div>
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
 <div className="grid grid-cols-2 gap-2">
 {[
 { key: 'grandparent', dot: 'bg-purple-400', text: 'text-purple-700', bg: 'bg-purple-50' },
 { key: 'breeder', dot: 'bg-blue-400', text: 'text-blue-700', bg: 'bg-blue-50' },
 { key: 'hatchery', dot: 'bg-amber-400', text: 'text-amber-700', bg: 'bg-amber-50' },
 { key: 'broiler', dot: 'bg-emerald-400', text: 'text-emerald-700', bg: 'bg-emerald-50' },
 ].map(({ key, dot, text, bg }) => (
 <div key={key} className={`${bg} rounded-lg p-3 flex items-center gap-2.5`}>
 <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
 <div className="min-w-0">
 <p className={`text-lg font-semibold stat-value ${text}`}>{lotsByType[key] ?? 0}</p>
 <p className="text-xs font-medium text-slate-500 truncate">{t(`birdTypes.${key}`, key)}</p>
 </div>
 </div>
 ))}
 </div>
 )}
 </CardBody>
 </Card>

 {/* Mortality trend */}
 {mortalityTrend.length > 0 && (
 <Card>
 <CardHeader
 title={t('dashboard.mortalityTrend', 'Tendencia de mortalidad')}
 subtitle={t('dashboard.last8Weeks', 'Ultimas 8 semanas')}
 />
 <CardBody>
 <ResponsiveContainer width="100%" height={190}>
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

 {/* Events generated by process */}
 {data?.top_event_types && Object.keys(data.top_event_types).length > 0 && (
 <Card>
 <CardHeader title={t('dashboard.topEventTypes', 'Eventos generados por tipo')} />
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
 <div className="h-full bg-[#5a9bba] rounded-full transition-all" style={{ width: `${pct}%` }} />
 </div>
 </div>
 )
 })}
 </div>
 </CardBody>
 </Card>
 )}
 </>
 ) : (
 <>
 {/* KPI Section */}
 <div className="space-y-2">
 <h2 className="text-sm font-bold uppercase text-slate-400 tracking-wider">
 {t('dashboard.todayMetrics', 'Hoy')}
 </h2>
 <div className="grid grid-cols-3 gap-2.5">
 <div className="bg-white rounded-xl border border-slate-200/80 p-3 text-center">
 <div className="text-xl font-bold text-slate-800">{data?.today_events ?? 0}</div>
 <div className="text-xs text-slate-400 mt-0.5 font-semibold uppercase tracking-wide">
 {t('dashboard.todayEvents', 'Registros')}
 </div>
 </div>
 <div className="bg-white rounded-xl border border-slate-200/80 p-3 text-center">
 <div className="text-xl font-bold text-amber-600">{data?.pending_corrections ?? 0}</div>
 <div className="text-xs text-slate-400 mt-0.5 font-semibold uppercase tracking-wide">
 {t('dashboard.pendingCorrections', 'Pendientes')}
 </div>
 </div>
 <div className="bg-white rounded-xl border border-slate-200/80 p-3 text-center">
 <div className="text-xl font-bold text-emerald-600">{data?.approved_today ?? 0}</div>
 <div className="text-xs text-slate-400 mt-0.5 font-semibold uppercase tracking-wide">
 {t('dashboard.approvedToday', 'Aprobados')}
 </div>
 </div>
 </div>
 </div>

 {/* Alerts */}
 {data?.pending_corrections && data.pending_corrections > 0 && (
 <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2">
 <AlertCircle size={16} className="text-amber-600 shrink-0 mt-0.5" />
 <div>
 <p className="text-xs font-semibold text-amber-900">{t('dashboard.hasPendingCorrections', 'Tienes correcciones pendientes')}</p>
 <p className="text-sm text-amber-700 mt-0.5">{t('dashboard.checkAndReview', 'Revisa tus operaciones rechazadas')}</p>
 </div>
 </div>
 )}

 <div className="space-y-2">
 <h2 className="text-sm font-bold uppercase text-slate-400 tracking-wider">
 {t('process.hub.title', 'Procesos')}
 </h2>
 <div className="space-y-2.5">
 {birdTypeGroups.map((group) => {
 const hasSubPhases = group.stages.length > 1
 return (
 <div key={group.id} className="space-y-2">
 {/* Bird type card */}
 {hasSubPhases ? (
 <button
 onClick={() => setExpandedBird(expandedBird === group.id ? null : group.id)}
 className="w-full bg-white rounded-xl border border-slate-200/80 p-3.5 flex items-center gap-3 active:bg-slate-50 transition-colors text-left"
 >
 <span className={`w-9 h-9 rounded-lg bg-gradient-to-br ${group.color} flex items-center justify-center shrink-0`}>
 <group.icon size={18} className="text-white" />
 </span>
 <div className="flex-1 min-w-0">
 <h3 className="text-sm font-bold text-slate-800">{t(group.labelKey, group.fallback)}</h3>
 <p className="text-sm text-slate-400 mt-0.5">
 {group.stages.length} {t('process.hub.phases', 'fases')} · {group.stages.reduce((acc, s) => acc + flowForStage(s.key).length, 0)} {t('process.hub.operations', 'operaciones')}
 </p>
 </div>
 {expandedBird === group.id ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
 </button>
 ) : (
 <Link
 to={stagePathForKey(group.stages[0].key)}
 className="w-full bg-white rounded-xl border border-slate-200/80 p-3.5 flex items-center gap-3 active:bg-slate-50 transition-colors"
 >
 <span className={`w-9 h-9 rounded-lg bg-gradient-to-br ${group.color} flex items-center justify-center shrink-0`}>
 <group.icon size={18} className="text-white" />
 </span>
 <div className="flex-1 min-w-0">
 <h3 className="text-sm font-bold text-slate-800">{t(group.labelKey, group.fallback)}</h3>
 <p className="text-sm text-slate-400 mt-0.5">
 {flowForStage(group.stages[0].key).length} {t('process.hub.operations', 'operaciones')}
 </p>
 </div>
 <ChevronRight size={16} className="text-slate-400" />
 </Link>
 )}

 {/* Sub-phase cards (Cría / Producción) */}
 {hasSubPhases && expandedBird === group.id && (
 <div className="pl-2 space-y-2 border-l-2 border-slate-200 ml-5">
 {group.stages.map((stage) => {
 const count = flowForStage(stage.key).length
 const isRearing = stage.key.includes('rearing')
 return (
 <Link
 key={stage.key}
 to={stagePathForKey(stage.key)}
 className="flex items-center gap-2.5 p-3 bg-white border border-slate-200/80 rounded-lg active:bg-slate-50 transition-colors"
 >
 <span className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 ${isRearing ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
 {isRearing ? <Sprout size={14} /> : <Egg size={14} />}
 </span>
 <div className="flex-1 min-w-0">
 <span className="text-sm font-semibold text-slate-700">{t(stage.labelKey, stage.fallback)}</span>
 <span className="text-xs text-slate-400 ml-2">{count} {t('process.hub.steps', 'pasos')}</span>
 </div>
 <ChevronRight size={14} className="text-slate-300" />
 </Link>
 )
 })}
 </div>
 )}
 </div>
 )
 })}
 </div>
 </div>
 </>
 )}
 </div>
 </div>
 )
 }

 // ── ADMIN / WEB DASHBOARD ──────────────────────────────────

 const summaryCards = [
 { label: t('dashboard.totalEvents'), value: data?.total_events ?? 0, icon: <FileText size={16} /> },
 { label: t('dashboard.pendingReview'), value: data?.pending_review ?? 0, icon: <Clock size={16} /> },
 { label: t('dashboard.pendingApproval'),value: data?.pending_approval ?? 0, icon: <CheckCircle size={16} /> },
 { label: t('dashboard.last7Days'), value: data?.last_7_days ?? 0, icon: <TrendingDown size={16} /> },
 ]

 const CARD_ACCENT_COLORS = [
 { dot: 'bg-blue-500', icon: 'text-blue-600 bg-blue-50' },
 { dot: 'bg-amber-500', icon: 'text-amber-600 bg-amber-50' },
 { dot: 'bg-teal-500', icon: 'text-teal-600 bg-teal-50' },
 { dot: 'bg-emerald-500', icon: 'text-emerald-600 bg-emerald-50' },
 ]

 return (
 <div className="max-w-5xl mx-auto space-y-5">
 {/* Page header */}
 <div>
 <h1 className="text-xl font-semibold text-slate-900">{t('nav.dashboard')}</h1>
 <p className="text-sm text-slate-400 mt-0.5">
 {t('dashboard.welcome')}{user?.first_name ? `, ${user.first_name}` : ''} · {new Date().toLocaleDateString(i18n.language === 'es' ? 'es-VE' : 'en-US', { weekday: 'long', day: 'numeric', month: 'long' })}
 </p>
 </div>

 {/* Summary KPI cards */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
 {summaryCards.map((card, i) => {
 const ac = CARD_ACCENT_COLORS[i]
 return (
 <div key={i} className="bg-white rounded-xl border border-slate-200/80 p-4">
 <div className="flex items-center gap-1.5 mb-2">
 <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ac.dot}`} />
 <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 leading-none truncate">{card.label}</p>
 </div>
 <div className="flex items-end justify-between gap-2">
 <p className="text-2xl font-semibold text-slate-900 stat-value">{card.value}</p>
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
 { key: 'breeder', dot: 'bg-blue-400', text: 'text-blue-700', bg: 'bg-blue-50' },
 { key: 'hatchery', dot: 'bg-amber-400', text: 'text-amber-700', bg: 'bg-amber-50' },
 { key: 'broiler', dot: 'bg-emerald-400',text: 'text-emerald-700',bg: 'bg-emerald-50' },
 ].map(({ key, dot, text, bg }) => (
 <div key={key} className={`${bg} rounded-lg p-3 flex items-center gap-3`}>
 <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
 <div className="min-w-0">
 <p className={`text-xl font-semibold stat-value ${text}`}>{lotsByType[key] ?? 0}</p>
 <p className="text-xs font-medium text-slate-500 truncate">{t(`birdTypes.${key}`, key)}</p>
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
 className="h-full bg-[#5a9bba] rounded-full transition-all"
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
