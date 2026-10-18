import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Search } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import DataTable, { type RowAction } from '../../components/data-table/DataTable'
import { Button, Modal, Input } from '../../components/ui'
import SearchSelect from '../../components/ui/SearchSelect'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import { getErrorMessage, useToast } from '../../components/Toast'

interface MasterListPageProps {
 entity: string
 titleKey: string
 columns: { key: string; labelKey: string }[]
 searchFields?: string[]
 /**
  * `R-96`. Acciones propias de la entidad. `genetic-lines` las necesita para llegar a sus
  * curvas de peso (`OD-06`), y parametrizar esta pantalla es preferible a duplicarla.
  */
 rowActions?: RowAction<any>[]
}

/**
 * `R-196`. Configuración por entidad: padre obligatorio (selector) y campos
 * numéricos que, vacíos, viajan como `null` — nunca como `''` (422 del int).
 */
const PADRE_DE: Record<string, {
 key: string
 entidad: string
 labelKey: string
 fallback: string
 /** `QA-012`. Rótulo de la columna que muestra el padre en la tabla. */
 colLabelKey: string
 colFallback: string
}> = {
 houses: {
 key: 'farm_id', entidad: 'farms', labelKey: 'masters.selectFarm', fallback: 'Seleccionar granja',
 colLabelKey: 'masters.fields.farm', colFallback: 'Granja',
 },
 incubators: {
 key: 'hatchery_id', entidad: 'hatcheries', labelKey: 'masters.selectPlant', fallback: 'Seleccionar planta',
 colLabelKey: 'masters.fields.hatchery', colFallback: 'Planta de incubación',
 },
 hatchers: {
 key: 'hatchery_id', entidad: 'hatcheries', labelKey: 'masters.selectPlant', fallback: 'Seleccionar planta',
 colLabelKey: 'masters.fields.hatchery', colFallback: 'Planta de incubación',
 },
}

/**
 * `QA-002`. `useToast` lanza si no hay `ToastProvider` — y hay superficies de maestros que
 * se montan sin él (pruebas de autoridad, de error estructurado, de 403). El aviso es un
 * extra de esta pantalla, no un requisito para pintarla: sin provider, el toast es no-op.
 */
type ToastOpcional = { success: (m: string) => void; error: (m: string) => void; warning: (m: string) => void; info: (m: string) => void }
const TOAST_MUDO: ToastOpcional = { success: () => {}, error: () => {}, warning: () => {}, info: () => {} }
function useToastOpcional(): ToastOpcional {
 try {
  return useToast()
 } catch {
  return TOAST_MUDO
 }
}

const NUMERICOS_DE: Record<string, string[]> = {
 houses: ['capacity'],
 incubators: ['capacity'],
 hatchers: ['capacity'],
 'productive-phases': ['order'],
}

