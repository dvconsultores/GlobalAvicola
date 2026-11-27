/**
 * GA-REQ-061 · T14 · C8 + SPEC 006 — «Cargas Iniciales» (cutover operacional v2).
 *
 * La pantalla guía al usuario en el orden del mandato (§35): unidad y corte → crear carga →
 * descargar la plantilla **de esa unidad** (XLSX o CSV; la BU la fija la carga, nunca un
 * selector) → subir archivo → validación con mensajes y descarga de errores → vista previa
 * funcional por BU → enviar → aprobar (otro actor) → aplicar → reconciliación → continuar al
 * módulo operativo con el primer evento post-corte.
 *
 * Reglas duras de esta superficie:
 *   - El estado de la carga SIEMPRE visible (AC82) y las cargas se listan: nada se pierde al recargar.
 *   - «Aplicar» jamás accionable con filas inválidas/pendientes (AC81); el backend es la autoridad.
 *   - UNKNOWN y N/A se muestran como tales (`null` nunca se pinta como 0 — AC77).
 *   - Todo texto sale de i18n (AC84/85); responsive 360/390/desktop (tablas con scroll, cards en móvil).
 */
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Upload, Send, CheckCircle2, XCircle, PlayCircle, RefreshCw, Layers, Download, FileSpreadsheet,
  FileText, ArrowRight, ListChecks,
} from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
import { hasPermission } from '../../auth/permissions'
import { Badge, Button, Card, CardBody, EmptyState } from '../../components/ui'
import type { StatusKey } from '../../data/statusColors'
import { useToast, getErrorMessage } from '../../components/Toast'
import SubNavHeader from '../../components/layout/SubNavHeader'
import {
  BUSINESS_UNITS,
  cutoverService,
  descargarBlob,
  type BusinessUnitCode,
  type CutoverBatch,
  type CutoverHatcheryOpening,
  type CutoverPreview,
  type CutoverPreviewRow,
  type CutoverReconciliation,
  type CutoverReconciliationLot,
  type CutoverValidation,
  type MetricCell,
  type TemplateFormat,
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

const STEPS = ['unit', 'template', 'upload', 'validation', 'preview', 'approval', 'apply', 'reconcile'] as const

function pasoActual(batch: CutoverBatch | null): number {
  if (!batch) return 0
  switch (batch.status) {
    case 'draft': return 1
    case 'validating': return 3
    case 'validated': return 4
    case 'pending_approval': return 5
    case 'approved': return 6
    case 'applied': return 7
    case 'rejected': return 5
    default: return 1
  }
}

/** AC77: un `null` es UNKNOWN — jamás se pinta como 0. */
function Metric({ value, status }: { value: number | string | null | undefined; status?: string }) {
  const { t } = useTranslation()
  if (status === 'NOT_APPLICABLE') {
    return <span className="text-slate-400 italic">{t('cutover.notApplicable', 'N/A')}</span>
  }
  if (value === null || value === undefined || status === 'UNKNOWN') {
    return (
      <span className="inline-flex items-center gap-1 text-amber-700 font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" aria-hidden />
        {t('cutover.unknown', 'UNKNOWN')}
      </span>
    )
  }
  return <span className="tabular-nums">{typeof value === 'number' ? value.toLocaleString() : String(value)}</span>
}

function Cell({ cell }: { cell?: MetricCell }) {
  if (!cell) return <span className="text-slate-300">—</span>
  return <Metric value={cell.value} status={cell.status} />
}

/**
 * SPEC 018 · D-3/D-10 — «Total no incubables» **derivado** (nunca editable): el backend solo lo
 * entrega si los tres componentes son KNOWN; si falta alguno llega `null` + UNKNOWN y aquí se
 * pinta UNKNOWN (jamás una suma parcial ni un 0 inventado). El desglose va compacto en la celda.
 */
function TotalNoIncubables({ hatchery }: { hatchery?: CutoverHatcheryOpening | null }) {
  const { t } = useTranslation()
  const componentes = [
    { campo: 'eggs_non_incubable_oversized', valor: hatchery?.eggs_non_incubable_oversized, estado: hatchery?.eggs_non_incubable_oversized_status },
    { campo: 'eggs_non_incubable_dirty', valor: hatchery?.eggs_non_incubable_dirty, estado: hatchery?.eggs_non_incubable_dirty_status },
    { campo: 'eggs_non_incubable_broken', valor: hatchery?.eggs_non_incubable_broken, estado: hatchery?.eggs_non_incubable_broken_status },
  ]
  return (
    <div
      className="leading-tight"
      title={`${t('cutover.derivedHint', 'Calculado por el sistema: no editable')} (${t('cutover.derivedLabel', 'derivado')})`}
    >
      <Metric value={hatchery?.eggs_non_incubable_total ?? null} status={hatchery?.eggs_non_incubable_total_status} />
      <ul
        className="mt-0.5 space-y-0 text-[11px] text-slate-500"
        aria-label={t('cutover.nonIncubableBreakdown', 'Desglose de no incubables')}
        data-testid="cutover-non-incubable-breakdown"
      >
        {componentes.map(c => (
          <li key={c.campo} data-testid={`cutover-non-incubable-${c.campo}`}>
            <span>{t(`cutover.fields.${c.campo}`, c.campo)}: </span>
            <Metric value={c.valor ?? null} status={c.estado} />
          </li>
        ))}
      </ul>
    </div>
  )
}

/** SPEC 018 · D-3: total derivado de una fila del preview (la cifra la calcula el backend). */
function totalDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_non_incubable_total
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}

