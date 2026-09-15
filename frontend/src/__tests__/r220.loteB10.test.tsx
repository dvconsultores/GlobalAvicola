/**
 * R-220 · B10 (F §3, G-27) — RED: cosméticos R7–R12/R14/R15.
 *
 * ítems de PRESENTACIÓN/CSS (wraps, inputMode, chevron): no hay comportamiento
 * runtime observable en jsdom, así que la guarda es textual sobre la fuente del
 * componente — es una verificación de artefacto, documentada como tal.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

// Nota: en jsdom el `URL` global resuelve contra `http://localhost:3000` — se usa
// resolución de node para leer las fuentes.
const here = dirname(fileURLToPath(import.meta.url))
const src = (rel: string) => readFileSync(resolve(here, '..', rel), 'utf8')

describe('R-220 · B10 · cosméticos R7–R12/R14/R15', () => {
  it('R7 · ReviewDetail: los renglones observación+botón envuelven en <420px', () => {
    const s = src('pages/review/ReviewDetail.tsx')
    // Dos contenedores (revisión y devolución) deben poder envolver.
    expect((s.match(/flex flex-wrap gap-2 items-center/g) ?? []).length).toBe(2)
  })

  it('R8 · Toast: contenedor limitado al viewport en móvil (no sobresale a 390px)', () => {
    const s = src('components/Toast.tsx')
    expect(s).toContain('max-w-[calc(100vw-2rem)]')
    expect(s).not.toContain('gap-2 max-w-sm')
  })

  it('R9 · OperationFormPage: etiqueta de parámetros a ancho completo en móvil', () => {
    const s = src('pages/operations/OperationFormPage.tsx')
    expect(s).toContain('flex flex-wrap items-center gap-3')
    expect(s).toContain('w-full sm:w-44 shrink-0')
  })

  it('R10 · Dashboard: KPIs apilan en <420px (sin corte de etiquetas)', () => {
    const s = src('pages/dashboard/DashboardPage.tsx')
    expect(s).toContain('max-[419px]:grid-cols-1')
    expect(s).not.toContain('grid grid-cols-3 gap-2.5"')
  })

  it('R11 · LotDetail: cabecera con wrap (el título no se comprime)', () => {
    const s = src('pages/lots/LotDetailPage.tsx')
    expect(s).toContain('flex flex-wrap items-center gap-3 mb-6')
  })

  it('R12 · ApprovalPanel: barra de lote con wrap', () => {
    const s = src('pages/approvals/ApprovalPanel.tsx')
    expect(s).toContain('flex flex-wrap items-center justify-between gap-2 shadow-sm')
  })

  it('R14 · los 65 input number declaran inputMode decimal', () => {
    const s = src('pages/operations/OperationFormPage.tsx')
    const nums = (s.match(/type="number"/g) ?? []).length
    const modes = (s.match(/type="number" inputMode="decimal"/g) ?? []).length
    expect(nums).toBe(65)
    expect(modes).toBe(nums)
  })

  it('R15 · selects <1024px con chevron propio (no "parecen inputs")', () => {
    const s = src('index.css')
    expect(s).not.toContain('background-image: none !important;')
    expect(s).toContain('data:image/svg+xml')
  })
})
