import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Droplets, Download, BarChart2, Wheat, Egg, Baby, Truck, ClipboardList, RefreshCw } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { exportToExcel, exportToPDF, kpisToRows } from '../../utils/export'
import { Button } from '../../components/ui'

export default function ReportsPage() {
 const { t, i18n } = useTranslation()
 const [kpis, setKpis] = useState<any>(null)
 const [lotId, setLotId] = useState(2)
 // `R-220` · A2 (C#18): selector real de lote — el listado de lotes alimenta la lista.
 const [lotes, setLotes] = useState<any[]>([])
 const [chartData, setChartData] = useState<any[]>([])
 // `R-212` · AC-04.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const [refresco, setRefresco] = useState(0)

 useEffect(() => {
 // `R-220` · A2: opciones del selector (si la sesión no puede listar, se conserva
 // el lote actual como única opción — la pantalla nunca queda sin contexto).
 api.get('/lots?limit=100').then(r => setLotes(r.data || [])).catch(() => setLotes([]))
 api.get(`/reports/kpis?lot_id=${lotId}`).then(r => { setKpis(r.data); setEstado('ok') }).catch((err: any) => setEstado(err?.response?.status === 403 ? 'prohibido' : 'error'))
 // G-12: Fetch events for chart visualization
 // `R-218` · C-01=A: las series salen del agregado semanal del lote — la LISTA de
 // `/operations` no expone sublistas (C#4) y los gráficos quedaban planos.
 api.get(`/reports/lot/${lotId}/weekly`).then(r => {
 const semanas = r.data?.weeks || []
 setChartData(semanas.map((s: any) => ({
 date: `S${s.week}`, mortality: s.mortality || 0, feed_kg: s.feed_kg || 0,
 water_l: s.water_l || 0, weight_g: s.weight_g || 0,
 })))
 }).catch((err: any) => setEstado(err?.response?.status === 403 ? 'prohibido' : 'error'))
 }, [lotId, refresco])

 // T-081: Real client-side export
 const [exporting, setExporting] = useState<'excel'|'pdf'|null>(null)

 const handleExport = async (format: 'excel' | 'pdf') => {
 setExporting(format)
 try {
 // `R-220` · C6 (F G-14): cabeceras de exportación por clave i18n, no ES fijo.
 const headers: Record<string, string> = {
 lot_id: t('reports.exportHeaders.lot_id', 'Lote ID'),
 mortality_rate: t('reports.exportHeaders.mortality_rate', 'Mortalidad %'),
 total_deaths: t('reports.exportHeaders.total_deaths', 'Bajas'),
 feed_conversion: t('reports.exportHeaders.feed_conversion', 'Conv. Alimento'),
 total_feed_kg: t('reports.exportHeaders.total_feed_kg', 'Alimento (kg)'),
 total_eggs: t('reports.exportHeaders.total_eggs', 'Huevos'),
 hen_day_pct: t('reports.exportHeaders.hen_day_pct', '% Postura'),
 chicks_born: t('reports.exportHeaders.chicks_born', 'Pollitos nacidos'),
 hatchability_pct: t('reports.exportHeaders.hatchability_pct', '% Nacimiento'),
 }
 const rows = kpisToRows(kpis, lotId)
 const filename = `GlobalAvicola_KPI_Lote${lotId}_${new Date().toISOString().slice(0,10)}`
 if (format === 'excel') {
 await exportToExcel(rows, headers, filename)
 } else {
 await exportToPDF(rows, headers, `KPIs — Lote ${lotId}`, filename, i18n.language)
 }
 } catch {
 console.error('Export failed')
 } finally {
 setExporting(null)
 }
 }

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={() => setRefresco(n => n + 1)} />
 </div>
 )
 }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
 <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('nav.reports')}</h1>
 <div className="flex gap-2 items-center">
 <select
 data-filtro="lote"
 aria-label={t('reports.selectLot', 'Seleccionar lote')}
 value={lotId}
 onChange={e => setLotId(Number(e.target.value))}
 className="h-9 px-2 border border-slate-300 rounded text-sm bg-white"
 >
 {(lotes.length ? lotes : [{ id: lotId, lot_code: `#${lotId}` }]).map((l: any) => (
 <option key={l.id} value={l.id}>{l.lot_code || `#${l.id}`}</option>
 ))}
 </select>
 <Button
 size="sm"
 variant="secondary"
 leftIcon={<Download size={14} />}
 loading={exporting === 'excel'}
 onClick={() => handleExport('excel')}
 >
 Excel
 </Button>
 <Button
 size="sm"
 variant="danger"
 leftIcon={<Download size={14} />}
 loading={exporting === 'pdf'}
 onClick={() => handleExport('pdf')}
 >
 PDF
 </Button>
 </div>
 </div>

 {/* KPI Cards */}
 <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
 {kpis?.mortality && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><span className="text-red-500">↓</span> {t('reports.mortality')}</h2>
 <p className="text-3xl font-bold text-red-600">{kpis.mortality.mortality_rate_pct}%</p>
 <p className="text-sm text-slate-500">{kpis.mortality.total_deaths} {t('reports.bajas')} / {kpis.mortality.initial_population} {t('reports.inicial')}</p>
 </div>
 )}
 {kpis?.feed_conversion && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Wheat size={16} className="text-amber-500" /> {t('reports.feedConversion')}</h2>
 <p className="text-3xl font-bold text-amber-600">{kpis.feed_conversion.feed_conversion_ratio}</p>
 <p className="text-sm text-slate-500">{kpis.feed_conversion.total_feed_kg} kg</p>
 </div>
 )}
 {kpis?.egg_production && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Egg size={16} className="text-blue-500" /> {t('reports.eggProduction')}</h2>
 <p className="text-3xl font-bold text-blue-600">{kpis.egg_production.hen_day_production_pct}%</p>
 <p className="text-sm text-slate-500">{kpis.egg_production.total_eggs} {t('reports.huevos')}</p>
 </div>
 )}
 {kpis?.hatchery_yield && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Baby size={16} className="text-purple-500" /> {t('reports.hatchery')}</h2>
 <p className="text-3xl font-bold text-purple-600">{kpis.hatchery_yield.total_chicks_born}</p>
 <p className="text-sm text-slate-500">{t('reports.pollitosNacidos')}</p>
 </div>
 )}
 </div>

 {/* G-12: Charts — recharts visualization (matching old app: water, mortality, weight) */}
 {chartData.length > 0 && (
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
 {/* Mortality Bar Chart */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><BarChart2 size={16} className="text-slate-400" /> {t('reports.dailyMortality')}</h2>
 <ResponsiveContainer width="100%" height={250}>
 <BarChart data={chartData}>
 <CartesianGrid strokeDasharray="3 3" />
 <XAxis dataKey="date" fontSize={11} />
 <YAxis fontSize={11} />
 <Tooltip />
 <Bar dataKey="mortality" fill="#EF4444" name={t('reports.deaths')} radius={[4, 4, 0, 0]} />
 </BarChart>
 </ResponsiveContainer>
 </div>

 {/* Feed Consumption Bar Chart */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Wheat size={16} className="text-amber-400" /> {t('reports.feedConsumption')}</h2>
 <ResponsiveContainer width="100%" height={250}>
 <BarChart data={chartData}>
 <CartesianGrid strokeDasharray="3 3" />
 <XAxis dataKey="date" fontSize={11} />
 <YAxis fontSize={11} />
 <Tooltip />
 <Bar dataKey="feed_kg" fill="#F59E0B" name={t('reports.feedKg')} radius={[4, 4, 0, 0]} />
 </BarChart>
 </ResponsiveContainer>
 </div>

 {/* Water Consumption Bar Chart — `GA-REM-021-A` · B05 (AC02: la serie deja de estar vacía) */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Droplets size={16} className="text-sky-400" /> {t('reports.waterConsumption')}</h2>
 <ResponsiveContainer width="100%" height={250}>
 <BarChart data={chartData}>
 <CartesianGrid strokeDasharray="3 3" />
 <XAxis dataKey="date" fontSize={11} />
 <YAxis fontSize={11} />
 <Tooltip />
 <Bar dataKey="water_l" fill="#0EA5E9" name={t('reports.waterL')} radius={[4, 4, 0, 0]} />
 </BarChart>
 </ResponsiveContainer>
 </div>

 {/* Weight Line Chart */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 lg:col-span-2">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><BarChart2 size={16} className="text-blue-400" /> {t('reports.weightEvolution')}</h2>
 <ResponsiveContainer width="100%" height={250}>
 <LineChart data={chartData.filter((d: any) => d.weight_g > 0)}>
 <CartesianGrid strokeDasharray="3 3" />
 <XAxis dataKey="date" fontSize={11} />
 <YAxis fontSize={11} />
 <Tooltip />
 <Legend />
 <Line type="monotone" dataKey="weight_g" stroke="#5a9bba" name={t('reports.weightG')} strokeWidth={2} dot={{ r: 4 }} />
 </LineChart>
 </ResponsiveContainer>
 </div>
 </div>
 )}

 {/* Quick Access + New KPIs from gaps */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">
 <h2 className="font-semibold text-slate-700 mb-3">{t('reports.quickAccess')}</h2>
 <div className="flex flex-wrap gap-3">
 <Link to={`/reports/lot/${lotId}`} className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800 transition">
 <ClipboardList size={16} className="inline-block mr-1.5 -mt-0.5" aria-hidden="true" />
 {t('reports.lotReportLink', { id: 2 })}
 </Link>
 <Link to="/reports/sap" className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 transition">
 <RefreshCw size={16} className="inline-block mr-1.5 -mt-0.5" aria-hidden="true" />
 {t('reports.sapComparisonLink')}
 </Link>
 </div>
 </div>

 {/* G-01, G-03: tarjetas KPI. G-02 (vacunación) retirada de la superficie certificada:
        R-133 `DEFERRED_FUNCTIONAL_DEFINITION` (Owner 2026-09-16). */}
 {(kpis?.animal_welfare || kpis?.transfer_efficiency) && (
 <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
 {kpis?.animal_welfare && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><span className="w-4 h-4 rounded-full bg-green-500 inline-block" /> {t('reports.animalWelfare')}</h2>
 <p className="text-3xl font-bold text-green-600">{kpis.animal_welfare.welfare_score_pct}%</p>
 </div>
 )}
 {kpis?.transfer_efficiency && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Truck size={16} className="text-teal-500" /> {t('reports.transferEfficiency')}</h2>
 <p className="text-3xl font-bold text-teal-600">{kpis.transfer_efficiency.transfer_efficiency_pct}%</p>
 </div>
 )}
 </div>
 )}
 </div>
 )
}
