import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import api from '../../services/api'
import { formatFecha } from '../../utils/dates'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import { useAuthStore } from '../../stores/auth.store'

const BIRD_TYPE_KEYS = ['grandparent', 'breeder', 'broiler'] as const

const STATUS_COLORS: Record<string, string> = {
 active: 'bg-emerald-100 text-emerald-800',
 closed: 'bg-slate-100 text-slate-600',
 cancelled: 'bg-red-100 text-red-800',
}

export default function LotListPage() {
 const can = useCan()
 const { t } = useTranslation()
 const { user } = useAuthStore()
 const isWebUser = user?.view_type !== 'mobile'
 const [brutos, setBrutos] = useState<any[]>([])
 const [total, setTotal] = useState(0)
 const [cargandoMas, setCargandoMas] = useState(false)
 const [loading, setLoading] = useState(true)
 const [birdType, setBirdType] = useState(() => {
 // `004` · AC10: el filtro de listado sobrevive al ciclo lista→detalle→atrás
 // (mecanismo existente del repo: sessionStorage; no se introduce uno nuevo).
 try { return sessionStorage.getItem('ga.filters.lots.birdType') ?? '' } catch { return '' }
 })
 // `R-212` · AC-04.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

 // `R-220` · A8 (C#33): el filtro por tipo es de cliente; la paginación no.
 const lots = birdType ? brutos.filter((l: any) => l.bird_type === birdType) : brutos

 const fetchLots = useCallback(async () => {
 setLoading(true)
 try {
 const r = await api.get('/lots?limit=100&skip=0')
 const data = r.data || []
 setBrutos(data)
 setTotal(Number(r.headers?.['x-total-count'] ?? data.length))
 setEstado('ok')
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setLoading(false)
 }
 }, [])

 // `R-220` · A8: trae la página siguiente y la acumula (total del backend).
 const cargarMas = async () => {
 setCargandoMas(true)
 try {
 const r = await api.get(`/lots?limit=100&skip=${brutos.length}`)
 setBrutos(prev => [...prev, ...(r.data || [])])
 setTotal(Number(r.headers?.['x-total-count'] ?? total))
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setCargandoMas(false)
 }
 }

 useEffect(() => { fetchLots() }, [fetchLots])

 // `004` · AC10: persistir el filtro para el retorno lista→detalle→lista.
 useEffect(() => {
 try {
 if (birdType) sessionStorage.setItem('ga.filters.lots.birdType', birdType)
 else sessionStorage.removeItem('ga.filters.lots.birdType')
 } catch { /* storage no disponible */ }
 }, [birdType])

 const activeLots = lots.filter(l => l.status === 'active').length
 const closedLots = lots.filter(l => l.status === 'closed').length

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={fetchLots} />
 </div>
 )
 }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex items-center justify-between mb-6">
 <div>
 <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('lots.title')}</h1>
 <p className="text-sm text-slate-500 mt-1">
 {activeLots} {t('lots.activeCount')} · {closedLots} {t('lots.closedCount')}
 </p>
 </div>
 {isWebUser && can({ permission: 'lots:create' }) && (
 <Link to="/lots/new" className="bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5">
 <Plus size={16} /> {t('lots.newLot')}
 </Link>
 )}
 </div>

 {/* Stage quick filters */}
 <div className="flex flex-wrap gap-2 mb-4">
 <button onClick={() => setBirdType('')} aria-pressed={!birdType} data-testid="lot-filter-all"
 className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${!birdType ? 'bg-[#1E3A5F] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
 {t('common.all')}
 </button>
 {BIRD_TYPE_KEYS.map((key) => (
 <button key={key} onClick={() => setBirdType(birdType === key ? '' : key)} aria-pressed={birdType === key} data-testid={`lot-filter-${key}`}
 className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${birdType === key ? 'bg-[#1E3A5F] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
 {t(`birdTypes.${key}`)}
 </button>
 ))}
 </div>

 {/* Mobile Cards */}
 <div className="lg:hidden space-y-3">
 {loading && <p className="text-slate-500 text-center py-8">{t('common.loading')}</p>}
 {!loading && lots.length === 0 && <p className="text-slate-500 text-center py-8">{t('lots.noLots')}</p>}
 {lots.map((lot: any) => (
 <Link key={lot.id} to={`/lots/${lot.id}`}
 className="block bg-white rounded-xl shadow-sm border border-slate-200 p-4 hover:border-[#5a9bba] transition">
 <div className="flex items-center justify-between mb-2">
 <span className="font-mono font-semibold text-[#1E3A5F]">{lot.lot_code || `L-${lot.id}`}</span>
 <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[lot.status] || 'bg-slate-100'}`}>
 {t(`lotStatus.${lot.status}`, String(lot.status))}
 </span>
 </div>
 <p className="text-sm text-slate-600">{t(`birdTypes.${lot.bird_type}`, String(lot.bird_type || t('lots.noType')))}</p>
 <p className="text-xs text-slate-400 mt-1">{t('lots.startPrefix')}{formatFecha(lot.start_date)}</p>
 </Link>
 ))}
 </div>

 {/* Desktop Table */}
 <div className="hidden lg:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
 <table className="w-full text-sm">
 <thead className="bg-slate-50 border-b border-slate-200">
 <tr>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.code')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.type')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.status')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.start')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.actions')}</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100">
 {loading && <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">{t('common.loading')}</td></tr>}
 {!loading && lots.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">{t('lots.noLots')}</td></tr>}
 {lots.map((lot: any) => (
 <tr key={lot.id} className="hover:bg-slate-50 transition">
 <td className="px-4 py-3 font-mono font-medium text-[#1E3A5F]">{lot.lot_code || `L-${lot.id}`}</td>
 <td className="px-4 py-3">{t(`birdTypes.${lot.bird_type}`, String(lot.bird_type || '—'))}</td>
 <td className="px-4 py-3">
 <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[lot.status] || 'bg-slate-100'}`}>
 {t(`lotStatus.${lot.status}`, String(lot.status))}
 </span>
 </td>
 <td className="px-4 py-3 text-slate-500">{formatFecha(lot.start_date)}</td>
 <td className="px-4 py-3">
 <Link to={`/lots/${lot.id}`}
 className="bg-[#1E3A5F] text-white px-3 py-1 rounded text-xs font-medium hover:bg-blue-800 transition">
 {t('lots.viewDetail')}
 </Link>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {/* `R-220` · A8: paginación real — el total viene del backend (`X-Total-Count`). */}
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
