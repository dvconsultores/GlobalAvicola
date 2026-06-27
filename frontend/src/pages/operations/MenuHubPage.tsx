import { useMemo, useState } from 'react'
import { useNavigate, useParams, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LayoutGrid } from 'lucide-react'
import { NAV_ITEMS, type NavItem } from '../../data/navigationConfig'
import SubNavHeader from '../../components/layout/SubNavHeader'
import MenuCard from '../../components/ui/MenuCard'
import type { BreadcrumbItem } from '../../components/ui/Breadcrumbs'

/** Busca recursivamente un NavItem por su clave dentro de NAV_ITEMS. */
function findNavItem(key: string, items: NavItem[] = NAV_ITEMS): NavItem | null {
  for (const it of items) {
    if (it.key === key) return it
    if (it.children) {
      const found = findNavItem(key, it.children)
      if (found) return found
    }
  }
  return null
}

/**
 * MenuHubPage — Hub de opciones en grilla.
 *
 * Patrón atenea: el menú lateral abre un hub que despliega las opciones del
 * área como una grilla de tarjetas. Al elegir una opción con sub-opciones se
 * profundiza (drill-in) mostrando un nuevo grid con botón "Atrás" y migas de
 * pan; al elegir una operación final se navega a su formulario/pantalla.
 *
 * Es una capa de presentación: no cambia rutas ni lógica existentes.
 */
export default function MenuHubPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { menuKey } = useParams<{ menuKey: string }>()

  const root = useMemo(() => (menuKey ? findNavItem(menuKey) : null), [menuKey])
  // Pila de navegación interna (drill-in dentro del hub)
  const [stack, setStack] = useState<NavItem[]>([])

  if (!root) return <Navigate to="/" replace />

  const current = stack.length ? stack[stack.length - 1] : root
  const items = current.children ?? []

  const handleSelect = (item: NavItem) => {
    if (item.children && item.children.length > 0) {
      setStack((prev) => [...prev, item])
    } else if (item.to) {
      navigate(item.to)
    }
  }

  const handleBack = () => {
    if (stack.length > 0) {
      setStack((prev) => prev.slice(0, -1))
    } else {
      navigate('/')
    }
  }

  // Migas: raíz → ...drill → actual
  const path = [root, ...stack]
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'nav.dashboard', fallback: 'Dashboard', to: '/' },
    ...path.map((node) => ({ label: node.labelKey, fallback: node.fallback })),
  ]

  return (
    <div className="max-w-5xl mx-auto">
      <SubNavHeader
        title={t(current.labelKey, current.fallback)}
        breadcrumbs={breadcrumbs}
        onBack={handleBack}
      />

      <p className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-4 -mt-2">
        <LayoutGrid size={13} />
        {t('process.hub.chooseOption', 'Elige una opción')}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => {
          const childCount = item.children?.length ?? 0
          const description =
            childCount > 0
              ? t('nav.optionsCount', `${childCount} opciones`, { count: childCount })
              : t('process.hub.open', 'Abrir')
          return (
            <MenuCard
              key={item.key}
              icon={item.icon}
              title={t(item.labelKey, item.fallback)}
              description={description}
              badge={item.badge}
              onClick={() => handleSelect(item)}
            />
          )
        })}
      </div>
    </div>
  )
}
