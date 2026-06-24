import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Shield } from 'lucide-react'
import api from '../../services/api'


export default function AuditPage() {
  const { t } = useTranslation()
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/audit?limit=20')
      .then(r => { setLogs(r.data.logs || []); setTotal(r.data.total || 0) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-[#1E3A5F] mb-6">
        <Shield size={24} className="inline-block mr-2 -mt-0.5" aria-hidden="true" />
        {t('nav.audit')}
      </h1>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
          <span className="text-sm font-semibold text-slate-700">{t('audit.recentActivity')}</span>
          <span className="text-xs text-slate-500">{total} {t('audit.records')}</span>
        </div>
        {loading ? (
          <p className="px-5 py-8 text-center text-slate-500">{t('common.loading')}</p>
        ) : logs.length === 0 ? (
          <p className="px-5 py-8 text-center text-slate-400">{t('audit.noRecords')}</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {logs.map((log: any) => (
              <div key={log.id} className="px-5 py-3 hover:bg-slate-50 transition">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-slate-700">{log.action}</span>
                  <span className="text-slate-400">|</span>
                  <span className="text-slate-500">{log.entity_type}#{log.entity_id}</span>
                  <span className="text-slate-400 ml-auto text-xs">{new Date(log.created_at).toLocaleString()}</span>
                </div>
                {log.change_reason && <p className="text-xs text-slate-500 mt-1">{log.change_reason}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
