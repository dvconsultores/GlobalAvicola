/**
 * TraceabilityTree — Árbol de trazabilidad generacional para un lote
 * Cadena completa: PROGENITORAS → INCUBADORA → REPRODUCTORAS → INCUBADORA → ENGORDE
 * Consume GET /lots/{id}/traceability
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Egg, Baby, ArrowRight, RefreshCw } from 'lucide-react'
import api from '../services/api'
import { Badge, statusToVariant } from './ui'
import { Button, Input, Modal } from './ui'

interface LotRef {
  id: number
  lot_code: string
  bird_type?: string
  status: string
}

interface EggBatch {
  id: number
  source_lot_id: number
  hatchery_lot_id?: number
  quantity_dispatched: number
  quantity_received?: number
  dispatch_date: string
  source_lot?: LotRef
  hatchery_lot?: LotRef
}

interface ChickBatch {
  id: number
  hatchery_lot_id: number
  destination_lot_id?: number
  broiler_lot_id?: number
  quantity_dispatched: number
  quantity_received?: number
  dispatch_date: string
  hatchery_lot?: LotRef
  destination_lot?: LotRef
  broiler_lot?: LotRef
}

interface TraceabilityNode {
  lot: LotRef
  egg_batches_sent: EggBatch[]
  egg_batches_received: EggBatch[]
  chick_batches_sent: ChickBatch[]
  chick_batches_received: ChickBatch[]
}

interface Props { lotId: number | string; birdType?: string }

function LotChip({ lot }: { lot: LotRef }) {
  return (
    <Link
      to={`/lots/${lot.id}`}
      className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#1E3A5F]/5 border border-[#1E3A5F]/20 text-[#1E3A5F] text-xs font-mono font-semibold hover:bg-[#1E3A5F]/10 transition-colors"
    >
      {lot.lot_code}
      <Badge variant={statusToVariant(lot.status)} size="sm">{lot.status}</Badge>
    </Link>
  )
}

export function TraceabilityTree({ lotId, birdType }: Props) {
  const { t } = useTranslation()
  const [data, setData] = useState<TraceabilityNode | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // F-02: Link creation state
  const [showEggLink, setShowEggLink] = useState(false)
  const [showChickLink, setShowChickLink] = useState(false)
  const [linking, setLinking] = useState(false)
  const [linkError, setLinkError] = useState('')
  const today = new Date().toISOString().split('T')[0]
  const [eggForm, setEggForm] = useState({ hatcheryLotId: '', quantity: '', date: today })
  const [chickForm, setChickForm] = useState({ destinationLotId: '', quantity: '', date: today })

  const handleCreateEggBatch = async () => {
    setLinking(true)
    setLinkError('')
    try {
      await api.post('/lots/egg-batches', {
        source_lot_id: Number(lotId),
        hatchery_lot_id: Number(eggForm.hatcheryLotId) || null,
        quantity_dispatched: Number(eggForm.quantity),
        dispatch_date: eggForm.date,
      })
      setShowEggLink(false)
      load()
    } catch (err: any) {
      setLinkError(err?.response?.data?.detail ?? t('errors.saveFailed', 'Error al guardar'))
    } finally {
      setLinking(false)
    }
  }

  const handleCreateChickBatch = async () => {
    setLinking(true)
    setLinkError('')
    try {
      await api.post('/lots/chick-batches', {
        hatchery_lot_id: Number(lotId),
        destination_lot_id: Number(chickForm.destinationLotId) || null,
        quantity_dispatched: Number(chickForm.quantity),
        dispatch_date: chickForm.date,
      })
      setShowChickLink(false)
      load()
    } catch (err: any) {
      setLinkError(err?.response?.data?.detail ?? t('errors.saveFailed', 'Error al guardar'))
    } finally {
      setLinking(false)
    }
  }

  const load = async () => {
    setLoading(true)
    setError(false)
    try {
      const { data: d } = await api.get(`/lots/${lotId}/traceability`)
      setData(d)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [lotId])

  const hasData = data && (
    data.egg_batches_sent.length > 0 ||
    data.egg_batches_received.length > 0 ||
    data.chick_batches_sent.length > 0 ||
    data.chick_batches_received.length > 0
  )

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-slate-100 dark:bg-slate-700 rounded w-1/3 mb-3" />
        <div className="h-16 bg-slate-100 dark:bg-slate-700 rounded" />
      </div>
    )
  }

  if (error) {
    return (
      <p className="text-xs text-slate-400 dark:text-slate-400 dark:text-slate-400 flex items-center gap-1">
        {t('traceability.loadError', 'Error al cargar trazabilidad')}
        <button onClick={load} className="text-blue-500 hover:underline ml-1">{t('common.retry', 'Reintentar')}</button>
      </p>
    )
  }

  if (!hasData) {
    return (
      <p className="text-sm text-slate-400 dark:text-slate-400 dark:text-slate-400 italic">
        {t('traceability.noLinks', 'Sin vínculos de trazabilidad generacional registrados.')}
      </p>
    )
  }

  return (
    <div className="space-y-5">
      {/* Eggs sent upstream (Breeder → Hatchery) */}
      {data!.egg_batches_sent.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Egg size={13} />
            {t('traceability.eggsSent', 'Huevos enviados a incubadora')}
          </h4>
          <div className="space-y-2">
            {data!.egg_batches_sent.map(b => (
              <div key={b.id} className="flex items-center gap-2 text-sm">
                <span className="text-slate-500 dark:text-slate-400">{new Date(b.dispatch_date).toLocaleDateString()}</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">{b.quantity_dispatched.toLocaleString()}</span>
                <span className="text-slate-400 dark:text-slate-400 dark:text-slate-400">{t('traceability.eggs', 'huevos')}</span>
                {b.quantity_received != null && (
                  <span className="text-xs text-slate-400 dark:text-slate-400 dark:text-slate-400">({t('traceability.received', 'recibidos')}: {b.quantity_received.toLocaleString()})</span>
                )}
                {b.hatchery_lot && (
                  <>
                    <ArrowRight size={13} className="text-slate-300 dark:text-slate-400 shrink-0" />
                    <LotChip lot={b.hatchery_lot} />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Eggs received (Hatchery ← Breeder) */}
      {data!.egg_batches_received.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Egg size={13} />
            {t('traceability.eggsReceived', 'Huevos recibidos de reproductoras')}
          </h4>
          <div className="space-y-2">
            {data!.egg_batches_received.map(b => (
              <div key={b.id} className="flex items-center gap-2 text-sm">
                {b.source_lot && (
                  <>
                    <LotChip lot={b.source_lot} />
                    <ArrowRight size={13} className="text-slate-300 dark:text-slate-400 shrink-0" />
                  </>
                )}
                <span className="text-slate-500 dark:text-slate-400">{new Date(b.dispatch_date).toLocaleDateString()}</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">{b.quantity_dispatched.toLocaleString()}</span>
                <span className="text-slate-400 dark:text-slate-400 dark:text-slate-400">{t('traceability.eggs', 'huevos')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chicks dispatched (Hatchery → Broiler) */}
      {data!.chick_batches_sent.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Baby size={13} />
            {t('traceability.chicksSent', 'Pollitos enviados a engorde')}
          </h4>
          <div className="space-y-2">
            {data!.chick_batches_sent.map(b => (
              <div key={b.id} className="flex items-center gap-2 text-sm">
                <span className="text-slate-500 dark:text-slate-400">{new Date(b.dispatch_date).toLocaleDateString()}</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">{b.quantity_dispatched.toLocaleString()}</span>
                <span className="text-slate-400 dark:text-slate-400 dark:text-slate-400">{t('traceability.chicks', 'pollitos')}</span>
                {b.quantity_received != null && (
                  <span className="text-xs text-slate-400 dark:text-slate-400 dark:text-slate-400">({t('traceability.received', 'recibidos')}: {b.quantity_received.toLocaleString()})</span>
                )}
                {(b.destination_lot || b.broiler_lot) && (
                  <>
                    <ArrowRight size={13} className="text-slate-300 dark:text-slate-400 shrink-0" />
                    <LotChip lot={b.destination_lot || b.broiler_lot!} />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chicks received (Broiler ← Hatchery) */}
      {data!.chick_batches_received.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Baby size={13} />
            {t('traceability.chicksReceived', 'Pollitos recibidos de incubadora')}
          </h4>
          <div className="space-y-2">
            {data!.chick_batches_received.map(b => (
              <div key={b.id} className="flex items-center gap-2 text-sm">
                {b.hatchery_lot && (
                  <>
                    <LotChip lot={b.hatchery_lot} />
                    <ArrowRight size={13} className="text-slate-300 dark:text-slate-400 shrink-0" />
                  </>
                )}
                <span className="text-slate-500 dark:text-slate-400">{new Date(b.dispatch_date).toLocaleDateString()}</span>
                <span className="font-semibold text-slate-700 dark:text-slate-200">{b.quantity_dispatched.toLocaleString()}</span>
                <span className="text-slate-400 dark:text-slate-400 dark:text-slate-400">{t('traceability.chicks', 'pollitos')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={load}
        disabled={loading}
        className="text-xs text-slate-400 dark:text-slate-400 dark:text-slate-400 hover:text-slate-600 dark:text-slate-300 dark:text-slate-400 dark:text-slate-300 dark:text-slate-400 flex items-center gap-1 transition-colors"
      >
        <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
        {t('common.refresh', 'Actualizar')}
      </button>

      {/* F-02: Link creation buttons */}
      <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
        {(birdType === 'breeder' || birdType === 'grandparent') && (
          <Button
            size="sm"
            variant="outline"
            leftIcon={<Egg size={12} />}
            onClick={() => setShowEggLink(true)}
          >
            {t('traceability.linkEggs', 'Vincular huevos a incubadora')}
          </Button>
        )}
        {birdType === 'hatchery' && (
          <Button
            size="sm"
            variant="outline"
            leftIcon={<Baby size={12} />}
            onClick={() => setShowChickLink(true)}
          >
            {t('traceability.linkChicks', 'Vincular pollitos a engorde')}
          </Button>
        )}
      </div>

      {/* Egg batch creation modal */}
      <Modal
        open={showEggLink}
        onClose={() => setShowEggLink(false)}
        title={t('traceability.createEggBatch', 'Vincular huevos a incubadora')}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEggLink(false)}>
              {t('common.cancel', 'Cancelar')}
            </Button>
            <Button onClick={handleCreateEggBatch} loading={linking}>
              {t('common.save', 'Guardar')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('traceability.hatcheryLotId', 'Lote de incubadora destino')}
            type="number"
            min={1}
            placeholder="ID del lote HATCHERY"
            value={eggForm.hatcheryLotId}
            onChange={e => setEggForm(prev => ({ ...prev, hatcheryLotId: e.target.value }))}
          />
          <Input
            label={t('traceability.quantity', 'Cantidad de huevos')}
            type="number"
            min={1}
            value={eggForm.quantity}
            onChange={e => setEggForm(prev => ({ ...prev, quantity: e.target.value }))}
          />
          <Input
            label={t('traceability.dispatchDate', 'Fecha de despacho')}
            type="date"
            value={eggForm.date}
            onChange={e => setEggForm(prev => ({ ...prev, date: e.target.value }))}
          />
          {linkError && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{linkError}</p>}
        </div>
      </Modal>

      {/* Chick batch creation modal */}
      <Modal
        open={showChickLink}
        onClose={() => setShowChickLink(false)}
        title={t('traceability.createChickBatch', 'Vincular pollitos a engorde')}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowChickLink(false)}>
              {t('common.cancel', 'Cancelar')}
            </Button>
            <Button onClick={handleCreateChickBatch} loading={linking}>
              {t('common.save', 'Guardar')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('traceability.destinationLotId', 'Lote destino (reproductoras o engorde)')}
            type="number"
            min={1}
            placeholder="ID del lote destino"
            value={chickForm.destinationLotId}
            onChange={e => setChickForm(prev => ({ ...prev, destinationLotId: e.target.value }))}
          />
          <Input
            label={t('traceability.quantity', 'Cantidad de pollitos')}
            type="number"
            min={1}
            value={chickForm.quantity}
            onChange={e => setChickForm(prev => ({ ...prev, quantity: e.target.value }))}
          />
          <Input
            label={t('traceability.dispatchDate', 'Fecha de despacho')}
            type="date"
            value={chickForm.date}
            onChange={e => setChickForm(prev => ({ ...prev, date: e.target.value }))}
          />
          {linkError && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{linkError}</p>}
        </div>
      </Modal>
    </div>
  )
}