/** SPEC 018 §8 · D-20: «huevos en proceso» derivado de una fila (lo calcula el backend; `null` = UNKNOWN). */
function enProcesoDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_in_process
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}

/** SPEC 018 §9 · D-24: saldo disponible para cargar de una fila (lo calcula el backend; `null` = UNKNOWN). */
function disponibleDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_available_to_set
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}

/**
 * SPEC 018 §9 · D-26: columnas derivadas del preview de incubadora, cada una tras su columna ancla para
 * leer las dos etapas: PRE-CARGA (recibidos → no incubables → fosa → cargados → saldo disponible) y
 * POST-CARGA (transferidos → en proceso). Si el ancla no está en la vista, la derivada va al final.
 */
interface DerivadaPreview {
  clave: string
  tras: string
  etiqueta: string
  porDefecto: string
  thTestId?: string
  celdaTestId: string
  cardTestId?: string
  valor: (fila: CutoverPreviewRow) => { value: number | null; status: string }
}
const DERIVADAS_PREVIEW: DerivadaPreview[] = [
  { clave: 'total', tras: 'eggs_non_incubable_broken', etiqueta: 'cutover.eggsNonIncubableTotal', porDefecto: 'Total no incubables',
    celdaTestId: 'cutover-preview-total', valor: totalDerivado },
  { clave: 'available', tras: 'eggs_set', etiqueta: 'cutover.eggsAvailableToSet', porDefecto: 'Saldo disponible para cargar',
    thTestId: 'cutover-th-preview-available', celdaTestId: 'cutover-preview-available', cardTestId: 'cutover-preview-available-card',
    valor: disponibleDerivado },
  { clave: 'in-process', tras: 'eggs_transferred', etiqueta: 'cutover.eggsInProcess', porDefecto: 'Huevos en proceso',
    thTestId: 'cutover-th-preview-in-process', celdaTestId: 'cutover-preview-in-process', cardTestId: 'cutover-preview-in-process-card',
    valor: enProcesoDerivado },
]

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation()
  return (
    <Badge variant={STATUS_VARIANT[status] || 'neutral'}>
      {t(`cutover.status.${status}`, status)}
    </Badge>
  )
}

function Stepper({ actual }: { actual: number }) {
  const { t } = useTranslation()
  return (
    <ol className="flex flex-wrap gap-2 text-xs" aria-label={t('cutover.title')}>
      {STEPS.map((paso, i) => {
        const hecho = i < actual
        const activo = i === actual
        return (
          <li
            key={paso}
            className={[
              'inline-flex items-center gap-1 rounded-full px-2.5 py-1 border',
              hecho ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : '',
              activo ? 'bg-brand-50 text-brand-800 border-brand-300 font-semibold' : '',
              !hecho && !activo ? 'bg-slate-50 text-slate-500 border-slate-200' : '',
            ].join(' ')}
            aria-current={activo ? 'step' : undefined}
          >
            <span className="tabular-nums">{i + 1}</span>
            <span>{t(`cutover.steps.${paso}`)}</span>
          </li>
        )
      })}
    </ol>
  )
}

/** SPEC 011 · el nombre del archivo viene del servidor (Content-Disposition), con la versión real del template. */
export function nombreDescarga(res: { headers?: Record<string, unknown> }, fallback: string): string {
  const cd = String(res.headers?.['content-disposition'] ?? '')
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd)
  return m ? decodeURIComponent(m[1]) : fallback
}

