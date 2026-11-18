/**
 * `UAT S1` · `AC-S1-U01` (el toast no queda bajo el overlay) y `AC-S1-I03`
 * (los estados/acciones del backend se nombran traducidos, no en crudo).
 *
 * Un toast invisible porque un modal lo tapa es un aviso perdido: el `ConfirmDialog`
 * vive en un portal con `z-[60]`, así que el contenedor de toasts debe ir por encima.
 * Y un código crudo (`started_review`, `no_curve_assigned`) en pantalla no es texto
 * para el usuario: estas claves tienen que existir en los dos idiomas.
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { ToastProvider, useToast } from '../components/Toast'

function Disparador() {
  const toast = useToast()
  return <button onClick={() => toast.success('Registro guardado')}>disparar</button>
}

function cargarIdioma(idioma: 'es' | 'en'): any {
  // vitest se ejecuta desde `frontend/`: los JSON viven en `public/locales`.
  const ruta = resolve(process.cwd(), 'public', 'locales', idioma, 'translation.json')
  return JSON.parse(readFileSync(ruta, 'utf8'))
}

describe('UAT S1 · toast por encima de overlays', () => {
  it('el contenedor de toasts usa z-[70] (por encima del overlay z-[60])', () => {
    render(
      <ToastProvider>
        <Disparador />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    // El mensaje se pinta…
    expect(screen.getByText('Registro guardado')).toBeInTheDocument()

    // …y su contenedor queda por encima del modal de confirmación. `F8`: el contenedor
    // vive en un portal sobre `document.body`, no dentro del contenedor de render.
    const contenedor = document.body.querySelector('[class*="z-[70]"]')
    expect(contenedor).not.toBeNull()
    expect(contenedor).toHaveClass('fixed', 'top-4', 'right-4')
    expect(document.body.querySelector('[class*="z-50"]')).toBeNull()
  })
})

describe('UAT S1 · claves de traducción de estados y acciones', () => {
  const ACCIONES_AUDITORIA = ['started_review']
  const ACCIONES_REVISION = ['start', 'complete', 'return']
  const MOTIVOS_CURVA = [
    'no_curve_assigned',
    'lot_without_start_date',
    'lot_without_genetic_line',
    'curve_without_points',
    'event_before_lot_start',
    'age_outside_curve_table',
  ]

  for (const idioma of ['es', 'en'] as const) {
    it(`${idioma} · existen todas las claves (y con texto no vacío)`, () => {
      const t = cargarIdioma(idioma)

      for (const accion of ACCIONES_AUDITORIA) {
        expect(t.audit?.actions?.[accion], `audit.actions.${accion}`).toBeTruthy()
      }
      for (const accion of ACCIONES_REVISION) {
        expect(t.review?.actionDone?.[accion], `review.actionDone.${accion}`).toBeTruthy()
      }
      for (const motivo of MOTIVOS_CURVA) {
        expect(t.curves?.reasons?.[motivo], `curves.reasons.${motivo}`).toBeTruthy()
      }
      expect(t.lotStatus?.active, 'lotStatus.active').toBeTruthy()
    })
  }

  it('el texto es español en es y su equivalente en en', () => {
    const es = cargarIdioma('es')
    const en = cargarIdioma('en')

    expect(es.audit.actions.started_review).toBe('Revisión iniciada')
    expect(en.audit.actions.started_review).toBe('Review started')
    expect(es.review.actionDone.start).toBe('Revisión iniciada')
    expect(es.review.actionDone.complete).toBe('Revisión completada')
    expect(es.review.actionDone.return).toBe('Registro devuelto')
    expect(en.review.actionDone.start).toBe('Review started')
    expect(en.review.actionDone.complete).toBe('Review completed')
    expect(en.review.actionDone.return).toBe('Record returned')
    expect(es.lotStatus.active).toBe('Activo')
    expect(en.lotStatus.active).toBe('Active')
  })
})
