import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../stores/auth.store'

const BIRD_TYPE_KEYS = ['grandparent', 'breeder', 'broiler'] as const

const STATUS_COLORS: Record<string, string> = {
 active: 'bg-emerald-100 text-emerald-800',
 closed: 'bg-slate-100 text-slate-600',
 cancelled: 'bg-red-100 text-red-800',
}

export default function LotListPage() {
 const { t } = useTranslation()
 const { user } = useAuthStore()
 const isWebUser = user?.view_type !== 'mobile'
 const [lots, setLots] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [birdType, setBirdType] = useState('')

 const fetchLots = useCallback(async () => {
 setLoading(true)
 try {
 const { data } = await api.get('/lots?limit=100')
 const filtered = birdType ? (data || []).filter((l: any) => l.bird_type === birdType) : (data || [])
 setLots(filtered)
 } catch (err) {
 console.error(err)
 } finally {
 setLoading(false)
 }
 }, [birdType])

 useEffect(() => { fetchLots() }, [fetchLots])

 const activeLots = lots.filter(l => l.status === 'active').length
 const closedLots = lots.filter(l => l.status === 'closed').length

 return (
 <div className="py-4 sm:py-6">
 <div className="flex items-center justify-between mb-6">
 <div>
 <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('lots.title')}</h1>
 <p className="text-sm text-slate-500 mt-1">
 {activeLots} {t('lots.activeCount')} · {closedLots} {t('lots.closedCount')}
 </p>
 </div>
 {isWebUser && (
 <Link to="/lots/new" className="bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5">
 <Plus size={16} /> {t('lots.newLot')}
 </Link>
 )}
 </div>

 {/* Stage quick filters */}
 <div className="flex flex-wrap gap-2 mb-4">
 <button onClick={() => setBirdType('')}
 className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${!birdType ? 'bg-[#1E3A5F] text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
 {t('common.all')}
 </button>
 {BIRD_TYPE_KEYS.map((key) => (
 <button key={key} onClick={() => setBirdType(birdType === key ? '' : key)}
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
 <p className="text-xs text-slate-400 mt-1">{t('lots.startPrefix')}{lot.start_date || '—'}</p>
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
 <td className="px-4 py-3 text-slate-500">{lot.start_date || '—'}</td>
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
 </div>
 )
}
