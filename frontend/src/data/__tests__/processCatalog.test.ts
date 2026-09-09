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
