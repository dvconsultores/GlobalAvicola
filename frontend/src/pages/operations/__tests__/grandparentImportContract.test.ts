// Contrato estático de la importación de abuelas — `GA-REM-042` (`R-152`, `BR-22`, `RR-19`).
// El formulario captura el plan de `docs/02 §3.4.1` con claves tipadas bajo `extra_data.import_plan.*`; el detalle lo muestra;
// los adjuntos se clasifican en las cinco clases del documento. Todo con i18n ES/EN, sin texto fijo.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const formulario = readFileSync(resolve(__dirname, '../OperationFormPage.tsx'), 'utf8')
const detalle = readFileSync(resolve(__dirname, '../OperationDetailPage.tsx'), 'utf8')
const es = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/es/translation.json'), 'utf8'))
const en = JSON.parse(readFileSync(resolve(__dirname, '../../../../public/locales/en/translation.json'), 'utf8'))

const CAMPOS_DEL_PLAN = [
  'origin_country', 'purchased_total', 'shipped_total', 'received_total', 'transit_mortality',
  'departure_date', 'arrival_date', 'reception_condition', 'quarantine_days', 'quarantine_end_date', 'initial_health_inspection',
]
const CLASES_DE_ADJUNTO = ['sanitary_document', 'import_permit', 'customs_document', 'vaccination_certificate', 'origin_certificate']

function bloque(fuente: string, desde: string, hasta: string): string {
  const i = fuente.indexOf(desde)
  const j = fuente.indexOf(hasta, i + desde.length)
  expect(i, desde).toBeGreaterThan(-1)
  expect(j, hasta).toBeGreaterThan(i)
  return fuente.slice(i, j)
}

describe('importación de abuelas · formulario (AC-R152-20)', () => {
  const caso = bloque(formulario, "case 'grandparent_import':", 'default: return (')
  it('registra cada campo del plan bajo extra_data.import_plan.*', () => {
    for (const campo of CAMPOS_DEL_PLAN) {
      expect(caso, campo).toContain(`extra_data.import_plan.${campo}`)
    }
  })
  it('ya no registra las claves libres que no eran las del documento', () => {
    for (const vieja of ['extra_data.sanitary_cert', 'extra_data.import_doc', "'extra_data.origin_country'", "'extra_data.quarantine_days'"]) {
      expect(caso, vieja).not.toContain(vieja)
    }
  })
  it('ofrece proveedor y transporte dentro de la importación y las filas ♂/♀ recibidas', () => {
    expect(caso).toContain("'supplier_id'")
    expect(caso).toContain("'transport_id'")
    expect(caso).toContain('renderMFRows(')
  })
  it('las etiquetas del plan existen en ES y EN (sin texto fijo)', () => {
    for (const clave of ['importOriginCountry', 'importPurchasedTotal', 'importShippedTotal', 'importReceivedTotal', 'importTransitMortality',
      'importDepartureDate', 'importArrivalDate', 'importReceptionCondition', 'importQuarantineDays', 'importQuarantineEndDate', 'importInitialHealthInspection']) {
      expect(es.operations[clave], `es.operations.${clave}`).toBeTruthy()
      expect(en.operations[clave], `en.operations.${clave}`).toBeTruthy()
      expect(caso, clave).toContain(`t('operations.${clave}'`)
    }
  })
})

describe('importación de abuelas · detalle y adjuntos (AC-R152-21)', () => {
  it('el detalle muestra el plan de importación con sus etiquetas', () => {
    expect(detalle).toContain('import_plan')
    for (const campo of ['origin_country', 'purchased_total', 'shipped_total', 'received_total', 'transit_mortality', 'departure_date', 'arrival_date']) {
      expect(detalle, campo).toContain(campo)
    }
  })
  it('ofrece las cinco clases de adjunto del plan al adjuntar en una importación y las etiqueta en ES/EN', () => {
    for (const clase of CLASES_DE_ADJUNTO) {
      expect(detalle, clase).toContain(clase)
      expect(es.evidence.types?.[clase], `es.evidence.types.${clase}`).toBeTruthy()
      expect(en.evidence.types?.[clase], `en.evidence.types.${clase}`).toBeTruthy()
    }
    expect(detalle).toContain("'evidence_type'")
  })
})
