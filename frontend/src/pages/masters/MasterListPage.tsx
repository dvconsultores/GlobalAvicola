import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Search, Trash2 } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import DataTable, { type RowAction } from '../../components/data-table/DataTable'
import { Button, Modal, Input } from '../../components/ui'
import SearchSelect from '../../components/ui/SearchSelect'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import { getErrorMessage } from '../../components/Toast'

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
const PADRE_DE: Record<string, { key: string; entidad: string; labelKey: string; fallback: string }> = {
 houses: { key: 'farm_id', entidad: 'farms', labelKey: 'masters.selectFarm', fallback: 'Seleccionar granja' },
 incubators: { key: 'hatchery_id', entidad: 'hatcheries', labelKey: 'masters.selectPlant', fallback: 'Seleccionar planta' },
 hatchers: { key: 'hatchery_id', entidad: 'hatcheries', labelKey: 'masters.selectPlant', fallback: 'Seleccionar planta' },
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
 const [activarConfirm, setActivarConfirm] = useState(false)
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
 useEffect(() => {
 const p = PADRE_DE[entity]
 if (!p) { setPadreOpciones([]); return }
 let vivo = true
 api.get(`/masters/${p.entidad}`, { params: { limit: 100 } })
 .then((res) => { if (vivo) setPadreOpciones((res.data ?? []).filter((x: any) => x.is_active !== false)) })
 .catch(() => { if (vivo) setPadreOpciones([]) })
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

 // ── Reactivar (`R-196`) ──
 const reactivar = async () => {
 if (!editItem) return
 setSaving(true)
 setFormError('')
 try {
 await api.put(`/masters/${entity}/${editItem.id}`, { is_active: true })
 setActivarConfirm(false)
 setModalOpen(false)
 fetchItems()
 } catch (err: any) {
 setFormError(getErrorMessage(err, t('errors.saveFailed', 'Error al guardar')))
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

 // ── Delete ──
 const handleDelete = async () => {
 if (!deleteTarget) return
 setDeleting(true)
 try {
 await api.delete(`/masters/${entity}/${deleteTarget.id}`)
 setDeleteTarget(null)
 fetchItems()
 } catch (err: any) {
 console.error('Error deleting:', err)
 } finally {
 setDeleting(false)
 }
 }

 const tableColumns = columns.map(col => ({
 key: col.key,
 label: t(col.labelKey),
 }))

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
 onDelete={can({ permission: 'masters:delete' }) ? (item: any) => setDeleteTarget(item) : undefined}
 rowActions={rowActions}
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
 onConfirm={reactivar}
 title={t('masters.activate', 'Activar')}
 message={t('masters.activateConfirm', '¿Confirmás reactivar este registro?')}
 confirmLabel={t('masters.activate', 'Activar')}
 loading={saving}
 />

 {/* ── Delete Confirmation Modal ── */}
 <Modal
 open={!!deleteTarget}
 onClose={() => setDeleteTarget(null)}
 title={t('common.confirmDelete', '¿Eliminar registro?')}
 size="sm"
 footer={
 <>
 <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
 {t('common.cancel', 'Cancelar')}
 </Button>
 <Button variant="danger" onClick={handleDelete} loading={deleting} leftIcon={<Trash2 size={14} />}>
 {t('common.delete', 'Eliminar')}
 </Button>
 </>
 }
 >
 <p className="text-sm text-slate-600">
 {t('common.deleteWarning', 'Esta acción no se puede deshacer.')}{' '}
 {deleteTarget?.name && <strong>"{deleteTarget.name}"</strong>}
 </p>
 </Modal>
 </div>
 )
}
