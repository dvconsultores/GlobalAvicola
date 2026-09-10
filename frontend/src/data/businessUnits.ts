/**
 * GA-FE-02 · Mapeo central de las cuatro unidades productivas (`OD-16.a`).
 *
 * El backend entrega `code` canónico + `name_key` (i18n). Un ÚNICO mapeo central evita
 * strings mágicos duplicados entre pantallas (AC-UI-08). Los nombres fallback son los
 * canónicos del producto: Progenitoras · Reproductoras · Incubadora · Engorde.
 */

import type { TFunction } from 'i18next'

export const BUSINESS_UNIT_CODES = ['grandparent', 'breeder', 'hatchery', 'broiler'] as const

export type BusinessUnitCode = (typeof BUSINESS_UNIT_CODES)[number]

export const BUSINESS_UNIT_FALLBACKS: Record<string, string> = {
  grandparent: 'Progenitoras',
  breeder: 'Reproductoras',
  hatchery: 'Incubadora',
  broiler: 'Engorde',
}

/** Nombre localizado de una unidad: `name_key` del backend con fallback canónico por código. */
export function businessUnitName(code: string, nameKey: string | undefined, t: TFunction): string {
  const key = nameKey || `businessUnits.${code}`
  return t(key, BUSINESS_UNIT_FALLBACKS[code] ?? code)
}

/** ¿Es una concesión viva (no revocada)? Contrato: `revoked_at === null`. */
export function isLiveGrant(grant: { revoked_at: string | null }): boolean {
  return grant.revoked_at === null
}
