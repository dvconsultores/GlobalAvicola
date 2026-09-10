// `GA-REM-021` enmienda A · `B05`: el consumo de agua se ofrece solo donde el cliente lo exige
// (`Bases` p.2, 4, 12): Reproductoras (cría y producción) y Engorde. Ni Incubadora ni Progenitoras.
import { describe, expect, it } from 'vitest'
import { STAGE_OPERATIONS } from '../processCatalog'

describe('processCatalog · water_consumption (B05)', () => {
  it('está en breeder_rearing, breeder_production y broiler', () => {
    for (const stage of ['breeder_rearing', 'breeder_production', 'broiler'] as const) {
      expect(STAGE_OPERATIONS[stage]).toContain('water_consumption')
    }
  })
  it('no está en grandparent_* ni en hatchery (no aplica por fuente)', () => {
    for (const stage of ['grandparent_rearing', 'grandparent_production', 'hatchery'] as const) {
      expect(STAGE_OPERATIONS[stage]).not.toContain('water_consumption')
    }
  })
})

// `GA-REM-021` enmienda D · `R-171` (`RR-16`): la etapa de incubadora ofrece la mortalidad y el descarte de pollitos,
// que son lo que viables y rendimiento restan (`Bases` p.10, Rec. §12). El backend ya los acepta (`AC-R161-16`);
// el catálogo era lo único que faltaba. Sin cadena i18n nueva: las claves ya existen en ES y EN.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { STAGE_FLOWS } from '../processCatalog'

const es = JSON.parse(readFileSync(resolve(__dirname, '../../../public/locales/es/translation.json'), 'utf8'))
const en = JSON.parse(readFileSync(resolve(__dirname, '../../../public/locales/en/translation.json'), 'utf8'))

// Instantánea del catálogo en `4f70273` (antes de R-171): ninguna etapa pierde nada; solo hatchery gana dos.
const EN_4F70273: Record<string, string[]> = {
  grandparent_rearing: [
    'grandparent_import', 'farm_inspection', 'bird_reception', 'bird_distribution',
    'bird_transfer', 'transport_inspection', 'feed_registration', 'weight_recording',
    'mortality_recording', 'cull_recording', 'vaccination', 'medication', 'bird_exit',
  ],
  grandparent_production: [
    'farm_inspection', 'bird_transfer', 'transport_inspection', 'feed_registration',
    'weight_recording', 'mortality_recording', 'cull_recording', 'vaccination',
    'medication', 'egg_collection', 'egg_dispatch', 'bird_exit',
  ],
  breeder_rearing: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'bird_transfer',
    'transport_inspection', 'feed_registration', 'water_consumption', 'weight_recording', 'mortality_recording',
    'cull_recording', 'vaccination', 'medication', 'bird_exit',
  ],
  breeder_production: [
    'farm_inspection', 'bird_transfer', 'transport_inspection', 'feed_registration',
    'water_consumption', 'weight_recording', 'mortality_recording', 'cull_recording', 'vaccination',
    'medication', 'egg_collection', 'egg_dispatch', 'bird_exit',
  ],
  hatchery: [
    'hatchery_inspection', 'egg_reception_hatchery', 'egg_reception_classification', 'transport_inspection',
    'incubation_load', 'ovoscopy', 'transfer_to_hatcher', 'birth_registration', 'chick_dispatch',
  ],
  broiler: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'bird_transfer',
    'transport_inspection', 'feed_registration', 'water_consumption', 'weight_recording', 'mortality_recording',
    'cull_recording', 'vaccination', 'medication', 'bird_exit', 'lot_closure',
  ],
}

describe('processCatalog · incubadora ofrece mortalidad y descarte de pollitos (R-171 · GA-REM-021-D)', () => {
  it('AC-R171-01 · STAGE_OPERATIONS.hatchery contiene mortality_recording', () => {
    expect(STAGE_OPERATIONS.hatchery).toContain('mortality_recording')
  })
  it('AC-R171-02 · STAGE_OPERATIONS.hatchery contiene cull_recording', () => {
    expect(STAGE_OPERATIONS.hatchery).toContain('cull_recording')
  })
  it('AC-R171-03 · el flujo de incubadora tiene ambos pasos, tras el nacimiento y antes del despacho, con su clave de descripción', () => {
    const eventos = STAGE_FLOWS.hatchery.map((s) => s.event)
    const nacimiento = eventos.indexOf('birth_registration')
    const despacho = eventos.indexOf('chick_dispatch')
    for (const ev of ['mortality_recording', 'cull_recording']) {
      const i = eventos.indexOf(ev)
      expect(i, `${ev} en el flujo`).toBeGreaterThan(nacimiento)
      expect(i, `${ev} antes del despacho`).toBeLessThan(despacho)
      expect(STAGE_FLOWS.hatchery[i].descKey).toBe(`process.flowDesc.${ev}`)
    }
  })
  it('AC-R171-04 · las etiquetas ES/EN existen y no están vacías (sin cadena nueva ni texto fijo)', () => {
    for (const idioma of [es, en]) {
      for (const ev of ['mortality_recording', 'cull_recording']) {
        expect(idioma.events[ev], `events.${ev}`).toBeTruthy()
        expect(idioma.eventsShort[ev], `eventsShort.${ev}`).toBeTruthy()
        expect(idioma.process.flowDesc[ev], `process.flowDesc.${ev}`).toBeTruthy()
      }
    }
    expect(es.events.mortality_recording).toBe('Registro de Mortalidad')
    expect(es.events.cull_recording).toBe('Registro de Descarte')
    expect(en.events.mortality_recording).toBe('Mortality Recording')
    expect(en.events.cull_recording).toBe('Cull Recording')
  })
  it('AC-R171-05 · aplicabilidad: las demás etapas no cambian y hatchery solo gana los dos eventos', () => {
    for (const etapa of ['grandparent_rearing', 'grandparent_production', 'breeder_rearing', 'breeder_production', 'broiler'] as const) {
      expect(STAGE_OPERATIONS[etapa], etapa).toEqual(EN_4F70273[etapa])
    }
    const hatchery = STAGE_OPERATIONS.hatchery.filter((e) => e !== 'mortality_recording' && e !== 'cull_recording')
    expect(hatchery).toEqual(EN_4F70273.hatchery)
  })
})
