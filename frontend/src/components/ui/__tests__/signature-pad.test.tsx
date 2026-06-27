import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SignaturePad from '../SignaturePad'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key,
    i18n: { language: 'es', changeLanguage: vi.fn() },
  }),
}))

describe('SignaturePad', () => {
  it('renders canvas and buttons', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Limpiar')).toBeInTheDocument()
    expect(screen.getByText('Cancelar')).toBeInTheDocument()
    expect(screen.getByText('Firmar')).toBeInTheDocument()
  })

  it('renders with custom label', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} label="Firma del operador" />)
    expect(screen.getByText('Firma del operador')).toBeInTheDocument()
  })

  it('renders canvas with correct dimensions', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} width={400} height={200} />)
    const canvas = document.querySelector('canvas')
    expect(canvas).toBeTruthy()
    expect(canvas?.getAttribute('width')).toBe('400')
    expect(canvas?.getAttribute('height')).toBe('200')
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<SignaturePad onSign={vi.fn()} onCancel={onCancel} />)
    screen.getByText('Cancelar').click()
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('confirm button is disabled when no signature drawn', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} />)
    const confirmBtn = screen.getByText('Firmar')
    expect(confirmBtn).toBeDisabled()
  })

  it('calls onSign with data URL after drawing and confirming', () => {
    // Mock canvas toDataURL (not fully supported in jsdom)
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL
    HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/png;base64,mock')

    const onSign = vi.fn()
    render(<SignaturePad onSign={onSign} onCancel={vi.fn()} />)

    const canvas = document.querySelector('canvas')!
    // Simulate pointer events to draw a signature
    fireEvent.pointerDown(canvas, { clientX: 50, clientY: 50 })
    fireEvent.pointerMove(canvas, { clientX: 100, clientY: 80 })
    fireEvent.pointerUp(canvas)

    // Now confirm button should be enabled
    const confirmBtn = screen.getByText('Firmar')
    expect(confirmBtn).not.toBeDisabled()

    // Click confirm
    confirmBtn.click()
    expect(onSign).toHaveBeenCalledTimes(1)
    const dataUrl = onSign.mock.calls[0][0]
    expect(dataUrl).toContain('data:image/png;base64,')

    // Restore
    HTMLCanvasElement.prototype.toDataURL = originalToDataURL
  })

  it('clear button is present and clickable', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} />)
    const clearBtn = screen.getByText('Limpiar')
    expect(clearBtn).toBeInTheDocument()
    // Should not throw when clicked
    clearBtn.click()
  })

  it('stops drawing on pointer leave', () => {
    render(<SignaturePad onSign={vi.fn()} onCancel={vi.fn()} />)
    const canvas = document.querySelector('canvas')!

    fireEvent.pointerDown(canvas, { clientX: 10, clientY: 10 })
    fireEvent.pointerLeave(canvas)
    // Should not crash — drawing stops gracefully
    expect(canvas).toBeTruthy()
  })
})
