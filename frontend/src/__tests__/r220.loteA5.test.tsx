/**
 * R-220 · RED — Lote A, quinta tanda: A7 (C#32 / INT-30).
 *   - `destino()` solo conoce `operational_event`: los avisos de `lot` y
 *     `sap_payload` se marcan leídos y no navegan a ninguna parte.
 *   - Guardia de textos: los 6 tipos deben tener redacción ES y EN.
 */
import { describe, it, expect } from 'vitest'

import { destino, type Notification } from '../services/notifications'
import es from '../../public/locales/es/translation.json'
import en from '../../public/locales/en/translation.json'

function aviso(tipo: string | null, id: number | null): Notification {
  return {
    id: 1, company_id: 1, recipient_user_id: 1,
    notification_type: 'record_rejected',
    payload: {}, related_entity_type: tipo, related_entity_id: id,
    created_at: '2026-09-14T10:00:00Z', read_at: null,
  }
}

const TIPOS = ['record_rejected', 'sap_send_failed', 'mortality_over_threshold',
  'weight_out_of_standard', 'review_pending_24h', 'lot_near_close']

describe('R-220 · Lote A quinta tanda (RED)', () => {
  it('AC-R220-A·A7 · los avisos de lote y de payload SAP tienen destino', () => {
    expect(destino(aviso('lot', 7))).toBe('/lots/7')
    expect(destino(aviso('sap_payload', 12))).toBe('/sap')
  })

  it('AC-R220-A·A7 · control: el evento operativo conserva su destino', () => {
    expect(destino(aviso('operational_event', 55))).toBe('/operations/55')
    expect(destino(aviso(null, null))).toBeNull()
  })

  it('AC-R220-A·A7 · guardia de textos: los 6 tipos están redactados en ES y EN', () => {
    for (const tipo of TIPOS) {
      expect((es as any).notifications.types[tipo], `ES sin ${tipo}`).toBeTruthy()
      expect((en as any).notifications.types[tipo], `EN sin ${tipo}`).toBeTruthy()
      expect((en as any).notifications.types[tipo]).not.toBe((es as any).notifications.types[tipo])
    }
  })
})
