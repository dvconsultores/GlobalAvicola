/**
 * `F4` (AC-S1-F01) · RED jsdom — los detalles de validación de FastAPI (en inglés)
 * se muestran en español, y un aviso repetido no se apila.
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { getErrorMessage, ToastProvider, useToast } from '../Toast'

const E422_LOTE = {
  response: {
    data: {
      detail: [{
        loc: ['query', 'lot_id'],
        msg: 'Input should be a valid integer, unable to parse string as an integer',
        type: 'int_parsing',
      }],
    },
  },
}

function Disparador() {
  const toast = useToast()
  return (
    <>
      <button onClick={() => toast.error(getErrorMessage(E422_LOTE, 'Error al cargar'))}>error422</button>
      <button onClick={() => { toast.error('X'); toast.error('X') }}>duplicado</button>
    </>
  )
}

describe('F4 · detalles de validación en español', () => {
  it('detalle pydantic de `lot_id` ⇒ «Valor no válido en «lote»» sin texto en inglés', () => {
    const salida = getErrorMessage(E422_LOTE, 'Error al cargar')
    expect(salida).toBe('Valor no válido en «lote»')
    expect(salida).not.toContain('Input')
    expect(salida).not.toContain('[object Object]')
  })

  it('campos conocidos se traducen y los duplicados se descartan', () => {
    const error = {
      response: {
        data: {
          detail: [
            { loc: ['query', 'farm_id'], msg: 'Input should be a valid integer', type: 'int_parsing' },
            { loc: ['query', 'farm_id'], msg: 'Input should be a valid integer', type: 'int_parsing' },
            { loc: ['query', 'house_id'], msg: 'Input should be a valid integer', type: 'int_parsing' },
            { loc: ['body', 'event_date'], msg: 'Input should be a valid date', type: 'date_parsing' },
            { loc: ['body', 'custom_field'], msg: 'Field required', type: 'missing' },
          ],
        },
      },
    }
    // `F6` §4: el item `missing` se nombra como obligatorio que falta; el resto sigue igual.
    expect(getErrorMessage(error, 'fallback')).toBe(
      'Valor no válido en «granja» · Valor no válido en «galpón» · Valor no válido en «fecha»'
      + ' · Falta el dato obligatorio «custom_field»',
    )
  })

  it('`type: missing` sin campo localizable ⇒ «Falta un dato obligatorio»', () => {
    expect(getErrorMessage({ response: { data: { detail: [{ type: 'missing', msg: 'Field required' }] } } }, 'x'))
      .toBe('Falta un dato obligatorio')
  })

  it('los mensajes ya redactados en español se conservan', () => {
    expect(getErrorMessage({ response: { data: { detail: 'Lot no encontrado' } } }, 'x')).toBe('Lot no encontrado')
    expect(getErrorMessage({ response: { data: { detail: [{ message: 'El lote está cerrado' }] } } }, 'x'))
      .toBe('El lote está cerrado')
  })

  it('el aviso llega al toast sin texto en inglés', async () => {
    render(<ToastProvider><Disparador /></ToastProvider>)
    fireEvent.click(screen.getByText('error422'))
    expect(await screen.findByText('Valor no válido en «lote»')).toBeTruthy()
    expect(screen.queryByText(/Input should be/i)).toBeNull()
  })

  it('dos toasts iguales dejan un único aviso', async () => {
    render(<ToastProvider><Disparador /></ToastProvider>)
    fireEvent.click(screen.getByText('duplicado'))
    expect((await screen.findAllByText('X')).length).toBe(1)
  })
})
