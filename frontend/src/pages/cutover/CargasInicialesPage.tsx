/**
 * GA-REQ-061 · T14 · C8 — «Cargas Iniciales» (cutover operacional).
 *
 * Flujo AC80-85: nuevo batch (empresa/BU/corte) → subir plantilla → errores de
 * validación (fila/campo/código) → preview → enviar → aprobar/rechazar → aplicar
 * solo sin errores pendientes → reconciliación Opening/Post/Lifetime.
 *
 * Reglas duras de esta superficie:
 *   - El estado del batch SIEMPRE visible (AC82).
 *   - «Aplicar» jamás accionable con filas inválidas/pendientes (AC81) — y el
 *     backend sigue siendo la autoridad: aquí solo se evita el gesto inútil.
 *   - UNKNOWN se muestra tal cual (`null` nunca se pinta como 0 — AC77).
 *   - Todo texto sale de i18n (AC84/85); responsive con el patrón existente.
 */
import { useCallback, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Upload, Send, CheckCircle2, XCircle, PlayCircle, RefreshCw, Layers } from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
import { hasPermission } from '../../auth/permissions'
import { Badge, Button, Card, CardBody, EmptyState } from '../../components/ui'
import type { StatusKey } from '../../data/statusColors'
import { useToast, getErrorMessage } from '../../components/Toast'
import SubNavHeader from '../../components/layout/SubNavHeader'
import {
  cutoverService,
  type BusinessUnitCode,
  type CutoverBatch,
  type CutoverItem,
  type CutoverReconciliation,
  type CutoverReconciliationLot,
  type CutoverValidation,
} from '../../services/cutover.service'

const STATUS_VARIANT: Record<string, StatusKey> = {
  draft: 'draft',
  validating: 'pending',
  validated: 'info',
  pending_approval: 'pending_review',
  approved: 'approved',
  applied: 'consolidated',
  rejected: 'rejected',
}

/** AC77: un `null` es UNKNOWN — jamás se pinta como 0. */
function Metric({ value }: { value: number | null | undefined }) {
  const { t } = useTranslation()
  if (value === null || value === undefined) {
    return (
      <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" aria-hidden />
        {t('cutover.unknown', 'UNKNOWN')}
      </span>
    )
  }
  return <span className="tabular-nums">{value.toLocaleString()}</span>
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation()
  return (
    <Badge variant={STATUS_VARIANT[status] || 'neutral'}>
      {t(`cutover.status.${status}`, status)}
    </Badge>
  )
}

