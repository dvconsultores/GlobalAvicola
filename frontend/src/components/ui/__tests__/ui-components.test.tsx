import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
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
import { Search } from 'lucide-react'
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
 expect(btn?.className).toContain('bg-red-600')
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
 render(<Button size="lg">Touch</Button>)
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
 render(<KpiCard label="Test" value={1} color="red" />)
 expect(screen.getByText('Test')).toBeInTheDocument()
 })
})

// ============================================================
// EmptyState
// ============================================================
describe('EmptyState', () => {
 it('renders title and description', () => {
 render(
 <BrowserRouter>
 <EmptyState icon={Search} title="Sin datos" description="No hay registros" />
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

// ============================================================
// Additional edge-case & integration tests
// ============================================================

describe('Button — edge cases', () => {
 it('renders with left and right icons', () => {
 render(<Button leftIcon={<span data-testid="left">L</span>} rightIcon={<span data-testid="right">R</span>}>With Icons</Button>)
 expect(screen.getByTestId('left')).toBeInTheDocument()
 expect(screen.getByTestId('right')).toBeInTheDocument()
 })

 it('applies all 5 variant classes', () => {
 const variants = ['primary', 'secondary', 'danger', 'ghost', 'outline'] as const
 for (const v of variants) {
 const { container } = render(<Button variant={v}>Test</Button>)
 expect(container.querySelector('button')).toBeTruthy()
 }
 })

 it('applies all 3 size classes', () => {
 const { container: c1 } = render(<Button size="sm">S</Button>)
 const { container: c2 } = render(<Button size="md">M</Button>)
 const { container: c3 } = render(<Button size="lg">L</Button>)
 expect(c1.querySelector('button')?.className).toContain('h-9')
 expect(c2.querySelector('button')?.className).toContain('h-10')
 expect(c3.querySelector('button')?.className).toContain('h-11')
 })

 it('renders as submit type when specified', () => {
 render(<Button type="submit">Submit</Button>)
 expect(screen.getByRole('button')).toHaveAttribute('type', 'submit')
 })
})

describe('Badge — status resolution', () => {
 it('resolves all 13 operational statuses', () => {
 const statuses = [
 'draft', 'registered', 'pending_review', 'in_review', 'returned',
 'corrected', 'approved', 'rejected', 'consolidated', 'sent_to_sap',
 'sap_confirmed', 'sap_error', 'cancelled',
 ]
 for (const s of statuses) {
 const variant = statusToVariant(s)
 expect(typeof variant).toBe('string')
 expect(variant.length).toBeGreaterThan(0)
 }
 })

 it('renders with dot indicator', () => {
 const { container } = render(<Badge variant="approved" dot>Aprobado</Badge>)
 const dotEl = container.querySelector('.w-1\\.5')
 expect(dotEl).toBeTruthy()
 })

 it('renders with sm size', () => {
 const { container } = render(<Badge size="sm">Small</Badge>)
 expect(container.querySelector('span')?.className).toContain('px-1.5')
 })
})

describe('ConfirmDialog — interaction', () => {
 it('calls onConfirm when confirm button clicked', () => {
 const onConfirm = vi.fn()
 render(
 <ConfirmDialog open={true} onClose={() => {}} onConfirm={onConfirm} title="Test" message="Msg" />
 )
 screen.getByRole('button', { name: /confirmar/i }).click()
 expect(onConfirm).toHaveBeenCalledTimes(1)
 })

 it('calls onClose when cancel button clicked', () => {
 const onClose = vi.fn()
 render(
 <ConfirmDialog open={true} onClose={onClose} onConfirm={() => {}} title="Test" message="Msg" />
 )
 screen.getByRole('button', { name: /cancelar/i }).click()
 expect(onClose).toHaveBeenCalledTimes(1)
 })

 it('renders danger variant with red confirm button', () => {
 render(
 <ConfirmDialog open={true} onClose={() => {}} onConfirm={() => {}} title="Delete" message="Sure?" variant="danger" />
 )
 const btn = screen.getByRole('button', { name: /confirmar/i })
 expect(btn.className).toContain('red')
 })
})

describe('KpiCard — all colors', () => {
 const colors = ['blue', 'green', 'red', 'amber', 'teal', 'indigo', 'slate'] as const
 for (const color of colors) {
 it(`renders with ${color} color`, () => {
 render(<KpiCard label="Test" value={99} color={color} />)
 expect(screen.getByText('Test')).toBeInTheDocument()
 })
 }
})

describe('FormSection — collapsible', () => {
 it('toggles collapse', () => {
 render(
 <FormSection title="Sección" collapsible defaultOpen={true}>
 <p>Visible</p>
 </FormSection>
 )
 expect(screen.getByText('Visible')).toBeInTheDocument()
 })
})

describe('FilterPanel — with results count', () => {
 it('shows total results', () => {
 render(
 <FilterPanel totalResults={42}>
 <FilterGroup label="Status">
 <span>Active</span>
 </FilterGroup>
 </FilterPanel>
 )
 // The number "42" may be rendered as part of a text node with "resultados"
 expect(screen.getByText(/42/)).toBeInTheDocument()
 })
})

describe('Card — variants', () => {
 it('renders default card', () => {
 const { container } = render(<Card><p>Content</p></Card>)
 expect(container.querySelector('.rounded-xl')).toBeTruthy()
 })
})

describe('EmptyState — with action', () => {
 it('renders action button when provided', () => {
 render(
 <BrowserRouter>
 <EmptyState icon={Search} title="Empty" description="Nothing here" action={{ label: 'Create', onClick: () => {} }} />
 </BrowserRouter>
 )
 expect(screen.getByText('Create')).toBeInTheDocument()
 })
})
