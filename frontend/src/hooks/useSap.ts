import { useState, useCallback } from 'react'
import { sapService, type SapReference, type SapSyncJob, type SapPayload } from '../services/sap.service'
import { getErrorMessage } from '../components/Toast'

export function useSap() {
  const [references, setReferences] = useState<SapReference[]>([])
  const [jobs, setJobs] = useState<SapSyncJob[]>([])
  const [payloads, setPayloads] = useState<SapPayload[]>([])
  const [connection, setConnection] = useState<{ connected: boolean; adapter: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [refRes, jobRes, payRes, connRes] = await Promise.all([
        sapService.listReferences({ limit: 10 }),
        sapService.listSyncJobs({ limit: 5 }),
        sapService.listPayloads({ limit: 5 }),
        sapService.checkConnection(),
      ])
      setReferences(refRes.data?.references || [])
      setJobs(jobRes.data?.jobs || [])
      setPayloads(payRes.data?.payloads || [])
      setConnection(connRes.data)
    } catch (e: any) {
      setError(getErrorMessage(e, 'Error al cargar datos SAP'))
    } finally {
      setLoading(false)
    }
  }, [])

  const consolidate = useCallback(async () => {
    const res = await sapService.consolidate()
    await fetchAll()
    return res.data
  }, [fetchAll])

  const exportToSap = useCallback(async () => {
    const res = await sapService.exportToSap()
    await fetchAll()
    return res.data
  }, [fetchAll])

  const importReferences = useCallback(async (refType: string, entries: Record<string, unknown>[]) => {
    const res = await sapService.importReferences({ ref_type: refType, entries })
    await fetchAll()
    return res.data
  }, [fetchAll])

  return {
    references, jobs, payloads, connection, loading, error,
    fetchAll, consolidate, exportToSap, importReferences,
  }
}
