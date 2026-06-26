import { useTranslation } from 'react-i18next'

interface SidebarSectionProps {
  labelKey: string
  fallback: string
}

export default function SidebarSection({ labelKey, fallback }: SidebarSectionProps) {
  const { t } = useTranslation()
  const label = t(labelKey, fallback)

  if (!label) return null

  return (
    <div className="px-3 pt-5 pb-1">
      <span
        className="text-[10px] font-semibold uppercase tracking-[0.18em] select-none"
        style={{ color: 'rgba(147,197,253,0.45)' }}
      >
        {label}
      </span>
    </div>
  )
}
