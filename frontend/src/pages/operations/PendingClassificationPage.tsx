/**
 * Bandeja de **pendientes de clasificar** (`spec 015 §5` · `AC-S1-T02`, `GA-REM-040 §11`).
 *
 * Pantalla de **solo lectura** a propósito: clasificar exige el id interno de la habilitación
 * de empresa, que la API de unidades no expone (decisión de seguridad `GA-REM-040`). Aquí el
 * autor ve sus registros sin cadena productiva inequívoca y el control autorizado ve los de su
 * empresa, con los nombres ya resueltos, para saber a quién pedir la clasificación.
 */
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ClipboardX } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import BackNavigation from '../../components/layout/BackNavigation'
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

export default function PendingClassificationPage() {
  const { t } = useTranslation()
  const [filas, setFilas] = useState<Pendiente[]>([])
  const [loading, setLoading] = useState(true)
  // `R-212` · AC-04: denegación ≠ vacío.
  const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

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
            'Estos registros no tienen una cadena productiva inequívoca (por ejemplo, una inspección de una granja con lotes de varias cadenas). Se muestran aquí hasta que un administrador los clasifique; no aparecen en el historial normal.')}
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
          <div className="hidden lg:grid lg:grid-cols-6 lg:gap-3 px-4 py-2 bg-slate-50 text-xs font-semibold text-slate-600">
            <span>{t('operations.pendingClassification.columns.type', 'Tipo de registro')}</span>
            <span>{t('operations.pendingClassification.columns.date', 'Fecha del evento')}</span>
            <span>{t('operations.pendingClassification.columns.farm', 'Granja')}</span>
            <span>{t('operations.pendingClassification.columns.house', 'Galpón')}</span>
            <span>{t('operations.pendingClassification.columns.registeredBy', 'Registrado por')}</span>
            <span>{t('operations.pendingClassification.columns.status', 'Estado')}</span>
          </div>
          {filas.map((ev) => (
            <div
              key={ev.id}
              data-testid="pending-row"
              className="px-4 py-3 lg:grid lg:grid-cols-6 lg:gap-3 lg:items-center"
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
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
