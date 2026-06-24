import { useState, useEffect, useCallback } from 'react'
import { operationsService, type OperationEvent } from '../services/operations.service'

interface UseOperationsOptions {
  lotId?: number
  eventType?: string
  status?: string
  limit?: number
  autoFetch?: boolean
}

export function useOperations(options: UseOperationsOptions = {}) {
  const { autoFetch = true, limit = 100 } = options
  const [events, setEvents] = useState<OperationEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async (extraParams?: Record<string, unknown>) => {
    setLoading(true)
    setError(null)
    try {
      const res = await operationsService.list({
        lot_id: options.lotId,
        event_type: options.eventType,
        status: options.status,
        limit,
        ...extraParams,
      })
      setEvents(Array.isArray(res.data) ? res.data : [])
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar operaciones')
    } finally {
      setLoading(false)
    }
  }, [options.lotId, options.eventType, options.status, limit])

  useEffect(() => {
    if (autoFetch) fetchEvents()
  }, [autoFetch, fetchEvents])

  return { events, loading, error, fetchEvents, setEvents }
}

export function useOperationDetail(id: number | undefined) {
  const [event, setEvent] = useState<OperationEvent | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDetail = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      // The API uses list with filters, so search by ID
      const res = await operationsService.list({ limit: 200 })
      const events = Array.isArray(res.data) ? res.data : []
      const found = events.find((e: any) => String(e.id) === String(id))
      if (found) setEvent(found)
      else throw new Error('Evento no encontrado')
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar operación')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    if (id) fetchDetail()
  }, [id, fetchDetail])

  return { event, loading, error, fetchDetail }
}

export function useMyPending() {
  const [ops, setOps] = useState<OperationEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPending = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await operationsService.list({
        registered_by_me: true,
        status: 'draft,registered',
        limit: 50,
      })
      const data = res.data as any
      setOps(data?.items ?? data ?? [])
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar pendientes')
    } finally {
      setLoading(false)
    }
  }, [])

  return { ops, loading, error, fetchPending, setOps }
}
