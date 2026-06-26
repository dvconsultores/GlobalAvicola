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
}

export default function SidebarItem({
  icon: Icon,
  labelKey,
  fallback,
  to,
  depth = 0,
  badge,
  onClick,
}: SidebarItemProps) {
  const { t } = useTranslation()
  const location = useLocation()
  const active = isPathActive(location.pathname, to)

  const paddingByDepth = ['px-3', 'pl-9 pr-3', 'pl-14 pr-3']

  return (
    <Link
      to={to}
      onClick={onClick}
      className={`
        flex items-center gap-2.5 py-2 rounded-lg text-[13px] font-medium transition-all duration-150
        ${paddingByDepth[depth] ?? paddingByDepth[0]}
        ${active
          ? 'bg-white text-brand-800 shadow-sm'
          : 'text-white/65 hover:text-white hover:bg-white/[0.07]'
        }
      `}
      aria-current={active ? 'page' : undefined}
    >
      {Icon && (
        <span
          className={`shrink-0 flex items-center justify-center w-5 h-5 ${
            active ? 'text-brand-600' : 'text-white/60'
          }`}
        >
          <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
        </span>
      )}
      <span className="flex-1 truncate">{t(labelKey, fallback)}</span>
      {badge !== undefined && badge > 0 && (
        <span
          className={`inline-flex items-center justify-center min-w-[18px] h-4.5 px-1.5 rounded-full text-[10px] font-bold ${
            active
              ? 'bg-brand-500 text-white'
              : 'bg-white/20 text-white'
          }`}
        >
          {badge > 99 ? '99+' : badge}
        </span>
      )}
    </Link>
  )
}