export default function MasterListPage({
 entity,
 titleKey,
 columns,
 searchFields: _searchFields,
 rowActions,
}: MasterListPageProps) {
 const { t } = useTranslation()
 const can = useCan()
 const toast = useToastOpcional()
 const padre = PADRE_DE[entity]
 const [items, setItems] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [search, setSearch] = useState('')
 const [page, setPage] = useState(0)
 const [total, setTotal] = useState(0)
 const pageSize = 20

 // Modal state
 const [modalOpen, setModalOpen] = useState(false)
 const [editItem, setEditItem] = useState<any | null>(null)
 const [formValues, setFormValues] = useState<Record<string, string>>({})
 const [saving, setSaving] = useState(false)
 const [formError, setFormError] = useState('')
 const [deleteTarget, setDeleteTarget] = useState<any | null>(null)
 const [deleting, setDeleting] = useState(false)
 const [padreOpciones, setPadreOpciones] = useState<any[]>([])
 /** `QA-012`. Mapa id→nombre del padre para la columna de la tabla. */
 const [padreNombres, setPadreNombres] = useState<Record<string, string>>({})
 const [activarConfirm, setActivarConfirm] = useState(false)
 /** `QA-002`. Reactivación disparada desde la fila (no desde el modal). */
 const [reactivarTarget, setReactivarTarget] = useState<any | null>(null)
 // `R-212` · AC-04.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

 const fetchItems = useCallback(async () => {
 setLoading(true)
 try {
 const response = await api.get(`/masters/${entity}`, {
 params: { skip: page * pageSize, limit: pageSize, search },
 })
 setItems(response.data)
 // `GA-REM-033 AC03` / `R-89`. Antes se usaba `response.data.length`, que es el tamaño de
 // la página: con 45 registros y páginas de 20 el panel decía «20 resultados». No era un
 // fallo de aquí — el backend calculaba el total y lo descartaba —, y ahora lo expone en
 // `X-Total-Count`. Se conserva la longitud como reserva por si la cabecera no viaja.
 const totalHeader = response.headers['x-total-count']
 setTotal(totalHeader !== undefined ? Number(totalHeader) : response.data.length)
 setEstado('ok')
 } catch (err) {
 console.error(`Error fetching ${entity}:`, err)
 setEstado((err as any)?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setLoading(false)
 }
 }, [entity, page, search])

 useEffect(() => { fetchItems() }, [fetchItems])

 // `R-196`. Opciones del padre (granja/planta) para el selector del formulario.
 // `QA-012`. La lista completa alimenta el mapa id→nombre de la columna (una fila puede
 // apuntar a un padre ya inactivo y aun así debe mostrar su nombre); el selector del modal
 // sigue ofreciendo solo los activos.
 useEffect(() => {
 const p = PADRE_DE[entity]
 if (!p) { setPadreOpciones([]); setPadreNombres({}); return }
 let vivo = true
 api.get(`/masters/${p.entidad}`, { params: { limit: 100 } })
 .then((res) => {
  if (!vivo) return
  const todos: any[] = res.data ?? []
  setPadreNombres(Object.fromEntries(todos.map((x: any) => [String(x.id), x.name])))
  setPadreOpciones(todos.filter((x: any) => x.is_active !== false))
 })
 .catch(() => { if (vivo) { setPadreOpciones([]); setPadreNombres({}) } })
 return () => { vivo = false }
 }, [entity])

 // ── Open create modal ──
 const openCreate = () => {
 setEditItem(null)
 setFormValues({})
 setFormError('')
 setModalOpen(true)
 }

 // ── Open edit modal ──
 const openEdit = (item: any) => {
 setEditItem(item)
 const vals: Record<string, string> = {}
 columns.forEach(c => { vals[c.key] = item[c.key] ?? '' })
 if (padre) vals[padre.key] = item[padre.key] ?? ''
 setFormValues(vals)
 setFormError('')
 setModalOpen(true)
 }

 // `R-196`. Numéricos vacíos ⇒ `null`; el padre viaja como número.
 const construirPayload = () => {
 const payload: Record<string, any> = { ...formValues }
 if (padre) payload[padre.key] = formValues[padre.key] ? Number(formValues[padre.key]) : null
 for (const k of NUMERICOS_DE[entity] ?? []) {
 const v = formValues[k]
 payload[k] = v === '' || v === undefined || v === null ? null : Number(v)
 }
 return payload
 }

 // ── Reactivar (`R-196`, `QA-002`) ──
 // Sirve al botón del modal y a la acción de la fila: recibe el registro a reactivar.
 const reactivar = async (objetivo?: any) => {
 const item = objetivo ?? editItem
 if (!item) return
 setSaving(true)
 setFormError('')
 try {
 await api.put(`/masters/${entity}/${item.id}`, { is_active: true })
 setActivarConfirm(false)
 setReactivarTarget(null)
 setModalOpen(false)
 fetchItems()
 } catch (err: any) {
 const mensaje = getErrorMessage(err, t('errors.saveFailed', 'Error al guardar'))
 setFormError(mensaje)
 toast.error(mensaje)
 } finally {
 setSaving(false)
 }
 }

 // ── Save (create or update) ──
 const handleSave = async () => {
 setSaving(true)
 setFormError('')
 try {
 if (editItem) {
 await api.put(`/masters/${entity}/${editItem.id}`, construirPayload())
 } else {
 await api.post(`/masters/${entity}`, construirPayload())
 }
 setModalOpen(false)
 fetchItems()
 } catch (err: any) {
 // `R-215`. `detail` puede ser lista (422): pintarla cruda lanzaba React #31.
 setFormError(getErrorMessage(err, t('errors.saveFailed', 'Error al guardar')))
 } finally {
 setSaving(false)
 }
 }

 // ── Desactivar (el DELETE del backend es baja lógica: `is_active=false`) ──
 // `QA-002`. Un fallo debe avisarse: antes solo iba a la consola y el usuario no sabía nada.
 const handleDelete = async () => {
 if (!deleteTarget) return
 setDeleting(true)
 try {
 await api.delete(`/masters/${entity}/${deleteTarget.id}`)
 setDeleteTarget(null)
 fetchItems()
 } catch (err: any) {
 console.error('Error deleting:', err)
 toast.error(getErrorMessage(err, t('errors.saveFailed', 'Error al guardar')))
 } finally {
 setDeleting(false)
 }
 }

 /** `QA-012`. Nombre del padre; nunca el id crudo. */
 const nombrePadre = (item: any): string => {
 if (!padre) return '—'
 const id = item?.[padre.key]
 if (id === null || id === undefined || id === '') return '—'
 return padreNombres[String(id)] ?? '—'
 }

 const tableColumns = [
 ...columns.map(col => ({
 key: col.key,
 label: t(col.labelKey),
 })),
 ...(padre ? [{
 key: padre.key,
 label: t(padre.colLabelKey, padre.colFallback),
 render: (item: any) => nombrePadre(item),
 }] : []),
 // `QA-002`. Estado explícito: la baja es lógica, así que «desaparecer» no es una opción.
 {
 key: 'is_active',
 label: t('masters.fields.status', 'Estado'),
 render: (item: any) => (item.is_active === false
 ? t('common.inactive', 'Inactivo')
 : t('common.active', 'Activo')),
 },
 ]

 // `QA-002`. Desactivar y reactivar son la misma acción sobre estados opuestos: cada una
 // se ofrece solo en la fila donde tiene sentido.
 const accionesEstado: RowAction<any>[] = []
 if (can({ permission: 'masters:delete' })) {
 accionesEstado.push({
 label: t('common.deactivate', 'Desactivar'),
 onClick: (item: any) => setDeleteTarget(item),
 visible: (item: any) => item.is_active !== false,
 })
 }
 if (can({ permission: 'masters:update' })) {
 accionesEstado.push({
 label: t('common.reactivate', 'Reactivar'),
 onClick: (item: any) => setReactivarTarget(item),
 visible: (item: any) => item.is_active === false,
 })
 }
 const todasLasAcciones = [...(rowActions ?? []), ...accionesEstado]

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={fetchItems} />
 </div>
 )
 }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
 <div>
 <h1 className="text-2xl font-bold text-slate-800">{t(titleKey)}</h1>
 <p className="text-sm text-slate-500 mt-1">{total} {t('common.results')}</p>
 {!can({ permission: 'masters:create' }) && !can({ permission: 'masters:update' }) && !can({ permission: 'masters:delete' }) && (
 <p className="text-xs text-slate-400 mt-1">{t('actions.readOnlyViewer')}</p>
 )}
 </div>
 <div className="flex gap-3">
 <div className="relative">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
 <input
 type="text"
 placeholder={`${t('common.search')}...`}
 value={search}
 onChange={e => { setSearch(e.target.value); setPage(0) }}
 className="h-10 pl-9 pr-3 border border-slate-300 rounded-lg text-sm focus:border-[#5a9bba] focus:ring-2 focus:ring-blue-200 outline-none"
 />
 </div>
 {can({ permission: 'masters:create' }) && <Button leftIcon={<Plus size={15} />} onClick={openCreate}>
 {t('common.new', 'Nuevo')}
 </Button>}
 </div>
 </div>

 <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
 <DataTable
 columns={tableColumns}
 data={items}
 loading={loading}
 onEdit={can({ permission: 'masters:update' }) ? openEdit : undefined}
 rowActions={todasLasAcciones}
 rowClassName={(item: any) => (item.is_active === false ? 'opacity-60' : undefined)}
 />
 </div>

 {/* Pagination */}
 {total >= pageSize && (
 <div className="flex items-center justify-between mt-4 text-sm">
 <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
 ← {t('common.back')}
 </Button>
 <span className="text-slate-500">{t('common.page')} {page + 1}</span>
 <Button variant="outline" size="sm" disabled={items.length < pageSize} onClick={() => setPage(page + 1)}>
 {t('common.next')} →
 </Button>
 </div>
 )}

 {/* ── Create / Edit Modal ── */}
 <Modal
 open={modalOpen}
 onClose={() => setModalOpen(false)}
 title={editItem ? `${t('common.edit', 'Editar')} ${t(titleKey)}` : `${t('common.new', 'Nuevo')} ${t(titleKey)}`}
 footer={
 <>
 <Button variant="secondary" onClick={() => setModalOpen(false)}>
 {t('common.cancel', 'Cancelar')}
 </Button>
 {editItem && editItem.is_active === false && !activarConfirm && (
 <Button variant="secondary" onClick={() => setActivarConfirm(true)}>
 {t('masters.activate', 'Activar')}
 </Button>
 )}
 <Button onClick={handleSave} loading={saving}>
 {t('common.save', 'Guardar')}
 </Button>
 </>
 }
 >
 <div className="space-y-4">
 {padre && (
 <div>
 <p className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1.5">
 {t(padre.labelKey, padre.fallback)}
 </p>
 <SearchSelect
 value={formValues[padre.key] ?? ''}
 onChange={(v: string) => setFormValues(prev => ({ ...prev, [padre.key]: v }))}
 items={padreOpciones}
 placeholder={t(padre.labelKey, padre.fallback)}
 />
 </div>
 )}
 {columns.map(col => (
 <Input
 key={col.key}
 label={t(col.labelKey)}
 type={(NUMERICOS_DE[entity] ?? []).includes(col.key) ? 'number' : undefined}
 value={formValues[col.key] ?? ''}
 onChange={e => setFormValues(prev => ({ ...prev, [col.key]: e.target.value }))}
 />
 ))}
 {formError && (
 <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
 {formError}
 </p>
 )}
 </div>
 </Modal>

 {/* `R-196`. Reactivación con confirmación explícita (PUT is_active:true). */}
 <ConfirmDialog
 open={activarConfirm}
 onClose={() => setActivarConfirm(false)}
 onConfirm={() => reactivar()}
 title={t('masters.activate', 'Activar')}
 message={t('masters.activateConfirm', '¿Confirmás reactivar este registro?')}
 confirmLabel={t('masters.activate', 'Activar')}
 loading={saving}
 />

 {/* `QA-002`. Reactivar desde la fila: mismo PUT, misma confirmación. */}
 <ConfirmDialog
 open={!!reactivarTarget}
 onClose={() => setReactivarTarget(null)}
 onConfirm={() => reactivar(reactivarTarget)}
 title={t('common.reactivate', 'Reactivar')}
 message={t('masters.activateConfirm', '¿Confirmás reactivar este registro?')}
 confirmLabel={t('common.reactivate', 'Reactivar')}
 loading={saving}
 />

 {/* `QA-002`. Baja lógica: se confirma como desactivación, no como borrado. */}
 <ConfirmDialog
 open={!!deleteTarget}
 onClose={() => setDeleteTarget(null)}
 onConfirm={handleDelete}
 title={t('common.confirmDeactivate', '¿Desactivar registro?')}
 message={`${t('common.deactivateWarning', 'Dejará de poder seleccionarse; podrá reactivarlo después.')}${deleteTarget?.name ? ` "${deleteTarget.name}"` : ''}`}
 confirmLabel={t('common.deactivate', 'Desactivar')}
 variant="danger"
 loading={deleting}
 showWarning
 />
 </div>
 )
}
