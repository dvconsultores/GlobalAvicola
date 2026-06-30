import { useState, useRef, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
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
 placeholder,
 searchPlaceholder,
 renderLabel = (x: any) => x.name || x.lot_code || x.code || String(x.id),
 renderSub,
 disabled = false,
 error = false,
 className = '',
 minSearchLength = 0,
}: SearchSelectProps) {
 const { t } = useTranslation()
 const _placeholder = placeholder ?? t('common.select', 'Seleccionar...')
 const _searchPlaceholder = searchPlaceholder ?? t('common.search', 'Buscar...')
 const [open, setOpen] = useState(false)
 const [search, setSearch] = useState('')
 const [isMobileView, setIsMobileView] = useState(() =>
 typeof window !== 'undefined' ? window.matchMedia('(max-width: 1023px)').matches : false,
 )
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

 useEffect(() => {
 if (typeof window === 'undefined') return
 const mq = window.matchMedia('(max-width: 1023px)')
 const onChange = (e: MediaQueryListEvent) => setIsMobileView(e.matches)
 setIsMobileView(mq.matches)
 try {
 mq.addEventListener('change', onChange)
 return () => mq.removeEventListener('change', onChange)
 } catch {
 mq.addListener(onChange)
 return () => mq.removeListener(onChange)
 }
 }, [])

 const handleSelect = (item: any) => {
 onChange(String(item.id))
 setSearch('')
 setOpen(false)
 }

 const borderColor = error
 ? 'border-red-300'
 : 'border-slate-300'

 if (isMobileView) {
 return (
 <div className={`relative ${className}`}>
 <select
 value={value === undefined || value === null ? '' : String(value)}
 onChange={(e) => onChange(e.target.value)}
 disabled={disabled}
 className={`w-full h-11 px-3 border ${borderColor} rounded-lg text-sm text-slate-900 bg-white disabled:opacity-50`}
 >
 <option value="">{_placeholder}</option>
 {items.map((item: any) => {
 const label = renderLabel(item)
 const sub = renderSub ? renderSub(item) : ''
 return (
 <option key={item.id} value={String(item.id)}>
 {sub ? `${label} (${sub})` : label}
 </option>
 )
 })}
 </select>
 </div>
 )
 }

 return (
 <div ref={containerRef} className={`relative ${className}`}>
 {open ? (
 <div className={`flex items-center w-full h-11 px-3 border ${borderColor} rounded-lg bg-white`}>
 <Search size={15} className="text-slate-400 shrink-0 mr-2" />
 <input
 ref={inputRef}
 type="text"
 value={search}
 onChange={e => setSearch(e.target.value)}
 placeholder={_searchPlaceholder}
 className="flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder"
 />
 <button type="button" onClick={() => { setOpen(false); setSearch('') }}
 className="shrink-0 text-slate-400 hover p-0.5">
 <X size={14} />
 </button>
 </div>
 ) : (
 <button type="button" disabled={disabled}
 onClick={() => setOpen(true)}
 className={`flex items-center w-full h-11 px-3 border ${borderColor} rounded-lg text-sm bg-white disabled:opacity-50 hover:border-slate-400 transition-colors text-left`}>
 <Search size={15} className="text-slate-400 shrink-0 mr-2" />
 <span className={`flex-1 truncate ${selectedLabel ? 'text-slate-900' : 'text-slate-400'}`}>
 {selectedLabel || _placeholder}
 </span>
 <ChevronDown size={15} className="text-slate-400 shrink-0 ml-2" />
 </button>
 )}

 {open && (
 <div className="absolute z-50 left-0 right-0 mt-1 max-h-52 overflow-y-auto bg-white border border-slate-200 rounded-lg shadow-lg">
 {filtered.length === 0 ? (
 <p className="px-3 py-3 text-xs text-slate-400 text-center">Sin resultados</p>
 ) : (
 filtered.map((item: any) => {
 const isSelected = String(item.id) === String(value)
 return (
 <button key={item.id} type="button" onClick={() => handleSelect(item)}
 className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
 isSelected ? 'bg-blue-50 text-blue-700 font-semibold'
 : 'text-slate-700 hover:bg-slate-50:bg-slate-700'}`}>
 <span className="flex-1 truncate">{renderLabel(item)}</span>
 {renderSub && <span className="text-xs text-slate-400 shrink-0">{renderSub(item)}</span>}
 </button>
 )
 })
 )}
 </div>
 )}
 </div>
 )
}
