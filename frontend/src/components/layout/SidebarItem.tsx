import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { type LucideIcon } from 'lucide-react'
import { isPathActive } from '../../data/navigationConfig'

interface SidebarItemProps {
 icon?: LucideIcon
 labelKey: string
 fallback: string
 to: string
 depth?: number
 badge?: number
 onClick?: () => void
 /** Forzar estado activo (ej. hub activo por ruta hija) */
 forceActive?: boolean
}

export default function SidebarItem({
 icon: Icon,
 labelKey,
 fallback,
 to,
 depth = 0,
 badge,
 onClick,
 forceActive,
}: SidebarItemProps) {
 const { t } = useTranslation()
 const location = useLocation()
 const active = forceActive || isPathActive(location.pathname, to)

 const paddingByDepth = ['px-3', 'pl-9 pr-3', 'pl-14 pr-3']

 return (
 <Link
 to={to}
 onClick={onClick}
 className={`
 flex items-center gap-2 py-1.5 rounded-lg text-[13px] transition-colors duration-100
 ${paddingByDepth[depth] ?? paddingByDepth[0]}
 ${active
 ? 'bg-white[0.12] text-white font-medium'
 : 'text-white/55 font-normal hover:text-white/90 hover:bg-white/[0.06]'
 }
 `}
 aria-current={active ? 'page' : undefined}
 >
 {Icon && (
 <span className={`shrink-0 ${active ? 'text-white/90' : 'text-white/40'}`}>
 <Icon size={15} strokeWidth={active ? 2 : 1.7} />
 </span>
 )}
 <span className="flex-1 truncate">{t(labelKey, fallback)}</span>
 {badge !== undefined && badge > 0 && (
 <span className="inline-flex items-center justify-center min-w-[18px] h-4 px-1 rounded-full text-[10px] font-semibold bg-white text-white/90">
 {badge > 99 ? '99+' : badge}
 </span>
 )}
 </Link>
 )
}
