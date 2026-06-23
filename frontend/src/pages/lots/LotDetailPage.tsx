import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, TrendingUp, Activity, Calendar, Bird, Wheat, Skull, Syringe, Egg, Baby } from 'lucide-react'
import api from '../../services/api'

const BIRD_TYPE_LABELS: Record<string, string> = {
  grandparent: 'Progenitoras', breeder: 'Reproductoras', broiler: 'Engorde',
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-800', closed: 'bg-slate-100 text-slate-600', cancelled: 'bg-red-100 text-red-800',
}

// Operations available per bird_type (productive stage)
const STAGE_OPERATIONS: Record<string, { label: string; eventType: string; icon: any }[]> = {
  grandparent: [
    { label: 'Inspección Granja', eventType: 'farm_inspection', icon: Activity },
    { label: 'Recepción de Aves', eventType: 'bird_reception', icon: Bird },
    { label: 'Distribución', eventType: 'bird_distribution', icon: Bird },
    { label: 'Alimento', eventType: 'feed_registration', icon: Wheat },
    { label: 'Pesaje', eventType: 'weight_recording', icon: TrendingUp },
    { label: 'Mortalidad', eventType: 'mortality_recording', icon: Skull },
    { label: 'Vacunación', eventType: 'vaccination', icon: Syringe },
    { label: 'Medicación', eventType: 'medication', icon: Syringe },
    { label: 'Salida de Aves', eventType: 'bird_exit', icon: Bird },
  ],
  breeder: [
    { label: 'Inspección Granja', eventType: 'farm_inspection', icon: Activity },
    { label: 'Recepción de Aves', eventType: 'bird_reception', icon: Bird },
    { label: 'Distribución', eventType: 'bird_distribution', icon: Bird },
    { label: 'Alimento', eventType: 'feed_registration', icon: Wheat },
    { label: 'Pesaje', eventType: 'weight_recording', icon: TrendingUp },
    { label: 'Mortalidad', eventType: 'mortality_recording', icon: Skull },
    { label: 'Vacunación', eventType: 'vaccination', icon: Syringe },
    { label: 'Medicación', eventType: 'medication', icon: Syringe },
    { label: 'Recolección Huevos', eventType: 'egg_collection', icon: Egg },
    { label: 'Clasificación Huevos', eventType: 'egg_classification', icon: Egg },
    { label: 'Despacho Huevos', eventType: 'egg_dispatch', icon: Egg },
    { label: 'Salida de Aves', eventType: 'bird_exit', icon: Bird },
  ],
  broiler: [
    { label: 'Inspección Granja', eventType: 'farm_inspection', icon: Activity },
    { label: 'Recepción Pollitos', eventType: 'bird_reception', icon: Baby },
    { label: 'Alimento', eventType: 'feed_registration', icon: Wheat },
    { label: 'Pesaje', eventType: 'weight_recording', icon: TrendingUp },
    { label: 'Mortalidad', eventType: 'mortality_recording', icon: Skull },
    { label: 'Vacunación', eventType: 'vaccination', icon: Syringe },
    { label: 'Medicación', eventType: 'medication', icon: Syringe },
    { label: 'Cierre de Lote', eventType: 'lot_closure', icon: Activity },
  ],
}

