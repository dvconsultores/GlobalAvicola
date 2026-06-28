import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Pen, Check, X } from 'lucide-react'

interface SignaturePadProps {
 onSign: (signatureDataUrl: string) => void
 onCancel: () => void
 width?: number
 height?: number
 label?: string
}

/**
 * SignaturePad — canvas-based digital signature capture.
 * Used for critical operations: mortality recording, lot closure, bird dispatch.
 *
 * Mobile-first: touch-enabled with pointer events.
 * Desktop: mouse drawing support.
 */
export default function SignaturePad({
 onSign,
 onCancel,
 width = 320,
 height = 140,
 label,
}: SignaturePadProps) {
 const { t } = useTranslation()
 const canvasRef = useRef<HTMLCanvasElement>(null)
 const [isDrawing, setIsDrawing] = useState(false)
 const [hasSignature, setHasSignature] = useState(false)
 const lastPos = useRef<{ x: number; y: number } | null>(null)

 const getPos = (e: React.PointerEvent<HTMLCanvasElement>) => {
 const canvas = canvasRef.current
 if (!canvas) return { x: 0, y: 0 }
 const rect = canvas.getBoundingClientRect()
 return {
 x: e.clientX - rect.left,
 y: e.clientY - rect.top,
 }
 }

 const startDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
 setIsDrawing(true)
 setHasSignature(true)
 const pos = getPos(e)
 lastPos.current = pos
 const ctx = canvasRef.current?.getContext('2d')
 if (ctx) {
 ctx.beginPath()
 ctx.moveTo(pos.x, pos.y)
 }
 }

 const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
 if (!isDrawing) return
 const ctx = canvasRef.current?.getContext('2d')
 if (!ctx) return
 const pos = getPos(e)
 ctx.lineWidth = 2
 ctx.lineCap = 'round'
 ctx.strokeStyle = '#1E3A5F'
 ctx.lineTo(pos.x, pos.y)
 ctx.stroke()
 lastPos.current = pos
 }

 const stopDrawing = () => {
 setIsDrawing(false)
 lastPos.current = null
 }

 const handleClear = () => {
 const canvas = canvasRef.current
 if (!canvas) return
 const ctx = canvas.getContext('2d')
 if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
 setHasSignature(false)
 }

 const handleConfirm = () => {
 const canvas = canvasRef.current
 if (!canvas) return
 const dataUrl = canvas.toDataURL('image/png')
 onSign(dataUrl)
 }

 return (
 <div className="border-2 border-dashed border-slate-300 rounded-xl p-3 bg-slate-50">
 {label && (
 <p className="text-xs font-semibold text-slate-600 mb-2 flex items-center gap-1.5">
 <Pen size={13} /> {label}
 </p>
 )}
 <canvas
 ref={canvasRef}
 width={width}
 height={height}
 className="w-full bg-white rounded-lg border border-slate-200 cursor-crosshair touch-none"
 onPointerDown={startDrawing}
 onPointerMove={draw}
 onPointerUp={stopDrawing}
 onPointerLeave={stopDrawing}
 />
 <div className="flex items-center justify-between mt-2">
 <button
 type="button"
 onClick={handleClear}
 className="text-xs text-slate-500 hover:text-red-600 transition-colors"
 >
 {t('common.clear', 'Limpiar')}
 </button>
 <div className="flex gap-2">
 <button
 type="button"
 onClick={onCancel}
 className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-slate-600 hover bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
 >
 <X size={13} /> {t('common.cancel', 'Cancelar')}
 </button>
 <button
 type="button"
 onClick={handleConfirm}
 disabled={!hasSignature}
 className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
 >
 <Check size={13} /> {t('common.confirmSignature', 'Firmar')}
 </button>
 </div>
 </div>
 </div>
 )
}
