import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { EVENT_ICON_MAP, eventColor, type FlowStep } from '../../data/processCatalog'

interface OperationTileProps {
 step: FlowStep
 /** 1-based position in the sequence. */
 index: number
 /** Active lot id, forwarded to the operation form. */
 lotId?: string | number
 /** Render as a static (non-clickable) tile, e.g. read-only mobile view. */
 readOnly?: boolean
}

/**
 * Large, tappable icon tile representing a single operation in a process
 * sequence. Designed to be instantly recognizable (big colored icon + number
 * badge + short label) for users of any age — the visual style of a modern
 * field-ops app grid.
 */
export default function OperationTile({ step, index, lotId, readOnly }: OperationTileProps) {
 const { t } = useTranslation()
 const location = useLocation()
 const Icon = EVENT_ICON_MAP[step.event] ?? EVENT_ICON_MAP.feed_registration
 const color = eventColor(step.event)
 const label = t(`events.${step.event}`, step.event)

 const inner = (
 <>
 {/* Sequence number badge */}
 <span className="absolute top-2 left-2 w-6 h-6 rounded-full bg-white text-xs font-extrabold text-slate-700 flex items-center justify-center shadow-sm ring-1 ring-black/5">
 {index}
 </span>

 {/* Big colored icon */}
 <span
 className={`w-16 h-16 rounded-2xl ${color.bg} text-white flex items-center justify-center shadow-md ring-4 ${color.ring} transition-transform group-hover:scale-110 group-active:scale-95`}
 >
 <Icon size={30} strokeWidth={2.2} />
 </span>

 {/* Label */}
 <span className="mt-3 text-sm font-bold leading-tight text-center text-slate-700 line-clamp-2">
 {label}
 </span>
 </>
 )

 const base =
 'group relative flex flex-col items-center justify-start p-4 pt-9 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-lg hover:border-slate-200:border-slate-600 transition-all min-h-[150px]'

 if (readOnly) {
 return (
 <div className={base} aria-label={label}>
 {inner}
 </div>
 )
 }

 const href = lotId
 ? `/operations/new?type=${step.event}&lot_id=${lotId}`
 : `/operations/new?type=${step.event}`

 return (
 <Link
 to={href}
 className={`${base} active:scale-[0.97]`}
 aria-label={label}
 onClick={() => sessionStorage.setItem('operationBackTarget', location.pathname)}
 >
 {inner}
 </Link>
 )
}
