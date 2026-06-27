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
    <div className="px-3 pt-4 pb-0.5">
      <span
        className="text-[10px] font-semibold uppercase tracking-[0.12em] select-none"
        style={{ color: 'rgba(148,163,184,0.35)' }}
      >
        {label}
      </span>
    </div>
  )
}
