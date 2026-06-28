/**
 * MyPendingPage — operaciones propias en estado draft/registered
 * Solo visible para operadores móviles (view_type === 'mobile')
 * Usa filter ?registered_by_me=true&status=draft,registered
 */
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Clock, RefreshCw } from 'lucide-react'
import api from '../../services/api'
import { Badge, statusToVariant } from '../../components/ui'

interface Operation {
 id: number
 event_type: string
 event_date: string
 status: string
 lot?: { name: string }
 notes?: string
}

export default function MyPendingPage() {
 const { t } = useTranslation()
 const navigate = useNavigate()
 const [ops, setOps] = useState<Operation[]>([])
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)

 const fetch = useCallback(async () => {
 setLoading(true)
 setError(null)
 try {
 const res = await api.get('/operations', {
 params: { registered_by_me: true, status: 'draft,registered', limit: 50 },
 })
 setOps(res.data?.items ?? res.data ?? [])
 } catch {
 setError(t('errors.loadFailed', 'Error al cargar'))
 } finally {
 setLoading(false)
 }
 }, [t])

 useEffect(() => { fetch() }, [fetch])

 return (
 <div className="min-h-screen bg-slate-50 pb-24">
 {/* Page header */}
 <div className="bg-white border-b border-slate-200 px-4 py-4 flex items-center justify-between">
 <div className="flex items-center gap-2">
 <Clock size={18} className="text-[#5a9bba]" />
 <h1 className="text-base font-semibold text-slate-800">
 {t('nav.myPending', 'Mis Pendientes')}
 </h1>
 </div>
 <button
 onClick={fetch}
 disabled={loading}
 aria-label={t('common.refresh', 'Actualizar')}
 className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover hover:bg-slate-100 transition-colors disabled:opacity-50"
 >
 <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
 </button>
 </div>

 <div className="px-4 py-4 space-y-3">
 {loading && (
 <div className="text-center py-12 text-slate-400 text-sm">
 {t('common.loading', 'Cargando...')}
 </div>
 )}

 {error && (
 <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
 {error}
 </div>
 )}

 {!loading && !error && ops.length === 0 && (
 <div className="text-center py-16">
 <Clock size={40} className="mx-auto text-slate-300 mb-3" />
 <p className="text-slate-500 text-sm">{t('operations.noPending', 'No tienes registros pendientes')}</p>
 </div>
 )}

 {ops.map(op => (
 <button
 key={op.id}
 onClick={() => navigate(`/operations/${op.id}`)}
 className="w-full text-left bg-white rounded-xl border border-slate-200 px-4 py-3 shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
 >
 <div className="flex items-start justify-between gap-2 mb-1">
 <p className="text-sm font-medium text-slate-800 leading-snug">
 {t(`events.${op.event_type}`, op.event_type)}
 </p>
 <Badge variant={statusToVariant(op.status)} size="sm">
 {t(`status.${op.status}`, op.status)}
 </Badge>
 </div>
 <div className="flex items-center gap-3 text-xs text-slate-500">
 {op.lot && <span>{op.lot.name}</span>}
 <span>{new Date(op.event_date).toLocaleDateString()}</span>
 </div>
 </button>
 ))}
 </div>
 </div>
 )
}
