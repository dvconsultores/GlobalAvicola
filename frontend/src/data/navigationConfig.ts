/**
 * NAVIGATION CONFIG — Configuración central de navegación del sidebar
 *
 * Define la jerarquía completa del menú lateral:
 * Secciones → Items (con o sin hijos) → Sub-items
 *
 * Se usa tanto en Sidebar (desktop) como en MobileDrawer (mobile)
 * para mantener una única fuente de verdad.
 */
import {
  Home, Bird, Egg, Flame, Drumstick, Feather, Plane,
  Search, CheckCircle, RefreshCw, TrendingUp, Shield,
  Database, Settings, Users, Clock, Undo2,
  Send, AlertTriangle, BarChart3, UserCheck, FileText,
  Sprout,
  type LucideIcon,
} from 'lucide-react'
import { hasPermission, type SessionLike } from '../auth/permissions'

export interface NavItem {
  /** Clave única para el submenú */
  key: string
  /** Icono Lucide */
  icon: LucideIcon
  /** Clave i18n para la etiqueta */
  labelKey: string
  /** Texto fallback si no hay traducción */
  fallback: string
  /** Ruta (opcional — si no tiene, es un contenedor) */
  to?: string
  /** Hijos (submenú anidado) */
  children?: NavItem[]
  /** Badge numérico opcional (ej: pendientes count) */
  badge?: number
  /** GA-FE-02 · permiso RBAC requerido para mostrar la entrada (ausente = visible como siempre).
   * Frontera `R-98`/GA-FE-03: SOLO las entradas que declaran `permission` se filtran. */
  permission?: string
  /** Agrupar bajo qué sección */
  section: NavSectionKey
}

export type NavSectionKey =
  | 'main'
  | 'operational'
  | 'review'
  | 'integration'
  | 'reports'
  | 'administration'

export interface NavSection {
  key: NavSectionKey
  /** Clave i18n */
  labelKey: string
  fallback: string
}

/** Secciones del sidebar */
export const NAV_SECTIONS: NavSection[] = [
  { key: 'main', labelKey: 'nav.sections.main', fallback: '' },
  { key: 'operational', labelKey: 'nav.sections.operational', fallback: 'OPERATIVO' },
  { key: 'review', labelKey: 'nav.sections.review', fallback: 'REVISIÓN' },
  { key: 'integration', labelKey: 'nav.sections.integration', fallback: 'INTEGRACIÓN' },
  { key: 'reports', labelKey: 'nav.sections.reports', fallback: 'REPORTES' },
  { key: 'administration', labelKey: 'nav.sections.administration', fallback: 'ADMINISTRACIÓN' },
]

/**
 * Items del menú principal (sidebar + drawer).
 * Sigue la jerarquía: Sección → Módulo → Submódulo → (rutas)
 */
