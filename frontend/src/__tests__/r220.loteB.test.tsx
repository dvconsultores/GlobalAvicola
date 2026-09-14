/**
 * R-220 · RED — Lote B, primera tanda:
 *   B5 (F G-19): `/operations` (historial operativo) no tiene entrada de menú.
 *   B3 (F G-05): `/my-pending` (mis pendientes del operador) está huérfana.
 * Ambas existen como rutas y como pantallas; el problema es de descubribilidad.
 */
import { describe, it, expect } from 'vitest'

import { NAV_ITEMS } from '../data/navigationConfig'

type Nodo = { to?: string; permission?: string; children?: Nodo[] }

function rutas(items: Nodo[]): { to: string; permission?: string }[] {
  const salida: { to: string; permission?: string }[] = []
  for (const item of items) {
    if (item.to) salida.push({ to: item.to, permission: item.permission })
    if (item.children) salida.push(...rutas(item.children as Nodo[]))
  }
  return salida
}

describe('R-220 · Lote B primera tanda (RED)', () => {
  it('AC-R220-B·B5 · `/operations` tiene entrada de menú (Historial) con `operations:read`', () => {
    const entrada = rutas(NAV_ITEMS as Nodo[]).find((r) => r.to === '/operations')
    expect(entrada, 'historial operativo sin entrada de menú').toBeTruthy()
    expect(entrada?.permission).toBe('operations:read')
  })

  it('AC-R220-B·B3 · `/my-pending` tiene entrada de menú (Mis pendientes) con `operations:read`', () => {
    const entrada = rutas(NAV_ITEMS as Nodo[]).find((r) => r.to === '/my-pending')
    expect(entrada, '/my-pending huérfana').toBeTruthy()
    expect(entrada?.permission).toBe('operations:read')
  })

  it('control: las entradas existentes se conservan', () => {
    const todas = rutas(NAV_ITEMS as Nodo[]).map((r) => r.to)
    expect(todas).toContain('/lots')
    expect(todas).toContain('/')
  })
})
