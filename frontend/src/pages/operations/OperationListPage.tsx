import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ClipboardList } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { formatFecha, formatFechaHora } from '../../utils/dates'
import { PROCESS_STAGES, flowForStage, type StageKey } from '../../data/processCatalog'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

// `SPEC 020` (AC-S2-U01): «Se creará al aprobar» describe SÓLO la importación de
// abuelos (la única que crea lote al aprobar). Cualquier otro evento sin lote es de
// nivel granja — nunca «#null».
const lotCellLabel = (ev: any, t: any): string => {
 if (ev.lot_code) return ev.lot_code
 if (ev.lot_id) return `#${ev.lot_id}`
 return ev.event_type === 'grandparent_import'
 ? t('operations.lotAutoPending', 'Se creará al aprobar')
 : t('operations.noLotFarmLevel', 'Sin lote (nivel granja)')
}

const STATUS_COLORS: Record<string, string> = {
 registered: 'bg-blue-100 text-blue-800', pending_review: 'bg-yellow-100 text-yellow-800',
 approved: 'bg-green-100 text-green-800', rejected: 'bg-red-100 text-red-800',
 cancelled: 'bg-slate-100 text-slate-600',
 reversed: 'bg-rose-100 text-rose-800',
}

export default function OperationListPage() {
 const { t } = useTranslation()
 const [brutos, setBrutos] = useState<any[]>([])
 const [total, setTotal] = useState(0)
 const [cargandoMas, setCargandoMas] = useState(false)
 const [loading, setLoading] = useState(true)
 // `R-212` · AC-04: denegación ≠ vacío.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 // `F4` (AC-S1-F01): el filtro de lote es por CÓDIGO legible (`lot_code`, el backend
 // ya lo acepta con coincidencia parcial) y espera 400 ms antes de pedir.
 const [lotCode, setLotCode] = useState(() => {
 // `004` · AC10: filtros preservados al volver (mismo mecanismo sessionStorage del repo).
 try { return sessionStorage.getItem('ga.filters.operations.lotCode') ?? '' } catch { return '' }
 })
 const lotCodeDebounced = useDebouncedValue(lotCode.trim(), 400)
 const [eventType, setEventType] = useState(() => {
 try { return sessionStorage.getItem('ga.filters.operations.eventType') ?? '' } catch { return '' }
 })
 // `QA-015`/`QA-014`: filtro por granja (servidor) y catálogo de granjas.
 const [farmId, setFarmId] = useState(() => {
 try { return sessionStorage.getItem('ga.filters.operations.farmId') ?? '' } catch { return '' }
 })
 const [farms, setFarms] = useState<any[]>([])

 const fetchEvents = useCallback(async () => {
 setLoading(true)
 try {
 const params: any = { limit: 100, skip: 0 }
 if (lotCodeDebounced) params.lot_code = lotCodeDebounced
 if (farmId) params.farm_id = farmId
 // For stage-based filter: fetch all and filter client-side
 // (backend doesn't support multi event_type yet)
 if (eventType && !eventType.startsWith('__stage__')) {
 params.event_type = eventType
 }
 const r = await api.get('/operations', { params })
 setBrutos(r.data ?? [])
 setTotal(Number(r.headers?.['x-total-count'] ?? (r.data ?? []).length))
 setEstado('ok')
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 }
 finally { setLoading(false) }
 }, [lotCodeDebounced, eventType, farmId])

 // `QA-015`: catálogo de granjas para el filtro (mismo patrón que Lotes).
 useEffect(() => {
 api.get('/masters/farms?limit=100').then(r => setFarms(r.data || [])).catch(() => {})
 }, [])

 // `R-220` · A8 (C#33): página siguiente acumulada (skip por lo ya cargado).
 const cargarMas = async () => {
 setCargandoMas(true)
 try {
 const params: any = { limit: 100, skip: brutos.length }
 if (lotCodeDebounced) params.lot_code = lotCodeDebounced
 if (farmId) params.farm_id = farmId
 if (eventType && !eventType.startsWith('__stage__')) params.event_type = eventType
 const r = await api.get('/operations', { params })
 setBrutos(prev => [...prev, ...(r.data ?? [])])
 setTotal(Number(r.headers?.['x-total-count'] ?? total))
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally { setCargandoMas(false) }
 }

 // El filtro por etapa es de cliente; la paginación no (`R-220` · A8).
 const events = (eventType && eventType.startsWith('__stage__'))
 ? brutos.filter((ev: any) => flowForStage(eventType.replace('__stage__', '') as StageKey).map(s => s.event).includes(ev.event_type))
 : brutos

 useEffect(() => { fetchEvents() }, [fetchEvents])

 // `004` · AC10: persistir filtros para el retorno lista→detalle→lista.
 useEffect(() => {
 try {
 if (lotCode) sessionStorage.setItem('ga.filters.operations.lotCode', lotCode)
 else sessionStorage.removeItem('ga.filters.operations.lotCode')
 if (eventType) sessionStorage.setItem('ga.filters.operations.eventType', eventType)
 else sessionStorage.removeItem('ga.filters.operations.eventType')
 if (farmId) sessionStorage.setItem('ga.filters.operations.farmId', farmId)
 else sessionStorage.removeItem('ga.filters.operations.farmId')
 } catch { /* storage no disponible */ }
 }, [lotCode, eventType, farmId])

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={fetchEvents} />
 </div>
 )
 }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
 <div>
 <h1 className="text-2xl font-bold text-slate-800">{t('nav.operations')}</h1>
 <p className="text-sm text-slate-500">{events.length} {t('common.results')}</p>
 </div>
 <div className="flex items-center gap-3">
 {/* `spec 015 §5` · `AC-S1-T02`: acceso a la bandeja de pendientes de clasificar. */}
 <Link to="/operations/pending-classification" data-testid="pending-classification-link" className="inline-flex items-center h-10 px-4 border border-slate-300 text-slate-600 hover:bg-slate-50 text-sm font-medium rounded-lg transition">
 {t('operations.pendingClassification.link', 'Pendientes de clasificar')}
 </Link>
 <Link to="/menu/poultry" className="inline-flex items-center h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition">
 + {t('common.create')}
 </Link>
 </div>
 </div>

 {/* Filters — stage-based instead of old 24-event flat dropdown */}
 <div className="flex gap-3 mb-4 flex-wrap">
 <input type="text" maxLength={50} data-testid="operation-filter-lot-code" aria-label={t('operations.lotCodeFilter', 'Código de lote')} placeholder={t('operations.lotCodeFilter', 'Código de lote')} value={lotCode} onChange={e => setLotCode(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm w-40" />
 <select value={eventType} onChange={e => setEventType(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm max-w-[200px]">
 <option value="">{t('common.allTypes')}</option>
 <optgroup label={t('operations.stagesGroup', 'Etapas de producción')}>
 {PROCESS_STAGES.map(s => (
 <option key={s.key} value={`__stage__${s.key}`}>
 {t(s.labelKey, s.fallback)}
 </option>
 ))}
 </optgroup>
 </select>
 <select value={farmId} onChange={e => setFarmId(e.target.value)} data-testid="operation-filter-farm" aria-label={t('common.farm', 'Granja')} className="h-10 px-3 border border-slate-300 rounded-lg text-sm max-w-[220px]">
 <option value="">{t('common.allFarms', 'Todas las granjas')}</option>
 {farms.map((f: any) => (
 <option key={f.id} value={f.id}>{f.name}</option>
 ))}
 </select>
 </div>

 {/* Event list (mobile: tarjetas · desktop: columnas) */}
 {loading ? <p className="text-slate-500 text-sm py-8 text-center">{t('common.loading')}</p>
 : events.length === 0 ? <p className="text-slate-400 text-sm py-8 text-center">{t('common.noResults')}</p>
 : <div className="bg-white rounded-xl shadow-sm border border-slate-200 divide-y divide-slate-100">
 {/* `QA-014`/`QA-018`: encabezado de columnas (solo desktop). */}
 <div className="hidden lg:grid lg:grid-cols-7 lg:gap-3 px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-600">
 <span>{t('common.lotCode', 'Lote')}</span>
 <span>{t('common.farm', 'Granja')}</span>
 <span>{t('operations.recordType', 'Tipo de registro')}</span>
 <span>{t('common.eventDate', 'Fecha del evento')}</span>
 <span>{t('common.registeredBy', 'Registrado por')}</span>
 <span>{t('common.registeredAt', 'Fecha de registro')}</span>
 <span>{t('common.status', 'Estado')}</span>
 </div>
 {events.map((ev: any) => (
 <div key={ev.id} data-testid={`operation-row-${ev.id}`} className="px-4 py-3 lg:grid lg:grid-cols-7 lg:gap-3 lg:items-center">
 <div className="flex items-center gap-2 mb-1 lg:mb-0">
 <ClipboardList size={20} className="text-slate-400 shrink-0" aria-hidden="true" />
 <span className="text-sm font-mono font-medium text-slate-700">{lotCellLabel(ev, t)}</span>
 </div>
 <span className="block text-sm text-slate-600">{ev.farm_name ?? '—'}</span>
 <span className="block text-sm font-medium text-slate-700">{getEventLabel(t, ev.event_type)}</span>
 <span className="block text-xs text-slate-500">{formatFecha(ev.event_date)}</span>
 <span className="block text-sm text-slate-600">{ev.registered_by_name ?? '—'}</span>
 <span className="block text-xs text-slate-500">{formatFechaHora(ev.created_at)}</span>
 <div className="flex items-center justify-between gap-2 mt-2 lg:mt-0">
 <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[ev.status] || 'bg-slate-100 text-slate-600'}`}>{t(`status.${ev.status}`)}</span>
 <Link to={`/operations/${ev.id}`} className="text-blue-600 text-sm hover:underline">{t('common.viewDetail', 'Ver detalle')}</Link>
 </div>
 </div>
 ))}
 </div>
 }
 {/* `R-220` · A8: paginación real con `X-Total-Count`. */}
 {!loading && brutos.length < total && (
 <div className="flex justify-center py-4">
 <button
 type="button"
 onClick={cargarMas}
 disabled={cargandoMas}
 className="px-4 py-2 rounded-lg text-sm font-semibold border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
 >
 {cargandoMas ? t('common.loading') : t('common.loadMore', 'Cargar más')}
 </button>
 </div>
 )}
 </div>
 )
}
