import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../services/api'
import DataTable from '../../components/data-table/DataTable'

interface MasterListPageProps {
  entity: string           // e.g. "farms", "companies", "suppliers"
  titleKey: string         // i18n key, e.g. "masters.farms"
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

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  const handleDelete = async (item: any) => {
    if (!confirm(t('common.confirm'))) return
    try {
      await api.delete(`/masters/${entity}/${item.id}`)
      fetchItems()
    } catch (err) {
      console.error('Error deleting:', err)
    }
  }

  const tableColumns = columns.map((col) => ({
    key: col.key,
    label: t(col.labelKey),
  }))

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t(titleKey)}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {total} {t('common.noResults') === 'No results' ? 'results' : 'resultados'}
          </p>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder={t('common.search') + '...'}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0) }}
            className="h-10 px-3 border border-slate-300 rounded-lg text-sm focus:border-[#2563EB] focus:ring-2 focus:ring-blue-200 outline-none"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <DataTable
          columns={tableColumns}
          data={items}
          loading={loading}
          onDelete={handleDelete}
        />
      </div>

      {/* Pagination */}
      {total >= pageSize && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <button
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg disabled:opacity-40 hover:bg-slate-50 transition"
          >
            ← {t('common.back')}
          </button>
          <span className="text-slate-500">
            {t('common.noResults') === 'No results' ? 'Page' : 'Página'} {page + 1}
          </span>
          <button
            disabled={items.length < pageSize}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg disabled:opacity-40 hover:bg-slate-50 transition"
          >
            {t('common.noResults') === 'No results' ? 'Next' : 'Siguiente'} →
          </button>
        </div>
      )}
    </div>
  )
}
