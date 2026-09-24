/**
 * Curvas estándar de peso de una línea genética — `R-96` · `OD-06` · `GA-REM-037` enmienda A.
 *
 * El backend sabía cargar una curva desde el 2026-09-06; el administrador no. `OD-06` dice
 * que cada línea genética puede tener su tabla y que **esa tabla debe poder cargarse dentro
 * de Global Avícola**, y un `201` de la API no demuestra eso.
 *
 * No es un módulo nuevo: cuelga del maestro `GeneticLine` que ya existe (`GA-REM-033`) y
 * reutiliza sus primitivas. Un segundo sistema de administración habría sido el error.
 */
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LineChart, Upload } from 'lucide-react'
import BackNavigation from '../../components/layout/BackNavigation'

import { Button, Modal, Input, EmptyState } from '../../components/ui'
import {
  activateWeightCurve, getGeneticLine, listWeightCurves, parsearTabla, uploadWeightCurve,
  type CurveRowError, type GeneticLine, type WeightCurve, type WeightCurvePoint,
} from '../../services/weightCurves'
import { useCan } from '../../auth/actionAuthority'

/** Extrae el informe de rechazo del backend, que no es el 422 de Pydantic. */
function erroresDeFila(err: any): CurveRowError[] {
  const detalle = err?.response?.data?.detail
  return Array.isArray(detalle?.errores) ? detalle.errores : []
}

function mensajeGeneral(err: any, porDefecto: string): string {
  const detalle = err?.response?.data?.detail
  if (typeof detalle === 'string') return detalle
  if (typeof detalle?.mensaje === 'string') return detalle.mensaje
  return porDefecto
}

