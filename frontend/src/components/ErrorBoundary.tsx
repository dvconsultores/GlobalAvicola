import { Component, useState } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, RotateCcw, RefreshCw } from 'lucide-react'

/**
 * R-215 · límite de error global.
 *
 * Sin esto, una excepción de render (p. ej. React #31 al pintar un `detail` de
 * FastAPI sin normalizar) dejaba la aplicación completa en blanco. El boundary
 * captura, registra `console.error` **sin PII** (C-05) y ofrece recuperación:
 * «Reintentar» (remonta el árbol) y «Recargar la página».
 *
 * C-02: se decide **solo global**; el boundary por sección (p. ej. envolviendo
 * `<Outlet/>` en `AppLayout`) queda evaluado y descartado por ahora.
 */
interface Etiquetas {
  title: string
  retry: string
  reload: string
}

interface InnerProps {
  labels: Etiquetas
  onRetry: () => void
  children: ReactNode
}

interface InnerState {
  hasError: boolean
}

class BoundaryInner extends Component<InnerProps, InnerState> {
  state: InnerState = { hasError: false }

  static getDerivedStateFromError(): InnerState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    // C-05: solo el mensaje técnico — nunca payloads ni datos de usuario.
    console.error('[ErrorBoundary] Excepción de render capturada:', error?.message ?? 'desconocida')
  }

  render() {
    if (this.state.hasError) {
      const { labels, onRetry } = this.props
      return (
        <div role="alert" className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
          <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl shadow-sm p-6 text-center">
            <AlertTriangle size={36} className="mx-auto text-amber-500" aria-hidden="true" />
            <h1 className="mt-3 text-lg font-semibold text-slate-800">{labels.title}</h1>
            <div className="mt-5 flex flex-col sm:flex-row gap-2 justify-center">
              <button
                onClick={onRetry}
                className="inline-flex items-center justify-center gap-1.5 bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition"
              >
                <RotateCcw size={15} aria-hidden="true" /> {labels.retry}
              </button>
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center justify-center gap-1.5 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition"
              >
                <RefreshCw size={15} aria-hidden="true" /> {labels.reload}
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export function ErrorBoundary({ children }: { children: ReactNode }) {
  const { t } = useTranslation()
  const [intento, setIntento] = useState(0)
  return (
    <BoundaryInner
      key={intento}
      onRetry={() => setIntento(n => n + 1)}
      labels={{
        title: t('boundary.title', 'Se produjo un error inesperado'),
        retry: t('boundary.retry', 'Reintentar'),
        reload: t('boundary.reload', 'Recargar la página'),
      }}
    >
      {children}
    </BoundaryInner>
  )
}
