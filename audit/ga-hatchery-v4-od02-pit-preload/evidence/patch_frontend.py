#!/usr/bin/env python3
"""OD-HATCH-V4-02 · frontend + orden del preview (desde la raíz del repo): fosa PRE-CARGA en dos etapas."""
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
    if j < i:
        ERR.append(f"{path}: el marcador final precede al inicial: {fin[:60]!r}")
        return
    p.write_text(s[:i] + nuevo + s[j:], encoding="utf-8")


# ── backend: orden destacado del preview en dos etapas (D-26) ───────────────
S = "backend/app/cutover/service.py"
R(S, """    "hatchery": ("legacy_lot_code", "hatchery_code", "incubator_name", "set_date", "eggs_received", "eggs_set",
                 "eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken",
                 "eggs_transferred", "fertile_eggs_to_pit", "chicks_hatched", "chicks_available", "expected_hatch_date"),""",
  """    # SPEC 018 §9 · D-26: dos etapas. PRE-CARGA = recibidos → no incubables → fosa → cargados (el saldo
    # disponible derivado va tras los cargados); POST-CARGA = transferidos (en proceso derivado detrás).
    "hatchery": ("legacy_lot_code", "hatchery_code", "incubator_name", "set_date", "eggs_received",
                 "eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken",
                 "fertile_eggs_to_pit", "eggs_set", "eggs_transferred", "chicks_hatched", "chicks_available",
                 "expected_hatch_date"),""")

# ── i18n ────────────────────────────────────────────────────────────────────
ES = "frontend/public/locales/es/translation.json"
R(ES, '    "fertileEggsToPit": "Huevos fértiles a fosa (post-carga)",\n',
  '    "fertileEggsToPit": "Huevos fértiles a fosa (pre-carga)",\n'
  '    "eggsAvailableToSet": "Saldo disponible para cargar",\n'
  '    "stagesHint": "Pre-carga: recibidos − no incubables − fosa − cargados = saldo disponible para cargar. Post-carga: cargados − transferidos = huevos en proceso.",\n')
R(ES, '      "fertile_eggs_to_pit": "Huevos fértiles a fosa (post-carga)",', '      "fertile_eggs_to_pit": "Huevos fértiles a fosa (pre-carga)",')
EN = "frontend/public/locales/en/translation.json"
R(EN, '    "fertileEggsToPit": "Fertile eggs sent to pit (post-load)",\n',
  '    "fertileEggsToPit": "Fertile eggs sent to pit (pre-load)",\n'
  '    "eggsAvailableToSet": "Available to set",\n'
  '    "stagesHint": "Pre-load: received − non-incubable − pit − set = available to set. Post-load: set − transferred = eggs in process.",\n')
R(EN, '      "fertile_eggs_to_pit": "Fertile eggs sent to pit (post-load)",', '      "fertile_eggs_to_pit": "Fertile eggs sent to pit (pre-load)",')

# ── página de Cargas Iniciales ──────────────────────────────────────────────
P = "frontend/src/pages/cutover/CargasInicialesPage.tsx"
R(P, "import { useCallback, useEffect, useMemo, useRef, useState } from 'react'",
  "import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'")

R(P, """/** SPEC 018 §8 · D-20: «huevos en proceso» derivado de una fila (lo calcula el backend; `null` = UNKNOWN). */
function enProcesoDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_in_process
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}
""", """/** SPEC 018 §8 · D-20: «huevos en proceso» derivado de una fila (lo calcula el backend; `null` = UNKNOWN). */
function enProcesoDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_in_process
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}

/** SPEC 018 §9 · D-24: saldo disponible para cargar de una fila (lo calcula el backend; `null` = UNKNOWN). */
function disponibleDerivado(fila: CutoverPreviewRow): { value: number | null; status: string } {
  const bruto = fila.derived?.eggs_available_to_set
  return typeof bruto === 'number' ? { value: bruto, status: 'KNOWN' } : { value: null, status: 'UNKNOWN' }
}

/**
 * SPEC 018 §9 · D-26: columnas derivadas del preview de incubadora, cada una tras su columna ancla para
 * leer las dos etapas: PRE-CARGA (recibidos → no incubables → fosa → cargados → saldo disponible) y
 * POST-CARGA (transferidos → en proceso). Si el ancla no está en la vista, la derivada va al final.
 */
interface DerivadaPreview {
  clave: string
  tras: string
  etiqueta: string
  porDefecto: string
  thTestId?: string
  celdaTestId: string
  cardTestId?: string
  valor: (fila: CutoverPreviewRow) => { value: number | null; status: string }
}
const DERIVADAS_PREVIEW: DerivadaPreview[] = [
  { clave: 'total', tras: 'eggs_non_incubable_broken', etiqueta: 'cutover.eggsNonIncubableTotal', porDefecto: 'Total no incubables',
    celdaTestId: 'cutover-preview-total', valor: totalDerivado },
  { clave: 'available', tras: 'eggs_set', etiqueta: 'cutover.eggsAvailableToSet', porDefecto: 'Saldo disponible para cargar',
    thTestId: 'cutover-th-preview-available', celdaTestId: 'cutover-preview-available', cardTestId: 'cutover-preview-available-card',
    valor: disponibleDerivado },
  { clave: 'in-process', tras: 'eggs_transferred', etiqueta: 'cutover.eggsInProcess', porDefecto: 'Huevos en proceso',
    thTestId: 'cutover-th-preview-in-process', celdaTestId: 'cutover-preview-in-process', cardTestId: 'cutover-preview-in-process-card',
    valor: enProcesoDerivado },
]
""")

