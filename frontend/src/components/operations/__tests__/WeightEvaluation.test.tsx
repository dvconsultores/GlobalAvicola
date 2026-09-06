/**
 * Presentación de la evaluación de peso — `AC-FE11`, `AC-FE12`, `AC-FE13`, `AC-FE14`.
 *
 * `R-97`. Antes, «dentro de norma» y «sin referencia» se veían igual desde fuera: sin nada.
 * Estas pruebas fijan que ahora se distinguen **por texto**, no por la ausencia de una señal
 * ni por un color.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import WeightEvaluation from '../WeightEvaluation'

const get = vi.fn()
vi.mock('../../../services/api', () => ({ default: { get: (...a: any[]) => get(...a) } }))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (clave: string, opciones?: any) =>
      opciones?.days !== undefined ? `${clave}:${opciones.days}` : clave,
    i18n: { language: 'es' },
  }),
}))

function respuesta(fila: any, extra: any = {}) {
  return {
    data: {
      event_id: 1, lot_id: 2, age_days: 15, curve_version_label: 'v2024', reason: null,
      evaluations: [fila], ...extra,
    },
  }
}

beforeEach(() => { get.mockReset() })

describe('WeightEvaluation', () => {
  it('`AC-FE12` · un peso bajo norma se nombra y muestra su rango', async () => {
    get.mockResolvedValue(respuesta({
      avg_weight: 100, status: 'below_standard',
      expected_min: 135, expected_target: 150, expected_max: 165,
    }))
    render(<WeightEvaluation eventId={1} />)

    expect(await screen.findByText('curves.below')).toBeInTheDocument()
    expect(screen.getByText(/135–165 g/)).toBeInTheDocument()
    expect(screen.queryByText('curves.within')).not.toBeInTheDocument()
  })

  it('`AC-FE12` · un peso dentro de norma también muestra su rango', async () => {
    get.mockResolvedValue(respuesta({
      avg_weight: 150, status: 'within_standard',
      expected_min: 135, expected_target: 150, expected_max: 165,
    }))
    render(<WeightEvaluation eventId={1} />)

    expect(await screen.findByText('curves.within')).toBeInTheDocument()
    // Sin esto, «dentro de norma» sería indistinguible de «sin referencia»: las dos callarían.
    expect(screen.getByText(/135–165 g/)).toBeInTheDocument()
  })

  it('`AC-FE12` · un peso sobre norma se distingue del que está bajo ella', async () => {
    get.mockResolvedValue(respuesta({
      avg_weight: 200, status: 'above_standard',
      expected_min: 135, expected_target: 150, expected_max: 165,
    }))
    render(<WeightEvaluation eventId={1} />)

    expect(await screen.findByText('curves.above')).toBeInTheDocument()
    expect(screen.queryByText('curves.below')).not.toBeInTheDocument()
  })

  it('`AC-FE13` · sin referencia se declara, y nunca como normalidad', async () => {
    get.mockResolvedValue(respuesta({
      avg_weight: 5, status: 'no_reference',
      expected_min: null, expected_target: null, expected_max: null,
    }, { age_days: null, curve_version_label: null, reason: 'no_curve_assigned' }))
    render(<WeightEvaluation eventId={1} />)

    expect(await screen.findByText('curves.noReference')).toBeInTheDocument()
    expect(screen.getByText('curves.noReferenceHelp')).toBeInTheDocument()
    expect(screen.queryByText('curves.within')).not.toBeInTheDocument()
    // Ni un cero disfrazado de rango: cero engañaría igual que callar.
    expect(screen.queryByText(/0–0/)).not.toBeInTheDocument()
  })

  it('`AC-FE11` · cita la versión de curva y la edad que el backend usó', async () => {
    get.mockResolvedValue(respuesta({
      avg_weight: 150, status: 'within_standard',
      expected_min: 135, expected_target: 150, expected_max: 165,
    }))
    render(<WeightEvaluation eventId={7} />)

    expect(await screen.findByText('v2024')).toBeInTheDocument()
    expect(screen.getByText('curves.atAge:15')).toBeInTheDocument()
    expect(get).toHaveBeenCalledWith('/operations/7/weight-evaluation')
  })

  it('`AC-FE14` · no calcula: pinta exactamente lo que el backend concluyó', async () => {
    // El estado contradice al rango a propósito. Si el componente interpolara o clasificara
    // por su cuenta, lo «corregiría» — y habría dos motores.
    get.mockResolvedValue(respuesta({
      avg_weight: 150, status: 'below_standard',
      expected_min: 135, expected_target: 150, expected_max: 165,
    }))
    render(<WeightEvaluation eventId={1} />)

    expect(await screen.findByText('curves.below')).toBeInTheDocument()
    expect(screen.queryByText('curves.within')).not.toBeInTheDocument()
  })

  it('no pinta nada si el evento no trae pesajes', async () => {
    get.mockResolvedValue(respuesta(null, { evaluations: [] }))
    const { container } = render(<WeightEvaluation eventId={1} />)
    await waitFor(() => expect(get).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })
})
