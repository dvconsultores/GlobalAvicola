/**
 * La evaluación de un pesaje contra la curva estándar — `AC-FE11`…`AC-FE14`.
 *
 * **Aquí no se calcula nada.** Ni interpolación, ni clasificación, ni tolerancia: el motor
 * vive en `backend/app/operations/weight_curve.py` y este componente pinta lo que aquél
 * concluyó. Dos motores acabarían discrepando y el usuario no sabría a cuál creer.
 *
 * `R-97` es la razón de que exista la lectura que alimenta esto: antes la evaluación solo
 * era observable cuando generaba alerta, de modo que «dentro de norma» y «sin referencia»
 * se veían igual —sin nada—. Y `OD-06` prohíbe la tolerancia global, así que la ausencia de
 * referencia debe **decirse**: callar equivale a afirmar que el peso es correcto.
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, CheckCircle2, HelpCircle, TrendingUp } from 'lucide-react'

import api from '../../services/api'

interface EvaluationRow {
  avg_weight: number
  status: 'below_standard' | 'within_standard' | 'above_standard' | 'no_reference'
  expected_min: number | null
  expected_target: number | null
  expected_max: number | null
}

interface Evaluation {
  event_id: number
  lot_id: number | null
  age_days: number | null
  curve_version_label: string | null
  reason: string | null
  evaluations: EvaluationRow[]
}

/** Texto, icono y color. Nunca solo color: el estado debe leerse (`AC-FE12`). */
const PRESENTACION = {
  below_standard: { clave: 'curves.below', Icono: AlertTriangle, clase: 'text-amber-700 bg-amber-50 border-amber-200' },
  above_standard: { clave: 'curves.above', Icono: TrendingUp, clase: 'text-amber-700 bg-amber-50 border-amber-200' },
  within_standard: { clave: 'curves.within', Icono: CheckCircle2, clase: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  no_reference: { clave: 'curves.noReference', Icono: HelpCircle, clase: 'text-slate-600 bg-slate-50 border-slate-200' },
} as const

export default function WeightEvaluation({ eventId }: { eventId: number }) {
  const { t } = useTranslation()
  const [datos, setDatos] = useState<Evaluation | null>(null)

  useEffect(() => {
    let vigente = true
    api.get<Evaluation>(`/operations/${eventId}/weight-evaluation`)
      .then(r => { if (vigente) setDatos(r.data) })
      .catch(() => { if (vigente) setDatos(null) })
    return () => { vigente = false }
  }, [eventId])

  if (!datos || datos.evaluations.length === 0) return null

  return (
    <div className="mt-4 pt-4 border-t">
      <h3 className="font-semibold text-sm text-slate-600 mb-2">
        {t('curves.evaluationTitle')}
        {datos.curve_version_label && (
          <span className="ml-2 font-normal text-xs text-slate-500 font-mono">
            {datos.curve_version_label}
          </span>
        )}
        {datos.age_days !== null && (
          <span className="ml-2 font-normal text-xs text-slate-500">
            {t('curves.atAge', { days: datos.age_days })}
          </span>
        )}
      </h3>

      {/* `R-220` · A5 (C#28): lo que el motor declara (p. ej. por qué no hay
 referencia) se muestra; callarlo obligaría a adivinar el motivo. */}
      {datos.reason && (
        <p className="text-xs text-slate-500 mb-2">{datos.reason}</p>
      )}

      <div className="space-y-2">
        {datos.evaluations.map((fila, i) => {
          const { clave, Icono, clase } = PRESENTACION[fila.status]
          return (
            <div key={i} className={`flex flex-wrap items-center gap-2 text-xs border rounded-lg px-3 py-2 ${clase}`}>
              <Icono size={14} aria-hidden />
              <span className="font-semibold">{t(clave)}</span>
              <span className="text-slate-600">
                {t('curves.recorded')}: <strong>{fila.avg_weight} g</strong>
              </span>
              {fila.expected_min !== null && fila.expected_max !== null ? (
                <span className="text-slate-600">
                  {t('curves.expectedRange')}: <strong>{fila.expected_min}–{fila.expected_max} g</strong>
                </span>
              ) : (
                // Sin rango no se escribe cero ni se deja el hueco: se nombra el motivo.
                <span className="text-slate-500">{t('curves.noReferenceHelp')}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
