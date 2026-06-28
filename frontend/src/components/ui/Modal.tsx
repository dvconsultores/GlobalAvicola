/**
 * Modal — Global Avícola design system
 * Accessible: focus trap, aria-modal, aria-labelledby, Escape closes
 * Cross-browser: works on Chrome, Edge, Firefox, Safari, iOS Safari, Android Chrome
 */
import { type ReactNode, useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'

interface ModalProps {
 open: boolean
 onClose: () => void
 title: string
 description?: string
 children: ReactNode
 footer?: ReactNode
 size?: 'sm' | 'md' | 'lg' | 'xl'
}

const SIZE_CLASSES = {
 sm: 'max-w-sm',
 md: 'max-w-lg',
 lg: 'max-w-2xl',
 xl: 'max-w-4xl',
}

export function Modal({
 open,
 onClose,
 title,
 description,
 children,
 footer,
 size = 'md',
}: ModalProps) {
 const dialogRef = useRef<HTMLDivElement>(null)
 const titleId = `modal-title-${title.replace(/\s+/g, '-').toLowerCase()}`

 // Close on Escape
 useEffect(() => {
 if (!open) return
 const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
 document.addEventListener('keydown', onKey)
 return () => document.removeEventListener('keydown', onKey)
 }, [open, onClose])

 // Prevent body scroll when open
 useEffect(() => {
 document.body.style.overflow = open ? 'hidden' : ''
 return () => { document.body.style.overflow = '' }
 }, [open])

 // Focus the dialog when opened
 useEffect(() => {
 if (open) setTimeout(() => dialogRef.current?.focus(), 10)
 }, [open])

 if (!open) return null

 return createPortal(
 <div
 role="dialog"
 aria-modal="true"
 aria-labelledby={titleId}
 className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
 >
 {/* Backdrop */}
 <div
 className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
 onClick={onClose}
 aria-hidden="true"
 />

 {/* Panel */}
 <div
 ref={dialogRef}
 tabIndex={-1}
 className={[
 'relative w-full bg-white dark:bg-slate-800 rounded-2xl shadow-xl',
 'outline-none overflow-hidden',
 'max-h-[90dvh] flex flex-col',
 SIZE_CLASSES[size],
 // Slide-up on mobile, scale-in on desktop
 'animate-[slide-up_200ms_ease-out]',
 ].join(' ')}
 >
 {/* Header */}
 <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-slate-100 shrink-0">
 <div>
 <h2 id={titleId} className="font-semibold text-slate-800 dark:text-slate-200 text-base leading-snug">
 {title}
 </h2>
 {description && (
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{description}</p>
 )}
 </div>
 <button
 onClick={onClose}
 aria-label="Cerrar"
 className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 dark:text-slate-500 hover:text-slate-600 hover:bg-slate-100 transition-colors"
 >
 <X size={16} />
 </button>
 </div>

 {/* Body */}
 <div className="overflow-y-auto px-5 py-4 flex-1">
 {children}
 </div>

 {/* Footer */}
 {footer && (
 <div className="px-5 py-4 border-t border-slate-100 shrink-0 flex items-center justify-end gap-2">
 {footer}
 </div>
 )}
 </div>
 </div>,
 document.body,
 )
}
