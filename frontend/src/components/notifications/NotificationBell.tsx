/**
 * Campana de notificaciones internas — `AC16`…`AC19` de `GA-REM-038`.
 *
 * `OD-07` decidió que los avisos viven dentro de Global Avícola. Esto es ese «dentro»: la
 * única superficie por la que un usuario se entera de que su registro fue rechazado.
 *
 * No hay tiempo real y no se finge que lo haya: el proyecto no tiene WebSocket, SSE ni caché
 * de consultas, y `OD-07` exige que la notificación **exista** en el sistema, no que llegue al
 * instante. El contador se refresca al montar, al abrir el panel y con un sondeo espaciado.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Bell } from 'lucide-react'

import {
  destino, getUnreadCount, listNotifications, markRead, type Notification,
} from '../../services/notifications'

/** Un minuto. Suficiente para que el aviso aparezca solo; lejos de martillear la API. */
const SONDEO_MS = 60_000

function cuando(iso: string, t: (k: string, o?: any) => string): string {
  const minutos = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000)
  if (minutos < 1) return t('notifications.justNow')
  if (minutos < 60) return t('notifications.minutesAgo', { count: minutos })
  const horas = Math.floor(minutos / 60)
  if (horas < 24) return t('notifications.hoursAgo', { count: horas })
  return t('notifications.daysAgo', { count: Math.floor(horas / 24) })
}

export default function NotificationBell() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const contenedor = useRef<HTMLDivElement>(null)

  const [sinLeer, setSinLeer] = useState(0)
  const [abierto, setAbierto] = useState(false)
  const [avisos, setAvisos] = useState<Notification[]>([])
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  const refrescarContador = useCallback(async () => {
    try {
      setSinLeer(await getUnreadCount())
    } catch {
      // Un fallo del contador no debe romper la cabecera entera. El panel sí informa.
    }
  }, [])

  useEffect(() => {
    void refrescarContador()
    const reloj = setInterval(() => { void refrescarContador() }, SONDEO_MS)
    return () => clearInterval(reloj)
  }, [refrescarContador])

  // Cerrar al pulsar fuera, como el selector de empresa que ya vive en esta cabecera.
  useEffect(() => {
    function fuera(e: MouseEvent) {
      if (contenedor.current && !contenedor.current.contains(e.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', fuera)
    return () => document.removeEventListener('mousedown', fuera)
  }, [])

  const abrir = async () => {
    const siguiente = !abierto
    setAbierto(siguiente)
    if (!siguiente) return

    setCargando(true)
    setError('')
    try {
      setAvisos(await listNotifications(20))
      await refrescarContador()
    } catch {
      // `AC19`: un fallo de API **no** se presenta como bandeja vacía. Son cosas distintas y
      // confundirlas haría que un error de red pareciera «no tienes nada».
      setError(t('notifications.loadFailed'))
    } finally {
      setCargando(false)
    }
  }

  const abrirAviso = async (n: Notification) => {
    if (n.read_at === null) {
      try {
        const leida = await markRead(n.id)
        setAvisos(prev => prev.map(a => (a.id === n.id ? leida : a)))
        setSinLeer(c => Math.max(0, c - 1))
      } catch {
        setError(t('notifications.markFailed'))
        return
      }
    }
    const ruta = destino(n)
    if (ruta) {
      setAbierto(false)
      navigate(ruta)
    }
  }

  const titulo = (n: Notification) => t(`notifications.types.${n.notification_type}`)

  const detalle = (n: Notification): string => {
    const p = n.payload ?? {}
    if (n.notification_type === 'record_rejected') return String(p.observations ?? '')
    if (n.notification_type === 'sap_send_failed') return String(p.error_message ?? '')
    return ''
  }

  return (
    <div ref={contenedor} className="relative">
      <button
        onClick={abrir}
        aria-haspopup="dialog"
        aria-expanded={abierto}
        /* El número va en el nombre accesible y no solo en un punto de color: quien navega
           con lector de pantalla también debe saber cuántas tiene sin leer (`AC16`). */
        aria-label={sinLeer > 0
          ? t('notifications.bellWithUnread', { count: sinLeer })
          : t('notifications.bell')}
        className="relative inline-flex items-center justify-center h-7 w-7 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
      >
        <Bell size={15} />
        {sinLeer > 0 && (
          <span
            aria-hidden
            className="absolute -top-0.5 -right-0.5 min-w-[15px] h-[15px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold leading-[15px] text-center"
          >
            {sinLeer > 99 ? '99+' : sinLeer}
          </span>
        )}
      </button>

      {abierto && (
        <div
          role="dialog"
          aria-label={t('notifications.title')}
          className="absolute right-0 mt-2 w-[min(22rem,calc(100vw-2rem))] max-h-[70vh] overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-lg z-40"
        >
          <div className="px-4 py-2.5 border-b border-slate-100">
            <p className="text-sm font-semibold text-slate-700">{t('notifications.title')}</p>
          </div>

          {cargando ? (
            /* Mientras carga no se dice «no tienes nada»: sería mentira durante un segundo. */
            <p className="px-4 py-6 text-sm text-slate-500 text-center">{t('common.loading')}</p>
          ) : error ? (
            <p role="alert" className="px-4 py-6 text-sm text-red-600 text-center">{error}</p>
          ) : avisos.length === 0 ? (
            <p className="px-4 py-8 text-sm text-slate-400 text-center">
              {t('notifications.empty')}
            </p>
          ) : (
            <ul role="list" className="divide-y divide-slate-100">
              {avisos.map(n => (
                <li key={n.id} role="listitem">
                  <button
                    onClick={() => abrirAviso(n)}
                    className={`w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors ${
                      n.read_at === null ? 'bg-blue-50/40' : ''}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-slate-800">{titulo(n)}</p>
                      {/* Por texto y no solo por color de fondo (`AC17`). */}
                      <span className={`shrink-0 text-[10px] font-semibold uppercase tracking-wide ${
                        n.read_at === null ? 'text-blue-700' : 'text-slate-400'}`}>
                        {n.read_at === null ? t('notifications.unread') : t('notifications.read')}
                      </span>
                    </div>
                    {detalle(n) && (
                      <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{detalle(n)}</p>
                    )}
                    <p className="text-[11px] text-slate-400 mt-1">{cuando(n.created_at, t)}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
