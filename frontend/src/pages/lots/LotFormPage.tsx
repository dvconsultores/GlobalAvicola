/**
 * LotFormPage — Crear nuevo lote (T-073)
 * Ruta: /lots/new
 * Llama POST /lots
 * Campos: lot_code, bird_type, farm_id, house_id, genetic_line_id, breed_id, start_date, sap_reference
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, Bird } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import { Button, Input, Card, CardHeader, CardBody } from '../../components/ui'

const BIRD_TYPES = ['grandparent', 'breeder', 'broiler', 'hatchery'] as const

const schema = z.object({
 lot_code: z.string().min(2, 'Mínimo 2 caracteres').max(50),
 bird_type: z.enum(BIRD_TYPES, { error: 'Requerido' }),
 farm_id: z.coerce.number().min(1, 'Requerido'),
 house_id: z.coerce.number().optional().nullable(),
 genetic_line_id: z.coerce.number().optional().nullable(),
 breed_id: z.coerce.number().optional().nullable(),
 start_date: z.string().optional(),
 sap_reference: z.string().optional(),
})

type FormInput = z.input<typeof schema>
type FormValues = z.output<typeof schema>

interface SelectOption { id: number; name: string; code?: string }

export default function LotFormPage() {
 const { t } = useTranslation()
 const navigate = useNavigate()
 const toast = useToast()

 const [farms, setFarms] = useState<SelectOption[]>([])
 const [houses, setHouses] = useState<SelectOption[]>([])
 const [lines, setLines] = useState<SelectOption[]>([])
 const [breeds, setBreeds] = useState<SelectOption[]>([])
 const [loadingMasters, setLoadingMasters] = useState(true)

 const {
 register,
 handleSubmit,
 watch,
 formState: { errors, isSubmitting },
 } = useForm<FormInput, unknown, FormValues>({ resolver: zodResolver(schema) })

 const selectedFarmId = watch('farm_id')
 const selectedLineId = watch('genetic_line_id')

 // `AC-FE10` / `OD-06`. El lote queda fijado a una **versión concreta** de curva, y esa
 // versión es la activa de su línea en el momento del alta. Quien crea el lote debe verla
 // antes de guardar: si la línea no tiene ninguna, se dice — callar equivale a insinuar que
 // habrá referencia y luego no haberla.
 const [curvaActiva, setCurvaActiva] = useState<{ version_label: string } | null>(null)
 const [curvaConsultada, setCurvaConsultada] = useState(false)

 useEffect(() => {
 let vigente = true
 if (!selectedLineId) { setCurvaActiva(null); setCurvaConsultada(false); return }
 setCurvaConsultada(false)
 api.get(`/masters/genetic-lines/${selectedLineId}/weight-curves`)
 .then(r => {
 if (!vigente) return
 setCurvaActiva((r.data ?? []).find((c: any) => c.is_active) ?? null)
 setCurvaConsultada(true)
 })
 .catch(() => { if (vigente) { setCurvaActiva(null); setCurvaConsultada(true) } })
 return () => { vigente = false }
 }, [selectedLineId])

 // Load masters
 useEffect(() => {
 const load = async () => {
 try {
 const [farmRes, houseRes, lineRes, breedRes] = await Promise.allSettled([
 api.get('/masters/farms?limit=100'),
 api.get('/masters/houses?limit=100'),
 api.get('/masters/genetic-lines?limit=100'),
 api.get('/masters/breeds?limit=100'),
 ])
 if (farmRes.status === 'fulfilled') setFarms(farmRes.value.data ?? [])
 if (houseRes.status === 'fulfilled') setHouses(houseRes.value.data ?? [])
 if (lineRes.status === 'fulfilled') setLines(lineRes.value.data ?? [])
 if (breedRes.status === 'fulfilled') setBreeds(breedRes.value.data ?? [])
 } finally {
 setLoadingMasters(false)
 }
 }
 load()
 }, [])

 // Filter houses by selected farm
 const filteredHouses = selectedFarmId
 ? houses.filter((h: any) => !h.farm_id || h.farm_id === Number(selectedFarmId))
 : houses

 const onSubmit = async (values: FormValues) => {
 try {
 const payload = {
 lot_code: values.lot_code,
 bird_type: values.bird_type,
 farm_id: values.farm_id || null,
 house_id: values.house_id || null,
 genetic_line_id: values.genetic_line_id || null,
 breed_id: values.breed_id || null,
 start_date: values.start_date || null,
 sap_reference: values.sap_reference || null,
 }
 const { data } = await api.post('/lots', payload)
 toast.success(t('lots.createdSuccess', 'Lote creado exitosamente'))
 navigate(`/lots/${data.id}`)
 } catch (err: any) {
 toast.error(err?.response?.data?.detail ?? t('errors.saveFailed', 'Error al guardar'))
 }
 }

 const selectClass = 'w-full h-10 px-3 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-[#5a9bba] disabled:bg-slate-50 disabled'

 return (
 <div className="py-4 sm:py-6">
 {/* Header */}
 <div className="flex items-center gap-3 mb-6">
 <button
 onClick={() => navigate('/lots')}
 className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-500 hover hover:bg-slate-100 transition-colors"
 aria-label={t('common.back', 'Volver')}
 >
 <ArrowLeft size={18} />
 </button>
 <div className="flex items-center gap-2">
 <Bird size={22} className="text-[#1E3A5F]" />
 <h1 className="text-xl font-bold text-[#1E3A5F]">{t('lots.newLot', 'Nuevo Lote')}</h1>
 </div>
 </div>

 <form onSubmit={handleSubmit(onSubmit)} noValidate>
 <Card>
 <CardHeader title={t('lots.basicInfo', 'Información básica')} />
 <CardBody className="space-y-4">
 {/* Código */}
 <Input
 label={t('lots.code', 'Código')}
 required
 placeholder="AVI-REP-PES-2024-001"
 error={errors.lot_code?.message}
 {...register('lot_code')}
 />

 {/* Tipo de ave */}
 <div className="flex flex-col gap-1">
 <label className="text-sm font-semibold text-slate-700">
 {t('lots.type', 'Tipo de producción')}
 <span className="text-red-500 ml-0.5" aria-hidden>*</span>
 </label>
 <select className={selectClass} {...register('bird_type')}>
 <option value="">{t('lots.selectType', 'Seleccionar tipo...')}</option>
 {BIRD_TYPES.map(bt => (
 <option key={bt} value={bt}>{t(`birdTypes.${bt}`, bt)}</option>
 ))}
 </select>
 {errors.bird_type && (
 <p className="text-xs text-red-600">{errors.bird_type.message}</p>
 )}
 </div>

 {/* Fecha inicio */}
 <Input
 label={t('lots.start', 'Fecha inicio')}
 type="date"
 error={errors.start_date?.message}
 {...register('start_date')}
 />
 </CardBody>
 </Card>

 <Card className="mt-4">
 <CardHeader title={t('lots.locationInfo', 'Ubicación')} />
 <CardBody className="space-y-4">
 {/* Granja */}
 <div className="flex flex-col gap-1">
 <label className="text-sm font-semibold text-slate-700">
 {t('masters.farms', 'Granja')}
 <span className="text-red-500 ml-0.5" aria-hidden>*</span>
 </label>
 <select
 className={selectClass}
 disabled={loadingMasters}
 {...register('farm_id')}
 >
 <option value="">{loadingMasters ? t('common.loading') : t('lots.selectFarm', 'Seleccionar granja...')}</option>
 {farms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
 </select>
 {errors.farm_id && <p className="text-xs text-red-600">{errors.farm_id.message}</p>}
 </div>

 {/* Galpón */}
 <div className="flex flex-col gap-1">
 <label className="text-sm font-semibold text-slate-700">{t('masters.houses', 'Galpón')}</label>
 <select className={selectClass} {...register('house_id')}>
 <option value="">{t('lots.selectHouse', 'Seleccionar galpón...')}</option>
 {filteredHouses.map(h => <option key={h.id} value={h.id}>{h.name}</option>)}
 </select>
 </div>
 </CardBody>
 </Card>

 <Card className="mt-4">
 <CardHeader title={t('lots.genetics', 'Genética')} />
 <CardBody className="space-y-4">
 {/* Línea genética */}
 <div className="flex flex-col gap-1">
 <label htmlFor="lot-genetic-line" className="text-sm font-semibold text-slate-700">{t('masters.geneticLines', 'Línea genética')}</label>
 <select id="lot-genetic-line" className={selectClass} {...register('genetic_line_id')}>
 <option value="">{t('lots.selectLine', 'Seleccionar línea...')}</option>
 {lines.map(l => <option key={l.id} value={l.id}>{l.name}{l.code ? ` (${l.code})` : ''}</option>)}
 </select>
 {curvaConsultada && (
 curvaActiva ? (
 <p className="text-xs text-slate-600">
 {t('curves.lotWillUse')}: <strong className="font-mono">{curvaActiva.version_label}</strong>
 </p>
 ) : (
 <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
 {t('curves.noActiveCurve')}
 </p>
 )
 )}
 </div>

 {/* Raza */}
 <div className="flex flex-col gap-1">
 <label className="text-sm font-semibold text-slate-700">{t('masters.breeds', 'Raza')}</label>
 <select className={selectClass} {...register('breed_id')}>
 <option value="">{t('lots.selectBreed', 'Seleccionar raza...')}</option>
 {breeds.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
 </select>
 </div>
 </CardBody>
 </Card>

 <Card className="mt-4">
 <CardHeader title={t('lots.integration', 'Integración SAP')} />
 <CardBody>
 <Input
 label={t('lots.sapReference', 'Referencia SAP')}
 placeholder="SAP-2024-..."
 helperText={t('lots.sapRefHelper', 'Opcional. Centro de costo o referencia en SAP.')}
 {...register('sap_reference')}
 />
 </CardBody>
 </Card>

 {/* Actions */}
 <div className="flex items-center justify-end gap-3 mt-6">
 <Button variant="secondary" type="button" onClick={() => navigate('/lots')}>
 {t('common.cancel', 'Cancelar')}
 </Button>
 <Button type="submit" loading={isSubmitting}>
 {t('lots.create', 'Crear Lote')}
 </Button>
 </div>
 </form>
 </div>
 )
}
