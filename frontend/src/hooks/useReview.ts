import { useState, useCallback } from 'react'
import { reviewService, type ApprovalAction } from '../services/review.service'
import { getErrorMessage } from '../components/Toast'

interface ReviewFilters {
  lot_id?: number
  event_type?: string
  date_from?: string
  date_to?: string
  farm_id?: number
  status?: string
  operator_id?: number
}

export function useReview() {
  const [events, setEvents] = useState<ApprovalAction[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPending = useCallback(async (filters?: ReviewFilters, offset = 0) => {
    setLoading(true)
    setError(null)
    try {
      const res = await reviewService.getPending({ ...filters, limit: 20, offset })
      setEvents(res.data?.events || [])
      setTotal(res.data?.total || 0)
    } catch (e: any) {
      setError(getErrorMessage(e, 'Error al cargar pendientes'))
    } finally {
      setLoading(false)
    }
  }, [])

  const startReview = useCallback(async (eventId: number) => {
    await reviewService.startReview(eventId)
  }, [])

  const returnEvent = useCallback(async (eventId: number, observations?: string) => {
    await reviewService.returnEvent({ event_id: eventId, observations })
  }, [])

  const completeReview = useCallback(async (eventId: number) => {
    await reviewService.completeReview({ event_id: eventId })
  }, [])

  const createBatch = useCallback(async (name: string, eventIds: number[]) => {
    const res = await reviewService.createBatch({ batch_name: name, event_ids: eventIds })
    return res.data
  }, [])

  return {
    events, total, loading, error,
    fetchPending, startReview, returnEvent, completeReview, createBatch,
  }
}
