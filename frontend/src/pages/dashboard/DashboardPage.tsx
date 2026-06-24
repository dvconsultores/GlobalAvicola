import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { Bird, FileText, Clock, CheckCircle, TrendingDown } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Card, CardHeader, CardBody, Badge, statusToVariant } from '../../components/ui'

const BIRD_TYPE_COLORS: Record<string, string> = {
  grandparent: 'bg-purple-100 text-purple-700 border-purple-200',
  breeder:     'bg-blue-100 text-blue-700 border-blue-200',
  hatchery:    'bg-amber-100 text-amber-700 border-amber-200',
  broiler:     'bg-emerald-100 text-emerald-700 border-emerald-200',
}

export default function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const toast = useToast()

  useEffect(() => {
    api.get('/dashboard/admin')
      .then(r => setData(r.data))
      .catch((e: any) => {
        const msg = getErrorMessage(e, t('dashboard.errorLoading'))
        setError(msg)
        toast.error(msg)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-4 sm:p-6 max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 h-24 animate-pulse bg-slate-100" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return <div className="p-6 text-red-600 bg-red-50 rounded-lg m-6">{error}</div>
  }

  const lotsByType: Record<string, number> = data?.lots_by_type ?? {}
  const totalActiveLots = Object.values(lotsByType).reduce((a, b) => a + (b as number), 0)
  const mortalityTrend: { week: string; mortality: number }[] = data?.mortality_trend ?? []

  const summaryCards = [
    {
      label: t('dashboard.totalEvents'),
      value: data?.total_events ?? 0,
      icon: <FileText size={18} />,
      color: 'text-blue-600 bg-blue-50',
    },
    {
      label: t('dashboard.pendingReview'),
      value: data?.pending_review ?? 0,
      icon: <Clock size={18} />,
      color: 'text-amber-600 bg-amber-50',
    },
    {
      label: t('dashboard.pendingApproval'),
      value: data?.pending_approval ?? 0,
      icon: <CheckCircle size={18} />,
      color: 'text-teal-600 bg-teal-50',
    },
    {
      label: t('dashboard.last7Days'),
      value: data?.last_7_days ?? 0,
      icon: <TrendingDown size={18} />,
      color: 'text-emerald-600 bg-emerald-50',
    },
  ]

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('nav.dashboard')}</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          {t('dashboard.welcome')}{user?.first_name ? `, ${user.first_name}` : ''}
        </p>
      </div>

      {/* Summary KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {summaryCards.map((card, i) => (
          <Card key={i}>
            <CardBody>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${card.color}`}>
                {card.icon}
              </div>
              <p className="text-2xl font-bold text-slate-800">{card.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{card.label}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Active lots by stage */}
      <Card>
        <CardHeader
          title={t('dashboard.activeLotsByStage', 'Lotes activos por etapa')}
          subtitle={`${totalActiveLots} ${t('dashboard.totalActive', 'lotes activos')}`}
          action={
            <Bird size={18} className="text-slate-400" />
          }
        />
        <CardBody>
          {totalActiveLots === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">{t('lots.noLots', 'Sin lotes activos')}</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {['grandparent', 'breeder', 'hatchery', 'broiler'].map(bt => (
                <div
                  key={bt}
                  className={`rounded-xl border p-4 ${BIRD_TYPE_COLORS[bt] ?? 'bg-slate-100 text-slate-600 border-slate-200'}`}
                >
                  <p className="text-2xl font-bold">{lotsByType[bt] ?? 0}</p>
                  <p className="text-xs font-medium mt-0.5">{t(`birdTypes.${bt}`, bt)}</p>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Mortality trend chart */}
      {mortalityTrend.length > 0 && (
        <Card>
          <CardHeader title={t('dashboard.mortalityTrend', 'Tendencia de mortalidad')} subtitle={t('dashboard.last8Weeks', 'Últimas 8 semanas')} />
          <CardBody>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mortalityTrend} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="week" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Line
                  type="monotone"
                  dataKey="mortality"
                  stroke="#DC2626"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#DC2626' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      )}

      {/* Status distribution + top event types */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Status distribution */}
        {data?.by_status && Object.keys(data.by_status).length > 0 && (
          <Card>
            <CardHeader title={t('dashboard.statusDistribution')} />
            <CardBody>
              <div className="flex flex-wrap gap-2">
                {Object.entries(data.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center gap-1.5">
                    <Badge variant={statusToVariant(status)} dot>
                      {t(`status.${status}`, status)}: {count as number}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {/* Top event types */}
        {data?.top_event_types && Object.keys(data.top_event_types).length > 0 && (
          <Card>
            <CardHeader title={t('dashboard.topEventTypes')} />
            <CardBody>
              <div className="space-y-2">
                {Object.entries(data.top_event_types).map(([etype, count]) => {
                  const max = Math.max(...Object.values(data.top_event_types) as number[])
                  const pct = Math.round(((count as number) / max) * 100)
                  return (
                    <div key={etype}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600">{t(`events.${etype}`, etype)}</span>
                        <span className="font-semibold text-slate-800">{count as number}</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#2563EB] rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  )
}