export const NAV_ITEMS: NavItem[] = [
  // ===== MAIN =====
  {
    key: 'dashboard',
    icon: Home,
    labelKey: 'nav.dashboard',
    fallback: 'Dashboard',
    to: '/',
    section: 'main',
  },

  // ===== OPERATIVO =====
  {
    key: 'poultry',
    icon: Bird,
    labelKey: 'nav.poultry',
    fallback: 'Gestión Avícola',
    section: 'operational',
    children: [
      {
        key: 'grandparent',
        icon: Plane,
        labelKey: 'nav.grandparent',
        fallback: 'Progenitoras',
        section: 'operational',
        children: [
          { key: 'gp_rearing', icon: Sprout, labelKey: 'nav.gpRearing', fallback: 'Cría', to: '/poultry/grandparent/rearing', section: 'operational' },
          { key: 'gp_production', icon: Egg, labelKey: 'nav.gpProduction', fallback: 'Producción', to: '/poultry/grandparent/production', section: 'operational' },
        ],
      },
      {
        key: 'breeder',
        icon: Feather,
        labelKey: 'nav.breeder',
        fallback: 'Reproductoras',
        section: 'operational',
        children: [
          { key: 'br_rearing', icon: Sprout, labelKey: 'nav.brRearing', fallback: 'Cría', to: '/poultry/breeder/rearing', section: 'operational' },
          { key: 'br_production', icon: Egg, labelKey: 'nav.brProduction', fallback: 'Producción', to: '/poultry/breeder/production', section: 'operational' },
        ],
      },
      {
        key: 'hatchery',
        icon: Flame,
        labelKey: 'nav.hatchery',
        fallback: 'Incubadora',
        to: '/poultry/hatchery',
        section: 'operational',
      },
      {
        key: 'broiler',
        icon: Drumstick,
        labelKey: 'nav.broiler',
        fallback: 'Pollo de Engorde',
        to: '/poultry/broiler',
        section: 'operational',
      },
    ],
  },

  // ===== REVISIÓN =====
  {
    key: 'review',
    icon: Search,
    labelKey: 'nav.review',
    fallback: 'Centro de Revisión',
    section: 'review',
    children: [
      { key: 'review_pending', icon: Clock, labelKey: 'nav.reviewPending', fallback: 'Pendientes', to: '/review', section: 'review' },
      { key: 'review_approved', icon: CheckCircle, labelKey: 'nav.reviewApproved', fallback: 'Aprobados', to: '/review?status=approved', section: 'review' },
      { key: 'review_returned', icon: Undo2, labelKey: 'nav.reviewReturned', fallback: 'Devueltos', to: '/review?status=returned', section: 'review' },
    ],
  },
  {
    key: 'approvals',
    icon: CheckCircle,
    labelKey: 'nav.approvals',
    fallback: 'Aprobaciones',
    to: '/approvals',
    section: 'review',
  },

  // ===== INTEGRACIÓN =====
  {
    key: 'sap',
    icon: RefreshCw,
    labelKey: 'nav.sap',
    fallback: 'Integración SAP',
    section: 'integration',
    children: [
      { key: 'sap_pending', icon: Clock, labelKey: 'nav.sapPending', fallback: 'Documentos Pendientes', to: '/sap', section: 'integration' },
      { key: 'sap_sent', icon: Send, labelKey: 'nav.sapSent', fallback: 'Envíos a SAP', to: '/sap', section: 'integration' },
      { key: 'sap_errors', icon: AlertTriangle, labelKey: 'nav.sapErrors', fallback: 'Errores SAP', to: '/sap', section: 'integration' },
      { key: 'sap_log', icon: FileText, labelKey: 'nav.sapLog', fallback: 'Bitácora SAP', to: '/sap', section: 'integration' },
    ],
  },

  // ===== REPORTES =====
  {
    key: 'reports',
    icon: TrendingUp,
    labelKey: 'nav.reports',
    fallback: 'Reportes',
    section: 'reports',
    children: [
      { key: 'rpt_production', icon: Egg, labelKey: 'nav.rptProduction', fallback: 'Producción', to: '/reports', section: 'reports' },
      { key: 'rpt_mortality', icon: BarChart3, labelKey: 'nav.rptMortality', fallback: 'Mortalidad', to: '/reports', section: 'reports' },
      { key: 'rpt_sap', icon: RefreshCw, labelKey: 'nav.rptSap', fallback: 'Diferencias SAP vs App', to: '/reports/sap', section: 'reports' },
    ],
  },

  // ===== ADMINISTRACIÓN =====
  {
    key: 'audit',
    icon: Shield,
    labelKey: 'nav.audit',
    fallback: 'Auditoría',
    to: '/audit',
    section: 'administration',
  },
  {
    key: 'masters',
    icon: Database,
    labelKey: 'nav.masters',
    fallback: 'Maestros',
    to: '/masters',
    section: 'administration',
  },
  {
    key: 'settings',
    icon: Settings,
    labelKey: 'nav.settings',
    fallback: 'Configuración',
    section: 'administration',
    children: [
      { key: 'settings_users', icon: Users, labelKey: 'nav.users', fallback: 'Usuarios y Roles', to: '/users', section: 'administration' },
      { key: 'settings_profile', icon: UserCheck, labelKey: 'nav.profile', fallback: 'Mi Perfil', to: '/profile', section: 'administration' },
      { key: 'settings_unit_access', icon: Shield, labelKey: 'nav.unitAccess', fallback: 'Acceso por unidad', to: '/admin/unit-access', section: 'administration', permission: 'business_units:read' },
    ],
  },
]

