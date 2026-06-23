import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

export default function LotReportPage() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<any>(null)
  const toast = useToast()

  useEffect(() => {
    api.get(`/reports/lot/${id}`).then(r => setReport(r.data)).catch((e: any) => toast.error(getErrorMessage(e, 'Error al cargar')))
  }, [id])

  if (!report) return <div className="p-6 text-slate-500">Cargando...</div>

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">
      <Link to="/reports" className="text-slate-400 hover:text-slate-600 flex items-center gap-1 mb-4"><ArrowLeft size={16} /> Reportes</Link>
      <h1 className="text-2xl font-bold text-[#1E3A5F] mb-6">Reporte: {report.lot?.lot_code || `Lote #${report.lot?.id}`}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-700 mb-3">Info del Lote</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Estado</dt><dd>{report.lot?.status}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Inicio</dt><dd>{report.lot?.start_date || '—'}</dd></div>
          </dl>
        </div>
        {report.opening_balance && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-700 mb-3">Balance Inicial</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Aves</dt><dd>{report.opening_balance.total_birds}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Machos</dt><dd>{report.opening_balance.total_males}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Hembras</dt><dd>{report.opening_balance.total_females}</dd></div>
            </dl>
          </div>
        )}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:col-span-2">
          <h2 className="font-semibold text-slate-700 mb-3">Resumen de Eventos</h2>
          <p className="text-sm text-slate-600 mb-2">Total: {report.event_summary?.total_events || 0} eventos</p>
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
