import { useState, useCallback } from 'react'
import { reportsService, type KpiData, type LotReport } from '../services/reports.service'
import { getErrorMessage } from '../components/Toast'

export function useKpis(lotId?: number) {
  const [kpis, setKpis] = useState<KpiData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchKpis = useCallback(async (id?: number) => {
    const targetId = id ?? lotId
    if (!targetId) return
    setLoading(true)
    setError(null)
    try {
      const res = await reportsService.getKpis(targetId)
      setKpis(res.data)
    } catch (e: any) {
      setError(getErrorMessage(e, 'Error al cargar KPIs'))
    } finally {
      setLoading(false)
    }
  }, [lotId])

  return { kpis, loading, error, fetchKpis }
}

export function useLotReport() {
  const [report, setReport] = useState<LotReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReport = useCallback(async (lotId: number) => {
    setLoading(true)
    setError(null)
    try {
      const res = await reportsService.getLotReport(lotId)
      setReport(res.data)
    } catch (e: any) {
      setError(getErrorMessage(e, 'Error al cargar reporte'))
    } finally {
      setLoading(false)
    }
  }, [])

  return { report, loading, error, fetchReport }
}
