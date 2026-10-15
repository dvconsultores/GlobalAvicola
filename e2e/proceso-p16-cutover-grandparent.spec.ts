/**
 * P-16-GP — PROGENITORAS — CARGAS INICIALES v2 (SPEC 006 · remediación post-certificación de GA-REQ-061).
 *
 * Certificación por BU **sin transitividad**: este spec recorre por la interfaz el ciclo completo
 * (crear carga → plantilla de la unidad → subir XLSX → validar → preview → enviar → aprobar con
 * otro actor → aplicar → reconciliación → lote migrado → primer evento post-corte → CUT-GL-02).
 * El journal queda en `test-results/spec-006/e2e-grandparent-xlsx.json`.
 */
import { test } from '@playwright/test'
import { flujoPorBu } from '../test-support/cutover-flow'

test.describe('P-16 · Cargas Iniciales v2 — progenitoras', () => {
  test('grandparent: ciclo completo por UI con plantilla XLSX y primer evento post-corte', async ({ page, browser, request }) => {
    test.setTimeout(180_000)
    await flujoPorBu(page, browser, request, { bu: 'grandparent', formato: 'xlsx' })
  })
})
