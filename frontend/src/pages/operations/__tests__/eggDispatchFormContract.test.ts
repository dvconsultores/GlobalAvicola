// Contrato estático del formulario de despacho de huevos — `R-172` (`GA-REM-005-F`, `RR-17`).
// A la incubadora solo se despacha huevo fértil (`Bases` p.7-9, `docs/02 §3.6.4/§3.7.1`): el formulario no ofrece filas
// que el backend rechaza. La recolección conserva sus cinco tipos (hechos capturados).
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const fuente = readFileSync(resolve(__dirname, '../OperationFormPage.tsx'), 'utf8')

function bloque(desde: string, hasta: string): string {
  const i = fuente.indexOf(desde)
  const j = fuente.indexOf(hasta, i + desde.length)
  expect(i, desde).toBeGreaterThan(-1)
  expect(j, hasta).toBeGreaterThan(i)
  return fuente.slice(i, j)
}

describe('formulario de despacho de huevos · R-172 (solo huevo fértil)', () => {
  it('AC-R172-08 · el caso egg_dispatch registra únicamente la fila fertile', () => {
    const despacho = bloque("case 'egg_dispatch':", "case 'egg_reception_hatchery':")
    expect(despacho).toContain("key: 'fertile'")
    for (const tipo of ['dirty', 'broken', 'infertile', 'discarded', 'commercial']) {
      expect(despacho, tipo).not.toContain(`key: '${tipo}'`)
    }
    expect(despacho).toContain('egg_movements.${i}.egg_type')
  })
  it('AC-R172-08 · la recolección conserva los cinco tipos capturados', () => {
    const recoleccion = bloque("case 'egg_collection':", "case 'egg_dispatch':")
    for (const tipo of ['fertile', 'dirty', 'broken', 'infertile', 'discarded']) {
      expect(recoleccion, tipo).toContain(`key: '${tipo}'`)
    }
  })
})
