import { useState, useCallback } from 'react'
import { approvalsService } from '../services/approvals.service'
import { getErrorMessage } from '../components/Toast'

export function useApprovals() {
  const [events, setEvents] = useState<Record<string, unknown>[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPending = useCallback(async (lotId?: number, offset = 0) => {
    setLoading(true)
    setError(null)
    try {
      const res = await approvalsService.getPending({ lot_id: lotId, limit: 20, offset })
      setEvents(res.data?.events || [])
      setTotal(res.data?.total || 0)
    } catch (e: any) {
      setError(getErrorMessage(e, 'Error al cargar aprobaciones pendientes'))
    } finally {
      setLoading(false)
    }
  }, [])

  const approve = useCallback(async (eventId: number) => {
    await approvalsService.approve({ event_id: eventId })
  }, [])

  const reject = useCallback(async (eventId: number, observations?: string) => {
    await approvalsService.reject({ event_id: eventId, observations })
  }, [])

  const batchApprove = useCallback(async (eventIds: number[]) => {
    await approvalsService.batchApprove({ event_ids: eventIds })
  }, [])

  const batchReject = useCallback(async (eventIds: number[], observations?: string) => {
    await approvalsService.batchReject({ event_ids: eventIds, observations })
  }, [])

  return {
    events, total, loading, error,
    fetchPending, approve, reject, batchApprove, batchReject,
  }
}
