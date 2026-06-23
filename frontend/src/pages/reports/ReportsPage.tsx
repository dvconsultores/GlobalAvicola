import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Download } from 'lucide-react'
import api from '../../services/api'

export default function ReportsPage() {
  const { t } = useTranslation()
  const [kpis, setKpis] = useState<any>(null)
  const [lotId, setLotId] = useState(2)
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    api.get(`/reports/kpis?lot_id=${lotId}`).then(r => setKpis(r.data)).catch(() => {})
    // G-12: Fetch events for chart visualization
    api.get(`/operations?lot_id=${lotId}&limit=200`).then(r => {
      const events = r.data?.events || r.data || []
      const byDate: Record<string, any> = {}
      events.forEach((e: any) => {
        const d = e.event_date || ''
        if (!byDate[d]) byDate[d] = { date: d, mortality: 0, feed_kg: 0, water_l: 0, weight_g: 0 }
        e.bird_movements?.forEach((bm: any) => {
          if (e.event_type === 'mortality_recording') byDate[d].mortality += bm.quantity || 0
          if (e.event_type === 'weight_recording' && bm.avg_weight) byDate[d].weight_g = bm.avg_weight
        })
        e.feed_movements?.forEach((fm: any) => { byDate[d].feed_kg += fm.quantity_kg || 0 })
        if (e.water_liters) byDate[d].water_l += e.water_liters
      })
      setChartData(Object.values(byDate).sort((a: any, b: any) => a.date.localeCompare(b.date)))
    }).catch(() => {})
  }, [lotId])

  // G-06: Export handler
  const handleExport = async (format: 'excel' | 'pdf') => {
    try {
      const { data } = await api.post('/reports/export', { format, lot_id: lotId })
      alert(`Exportación ${format.toUpperCase()} iniciada: ${data?.message || 'OK'}`)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al exportar')
    }
  }

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-[#1E3A5F]">📊 {t('nav.reports')}</h1>
        <div className="flex gap-2 items-center">
          <input type="number" value={lotId} onChange={e => setLotId(Number(e.target.value))}
            className="w-24 h-9 px-2 border border-slate-300 rounded text-sm" placeholder="Lote ID" />
          {/* G-06: Export buttons */}
          <button onClick={() => handleExport('excel')}
            className="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-emerald-700 flex items-center gap-1">
            <Download size={14} /> Excel
          </button>
          <button onClick={() => handleExport('pdf')}
            className="bg-red-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-red-700 flex items-center gap-1">
            <Download size={14} /> PDF
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {kpis?.mortality && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">💀 {t('reports.mortality')}</h2>
            <p className="text-3xl font-bold text-red-600">{kpis.mortality.mortality_rate_pct}%</p>
            <p className="text-sm text-slate-500">{kpis.mortality.total_deaths} bajas / {kpis.mortality.initial_population} inicial</p>
          </div>
        )}
        {kpis?.feed_conversion && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">🌾 {t('reports.feedConversion')}</h2>
            <p className="text-3xl font-bold text-amber-600">{kpis.feed_conversion.feed_conversion_ratio}</p>
            <p className="text-sm text-slate-500">{kpis.feed_conversion.total_feed_kg} kg</p>
          </div>
        )}
        {kpis?.egg_production && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">🥚 {t('reports.eggProduction')}</h2>
            <p className="text-3xl font-bold text-blue-600">{kpis.egg_production.hen_day_production_pct}%</p>
            <p className="text-sm text-slate-500">{kpis.egg_production.total_eggs} huevos</p>
          </div>
        )}
        {kpis?.hatchery_yield && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">🐤 {t('reports.hatchery')}</h2>
            <p className="text-3xl font-bold text-purple-600">{kpis.hatchery_yield.total_chicks_born}</p>
            <p className="text-sm text-slate-500">pollitos nacidos</p>
          </div>
        )}
      </div>

      {/* G-12: Charts — recharts visualization (matching old app: water, mortality, weight) */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Mortality Bar Chart */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">💀 Mortalidad Diaria</h2>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="mortality" fill="#EF4444" name="Bajas" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Feed Consumption Bar Chart */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">🌾 Consumo de Alimento (kg)</h2>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="feed_kg" fill="#F59E0B" name="Alimento kg" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Weight Line Chart */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 lg:col-span-2">
            <h2 className="font-semibold text-slate-700 mb-3">⚖️ Evolución de Peso (g)</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData.filter((d: any) => d.weight_g > 0)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="weight_g" stroke="#2563EB" name="Peso (g)" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Quick Access + New KPIs from gaps */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">
        <h2 className="font-semibold text-slate-700 mb-3">📋 {t('reports.quickAccess')}</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/reports/lot/2" className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800 transition">
            📋 Reporte Lote #2
          </Link>
          <Link to="/reports/sap" className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 transition">
            🔄 SAP Comparison
          </Link>
        </div>
      </div>

      {/* G-01, G-02, G-03: New KPI cards if available */}
      {(kpis?.animal_welfare || kpis?.vaccination_efficiency || kpis?.transfer_efficiency) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {kpis?.animal_welfare && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-700 mb-3">🏥 Bienestar Animal</h2>
              <p className="text-3xl font-bold text-green-600">{kpis.animal_welfare.welfare_score_pct}%</p>
            </div>
          )}
          {kpis?.vaccination_efficiency && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-700 mb-3">💉 Eficiencia Vacunación</h2>
              <p className="text-3xl font-bold text-indigo-600">{kpis.vaccination_efficiency.vaccination_coverage_pct}%</p>
            </div>
          )}
          {kpis?.transfer_efficiency && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-700 mb-3">🚛 Eficiencia Traslado</h2>
              <p className="text-3xl font-bold text-teal-600">{kpis.transfer_efficiency.transfer_efficiency_pct}%</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
