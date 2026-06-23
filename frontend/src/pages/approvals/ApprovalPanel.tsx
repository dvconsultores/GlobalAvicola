import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Check, CheckCircle, X, ArrowLeft } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_COLORS: Record<string, string> = {
  corrected: 'bg-teal-100 text-teal-800', in_review: 'bg-indigo-100 text-indigo-800',
  approved: 'bg-emerald-100 text-emerald-800', rejected: 'bg-red-100 text-red-800',
}

export default function ApprovalPanel() {
  const { t } = useTranslation()
  const toast = useToast()
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [lotId, setLotId] = useState('')
  const [page, setPage] = useState(0)
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectTarget, setRejectTarget] = useState<'single' | 'batch'>('single')
  const [singleRejectId, setSingleRejectId] = useState<number | null>(null)
  const limit = 20

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) })
      if (lotId) params.set('lot_id', lotId)
      const { data } = await api.get(`/approvals/pending?${params}`)
      setEvents(data.events || [])
      setTotal(data.total || 0)
    } catch (err: any) {
      const msg = getErrorMessage(err, t('review.errorLoadingApprovals'))

      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }, [lotId, page])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  const handleApprove = async (eventId: number) => {
    try {
      await api.post('/approvals/approve', { event_id: eventId })
      toast.success(t('review.eventApproved'))
      fetchEvents()
    } catch (err: any) {
      toast.error(getErrorMessage(err, t('review.errorApprove')))
    }
  }

  const handleRejectSingle = async () => {
    if (!rejectReason || rejectReason.length < 10) {
      toast.warning(t('review.reasonMinLength'))
      return
    }
    try {
      await api.post('/approvals/reject', { event_id: singleRejectId, observations: rejectReason })
      setShowRejectModal(false)
      setRejectReason('')
      setSingleRejectId(null)
      toast.success(t('review.eventRejected'))
      fetchEvents()
    } catch (err: any) {
      toast.error(getErrorMessage(err, t('review.errorReject')))
    }
  }

  const openRejectSingle = (eventId: number) => {
    setSingleRejectId(eventId)
    setRejectTarget('single')
    setRejectReason('')
    setShowRejectModal(true)
  }

  const handleBatchApprove = async () => {
    const selected = events.filter((e: any) => e._checked)
    if (selected.length === 0) return alert(t('common.noSelection'))
    try {
      await api.post('/approvals/batch-approve', { event_ids: selected.map((e: any) => e.id) })
      fetchEvents()
    } catch (err: any) {
      alert(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleBatchReject = async () => {
    if (!rejectReason || rejectReason.length < 10) return alert(t('review.reasonMinLength'))
    const selected = events.filter((e: any) => e._checked)
    if (selected.length === 0) return alert('Selecciona al menos un evento')
    try {
      await api.post('/approvals/batch-reject', { event_ids: selected.map((e: any) => e.id), observations: rejectReason })
      setShowRejectModal(false)
      setRejectReason('')
      fetchEvents()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error')
    }
  }

  const openBatchReject = () => {
    const selected = events.filter((e: any) => e._checked)
    if (selected.length === 0) return alert('Selecciona al menos un evento')
    setRejectTarget('batch')
    setRejectReason('')
    setShowRejectModal(true)
  }

  const toggleCheck = (id: number) => {
    setEvents(prev => prev.map(e => e.id === id ? { ...e, _checked: !e._checked } : e))
  }

  const selectedCount = events.filter((e: any) => e._checked).length

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2"><CheckCircle size={24} /> {t('review.approvalPanel')}</h1>
        <div className="flex gap-2">
          <Link to="/review" className="bg-slate-100 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-200 transition flex items-center gap-1.5">
            <ArrowLeft size={16} /> {t('nav.review')}
          </Link>
        </div>
      </div>

      {/* Batch Actions Bar */}
      {selectedCount > 0 && (
        <div className="bg-[#1E3A5F] text-white rounded-xl px-5 py-3 mb-4 flex items-center justify-between">
          <span className="text-sm">{selectedCount} {t('review.selectedEvents')}</span>
          <div className="flex gap-2">
            <button onClick={handleBatchApprove}
              className="bg-emerald-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-emerald-600 transition">
                <Check size={16} /> {t('review.approveAll')}
              </button>
              <button onClick={openBatchReject}
                className="bg-red-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-red-600 transition flex items-center gap-1.5">
                <X size={16} /> {t('review.rejectAll')}
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4 flex flex-wrap gap-3 items-center">
        <input type="number" placeholder={t('review.lot') + ' ID'} value={lotId} onChange={e => { setLotId(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-28" />
        <span className="text-sm text-slate-500 ml-auto">{total} {t('common.results')}</span>
      </div>

      {/* Mobile Cards */}
      <div className="lg:hidden space-y-3">
        {loading && <p className="text-slate-500 text-center py-8">{t('common.loading')}</p>}
        {!loading && events.length === 0 && (
          <div className="text-center py-12">
            <p className="text-4xl mb-2">✅</p>
            <p className="text-slate-500">{t('review.noPendingApprovals')}</p>
          </div>
        )}
        {events.map((event: any) => (
          <div key={event.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-start gap-3">
              <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)}
                className="mt-1 h-4 w-4 rounded border-slate-300" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-slate-800">#{event.id}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>
                    {event.status}
                  </span>
                </div>
                <p className="text-sm text-slate-600">{getEventLabel(t, event.event_type)}</p>
                <p className="text-xs text-slate-400">{t('review.lotPrefix')}{event.lot_id} | {event.event_date}</p>
              </div>
            </div>
            <div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">
              <button onClick={() => handleApprove(event.id)}
                className="flex-1 bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-emerald-200 transition">
                ✓ {t('review.approve')}
              </button>
              <button onClick={() => openRejectSingle(event.id)}
                className="flex-1 bg-red-100 text-red-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-red-200 transition">
                ✗ {t('review.reject')}
              </button>
              <Link to={`/review/${event.id}`}
                className="flex-1 bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-slate-200 transition text-center">
                🔎
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop Table */}
      <div className="hidden lg:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="w-10 px-4 py-3 text-left">
                <input type="checkbox" onChange={e => setEvents(prev => prev.map(ev => ({ ...ev, _checked: e.target.checked })))} />
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.type')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Lote</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.date')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.status')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">{t('common.loading')}</td></tr>
            )}
            {!loading && events.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                <p className="text-2xl mb-1">✅</p>
                {t('review.noPendingApprovals')}
              </td></tr>
            )}
            {events.map((event: any) => (
              <tr key={event.id} className="hover:bg-slate-50 transition">
                <td className="px-4 py-3">
                  <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)} className="rounded" />
                </td>
                <td className="px-4 py-3 font-mono text-xs">#{event.id}</td>
                <td className="px-4 py-3">{getEventLabel(t, event.event_type)}</td>
                <td className="px-4 py-3 font-mono text-xs">L-{event.lot_id}</td>
                <td className="px-4 py-3 text-slate-500">{event.event_date}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>
                    {event.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    <button onClick={() => handleApprove(event.id)}
                      className="bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-emerald-200 transition">
                      ✓ {t('review.approve')}
                    </button>
                    <button onClick={() => openRejectSingle(event.id)}
                      className="bg-red-100 text-red-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-red-200 transition">
                      ✗ {t('review.reject')}
                    </button>
                    <Link to={`/review/${event.id}`}
                      className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-slate-200 transition">
                      🔎
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 disabled:opacity-40">←</button>
          <span className="px-3 py-1.5 text-sm text-slate-600">{page + 1} / {Math.ceil(total / limit)}</span>
          <button disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 disabled:opacity-40">→</button>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowRejectModal(false)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold text-[#1E3A5F] mb-2">
              ✗ {rejectTarget === 'batch' ? t('review.rejectAll') : t('review.reject')}
            </h2>
            <p className="text-sm text-slate-500 mb-4">{t('review.rejectionReasonRequired')}</p>
            <textarea value={rejectReason} onChange={e => setRejectReason(e.target.value)}
              rows={3}
              placeholder={t('review.rejectionReasonPlaceholder')}
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm mb-4 focus:ring-2 focus:ring-red-400" />
            <div className="flex gap-3">
              <button onClick={rejectTarget === 'batch' ? handleBatchReject : handleRejectSingle}
                className="flex-1 bg-red-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-red-700 transition">
                ✗ {t('common.confirm')}
              </button>
              <button onClick={() => setShowRejectModal(false)}
                className="flex-1 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
