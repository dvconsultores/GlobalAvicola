/**
 * Bandeja de **pendientes de clasificar** (`spec 015 §5` · `AC-S1-T02`, `GA-REM-040 §11`) y
 * superficie de **clasificación** (`SPEC 016 §A` · `O-3`).
 *
 * Ver NO es clasificar (`GA-REM-040`): la lista la ve el autor de los registros y el control
 * autorizado de la empresa; la acción de fijar la cadena productiva exige `masters:update`.
 * Quien no tiene ese permiso ve exactamente la misma bandeja sin botón, y el backend sigue
 * siendo la autoridad final (403/404 aunque la UI se equivoque).
 *
 * La unidad se elige por su **código** (`code` canónico) y se muestra como
 * `Código — Descripción`: el id interno de la habilitación de empresa nunca llega a la UI.
 */
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ClipboardX } from 'lucide-react'
import api from '../../services/api'
import { operationsService, type ClassificationCandidate } from '../../services/operations.service'
import ErrorState from '../../components/ui/ErrorState'
import { Button, Modal } from '../../components/ui'
import BackNavigation from '../../components/layout/BackNavigation'
import { useToast } from '../../components/Toast'
import { useAuthStore } from '../../stores/auth.store'
import { hasPermission } from '../../auth/permissions'
import { businessUnitName } from '../../data/businessUnits'
import { formatFecha } from '../../utils/dates'

interface Pendiente {
  id: number
  event_type: string
  event_date?: string | null
  status?: string | null
  farm_name?: string | null
  house_name?: string | null
  registered_by_name?: string | null
}

/** Contrato del backend (`ClassificationRequest`): 3 caracteres tras `trim`. */
const MOTIVO_MIN = 3

type EstadoCandidatos = 'idle' | 'loading' | 'ok' | 'error'

