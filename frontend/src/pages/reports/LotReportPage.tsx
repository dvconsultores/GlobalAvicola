import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Download, TrendingUp, Activity } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Button } from '../../components/ui'
import { exportToExcel, exportToPDF, lotReportToRows } from '../../utils/export'

export default function LotReportPage() {
 const { t } = useTranslation()
 const { id } = useParams<{ id: string }>()
 const [report, setReport] = useState<any>(null)
 const [kpiIpe, setKpiIpe] = useState<any>(null)
 const [kpiUniformity, setKpiUniformity] = useState<any>(null)
 const [kpiAfcr, setKpiAfcr] = useState<any>(null)
 // `GA-REM-022 AC07`. «Eficiencia de Vacunación» y «Eficiencia de Traslado» son KPI que el
 // cliente exige: estaban calculados en el backend y no los consumía nadie.
 const [kpiVacunacion, setKpiVacunacion] = useState<any>(null)
 const [kpiTraslado, setKpiTraslado] = useState<any>(null)
 const [kpiIncubadora, setKpiIncubadora] = useState<any>(null)
 const [exporting, setExporting] = useState<'excel'|'pdf'|null>(null)
 // `R-212` · AC-05: 403/500 ⇒ estado con reintento, nunca spinner eterno.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const toast = useToast()

 const cargar = () => {
 api.get(`/reports/lot/${id}`).then(r => { setReport(r.data); setEstado('ok') }).catch((e: any) => {
 setEstado(e?.response?.status === 403 ? 'prohibido' : 'error')
 toast.error(getErrorMessage(e, t('reports.errorLoading')))
 })
 Promise.allSettled([
 api.get(`/reports/kpi/ipe/${id}`),
 api.get(`/reports/kpi/weight-uniformity/${id}`),
 api.get(`/reports/kpis/afcr?lot_id=${id}`),
 api.get(`/reports/kpis/vaccination-efficiency?lot_id=${id}`),
 api.get(`/reports/kpis/transfer-efficiency?lot_id=${id}`),
 api.get(`/reports/kpis/hatchery?lot_id=${id}`),
 ]).then(([ipeRes, uniformRes, afcrRes, vacRes, traRes, incRes]) => {
 if (ipeRes.status === 'fulfilled') setKpiIpe(ipeRes.value.data)
 if (uniformRes.status === 'fulfilled') setKpiUniformity(uniformRes.value.data)
 if (afcrRes.status === 'fulfilled') setKpiAfcr(afcrRes.value.data)
 if (vacRes.status === 'fulfilled') setKpiVacunacion(vacRes.value.data)
 if (traRes.status === 'fulfilled') setKpiTraslado(traRes.value.data)
 if (incRes.status === 'fulfilled') setKpiIncubadora(incRes.value.data)
 })
 }

 useEffect(() => { cargar() }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

 const handleExport = async (format: 'excel'|'pdf') => {
 setExporting(format)
 try {
 const headers: Record<string, string> = {
 lot_code: t('lots.code', 'Código'), bird_type: t('lots.type', 'Tipo'),
 status: t('common.status', 'Estado'), start_date: t('lots.start', 'Inicio'),
 end_date: t('lots.end', 'Cierre'), total_birds: t('reports.birds', 'Aves'),
 males: t('reports.males', 'Machos'), females: t('reports.females', 'Hembras'),
 total_events: t('dashboard.totalEvents', 'Total eventos'),
 }
 const rows = lotReportToRows(report)
 const lotCode = report?.lot?.lot_code ?? id
 const filename = `GlobalAvicola_Lote_${lotCode}_${new Date().toISOString().slice(0,10)}`
 if (format === 'excel') await exportToExcel(rows, headers, filename)
 else await exportToPDF(rows, headers, `${t('reports.lotReport', 'Reporte de Lote')}: ${lotCode}`, filename)
 } finally {
 setExporting(null)
 }
 }

 if (estado !== 'ok') return <div className="py-4 sm:py-6"><ErrorState kind={estado} onRetry={cargar} /></div>

 if (!report) return <div className="py-4 sm:py-6 text-slate-500">{t('common.loading')}</div>

 return (
 <div className="py-4 sm:py-6">
 <Link to="/reports" className="text-slate-400 hover flex items-center gap-1 mb-4"><ArrowLeft size={16} /> {t('nav.reports')}</Link>
 <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
 <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('reports.lotReport')}: {report.lot?.lot_code || `${t('lots.title')} #${report.lot?.id}`}</h1>
 <div className="flex gap-2">
 <Button size="sm" variant="secondary" leftIcon={<Download size={14} />} loading={exporting === 'excel'} onClick={() => handleExport('excel')}>
 Excel
 </Button>
 <Button size="sm" variant="danger" leftIcon={<Download size={14} />} loading={exporting === 'pdf'} onClick={() => handleExport('pdf')}>
 PDF
 </Button>
 </div>
 </div>

 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3">{t('reports.lotInfo')}</h2>
 <dl className="space-y-2 text-sm">
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.status')}</dt><dd>{report.lot?.status}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.start')}</dt><dd>{report.lot?.start_date || '—'}</dd></div>
 </dl>
 </div>
 {report.opening_balance && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3">{t('reports.openingBalance')}</h2>
 <dl className="space-y-2 text-sm">
 <div className="flex justify-between"><dt className="text-slate-500">{t('reports.birds')}</dt><dd>{report.opening_balance.total_birds}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('reports.males')}</dt><dd>{report.opening_balance.total_males}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('reports.females')}</dt><dd>{report.opening_balance.total_females}</dd></div>
 </dl>
 </div>
 )}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:col-span-2">
 <h2 className="font-semibold text-slate-700 mb-3">{t('reports.eventsSummary')}</h2>
 <p className="text-sm text-slate-600 mb-2">{t('dashboard.totalEvents')}: {report.event_summary?.total_events || 0} {t('reports.eventsCount')}</p>
 {report.event_summary?.by_type && (
 <div className="flex flex-wrap gap-2">
 {Object.entries(report.event_summary.by_type).map(([k, v]) => (
 <span key={k} className="px-2 py-1 bg-slate-100 rounded-lg text-xs">{k}: {v as number}</span>
 ))}
 </div>
 )}
 </div>

 {/* `GA-REM-022 AC05`. Los indicadores solo cuentan eventos aprobados, de modo que un
 lote con actividad sin aprobar los muestra en cero. Decirlo es parte del requisito:
 sin este aviso, un cero indistinguible de «no hay nada que medir» induce a error. */}
 {kpiIncubadora?.insufficient_data && (
 <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
 <p className="text-sm font-semibold text-amber-900">
 {t('reports.onlyApproved', 'Los indicadores se calculan solo con datos aprobados')}
 </p>
 <p className="text-xs text-amber-800 mt-1">
 {t('reports.onlyApprovedDetail', 'Este lote todavía no tiene registros aprobados suficientes, por lo que sus indicadores aparecen sin valor en lugar de en cero.')}
 </p>
 </div>
 )}

 {/* Incubadora: nacimiento, eclosión y rendimiento (`docs/02 §3.12.1`) */}
 {kpiIncubadora && kpiIncubadora.nacimiento_pct != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={16} className="text-amber-600" /> {t('kpi.hatchery', 'Incubadora')}
 </h2>
 <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.birthRate', 'Nacimiento')}</dt><dd className="font-medium">{kpiIncubadora.nacimiento_pct}%</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.hatchRate', 'Eclosión')}</dt><dd className="font-medium">{kpiIncubadora.eclosion_pct ?? '—'}%</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.hatcheryYield', 'Rendimiento')}</dt><dd className="font-medium">{kpiIncubadora.rendimiento_pct}%</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.chicksBorn', 'Nacidos')}</dt><dd className="font-medium">{kpiIncubadora.total_chicks_born}</dd></div>
 </dl>
 </div>
 )}

 {/* Eficiencia de vacunación y de traslado — exigidos por el cliente (`AC07`) */}
 {kpiVacunacion && kpiVacunacion.vaccination_coverage_pct != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Activity size={16} className="text-indigo-600" /> {t('kpi.vaccinationEfficiency', 'Eficiencia de Vacunación')}
 </h2>
 <p className="text-3xl font-black text-indigo-700">{kpiVacunacion.vaccination_coverage_pct}%</p>
 </div>
 )}

 {kpiTraslado && kpiTraslado.transfer_efficiency_pct != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={16} className="text-teal-600" /> {t('kpi.transferEfficiency', 'Eficiencia de Traslado')}
 </h2>
 <p className="text-3xl font-black text-teal-700">{kpiTraslado.transfer_efficiency_pct}%</p>
 </div>
 )}

 {/* IPE KPI */}
 {kpiIpe && kpiIpe.ipe != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={16} className="text-emerald-600" /> IPE {t('kpi.europeanProductionIndex', '')}
 </h2>
 <p className="text-4xl font-black text-emerald-700 mb-1">{kpiIpe.ipe}</p>
 <p className="text-xs text-slate-500 mb-3">
 {kpiIpe.ipe >= 300 ? '🟢 ' : kpiIpe.ipe >= 250 ? '🟡 ' : '🔴 '}
 {kpiIpe.ipe >= 300 ? t('kpi.excellent', 'Excelente') : kpiIpe.ipe >= 250 ? t('kpi.good', 'Bueno') : t('kpi.average', 'Regular')}
 </p>
 <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.viability', 'Viabilidad')}</dt><dd className="font-medium">{kpiIpe.viabilidad_pct}%</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">FCR</dt><dd className="font-medium">{kpiIpe.fcr}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.avgWeight', 'Peso prom.')}</dt><dd className="font-medium">{kpiIpe.avg_weight_g}g</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.dailyGain', 'Gan. diaria')}</dt><dd className="font-medium">{kpiIpe.ganancia_diaria_g}g/día</dd></div>
 <div className="flex justify-between col-span-2"><dt className="text-slate-500">{t('kpi.ageDays', 'Edad')}</dt><dd className="font-medium">{kpiIpe.age_days} días</dd></div>
 </dl>
 </div>
 )}

 {/* Weight Uniformity KPI */}
 {kpiUniformity && kpiUniformity.cv_pct != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <Activity size={16} className="text-blue-600" /> {t('kpi.uniformity', 'Uniformidad de Lote')}
 </h2>
 <p className={`text-4xl font-black mb-1 ${
 kpiUniformity.uniformity_status === 'excellent' ? 'text-emerald-700' :
 kpiUniformity.uniformity_status === 'acceptable' ? 'text-amber-700' : 'text-red-700'
 }`}>CV {kpiUniformity.cv_pct}%</p>
 <p className="text-xs text-slate-500 mb-3">
 {kpiUniformity.uniformity_status === 'excellent' ? '🟢 ' : kpiUniformity.uniformity_status === 'acceptable' ? '🟡 ' : '🔴 '}
 {String(t(`kpi.${kpiUniformity.uniformity_status}`, kpiUniformity.uniformity_status))}
 </p>
 <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.meanWeight', 'Peso medio')}</dt><dd className="font-medium">{kpiUniformity.mean_weight_g?.toFixed(1) ?? '—'}g</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.samples', 'Muestras')}</dt><dd className="font-medium">{kpiUniformity.n_samples}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.min')}</dt><dd className="font-medium">{kpiUniformity.min_weight_g?.toFixed(1) ?? '—'}g</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.max')}</dt><dd className="font-medium">{kpiUniformity.max_weight_g?.toFixed(1) ?? '—'}g</dd></div>
 </dl>
 </div>
 )}

 {/* AFCR KPI */}
 {kpiAfcr && kpiAfcr.afcr != null && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
 <TrendingUp size={16} className="text-violet-600" /> AFCR {t('kpi.afcr', 'FCR Ajustado')}
 </h2>
 <p className={`text-4xl font-black mb-1 ${
 kpiAfcr.afcr <= 1.6 ? 'text-emerald-700' : kpiAfcr.afcr <= 1.8 ? 'text-amber-700' : 'text-red-700'
 }`}>{kpiAfcr.afcr}</p>
 <p className="text-xs text-slate-500 mb-3">
 {kpiAfcr.afcr <= 1.6 ? '🟢 ' : kpiAfcr.afcr <= 1.8 ? '🟡 ' : '🔴 '}
 {kpiAfcr.afcr <= 1.6 ? t('kpi.excellent', 'Excelente') : kpiAfcr.afcr <= 1.8 ? t('kpi.good', 'Bueno') : t('kpi.average', 'Regular')}
 </p>
 <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.totalFeed', 'Alimento total')}</dt><dd className="font-medium">{kpiAfcr.total_feed_kg?.toFixed(1) ?? '—'} kg</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('kpi.totalWeight', 'Peso total')}</dt><dd className="font-medium">{kpiAfcr.total_weight_kg?.toFixed(1) ?? '—'} kg</dd></div>
 </dl>
 </div>
 )}
 </div>
 </div>
 )
}
