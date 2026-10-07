import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { AlertTriangle, CheckCircle, Database, Lock, RefreshCw, ShieldCheck } from 'lucide-react'
import { Badge } from '../../components/ui'
import { formatFechaHora } from '../../utils/dates'

/**
 * SPEC 005 · Estado del inbound SAP HANA Cloud (solo lectura).
 *
 * La pantalla muestra lo que el backend afirma, ni más ni menos: «configurado» no es
 * «conectado», y un simulador local se anuncia como tal. Nunca recibe —ni podría mostrar—
 * host, usuario o contraseña: la API solo entrega los NOMBRES de las variables que faltan.
 */
export type InboundStatus =
  | 'PENDING_CREDENTIALS' | 'TLS_POLICY_VIOLATION' | 'CONFIGURED_NOT_TESTED'
  | 'CONNECTED' | 'SIMULATED_CONNECTED' | 'CONNECTION_FAILED'

export interface InboundReadiness {
  status?: InboundStatus
  configured?: boolean
  connected?: boolean
  simulated?: boolean
  missing?: string[]
  error_code?: string | null
  write_operations_allowed?: boolean
}

export interface InboundJob {
  id: number
  object_type: string
  status: string
  rows_read: number
  rows_raw: number
  rows_promoted: number
  rows_pending_mapping: number
  error_code?: string | null
  error_message?: string | null
  completed_at?: string | null
}

const STATUS_FALLBACK: Record<InboundStatus, string> = {
  PENDING_CREDENTIALS: 'Pendiente de credenciales',
  TLS_POLICY_VIOLATION: 'Configuración TLS no válida',
  CONFIGURED_NOT_TESTED: 'Configurado · sin probar',
  CONNECTED: 'Conectado',
  SIMULATED_CONNECTED: 'Simulador local (no es SAP)',
  CONNECTION_FAILED: 'Sin conexión',
}

/** Traducción de una clave dinámica: con claves calculadas `t` no devuelve `string` a secas. */
export function tr(t: TFunction, clave: string, porDefecto: string): string {
  return String(t(clave, porDefecto))
}

export function inboundStatusLabel(t: TFunction, status?: InboundStatus): string {
  const clave = status ?? 'PENDING_CREDENTIALS'
  return tr(t, `sap.inbound.status.${clave}`, STATUS_FALLBACK[clave])
}

export function inboundStatusTone(status?: InboundStatus): string {
  if (status === 'CONNECTED') return 'bg-emerald-50 text-emerald-700'
  if (status === 'SIMULATED_CONNECTED') return 'bg-sky-50 text-sky-700'
  if (status === 'CONFIGURED_NOT_TESTED') return 'bg-slate-100 text-slate-600'
  if (status === 'PENDING_CREDENTIALS') return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-700'
}

export function jobVariant(status: string): 'approved' | 'rejected' | 'pending' {
  if (status === 'completed') return 'approved'
  if (status === 'failed') return 'rejected'
  return 'pending'
}

interface Props {
  readiness: InboundReadiness | null
  jobs: InboundJob[]
  outboundEnabled: boolean
  canSync: boolean
  syncing: boolean
  onSync: () => void
}

