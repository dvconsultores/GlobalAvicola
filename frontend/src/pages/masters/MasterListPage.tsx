import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Search, Trash2 } from 'lucide-react'
import api from '../../services/api'
import DataTable from '../../components/data-table/DataTable'
import { Button, Modal, Input } from '../../components/ui'

interface MasterListPageProps {
  entity: string
  titleKey: string
  columns: { key: string; labelKey: string }[]
  searchFields?: string[]
}

export default function MasterListPage({
  entity,
  titleKey,
  columns,
  searchFields: _searchFields,
}: MasterListPageProps) {
  const { t } = useTranslation()
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  // Modal state
  const [modalOpen, setModalOpen]   = useState(false)
  const [editItem, setEditItem]     = useState<any | null>(null)
  const [formValues, setFormValues] = useState<Record<string, string>>({})
  const [saving, setSaving]         = useState(false)
  const [formError, setFormError]   = useState('')
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null)
  const [deleting, setDeleting]     = useState(false)

  const fetchItems = useCallback(async () => {
    setLoading(true)
    try {
      const response = await api.get(`/masters/${entity}`, {
        params: { skip: page * pageSize, limit: pageSize, search },
      })
      setItems(response.data)
      setTotal(response.data.length)
    } catch (err) {
      console.error(`Error fetching ${entity}:`, err)
    } finally {
      setLoading(false)
    }
  }, [entity, page, search])

  useEffect(() => { fetchItems() }, [fetchItems])

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
    setFormValues(vals)
    setFormError('')
    setModalOpen(true)
  }

  // ── Save (create or update) ──
  const handleSave = async () => {
    setSaving(true)
    setFormError('')
    try {
      if (editItem) {
        await api.put(`/masters/${entity}/${editItem.id}`, formValues)
      } else {
        await api.post(`/masters/${entity}`, formValues)
      }
      setModalOpen(false)
      fetchItems()
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? t('errors.saveFailed', 'Error al guardar'))
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

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-200">{t(titleKey)}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 dark:text-slate-500 mt-1">{total} {t('common.results')}</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
            <input
              type="text"
              placeholder={`${t('common.search')}...`}
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0) }}
              className="h-10 pl-9 pr-3 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:border-[#2563EB] focus:ring-2 focus:ring-blue-200 outline-none"
            />
          </div>
          <Button leftIcon={<Plus size={15} />} onClick={openCreate}>
            {t('common.new', 'Nuevo')}
          </Button>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 dark:border-slate-700 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 dark:shadow-none overflow-hidden">
        <DataTable
          columns={tableColumns}
          data={items}
          loading={loading}
          onEdit={openEdit}
          onDelete={(item: any) => setDeleteTarget(item)}
        />
      </div>

      {/* Pagination */}
      {total >= pageSize && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
            ← {t('common.back')}
          </Button>
          <span className="text-slate-500 dark:text-slate-400 dark:text-slate-500">{t('common.page')} {page + 1}</span>
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
            <Button onClick={handleSave} loading={saving}>
              {t('common.save', 'Guardar')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {columns.map(col => (
            <Input
              key={col.key}
              label={t(col.labelKey)}
              value={formValues[col.key] ?? ''}
              onChange={e => setFormValues(prev => ({ ...prev, [col.key]: e.target.value }))}
            />
          ))}
          {formError && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
              {formError}
            </p>
          )}
        </div>
      </Modal>

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
        <p className="text-sm text-slate-600 dark:text-slate-300 dark:text-slate-500">
          {t('common.deleteWarning', 'Esta acción no se puede deshacer.')}{' '}
          {deleteTarget?.name && <strong>"{deleteTarget.name}"</strong>}
        </p>
      </Modal>
    </div>
  )
}
