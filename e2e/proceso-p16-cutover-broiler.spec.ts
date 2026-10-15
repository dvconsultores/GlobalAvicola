/**
 * P-16-ENG — POLLO DE ENGORDE — CARGAS INICIALES v2 (SPEC 006 · remediación post-certificación de GA-REQ-061).
 *
 * Certificación por BU **sin transitividad**: este spec recorre por la interfaz el ciclo completo
 * (crear carga → plantilla de la unidad → subir CSV → validar → preview → enviar → aprobar con
 * otro actor → aplicar → reconciliación → lote migrado → primer evento post-corte → CUT-GL-02).
 * El journal queda en `test-results/spec-006/e2e-broiler-csv.json`.
 */
import { test } from '@playwright/test'
import { flujoPorBu } from '../test-support/cutover-flow'

test.describe('P-16 · Cargas Iniciales v2 — engorde', () => {
  test('broiler: ciclo completo por UI con plantilla CSV y primer evento post-corte', async ({ page, browser, request }) => {
    test.setTimeout(180_000)
    await flujoPorBu(page, browser, request, { bu: 'broiler', formato: 'csv' })
  })
})
