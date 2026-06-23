import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Activity } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600', registered: 'bg-blue-100 text-blue-800',
  pending_review: 'bg-amber-100 text-amber-800', in_review: 'bg-indigo-100 text-indigo-800',
  returned: 'bg-orange-100 text-orange-800', corrected: 'bg-teal-100 text-teal-800',
  approved: 'bg-emerald-100 text-emerald-800', rejected: 'bg-red-100 text-red-800',
  consolidated: 'bg-purple-100 text-purple-800', sent_to_sap: 'bg-cyan-100 text-cyan-800',
  sap_confirmed: 'bg-green-100 text-green-800',
}

export default function OperationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [event, setEvent] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()
  useEffect(() => {
    api.get('/operations?limit=200').then(({ data }) => {
      const found = (data as any[]).find((e: any) => e.id === Number(id))
      setEvent(found || null)
    }).catch((e: any) => {
      const msg = getErrorMessage(e, 'Error al cargar operación')
      setError(msg)
      toast.error(msg)
    }).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="p-6 text-slate-500">Cargando...</div>
  if (error) return <div className="p-6 text-red-600 bg-red-50 rounded-lg">{error}</div>
  if (!event) return <div className="p-6 text-slate-500">Evento no encontrado</div>

  return (
    <div className="p-4 sm:p-6 max-w-3xl mx-auto">
      <Link to="/operations" className="text-slate-400 hover:text-slate-600 flex items-center gap-1 mb-4"><ArrowLeft size={16} /> Volver</Link>
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-[#1E3A5F]">Evento #{event.id}</h1>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>{event.status}</span>
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-slate-500">Tipo</dt><dd className="font-medium">{event.event_type}</dd></div>
          <div><dt className="text-slate-500">Fecha</dt><dd>{event.event_date}</dd></div>
          <div><dt className="text-slate-500">Lote</dt><dd className="font-mono">#{event.lot_id}</dd></div>
          <div><dt className="text-slate-500">Versión</dt><dd>v{event.version}</dd></div>
          <div className="col-span-2"><dt className="text-slate-500">Observaciones</dt><dd>{event.observations || '—'}</dd></div>
          {event.sap_document_ref && <div className="col-span-2"><dt className="text-slate-500">Ref. SAP</dt><dd className="font-mono">{event.sap_document_ref}</dd></div>}
        </dl>

        {event.bird_movements?.length > 0 && (
          <div className="mt-4 pt-4 border-t"><h3 className="font-semibold text-sm text-slate-600 mb-2 flex items-center gap-1"><Activity size={14} /> Movimientos de Aves</h3>
            {event.bird_movements.map((bm: any, i: number) => <div key={i} className="text-xs text-slate-600">{bm.quantity} aves {bm.sex || ''} {bm.avg_weight ? `· ${bm.avg_weight}g` : ''}</div>)}
          </div>
        )}
        {event.feed_movements?.length > 0 && (
          <div className="mt-4 pt-4 border-t"><h3 className="font-semibold text-sm text-slate-600 mb-2">Alimento</h3>
            {event.feed_movements.map((fm: any, i: number) => <div key={i} className="text-xs text-slate-600">{fm.quantity_kg} kg</div>)}
          </div>
        )}
        {event.egg_movements?.length > 0 && (
          <div className="mt-4 pt-4 border-t"><h3 className="font-semibold text-sm text-slate-600 mb-2">Huevos</h3>
            {event.egg_movements.map((em: any, i: number) => <div key={i} className="text-xs text-slate-600">{em.quantity} · {em.egg_type}</div>)}
          </div>
        )}
      </div>
    </div>
  )
}
