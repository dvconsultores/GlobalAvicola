import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { X, AlertTriangle } from 'lucide-react'

interface ConfirmDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'primary' | 'danger' | 'success'
  loading?: boolean
  /** Mostrar icono de advertencia */
  showWarning?: boolean
}

const VARIANT_STYLES = {
  primary: { bg: 'bg-blue-600 hover:bg-blue-700', focus: 'focus:ring-blue-500' },
  danger: { bg: 'bg-red-600 hover:bg-red-700', focus: 'focus:ring-red-500' },
  success: { bg: 'bg-emerald-600 hover:bg-emerald-700', focus: 'focus:ring-emerald-500' },
}

/**
 * ConfirmDialog — Modal de confirmación estandarizado.
 *
 * Uso: antes de aprobar, rechazar, eliminar o enviar a SAP.
 */
export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel,
  cancelLabel,
  variant = 'primary',
  loading = false,
  showWarning = false,
}: ConfirmDialogProps) {
  const { t } = useTranslation()
  const confirmRef = useRef<HTMLButtonElement>(null)
  const styles = VARIANT_STYLES[variant]

  // Cerrar con Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose, loading])

  // Enfocar botón de confirmar al abrir
  useEffect(() => {
    if (open) setTimeout(() => confirmRef.current?.focus(), 50)
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={loading ? undefined : onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-dark-card rounded-2xl shadow-xl w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          disabled={loading}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50"
          aria-label={t('common.close', 'Cerrar')}
        >
          <X size={18} />
        </button>

        {/* Icono de advertencia */}
        {showWarning && (
          <div className="mx-auto w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mb-4">
            <AlertTriangle size={24} className="text-amber-600" />
          </div>
        )}

        {/* Title */}
        <h2 id="confirm-title" className="text-lg font-bold text-slate-900 dark:text-slate-200 text-center mb-2">
          {title}
        </h2>

        {/* Message */}
        <p className="text-sm text-slate-600 dark:text-slate-400 text-center mb-6">
          {message}
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 h-11 rounded-lg border border-slate-300 dark:border-slate-600 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            {cancelLabel || t('common.cancel', 'Cancelar')}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            disabled={loading}
            className={`flex-1 h-11 rounded-lg text-sm font-semibold text-white transition-all disabled:opacity-50 ${styles.bg} ${styles.focus} focus:outline-none focus:ring-2 focus:ring-offset-2`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {t('common.saving', 'Guardando...')}
              </span>
            ) : (
              confirmLabel || t('common.confirm', 'Confirmar')
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