R(P, """  /** SPEC 018 · D-10: «Huevos descartados (histórico V3)» solo si el batch trae algún descartado KNOWN. */""",
  """  /** SPEC 018 §9 · D-26: derivadas tras su ancla; las de ancla ausente se pintan al final. */
  const derivadasTras = (col: string): DerivadaPreview[] =>
    (muestraTotalDerivadoPreview ? DERIVADAS_PREVIEW.filter(d => d.tras === col) : [])
  const derivadasHuerfanas: DerivadaPreview[] = muestraTotalDerivadoPreview
    ? DERIVADAS_PREVIEW.filter(d => !columnasPreview.includes(d.tras))
    : []
  /** SPEC 018 · D-10: «Huevos descartados (histórico V3)» solo si el batch trae algún descartado KNOWN. */""")

# leyenda de etapas bajo los chips del preview de incubadora
R(P, """                    <span className="rounded-md bg-amber-50 text-amber-800 px-2 py-1">{t('cutover.unknownMetrics')}: <b className="tabular-nums">{resumen?.unknown_metrics ?? 0}</b></span>
                  </div>
""", """                    <span className="rounded-md bg-amber-50 text-amber-800 px-2 py-1">{t('cutover.unknownMetrics')}: <b className="tabular-nums">{resumen?.unknown_metrics ?? 0}</b></span>
                  </div>
                  {muestraTotalDerivadoPreview && (
                    <p className="text-xs text-slate-500" data-testid="cutover-preview-stages">
                      {t('cutover.stagesHint', 'Pre-carga: recibidos − no incubables − fosa − cargados = saldo disponible para cargar. Post-carga: cargados − transferidos = huevos en proceso.')}
                    </p>
                  )}
""")

cabecera_derivada = """<th key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={d.thTestId}>
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase text-slate-400">
                                    ({t('cutover.derivedLabel', 'derivado')})
                                  </span>
                                </th>"""
entre(P, """                          {columnasPreview.map(col => (
                            <th key={col} className="py-1 pr-3 whitespace-nowrap">{t(`cutover.fields.${col}`, col)}</th>""",
      """                          <th className="py-1 pr-3">{t('common.status')}</th>""",
      """                          {columnasPreview.map(col => (
                            <Fragment key={col}>
                              <th className="py-1 pr-3 whitespace-nowrap">{t(`cutover.fields.${col}`, col)}</th>
                              {derivadasTras(col).map(d => (
                                """ + cabecera_derivada + """
                              ))}
                            </Fragment>
                          ))}
                          {derivadasHuerfanas.map(d => (
                                """ + cabecera_derivada + """
                          ))}
""")

celda_derivada = """<td key={d.clave} className="py-1 pr-3 whitespace-nowrap" data-testid={`${d.celdaTestId}-${fila.row_number}`}>
                                  <Metric {...d.valor(fila)} />
                                </td>"""
