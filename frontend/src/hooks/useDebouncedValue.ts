import { useEffect, useState } from 'react'

/**
 * `F4` (AC-S1-F01): los filtros de texto que disparan peticiones al servidor
 * esperan `delayMs` desde la última tecla. Evita la ráfaga de `GET` por carácter.
 */
export function useDebouncedValue<T>(value: T, delayMs = 400): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const temporizador = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(temporizador)
  }, [value, delayMs])

  return debounced
}
