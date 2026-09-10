// Contrato estático del formulario de operaciones — `R-169` (`GA-REM-035-A`) y `R-168` (`GA-REM-021-C`).
// El formulario no es una segunda autoridad normativa: ni umbrales sin fuente ni campos que el esquema descarta.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const fuente = readFileSync(resolve(__dirname, '../OperationFormPage.tsx'), 'utf8')
const es = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/es/translation.json'), 'utf8'))
const en = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/en/translation.json'), 'utf8'))

describe('formulario de recepción · R-169 (sin tolerancia ±10 % sin fuente; OD-04 / BR-18)', () => {
  it('AC15 · no calcula ni muestra una diferencia porcentual con umbral frente a la cantidad declarada', () => {
    for (const simbolo of ['pctDiff', 'outOfRange', 'qtyOutOfRange', 'Math.abs(pct']) {
      expect(fuente, simbolo).not.toContain(simbolo)
    }
  })
  it('AC16 · el envío no inyecta textos generados por umbral en observations', () => {
    expect(fuente).not.toContain('sapQtyAlert')
    expect(es.operations.sapQtyAlert).toBeUndefined()
    expect(en.operations.sapQtyAlert).toBeUndefined()
    expect(es.operations.qtyOutOfRange).toBeUndefined()
    expect(en.operations.qtyOutOfRange).toBeUndefined()
  })
  it('AC17 · la tarjeta informativa de la OC se conserva', () => {
    expect(fuente).toContain("t('operations.declaredQty'")
  })
})

describe('formulario de recepción · R-168 (la muestra tomada se persiste)', () => {
  it('la recepción registra sample_size a nivel de evento y ningún campo por galpón que el esquema descarte', () => {
    expect(fuente).not.toContain('bird_movements.${i}.sample_size')
    const recepcion = fuente.slice(fuente.indexOf("case 'bird_reception'"), fuente.indexOf("case 'bird_distribution'"))
    expect(recepcion).toContain("register('sample_size'")
  })
})

describe('formulario de nacimiento · R-170 (una sola contabilidad) y B13 (sanos/débiles)', () => {
  const nacimiento = fuente.slice(fuente.indexOf("case 'birth_registration'"), fuente.indexOf("case 'birth_registration'") + 4000)
  it('AC-R170-07 · no registra una fila «Total nacidos» ni «Débiles» como nacidos; el total se deriva', () => {
    expect(nacimiento).not.toContain("t('operations.totalHatched'")
    expect(nacimiento).not.toContain("t('operations.weak'")
    expect(nacimiento).toContain("t('operations.hatchedTotalHint'")
    expect(nacimiento).not.toContain('idx: 3')
  })
  it('B13 · registra sanos y débiles como datos del evento', () => {
    expect(nacimiento).toContain("register('chicks_healthy'")
    expect(nacimiento).toContain("register('chicks_weak'")
  })
})
