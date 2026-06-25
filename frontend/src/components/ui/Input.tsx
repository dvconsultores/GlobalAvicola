/**
 * Input — Global Avícola design system
 * Includes: label, helper text, error state, leading/trailing icons
 * Accessible: aria-invalid, aria-describedby, native HTML semantics
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
    <div className={`flex flex-col gap-1 ${wrapperClassName}`}>
      {label && (
        <label htmlFor={inputId} className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          {label}
          {props.required && <span className="text-red-500 ml-0.5" aria-hidden>*</span>}
        </label>
      )}

      <div className="relative">
        {leadingIcon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            {leadingIcon}
          </span>
        )}

        <input
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : helperText ? helpId : undefined}
          className={[
            'w-full h-10 border rounded-lg text-sm text-slate-900 dark:text-slate-100 bg-white dark:bg-dark-surface',
            'placeholder:text-slate-400 dark:placeholder:text-slate-500',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            error ? 'border-red-500 focus:ring-red-400' : 'border-slate-300 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500',
            leadingIcon ? 'pl-9' : 'pl-3',
            trailingIcon ? 'pr-9' : 'pr-3',
            error
              ? 'border-red-400 focus:border-red-500 focus:ring-red-200'
              : 'border-slate-300 focus:border-[#2563EB] focus:ring-blue-200',
            'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed',
            className,
          ].join(' ')}
          {...props}
        />

        {trailingIcon && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
            {trailingIcon}
          </span>
        )}
      </div>

      {error ? (
        <p id={errorId} role="alert" className="flex items-center gap-1 text-xs text-red-600">
          <AlertCircle size={12} className="shrink-0" />
          {error}
        </p>
      ) : helperText ? (
        <p id={helpId} className="text-xs text-slate-500">{helperText}</p>
      ) : null}
    </div>
  )
}
