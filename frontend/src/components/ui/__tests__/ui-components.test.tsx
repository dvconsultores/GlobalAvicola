import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Button } from '../Button'
import { Input } from '../Input'
import { Card, CardHeader, CardBody } from '../Card'
import { Badge, statusToVariant } from '../Badge'

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
