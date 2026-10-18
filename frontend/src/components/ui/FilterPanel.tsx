import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, RotateCcw } from 'lucide-react'

interface FilterPanelProps {
 children: React.ReactNode
 onClear?: () => void
 /** Número total de resultados (se muestra a la derecha) */
 totalResults?: number
 /** Label del botón limpiar */
 clearLabel?: string
}

/**
 * FilterPanel — Panel de filtros colapsable.
 *
 * Agrupa los filtros en una sección que se puede expandir/colapsar.
 * Ideal para ReviewCenter, Reportes, y páginas con múltiples filtros.
 */
export default function FilterPanel({
 children,
 onClear,
 totalResults,
 clearLabel,
}: FilterPanelProps) {
 const { t } = useTranslation()
 const [open, setOpen] = useState(true)

 return (
 <div className="bg-white rounded-xl border border-slate-200 mb-4 overflow-hidden">
 {/* Header: el disparador y «Limpiar» son HERMANOS. Un `<button>` dentro de otro
     `<button>` es HTML inválido (React: «<button> cannot be a descendant of <button>»). */}
 <div className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-slate-700 transition-colors">
 <button
 onClick={() => setOpen(!open)}
 className="flex items-center gap-2 hover:text-slate-900 transition-colors"
 aria-expanded={open}
 >
 <ChevronDown
 size={16}
 className={`text-slate-400 transition-transform duration-200 ${
 open ? 'rotate-0' : '-rotate-90'
 }`}
 />
 {t('ui.filterPanel.title', 'Filtros')}
 </button>
 <div className="flex items-center gap-3">
 {totalResults !== undefined && (
 <span className="text-xs text-slate-400 font-normal">
 {totalResults} {t('common.results', 'resultados')}
 </span>
 )}
 {onClear && (
 <button
 onClick={onClear}
 className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 transition-colors"
 >
 <RotateCcw size={12} />
 {clearLabel || t('ui.filterPanel.clear', 'Limpiar')}
 </button>
 )}
 </div>
 </div>

 {/* Contenido colapsable */}
 <div
 className={`transition-all duration-200 ease-in-out overflow-hidden ${
 open ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
 }`}
 >
 <div className="px-4 pb-4 flex flex-wrap gap-3 border-t border-slate-100 pt-3">
 {children}
 </div>
 </div>
 </div>
 )
}

/**
 * FilterGroup — Agrupación de filtros relacionados con label.
 * Responsive: en mobile (<640px) los filtros se apilan verticalmente.
 */
export function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
 return (
 <div className="flex flex-col gap-1.5">
 <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
 <div className="flex flex-col sm:flex-row sm:flex-wrap items-start sm:items-center gap-1.5 sm:gap-2">
 {children}
 </div>
 </div>
 )
}
