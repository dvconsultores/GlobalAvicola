import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, TrendingUp, Activity, Calendar, Lock } from 'lucide-react'
import { EVENT_ICONS } from '../../components/Icon'
import { Button, Modal, Input } from '../../components/ui'
import api from '../../services/api'

// ─── Status badge colours ────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-800',
  closed: 'bg-slate-100 text-slate-600',
  cancelled: 'bg-red-100 text-red-800',
}

// ─── Operations per stage / phase ────────────────────────────────────────────
// Each key maps to the ordered list of event_types available in that context.
// Icons come from the canonical EVENT_ICONS map in Icon.tsx (lucide-react).

const STAGE_OPERATIONS: Record<string, string[]> = {
  // PROGENITORAS / ABUELAS — full cycle including egg production
  grandparent: [
    'grandparent_import',
    'farm_inspection',
    'bird_reception',
    'bird_distribution',
    'transport_inspection',
    'feed_registration',
    'weight_recording',
    'mortality_recording',
    'cull_recording',
    'vaccination',
    'medication',
    'egg_collection',
    'egg_classification',
    'egg_dispatch',
    'bird_exit',
  ],

  // REPRODUCTORAS — FASE CRÍA (no hay operaciones de huevo aún)
  breeder_rearing: [
    'farm_inspection',
    'bird_reception',
    'bird_distribution',
    'transport_inspection',
    'feed_registration',
    'weight_recording',
    'mortality_recording',
    'cull_recording',
    'vaccination',
    'medication',
    'bird_exit',
  ],

  // REPRODUCTORAS — FASE PRODUCCIÓN (ciclo diario de postura)
  breeder_production: [
    'farm_inspection',
    'transport_inspection',
    'feed_registration',
    'weight_recording',
    'mortality_recording',
    'cull_recording',
    'vaccination',
    'medication',
    'egg_collection',
    'egg_classification',
    'egg_dispatch',
    'bird_exit',
  ],

  // INCUBADORA — desde recepción de huevos hasta despacho de pollitos
  hatchery: [
    'egg_reception_hatchery',
    'hatchery_inspection',
    'transport_inspection',
    'incubation_load',
    'ovoscopy',
    'transfer_to_hatcher',
    'birth_registration',
    'chick_dispatch',
  ],

  // ENGORDE — desde recepción hasta desalojo a planta
  broiler: [
    'farm_inspection',
    'bird_reception',
    'bird_distribution',
    'transport_inspection',
    'feed_registration',
    'weight_recording',
    'mortality_recording',
    'cull_recording',
    'vaccination',
    'medication',
    'bird_exit',
    'lot_closure',
  ],
}

// ─── Determine stage ops key from lot + active phase ─────────────────────────
function resolveStageKey(birdType: string, activePhase: string | null): string {
  if (birdType === 'breeder') {
    // If phase name / code contains production keywords → production ops
    if (activePhase && /producc|production|hf|huevo/i.test(activePhase)) {
      return 'breeder_production'
    }
    return 'breeder_rearing'
  }
  return birdType in STAGE_OPERATIONS ? birdType : 'broiler'
}


