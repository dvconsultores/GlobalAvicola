import { useState, useCallback, createContext, useContext } from 'react'
import type { ReactNode } from 'react'
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

export function ToastProvider({ children }: { children: ReactNode }) {
 const [toasts, setToasts] = useState<Toast[]>([])

 const addToast = useCallback((type: ToastType, message: string) => {
 const id = ++toastId
 setToasts(prev => [...prev.slice(-4), { id, type, message }])
 setTimeout(() => {
 setToasts(prev => prev.filter(t => t.id !== id))
 }, 4000)
 }, [])

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
 {/* Toast container */}
 <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
 {toasts.map(t => (
 <div
 key={t.id}
 className={`flex items-start gap-2 px-4 py-3 rounded-lg border shadow-lg text-sm font-medium animate-slide-in ${bgColors[t.type]} ${textColors[t.type]}`}
 >
 {icons[t.type]}
 <span className="flex-1">{t.message}</span>
 <button onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))} className="opacity-60 hover:opacity-100">
 <X size={14} />
 </button>
 </div>
 ))}
 </div>
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
export function getErrorMessage(err: any, fallback = 'Unexpected error'): string {
 if (typeof err === 'string') return err
 return err?.response?.data?.detail || err?.message || fallback
}
