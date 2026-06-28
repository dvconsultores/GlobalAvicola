/**
 * Input — Global Avícola Corporate Design System v2
 */
import { type InputHTMLAttributes, type ReactNode, useId } from 'react'
import { AlertCircle } from 'lucide-react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
 label?: string
 helperText?: string
 error?: string
 leadingIcon?: ReactNode
 trailingIcon?: ReactNode
 wrapperClassName?: string
}

export function Input({
 label,
 helperText,
 error,
 leadingIcon,
 trailingIcon,
 wrapperClassName = '',
 className = '',
 id,
 ...props
}: InputProps) {
 const generatedId = useId()
 const inputId = id ?? generatedId
 const helpId = `${inputId}-help`
 const errorId = `${inputId}-error`

 return (
 <div className={`flex flex-col gap-1.5 ${wrapperClassName}`}>
 {label && (
 <label htmlFor={inputId} className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
 {label}
 {props.required && <span className="text-red-500 ml-0.5" aria-hidden>*</span>}
 </label>
 )}

 <div className="relative">
 {leadingIcon && (
 <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
 {leadingIcon}
 </span>
 )}

 <input
 id={inputId}
 aria-invalid={!!error}
 aria-describedby={error ? errorId : helperText ? helpId : undefined}
 className={[
 'w-full h-10 border rounded-xl text-sm text-slate-900',
 'bg-slate-50',
 'placeholder',
 'transition-all duration-150',
 'focus:outline-none focus:ring-2 focus:ring-offset-0 focus:bg-white',
 error
 ? 'border-red-400 focus:border-red-500 focus:ring-red-200:ring-red-800'
 : 'border-slate-200 focus:border-brand-500 focus:ring-brand-400/25',
 leadingIcon ? 'pl-10' : 'pl-3.5',
 trailingIcon ? 'pr-10' : 'pr-3.5',
 'disabled:bg-slate-100 disabled disabled:cursor-not-allowed',
 className,
 ].join(' ')}
 {...props}
 />

 {trailingIcon && (
 <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
 {trailingIcon}
 </span>
 )}
 </div>

 {error ? (
 <p id={errorId} role="alert" className="flex items-center gap-1 text-xs text-red-600">
 <AlertCircle size={11} className="shrink-0" />
 {error}
 </p>
 ) : helperText ? (
 <p id={helpId} className="text-xs text-slate-400">{helperText}</p>
 ) : null}
 </div>
 )
}

