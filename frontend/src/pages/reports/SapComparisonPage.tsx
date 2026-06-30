import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

export default function SapComparisonPage() {
 const { t } = useTranslation()
 const toast = useToast()
 const [data, setData] = useState<any>(null)

 useEffect(() => {
 api.get('/reports/sap-comparison').then(r => setData(r.data)).catch((e: any) => toast.error(getErrorMessage(e, t('reports.errorLoading'))))
 }, [])

 if (!data) return <div className="py-4 sm:py-6 text-slate-500">{t('common.loading')}</div>

 return (
 <div className="py-4 sm:py-6">
 <Link to="/reports" className="text-slate-400 hover flex items-center gap-1 mb-4"><ArrowLeft size={16} /> {t('nav.reports')}</Link>
 <h1 className="text-2xl font-bold text-[#1E3A5F] mb-6">{t('reports.sapComparison')}</h1>
 <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
 <p className="text-3xl font-bold text-[#1E3A5F]">{data.total_with_sap_ref}</p>
 <p className="text-sm text-slate-500">{t('reports.withSapRef')}</p>
 </div>
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
 <p className="text-3xl font-bold text-emerald-600">{data.matched_with_sap}</p>
 <p className="text-sm text-slate-500">{t('reports.sapConfirmed')}</p>
 </div>
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
 <p className="text-3xl font-bold text-amber-600">{data.pending_sap_sync}</p>
 <p className="text-sm text-slate-500">{t('reports.pendingSync')}</p>
 </div>
 </div>
 {data.events?.length > 0 && (
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
 <div className="px-5 py-3 bg-slate-50 border-b text-sm font-semibold text-slate-700">{t('reports.eventsWithSapRef')}</div>
 <div className="divide-y divide-slate-100">
 {data.events.map((ev: any) => (
 <div key={ev.id} className="px-5 py-3 flex justify-between text-sm">
 <span>#{ev.id} {ev.event_type}</span>
 <span className="text-slate-400 font-mono text-xs">{ev.sap_ref || '—'}</span>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 )
}
