import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { formatFechaHora } from '../../utils/dates'
import {
 RefreshCw, CheckCircle, XCircle, Package, Upload, Clock,
 Send, AlertTriangle, FileText, Building2, Database, ListChecks,
} from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'
import SubNavHeader from '../../components/layout/SubNavHeader'
import { KpiCard, Badge } from '../../components/ui'
import { useCompanyStore } from '../../stores/company.store'
import { useAuthStore } from '../../stores/auth.store'
import SapInboundPanel, {
 SapInboundErrors, SapInboundObjects, SapInboundRecords,
 inboundStatusLabel, inboundStatusTone, tr,
} from './SapInboundPanel'

type SapTab = 'inbound' | 'records' | 'inboundErrors' | 'overview' | 'pending' | 'sent' | 'errors' | 'log'

// SPEC 005: la fase es READ ONLY, así que la pantalla abre por el inbound.
const SAP_TABS: { key: SapTab; labelKey: string; fallback: string; icon: typeof RefreshCw }[] = [
 { key: 'inbound', labelKey: 'sap.inbound.tabObjects', fallback: 'Objetos SAP', icon: Database },
 { key: 'records', labelKey: 'sap.inbound.tabRecords', fallback: 'Registros', icon: ListChecks },
 { key: 'inboundErrors', labelKey: 'sap.inbound.tabErrors', fallback: 'Errores de sincronización', icon: AlertTriangle },
 { key: 'overview', labelKey: 'sap.overview', fallback: 'General', icon: RefreshCw },
 { key: 'pending', labelKey: 'sap.pending', fallback: 'Pendientes', icon: Clock },
 { key: 'sent', labelKey: 'sap.sent', fallback: 'Enviados', icon: Send },
 { key: 'errors', labelKey: 'sap.errors', fallback: 'Errores', icon: AlertTriangle },
 { key: 'log', labelKey: 'sap.log', fallback: 'Bitácora', icon: FileText },
]

