import { useState, useEffect, useCallback } from 'react'
import { lotsService, type LotResponse, type KpiResponse, type PhaseResponse } from '../services/lots.service'

interface UseLotsOptions {
  farmId?: number
  status?: string
  autoFetch?: boolean
}

export function useLots(options: UseLotsOptions = {}) {
  const { autoFetch = true } = options
  const [lots, setLots] = useState<LotResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchLots = useCallback(async (params?: { search?: string }) => {
    setLoading(true)
    setError(null)
    try {
      const res = await lotsService.list({ farm_id: options.farmId, status: options.status, ...params })
      setLots(Array.isArray(res.data) ? res.data : [])
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar lotes')
    } finally {
      setLoading(false)
    }
  }, [options.farmId, options.status])

  useEffect(() => {
    if (autoFetch) fetchLots()
  }, [autoFetch, fetchLots])

  return { lots, loading, error, fetchLots, setLots }
}

export function useLotDetail(id: number | undefined) {
  const [lot, setLot] = useState<LotResponse | null>(null)
  const [kpis, setKpis] = useState<KpiResponse | null>(null)
  const [phases, setPhases] = useState<PhaseResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDetail = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const [lotRes, kpiRes, phaseRes] = await Promise.all([
        lotsService.get(id),
        lotsService.list({}).catch(() => null), // KPIs fetched separately
        lotsService.getPhases(id),
      ])
      setLot(lotRes.data)
      setPhases(Array.isArray(phaseRes.data) ? phaseRes.data : [])
      if (kpiRes?.data) setKpis(kpiRes.data as unknown as KpiResponse)
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar detalle del lote')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    if (id) fetchDetail()
  }, [id, fetchDetail])

  return { lot, kpis, phases, loading, error, fetchDetail, setLot }
}