export default function LotDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const [lot, setLot] = useState<any>(null)
  const [kpis, setKpis] = useState<any>(null)
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [closeResult, setCloseResult] = useState<any>(null)
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    const fetch = async () => {
      try {
        // Get all lots and find this one
        const { data: lots } = await api.get('/lots?limit=100')
        const found = (lots as any[]).find((l: any) => l.id === Number(id))
        setLot(found || null)

        // Get KPIs
        const { data: kpiData } = await api.get(`/reports/kpis?lot_id=${id}`)
        setKpis(kpiData)

        // Get events for this lot
        const { data: evts } = await api.get(`/operations?lot_id=${id}&limit=50`)
        setEvents(evts || [])
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [id])

  if (loading) return <div className="p-6 text-slate-500">{t('common.loading')}</div>
  if (!lot) return <div className="p-6 text-slate-500">Lote no encontrado</div>

  const birdType = lot.bird_type || 'broiler'
  const stageOps = STAGE_OPERATIONS[birdType] || STAGE_OPERATIONS.broiler
  const stageLabel = BIRD_TYPE_LABELS[birdType] || birdType

  // G-09: Close lot with summary
  const handleCloseLot = async () => {
    if (!confirm('¿Estás seguro de cerrar este lote? Se generará un resumen final.')) return
    setClosing(true)
    try {
      const { data } = await api.post(`/lots/${id}/close`)
      setCloseResult(data)
      setLot((prev: any) => ({ ...prev, status: 'closed' }))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al cerrar lote')
    } finally {
      setClosing(false)
    }
  }

  // Group events by type
  const eventsByType: Record<string, any[]> = {}
  events.forEach(e => {
    if (!eventsByType[e.event_type]) eventsByType[e.event_type] = []
    eventsByType[e.event_type].push(e)
  })

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/lots" className="text-slate-400 hover:text-slate-600"><ArrowLeft size={20} /></Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-[#1E3A5F]">{lot.lot_code || `Lote #${lot.id}`}</h1>
          <p className="text-sm text-slate-500">{stageLabel} · {lot.status === 'active' ? 'Activo' : lot.status}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[lot.status] || 'bg-slate-100'}`}>
          {lot.status === 'active' ? 'Activo' : lot.status === 'closed' ? 'Cerrado' : 'Cancelado'}
        </span>
        {/* G-09: Close lot button */}
        {lot.status === 'active' && (
          <button onClick={handleCloseLot} disabled={closing}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition disabled:opacity-50">
            {closing ? 'Cerrando...' : '🔒 Cerrar Lote'}
          </button>
        )}
      </div>

      {/* G-09: Close summary modal */}
      {closeResult && (
        <div className="mb-6 p-5 bg-emerald-50 border border-emerald-200 rounded-xl">
          <h3 className="text-lg font-bold text-emerald-800 mb-3">✅ Lote Cerrado — Resumen Final</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div><span className="text-slate-500">Edad:</span> <strong>{closeResult.age_days} días</strong></div>
            <div><span className="text-slate-500">Mortalidad total:</span> <strong className="text-red-600">{closeResult.total_mortality}</strong></div>
            <div><span className="text-slate-500">Alimento total:</span> <strong>{closeResult.total_feed_kg} kg</strong></div>
            <div><span className="text-slate-500">Huevos totales:</span> <strong>{closeResult.total_eggs}</strong></div>
            <div><span className="text-slate-500">Eventos totales:</span> <strong>{closeResult.total_events}</strong></div>
            <div><span className="text-slate-500">Aprobados:</span> <strong className="text-emerald-600">{closeResult.approved_events}</strong></div>
            <div><span className="text-slate-500">Cierre:</span> <strong>{closeResult.end_date}</strong></div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Operations Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Actions — Stage-specific operations */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <Plus size={18} /> Registrar Operación — {stageLabel}
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {stageOps.map(op => {
                const Icon = op.icon
                return (
                  <Link key={op.eventType}
                    to={`/operations/new?type=${op.eventType}&lot_id=${lot.id}`}
                    className="flex flex-col items-center gap-1 p-3 rounded-lg border border-slate-200 hover:border-[#2563EB] hover:bg-blue-50 transition text-center">
                    <Icon size={22} className="text-[#2563EB]" />
                    <span className="text-xs text-slate-600 leading-tight">{op.label}</span>
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
                <h2 className="font-semibold text-slate-700 mb-3">📅 Vista Semanal</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">N° Sem</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Peso ♂ (g)</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Peso ♀ (g)</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Mort. ♂</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Mort. ♀</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Alim. (kg)</th>
                        <th className="px-3 py-2 text-left font-semibold text-slate-600">Fecha</th>
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
              <Activity size={18} /> Últimos Registros
            </h2>
            {events.length === 0 ? (
              <p className="text-sm text-slate-400">Sin registros operativos</p>
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
              <Calendar size={18} /> Información
            </h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Inicio</dt><dd>{lot.start_date || '—'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Tipo</dt><dd>{stageLabel}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Granja</dt><dd>{lot.farm_id || '—'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Galpón</dt><dd>{lot.house_id || '—'}</dd></div>
            </dl>
          </div>

          {/* KPIs */}
          {kpis && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <TrendingUp size={18} /> KPIs
              </h2>
              <div className="space-y-3">
                {kpis.mortality && (
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-red-600 font-medium">Mortalidad</p>
                    <p className="text-lg font-bold text-red-700">{kpis.mortality.mortality_rate_pct}%</p>
                    <p className="text-xs text-red-500">{kpis.mortality.total_deaths} bajas</p>
                  </div>
                )}
                {kpis.feed_conversion && (
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <p className="text-xs text-amber-600 font-medium">Conversión Alimenticia</p>
                    <p className="text-lg font-bold text-amber-700">{kpis.feed_conversion.total_feed_kg} kg</p>
                  </div>
                )}
                {kpis.egg_production && kpis.egg_production.total_eggs > 0 && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-600 font-medium">Prod. Huevos</p>
                    <p className="text-lg font-bold text-blue-700">{kpis.egg_production.total_eggs}</p>
                    <p className="text-xs text-blue-500">{kpis.egg_production.hen_day_production_pct}% hen-day</p>
                  </div>
                )}
                {kpis.hatchery_yield && kpis.hatchery_yield.total_chicks_born > 0 && (
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-xs text-purple-600 font-medium">Nacimientos</p>
                    <p className="text-lg font-bold text-purple-700">{kpis.hatchery_yield.total_chicks_born}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