export default function CargasInicialesPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const sessionUser = useAuthStore(s => s.user)

  const canCreate = hasPermission(sessionUser, 'cutover:create')
  const canValidate = hasPermission(sessionUser, 'cutover:validate')
  const canSubmit = hasPermission(sessionUser, 'cutover:submit')
  const canApprove = hasPermission(sessionUser, 'cutover:approve')
  const canApply = hasPermission(sessionUser, 'cutover:apply')

  const [businessUnit, setBusinessUnit] = useState<BusinessUnitCode>('broiler')
  const [cutoverDatetime, setCutoverDatetime] = useState('')
  const [batch, setBatch] = useState<CutoverBatch | null>(null)
  const [validation, setValidation] = useState<CutoverValidation | null>(null)
  const [items, setItems] = useState<CutoverItem[]>([])
  const [reconciliation, setReconciliation] = useState<CutoverReconciliation | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const busyRef = useRef(false)

  const aplicable =
    batch?.status === 'approved' && (batch?.invalid_rows ?? 1) === 0 &&
    (validation?.errors?.length ?? 1) === 0

  const refrescar = useCallback(async (b: CutoverBatch) => {
    setBatch(b)
    const v = await cutoverService.validation(b.id)
    setValidation(v.data)
    const its = await cutoverService.items(b.id)
    setItems(its.data.items || [])
    if (b.status === 'applied') {
      try {
        const rec = await cutoverService.reconciliation(b.id)
        setReconciliation(rec.data)
      } catch {
        setReconciliation(null) // la reconciliación no debe tumbar la pantalla
      }
    } else {
      setReconciliation(null)
    }
  }, [])

  const run = useCallback(async (fn: () => Promise<CutoverBatch>, okKey: string) => {
    if (busyRef.current) return
    busyRef.current = true
    try {
      const b = await fn()
      await refrescar(b)
      toast.success(t(okKey))
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    } finally {
      busyRef.current = false
    }
  }, [refrescar, toast, t])

  const handleCreate = async () => {
    if (!cutoverDatetime) {
      toast.warning(t('cutover.dateRequired', 'Indique la fecha/hora de corte'))
      return
    }
    await run(
      () => cutoverService.create({
        business_unit: businessUnit,
        cutover_datetime: new Date(cutoverDatetime).toISOString(),
      }).then(r => r.data),
      'cutover.created')
  }

  const handleUpload = async (file: File | null) => {
    if (!file || !batch) return
    await run(() => cutoverService.upload(batch.id, file).then(r => r.data), 'cutover.uploaded')
  }

  const handleDownloadTemplate = async () => {
    try {
      const res = await cutoverService.template(businessUnit)
      const url = URL.createObjectURL(res.data as Blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `cutover_template_${businessUnit}_v1.xlsx`
      enlace.click()
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    }
  }

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-6xl mx-auto">
      <SubNavHeader title={t('cutover.title', 'Cargas Iniciales')} />

      {/* 1 · Nuevo batch */}
      <Card>
        <CardBody>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">
            {t('cutover.newBatch')}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 items-end">
            <label className="text-sm">
              <span className="block text-slate-600 mb-1">{t('cutover.businessUnit')}</span>
              <select
                className="w-full border rounded-md px-3 py-2 bg-white"
                value={businessUnit}
                onChange={e => setBusinessUnit(e.target.value as BusinessUnitCode)}
                aria-label={t('cutover.businessUnit')}
              >
                {(['grandparent', 'breeder', 'hatchery', 'broiler'] as BusinessUnitCode[]).map(bu => (
                  <option key={bu} value={bu}>{t(`businessUnits.${bu}`, bu)}</option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="block text-slate-600 mb-1">{t('cutover.cutoverDatetime')}</span>
              <input
                type="datetime-local"
                className="w-full border rounded-md px-3 py-2"
                value={cutoverDatetime}
                onChange={e => setCutoverDatetime(e.target.value)}
                aria-label={t('cutover.cutoverDatetime')}
              />
            </label>
            {canCreate && (
              <Button onClick={handleCreate}>{t('cutover.createBatch', 'Crear batch')}</Button>
            )}
          </div>
        </CardBody>
      </Card>

      {!batch && (
        <EmptyState
          icon={Layers}
          title={t('cutover.emptyTitle', 'Sin batch en curso')}
          description={t('cutover.emptyHint', 'Cree un batch para cargar las aperturas del corte.')}
        />
      )}

      {batch && (
        <>
          {/* 2 · Estado + carga */}
          <Card>
            <CardBody className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm text-slate-600">{t('cutover.batch')} #{batch.id}</span>
                <StatusBadge status={batch.status} />
                <span className="text-sm text-slate-500">
                  {t(`businessUnits.${batch.business_unit}`, batch.business_unit)} ·{' '}
                  {new Date(batch.cutover_datetime).toLocaleString()}
                </span>
              </div>

              {canValidate && ['draft', 'validating', 'validated'].includes(batch.status) && (
                <div className="flex flex-wrap items-center gap-3">
                  {canCreate && (
                    <Button variant="outline" onClick={handleDownloadTemplate}>
                      {t('cutover.downloadTemplate', 'Descargar plantilla')}
                    </Button>
                  )}
                  <label className="inline-flex items-center gap-2 text-sm cursor-pointer border rounded-md px-3 py-2 bg-white hover:bg-slate-50">
                    <Upload className="w-4 h-4" aria-hidden />
                    {t('cutover.uploadTemplate', 'Subir plantilla Excel')}
                    <input
                      type="file"
                      accept=".xlsx"
                      className="sr-only"
                      aria-label={t('cutover.uploadTemplate', 'Subir plantilla Excel')}
                      onChange={e => handleUpload(e.target.files?.[0] ?? null)}
                    />
                  </label>
                  {batch.source_filename && (
                    <span className="text-xs text-slate-500">
                      {batch.source_filename} · {t('cutover.rows')}: {batch.total_rows}
                    </span>
                  )}
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div className="rounded-md bg-slate-50 p-3">
                  <div className="text-slate-500">{t('cutover.totalRows')}</div>
                  <div className="font-semibold tabular-nums">{batch.total_rows}</div>
                </div>
                <div className="rounded-md bg-emerald-50 p-3">
                  <div className="text-emerald-700">{t('cutover.validRows')}</div>
                  <div className="font-semibold tabular-nums">{batch.valid_rows}</div>
                </div>
                <div className="rounded-md bg-rose-50 p-3">
                  <div className="text-rose-700">{t('cutover.invalidRows')}</div>
                  <div className="font-semibold tabular-nums">{batch.invalid_rows}</div>
                </div>
                <div className="rounded-md bg-amber-50 p-3">
                  <div className="text-amber-700">{t('cutover.unknownMetrics')}</div>
                  <div className="font-semibold tabular-nums">
                    {reconciliation?.unknown_metrics ?? '—'}
                  </div>
                </div>
              </div>

              {/* Errores de validación */}
              {validation && validation.errors.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <caption className="text-left text-slate-600 pb-2">
                      {t('cutover.validationErrors')}
                    </caption>
                    <thead>
                      <tr className="text-slate-500 text-left border-b">
                        <th className="py-1 pr-3">{t('cutover.row')}</th>
                        <th className="py-1 pr-3">{t('cutover.field')}</th>
                        <th className="py-1 pr-3">{t('cutover.code')}</th>
                        <th className="py-1 pr-3">{t('cutover.receivedValue')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validation.errors.map((e, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="py-1 pr-3 tabular-nums">{e.row_number}</td>
                          <td className="py-1 pr-3">{e.field ?? e.column ?? '—'}</td>
                          <td className="py-1 pr-3 font-mono text-xs">{e.error_code}</td>
                          <td className="py-1 pr-3">{e.received_value ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Acciones del ciclo */}
              <div className="flex flex-wrap gap-3">
                {canSubmit && batch.status === 'validated' && batch.invalid_rows === 0 && (
                  <Button onClick={() => run(() => cutoverService.submit(batch.id).then(r => r.data), 'cutover.submitted')}>
                    <Send className="w-4 h-4 mr-1" aria-hidden />{t('cutover.submit')}
                  </Button>
                )}
                {canApprove && batch.status === 'pending_approval' && (
                  <>
                    <Button onClick={() => run(() => cutoverService.approve(batch.id).then(r => r.data), 'cutover.approved')}>
                      <CheckCircle2 className="w-4 h-4 mr-1" aria-hidden />{t('cutover.approve')}
                    </Button>
                    <div className="flex flex-wrap gap-2 items-center">
                      <input
                        className="border rounded-md px-3 py-2 text-sm"
                        placeholder={t('cutover.rejectReason')}
                        aria-label={t('cutover.rejectReason')}
                        value={rejectReason}
                        onChange={e => setRejectReason(e.target.value)}
                      />
                      <Button
                        variant="danger"
                        onClick={() => run(() => cutoverService.reject(batch.id, rejectReason).then(r => r.data), 'cutover.rejected')}
                        disabled={rejectReason.trim().length < 5}
                      >
                        <XCircle className="w-4 h-4 mr-1" aria-hidden />{t('cutover.reject')}
                      </Button>
                    </div>
                  </>
                )}
                {canApply && (
                  <Button
                    onClick={() => run(() => cutoverService.apply(batch.id).then(r => r.data), 'cutover.applied')}
                    disabled={!aplicable}
                    title={!aplicable ? t('cutover.applyBlocked') : t('cutover.apply')}
                  >
                    <PlayCircle className="w-4 h-4 mr-1" aria-hidden />{t('cutover.apply')}
                  </Button>
                )}
                {canApply && !aplicable && batch.status === 'approved' && (
                  <p className="text-xs text-rose-700 self-center">
                    {t('cutover.applyBlocked', 'No se aplica con errores pendientes')}
                  </p>
                )}
              </div>
            </CardBody>
          </Card>

          {/* 3 · Preview de filas (AC80) */}
          {items.length > 0 && (
            <Card>
              <CardBody>
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">
                  {t('cutover.preview')}
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-500 text-left border-b">
                        <th className="py-1 pr-3">{t('cutover.sourceRow')}</th>
                        <th className="py-1 pr-3">{t('cutover.legacyCode')}</th>
                        <th className="py-1 pr-3">{t('cutover.realStartDate')}</th>
                        <th className="py-1 pr-3">{t('common.status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map(it => (
                        <tr key={it.id} className="border-b last:border-0">
                          <td className="py-1 pr-3 tabular-nums">{it.source_row_number}</td>
                          <td className="py-1 pr-3 font-mono text-xs">{it.legacy_lot_reference ?? '—'}</td>
                          <td className="py-1 pr-3">{it.real_start_date ?? '—'}</td>
                          <td className="py-1 pr-3">
                            <Badge variant={it.validation_status === 'valid' || it.validation_status === 'applied' ? 'approved' : 'rejected'}>
                              {t(`cutover.itemStatus.${it.validation_status}`, it.validation_status)}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          )}

          {/* 4 · Reconciliación Opening/Post/Lifetime (AC76-79) */}
          {reconciliation && (
            <Card>
              <CardBody>
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                    {t('cutover.reconciliation')}
                  </h3>
                  <RefreshCw className="w-4 h-4 text-slate-400" aria-hidden />
                  <span className="text-xs text-slate-500">
                    {t('cutover.source')}: {reconciliation.source.type}
                    {reconciliation.source.filename ? ` · ${reconciliation.source.filename}` : ''}
                    {reconciliation.source.checksum
                      ? ` · ${String(reconciliation.source.checksum).slice(0, 12)}…`
                      : ''}
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-500 text-left border-b">
                        <th className="py-1 pr-3">{t('cutover.legacyCode')}</th>
                        <th className="py-1 pr-3">{t('cutover.openingLive')}</th>
                        <th className="py-1 pr-3">{t('cutover.historicalMortality')}</th>
                        <th className="py-1 pr-3">{t('cutover.postMortality')}</th>
                        <th className="py-1 pr-3">{t('cutover.lifetimeMortality')}</th>
                        <th className="py-1 pr-3">{t('cutover.currentLive')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reconciliation.lots.map((lote: CutoverReconciliationLot) => (
                        <tr key={lote.lot_id} className="border-b last:border-0">
                          <td className="py-1 pr-3 font-mono text-xs">
                            {lote.legacy_lot_code ?? `#${lote.lot_id}`}
                          </td>
                          <td className="py-1 pr-3 tabular-nums">{lote.opening.live.toLocaleString()}</td>
                          <td className="py-1 pr-3"><Metric value={lote.opening.historical_mortality} /></td>
                          <td className="py-1 pr-3 tabular-nums">{lote.post.mortality.toLocaleString()}</td>
                          <td className="py-1 pr-3"><Metric value={lote.lifetime.mortality} /></td>
                          <td className="py-1 pr-3 font-semibold tabular-nums">
                            {lote.current_live.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
