import { useTranslation } from 'react-i18next'

import type { FaseDelLote } from '../../utils/semanaProductiva'

/**
 * `SPEC 020 §6` · `RR-30`: la semana la deriva el servidor de la edad del lote; aquí solo se
 * muestra («Semana N»). No es un campo editable: no hay forma de tapar la derivación con un número.
 */
export function SemanaDerivada({ semana }: { semana: number | null }) {
  const { t } = useTranslation()
  return (
    <div data-testid="derived-week" aria-live="polite"
      className="w-full h-10 px-3 flex items-center border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-700">
      {semana !== null
        ? t('operations.derivedWeek', { n: semana })
        : t('operations.derivedWeekPending')}
    </div>
  )
}

/**
 * `SPEC 020 §6` · `RR-34`: la fase del alimento es la fase productiva vigente del lote en la fecha
 * del evento. Sin fase vigente se avisa; no se pide al operador que la corrija a mano.
 */
export function FaseDerivada({ fase, lotElegido }: { fase: FaseDelLote | null; lotElegido: boolean }) {
  const { t } = useTranslation()
  const nombre = fase?.phase?.name || fase?.phase?.code || (fase ? `#${fase.phase_id}` : '')
  return (
    <div data-testid="derived-phase" aria-live="polite"
      className={`w-full min-h-10 px-3 py-2 flex items-center border rounded-lg text-sm ${
        fase || !lotElegido ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-amber-300 bg-amber-50 text-amber-800'}`}>
      {fase
        ? t('operations.derivedPhase', { name: nombre })
        : (lotElegido ? t('operations.derivedPhaseNone') : t('operations.derivedWeekPending'))}
    </div>
  )
}
