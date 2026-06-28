import { useState, useRef, useEffect, useMemo } from 'react'
import { Search, ChevronDown, X } from 'lucide-react'

interface SearchSelectProps {
  value: string | number | undefined
  onChange: (value: string) => void
  items: any[]
  placeholder?: string
  searchPlaceholder?: string
  renderLabel?: (item: any) => string
  renderSub?: (item: any) => string
  disabled?: boolean
  error?: boolean
  className?: string
  minSearchLength?: number
  allowFreeText?: boolean
}

export default function SearchSelect({
  value,
  onChange,
  items,
  placeholder = 'Seleccionar...',
  searchPlaceholder = 'Buscar...',
  renderLabel = (x: any) => x.name || x.lot_code || x.code || String(x.id),
  renderSub,
  disabled = false,
  error = false,
  className = '',
  minSearchLength = 0,
}: SearchSelectProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedLabel = useMemo(() => {
    if (value === undefined || value === null || value === '') return ''
    const found = items.find((x: any) => String(x.id) === String(value))
    return found ? renderLabel(found) : String(value)
  }, [value, items, renderLabel])

  const filtered = useMemo(() => {
    if (search.length < minSearchLength) return items.slice(0, 50)
    const q = search.toLowerCase()
    return items.filter((x: any) => {
      const label = renderLabel(x).toLowerCase()
      const sub = renderSub ? renderSub(x).toLowerCase() : ''
      return label.includes(q) || sub.includes(q)
    }).slice(0, 50)
  }, [items, search, renderLabel, renderSub, minSearchLength])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setSearch('')
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus()
  }, [open])

  const handleSelect = (item: any) => {
    onChange(String(item.id))
    setSearch('')
    setOpen(false)
  }

  const borderColor = error
    ? 'border-red-300 dark:border-red-700'
    : 'border-slate-300 dark:border-slate-600'

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {open ? (
        <div className={`flex items-center w-full h-11 px-3 border ${borderColor} rounded-lg bg-white dark:bg-slate-800`}>
          <Search size={15} className="text-slate-400 dark:text-slate-500 shrink-0 mr-2" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={searchPlaceholder}
            className="flex-1 bg-transparent text-sm text-slate-900 dark:text-slate-100 outline-none placeholder:text-slate-400"
          />
          <button type="button" onClick={() => { setOpen(false); setSearch('') }}
            className="shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 p-0.5">
            <X size={14} />
          </button>
        </div>
      ) : (
        <button type="button" disabled={disabled}
          onClick={() => setOpen(true)}
          className={`flex items-center w-full h-11 px-3 border ${borderColor} rounded-lg text-sm bg-white dark:bg-slate-800 disabled:opacity-50 hover:border-slate-400 transition-colors text-left`}>
          <Search size={15} className="text-slate-400 dark:text-slate-500 shrink-0 mr-2" />
          <span className={`flex-1 truncate ${selectedLabel ? 'text-slate-900 dark:text-slate-100' : 'text-slate-400 dark:text-slate-500'}`}>
            {selectedLabel || placeholder}
          </span>
          <ChevronDown size={15} className="text-slate-400 dark:text-slate-500 shrink-0 ml-2" />
        </button>
      )}

      {open && (
        <div className="absolute z-50 left-0 right-0 mt-1 max-h-52 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg">
          {filtered.length === 0 ? (
            <p className="px-3 py-3 text-xs text-slate-400 dark:text-slate-500 text-center">Sin resultados</p>
          ) : (
            filtered.map((item: any) => {
              const isSelected = String(item.id) === String(value)
              return (
                <button key={item.id} type="button" onClick={() => handleSelect(item)}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
                    isSelected ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-semibold'
                    : 'text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700'}`}>
                  <span className="flex-1 truncate">{renderLabel(item)}</span>
                  {renderSub && <span className="text-xs text-slate-400 dark:text-slate-500 shrink-0">{renderSub(item)}</span>}
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
