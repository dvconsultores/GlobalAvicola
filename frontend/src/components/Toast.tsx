import { useState, useCallback, createContext, useContext, useRef } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
 id: number
 type: ToastType
 message: string
}

interface ToastContextType {
 success: (msg: string) => void
 error: (msg: string) => void
 warning: (msg: string) => void
 info: (msg: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

let toastId = 0

/**
 * `R-215 (C-03)`: red de seguridad — un mensaje no-string (p. ej. una `detail`
 * cruda de FastAPI) nunca debe romper el toast ni pintar «[object Object]».
 */
function normalizarMensaje(mensaje: unknown): string {
  if (typeof mensaje === 'string') return mensaje
  const deDetalle = textoDeDetalle(mensaje)
  if (deDetalle) return deDetalle
  const deError = getErrorMessage(mensaje, '')
  if (deError) return deError
  return String(mensaje)
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  // `F4`: espejo síncrono de los toasts visibles — dos avisos idénticos en el
  // mismo tick no deben apilarse aunque el estado aún no se haya re-renderizado.
  const visiblesRef = useRef<Toast[]>([])
  const temporizadoresRef = useRef(new Map<number, ReturnType<typeof setTimeout>>())

  const programarBorrado = useCallback((id: number) => {
    const previo = temporizadoresRef.current.get(id)
    if (previo) clearTimeout(previo)
    temporizadoresRef.current.set(id, setTimeout(() => {
      temporizadoresRef.current.delete(id)
      visiblesRef.current = visiblesRef.current.filter(t => t.id !== id)
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000))
  }, [])

  const quitar = useCallback((id: number) => {
    const temporizador = temporizadoresRef.current.get(id)
    if (temporizador) {
      clearTimeout(temporizador)
      temporizadoresRef.current.delete(id)
    }
    visiblesRef.current = visiblesRef.current.filter(t => t.id !== id)
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((type: ToastType, mensaje: unknown) => {
    const message = normalizarMensaje(mensaje)
    // Mismo `type` y mismo texto ⇒ no se apila: sólo se reinicia su temporizador.
    const repetido = visiblesRef.current.find(t => t.type === type && t.message === message)
    if (repetido) {
      programarBorrado(repetido.id)
      return
    }
    const id = ++toastId
    visiblesRef.current = [...visiblesRef.current.slice(-4), { id, type, message }]
    setToasts(visiblesRef.current)
    programarBorrado(id)
  }, [programarBorrado])

 const ctx: ToastContextType = {
 success: (msg: string) => addToast('success', msg),
 error: (msg: string) => addToast('error', msg),
 warning: (msg: string) => addToast('warning', msg),
 info: (msg: string) => addToast('info', msg),
 }

 const icons: Record<ToastType, ReactNode> = {
 success: <CheckCircle size={18} className="text-emerald-500" />,
 error: <XCircle size={18} className="text-red-500" />,
 warning: <AlertTriangle size={18} className="text-amber-500" />,
 info: <Info size={18} className="text-blue-500" />,
 }

 const bgColors: Record<ToastType, string> = {
 success: 'border-emerald-300 bg-emerald-50',
 error: 'border-red-300 bg-red-50',
 warning: 'border-amber-300 bg-amber-50',
 info: 'border-blue-300 bg-blue-50',
 }

 const textColors: Record<ToastType, string> = {
 success: 'text-emerald-800',
 error: 'text-red-800',
 warning: 'text-amber-800',
 info: 'text-blue-800',
 }

 return (
 <ToastContext.Provider value={ctx}>
 {children}
 {/* Toast container — `F8`: PORTAL sobre `document.body`. Dentro del árbol de la app el
 contenedor quedaba atrapado en un contexto de apilamiento inferior y el overlay del
 `ConfirmDialog` (z-[60], también en portal) lo tapaba: el aviso existía y no se veía. */}
 {typeof document !== 'undefined' && createPortal(
 <div
 data-testid="toast-container"
 role="status"
 aria-live="polite"
 className="fixed top-4 right-4 z-[70] flex flex-col gap-2 max-w-[calc(100vw-2rem)] sm:max-w-sm"
 >
 {toasts.map(t => (
 <div
 key={t.id}
 className={`flex items-start gap-2 px-4 py-3 rounded-lg border shadow-lg text-sm font-medium animate-slide-in ${bgColors[t.type]} ${textColors[t.type]}`}
 >
 {icons[t.type]}
 <span className="flex-1">{t.message}</span>
 <button onClick={() => quitar(t.id)} className="opacity-60 hover:opacity-100">
 <X size={14} />
 </button>
 </div>
 ))}
 </div>,
 document.body,
 )}
 </ToastContext.Provider>
 )
}

export function useToast(): ToastContextType {
 const ctx = useContext(ToastContext)
 if (!ctx) throw new Error('useToast must be used within ToastProvider')
 return ctx
}

/** Helper: extract error message from axios error. 
 * NOTE: This is a standalone function so it cannot use hooks directly.
 * Callers should pass a translated fallback using t() from their component.
 */
// `R-189 (F-01)`: el `detail` de FastAPI puede ser una lista de objetos de validación (o un objeto);
// devolverlo crudo rompía el render (React #31). Se normaliza SIEMPRE a texto renderizable.
// `F4` (AC-S1-F01/AC-S1-I02): los mensajes de validación de pydantic llegan en inglés
// («Input should be a valid integer…»); se sustituyen por un aviso en español por campo,
// sin repetir duplicados dentro del mismo detalle.
const CAMPO_EN_ES: Record<string, string> = {
  lot_id: 'lote',
  farm_id: 'granja',
  house_id: 'galpón',
  event_date: 'fecha',
  date_from: 'fecha',
  date_to: 'fecha',
}

/** Último segmento de `loc`, traducido cuando el campo es conocido. */
function etiquetaDeCampo(loc: unknown[]): string {
  const segmentos = loc.filter((p) => typeof p === 'string' || typeof p === 'number')
  if (segmentos.length === 0) return ''
  const ultimo = String(segmentos[segmentos.length - 1])
  if (!ultimo) return ''
  return CAMPO_EN_ES[ultimo] ?? ultimo
}

/** Un item de `detail` ⇒ texto en español (o el texto humano ya redactado). */
function textoDeItem(item: unknown): string | null {
  if (typeof item === 'string') return item.trim() ? item : null
  if (!item || typeof item !== 'object') return null
  const registro = item as { loc?: unknown; msg?: unknown; type?: unknown; message?: unknown }
  const mensajeHumano = typeof registro.message === 'string' ? registro.message.trim() : ''
  const tieneTipo = typeof registro.type === 'string' && registro.type !== ''
  // Un detalle ya redactado en español (mensaje propio, sin `type` de pydantic) se respeta.
  if (mensajeHumano && !tieneTipo) return mensajeHumano
  const campo = etiquetaDeCampo(Array.isArray(registro.loc) ? registro.loc : [])
  // `F6` §4: `missing` de pydantic = dato obligatorio que no llegó ⇒ se nombra como tal
  // (no es un «valor no válido»: no hay valor), con el mismo mapeo de nombres de campo.
  if (registro.type === 'missing') {
    return campo ? `Falta el dato obligatorio «${campo}»` : 'Falta un dato obligatorio'
  }
  if (tieneTipo || campo) {
    return campo ? `Valor no válido en «${campo}»` : 'Valor no válido'
  }
  if (typeof registro.msg === 'string' && registro.msg.trim()) return registro.msg
  return null
}

function textoDeDetalle(detail: unknown): string | null {
  if (detail === null || detail === undefined) return null
  if (typeof detail === 'string') return detail.trim() ? detail : null
  if (Array.isArray(detail)) {
    const partes = new Set<string>()
    for (const item of detail) {
      const texto = textoDeItem(item)
      if (texto) partes.add(texto)
    }
    return partes.size ? Array.from(partes).join(' · ') : null
  }
  if (typeof detail === 'object') {
    return textoDeItem(detail)
  }
  return null
}

export function getErrorMessage(err: any, fallback = 'Unexpected error'): string {
  if (typeof err === 'string') return err
  const detalle = textoDeDetalle(err?.response?.data?.detail)
  if (detalle) return detalle
  if (typeof err?.message === 'string' && err.message) return err.message
  return fallback
}
