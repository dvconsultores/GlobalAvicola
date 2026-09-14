import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, TrendingUp, Activity, Calendar, Lock, AlertTriangle, X } from 'lucide-react'
import { EVENT_ICONS } from '../../components/Icon'
import { Button, Modal, Input } from '../../components/ui'
import { TraceabilityTree } from '../../components/TraceabilityTree'
import { STAGE_OPERATIONS, resolveStageKey } from '../../data/processCatalog'
import api from '../../services/api'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'

// ─── Status badge colours ────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
 active: 'bg-emerald-100 text-emerald-800',
 closed: 'bg-slate-100 text-slate-600',
 cancelled: 'bg-red-100 text-red-800',
}


export default function LotDetailPage() {
 const can = useCan()
 const { t } = useTranslation()
 const { id } = useParams<{ id: string }>()
 const [lot, setLot] = useState<any>(null)
 const [kpis, setKpis] = useState<any>(null)
 const [kpiIpe, setKpiIpe] = useState<any>(null)
 const [kpiUniformity, setKpiUniformity] = useState<any>(null)
 const [lotAlerts, setLotAlerts] = useState<any[]>([])
 const [events, setEvents] = useState<any[]>([])
 // `R-218`: serie semanal del backend (la lista de operaciones no trae sublistas).
 const [semanal, setSemanal] = useState<any[]>([])
 const [phases, setPhases] = useState<any[]>([])
 // `R-191`: fases maestras (`masters/productive-phases`) para resolver el id por código.
 const [masterPhases, setMasterPhases] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [closeResult, setCloseResult] = useState<any>(null)
 const [closing, setClosing] = useState(false)
 const [transitioning, setTransitioning] = useState(false)
 // Modal states
 const [showTransitionModal, setShowTransitionModal] = useState(false)
 const [showCloseModal, setShowCloseModal] = useState(false)
 const [transitionDate, setTransitionDate] = useState(() => new Date().toISOString().split('T')[0])
 const [transitionMale, setTransitionMale] = useState('')
 const [transitionFemale, setTransitionFemale] = useState('')
 const toast = useToast()

 useEffect(() => {
 const fetchAll = async () => {
 try {
 // GA-REM-011 C-03: se consulta el lote por identificador en lugar de
 // listar 200 (el backend acepta le=100 y devolvía 422, abortando la pantalla).
 const { data: found } = await api.get(`/lots/${id}`)
 setLot(found || null)

 // `R-212` · AC-01: no se piden KPIs de reportes sin `reports:read` (el
 // servidor deniega; la UI deja de emitir la petición).
 const puedeReportes = can({ permission: 'reports:read' })
 const omitido = Promise.resolve({ data: null } as any)
 const [kpiRes, evtRes, phaseRes, ipeRes, uniformRes, alertsRes, mastersRes, semanalRes] = await Promise.allSettled([
 puedeReportes ? api.get(`/reports/kpis?lot_id=${id}`) : omitido,
 api.get(`/operations?lot_id=${id}&limit=50`),
 api.get(`/lots/${id}/phases`),
 puedeReportes ? api.get(`/reports/kpi/ipe/${id}`) : omitido,
 puedeReportes ? api.get(`/reports/kpi/weight-uniformity/${id}`) : omitido,
 api.get(`/operations/alerts?lot_id=${id}&is_resolved=false&limit=20`),
 api.get('/masters/productive-phases'),
 puedeReportes ? api.get(`/reports/lot/${id}/weekly`) : omitido,
 ])
 if (kpiRes.status === 'fulfilled') setKpis(kpiRes.value.data)
 if (evtRes.status === 'fulfilled') setEvents(evtRes.value.data || [])
 if (phaseRes.status === 'fulfilled') setPhases(phaseRes.value.data || [])
 if (ipeRes.status === 'fulfilled') setKpiIpe(ipeRes.value.data)
 if (uniformRes.status === 'fulfilled') setKpiUniformity(uniformRes.value.data)
 if (alertsRes.status === 'fulfilled') setLotAlerts(alertsRes.value.data || [])
 if (mastersRes.status === 'fulfilled') setMasterPhases(mastersRes.value.data || [])
 if (semanalRes.status === 'fulfilled') setSemanal(semanalRes.value.data?.weeks || [])
 } catch (err) {
 console.error(err)
 } finally {
 setLoading(false)
 }
 }
 fetchAll()
 }, [id])

 const handleResolveAlert = async (alertId: number) => {
 try {
 await api.patch(`/operations/alerts/${alertId}/resolve`)
 setLotAlerts(prev => prev.filter(a => a.id !== alertId))
 toast.success(t('alerts.resolvedOk', 'Alerta resuelta'))
 } catch (e: any) {
 toast.error(getErrorMessage(e, t('alerts.resolveError', 'Error al resolver')))
 }
 }

 if (loading) return <div className="py-4 sm:py-6 text-slate-500">{t('common.loading')}</div>
 if (!lot) return <div className="py-4 sm:py-6 text-slate-500">{t('lots.lotNotFound')}</div>

 const birdType: string = lot.bird_type || 'broiler'
 const activePhase = phases.find((p: any) => p.is_active)
 const activePhaseName: string | null = activePhase?.phase?.name ?? activePhase?.phase?.code ?? null
 const stageKey = resolveStageKey(birdType, activePhaseName)
 const stageOps = STAGE_OPERATIONS[stageKey] ?? STAGE_OPERATIONS.broiler
 const stageLabel = t(`birdTypes.${birdType}`, birdType)

 // Phase label for breeder/grandparent badge
 const phaseLabel = (stageKey === 'breeder_production' || stageKey === 'grandparent_production')
 ? t('phases.production', 'Producción')
 : (stageKey === 'breeder_rearing' || stageKey === 'grandparent_rearing')
 ? t('phases.rearing', 'Cría')
 : null

 // Can transition from rearing to production
 const canTransition = (birdType === 'breeder' || birdType === 'grandparent')
 && (stageKey === 'breeder_rearing' || stageKey === 'grandparent_rearing')
 && lot.status === 'active'

 const handleCloseLot = async () => {
 setShowCloseModal(false)
 setClosing(true)
 try {
 const { data } = await api.post(`/lots/${id}/close`)
 setCloseResult(data)
 setLot((prev: any) => ({ ...prev, status: 'closed' }))
 } catch (err: any) {
      // `R-192`: la verdad del rechazo es del backend (`R7`/`BR-05`/403/404) — se muestra
      // legible con el patrón vigente de la página; un cierre fallido nunca queda solo en
      // consola con el modal cerrado y el operador sin saber por qué.
      toast.error(getErrorMessage(err, t('lots.closeError', 'Error al cerrar lote')))
    } finally {
      setClosing(false)
    }
  }

 const handleTransitionPhase = async () => {
 setShowTransitionModal(false)
 setTransitioning(true)
 try {
 // `R-191`: el contrato exige ids — la fase destino se resuelve por **código**
 // contra las fases maestras (mismo nombre de campo que el backend: `lot_id`/`phase_id`).
 const destino = masterPhases.find((f: any) => String(f.code || '').toUpperCase() === 'PROD')
 || masterPhases.find((f: any) => /producc|production/i.test(`${f.name || ''} ${f.code || ''}`))
 if (!destino) {
 toast.error(t('lots.phaseNotFound', 'No se encontró la fase de producción'))
 return
 }
 await api.post(`/lots/${id}/phases`, {
 lot_id: Number(id),
 phase_id: destino.id,
 start_date: transitionDate || new Date().toISOString().split('T')[0],
 })
 const { data: newPhases } = await api.get(`/lots/${id}/phases`)
 setPhases(newPhases || [])
 toast.success(t('lots.transitionSuccess', 'Fase de producción iniciada'))
 } catch (err: any) {
 // `R-191`: el 422/400 del servidor se muestra legible — nunca en consola y en silencio.
 toast.error(getErrorMessage(err, t('lots.transitionError', 'Error al transicionar fase')))
 } finally {
 setTransitioning(false)
 }
 }

 // Group events by type for weekly table
 const eventsByType: Record<string, any[]> = {}
 events.forEach(e => {
 if (!eventsByType[e.event_type]) eventsByType[e.event_type] = []
 eventsByType[e.event_type].push(e)
 })

 return (
 <>
 <div className="py-4 sm:py-6">
 {/* ── Header ── */}
 <div className="flex items-center gap-3 mb-6">
 <Link to="/lots" className="text-slate-400 hover transition-colors">
 <ArrowLeft size={20} />
 </Link>
 <div className="flex-1 min-w-0">
 <h1 className="text-2xl font-bold text-[#1E3A5F] truncate">
 {lot.lot_code || `${t('lots.title')} #${lot.id}`}
 </h1>
 <div className="flex items-center gap-2 mt-0.5 flex-wrap">
 <span className="text-sm text-slate-500">{stageLabel}</span>
 {phaseLabel && (
 <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
 {phaseLabel}
 </span>
 )}
 <span className="text-slate-300">·</span>
 <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[lot.status] || 'bg-slate-100 text-slate-600'}`}>
 {t(`lotStatus.${lot.status}`, String(lot.status))}
 </span>
 </div>
 </div>

 {/* Phase transition button (Cría → Producción) */}
 {canTransition && can({ permission: 'lots:create' }) && (
 <Button
 size="sm"
 onClick={() => setShowTransitionModal(true)}
 loading={transitioning}
 >
 {t('lots.transitionToProduction', 'Iniciar Producción')}
 </Button>
 )}

 {/* Close lot button */}
 {lot.status === 'active' && can({ permission: 'lots:create' }) && (
 <Button
 variant="danger"
 size="sm"
 onClick={() => setShowCloseModal(true)}
 loading={closing}
 leftIcon={<Lock size={13} />}
 >
 {t('lots.closeButton', 'Cerrar Lote')}
 </Button>
 )}
 </div>

 {/* Close summary */}
 {closeResult && (
 <div className="mb-6 p-5 bg-emerald-50 border border-emerald-200 rounded-xl">
 <h3 className="text-lg font-bold text-emerald-800 mb-3">{t('lots.closedSummary')}</h3>
 <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
 <div><span className="text-slate-500">{t('lots.age')}:</span> <strong>{closeResult.age_days} {t('lots.days')}</strong></div>
 <div><span className="text-slate-500">{t('lots.totalMortality')}:</span> <strong className="text-red-600">{closeResult.total_mortality}</strong></div>
 <div><span className="text-slate-500">{t('lots.totalFeed')}:</span> <strong>{closeResult.total_feed_kg} {t('lots.kg')}</strong></div>
 <div><span className="text-slate-500">{t('lots.totalEggs')}:</span> <strong>{closeResult.total_eggs}</strong></div>
 <div><span className="text-slate-500">{t('lots.totalEvents')}:</span> <strong>{closeResult.total_events}</strong></div>
 <div><span className="text-slate-500">{t('lots.approvedEvents')}:</span> <strong className="text-emerald-600">{closeResult.approved_events}</strong></div>
 <div><span className="text-slate-500">{t('lots.closure')}:</span> <strong>{closeResult.end_date}</strong></div>
 </div>
 </div>
 )}

 <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
 {/* Left: Operations Panel */}
 <div className="lg:col-span-2 space-y-6">
 {/* ── Quick Actions: stage-specific operations ── */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
 <Plus size={18} className="text-[#5a9bba]" />
 {t('lots.registerOperation')}
 {phaseLabel && (
 <span className="ml-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
 {phaseLabel}
 </span>
 )}
 </h2>
 {can({ permission: 'operations:create' }) && <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
 {stageOps.map(eventType => {
 const Icon = EVENT_ICONS[eventType] ?? Activity
 return (
 <Link
 key={eventType}
 to={`/operations/new?type=${eventType}&lot_id=${lot.id}`}
 className="flex flex-col items-center gap-1.5 p-3 rounded-lg border border-slate-200 hover:border-[#5a9bba] hover:bg-blue-50 transition-colors text-center group"
 >
 <Icon size={20} className="text-[#5a9bba] group-hover:scale-110 transition-transform" />
 <span className="text-xs text-slate-600 leading-tight">{t(`eventsShort.${eventType}`, eventType)}</span>
 </Link>
 )
 })}
 </div>}
 </div>

 {/* G-11: Weekly Summary Table — `R-218` C-01=A: serie del agregado `/reports/lot/{id}/weekly`
 (la LISTA de `/operations` no expone sublistas por contrato). */}
 {semanal.length > 0 && (() => {
 const weekly: Record<number, any> = {}
 semanal.forEach((s: any) => {
 const w = s.week || 0
 weekly[w] = {
 week: w, male_weight: s.weight_g || 0, female_weight: 0,
 male_mort: s.mortality || 0, female_mort: 0,
 feed_kg: s.feed_kg || 0, water_l: s.water_l || 0, date: '',
 }
 })
 const weeks = Object.values(weekly).sort((a: any, b: any) => a.week - b.week)
 if (weeks.length === 0) return null
 return (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mt-4">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Calendar size={18} className="text-[#5a9bba]" /> {t('lots.weeklyView')}</h2>
 <div className="overflow-x-auto">
 <table className="w-full text-xs">
 <thead className="bg-slate-50">
 <tr>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.weekNumber')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.maleWeight')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.femaleWeight')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.maleMort')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.femaleMort')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.feed')}</th>
 <th className="px-3 py-2 text-left font-semibold text-slate-600">{t('weekly.date')}</th>
 </tr>
 </thead>
 <tbody>
 {weeks.map((w: any) => (
 <tr key={w.week} className="border-b border-slate-50 hover:bg-slate-50">
 <td className="px-3 py-2 font-mono font-medium">{w.week || '—'}</td>
 <td className="px-3 py-2">{w.male_weight > 0 ? w.male_weight : '—'}</td>
 <td className="px-3 py-2">{w.female_weight > 0 ? w.female_weight : '—'}</td>
 <td className="px-3 py-2 text-red-600">{w.male_mort > 0 ? w.male_mort : '—'}</td>
 <td className="px-3 py-2 text-red-600">{w.female_mort > 0 ? w.female_mort : '—'}</td>
 <td className="px-3 py-2">{w.feed_kg > 0 ? w.feed_kg.toFixed(1) : '—'}</td>
 <td className="px-3 py-2 text-slate-400">{w.date || '—'}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 )
 })()}

 {/* Recent Events */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Activity size={18} /> {t('lots.lastRecords')}
 </h2>
 {events.length === 0 ? (
 <p className="text-sm text-slate-400">{t('lots.noOperationalRecords')}</p>
 ) : (
 <div className="space-y-2 max-h-80 overflow-y-auto">
 {events.slice(0, 15).map((ev: any) => (
 <div key={ev.id} className="flex items-center justify-between text-sm py-2 border-b border-slate-50 last:border-0">
 <div>
 <span className="font-medium text-slate-700">{ev.event_type}</span>
 <span className="text-slate-400 ml-2">{ev.event_date}</span>
 </div>
 <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
 ev.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
 ev.status === 'registered' ? 'bg-blue-100 text-blue-700' :
 'bg-slate-100 text-slate-600'
 }`}>{ev.status}</span>
 </div>
 ))}
 </div>
 )}
 </div>
 </div>

 {/* Right: KPIs + Info */}
 <div className="space-y-4">
 {/* Lot Info */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Calendar size={18} /> {t('lots.info')}
 </h2>
 <dl className="space-y-2 text-sm">
 <div className="flex justify-between"><dt className="text-slate-500">{t('lots.start')}</dt><dd>{lot.start_date || '—'}</dd></div>
 {/* `R-182`: día natural tal como se capturó (corte del ISO en UTC, sin salto de zona). */}
 <div className="flex justify-between"><dt className="text-slate-500">{t('lots.plannedClose')}</dt><dd>{lot.planned_close_date ? String(lot.planned_close_date).slice(0, 10) : '—'}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('lots.type')}</dt><dd>{stageLabel}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('lots.farm')}</dt><dd>{lot.farm_id || '—'}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('lots.house')}</dt><dd>{lot.house_id || '—'}</dd></div>
 </dl>
 </div>

 {/* KPIs */}
 {kpis && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={18} /> {t('lots.kpis')}
 </h2>
 <div className="space-y-3">
 {kpis.mortality && (
 <div className="p-3 bg-red-50 rounded-lg">
 <p className="text-xs text-red-600 font-medium">{t('lots.mortalityKpi')}</p>
 <p className="text-lg font-bold text-red-700">{kpis.mortality.mortality_rate_pct}%</p>
 <p className="text-xs text-red-500">{kpis.mortality.total_deaths} {t('lots.bajas')}</p>
 </div>
 )}
 {kpis.feed_conversion && (
 <div className="p-3 bg-amber-50 rounded-lg">
 <p className="text-xs text-amber-600 font-medium">{t('lots.feedConversionKpi')}</p>
 <p className="text-lg font-bold text-amber-700">{kpis.feed_conversion.total_feed_kg} {t('lots.kg')}</p>
 </div>
 )}
 {kpis.egg_production && kpis.egg_production.total_eggs > 0 && (
 <div className="p-3 bg-blue-50 rounded-lg">
 <p className="text-xs text-blue-600 font-medium">{t('lots.eggProdKpi')}</p>
 <p className="text-lg font-bold text-blue-700">{kpis.egg_production.total_eggs}</p>
 <p className="text-xs text-blue-500">{kpis.egg_production.hen_day_production_pct}% {t('lots.henDay')}</p>
 </div>
 )}
 {kpis.hatchery_yield && kpis.hatchery_yield.total_chicks_born > 0 && (
 <div className="p-3 bg-purple-50 rounded-lg">
 <p className="text-xs text-purple-600 font-medium">{t('lots.birthsKpi')}</p>
 <p className="text-lg font-bold text-purple-700">{kpis.hatchery_yield.total_chicks_born}</p>
 </div>
 )}
 </div>
 </div>
 )}

 {/* IPE */}
 {kpiIpe && kpiIpe.ipe != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={18} className="text-emerald-600" /> IPE
 </h2>
 <p className="text-3xl font-bold text-emerald-700">{kpiIpe.ipe}</p>
 <p className="text-xs text-slate-500 mt-1">
 {kpiIpe.ipe >= 300 ? '🟢' : kpiIpe.ipe >= 250 ? '🟡' : '🔴'}{' '}
 {kpiIpe.ipe >= 300 ? t('kpi.excellent', 'Excelente') : kpiIpe.ipe >= 250 ? t('kpi.good', 'Bueno') : t('kpi.average', 'Regular')}
 </p>
 <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-slate-500">
 <span>{t('kpi.viability', 'Viab.')} {kpiIpe.viabilidad_pct}%</span>
 <span>{t('kpi.fcr', 'FCR')} {kpiIpe.fcr}</span>
 <span>{t('kpi.avgWeight', 'Peso')} {kpiIpe.avg_weight_g}g</span>
 <span>{t('kpi.ageDays', 'Días')} {kpiIpe.age_days}</span>
 </div>
 </div>
 )}

 {/* Weight Uniformity */}
 {kpiUniformity && kpiUniformity.cv_pct != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Activity size={18} className="text-blue-600" /> {t('kpi.uniformity', 'Uniformidad')}
 </h2>
 <p className={`text-2xl font-bold ${
 kpiUniformity.uniformity_status === 'excellent' ? 'text-emerald-700' :
 kpiUniformity.uniformity_status === 'acceptable' ? 'text-amber-700' : 'text-red-700'
 }`}>CV {kpiUniformity.cv_pct}%</p>
 <p className="text-xs text-slate-500 mt-1">
 {kpiUniformity.uniformity_status === 'excellent' ? '🟢 ' : kpiUniformity.uniformity_status === 'acceptable' ? '🟡 ' : '🔴 '}
 {t(`kpi.${kpiUniformity.uniformity_status}`, kpiUniformity.uniformity_status)}
 {' · '}{kpiUniformity.n_samples} {t('kpi.samples', 'muestras')}
 </p>
 </div>
 )}

 {/* Lot Alerts */}
 {lotAlerts.length > 0 && (
 <div className="bg-white rounded-xl shadow-sm border border-amber-200 p-5">
 <h2 className="font-semibold text-amber-700 mb-3 flex items-center gap-2">
 <AlertTriangle size={18} className="text-amber-500" />
 {t('alerts.activeTitle', 'Alertas activas')}
 <span className="ml-auto text-xs font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">{lotAlerts.length}</span>
 </h2>
 <div className="space-y-2">
 {lotAlerts.map((a: any) => (
 <div key={a.id} className={`flex items-start gap-2 rounded-lg p-2.5 text-xs ${
 a.severity === 'critical' ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'
 }`}>
 <div className="flex-1 min-w-0">
 <span className={`font-bold uppercase ${a.severity === 'critical' ? 'text-red-700' : 'text-amber-700'}`}>
 {String(t(`alerts.severity.${a.severity}`, a.severity))}
 </span>
 <p className="text-slate-700 mt-0.5 leading-snug">{a.message}</p>
 </div>
 {can({ permission: 'operations:update' }) && <button onClick={() => handleResolveAlert(a.id)} className="text-slate-400 hover shrink-0 p-0.5" title={t('alerts.resolve', 'Resolver')}>
 <X size={12} />
 </button>}
 </div>
 ))}
 </div>
 </div>
 )}

 {/* ── Traceability Tree (T-083) ── */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
 <Activity size={18} className="text-teal-600" />
 {t('traceability.title', 'Trazabilidad Generacional')}
 </h2>
 <TraceabilityTree lotId={Number(id)} birdType={birdType} />
 </div>
 </div>
 </div>
 </div>

 {/* ── Modal: Phase Transition (Cría → Producción) ── */}
 <Modal
 open={showTransitionModal}
 onClose={() => setShowTransitionModal(false)}
 title={t('lots.transitionToProduction', 'Iniciar Fase Producción')}
 description={t('lots.transitionConfirm', '¿Confirmar transición a Fase Producción? Esta acción no se puede deshacer.')}
 footer={
 <>
 <Button variant="secondary" onClick={() => setShowTransitionModal(false)}>
 {t('common.cancel', 'Cancelar')}
 </Button>
 <Button onClick={handleTransitionPhase} loading={transitioning}>
 {t('lots.confirmTransition', 'Confirmar')}
 </Button>
 </>
 }
 >
 <div className="space-y-4">
 <Input
 label={t('lots.transitionDate', 'Fecha de transición')}
 type="date"
 value={transitionDate}
 onChange={e => setTransitionDate(e.target.value)}
 />
 <Input
 label={t('lots.populationMale', 'Población machos')}
 type="number"
 min={0}
 placeholder={String(activePhase?.start_population_male ?? 0)}
 value={transitionMale}
 onChange={e => setTransitionMale(e.target.value)}
 />
 <Input
 label={t('lots.populationFemale', 'Población hembras')}
 type="number"
 min={0}
 placeholder={String(activePhase?.start_population_female ?? 0)}
 value={transitionFemale}
 onChange={e => setTransitionFemale(e.target.value)}
 />
 </div>
 </Modal>

 {/* ── Modal: Close Lot confirmation ── */}
 <Modal
 open={showCloseModal}
 onClose={() => setShowCloseModal(false)}
 title={t('lots.closeButton', 'Cerrar Lote')}
 description={t('lots.closeConfirm', '¿Estás seguro de cerrar este lote? No podrás registrar más operaciones.')}
 footer={
 <>
 <Button variant="secondary" onClick={() => setShowCloseModal(false)}>
 {t('common.cancel', 'Cancelar')}
 </Button>
 <Button variant="danger" onClick={handleCloseLot} loading={closing}>
 {t('lots.closeButton', 'Cerrar Lote')}
 </Button>
 </>
 }
 >
 <p className="text-sm text-slate-600">
 {t('lots.closeWarning', 'Se generará un resumen final con todas las métricas del lote.')}
 </p>
 </Modal>
 </>
 )
}