export default function LotDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const [lot, setLot] = useState<any>(null)
  const [kpis, setKpis] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [phases, setPhases] = useState<any[]>([])
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

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const { data: lots } = await api.get('/lots?limit=200')
        const found = (lots as any[]).find((l: any) => l.id === Number(id))
        setLot(found || null)

        const [kpiRes, evtRes, phaseRes] = await Promise.allSettled([
          api.get(`/reports/kpis?lot_id=${id}`),
          api.get(`/operations?lot_id=${id}&limit=50`),
          api.get(`/lots/${id}/phases`),
        ])
        if (kpiRes.status === 'fulfilled') setKpis(kpiRes.value.data)
        if (evtRes.status === 'fulfilled') setEvents(evtRes.value.data || [])
        if (phaseRes.status === 'fulfilled') setPhases(phaseRes.value.data || [])
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [id])

  if (loading) return <div className="p-6 text-slate-500">{t('common.loading')}</div>
  if (!lot) return <div className="p-6 text-slate-500">{t('lots.lotNotFound')}</div>

  const birdType = lot.bird_type || 'broiler'
  const activePhase = phases.find((p: any) => p.is_active)
  const activePhaseName: string | null = activePhase?.phase?.name ?? activePhase?.phase?.code ?? null
  const stageKey = resolveStageKey(birdType, activePhaseName)
  const stageOps = STAGE_OPERATIONS[stageKey] ?? STAGE_OPERATIONS.broiler
  const stageLabel = t(`birdTypes.${birdType}`, birdType)

  // Phase label for breeder badge
  const phaseLabel = stageKey === 'breeder_production'
    ? t('phases.production', 'Producción')
    : stageKey === 'breeder_rearing'
    ? t('phases.rearing', 'Cría')
    : null

  // Can transition from rearing to production
  const canTransition = birdType === 'breeder' && stageKey === 'breeder_rearing' && lot.status === 'active'

  const handleCloseLot = async () => {
    setShowCloseModal(false)
    setClosing(true)
    try {
      const { data } = await api.post(`/lots/${id}/close`)
      setCloseResult(data)
      setLot((prev: any) => ({ ...prev, status: 'closed' }))
    } catch (err: any) {
      console.error(err.response?.data?.detail || t('lots.closeError'))
    } finally {
      setClosing(false)
    }
  }

  const handleTransitionPhase = async () => {
    setShowTransitionModal(false)
    setTransitioning(true)
    try {
      await api.post(`/lots/${id}/phases`, {
        phase_code: 'production',
        start_date: transitionDate || new Date().toISOString().split('T')[0],
        start_population_male: Number(transitionMale) || activePhase?.start_population_male || 0,
        start_population_female: Number(transitionFemale) || activePhase?.start_population_female || 0,
      })
      const { data: newPhases } = await api.get(`/lots/${id}/phases`)
      setPhases(newPhases || [])
    } catch (err: any) {
      console.error(err.response?.data?.detail || t('lots.transitionError', 'Error al transicionar fase'))
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
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      {/* ── Header ── */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/lots" className="text-slate-400 hover:text-slate-600 transition-colors">
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
              {t(`lotStatus.${lot.status}`, lot.status)}
            </span>
          </div>
        </div>

        {/* Phase transition button (Cría → Producción) */}
        {canTransition && (
          <Button
            size="sm"
            onClick={() => setShowTransitionModal(true)}
            loading={transitioning}
          >
            {t('lots.transitionToProduction', 'Iniciar Producción')}
          </Button>
        )}

        {/* Close lot button */}
        {lot.status === 'active' && (
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
              <Plus size={18} className="text-[#2563EB]" />
              {t('lots.registerOperation')}
              {phaseLabel && (
                <span className="ml-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                  {phaseLabel}
                </span>
              )}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {stageOps.map(eventType => {
                const Icon = EVENT_ICONS[eventType] ?? Activity
                return (
                  <Link
                    key={eventType}
                    to={`/operations/new?type=${eventType}&lot_id=${lot.id}`}
                    className="flex flex-col items-center gap-1.5 p-3 rounded-lg border border-slate-200 hover:border-[#2563EB] hover:bg-blue-50 transition-colors text-center group"
                  >
                    <Icon size={20} className="text-[#2563EB] group-hover:scale-110 transition-transform" />
                    <span className="text-xs text-slate-600 leading-tight">{t(`eventsShort.${eventType}`, eventType)}</span>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* G-11: Weekly Summary Table (matching old app's week-based organization) */}
          {events.length > 0 && (() => {
            const weekly: Record<number, any> = {}
            events.forEach(e => {
              e.bird_movements?.forEach((bm: any) => {
                const w = bm.week_number || 0
                if (!weekly[w]) weekly[w] = { week: w, male_weight: 0, female_weight: 0, male_mort: 0, female_mort: 0, feed_kg: 0, date: e.event_date }
                if (e.event_type === 'weight_recording') {
                  if (bm.sex === 'male') weekly[w].male_weight = bm.avg_weight || 0
                  else if (bm.sex === 'female') weekly[w].female_weight = bm.avg_weight || 0
                  else weekly[w].male_weight = bm.avg_weight || 0
                }
                if (e.event_type === 'mortality_recording') {
                  if (bm.sex === 'male') weekly[w].male_mort += bm.quantity || 0
                  else if (bm.sex === 'female') weekly[w].female_mort += bm.quantity || 0
                  else weekly[w].male_mort += bm.quantity || 0
                }
              })
              e.feed_movements?.forEach((fm: any) => {
                const w = fm.week_number || 0
                if (!weekly[w]) weekly[w] = { week: w, male_weight: 0, female_weight: 0, male_mort: 0, female_mort: 0, feed_kg: 0, date: e.event_date }
                weekly[w].feed_kg += fm.quantity_kg || 0
              })
            })
            const weeks = Object.values(weekly).sort((a: any, b: any) => a.week - b.week)
            if (weeks.length === 0) return null
            return (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mt-4">
                <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Calendar size={18} className="text-[#2563EB]" /> {t('lots.weeklyView')}</h2>
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
  )
}