entre(P, """                            {columnasPreview.map(col => (
                              <td key={col} className="py-1 pr-3 whitespace-nowrap"><Cell cell={fila.values[col]} /></td>""",
      """                            <td className="py-1 pr-3">
                              <Badge variant={fila.status === 'valid' || fila.status === 'applied' ? 'approved' : 'rejected'}>""",
      """                            {columnasPreview.map(col => (
                              <Fragment key={col}>
                                <td className="py-1 pr-3 whitespace-nowrap"><Cell cell={fila.values[col]} /></td>
                                {derivadasTras(col).map(d => (
                                  """ + celda_derivada + """
                                ))}
                              </Fragment>
                            ))}
                            {derivadasHuerfanas.map(d => (
                                  """ + celda_derivada + """
                            ))}
""")

tarjeta_derivada = """<div key={d.clave} className="flex justify-between gap-2"
                                data-testid={d.cardTestId ? `${d.cardTestId}-${fila.row_number}` : undefined}>
                                <span className="text-slate-500">
                                  {t(d.etiqueta, d.porDefecto)}{' '}
                                  <span className="text-[11px] lowercase">({t('cutover.derivedLabel', 'derivado')})</span>
                                </span>
                                <Metric {...d.valor(fila)} />
                              </div>"""
entre(P, """                        {columnasPreview.filter(c => c !== 'legacy_lot_code').map(col => (""",
      """                      </li>
                    ))}
                  </ul>""",
      """                        {columnasPreview.filter(c => c !== 'legacy_lot_code').map(col => (
                          <Fragment key={col}>
                            <div className="flex justify-between gap-2">
                              <span className="text-slate-500">{t(`cutover.fields.${col}`, col)}</span>
                              <Cell cell={fila.values[col]} />
                            </div>
                            {derivadasTras(col).map(d => (
                              """ + tarjeta_derivada + """
                            ))}
                          </Fragment>
                        ))}
                        {derivadasHuerfanas.map(d => (
                              """ + tarjeta_derivada + """
                        ))}
""")

# reconciliación en dos etapas: recibidos, no incubables, fosa, cargados, disponible | en proceso
entre(P, """                            <th className="py-1 pr-3">{t('cutover.eggsReceived')}</th>""",
      """                            {muestraDescartadosHistoricos && (
                              <th""",
      """                            <th className="py-1 pr-3">{t('cutover.eggsReceived')}</th>
                            <th className="py-1 pr-3 whitespace-nowrap" data-testid="cutover-th-non-incubable-total">
                              {t('cutover.eggsNonIncubableTotal', 'Total no incubables')}{' '}
                              <span className="text-[11px] lowercase text-slate-400">
                                ({t('cutover.derivedLabel', 'derivado')})
                              </span>
                            </th>
                            <th className="py-1 pr-3 whitespace-nowrap">{t('cutover.fertileEggsToPit', 'Huevos fértiles a fosa')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsSet')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsAvailable')}</th>
                            <th className="py-1 pr-3">{t('cutover.eggsInProcess')}</th>
""")
entre(P, """                              <td className="py-1 pr-3"><Metric value={lote.opening.hatchery?.eggs_received} status={lote.opening.hatchery?.eggs_received_status} /></td>""",
      """                              {muestraDescartadosHistoricos && (
                                <td className="py-1 pr-3" data-testid={`cutover-eggs-discarded-${lote.lot_id}`}>""",
      """                              <td className="py-1 pr-3"><Metric value={lote.opening.hatchery?.eggs_received} status={lote.opening.hatchery?.eggs_received_status} /></td>
                              <td className="py-1 pr-3" data-testid={`cutover-non-incubable-total-${lote.lot_id}`}>
                                <TotalNoIncubables hatchery={lote.opening.hatchery} />
                              </td>
                              <td className="py-1 pr-3" data-testid={`cutover-fertile-pit-${lote.lot_id}`}>
                                <Metric
                                  value={lote.opening.hatchery?.fertile_eggs_to_pit ?? null}
                                  status={lote.opening.hatchery?.fertile_eggs_to_pit_status}
                                />
                              </td>
                              <td className="py-1 pr-3"><Metric value={lote.opening.hatchery?.eggs_set} status={lote.opening.hatchery?.eggs_set_status} /></td>
                              <td className="py-1 pr-3 font-semibold" data-testid={`cutover-eggs-available-${lote.lot_id}`}>
                                <Metric value={lote.current?.eggs_available_hatchery ?? null} />
                              </td>
                              <td className="py-1 pr-3" data-testid={`cutover-eggs-in-process-${lote.lot_id}`}>
                                <Metric value={lote.current?.eggs_in_process ?? null} />
                              </td>
""")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: frontend OD-HATCH-V4-02 aplicado")
