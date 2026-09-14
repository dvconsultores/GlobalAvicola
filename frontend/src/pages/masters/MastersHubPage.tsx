import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface MastersHubPageProps {
  entities?: { entity: string; title: string }[]
}

/**
 * `R-196` (AC-07, F G-01). Selector de entidades de maestros.
 *
 * Antes, `/masters` redirigía fijo a `farms` y las otras veinte entidades solo
 * eran alcanzables escribiendo la URL. La lista llega como prop desde `App`
 * (fuente única de rutas/columnas: sin duplicar la configuración).
 */
export default function MastersHubPage({ entities = [] }: MastersHubPageProps) {
  const { t } = useTranslation()
  return (
    <div className="py-4 sm:py-6">
      <h1 className="text-2xl font-bold text-[#1E3A5F] mb-2">
        {t('masters.hubTitle', 'Maestros')}
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        {t('masters.hubHint', 'Elegí una entidad para administrarla.')}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {entities.map((m) => (
          <Link
            key={m.entity}
            to={`/masters/${m.entity}`}
            className="bg-white border border-slate-200 rounded-xl p-4 text-sm font-medium text-[#1E3A5F] hover:border-blue-300 hover:bg-blue-50 transition"
          >
            {t(m.title)}
          </Link>
        ))}
      </div>
    </div>
  )
}