export default function WeightCurvesPage() {
 const can = useCan()
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const geneticLineId = Number(id)

  const [linea, setLinea] = useState<GeneticLine | null>(null)
  const [curvas, setCurvas] = useState<WeightCurve[]>([])
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')

  const [dialogo, setDialogo] = useState(false)
  const [etiqueta, setEtiqueta] = useState('')
  const [origen, setOrigen] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [puntos, setPuntos] = useState<WeightCurvePoint[]>([])
  const [subiendo, setSubiendo] = useState(false)
  const [errorDialogo, setErrorDialogo] = useState('')
  const [filasMal, setFilasMal] = useState<CurveRowError[]>([])
  const [activando, setActivando] = useState<number | null>(null)
  const [detalle, setDetalle] = useState<WeightCurve | null>(null)

  const refrescar = useCallback(async () => {
    setCargando(true)
    setErrorCarga('')
    try {
      const [l, c] = await Promise.all([
        getGeneticLine(geneticLineId),
        listWeightCurves(geneticLineId),
      ])
      setLinea(l)
      setCurvas(c)
    } catch (err: any) {
      setErrorCarga(mensajeGeneral(err, t('curves.loadFailed')))
    } finally {
      setCargando(false)
    }
  }, [geneticLineId, t])

  useEffect(() => { void refrescar() }, [refrescar])

  const abrirDialogo = () => {
    setEtiqueta('')
    setOrigen('')
    setArchivo(null)
    setPuntos([])
    setErrorDialogo('')
    setFilasMal([])
    setDialogo(true)
  }

  const elegirArchivo = async (f: File | null) => {
    setArchivo(f)
    setFilasMal([])
    setErrorDialogo('')
    if (!f) { setPuntos([]); return }
    try {
      setPuntos(parsearTabla(await f.text()))
    } catch {
      setPuntos([])
      setErrorDialogo(t('curves.fileUnreadable'))
    }
  }

  const subir = async () => {
    // Validación de experiencia, no de negocio: que falte el archivo o la etiqueta se ve
    // aquí; que la tabla sea coherente lo juzga el backend y solo el backend.
    if (!etiqueta.trim()) { setErrorDialogo(t('curves.versionRequired')); return }
    if (!puntos.length) { setErrorDialogo(t('curves.fileRequired')); return }

    setSubiendo(true)
    setErrorDialogo('')
    setFilasMal([])
    try {
      await uploadWeightCurve({
        genetic_line_id: geneticLineId,
        version_label: etiqueta.trim(),
        source: origen.trim() || undefined,
        points: puntos,
      })
      setDialogo(false)
      await refrescar()
    } catch (err: any) {
      const filas = erroresDeFila(err)
      setFilasMal(filas)
      if (!filas.length) setErrorDialogo(mensajeGeneral(err, t('curves.uploadFailed')))
    } finally {
      setSubiendo(false)
    }
  }

  const activar = async (curva: WeightCurve) => {
    setActivando(curva.id)
    try {
      await activateWeightCurve(curva.id)
      await refrescar()
    } catch (err: any) {
      setErrorCarga(mensajeGeneral(err, t('curves.activateFailed')))
    } finally {
      setActivando(null)
    }
  }

  const rango = (c: WeightCurve) => {
    if (!c.points.length) return '—'
    const edades = c.points.map(p => p.age_days)
    return `${Math.min(...edades)}–${Math.max(...edades)}`
  }

  return (
    <div className="py-4 sm:py-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <BackNavigation to="/masters/genetic-lines" className="mb-1" />
          <h1 className="text-2xl font-bold text-slate-800">{t('curves.title')}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {t('masters.geneticLines')}: <strong>{linea?.name ?? '—'}</strong>
          </p>
        </div>
        {can({ permission: 'masters:create' }) && <Button leftIcon={<Upload size={15} />} onClick={abrirDialogo}>
          {t('curves.upload')}
        </Button>}
      </div>

      {errorCarga && (
        <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
          {errorCarga}
        </p>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {cargando ? (
          <p className="text-slate-500 text-sm py-8 text-center">{t('common.loading')}</p>
        ) : curvas.length === 0 ? (
          <EmptyState
            icon={LineChart}
            title={t('curves.emptyTitle', { line: linea?.name ?? '' })}
            description={t('curves.emptyDescription')}
            action={can({ permission: 'masters:create' }) ? { label: t('curves.uploadFirst'), onClick: abrirDialogo } : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 font-semibold text-slate-700">{t('curves.version')}</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-700">{t('common.status')}</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-700">{t('curves.points')}</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-700">{t('curves.ageRange')}</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-700">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {curvas.map(c => (
                  <tr key={c.id} className="border-b border-slate-100">
                    <td className="px-4 py-3 font-mono text-slate-700">{c.version_label}</td>
                    <td className="px-4 py-3">
                      {/*
                        Por texto y no solo por color: quien no distingue verde de gris
                        también administra curvas (`AC-FE07`).
                      */}
                      <span className={c.is_active
                        ? 'inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5'
                        : 'inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-100 border border-slate-200 rounded-full px-2 py-0.5'}>
                        {c.is_active ? t('curves.active') : t('curves.inactive')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{c.points.length}</td>
                    <td className="px-4 py-3 text-slate-600">{rango(c)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setDetalle(c)}
                          className="text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded transition"
                        >
                          {t('common.view')}
                        </button>
                        {!c.is_active && can({ permission: 'masters:update' }) && (
                          <button
                            onClick={() => activar(c)}
                            disabled={activando === c.id}
                            className="text-xs px-2 py-1 text-slate-700 border border-slate-300 hover:bg-slate-50 rounded transition disabled:opacity-50"
                          >
                            {t('curves.activate')}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Subir nueva curva ── */}
      <Modal
        open={dialogo}
        onClose={() => setDialogo(false)}
        title={t('curves.upload')}
        description={t('curves.uploadHelp')}
        footer={
          <>
            <Button variant="secondary" onClick={() => setDialogo(false)} disabled={subiendo}>
              {t('common.cancel')}
            </Button>
            {/* `disabled` durante la subida: sin esto un doble clic manda dos POST. */}
            <Button onClick={subir} loading={subiendo} disabled={subiendo}>
              {t('common.save')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('curves.version')}
            value={etiqueta}
            onChange={e => setEtiqueta(e.target.value)}
            placeholder="2026-01"
            required
          />
          <Input
            label={t('curves.source')}
            value={origen}
            onChange={e => setOrigen(e.target.value)}
            placeholder={t('curves.sourcePlaceholder')}
          />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="curva-archivo" className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
              {t('curves.file')}
            </label>
            <input
              id="curva-archivo"
              type="file"
              accept=".csv,text/csv,text/plain"
              onChange={e => elegirArchivo(e.target.files?.[0] ?? null)}
              className="text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-slate-300 file:text-sm file:bg-white hover:file:bg-slate-50"
            />
            <p className="text-xs text-slate-500">{t('curves.fileFormat')}</p>
          </div>

          {archivo && (
            <p className="text-sm text-slate-600">
              {t('curves.parsedRows', { count: puntos.length, file: archivo.name })}
            </p>
          )}

          {filasMal.length > 0 && (
            <div role="alert" className="text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <p className="font-semibold text-red-700 mb-1">{t('curves.rejected')}</p>
              <ul className="space-y-1 text-red-700">
                {filasMal.map((f, i) => (
                  <li key={i}>
                    {t('curves.rowError', { row: f.fila, field: f.campo })}: {f.motivo}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {errorDialogo && (
            <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {errorDialogo}
            </p>
          )}
        </div>
      </Modal>

      {/* ── Detalle de una versión ── */}
      <Modal
        open={!!detalle}
        onClose={() => setDetalle(null)}
        title={`${t('curves.title')} · ${detalle?.version_label ?? ''}`}
        size="lg"
      >
        {detalle && (
          <div className="space-y-3">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div><dt className="text-slate-500">{t('common.status')}</dt>
                <dd>{detalle.is_active ? t('curves.active') : t('curves.inactive')}</dd></div>
              <div><dt className="text-slate-500">{t('curves.points')}</dt>
                <dd>{detalle.points.length}</dd></div>
              <div><dt className="text-slate-500">{t('curves.ageRange')}</dt>
                <dd>{rango(detalle)}</dd></div>
              <div><dt className="text-slate-500">{t('curves.source')}</dt>
                <dd>{detalle.source || '—'}</dd></div>
            </dl>
            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-slate-50">
                  <tr className="border-b border-slate-200">
                    <th className="text-left px-3 py-2">{t('curves.ageDays')}</th>
                    <th className="text-left px-3 py-2">{t('curves.target')}</th>
                    <th className="text-left px-3 py-2">{t('curves.min')}</th>
                    <th className="text-left px-3 py-2">{t('curves.max')}</th>
                  </tr>
                </thead>
                <tbody>
                  {detalle.points.map(p => (
                    <tr key={p.id ?? p.age_days} className="border-b border-slate-100">
                      <td className="px-3 py-1.5">{p.age_days}</td>
                      <td className="px-3 py-1.5">{p.target_weight ?? '—'}</td>
                      <td className="px-3 py-1.5">{p.min_weight}</td>
                      <td className="px-3 py-1.5">{p.max_weight}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