export default function PendingClassificationPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const sessionUser = useAuthStore((s) => s.user)
  const canClassify = hasPermission(sessionUser, 'masters:update')

  const [filas, setFilas] = useState<Pendiente[]>([])
  const [loading, setLoading] = useState(true)
  // `R-212` · AC-04: denegación ≠ vacío.
  const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

  // ── Diálogo de clasificación (`SPEC 016 §A` · `O-3`) ───────────────────────────────
  const [seleccion, setSeleccion] = useState<Pendiente | null>(null)
  const [candidatos, setCandidatos] = useState<ClassificationCandidate[]>([])
  const [candidatosEstado, setCandidatosEstado] = useState<EstadoCandidatos>('idle')
  const [candidatosError, setCandidatosError] = useState<string | null>(null)
  const [unidad, setUnidad] = useState('')
  const [motivo, setMotivo] = useState('')
  const [motivoTocado, setMotivoTocado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorServidor, setErrorServidor] = useState<string | null>(null)
  const [errorCliente, setErrorCliente] = useState<string | null>(null)

  const fetchPendientes = useCallback(async () => {
    setLoading(true)
    try {
      const r = await api.get('/operations/pending-classification', { params: { limit: 100 } })
      const cuerpo = r.data
      setFilas(Array.isArray(cuerpo) ? cuerpo : (cuerpo?.items ?? []))
      setEstado('ok')
    } catch (err: any) {
      setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPendientes() }, [fetchPendientes])

  const cargarCandidatos = useCallback(async (eventId: number) => {
    setCandidatosEstado('loading')
    setCandidatosError(null)
    setCandidatos([])
    try {
      const r = await operationsService.getClassificationCandidates(eventId)
      setCandidatos(Array.isArray(r.data) ? r.data : [])
      setCandidatosEstado('ok')
    } catch (err: any) {
      // 404: el registro dejó de estar pendiente entre la lista y el clic.
      setCandidatosError(
        err?.response?.status === 404
          ? t('operations.pendingClassification.dialog.gone', 'El registro ya no está pendiente de clasificar')
          : t('operations.pendingClassification.dialog.candidatesError', 'No se pudieron cargar las unidades disponibles'),
      )
      setCandidatosEstado('error')
    }
  }, [t])

  const abrirDialogo = (ev: Pendiente) => {
    setSeleccion(ev)
    setUnidad('')
    setMotivo('')
    setMotivoTocado(false)
    setErrorServidor(null)
    setErrorCliente(null)
    void cargarCandidatos(ev.id)
  }

  const cerrarDialogo = () => {
    if (enviando) return
    setSeleccion(null)
  }

  const motivoLimpio = motivo.trim()
  const motivoValido = motivoLimpio.length >= MOTIVO_MIN
  const formularioValido = Boolean(unidad) && motivoValido

  const clasificar = async () => {
    if (!seleccion || enviando) return
    const limpio = motivo.trim()
    // Validación de cliente: un motivo corto no llega al servidor (422 evitable).
    if (!unidad || limpio.length < MOTIVO_MIN) {
      setErrorCliente(t('operations.pendingClassification.dialog.reasonTooShort',
        'El motivo debe tener al menos 3 caracteres'))
      return
    }
    setErrorCliente(null)
    setErrorServidor(null)
    setEnviando(true)
    try {
      await operationsService.classifyEvent(seleccion.id, {
        business_unit_code: unidad,
        reason: limpio,
      })
      const nombre = businessUnitName(unidad, candidatos.find((c) => c.code === unidad)?.name_key ?? undefined, t)
      setSeleccion(null)
      toast.success(t('operations.pendingClassification.dialog.success',
        'Registro clasificado en {{unit}}', { unit: nombre }))
      // La fila ya no es un pendiente: se reconcilia con el backend, sin optimismo.
      await fetchPendientes()
    } catch (err: any) {
      const status = err?.response?.status
      if (status === 404) {
        setErrorServidor(t('operations.pendingClassification.dialog.gone',
          'El registro ya no está pendiente de clasificar'))
        await fetchPendientes()
      } else if (status === 400) {
        const detalle = err?.response?.data?.detail
        setErrorServidor(typeof detalle === 'string' && detalle.trim()
          ? detalle
          : t('operations.pendingClassification.dialog.classifyError', 'No se pudo clasificar el registro'))
      } else {
        // 422 y cualquier otro: mensaje propio en español, nunca el JSON crudo del servidor.
        setErrorServidor(t('operations.pendingClassification.dialog.classifyError',
          'No se pudo clasificar el registro'))
      }
    } finally {
      setEnviando(false)
    }
  }

  const columnas = canClassify ? 'lg:grid-cols-7' : 'lg:grid-cols-6'

  return (
    <div className="py-4 sm:py-6" data-testid="pending-classification-page">
      <BackNavigation to="/operations" />

      <div className="mt-2 mb-6">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <ClipboardX size={22} className="text-slate-400" aria-hidden="true" />
          {t('operations.pendingClassification.title', 'Pendientes de clasificar')}
        </h1>
        <p className="text-sm text-slate-500 max-w-3xl mt-1">
          {t('operations.pendingClassification.intro',
            'Estos registros no tienen una cadena productiva inequívoca (por ejemplo, una inspección de una granja con lotes de varias cadenas). Quedan fuera del historial normal hasta que se clasifiquen; si tienes permiso de administración de datos maestros, puedes clasificarlos aquí.')}
        </p>
      </div>

      {estado !== 'ok' ? (
        <ErrorState kind={estado} onRetry={fetchPendientes} />
      ) : loading ? (
        <p className="text-slate-500 text-sm py-8 text-center">{t('common.loading', 'Cargando...')}</p>
      ) : filas.length === 0 ? (
        <p className="text-slate-400 text-sm py-8 text-center">
          {t('operations.pendingClassification.empty', 'No hay registros pendientes de clasificar.')}
        </p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 divide-y divide-slate-100">
          {/* Encabezado de columnas (solo desktop). */}
          <div className={`hidden lg:grid lg:gap-3 px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-600 ${columnas}`}>
            <span>{t('operations.pendingClassification.columns.type', 'Tipo de registro')}</span>
            <span>{t('operations.pendingClassification.columns.date', 'Fecha del evento')}</span>
            <span>{t('operations.pendingClassification.columns.farm', 'Granja')}</span>
            <span>{t('operations.pendingClassification.columns.house', 'Galpón')}</span>
            <span>{t('operations.pendingClassification.columns.registeredBy', 'Registrado por')}</span>
            <span>{t('operations.pendingClassification.columns.status', 'Estado')}</span>
            {canClassify && (
              <span>{t('operations.pendingClassification.columns.actions', 'Acciones')}</span>
            )}
          </div>
          {filas.map((ev) => (
            <div
              key={ev.id}
              data-testid="pending-row"
              className={`px-4 py-3 lg:grid lg:gap-3 lg:items-center ${columnas}`}
            >
              <span className="block text-sm font-medium text-slate-700">
                {t(`eventsShort.${ev.event_type}`, ev.event_type)}
              </span>
              <span className="block text-xs text-slate-500">{formatFecha(ev.event_date)}</span>
              <span className="block text-sm text-slate-600">{ev.farm_name ?? '—'}</span>
              <span className="block text-sm text-slate-600">{ev.house_name ?? '—'}</span>
              <span className="block text-sm text-slate-600">{ev.registered_by_name ?? '—'}</span>
              <span className="block text-xs text-slate-500">
                {ev.status ? t(`status.${ev.status}`, ev.status) : '—'}
              </span>
              {canClassify && (
                <span className="mt-2 flex lg:mt-0 lg:justify-start">
                  <Button
                    variant="secondary"
                    size="sm"
                    data-testid="classify-btn"
                    onClick={() => abrirDialogo(ev)}
                  >
                    {t('operations.pendingClassification.classify', 'Clasificar')}
                  </Button>
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={Boolean(seleccion)}
        onClose={cerrarDialogo}
        title={t('operations.pendingClassification.dialog.title', 'Clasificar registro')}
        description={t('operations.pendingClassification.dialog.description',
          'Indica a qué unidad productiva pertenece este registro. La decisión queda auditada con el motivo.')}
        footer={(
          <>
            <Button variant="secondary" onClick={cerrarDialogo} disabled={enviando}>
              {t('common.cancel', 'Cancelar')}
            </Button>
            <Button
              data-testid="classify-submit"
              onClick={clasificar}
              loading={enviando}
              disabled={!formularioValido}
            >
              {t('operations.pendingClassification.classify', 'Clasificar')}
            </Button>
          </>
        )}
      >
        {seleccion && (
          <div data-testid="classify-dialog" className="space-y-4 text-left">
            {/* Contexto: el registro concreto que se va a clasificar, con nombres y sin ids. */}
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.type', 'Tipo de registro')}</dt>
                <dd className="font-medium text-slate-800">
                  {t(`eventsShort.${seleccion.event_type}`, seleccion.event_type)}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.date', 'Fecha del evento')}</dt>
                <dd className="font-medium text-slate-800">{formatFecha(seleccion.event_date)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.farm', 'Granja')}</dt>
                <dd className="font-medium text-slate-800">{seleccion.farm_name ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.house', 'Galpón')}</dt>
                <dd className="font-medium text-slate-800">{seleccion.house_name ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.registeredBy', 'Registrado por')}</dt>
                <dd className="font-medium text-slate-800">{seleccion.registered_by_name ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">{t('operations.pendingClassification.columns.status', 'Estado')}</dt>
                <dd className="font-medium text-slate-800">
                  {seleccion.status ? t(`status.${seleccion.status}`, seleccion.status) : '—'}
                </dd>
              </div>
            </dl>

            {candidatosEstado === 'loading' && (
              <p role="status" className="text-sm text-slate-500">
                {t('operations.pendingClassification.dialog.candidatesLoading', 'Cargando unidades disponibles...')}
              </p>
            )}

            {candidatosEstado === 'error' && (
              <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2">
                <p className="text-sm text-red-700">{candidatosError}</p>
                <button
                  type="button"
                  onClick={() => void cargarCandidatos(seleccion.id)}
                  className="mt-1 text-sm font-medium text-[#1E3A5F] hover:underline"
                >
                  {t('common.retry', 'Reintentar')}
                </button>
              </div>
            )}

            {candidatosEstado === 'ok' && candidatos.length === 0 && (
              <p role="alert" className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {t('operations.pendingClassification.dialog.noCandidates', 'La empresa no tiene unidades habilitadas')}
              </p>
            )}

            {candidatos.length > 0 && (
              <div>
                <label htmlFor="classify-unit" className="block text-sm font-semibold text-slate-700 mb-1.5">
                  {t('operations.pendingClassification.dialog.unit', 'Unidad productiva')}
                </label>
                <select
                  id="classify-unit"
                  data-testid="classify-unit"
                  value={unidad}
                  onChange={(e) => setUnidad(e.target.value)}
                  disabled={enviando}
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-base text-slate-900 bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-50"
                >
                  <option value="">{t('operations.pendingClassification.dialog.unitPlaceholder', 'Seleccione una unidad')}</option>
                  {candidatos.map((c) => (
                    <option key={c.code} value={c.code}>
                      {`${c.code} — ${businessUnitName(c.code, c.name_key ?? undefined, t)}`}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label htmlFor="classify-reason" className="block text-sm font-semibold text-slate-700 mb-1.5">
                {t('operations.pendingClassification.dialog.reason', 'Motivo')}
              </label>
              <textarea
                id="classify-reason"
                data-testid="classify-reason"
                rows={3}
                value={motivo}
                onChange={(e) => { setMotivo(e.target.value); setMotivoTocado(true); setErrorCliente(null) }}
                disabled={enviando}
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-50"
              />
              {motivoTocado && !motivoValido && (
                <p role="alert" className="mt-1 text-xs text-red-600">
                  {t('operations.pendingClassification.dialog.reasonTooShort', 'El motivo debe tener al menos 3 caracteres')}
                </p>
              )}
            </div>

            {errorCliente && (
              <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {errorCliente}
              </p>
            )}
            {errorServidor && (
              <p role="alert" data-testid="classify-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {errorServidor}
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