const MOBILE_TOP_LEVEL_KEYS = new Set(['poultry'])

function filterItemForView(item: NavItem, viewType?: string, depth = 0): NavItem | null {
  if (viewType !== 'mobile') return item
  if (depth === 0 && !MOBILE_TOP_LEVEL_KEYS.has(item.key)) return null

  if (!item.children) return item

  const visibleChildren = item.children
    .map((child) => filterItemForView(child, viewType, depth + 1))
    .filter(Boolean) as NavItem[]

  return { ...item, children: visibleChildren }
}

/**
 * Retorna los ítems de navegación visibles para el tipo de vista.
 *
 * Regla actual:
 * - web: menú completo
 * - mobile: solo Gestión Avícola (con sus sub-opciones)
 */
export function getNavItemsForViewType(viewType?: string): NavItem[] {
  if (viewType !== 'mobile') return NAV_ITEMS

  return NAV_ITEMS
    .map((item) => filterItemForView(item, viewType, 0))
    .filter(Boolean) as NavItem[]
}

/**
 * Dado un conjunto de ítems, devuelve solo las secciones que contienen elementos.
 */
export function getNavSectionsForItems(items: NavItem[]): NavSection[] {
  const presentSections = new Set(items.map((item) => item.section))
  return NAV_SECTIONS.filter((section) => presentSections.has(section.key))
}

/**
 * Obtiene la clave de sección para un ítem dada su ruta.
 * Útil para expandir automáticamente la sección correcta al navegar.
 */
export function getSectionKeyForPath(pathname: string): NavSectionKey | null {
  for (const item of NAV_ITEMS) {
    if (item.to && (pathname === item.to || pathname.startsWith(item.to + '/'))) {
      return item.section
    }
    if (item.children) {
      for (const child of item.children) {
        if (child.to && (pathname === child.to || pathname.startsWith(child.to + '/'))) {
          return item.section
        }
        if (child.children) {
          for (const grandchild of child.children) {
            if (grandchild.to && (pathname === grandchild.to || pathname.startsWith(grandchild.to + '/'))) {
              return item.section
            }
          }
        }
      }
    }
  }
  return null
}

/**
 * Determina si una ruta está activa (coincidencia exacta o comienza con la ruta + /)
 */
export function isPathActive(pathname: string, to: string): boolean {
  if (to === '/') return pathname === '/'
  return pathname === to || pathname.startsWith(to + '/')
}

/**
 * Determina si una ruta está activa para un submenú completo
 * (cualquier hijo está activo)
 */
export function isAnyChildActive(pathname: string, item: NavItem): boolean {
  if (item.to && isPathActive(pathname, item.to)) return true
  if (item.children) {
    return item.children.some(child => {
      if (child.to && isPathActive(pathname, child.to)) return true
      if (child.children) return child.children.some(gc => gc.to && isPathActive(pathname, gc.to))
      return false
    })
  }
  return false
}

/**
 * GA-FE-02 · Filtro MÍNIMO por permiso para la navegación.
 *
 * Solo se filtran las entradas que declaran `permission` (hoy, únicamente la de GA-FE-02).
 * El resto del menú no se toca: la navegación dinámica global sigue siendo `GA-FE-03`
 * (frontera `R-98`/`R-119` intacta).
 */
export function filterNavItemsByPermissions(
  items: NavItem[],
  session: SessionLike | null | undefined,
): NavItem[] {
  return items
    .map(item =>
      item.children ? { ...item, children: filterNavItemsByPermissions(item.children, session) } : item,
    )
    .filter(item => !item.permission || hasPermission(session, item.permission))
}