export default function SapInboundPanel({ readiness, jobs, outboundEnabled, canSync, syncing, onSync }: Props) {
  const { t, i18n } = useTranslation()
  const status = readiness?.status
  const ultima = jobs.find(j => j.status === 'completed' && j.completed_at)
  const listo = !!readiness?.configured

  return (
    <section
      aria-label={t('sap.inbound.title', 'SAP HANA Cloud · solo lectura')}
      className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 mb-6"
    >
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-sm font-bold text-slate-700 inline-flex items-center gap-2">
            <Database size={16} /> {t('sap.inbound.title', 'SAP HANA Cloud · solo lectura')}
          </h2>
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <span
              data-testid="sap-inbound-status"
              data-status={status ?? 'PENDING_CREDENTIALS'}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full ${inboundStatusTone(status)}`}
            >
              {readiness?.connected ? <CheckCircle size={14} /> : <AlertTriangle size={14} />}
              {inboundStatusLabel(t, status)}
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-slate-100 text-slate-600">
              <ShieldCheck size={14} /> {t('sap.inbound.readOnly', 'Solo lectura · sin escritura a SAP')}
            </span>
            {!outboundEnabled && (
              <span
                data-testid="sap-outbound-disabled"
                className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-slate-100 text-slate-600"
              >
                <Lock size={14} /> {t('sap.inbound.outboundDisabled', 'Envío a SAP deshabilitado en esta fase')}
              </span>
            )}
          </div>

          {!!readiness?.missing?.length && (
            <p className="text-xs text-amber-700 mt-3">
              {t('sap.inbound.missing', 'Configuración incompleta. Faltan:')}{' '}
              <span className="font-mono">{readiness.missing.join(', ')}</span>
            </p>
          )}
          {readiness?.simulated && (
            <p className="text-xs text-sky-700 mt-3">
              {t('sap.inbound.simulatedHint', 'Datos de un simulador local. No hay conexión con SAP real.')}
            </p>
          )}
          {status === 'CONNECTION_FAILED' && readiness?.error_code && (
            <p className="text-xs text-red-600 mt-3 font-mono">{readiness.error_code}</p>
          )}
          <p className="text-xs text-slate-500 mt-3">
            {t('sap.inbound.lastSync', 'Última sincronización')}:{' '}
            {ultima?.completed_at
              ? formatFechaHora(ultima.completed_at, i18n.language)
              : t('sap.inbound.never', 'Nunca')}
          </p>
        </div>

        {canSync && (
          <button
            type="button"
            data-testid="sap-inbound-sync"
            onClick={onSync}
            disabled={!listo || syncing}
            title={!listo ? t('sap.inbound.syncDisabledHint', 'Disponible cuando la conexión esté configurada') : undefined}
            className="bg-[#1E3A5F] text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-800 transition inline-flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? t('sap.inbound.syncing', 'Sincronizando…') : t('sap.inbound.sync', 'Sincronizar')}
          </button>
        )}
      </div>
    </section>
  )
}

interface ObjectsProps {
  objects: any[]
  jobs: InboundJob[]
}

/** Catálogo de objetos con el resultado de su última sincronización. */
export function SapInboundObjects({ objects, jobs }: ObjectsProps) {
  const { t } = useTranslation()
  const ultimoPor = new Map<string, InboundJob>()
  for (const j of jobs) if (!ultimoPor.has(j.object_type)) ultimoPor.set(j.object_type, j)

  if (objects.length === 0) {
    return <p className="text-sm text-slate-500 text-center py-8">{t('sap.inbound.noObjects', 'Sin objetos')}</p>
  }
  return (
    <div className="divide-y divide-slate-100">
      {objects.map((o: any) => {
        const job = ultimoPor.get(o.object_type)
        return (
          <div key={o.object_type} data-testid={`sap-inbound-object-${o.object_type}`}
            className="py-3 px-2 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-700">
                {tr(t, `sap.inbound.objects.${o.object_type}`, o.object_type)}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {job
                  ? `${job.rows_read} ${t('sap.inbound.read', 'leídos')} · ${job.rows_promoted} ${t('sap.inbound.promoted', 'promovidos')}` +
                    (job.rows_pending_mapping ? ` · ${job.rows_pending_mapping} ${t('sap.inbound.pendingMapping', 'sin mapping')}` : '')
                  : t('sap.inbound.notSynced', 'Sin sincronizar')}
              </p>
              {job?.error_code && <p className="text-xs text-red-600 mt-0.5 font-mono">{job.error_code}</p>}
            </div>
            {job && <Badge variant={jobVariant(job.status)} size="sm">{tr(t, `sap.inbound.job.${job.status}`, job.status)}</Badge>}
          </div>
        )
      })}
    </div>
  )
}

/** Registros sincronizados (RAW vigente) con su estado de mapping y promoción. */
export function SapInboundRecords({ records }: { records: any[] }) {
  const { t } = useTranslation()
  if (records.length === 0) {
    return <p className="text-sm text-slate-500 text-center py-8">{t('sap.inbound.noRecords', 'Sin registros sincronizados')}</p>
  }
  return (
    <div className="divide-y divide-slate-100">
      {records.map((r: any) => (
        <div key={r.id} className="py-3 px-2 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-700 font-mono truncate">{r.source_key}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {tr(t, `sap.inbound.objects.${r.object_type}`, r.object_type)} · v{r.version}
            </p>
          </div>
          <Badge variant={r.promotion_status === 'PROMOTED' ? 'approved' : r.error_code ? 'rejected' : 'pending'} size="sm">
            {tr(t, `sap.inbound.promotion.${r.promotion_status}`, r.promotion_status)}
          </Badge>
        </div>
      ))}
    </div>
  )
}

/** Registros retenidos o inválidos y jobs fallidos. El backend ya entrega los mensajes saneados. */
export function SapInboundErrors({ records, jobs }: { records: any[]; jobs: InboundJob[] }) {
  const { t } = useTranslation()
  if (records.length === 0 && jobs.length === 0) {
    return (
      <div className="text-center py-8">
        <CheckCircle size={32} className="mx-auto text-emerald-300 mb-2" />
        <p className="text-sm text-slate-500">{t('sap.inbound.noErrors', 'Sin errores de sincronización')}</p>
      </div>
    )
  }
  return (
    <div className="divide-y divide-slate-100">
      {jobs.map(j => (
        <div key={`job-${j.id}`} className="py-3 px-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium text-slate-700">
              {tr(t, `sap.inbound.objects.${j.object_type}`, j.object_type)} · #{j.id}
            </p>
            <Badge variant="rejected" size="sm">{j.error_code || j.status}</Badge>
          </div>
          {j.error_message && <p className="text-xs text-red-600 mt-1">{j.error_message}</p>}
        </div>
      ))}
      {records.map((r: any) => (
        <div key={`rec-${r.id}`} className="py-3 px-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium text-slate-700 font-mono truncate">{r.source_key}</p>
            <Badge variant="pending" size="sm">{r.error_code}</Badge>
          </div>
          {r.error_message && <p className="text-xs text-slate-500 mt-1">{r.error_message}</p>}
        </div>
      ))}
    </div>
  )
}
