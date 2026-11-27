#!/usr/bin/env python3
"""OD-HATCH-V4-02 · vitest de incubadora V4 (desde la raíz del repo): §7 post-carga → §9 pre-carga."""
import sys
from pathlib import Path

ERR = []


def R(path, old, new, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        ERR.append(f"{path}: se esperaban {count} apariciones y hay {n}: {old[:90]!r}")
        return
    p.write_text(s.replace(old, new), encoding="utf-8")


def entre(path, inicio, fin, nuevo):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    if s.count(inicio) != 1 or s.count(fin) != 1:
        ERR.append(f"{path}: marcadores no únicos ({s.count(inicio)}, {s.count(fin)}): {inicio[:70]!r}")
        return
    i, j = s.index(inicio), s.index(fin)
    p.write_text(s[:i] + nuevo + s[j:], encoding="utf-8")


F = "frontend/src/__tests__/cutoverHatcheryV4.test.tsx"
R(F, """ *   - «Huevos en proceso» se pinta tal como lo entrega la API: SPEC 018 §7 · D-12
 *     (`set − transferred − fosa` solo si los tres son KNOWN) es regla de servidor; la UI no
 *     calcula nada y un `null` es UNKNOWN, jamás 0 ni una cifra inventada.""",
  """ *   - «Huevos en proceso» y «Saldo disponible para cargar» se pintan tal como los entrega la API:
 *     SPEC 018 §9 · D-23/D-24 (`set − transferred`; `received − set − no incubables − fosa` solo si
 *     todo es KNOWN) son reglas de servidor; la UI no calcula nada y un `null` es UNKNOWN.""")
R(F, """    // SPEC 018 §7 · D-12: `null` aquí significa «falta un KNOWN» (transferidos), nunca «fosa > 0».""",
  """    // SPEC 018 §9 · D-23: `null` aquí significa «transferidos UNKNOWN»; la fosa ya no interviene.""")

entre(F, "/**\n * SPEC 018 §7 · AMENDMENT OD-HATCH-V4-01 = RATIFIED (2026-11-21): la fosa es POST-CARGA.",
      "/**\n * SPEC 018 §8 · RESIDUAL O-15", '''/**
 * SPEC 018 §9 · OD-HATCH-V4-02 = RATIFIED (2026-11-26): la fosa es PRE-CARGA (OD-HATCH-V4-01, que la
 * situaba después de la carga, queda SUPERSEDED). Pre-carga: recibidos → no incubables → fosa →
 * cargados → saldo disponible para cargar; post-carga: cargados → transferidos → en proceso
 * (`set − transferred`, sin la fosa). El cálculo vive en el backend; aquí se protege el orden de las
 * dos etapas y que la pantalla pinte exactamente lo que recibe.
 */
const COLUMNAS_V4_ETAPAS = [
  'legacy_lot_code', 'eggs_received', 'eggs_non_incubable_oversized', 'eggs_non_incubable_dirty',
  'eggs_non_incubable_broken', 'fertile_eggs_to_pit', 'eggs_set', 'eggs_transferred',
]

function filaEtapas(rowNumber: number, derived: Record<string, any>, fosa: number | null = 200) {
  return {
    row_number: rowNumber, legacy_lot_code: `INC-${rowNumber}`, status: 'valid', errors: 0, unknown_metrics: 0,
    not_applicable_metrics: 0, derived,
    values: {
      legacy_lot_code: celda(`INC-${rowNumber}`), eggs_received: celda(10000),
      eggs_non_incubable_oversized: celda(200), eggs_non_incubable_dirty: celda(200),
      eggs_non_incubable_broken: celda(100), fertile_eggs_to_pit: celda(fosa),
      eggs_set: celda(8500), eggs_transferred: celda(8000),
    },
  }
}

function previewEtapas(rows: any[]) {
  return { ...PREVIEW_V4, columns: COLUMNAS_V4_ETAPAS, highlight: COLUMNAS_V4_ETAPAS, rows }
}

/** Índices de las cabeceras que casan, en el orden pedido (−1 si alguna falta). */
function posiciones(cabeceras: string[], patrones: RegExp[]): number[] {
  return patrones.map(p => cabeceras.findIndex(c => p.test(c)))
}

describe('SPEC 018 §9 · fosa pre-carga en la UI (OD-HATCH-V4-02 ratificado)', () => {
  it('a) preview en dos etapas: recibidos → no incubables → fosa → cargados → saldo → transferidos → en proceso', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewEtapas([
      filaEtapas(2, { eggs_non_incubable_total: 500, eggs_available_to_set: 800, eggs_in_process: 500 }),
    ]), reconciliacion(120, hatcheryV4()))
    await abrirBatch()

    const preview = screen.getByTestId('cutover-preview')
    const cabeceras = within(preview).getAllByRole('columnheader').map(th => th.textContent ?? '')
    const indices = posiciones(cabeceras, [/Huevos recibidos/, /Total no incubables/, /fosa/, /Huevos cargados/,
                                           /Saldo disponible para cargar/, /Huevos transferidos/, /Huevos en proceso/])
    expect(indices.every(i => i >= 0), JSON.stringify(cabeceras)).toBe(true)
    expect([...indices].sort((a, b) => a - b), JSON.stringify(cabeceras)).toEqual(indices)

    expect(screen.getByTestId('cutover-th-preview-available').textContent).toContain('derivado')
    expect(screen.getByTestId('cutover-preview-available-2').textContent).toMatch(/^\\s*800\\s*$/)
    // Sin doble conteo: en proceso 500 (8.500 − 8.000), nunca 300 (restando otra vez la fosa).
    expect(screen.getByTestId('cutover-preview-in-process-2').textContent).toMatch(/^\\s*500\\s*$/)
    expect(screen.getByTestId('cutover-preview-stages').textContent).toMatch(/Pre-carga/)
    expect(screen.getByTestId('cutover-preview-stages').textContent).toMatch(/Post-carga/)
  })

  it('b) preview con fosa vacía: saldo disponible UNKNOWN (nunca 1.000) y en proceso numérico', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewEtapas([
      filaEtapas(3, { eggs_non_incubable_total: 500, eggs_available_to_set: null, eggs_in_process: 500 }, null),
    ]), reconciliacion(121, hatcheryV4()))
    await abrirBatch()

    const saldo = screen.getByTestId('cutover-preview-available-3')
    expect(saldo.textContent).toContain('UNKNOWN')
    expect(saldo.textContent).not.toMatch(/\\d/)
    expect(screen.getByTestId('cutover-preview-in-process-3').textContent).toMatch(/^\\s*500\\s*$/)
  })

  it('c) reconciliación 9.000/8.000 con fosa 500: en proceso 1.000 (no 500) y disponible 500, en dos etapas', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_non_incubable_oversized: 0, eggs_non_incubable_dirty: 0, eggs_non_incubable_broken: 0,
      eggs_non_incubable_total: 0,
      eggs_transferred: 8000, eggs_transferred_status: 'KNOWN',
      fertile_eggs_to_pit: 500, fertile_eggs_to_pit_status: 'KNOWN',
      eggs_in_process: 1000,   // 9.000 − 8.000, calculado por el servidor (la fosa no resta)
    })
    const lote = reconciliacion(122, hatchery, {
      current: { live: 0, eggs_available_hatchery: 500, eggs_in_process: 1000, chicks_available: 0 },
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, lote)
    const rec = await abrirBatch()

    const cabeceras = within(rec).getAllByRole('columnheader').map(th => th.textContent ?? '')
    const indices = posiciones(cabeceras, [/Huevos recibidos/, /Total no incubables/, /fosa/, /Huevos cargados/,
                                           /Huevo disponible en planta/, /Huevos en proceso/])
    expect(indices.every(i => i >= 0), JSON.stringify(cabeceras)).toBe(true)
    expect([...indices].sort((a, b) => a - b), JSON.stringify(cabeceras)).toEqual(indices)

    expect(within(rec).getByTestId('cutover-eggs-in-process-122').textContent).toMatch(/1[.,]000/)
    expect(within(rec).getByTestId('cutover-eggs-available-122').textContent?.trim()).toBe('500')
    expect(within(rec).getByTestId('cutover-fertile-pit-122').textContent?.trim()).toBe('500')
    // La fosa es una métrica aparte: el total no incubable no la incluye.
    expect(within(rec).getByTestId('cutover-non-incubable-total-122').textContent).not.toContain('500')
    expect(within(rec).queryByTestId('cutover-th-eggs-discarded')).toBeNull()
  })

  it('d) fosa UNKNOWN en la reconciliación: la fosa y el disponible son UNKNOWN; en proceso no depende de ella', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_set: 8500, eggs_transferred: 8000, eggs_transferred_status: 'KNOWN',
      fertile_eggs_to_pit: null, fertile_eggs_to_pit_status: 'UNKNOWN',
      eggs_in_process: 500,
    })
    const lote = reconciliacion(123, hatchery, {
      current: { live: 0, eggs_available_hatchery: null, eggs_in_process: 500, chicks_available: 0 },
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, lote)
    const rec = await abrirBatch()

    const fosa = within(rec).getByTestId('cutover-fertile-pit-123')
    expect(fosa.textContent).toContain('UNKNOWN')
    expect(fosa.textContent).not.toMatch(/\\d/)
    expect(within(rec).getByTestId('cutover-eggs-available-123').textContent).not.toMatch(/\\d/)
    expect(within(rec).getByTestId('cutover-eggs-in-process-123').textContent).toMatch(/^\\s*500\\s*$/)
  })

  it('e) i18n: la fosa se rotula pre-carga en ES y EN (ya no post-carga)', () => {
    expect((es as any).cutover.fertileEggsToPit).toMatch(/pre-carga/)
    expect((es as any).cutover.fields.fertile_eggs_to_pit).toMatch(/pre-carga/)
    expect(JSON.stringify((es as any).cutover)).not.toMatch(/post-carga\\)/)
    expect((en as any).cutover.fertileEggsToPit).toMatch(/pre-load/)
    expect((es as any).cutover.eggsAvailableToSet).toBe('Saldo disponible para cargar')
    expect((en as any).cutover.eggsAvailableToSet).toBeTruthy()
  })
})

''')

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: vitest OD-HATCH-V4-02 aplicado")
