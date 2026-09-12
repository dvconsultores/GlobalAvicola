/**
 * R-153 · OD-25 (B) — contrato estático del frontend de la importación sin lote.
 *
 * Pre-fix: la UI FUERZA lote para `grandparent_import` (superRefine + selector) y el detalle
 * no enlaza el lote. Estas aserciones fijan el contrato de la implementación (ROJO antes del fix).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const form = readFileSync(resolve(__dirname, '../OperationFormPage.tsx'), 'utf8')
const detail = readFileSync(resolve(__dirname, '../OperationDetailPage.tsx'), 'utf8')
const es = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/es/translation.json'), 'utf8'))
const en = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/en/translation.json'), 'utf8'))

describe('R-153/OD-25 (B) · importación de abuelas sin lote previo', () => {
  it('AC04/36 · el esquema deja de exigir lote para grandparent_import', () => {
    expect(form).toContain('const LOT_OPTIONAL_EVENTS')
    expect(form).toContain("'grandparent_import'")
    expect(form).toContain('LOT_OPTIONAL_EVENTS.has(data.event_type)')
  })

  it('AC36 · nota informativa del lote automático (i18n ES/EN)', () => {
    expect(form).toContain('operations.importLotAutoNote')
    expect(es.operations.importLotAutoNote).toBeTruthy()
    expect(en.operations.importLotAutoNote).toBeTruthy()
  })

  it('AC38 · el detalle enlaza el lote creado y muestra el estado pendiente', () => {
    expect(detail).toContain('/lots/${')
    expect(detail).toContain('operations.lotAutoPending')
    expect(es.operations.lotAutoPending).toBeTruthy()
    expect(en.operations.lotAutoPending).toBeTruthy()
  })
})
