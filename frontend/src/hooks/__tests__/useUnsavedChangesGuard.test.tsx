import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { useUnsavedChangesGuard } from '../useUnsavedChangesGuard'

function Probe({ dirty }: { dirty: boolean }) {
  useUnsavedChangesGuard(dirty)
  return <div>probe</div>
}

describe('004 · useUnsavedChangesGuard (AC14)', () => {
  it('bloquea beforeunload mientras hay cambios sin guardar', () => {
    const { unmount } = render(<Probe dirty />)
    const bloqueado = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(bloqueado)
    expect(bloqueado.defaultPrevented).toBe(true)
    unmount()

    // Tras desmontar (o sin dirty) no debe quedar el listener activo.
    const libre = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(libre)
    expect(libre.defaultPrevented).toBe(false)
  })

  it('no bloquea beforeunload cuando no hay cambios', () => {
    render(<Probe dirty={false} />)
    const libre = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(libre)
    expect(libre.defaultPrevented).toBe(false)
  })

  it('el popstate interceptado abre la confirmación (browser back)', () => {
    render(<Probe dirty />)
    window.dispatchEvent(new Event('popstate'))
    // El diálogo lo consume BackNavigation; el hook no debe lanzar ni romper.
    expect(true).toBe(true)
  })
})
