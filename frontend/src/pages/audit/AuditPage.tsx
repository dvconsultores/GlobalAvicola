import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Shield, User, Database, RotateCcw } from 'lucide-react'
import api from '../../services/api'
import SubNavHeader from '../../components/layout/SubNavHeader'
import { FilterPanel, FilterGroup, Badge, StatusTimeline, EmptyState } from '../../components/ui'
import type { TimelineEvent, TimelineEventType } from '../../components/ui/StatusTimeline'

type AuditTab = 'all' | 'by_lot' | 'by_user' | 'corrections'

const AUDIT_TABS = [
  { key: 'all' as AuditTab, labelKey: 'audit.all', icon: Shield },
  { key: 'by_lot' as AuditTab, labelKey: 'audit.byLot', icon: Database },
  { key: 'by_user' as AuditTab, labelKey: 'audit.byUser', icon: User },
  { key: 'corrections' as AuditTab, labelKey: 'audit.corrections', icon: RotateCcw },
]

// Mapeo de acciones a tipos de timeline
function mapActionToType(action: string): TimelineEventType {
  if (action.includes('create') || action.includes('regist')) return 'create'
  if (action.includes('review') || action.includes('revis')) return 'review'
  if (action.includes('correct') || action.includes('correg')) return 'correction'
  if (action.includes('approv') || action.includes('aprob')) return 'approval'
  if (action.includes('reject') || action.includes('rechaz')) return 'rejection'
  if (action.includes('return') || action.includes('devol')) return 'return'
  if (action.includes('sap_send') || action.includes('enviar')) return 'sap_send'
  if (action.includes('sap_error')) return 'sap_error'
  if (action.includes('consolid')) return 'consolidation'
  return 'view'
}

export default function AuditPage() {
  const { t } = useTranslation()
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<AuditTab>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: '50' })
    if (searchTerm) params.set('search', searchTerm)
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    if (activeTab === 'corrections') params.set('action_contains', 'correct')
    if (activeTab === 'by_user') params.set('group_by', 'user')

    api.get(`/audit?${params}`)
      .then(r => { setLogs(r.data.logs || []); setTotal(r.data.total || 0) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [activeTab, searchTerm, dateFrom, dateTo])

  const clearFilters = () => {
    setSearchTerm('')
    setDateFrom('')
    setDateTo('')
  }

  // Convertir logs a TimelineEvent
  const timelineEvents: TimelineEvent[] = logs.map((log: any) => ({
    id: log.id,
    date: new Date(log.created_at).toLocaleString(),
    action: log.action,
    user: log.user_name || log.user_id || t('common.unknown', 'Desconocido'),
    description: log.entity_type
      ? `${log.entity_type}#${log.entity_id}`
      : undefined,
    detail: log.change_reason || (log.old_value && log.new_value
      ? `${log.old_value} → ${log.new_value}`
      : undefined),
    type: mapActionToType(log.action),
  }))

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <SubNavHeader
          title={t('nav.audit', 'Auditoría')}
          hideBack
          actions={
            <span className="text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-700 px-3 py-1.5 rounded-full font-medium">
              {total} {t('audit.records', 'registros')}
            </span>
          }
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 overflow-x-auto pb-1 scrollbar-hide">
        {AUDIT_TABS.map((tab) => {
          const isActive = activeTab === tab.key
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`
                inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap shrink-0
                ${isActive
                  ? 'bg-[#1E3A5F] text-white shadow-md'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 dark:text-slate-500 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:bg-slate-800'
                }
              `}
            >
              <Icon size={16} />
              {t(tab.labelKey)}
            </button>
          )
        })}
      </div>

      {/* Filter Panel */}
      <FilterPanel onClear={clearFilters} totalResults={total}>
        <FilterGroup label={t('common.search', 'Buscar')}>
          <input
            type="text"
            placeholder={t('audit.searchPlaceholder', 'Buscar en auditoría...')}
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm w-56 focus:border-blue-500 dark:border-blue-400 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </FilterGroup>
        <FilterGroup label={t('common.date', 'Fecha')}>
          <input
            type="date"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:border-blue-500 dark:border-blue-400 focus:ring-1 focus:ring-blue-500 outline-none"
          />
          <span className="text-xs text-slate-400 dark:text-slate-500">—</span>
          <input
            type="date"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className="border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:border-blue-500 dark:border-blue-400 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </FilterGroup>
      </FilterPanel>

      {/* Content */}
      <div className="bg-white dark:bg-slate-800 dark:border-slate-700 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="flex gap-4 animate-pulse">
                <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-100 dark:bg-slate-700 rounded w-1/3" />
                  <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        ) : timelineEvents.length === 0 ? (
          <div className="py-12">
            <EmptyState
              icon={Shield}
              title={t('audit.noRecords', 'Sin registros de auditoría')}
              description={t('audit.noRecordsDesc', 'No se encontraron registros con los filtros actuales')}
            />
          </div>
        ) : (
          <div className="p-5">
            {activeTab === 'corrections' ? (
              /* Vista de correcciones: mostrar cambios lado a lado */
              <div className="space-y-4">
                {timelineEvents.map((event) => (
                  <div key={event.id} className="p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="corrected" size="sm">{t('audit.correction', 'Corrección')}</Badge>
                      <span className="text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500">{event.date}</span>
                    </div>
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{event.action}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500">{event.description}</p>
                    {event.detail && (
                      <div className="mt-2 p-2 bg-white dark:bg-slate-800 rounded-lg border border-amber-100 dark:border-amber-800 text-xs font-mono text-slate-600 dark:text-slate-300 dark:text-slate-500">
                        {event.detail}
                      </div>
                    )}
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">{t('common.by', 'por')} {event.user}</p>
                  </div>
                ))}
              </div>
            ) : (
              /* Timeline view */
              <StatusTimeline events={timelineEvents} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
