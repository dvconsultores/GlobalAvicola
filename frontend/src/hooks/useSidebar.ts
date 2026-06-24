/**
 * useSidebar — Estado del sidebar: secciones expandidas/colapsadas
 * Persiste en localStorage para recordar estado entre sesiones
 */
import { useState, useCallback, useEffect } from 'react'

const STORAGE_KEY = 'global-avicola-sidebar-sections'

function loadSavedState(): Record<string, boolean> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return JSON.parse(saved)
  } catch { /* ignore */ }
  return {}
}

function saveState(state: Record<string, boolean>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch { /* ignore */ }
}

export function useSidebar() {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(loadSavedState)

  useEffect(() => {
    saveState(expandedSections)
  }, [expandedSections])

  const isExpanded = useCallback(
    (key: string) => !!expandedSections[key],
    [expandedSections],
  )

  const toggleSection = useCallback((key: string) => {
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const setSectionExpanded = useCallback((key: string, expanded: boolean) => {
    setExpandedSections(prev => ({ ...prev, [key]: expanded }))
  }, [])

  const expandContaining = useCallback((sectionKey: string) => {
    setExpandedSections(prev => ({ ...prev, [sectionKey]: true }))
  }, [])

  return { expandedSections, isExpanded, toggleSection, setSectionExpanded, expandContaining }
}
