import { useTranslation } from 'react-i18next'
import { AlertTriangle, RefreshCw, ShieldOff } from 'lucide-react'

/** `R-212` · AC-04: denegación ≠ vacío. Estado reutilizable para listas y detalles:
 * «prohibido» (403) y «error» (resto) con reintento explícito. */
export type ErrorStateKind = 'prohibido' | 'error'

export default function ErrorState({ kind, onRetry }: { kind: ErrorStateKind; onRetry?: () => void }) {
 const { t } = useTranslation()
 const prohibido = kind === 'prohibido'
 return (
 <div
 role="alert"
 data-estado={kind}
 className={`rounded-xl border p-6 text-center ${prohibido ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'}`}
 >
 {prohibido
 ? <ShieldOff size={28} className="mx-auto text-amber-500 mb-2" />
 : <AlertTriangle size={28} className="mx-auto text-red-500 mb-2" />}
 <p className={`text-sm font-medium ${prohibido ? 'text-amber-800' : 'text-red-700'}`}>
 {prohibido
 ? t('common.forbidden', 'Permiso requerido para ver esta sección')
 : t('common.loadError', 'No se pudieron cargar los datos')}
 </p>
 {onRetry && (
 <button
 type="button"
 onClick={onRetry}
 className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#1E3A5F] hover:underline"
 >
 <RefreshCw size={14} aria-hidden="true" /> {t('common.retry', 'Reintentar')}
 </button>
 )}
 </div>
 )
}
