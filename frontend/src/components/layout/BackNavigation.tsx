import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft } from 'lucide-react'
import ConfirmDialog from '../ui/ConfirmDialog'
import { useUnsavedChangesGuard } from '../../hooks/useUnsavedChangesGuard'

/**
 * `specs/004-frontend-navigation-ui-consistency-remediation` · NAV-01 / UX-01.
 *
 * Botón «Volver» CANÓNICO de pantallas secundarias. Reemplaza las siete
 * variantes ad-hoc detectadas en la auditoría (icono solo, «← texto», links con
 * icono, botón aria…) por un único componente consistente:
 *
 *  - icono + texto (nunca solo icono), i18n `common.back` («Volver»/«Back»);
 *  - posición uniforme: primera fila del contenido de la página;
 *  - accesible: `aria-label`, `data-testid="back-navigation"`, altura táctil ≥36px;
 *  - mobile/desktop: mismo comportamiento.
 *
 * Resolución del destino (contrato NAV, nunca depende solo de `navigate(-1)`):
 *  1. `to` — parent route-aware declarado por la pantalla;
 *  2. historial interno de la SPA (si existe);
 *  3. `fallbackTo` — ruta canónica del módulo (deep-link seguro).
 */
export interface BackNavigationProps {
  /** Ruta padre explícita (preferida). */
  to?: string
  /** Ruta canónica de módulo cuando no hay `to` ni historial interno. */
  fallbackTo?: string
  /** Texto alternativo (por defecto `common.back`). */
  label?: string
  /** Hay cambios sin guardar: confirmar antes de salir. */
  dirty?: boolean
  /** Se ejecuta al confirmar la salida (limpieza de estado local, etc.). */
  onDiscard?: () => void
  className?: string
}

/** ¿Existe historial INTERNO de la SPA? (deep-link directo: `key === 'default'`). */
export function canGoBackInApp(locationKey: string): boolean {
  try {
    const state = window.history.state as { idx?: number } | null
    if (state && typeof state.idx === 'number') return state.idx > 0
  } catch {
    /* historial no accesible (jsdom / sandbox) */
  }
  return locationKey !== 'default'
}

export default function BackNavigation({
  to,
  fallbackTo = '/',
  label,
  dirty = false,
  onDiscard,
  className,
}: BackNavigationProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const guard = useUnsavedChangesGuard(dirty)
  const [text] = useState(() => label ?? t('common.back', 'Volver'))

  const proceed = () => {
    onDiscard?.()
    if (to) {
      navigate(to)
      return
    }
    if (canGoBackInApp(location.key)) {
      navigate(-1)
      return
    }
    navigate(fallbackTo)
  }

  const handleClick = () => {
    // `requestRouteLeave` muestra la confirmación solo si hay cambios sin guardar.
    guard.requestRouteLeave(proceed)
  }

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        data-testid="back-navigation"
        aria-label={text}
        className={`inline-flex items-center gap-1.5 min-h-9 -ml-1 px-2 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:text-[#5a9bba] hover:bg-blue-50 transition-colors active:scale-95 ${className ?? ''}`}
      >
        <ArrowLeft size={16} aria-hidden="true" />
        <span>{text}</span>
      </button>

      <ConfirmDialog
        open={guard.confirmOpen}
        onClose={guard.stay}
        onConfirm={guard.confirmLeave}
        title={t('common.unsavedChangesTitle', 'Cambios sin guardar')}
        message={t('common.unsavedChangesMessage', 'Si sales ahora, los cambios no guardados se perderán.')}
        confirmLabel={t('common.discardChanges', 'Salir sin guardar')}
        cancelLabel={t('common.stayOnPage', 'Quedarme')}
        variant="danger"
        showWarning
      />
    </>
  )
}
