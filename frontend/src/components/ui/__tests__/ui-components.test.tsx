import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import { Button } from '../Button'
import { Input } from '../Input'
import { Card, CardHeader, CardBody } from '../Card'
import { Badge, statusToVariant } from '../Badge'
import Breadcrumbs from '../Breadcrumbs'
import KpiCard from '../KpiCard'
import EmptyState from '../EmptyState'
import ConfirmDialog from '../ConfirmDialog'
import FormSection from '../FormSection'
import FilterPanel, { FilterGroup } from '../FilterPanel'
import StatusTimeline from '../StatusTimeline'
import type { TimelineEvent } from '../StatusTimeline'

// Mock i18n
const mockT = (key: string, fallback?: string) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
    i18n: { language: 'es', changeLanguage: vi.fn() },
  }),
}))

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    const { container } = render(<Button variant="danger">Delete</Button>)
    const btn = container.querySelector('button')
    expect(btn?.className).toContain('bg-[#DC2626]')
  })

  it('shows loading spinner when loading', () => {
    render(<Button loading>Saving</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()
    expect(btn.querySelector('svg')).toBeTruthy()
  })

  it('disables when disabled prop is set', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  // F-01: Verify touch target size
  it('has minimum 44px height for touch targets', () => {
    render(<Button size="sm">Touch</Button>)
    const btn = screen.getByRole('button')
    const classes = btn.className
    expect(classes).toContain('h-11') // 44px
  })
})

describe('Badge', () => {
  it('renders with variant', () => {
    render(<Badge variant="approved">Aprobado</Badge>)
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
  })

  it('maps status strings to variants', () => {
    expect(statusToVariant('approved')).toBe('approved')
    expect(statusToVariant('sent_to_sap')).toBe('sent_sap')
    expect(statusToVariant('unknown_status')).toBe('neutral')
  })
})

describe('Input', () => {
  it('renders label and input', () => {
    render(<Input label="Email" placeholder="user@example.com" />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(<Input label="Email" error="Campo requerido" />)
    expect(screen.getByText('Campo requerido')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })
})

describe('Card', () => {
  it('renders header and body', () => {
    render(
      <Card>
        <CardHeader title="Título" subtitle="Subtítulo" />
        <CardBody>Contenido</CardBody>
      </Card>
    )
    expect(screen.getByText('Título')).toBeInTheDocument()
    expect(screen.getByText('Contenido')).toBeInTheDocument()
  })
})

// ============================================================
// Breadcrumbs
// ============================================================
describe('Breadcrumbs', () => {
  it('renders items with chevrons', () => {
    render(
      <BrowserRouter>
        <Breadcrumbs
          items={[
            { label: 'nav.dashboard', fallback: 'Dashboard', to: '/' },
            { label: 'nav.poultry', fallback: 'Gestión Avícola' },
          ]}
        />
      </BrowserRouter>
    )
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Gestión Avícola')).toBeInTheDocument()
  })

  it('renders nothing with empty items', () => {
    const { container } = render(<Breadcrumbs items={[]} />)
    expect(container.innerHTML).toBe('')
  })
})

// ============================================================
// KpiCard
// ============================================================
describe('KpiCard', () => {
  it('renders value and label', () => {
    render(<KpiCard label="Producción" value={1234} />)
    expect(screen.getByText('Producción')).toBeInTheDocument()
    expect(screen.getByText('1234')).toBeInTheDocument()
  })

  it('renders trend indicator', () => {
    render(<KpiCard label="Test" value={100} trend={{ direction: 'up', value: '+8%' }} />)
    expect(screen.getByText('+8%')).toBeInTheDocument()
  })

  it('renders with different color variants', () => {
    const { container } = render(<KpiCard label="Test" value={1} color="red" />)
    // KpiCard se renderiza sin errores con variantes de color
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})

// ============================================================
// EmptyState
// ============================================================
describe('EmptyState', () => {
  it('renders title and description', () => {
    const { container } = render(
      <BrowserRouter>
        <EmptyState icon={() => null} title="Sin datos" description="No hay registros" />
      </BrowserRouter>
    )
    expect(screen.getByText('Sin datos')).toBeInTheDocument()
    expect(screen.getByText('No hay registros')).toBeInTheDocument()
  })
})

// ============================================================
// ConfirmDialog
// ============================================================
describe('ConfirmDialog', () => {
  it('renders when open', () => {
    render(
      <ConfirmDialog
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        title="Confirmar Acción"
        message="¿Está seguro de continuar?"
      />
    )
    expect(screen.getByText('Confirmar Acción')).toBeInTheDocument()
    expect(screen.getByText('¿Está seguro de continuar?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    const { container } = render(
      <ConfirmDialog
        open={false}
        onClose={() => {}}
        onConfirm={() => {}}
        title="Confirmar Acción"
        message="¿Está seguro?"
      />
    )
    expect(container.innerHTML).toBe('')
  })
})

// ============================================================
// FormSection
// ============================================================
describe('FormSection', () => {
  it('renders title', () => {
    render(
      <FormSection title="Datos del Lote">
        <p>Contenido</p>
      </FormSection>
    )
    expect(screen.getByText('Datos del Lote')).toBeInTheDocument()
  })
})

// ============================================================
// FilterPanel
// ============================================================
describe('FilterPanel', () => {
  it('renders children when expanded', () => {
    render(
      <FilterPanel>
        <FilterGroup label="Fecha">
          <input placeholder="Desde" />
        </FilterGroup>
      </FilterPanel>
    )
    expect(screen.getByText('Fecha')).toBeInTheDocument()
  })
})

// ============================================================
// StatusTimeline
// ============================================================
describe('StatusTimeline', () => {
  const events: TimelineEvent[] = [
    { id: 1, date: '24/06/2026', action: 'Registro creado', user: 'Juan', type: 'create' },
    { id: 2, date: '24/06/2026', action: 'Aprobado', user: 'María', type: 'approval', description: 'Lote #123' },
  ]

  it('renders events', () => {
    render(<StatusTimeline events={events} />)
    expect(screen.getByText('Registro creado')).toBeInTheDocument()
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
  })

  it('renders nothing with empty events', () => {
    const { container } = render(<StatusTimeline events={[]} />)
    expect(container.innerHTML).toBe('')
  })
})