export default function CargasInicialesPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const sessionUser = useAuthStore(s => s.user)

  const canCreate = hasPermission(sessionUser, 'cutover:create')
  const canValidate = hasPermission(sessionUser, 'cutover:validate')
  const canSubmit = hasPermission(sessionUser, 'cutover:submit')
  const canApprove = hasPermission(sessionUser, 'cutover:approve')
  const canApply = hasPermission(sessionUser, 'cutover:apply')

  const unidadesDelUsuario = useMemo<BusinessUnitCode[]>(() => {
    const efectivas = (sessionUser?.effective_business_units ?? []) as BusinessUnitCode[]
    const propias = BUSINESS_UNITS.filter(bu => efectivas.includes(bu))
    return propias.length ? propias : BUSINESS_UNITS
  }, [sessionUser])

  const [businessUnit, setBusinessUnit] = useState<BusinessUnitCode>(() => unidadesDelUsuario[0])
  const [cutoverDatetime, setCutoverDatetime] = useState('')
  const [batches, setBatches] = useState<CutoverBatch[]>([])
  const [batch, setBatch] = useState<CutoverBatch | null>(null)
  const [validation, setValidation] = useState<CutoverValidation | null>(null)
  const [preview, setPreview] = useState<CutoverPreview | null>(null)
  const [reconciliation, setReconciliation] = useState<CutoverReconciliation | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [todasLasColumnas, setTodasLasColumnas] = useState(false)
  const [inputKey, setInputKey] = useState(0)
  const [verInstrucciones, setVerInstrucciones] = useState(false)
  const busyRef = useRef(false)

  const aplicable =
    batch?.status === 'approved' && (batch?.invalid_rows ?? 1) === 0 &&
    (validation?.errors?.length ?? 1) === 0

  const cargarLista = useCallback(async () => {
    try {
      const r = await cutoverService.list({ limit: 20 })
      setBatches(r.data.items || [])
    } catch {
      setBatches([])
    }
  }, [])

  const refrescar = useCallback(async (b: CutoverBatch) => {
    setBatch(b)
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('batch', String(b.id))
      return next
    }, { replace: true })
    const v = await cutoverService.validation(b.id)
    setValidation(v.data)
    if (b.total_rows > 0) {
      try {
        const p = await cutoverService.preview(b.id)
        setPreview(p.data)
      } catch {
        setPreview(null)
      }
    } else {
      setPreview(null)
    }
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
  }, [setSearchParams])

  // Persistencia visible: la carga sobrevive a la recarga de la página (`?batch=`).
  useEffect(() => {
    void cargarLista()
    const id = Number(searchParams.get('batch'))
    if (id > 0) {
      cutoverService.get(id).then(r => refrescar(r.data)).catch(() => undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const run = useCallback(async (fn: () => Promise<CutoverBatch>, okKey: string) => {
    if (busyRef.current) return
    busyRef.current = true
    try {
      const b = await fn()
      await refrescar(b)
      await cargarLista()
      toast.success(t(okKey))
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    } finally {
      busyRef.current = false
    }
  }, [refrescar, cargarLista, toast, t])

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
    if (busyRef.current) return
    busyRef.current = true
    try {
      const b = (await cutoverService.upload(batch.id, file)).data
      await refrescar(b)
      await cargarLista()
      if (b.invalid_rows > 0) toast.warning(t('cutover.uploadedWithErrors'))
      else toast.success(t('cutover.uploaded'))
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    } finally {
      busyRef.current = false
      setInputKey(k => k + 1) // el mismo archivo corregido se puede volver a subir
    }
  }

  const handleDownloadTemplate = async (format: TemplateFormat) => {
    if (!batch) return
    try {
      const res = await cutoverService.template(batch.business_unit, { format, batchId: batch.id })
      descargarBlob(res.data as Blob, nombreDescarga(res, `cutover_template_${batch.business_unit}_${batch.template_version ?? 'v2'}.${format}`))
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    }
  }

  const handleDownloadTemplateEarly = async (format: TemplateFormat) => {
    if (!cutoverDatetime) return
    try {
      const res = await cutoverService.template(businessUnit, { format, cutoverDatetime: cutoverDatetime ? new Date(cutoverDatetime).toISOString() : undefined })
      descargarBlob(res.data as Blob, nombreDescarga(res, `cutover_template_${businessUnit}.${format}`))
      toast.success(t('cutover.downloadSuccess'))
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('cutover.downloadError')))
    }
  }

  const handleDownloadErrors = async (format: TemplateFormat) => {
    if (!batch) return
    try {
      const res = await cutoverService.errorsReport(batch.id, format)
      descargarBlob(res.data as Blob, `cutover_batch_${batch.id}_errores.${format}`)
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    }
  }

  const abrir = async (id: number) => {
    try {
      const r = await cutoverService.get(id)
      await refrescar(r.data)
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, t('common.error')))
    }
  }

  const columnasPreview = preview ? (todasLasColumnas ? preview.columns : preview.highlight) : []
  const resumen = preview?.summary
  const esIncubadora = batch?.business_unit === 'hatchery'
  /** SPEC 018 · D-3: el total no incubable es derivado (no es columna del contrato). */
  const muestraTotalDerivadoPreview = esIncubadora && (
    String(preview?.template_version ?? '') === 'v4' ||
    (preview?.rows ?? []).some(fila => !!fila.derived && 'eggs_non_incubable_total' in fila.derived)
  )
  /** SPEC 018 §9 · D-26: derivadas tras su ancla; las de ancla ausente se pintan al final. */
  const derivadasTras = (col: string): DerivadaPreview[] =>
    (muestraTotalDerivadoPreview ? DERIVADAS_PREVIEW.filter(d => d.tras === col) : [])
  const derivadasHuerfanas: DerivadaPreview[] = muestraTotalDerivadoPreview
    ? DERIVADAS_PREVIEW.filter(d => !columnasPreview.includes(d.tras))
    : []
  /** SPEC 018 · D-10: «Huevos descartados (histórico V3)» solo si el batch trae algún descartado KNOWN. */
  const muestraDescartadosHistoricos = esIncubadora &&
    (reconciliation?.lots ?? []).some(lote => lote.opening?.hatchery?.eggs_discarded_status === 'KNOWN')

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-6xl mx-auto">
      <SubNavHeader title={t('cutover.title', 'Cargas Iniciales')} />

      <Stepper actual={pasoActual(batch)} />

      {/* 0 · Cargas existentes */}
      <Card>
        <CardBody>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">
            {t('cutover.list')}
          </h2>
          {batches.length === 0 ? (
            <p className="text-sm text-slate-500">{t('cutover.listEmpty')}</p>
          ) : (
            <ul className="divide-y divide-slate-100" data-testid="cutover-batch-list">
              {batches.map(b => (
                <li key={b.id} className="py-2 flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-mono text-xs text-slate-500">#{b.id}</span>
                  <span className="font-medium">{t(`businessUnits.${b.business_unit}`, b.business_unit)}</span>
                  <span className="text-slate-500">{new Date(b.cutover_datetime).toLocaleString()}</span>
                  <StatusBadge status={b.status} />
                  <span className="text-slate-500">{b.total_rows} {t('cutover.rows')}</span>
                  <Button size="sm" variant={batch?.id === b.id ? 'secondary' : 'outline'} onClick={() => abrir(b.id)}>
                    {batch?.id === b.id ? t('cutover.current') : t('cutover.open')}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {/* 1 · Nueva carga */}
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
                {unidadesDelUsuario.map(bu => (
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
              <Button onClick={handleCreate}>{t('cutover.createBatch', 'Crear carga')}</Button>
            )}
          </div>

          {canCreate && (
            <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
              <p className="text-sm text-slate-600">{t('cutover.downloadIntro')}</p>
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => handleDownloadTemplateEarly('xlsx')} disabled={!cutoverDatetime}>
                  <FileSpreadsheet className="w-4 h-4 mr-1" aria-hidden />
                  {t('cutover.downloadTemplatePrimary')}
                </Button>
                <Button variant="outline" onClick={() => handleDownloadTemplateEarly('csv')} disabled={!cutoverDatetime}>
                  <FileText className="w-4 h-4 mr-1" aria-hidden />
                  {t('cutover.downloadTemplatePrimaryCsv')}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setVerInstrucciones(v => !v)} aria-expanded={verInstrucciones}>
                  {verInstrucciones ? t('cutover.hideInstructions') : t('cutover.viewInstructions')}
                </Button>
              </div>
              {!cutoverDatetime && (
                <p className="text-xs text-slate-500">{t('cutover.downloadDisabledHint')}</p>
              )}
              <div className="rounded-md bg-slate-50 border border-slate-200 p-3 text-sm text-slate-600">
                <p className="font-medium text-slate-700">{t('cutover.downloadHelpTitle')}</p>
                <p>{t('cutover.downloadHelpBody')}</p>
                <ol className="mt-2 list-decimal list-inside space-y-0.5">
                  <li>{t('cutover.howTo1')}</li>
                  <li>{t('cutover.howTo2')}</li>
                  <li>{t('cutover.howTo3')}</li>
                </ol>
              </div>
              {verInstrucciones && (
                <div className="rounded-md border border-slate-200 p-3 text-sm" data-testid="cutover-instructions">
                  <p className="font-semibold text-slate-800 mb-1">{t('cutover.instructionsTitle')}</p>
                  <ol className="list-decimal list-inside space-y-0.5 text-slate-600">
                    <li>{t('cutover.ins1')}</li>
                    <li>{t('cutover.ins2')}</li>
                    <li>{t('cutover.ins3')}</li>
                    <li>{t('cutover.ins4')}</li>
                    <li>{t('cutover.ins5')}</li>
                    <li>{t('cutover.ins6')}</li>
                    <li>{t('cutover.ins7')}</li>
                    <li>{t('cutover.ins8')}</li>
                  </ol>
                </div>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {!batch && (
        <EmptyState
          icon={Layers}
          title={t('cutover.emptyTitle', 'Sin carga en curso')}
          description={t('cutover.emptyHint')}
        />
      )}

      {batch && (
        <>
          {/* 2 · Estado + plantilla + carga */}
          <Card>
            <CardBody className="space-y-4">
              <div className="flex flex-wrap items-center gap-3" data-testid="cutover-batch-header">
                <span className="text-sm text-slate-600">{t('cutover.batch')} #{batch.id}</span>
                <StatusBadge status={batch.status} />
                <span className="text-sm font-medium">
                  {t(`businessUnits.${batch.business_unit}`, batch.business_unit)}
                </span>
                <span className="text-sm text-slate-500">{new Date(batch.cutover_datetime).toLocaleString()}</span>
                {batch.template_version && (
                  <span className="text-xs text-slate-500">
                    {t('cutover.templateVersion')}: {batch.template_version} · {t('cutover.format')}: {batch.source_type}
                  </span>
                )}
              </div>

              {canValidate && ['draft', 'validating', 'validated'].includes(batch.status) && (
                <div className="space-y-3">
                  {canCreate && (
                    <div className="flex flex-wrap items-center gap-3">
                      <Button variant="outline" onClick={() => handleDownloadTemplate('xlsx')}>
                        <FileSpreadsheet className="w-4 h-4 mr-1" aria-hidden />
                        {t('cutover.downloadTemplate')}
                      </Button>
                      <Button variant="outline" onClick={() => handleDownloadTemplate('csv')}>
                        <FileText className="w-4 h-4 mr-1" aria-hidden />
                        {t('cutover.downloadTemplateCsv')}
                      </Button>
                    </div>
                  )}
                  <div className="flex flex-wrap items-center gap-3">
                    <label className="inline-flex items-center gap-2 text-sm cursor-pointer border rounded-md px-3 py-2 bg-white hover:bg-slate-50">
                      <Upload className="w-4 h-4" aria-hidden />
                      {t('cutover.uploadTemplate')}
                      <input
                        key={inputKey}
                        type="file"
                        accept=".xlsx,.csv"
                        className="sr-only"
                        aria-label={t('cutover.uploadTemplate')}
                        data-testid="cutover-file-input"
                        onChange={e => handleUpload(e.target.files?.[0] ?? null)}
                      />
                    </label>
                    {batch.source_filename && (
                      <span className="text-xs text-slate-500">
                        {t('cutover.sourceFile')}: {batch.source_filename} · {t('cutover.rows')}: {batch.total_rows}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">{t('cutover.uploadHint')}</p>
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
                    {reconciliation?.unknown_metrics ?? resumen?.unknown_metrics ?? '—'}
                  </div>
                </div>
              </div>

              {/* Errores de validación: mensaje visible + descarga */}
              {validation && validation.errors.length > 0 && (
                <div className="space-y-2" data-testid="cutover-errors">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-rose-800">
                      {t('cutover.validationErrors')} ({validation.errors.length})
                    </span>
                    <Button size="sm" variant="outline" onClick={() => handleDownloadErrors('csv')}>
                      <Download className="w-4 h-4 mr-1" aria-hidden />{t('cutover.downloadErrors')}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleDownloadErrors('xlsx')}>
                      <Download className="w-4 h-4 mr-1" aria-hidden />{t('cutover.downloadErrorsXlsx')}
                    </Button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[560px]">
                      <thead>
                        <tr className="text-slate-500 text-left border-b">
                          <th className="py-1 pr-3">{t('cutover.row')}</th>
                          <th className="py-1 pr-3">{t('cutover.field')}</th>
                          <th className="py-1 pr-3">{t('cutover.code')}</th>
                          <th className="py-1 pr-3">{t('cutover.message')}</th>
                          <th className="py-1 pr-3">{t('cutover.receivedValue')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {validation.errors.slice(0, 200).map((e, i) => (
                          <tr key={i} className="border-b last:border-0 align-top">
                            <td className="py-1 pr-3 tabular-nums">{e.row_number}</td>
                            <td className="py-1 pr-3">{t(`cutover.fields.${e.field ?? e.column ?? ''}`, e.field ?? e.column ?? '—')}</td>
                            <td className="py-1 pr-3 font-mono text-xs">{e.error_code}</td>
                            <td className="py-1 pr-3 text-slate-700">{e.message}</td>
                            <td className="py-1 pr-3 font-mono text-xs">{e.received_value ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
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
                {canApply && batch.status !== 'applied' && batch.status !== 'rejected' && (
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

          {/* 3 · Vista previa funcional por BU */}
          <Card>
            <CardBody>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <ListChecks className="w-4 h-4 text-slate-400" aria-hidden />
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
                  {t('cutover.preview')}
                </h3>
                {preview && preview.columns.length > preview.highlight.length && (
                  <Button size="sm" variant="ghost" onClick={() => setTodasLasColumnas(v => !v)}>
                    {todasLasColumnas ? t('cutover.previewLess') : t('cutover.previewAll')}
                  </Button>
                )}
              </div>
              {!preview ? (
                <p className="text-sm text-slate-500">{t('cutover.previewEmpty')}</p>
              ) : (
                <div className="space-y-3" data-testid="cutover-preview">
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.lots')}: <b className="tabular-nums">{resumen?.lots ?? 0}</b></span>
                    {esIncubadora ? (
                      <>
                        <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.eggsReceived')}: <b className="tabular-nums">{Number(resumen?.eggs_received ?? 0).toLocaleString()}</b></span>
                        <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.eggsSet')}: <b className="tabular-nums">{Number(resumen?.eggs_set ?? 0).toLocaleString()}</b></span>
                        <span className="rounded-md bg-slate-100 px-2 py-1" data-testid="cutover-chip-eggs-in-process">{t('cutover.eggsInProcess')}: <Metric value={resumen?.eggs_in_process} status={resumen?.eggs_in_process_status} /></span>
                        <span className="rounded-md bg-slate-100 px-2 py-1" data-testid="cutover-chip-chicks-available">{t('cutover.chicksAvailable')}: <Metric value={resumen?.chicks_available} status={resumen?.chicks_available_status} /></span>
                        {(resumen?.hatcheries ?? []).length > 0 && (
                          <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.hatcheries')}: {(resumen?.hatcheries ?? []).join(', ')}</span>
                        )}
                      </>
                    ) : (
                      <>
                        <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.liveBirds')}: <b className="tabular-nums">{Number(resumen?.live_birds ?? 0).toLocaleString()}</b></span>
                        {batch.business_unit !== 'broiler' && (
                          <>
                            <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.liveMales')}: <b className="tabular-nums">{Number(resumen?.live_males ?? 0).toLocaleString()}</b></span>
                            <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.liveFemales')}: <b className="tabular-nums">{Number(resumen?.live_females ?? 0).toLocaleString()}</b></span>
                          </>
                        )}
                        <span className="rounded-md bg-slate-100 px-2 py-1">
                          {t('cutover.historicalMortality')}: <Metric value={resumen?.historical_mortality} status={resumen?.historical_mortality_status} />
                        </span>
                        <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.feedKg')}: <b className="tabular-nums">{Number(resumen?.accumulated_feed_kg ?? 0).toLocaleString()}</b></span>
                        {Object.keys(resumen?.by_phase ?? {}).length > 0 && (
                          <span className="rounded-md bg-slate-100 px-2 py-1">
                            {t('cutover.byPhase')}: {Object.entries(resumen?.by_phase ?? {}).map(([k, v]) => `${k} ${v}`).join(' · ')}
                          </span>
                        )}
                        {(resumen?.farms ?? []).length > 0 && (
                          <span className="rounded-md bg-slate-100 px-2 py-1">{t('cutover.farms')}: {(resumen?.farms ?? []).join(', ')}</span>
                        )}
                      </>
                    )}
                    <span className="rounded-md bg-amber-50 text-amber-800 px-2 py-1">{t('cutover.unknownMetrics')}: <b className="tabular-nums">{resumen?.unknown_metrics ?? 0}</b></span>
                  </div>
                  {muestraTotalDerivadoPreview && (
                    <p className="text-xs text-slate-500" data-testid="cutover-preview-stages">
                      {t('cutover.stagesHint', 'Pre-carga: recibidos − no incubables − fosa − cargados = saldo disponible para cargar. Post-carga: cargados − transferidos = huevos en proceso.')}
                    </p>
                  )}

                  {/* Tabla (≥ sm) */}
                  <div className="hidden sm:block overflow-x-auto">
                    <table className="w-full text-sm min-w-[640px]">
                      <thead>
                        <tr className="text-slate-500 text-left border-b">
                          <th className="py-1 pr-3">{t('cutover.sourceRow')}</th>
                          {columnasPreview.map(col => (
                            <Fragment key={col}>
                              <th className="py-1 pr-3 whitespace-nowrap">{t(`cutover.fields.${col}`, col)}</th>
                              {derivadasTras(col).map(d => (
                                <th key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={d.thTestId}>
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase text-slate-400">
                                    ({t('cutover.derivedLabel', 'derivado')})
                                  </span>
                                </th>
                              ))}
                            </Fragment>
                          ))}
                          {derivadasHuerfanas.map(d => (
                                <th key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={d.thTestId}>
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase text-slate-400">
                                    ({t('cutover.derivedLabel', 'derivado')})
                                  </span>
                                </th>
                          ))}
                          <th className="py-1 pr-3">{t('common.status')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.map(fila => (
                          <tr key={fila.row_number} className="border-b last:border-0">
                            <td className="py-1 pr-3 tabular-nums">{fila.row_number}</td>
                            {columnasPreview.map(col => (
                              <Fragment key={col}>
                                <td className="py-1 pr-3 whitespace-nowrap"><Cell cell={fila.values[col]} /></td>
                                {derivadasTras(col).map(d => (
                                  <td key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={`${d.celdaTestId}-${fila.row_number}`}>
                                  <Metric {...d.valor(fila)} />
                                </td>
                                ))}
                              </Fragment>
                            ))}
                            {derivadasHuerfanas.map(d => (
                                  <td key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={`${d.celdaTestId}-${fila.row_number}`}>
                                  <Metric {...d.valor(fila)} />
                                </td>
                            ))}
                            <td className="py-1 pr-3">
                              <Badge variant={fila.status === 'valid' || fila.status === 'applied' ? 'approved' : 'rejected'}>
                                {t(`cutover.itemStatus.${fila.status}`, fila.status)}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {/* Cards (móvil) */}
                  <ul className="sm:hidden space-y-2">
                    {preview.rows.map(fila => (
                      <li key={fila.row_number} className="rounded-md border border-slate-200 p-3 text-sm space-y-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-xs">{t('cutover.row')} {fila.row_number} · {fila.legacy_lot_code ?? '—'}</span>
                          <Badge variant={fila.status === 'valid' || fila.status === 'applied' ? 'approved' : 'rejected'}>
                            {t(`cutover.itemStatus.${fila.status}`, fila.status)}
                          </Badge>
                        </div>
                        {columnasPreview.filter(c => c !== 'legacy_lot_code').map(col => (
                          <Fragment key={col}>
                            <div className="flex justify-between gap-2">
                              <span className="text-slate-500">{t(`cutover.fields.${col}`, col)}</span>
                              <Cell cell={fila.values[col]} />
                            </div>
                            {derivadasTras(col).map(d => (
                              <div key={d.clave} className="flex justify-between gap-2"
                                data-testid={d.cardTestId ? `${d.cardTestId}-${fila.row_number}` : undefined}>
                                <span className="text-slate-500">
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase">({t('cutover.derivedLabel', 'derivado')})</span>
                                </span>
                                <Metric {...d.valor(fila)} />
                              </div>
                            ))}
                          </Fragment>
                        ))}
                        {derivadasHuerfanas.map(d => (
                              <div key={d.clave} className="flex justify-between gap-2"
                                data-testid={d.cardTestId ? `${d.cardTestId}-${fila.row_number}` : undefined}>
                                <span className="text-slate-500">
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase">({t('cutover.derivedLabel', 'derivado')})</span>
                                </span>
                                <Metric {...d.valor(fila)} />
                              </div>
                        ))}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardBody>
          </Card>

          {/* 4 · Reconciliación Opening/Post/Lifetime/Current (AC76-79 + SPEC 006) */}
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
                <div className="overflow-x-auto" data-testid="cutover-reconciliation">
                  <table className={`w-full text-sm ${esIncubadora ? 'min-w-[960px]' : 'min-w-[720px]'}`}>
                    <thead>
                      <tr className="text-slate-500 text-left border-b">
                        <th className="py-1 pr-3">{t('cutover.legacyCode')}</th>
                        {esIncubadora ? (
                          <>
                            <th className="py-1 pr-3">{t('cutover.eggsReceived')}</th>
                            <th className="py-1 pr-3 whitespace-nowrap" data-testid="cutover-th-non-incubable-total">
                              {t('cutover.eggsNonIncubableTotal', 'Total no incubables')}{' '}
                              <span className="text-[11px] lowercase text-slate-400">
                                ({t('cutover.derivedLabel', 'derivado')})
                              </span>
                            </th>
                            <th className="py-1 pr-3 whitespace-nowrap">{t('cutover.fertileEggsToPit', 'Huevos fértiles a fosa')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsSet')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsAvailable')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsInProcess')}</th>
                            {muestraDescartadosHistoricos && (
                              <th className="py-1 pr-3 whitespace-nowrap" data-testid="cutover-th-eggs-discarded">
                                {t('cutover.eggsDiscardedHistorical', 'Huevos descartados (histórico V3)')}
                              </th>
                            )}
                            <th className="py-1 pr-3">{t('cutover.chicksHatched')}</th>
                            <th className="py-1 pr-3">{t('cutover.chicksAvailable')}</th>
                          </>
                        ) : (
                          <>
                            <th className="py-1 pr-3">{t('cutover.openingLive')}</th>
                            <th className="py-1 pr-3">{t('cutover.historicalMortality')}</th>
                            <th className="py-1 pr-3">{t('cutover.postMortality')}</th>
                            <th className="py-1 pr-3">{t('cutover.lifetimeMortality')}</th>
                            <th className="py-1 pr-3">{t('cutover.historicalCulls')}</th>
                            <th className="py-1 pr-3">{t('cutover.feedKg')}</th>
                            {batch.business_unit !== 'broiler' && <th className="py-1 pr-3">{t('cutover.eggProduction')}</th>}
                            <th className="py-1 pr-3">{t('cutover.currentLive')}</th>
                          </>
                        )}
                        <th className="py-1 pr-3">{t('common.actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reconciliation.lots.map((lote: CutoverReconciliationLot) => (
                        <tr key={lote.lot_id} className="border-b last:border-0">
                          <td className="py-1 pr-3 font-mono text-xs">
                            {lote.legacy_lot_code ?? `#${lote.lot_id}`}
                          </td>
                          {esIncubadora ? (
                            <>
                              <td className="py-1 pr-3"><Metric value={lote.opening.hatchery?.eggs_received} status={lote.opening.hatchery?.eggs_received_status} /></td>
                              <td className="py-1 pr-3" data-testid={`cutover-non-incubable-total-${lote.lot_id}`}>
                                <TotalNoIncubables hatchery={lote.opening.hatchery} />
                              </td>
                              <td className="py-1 pr-3" data-testid={`cutover-fertile-pit-${lote.lot_id}`}>
                                <Metric
                                  value={lote.opening.hatchery?.fertile_eggs_to_pit ?? null}
                                  status={lote.opening.hatchery?.fertile_eggs_to_pit_status}
                                />
                              </td>
                              <td className="py-1 pr-3"><Metric value={lote.opening.hatchery?.eggs_set} status={lote.opening.hatchery?.eggs_set_status} /></td>
                              <td className="py-1 pr-3 font-semibold" data-testid={`cutover-eggs-available-${lote.lot_id}`}>
                                <Metric value={lote.current?.eggs_available_hatchery ?? null} />
                              </td>
                              <td className="py-1 pr-3" data-testid={`cutover-eggs-in-process-${lote.lot_id}`}>
                                <Metric value={lote.current?.eggs_in_process ?? null} />
                              </td>
                              {muestraDescartadosHistoricos && (
                                <td className="py-1 pr-3" data-testid={`cutover-eggs-discarded-${lote.lot_id}`}>
                                  <Metric
                                    value={lote.opening.hatchery?.eggs_discarded ?? null}
                                    status={lote.opening.hatchery?.eggs_discarded_status}
                                  />
                                </td>
                              )}
                              <td className="py-1 pr-3"><Metric value={lote.opening.chicks_hatched ?? null} status={lote.opening.chicks_hatched_status} /></td>
                              <td className="py-1 pr-3"><Metric value={lote.current?.chicks_available ?? null} /></td>
                            </>
                          ) : (
                            <>
                              <td className="py-1 pr-3 tabular-nums">{lote.opening.live.toLocaleString()}</td>
                              <td className="py-1 pr-3"><Metric value={lote.opening.historical_mortality} status={lote.opening.mortality_status} /></td>
                              <td className="py-1 pr-3 tabular-nums">{lote.post.mortality.toLocaleString()}</td>
                              <td className="py-1 pr-3"><Metric value={lote.lifetime.mortality} /></td>
                              <td className="py-1 pr-3"><Metric value={lote.opening.historical_culls ?? null} status={lote.opening.culls_status} /></td>
                              <td className="py-1 pr-3"><Metric value={lote.opening.feed_kg ?? null} status={lote.opening.feed_status} /></td>
                              {batch.business_unit !== 'broiler' && (
                                <td className="py-1 pr-3"><Metric value={lote.opening.egg_production ?? null} status={lote.opening.egg_production_status} /></td>
                              )}
                              <td className="py-1 pr-3 font-semibold tabular-nums">{lote.current_live.toLocaleString()}</td>
                            </>
                          )}
                          <td className="py-1 pr-3 whitespace-nowrap">
                            <Link className="text-brand-700 hover:underline mr-3" to={`/lots/${lote.lot_id}`}>{t('cutover.viewLot')}</Link>
                            <Link className="text-brand-700 hover:underline" to={`/operations/new?lot_id=${lote.lot_id}`}>{t('cutover.firstEvent')}</Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-sm flex flex-wrap items-center justify-between gap-3" data-testid="cutover-applied">
                  <div>
                    <div className="font-semibold text-emerald-900">{t('cutover.appliedTitle')}</div>
                    <div className="text-emerald-800">{t('cutover.appliedHint')} {t('cutover.cutoverDateRule')}</div>
                  </div>
                  <Button onClick={() => navigate('/operations/new')}>
                    {t('cutover.continueOps')}<ArrowRight className="w-4 h-4 ml-1" aria-hidden />
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
