/**
 * STATUS COLORS — Configuración centralizada de colores de estado.
 *
 * Unifica los colores usados por Badge, StatusTimeline, KpiCard y cualquier
 * otro componente que necesite representar visualmente estados operativos.
 *
 * Uso:
 *   import { STATUS_STYLES, type StatusKey } from './statusColors'
 *   const style = STATUS_STYLES['approved']
 *   // style.bg → 'bg-emerald-50'
 *   // style.text → 'text-emerald-700'
 *   // style.border → 'border-emerald-200'
 *   // style.dot → 'bg-emerald-500'
 */
import {
  FileText, Clock, Search, Undo2, RotateCcw, CheckCircle, XCircle,
  Ban, Package, Send, AlertTriangle, Check, type LucideIcon,
} from 'lucide-react'

export type StatusKey =
  | 'draft' | 'registered' | 'pending_review' | 'pending'
  | 'in_review' | 'returned' | 'corrected' | 'approved'
  | 'rejected' | 'cancelled' | 'consolidated'
  | 'sent_sap' | 'confirmed_sap' | 'error_sap'
  | 'info' | 'warning' | 'neutral'

export interface StatusStyle {
  /** Fondo para badges y contenedores */
  bg: string
  /** Color de texto */
  text: string
  /** Color de borde */
  border: string
  /** Color del punto indicador */
  dot: string
  /** Icono representativo */
  icon: LucideIcon
  /** Color del icono */
  iconColor: string
}

export const STATUS_STYLES: Record<StatusKey, StatusStyle> = {
  // ===== Estados operativos =====
  draft: {
    bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200',
    dot: 'bg-slate-400', icon: FileText, iconColor: 'text-slate-500',
  },
  registered: {
    bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200',
    dot: 'bg-sky-500', icon: FileText, iconColor: 'text-sky-600',
  },
  pending_review: {
    bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200',
    dot: 'bg-amber-500', icon: Clock, iconColor: 'text-amber-600',
  },
  pending: {
    bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200',
    dot: 'bg-amber-500', icon: Clock, iconColor: 'text-amber-600',
  },
  in_review: {
    bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200',
    dot: 'bg-indigo-500', icon: Search, iconColor: 'text-indigo-600',
  },
  returned: {
    bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200',
    dot: 'bg-orange-500', icon: Undo2, iconColor: 'text-orange-600',
  },
  corrected: {
    bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200',
    dot: 'bg-purple-500', icon: RotateCcw, iconColor: 'text-purple-600',
  },
  approved: {
    bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200',
    dot: 'bg-emerald-500', icon: CheckCircle, iconColor: 'text-emerald-600',
  },
  rejected: {
    bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200',
    dot: 'bg-red-500', icon: XCircle, iconColor: 'text-red-600',
  },
  cancelled: {
    bg: 'bg-slate-50', text: 'text-slate-500', border: 'border-slate-200',
    dot: 'bg-slate-400', icon: Ban, iconColor: 'text-slate-400',
  },
  consolidated: {
    bg: 'bg-teal-50', text: 'text-teal-700', border: 'border-teal-200',
    dot: 'bg-teal-500', icon: Package, iconColor: 'text-teal-600',
  },

  // ===== Estados SAP =====
  sent_sap: {
    bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200',
    dot: 'bg-blue-500', icon: Send, iconColor: 'text-blue-600',
  },
  confirmed_sap: {
    bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200',
    dot: 'bg-emerald-600', icon: Check, iconColor: 'text-emerald-700',
  },
  error_sap: {
    bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200',
    dot: 'bg-red-500', icon: AlertTriangle, iconColor: 'text-red-600',
  },

  // ===== Estados genéricos =====
  info: {
    bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200',
    dot: 'bg-blue-500', icon: FileText, iconColor: 'text-blue-600',
  },
  warning: {
    bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200',
    dot: 'bg-amber-500', icon: AlertTriangle, iconColor: 'text-amber-600',
  },
  neutral: {
    bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200',
    dot: 'bg-slate-400', icon: FileText, iconColor: 'text-slate-500',
  },
}

/**
 * Mapa de strings de estado de la API a StatusKey.
 * Normaliza nombres como 'pending_review' → 'pending', 'sent_to_sap' → 'sent_sap'
 */
const STATUS_ALIASES: Record<string, StatusKey> = {
  'pending_review': 'pending_review',
  'pending': 'pending',
  'in_review': 'in_review',
  'returned': 'returned',
  'corrected': 'corrected',
  'approved': 'approved',
  'rejected': 'rejected',
  'cancelled': 'cancelled',
  'consolidated': 'consolidated',
  'sent_to_sap': 'sent_sap',
  'sent': 'sent_sap',
  'confirmed': 'confirmed_sap',
  'error': 'error_sap',
  'draft': 'draft',
  'registered': 'registered',
}

/**
 * Resuelve un status string desde API a StatusKey.
 * Útil cuando el backend devuelve strings que pueden variar.
 */
export function resolveStatus(status: string): StatusKey {
  return STATUS_ALIASES[status] ?? 'neutral'
}

/**
 * Obtiene el StatusStyle para un status string.
 * Usa resolveStatus internamente.
 */
export function getStatusStyle(status: string): StatusStyle {
  return STATUS_STYLES[resolveStatus(status)]
}
