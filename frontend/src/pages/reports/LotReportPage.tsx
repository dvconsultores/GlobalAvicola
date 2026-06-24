import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Download } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Button } from '../../components/ui'
import { exportToExcel, exportToPDF, lotReportToRows } from '../../utils/export'

export default function LotReportPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<any>(null)
  const [exporting, setExporting] = useState<'excel'|'pdf'|null>(null)
  const toast = useToast()

  useEffect(() => {
    api.get(`/reports/lot/${id}`).then(r => setReport(r.data)).catch((e: any) => toast.error(getErrorMessage(e, t('reports.errorLoading'))))
  }, [id])

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

  if (!report) return <div className="p-6 text-slate-500">{t('common.loading')}</div>

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">
      <Link to="/reports" className="text-slate-400 hover:text-slate-600 flex items-center gap-1 mb-4"><ArrowLeft size={16} /> {t('nav.reports')}</Link>
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
      </div>
    </div>
  )
}