export default function SapManagerPage() {
 const can = useCan()
 const { t, i18n } = useTranslation()
 const toast = useToast()
 const { user } = useAuthStore()
 const { activeCompanyName } = useCompanyStore()
 const [activeTab, setActiveTab] = useState<SapTab>('inbound')
 const [inboundObjects, setInboundObjects] = useState<any[]>([])
 const [inboundJobs, setInboundJobs] = useState<any[]>([])
 const [inboundRecords, setInboundRecords] = useState<any[]>([])
 const [inboundErrors, setInboundErrors] = useState<{ records: any[]; jobs: any[] }>({ records: [], jobs: [] })
 const [syncing, setSyncing] = useState(false)
 const [refs, setRefs] = useState<any[]>([])
 const [jobs, setJobs] = useState<any[]>([])
 const [payloads, setPayloads] = useState<any[]>([])
 const [conn, setConn] = useState<any>(null)
 // `R-212` · AC-04: 403 no se disfraza de «vacío».
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const [refresco, setRefresco] = useState(0)

 useEffect(() => {
 const propaga403 = (e: any) => {
 if (e?.response?.status === 403) throw e
 return null
 }
 Promise.all([
 api.get('/sap/references?limit=10').catch((e: any) => propaga403(e) ?? { data: { references: [] } }),
 api.get('/sap/sync/jobs?limit=5').catch((e: any) => propaga403(e) ?? { data: { jobs: [] } }),
 api.get('/sap/payloads?limit=5').catch((e: any) => propaga403(e) ?? { data: { payloads: [] } }),
 api.get('/sap/connection-check').catch((e: any) => propaga403(e) ?? { data: null }),
 api.get('/sap/inbound/objects').catch((e: any) => propaga403(e) ?? { data: { objects: [] } }),
 api.get('/sap/inbound/jobs?limit=50').catch((e: any) => propaga403(e) ?? { data: { jobs: [] } }),
 api.get('/sap/inbound/records?limit=50').catch((e: any) => propaga403(e) ?? { data: { records: [] } }),
 api.get('/sap/inbound/errors?limit=50').catch((e: any) => propaga403(e) ?? { data: { records: [], jobs: [] } }),
 ]).then(([refRes, jobsRes, payloadRes, connRes, objRes, inJobsRes, inRecRes, inErrRes]) => {
 setRefs(refRes.data.references || [])
 setJobs(jobsRes.data.jobs || [])
 setPayloads(payloadRes.data.payloads || [])
 setConn(connRes.data)
 setInboundObjects(objRes.data?.objects || [])
 setInboundJobs(inJobsRes.data?.jobs || [])
 setInboundRecords(inRecRes.data?.records || [])
 setInboundErrors({ records: inErrRes.data?.records || [], jobs: inErrRes.data?.jobs || [] })
 setEstado('ok')
 }).catch((err: any) => setEstado(err?.response?.status === 403 ? 'prohibido' : 'error'))
 }, [refresco])

 const handleConsolidate = async () => {
 try {
 const r = await api.post('/sap/consolidate', {})
 toast.success(t('sap.consolidatedToast', { count: r.data.length }))
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('sap.errorConsolidate')))
 }
 }

 const handleExport = async () => {
 try {
 const r = await api.post('/sap/export', {})
 toast.success(t('sap.exportToast', { id: r.data.sync_job_id, message: r.data.message }))
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('sap.errorExport')))
 }
 }

 // SPEC 005 · sincronización inbound (solo lectura). Un fallo de SAP llega como job `failed`,
 // no como error HTTP: se informa sin fingir éxito.
 const handleSync = async () => {
 setSyncing(true)
 try {
 const r = await api.post('/sap/inbound/sync', {})
 const hechos: any[] = r.data?.jobs || []
 const fallidos = hechos.filter(j => j.status === 'failed').length
 const resumen = t('sap.inbound.syncToast', {
 defaultValue: 'Sincronización: {{ok}} objetos completados, {{failed}} con error',
 ok: hechos.length - fallidos, failed: fallidos,
 })
 if (fallidos > 0) toast.warning(resumen)
 else toast.success(resumen)
 setRefresco(n => n + 1)
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('sap.inbound.syncError', 'No se pudo sincronizar con SAP')))
 } finally {
 setSyncing(false)
 }
 }

 const inbound = conn?.inbound_hana ?? null
 // Mientras el outbound esté deshabilitado no se ofrece exportar: la fase es READ ONLY.
 const outboundEnabled = conn?.outbound?.enabled === true

 // Calcular KPIs
 const pendingCount = payloads.filter(p => p.status === 'pending' || p.status === 'draft').length
 const sentCount = payloads.filter(p => p.status === 'sent' || p.status === 'confirmed').length
 const errorCount = payloads.filter(p => p.status === 'error').length

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={() => setRefresco(n => n + 1)} />
 </div>
 )
 }

 return (
 <div>
 {/* Header */}
 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
 <div className="min-w-0">
 <SubNavHeader
 title={t('nav.sap', 'Integración SAP')}
 hideBack
 actions={
 <div className="flex items-center gap-2 flex-wrap">
 {(activeCompanyName || user?.company_name) && (
 <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 px-2 py-1 rounded-full bg-slate-100">
 <Building2 size={11} />
 {activeCompanyName || user?.company_name}
 </span>
 )}
 {conn && (
 // El modo manual no es una conexión: el indicador habla del inbound real.
 <div className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full ${inboundStatusTone(inbound?.status)}`}>
 {conn.connected ? <CheckCircle size={14} /> : <XCircle size={14} />}
 {inboundStatusLabel(t, inbound?.status)}
 </div>
 )}
 </div>
 }
 />
 </div>
 </div>

 <SapInboundPanel
 readiness={inbound}
 jobs={inboundJobs}
 outboundEnabled={outboundEnabled}
 canSync={can({ permission: 'sap:send_sap' })}
 syncing={syncing}
 onSync={handleSync}
 />

 {/* KPI Cards */}
 <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
 <KpiCard
 icon={Clock}
 label={t('sap.pendingDocuments', 'Documentos Pendientes')}
 value={pendingCount}
 color="amber"
 />
 <KpiCard
 icon={Send}
 label={t('sap.sentDocuments', 'Enviados a SAP')}
 value={sentCount}
 color="green"
 />
 <KpiCard
 icon={AlertTriangle}
 label={t('sap.errorDocuments', 'Errores SAP')}
 value={errorCount}
 color="red"
 />
 <KpiCard
 icon={Package}
 label={t('sap.references', 'Referencias SAP')}
 value={refs.length}
 color="blue"
 subtitle={t('sap.lastSync', 'Sincronizadas')}
 />
 </div>

 {/* Action buttons */}
 <div className="flex flex-wrap gap-3 mb-6">
 {can({ permission: 'sap:send_sap' }) && <button onClick={handleConsolidate}
 className="bg-[#1E3A5F] text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-800 transition inline-flex items-center gap-2 shadow-sm">
 <Package size={16} /> {t('sap.consolidate', 'Consolidar')}
 </button>}
 {outboundEnabled && can({ permission: 'sap:send_sap' }) && <button onClick={handleExport}
 className="bg-teal-600 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-teal-700 transition inline-flex items-center gap-2 shadow-sm">
 <Upload size={16} /> {t('sap.export', 'Exportar a SAP')}
 </button>}
 </div>

 {/* Tabs */}
 <div className="flex gap-1 mb-5 overflow-x-auto pb-1 scrollbar-hide">
 {SAP_TABS.map((tab) => {
 const isActive = activeTab === tab.key
 const Icon = tab.icon
 return (
 <button
 key={tab.key}
 onClick={() => setActiveTab(tab.key)}
 className={`
 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap shrink-0
 ${isActive
 ? 'bg-[#1E3A5F] text-white shadow-md'
 : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
 }
 `}
 >
 <Icon size={16} />
 {tr(t, tab.labelKey, tab.fallback)}
 </button>
 )
 })}
 </div>

 {/* Tab Content */}
 <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
 {activeTab === 'inbound' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.inbound.tabObjects', 'Objetos SAP')}</h3>
 <SapInboundObjects objects={inboundObjects} jobs={inboundJobs} />
 </div>
 )}

 {activeTab === 'records' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.inbound.tabRecords', 'Registros')}</h3>
 <SapInboundRecords records={inboundRecords} />
 </div>
 )}

 {activeTab === 'inboundErrors' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.inbound.tabErrors', 'Errores de sincronización')}</h3>
 <SapInboundErrors records={inboundErrors.records} jobs={inboundErrors.jobs} />
 </div>
 )}

 {activeTab === 'overview' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.recentActivity', 'Actividad reciente')}</h3>
 {jobs.length === 0 && payloads.length === 0 ? (
 <div className="text-center py-8">
 <RefreshCw size={32} className="mx-auto text-slate-300 mb-2" />
 <p className="text-sm text-slate-500">{t('sap.noActivity', 'Sin actividad reciente')}</p>
 </div>
 ) : (
 <div className="space-y-3">
 {jobs.slice(0, 5).map((j: any) => (
 <div key={j.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
 <div>
 <p className="text-sm font-medium text-slate-700">
 {t('sap.syncJob', 'Trabajo de sincronización')} #{j.id}
 </p>
 <p className="text-xs text-slate-500 mt-0.5">
 {j.direction} · {j.success_count}/{j.total_records} {t('sap.records', 'registros')}
 </p>
 </div>
 <Badge variant={j.status === 'completed' ? 'approved' : j.status === 'error' ? 'rejected' : 'pending'} size="sm">
 {j.status}
 </Badge>
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {activeTab === 'pending' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.pendingDocuments', 'Documentos Pendientes')}</h3>
 {payloads.filter(p => p.status === 'pending' || p.status === 'draft').length === 0 ? (
 <div className="text-center py-8">
 <CheckCircle size={32} className="mx-auto text-emerald-300 mb-2" />
 <p className="text-sm text-slate-500">{t('sap.noPending', 'Sin documentos pendientes')}</p>
 </div>
 ) : (
 <div className="divide-y divide-slate-100">
 {payloads.filter(p => p.status === 'pending' || p.status === 'draft').map((p: any) => (
 <div key={p.id} className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg transition">
 <div>
 <p className="text-sm font-medium text-slate-700">{p.sap_document_id || `#${p.id}`}</p>
 <p className="text-xs text-slate-500">{p.event_type || t('sap.document', 'Documento')}</p>
 </div>
 <Badge variant="pending" size="sm">{p.status}</Badge>
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {activeTab === 'sent' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.sentDocuments', 'Enviados a SAP')}</h3>
 {payloads.filter(p => p.status === 'sent' || p.status === 'confirmed').length === 0 ? (
 <div className="text-center py-8">
 <Send size={32} className="mx-auto text-slate-300 mb-2" />
 <p className="text-sm text-slate-500">{t('sap.noSent', 'Sin envíos a SAP')}</p>
 </div>
 ) : (
 <div className="divide-y divide-slate-100">
 {payloads.filter(p => p.status === 'sent' || p.status === 'confirmed').map((p: any) => (
 <div key={p.id} className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg transition">
 <div>
 <p className="text-sm font-medium text-slate-700">{p.sap_document_id || `#${p.id}`}</p>
 <p className="text-xs text-slate-500">{formatFechaHora(p.created_at, i18n.language)}</p>
 </div>
 <Badge variant={p.status === 'confirmed' ? 'approved' : 'sent_sap'} size="sm">{p.status}</Badge>
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {activeTab === 'errors' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.errorDocuments', 'Errores SAP')}</h3>
 {payloads.filter(p => p.status === 'error').length === 0 ? (
 <div className="text-center py-8">
 <CheckCircle size={32} className="mx-auto text-emerald-300 mb-2" />
 <p className="text-sm text-slate-500">{t('sap.noErrors', 'Sin errores SAP')}</p>
 </div>
 ) : (
 <div className="divide-y divide-slate-100">
 {payloads.filter(p => p.status === 'error').map((p: any) => (
 <div key={p.id} className="py-3 hover:bg-red-50 px-2 rounded-lg transition">
 <div className="flex items-center justify-between">
 <p className="text-sm font-medium text-slate-700">{p.sap_document_id || `#${p.id}`}</p>
 <Badge variant="error_sap" size="sm">{t('sap.error', 'Error')}</Badge>
 </div>
 {p.error_message && (
 <p className="text-xs text-red-600 mt-1 font-mono">{p.error_message}</p>
 )}
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {activeTab === 'log' && (
 <div className="p-5">
 <h3 className="text-sm font-bold text-slate-700 mb-4">{t('sap.syncJobs', 'Trabajos de Sincronización')}</h3>
 {jobs.length === 0 ? (
 <div className="text-center py-8">
 <FileText size={32} className="mx-auto text-slate-300 mb-2" />
 <p className="text-sm text-slate-500">{t('sap.noJobs', 'Sin trabajos de sincronización')}</p>
 </div>
 ) : (
 <div className="divide-y divide-slate-100">
 {jobs.map((j: any) => (
 <div key={j.id} className="py-3 hover:bg-slate-50 px-2 rounded-lg transition">
 <div className="flex items-center justify-between">
 <p className="text-sm font-medium text-slate-700">
 {t('sap.syncJob', 'Sincronización')} #{j.id}
 </p>
 <Badge variant={j.status === 'completed' ? 'approved' : j.status === 'error' ? 'rejected' : 'pending'} size="sm">
 {j.status}
 </Badge>
 </div>
 <p className="text-xs text-slate-500 mt-1">
 {j.direction} · {j.success_count}/{j.total_records} {t('sap.records', 'registros')}
 {j.created_at && ` · ${formatFechaHora(j.created_at, i18n.language)}`}
 </p>
 </div>
 ))}
 </div>
 )}
 </div>
 )}
 </div>
 </div>
 )
}
