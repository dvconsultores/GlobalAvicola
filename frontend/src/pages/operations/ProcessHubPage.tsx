import { useTranslation } from 'react-i18next'
import { Sparkles } from 'lucide-react'
import { PROCESS_STAGES, flowForStage } from '../../data/processCatalog'
import { ProcessCard } from '../../components/operations'

/**
 * Process hub — the main, visual entry point for registering operations.
 * The user picks a production stage (Incubadora, Reproductoras, etc.) and
 * is taken to that stage's ordered list of operations.
 * 
 * REDESIGN: Enhanced visual layout with improved typography, spacing,
 * and modern card design for better intuitiveness and mobile experience.
 */
export default function ProcessHubPage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-800">
      {/* Header Section */}
      <div className="p-4 sm:p-6 max-w-5xl mx-auto">
        <header className="mb-8 text-center sm:text-left">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={24} className="text-blue-600 dark:text-blue-400" />
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-slate-100">
              {t('process.hub.title', 'Procesos de Producción')}
            </h1>
          </div>
          <p className="text-base text-slate-600 dark:text-slate-400 mt-3 max-w-2xl">
            {t('process.hub.subtitle', 'Elige un proceso para registrar operaciones')}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
            {t('process.hub.totalProcesses', '6 procesos principales')} • {PROCESS_STAGES.reduce((acc, s) => acc + flowForStage(s.key).length, 0)} {t('process.hub.totalOperations', 'operaciones')}
          </p>
        </header>

        {/* Process Grid - 3 columns desktop, 1 column mobile */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {PROCESS_STAGES.map(process => {
            const operationCount = flowForStage(process.key).length
            return (
              <ProcessCard
                key={process.key}
                process={process}
                operationCount={operationCount}
              />
            )
          })}
        </div>

        {/* Footer Help Text */}
        <div className="mt-10 p-5 bg-blue-50 dark:bg-slate-700 border-2 border-blue-200 dark:border-slate-600 rounded-xl text-center">
          <p className="text-sm text-blue-900 dark:text-slate-100 font-medium">
            💡 {t('process.hub.hint', 'Toca cualquier proceso para ver el flujo de operaciones disponibles')}
          </p>
        </div>
      </div>
    </div>
  )
}
