import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import api from '../../services/api'
import { formatFecha } from '../../utils/dates'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import { hasAnyUnits, hasUnit } from '../../auth/navigation'
import { useAuthStore } from '../../stores/auth.store'

/** `F3` · AC-S1-B01: las cuatro unidades productivas canónicas (`OD-16.a`). */
const BIRD_TYPE_KEYS = ['grandparent', 'breeder', 'broiler', 'hatchery'] as const

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
 // `QA-014`/`QA-018`: filtro por granja (servidor) y catálogo de granjas.
 const [farmId, setFarmId] = useState('')
 const [farms, setFarms] = useState<any[]>([])
 // `R-212` · AC-04.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

 // `F3` · AC-S1-B01: sólo se ofrecen las unidades de negocio disponibles en la sesión
 // (misma política que la navegación: `auth/navigation`).
 const unidadesDisponibles = BIRD_TYPE_KEYS.filter((key) => hasUnit(user, key))
 const hayUnidades = hasAnyUnits(user)
 const unidadesKey = unidadesDisponibles.join('|')
 // Un tipo persistido que ya no está disponible se ignora (y se limpia en el efecto de abajo).
 const tipoActivo = birdType && unidadesDisponibles.includes(birdType as any) ? birdType : ''

 // `F3` · AC-S1-I01: el tipo viaja al servidor, de modo que `X-Total-Count` y
 // «Cargar más» son coherentes con el filtro. Como defensa en profundidad se
 // vuelve a filtrar en cliente: si el backend devolviera lotes de otro tipo, la
 // lista pintada nunca contradice la pestaña activa (`AC10`).
 const lots = tipoActivo ? brutos.filter((l: any) => l.bird_type === tipoActivo) : brutos

 // `QA-018`/`F3`: los filtros viajan al servidor (`GET /lots?farm_id=&bird_type=`).
 const queryFiltros = `${farmId ? `&farm_id=${farmId}` : ''}${tipoActivo ? `&bird_type=${tipoActivo}` : ''}`

 const fetchLots = useCallback(async () => {
 // Sin unidades de negocio no hay alcance productivo: no se pide nada al servidor.
 if (!hayUnidades) {
 setBrutos([])
 setTotal(0)
 setEstado('ok')
 setLoading(false)
 return
 }
 setLoading(true)
 try {
 const r = await api.get(`/lots?limit=100&skip=0${queryFiltros}`)
 const data = r.data || []
 setBrutos(data)
 setTotal(Number(r.headers?.['x-total-count'] ?? data.length))
 setEstado('ok')
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setLoading(false)
 }
 }, [queryFiltros, hayUnidades])

 // `QA-018`: catálogo de granjas para el filtro.
 useEffect(() => {
 api.get('/masters/farms?limit=100').then(r => setFarms(r.data || [])).catch(() => {})
 }, [])

 // `R-220` · A8: trae la página siguiente y la acumula (total del backend).
 const cargarMas = async () => {
 setCargandoMas(true)
 try {
 const r = await api.get(`/lots?limit=100&skip=${brutos.length}${queryFiltros}`)
 setBrutos(prev => [...prev, ...(r.data || [])])
 setTotal(Number(r.headers?.['x-total-count'] ?? total))
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setCargandoMas(false)
 }
 }

 useEffect(() => { fetchLots() }, [fetchLots])

 // `F3` · AC-S1-B01: un tipo guardado que ya no está disponible se resetea a «Todos».
 useEffect(() => {
 if (birdType && !unidadesKey.split('|').includes(birdType)) setBirdType('')
 }, [birdType, unidadesKey])

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

 {/* Stage quick filters — sólo unidades disponibles (`F3` · AC-S1-B01). El botón
     «Todos» requiere al menos una unidad. */}
 {hayUnidades && (
 <div className="flex flex-wrap gap-2 mb-4">
 <button onClick={() => setBirdType('')} aria-pressed={!tipoActivo} data-testid="lot-filter-all"
 className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${!tipoActivo ? 'bg-[#1E3A5F] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
 {t('common.all')}
 </button>
 {unidadesDisponibles.map((key) => (
 <button key={key} onClick={() => setBirdType(tipoActivo === key ? '' : key)} aria-pressed={tipoActivo === key} data-testid={`lot-filter-${key}`}
 className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${tipoActivo === key ? 'bg-[#1E3A5F] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
 {t(`birdTypes.${key}`)}
 </button>
 ))}
 </div>
 )}

 {/* `QA-018`: filtro por granja (servidor). */}
 {hayUnidades && (
 <div className="flex flex-wrap gap-3 mb-4">
 <label className="flex items-center gap-2 text-sm text-slate-600">
 <span>{t('common.farm', 'Granja')}</span>
 <select
 value={farmId}
 onChange={e => setFarmId(e.target.value)}
 data-testid="lot-filter-farm"
 className="h-10 px-3 border border-slate-300 rounded-lg text-sm max-w-[220px]"
 >
 <option value="">{t('common.allFarms', 'Todas las granjas')}</option>
 {farms.map((f: any) => (
 <option key={f.id} value={f.id}>{f.name}</option>
 ))}
 </select>
 </label>
 </div>
 )}

 {/* `F3` · AC-S1-B01: sin unidades de negocio no hay alcance productivo. */}
 {!hayUnidades && (
 <div data-testid="lots-no-units" className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
 <h2 className="text-lg font-semibold text-[#1E3A5F]">{t('lots.noUnitsTitle')}</h2>
 <p className="text-sm text-slate-500 mt-2">{t('lots.noUnitsHint')}</p>
 </div>
 )}

 {hayUnidades && (
 <>
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
 <p className="text-sm text-slate-600">{t('common.farm', 'Granja')}: {lot.farm_name ?? '—'}</p>
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
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.farm', 'Granja')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.type')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.status')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.start')}</th>
 <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('lots.actions')}</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100">
 {loading && <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">{t('common.loading')}</td></tr>}
 {!loading && lots.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">{t('lots.noLots')}</td></tr>}
 {lots.map((lot: any) => (
 <tr key={lot.id} className="hover:bg-slate-50 transition">
 <td className="px-4 py-3 font-mono font-medium text-[#1E3A5F]">{lot.lot_code || `L-${lot.id}`}</td>
 <td className="px-4 py-3 text-slate-600">{lot.farm_name ?? '—'}</td>
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
 </>
 )}
 </div>
 )
}
