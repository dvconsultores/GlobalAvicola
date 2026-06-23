import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

export default function SapManagerPage() {
  const { t } = useTranslation()
  const [refs, setRefs] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [payloads, setPayloads] = useState<any[]>([])
  const [conn, setConn] = useState<any>(null)
  const toast = useToast()

  useEffect(() => {
    api.get('/sap/references?limit=10').then(r => setRefs(r.data.references || [])).catch(() => {})
    api.get('/sap/sync/jobs?limit=5').then(r => setJobs(r.data.jobs || [])).catch(() => {})
    api.get('/sap/payloads?limit=5').then(r => setPayloads(r.data.payloads || [])).catch(() => {})
    api.get('/sap/connection-check').then(r => setConn(r.data)).catch(() => {})
  }, [])

  const handleConsolidate = async () => {
    try {
      const r = await api.post('/sap/consolidate', {})
      toast.success(`Consolidados: ${r.data.length} movimientos`)
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Error al consolidar'))
    }
  }

  const handleExport = async () => {
    try {
      const r = await api.post('/sap/export', {})
      toast.success(`Job #${r.data.sync_job_id}: ${r.data.message}`)
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Error al exportar'))
    }
  }

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-[#1E3A5F] mb-2">🔄 {t('nav.sap')}</h1>
      {conn && (
        <p className={`text-sm mb-6 ${conn.connected ? 'text-green-600' : 'text-red-600'}`}>
          {conn.connected ? '✅' : '❌'} {conn.adapter}
        </p>
      )}

      <div className="flex flex-wrap gap-3 mb-6">
        <button onClick={handleConsolidate} className="bg-[#1E3A5F] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition">
          📦 {t('sap.consolidate')}
        </button>
        <button onClick={handleExport} className="bg-teal-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-teal-700 transition">
          📤 {t('sap.export')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-2 text-sm">{t('sap.references')} ({refs.length})</h2>
          {refs.slice(0, 5).map((r: any) => (
            <div key={r.id} className="text-xs text-slate-600 py-1 border-b border-slate-50 last:border-0">
              <span className="font-mono">{r.sap_code}</span> — {r.ref_type}
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-2 text-sm">{t('sap.syncJobs')} ({jobs.length})</h2>
          {jobs.map((j: any) => (
            <div key={j.id} className="text-xs text-slate-600 py-1 border-b border-slate-50 last:border-0">
              Job #{j.id}: {j.direction} — {j.status} ({j.success_count}/{j.total_records})
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <h2 className="font-semibold text-slate-700 mb-2 text-sm">{t('sap.payloads')} ({payloads.length})</h2>
          {payloads.map((p: any) => (
            <div key={p.id} className="text-xs text-slate-600 py-1 border-b border-slate-50 last:border-0">
              {p.status}: {p.sap_document_id || 'pending'}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
