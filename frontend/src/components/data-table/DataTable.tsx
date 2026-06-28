import { useTranslation } from 'react-i18next'

interface Column<T> {
 key: string
 label: string
 render?: (item: T) => React.ReactNode
}

interface DataTableProps<T> {
 columns: Column<T>[]
 data: T[]
 loading?: boolean
 onEdit?: (item: T) => void
 onDelete?: (item: T) => void
}

export default function DataTable<T extends { id: number }>({
 columns,
 data,
 loading,
 onEdit,
 onDelete,
}: DataTableProps<T>) {
 const { t } = useTranslation()

 if (loading) {
 return <p className="text-slate-500 dark:text-slate-400 text-sm py-8 text-center">{t('common.loading')}</p>
 }

 if (!data.length) {
 return <p className="text-slate-400 dark:text-slate-500 text-sm py-8 text-center">{t('common.noResults')}</p>
 }

 return (
 <div className="overflow-x-auto">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200">
 {columns.map((col) => (
 <th
 key={col.key}
 className="text-left px-4 py-3 font-semibold text-slate-700 dark:text-slate-200 whitespace-nowrap"
 >
 {col.label}
 </th>
 ))}
 {(onEdit || onDelete) && (
 <th className="text-right px-4 py-3 font-semibold text-slate-700 dark:text-slate-200">
 {t('common.actions')}
 </th>
 )}
 </tr>
 </thead>
 <tbody>
 {data.map((item) => (
 <tr
 key={item.id}
 className="border-b border-slate-100 hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors"
 >
 {columns.map((col) => (
 <td key={col.key} className="px-4 py-3 text-slate-600 dark:text-slate-300 whitespace-nowrap">
 {col.render ? col.render(item) : String((item as any)[col.key] ?? '')}
 </td>
 ))}
 {(onEdit || onDelete) && (
 <td className="px-4 py-3 text-right">
 <div className="flex justify-end gap-2">
 {onEdit && (
 <button
 onClick={() => onEdit(item)}
 className="text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded transition"
 >
 {t('common.edit')}
 </button>
 )}
 {onDelete && (
 <button
 onClick={() => onDelete(item)}
 className="text-xs px-2 py-1 text-red-600 dark:text-red-400 hover:bg-red-50 rounded transition"
 >
 {t('common.delete')}
 </button>
 )}
 </div>
 </td>
 )}
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 )
}
