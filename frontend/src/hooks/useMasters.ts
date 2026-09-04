import { useState, useEffect, useCallback } from 'react'
import { mastersService, type MasterEntity } from '../services/masters.service'

export function useMasters(entity: string, autoFetch = true) {
  const [items, setItems] = useState<MasterEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchItems = useCallback(async (search?: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await mastersService.list(entity, { limit: 100, search })
      setItems(Array.isArray(res.data) ? res.data : [])
    } catch (e: any) {
      setError(e?.response?.data?.error?.message || e?.message || 'Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }, [entity])

  useEffect(() => {
    if (autoFetch) fetchItems()
  }, [autoFetch, fetchItems])

  const create = useCallback(async (data: Record<string, unknown>) => {
    const res = await mastersService.create(entity, data)
    await fetchItems()
    return res.data
  }, [entity, fetchItems])

  const update = useCallback(async (id: number, data: Record<string, unknown>) => {
    const res = await mastersService.update(entity, id, data)
    await fetchItems()
    return res.data
  }, [entity, fetchItems])

  const deactivate = useCallback(async (id: number) => {
    await mastersService.deactivate(entity, id)
    await fetchItems()
  }, [entity, fetchItems])

  return { items, loading, error, fetchItems, create, update, deactivate, setItems }
}

/** Fetch reference data (farms, houses, genetic lines, breeds, feed types) for forms */
export function useMasterOptions() {
  const [farms, setFarms] = useState<MasterEntity[]>([])
  const [houses, setHouses] = useState<MasterEntity[]>([])
  const [geneticLines, setGeneticLines] = useState<MasterEntity[]>([])
  const [breeds, setBreeds] = useState<MasterEntity[]>([])
  const [feedTypes, setFeedTypes] = useState<MasterEntity[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [f, h, gl, b, ft] = await Promise.all([
        mastersService.listFarms({ limit: 100 }),
        mastersService.listHouses({ limit: 100 }),
        mastersService.listGeneticLines({ limit: 100 }),
        mastersService.listBreeds({ limit: 100 }),
        mastersService.listFeedTypes({ limit: 100 }),
      ])
      setFarms(f.data ?? [])
      setHouses(h.data ?? [])
      setGeneticLines(gl.data ?? [])
      setBreeds(b.data ?? [])
      setFeedTypes(ft.data ?? [])
    } catch {
      // Silently fail — individual forms handle errors
    } finally {
      setLoading(false)
    }
  }, [])

  return { farms, houses, geneticLines, breeds, feedTypes, loading, fetchAll }
}
