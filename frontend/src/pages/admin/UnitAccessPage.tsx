/**
 * GA-FE-02 · «Acceso por unidad» — administración de las cuatro unidades productivas de la
 * empresa efectiva y de las concesiones de usuario por unidad.
 *
 * Contrato: `GA_FE_02_BACKEND_CONTRACT_MATRIX.md` (B04–B10). Reglas duras:
 *   - La empresa efectiva la resuelve el backend; sin ella esta superficie FALLA CERRADO
 *     (`OD-14.d`) y NO realiza ninguna petición.
 *   - Habilitar/deshabilitar NO concede a nadie (`OD-16.d`).
 *   - Conceder/revocar son actos separados, gobernados por permiso, con el backend como
 *     autoridad final (la ocultación no es seguridad).
 *   - Tras cualquier mutación, el estado visible se reconcilia con el backend (refetch).
 *     Sin optimismo que mienta.
 */
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ShieldCheck } from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { hasPermission } from '../../auth/permissions'
import { businessUnitsService, type CompanyBusinessUnit, type GrantCandidate } from '../../services/businessUnits.service'
import { businessUnitName } from '../../data/businessUnits'
import { Button, Card, CardBody, ConfirmDialog, EmptyState } from '../../components/ui'
import { useToast } from '../../components/Toast'

type ConfirmState =
  | { type: 'enable' | 'disable'; code: string }
  | { type: 'revoke'; code: string; userId: number }
  | null

export default function UnitAccessPage() {
  const { t } = useTranslation()
  const toast = useToast()
  const sessionUser = useAuthStore(s => s.user)
  const effectiveCompanyId = sessionUser?.effective_company_id ?? null
  const companyName = useCompanyStore(s => s.activeCompanyName)

  const canUpdate = hasPermission(sessionUser, 'business_units:update')
  const canCreate = hasPermission(sessionUser, 'business_units:create')
  const canDelete = hasPermission(sessionUser, 'business_units:delete')

  const [units, setUnits] = useState<CompanyBusinessUnit[]>([])
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [savingCode, setSavingCode] = useState<string | null>(null)
  const [confirm, setConfirm] = useState<ConfirmState>(null)
  const [selectedCode, setSelectedCode] = useState('')
  const [candidates, setCandidates] = useState<GrantCandidate[]>([])
  const [candidatesLoading, setCandidatesLoading] = useState(false)

  const loadUnits = useCallback(async (): Promise<CompanyBusinessUnit[] | null> => {
    setLoading(true)
    setFailed(false)
    try {
      const list = await businessUnitsService.getCompanyBusinessUnits()
      setUnits(list)
      return list
    } catch {
      setFailed(true)
      toast.error(t('admin.units.loadError'))
      return null
    } finally {
      setLoading(false)
    }
  }, [t, toast])

  // Carga ligada a la EMPRESA EFECTIVA: al cambiar de empresa se refetchea y se limpia la
  // selección (AC-COMP-04/05 — sin datos obsoletos del inquilino anterior).
  // La dependencia es SOLO `effectiveCompanyId`: `loadUnits` cambia de identidad por render y
  // incluirlo aquí produciría un bucle de refetch (cazado en el RED de esta tranche).
  useEffect(() => {
    if (effectiveCompanyId == null) {
      setUnits([])
      return
    }
    setSelectedCode('')
    setCandidates([])
    void loadUnits()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveCompanyId])

  const selectedUnit = units.find(u => u.code === selectedCode) ?? null

  const loadCandidates = useCallback(async (code: string) => {
    setCandidatesLoading(true)
    try {
      const list = await businessUnitsService.getGrantCandidates(code)
      setCandidates(list)
    } catch {
      toast.error(t('admin.grants.loadError'))
      setCandidates([])
    } finally {
      setCandidatesLoading(false)
    }
  }, [t, toast])

  const onSelectUnit = (code: string) => {
    setSelectedCode(code)
    setCandidates([])
    if (!code) return
    const unit = units.find(u => u.code === code)
    if (!unit || !unit.is_enabled) return // unidad OFF: el contrato responde 409 — no se provoca
    void loadCandidates(code)
  }

  const afterUnitsChanged = async (code: string) => {
    const fresh = await loadUnits()
    if (selectedCode && fresh) {
      const u = fresh.find(x => x.code === selectedCode)
      if (u?.is_enabled) await loadCandidates(selectedCode)
      else setCandidates([])
    }
    void code
  }

  const runToggle = async () => {
    if (!confirm || confirm.type === 'revoke') return
    const { type, code } = confirm
    setSavingCode(code)
    try {
      if (type === 'enable') await businessUnitsService.enableCompanyBusinessUnit(code)
      else await businessUnitsService.disableCompanyBusinessUnit(code)
      toast.success(t(type === 'enable' ? 'admin.units.enabledSuccess' : 'admin.units.disabledSuccess'))
    } catch {
      toast.error(t('admin.units.saveError'))
    } finally {
      setSavingCode(null)
      setConfirm(null)
      await afterUnitsChanged(code)
    }
  }

  const runGrant = async (userId: number, code: string) => {
    setSavingCode(code)
    try {
      await businessUnitsService.grantBusinessUnit(userId, code)
      toast.success(t('admin.grants.grantedSuccess'))
    } catch {
      toast.error(t('admin.grants.saveError'))
    } finally {
      setSavingCode(null)
      await loadCandidates(code)
    }
  }

  const runRevoke = async () => {
    if (!confirm || confirm.type !== 'revoke') return
    const { code, userId } = confirm
    setSavingCode(code)
    try {
      await businessUnitsService.revokeBusinessUnit(userId, code)
      toast.success(t('admin.grants.revokedSuccess'))
    } catch {
      toast.error(t('admin.grants.saveError'))
    } finally {
      setSavingCode(null)
      setConfirm(null)
      await loadCandidates(code)
    }
  }

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
      <h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2">
        <ShieldCheck size={24} /> {t('admin.units.heading')}
      </h1>
      {effectiveCompanyId != null && (
        <span className="text-sm text-slate-600">
          {t('admin.context.company')} <strong className="text-[#1E3A5F]">{companyName ?? `#${effectiveCompanyId}`}</strong>
        </span>
      )}
    </div>
  )

  // ── Fail closed (OD-14.d / AC-COMP-06): sin empresa efectiva no se administra ni se pide nada.
  if (effectiveCompanyId == null) {
    return (
      <div className="py-4 sm:py-6">
        {header}
        <EmptyState
          icon={ShieldCheck}
          title={t('admin.context.none')}
          description={t('admin.context.noneHint')}
        />
      </div>
    )
  }

  return (
    <div className="py-4 sm:py-6">
      {header}

      {loading && units.length === 0 && (
        <div role="status" className="bg-white rounded-xl border border-slate-200 p-8 text-center text-sm text-slate-500">
          {t('common.loading')}
        </div>
      )}

      {failed && !loading && (
        <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-sm font-medium text-red-800 mb-3">{t('admin.units.loadError')}</p>
          <Button variant="secondary" size="sm" onClick={() => void loadUnits()}>
            {t('common.retry')}
          </Button>
        </div>
      )}

      {!failed && units.length > 0 && (
        <ul aria-label={t('admin.units.heading')} className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {units.map(u => (
            <li key={u.code} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-[#1E3A5F]">{businessUnitName(u.code, u.name_key, t)}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    u.is_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {t(u.is_enabled ? 'admin.units.state.enabled' : 'admin.units.state.disabled')}
                </span>
              </div>
              {canUpdate && (
                <div className="flex justify-end">
                  <Button
                    variant={u.is_enabled ? 'danger' : 'primary'}
                    size="sm"
                    loading={savingCode === u.code}
                    onClick={() => setConfirm({ type: u.is_enabled ? 'disable' : 'enable', code: u.code })}
                  >
                    {t(u.is_enabled ? 'admin.units.disable' : 'admin.units.enable')}
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {units.length > 0 && (
        <Card>
          <CardBody>
            <h2 className="text-lg font-semibold text-[#1E3A5F] mb-4">{t('admin.grants.heading')}</h2>

            <div className="flex items-center gap-3 mb-4">
              <label htmlFor="ga-fe02-unit" className="text-sm font-medium text-slate-700">
                {t('admin.grants.unitLabel')}
              </label>
              <select
                id="ga-fe02-unit"
                value={selectedCode}
                onChange={e => onSelectUnit(e.target.value)}
                className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option value="">—</option>
                {units.map(u => (
                  <option key={u.code} value={u.code}>
                    {businessUnitName(u.code, u.name_key, t)}
                  </option>
                ))}
              </select>
            </div>

            {selectedUnit && !selectedUnit.is_enabled && (
              <p role="status" className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5">
                {t('admin.grants.unitDisabledNotice')}
              </p>
            )}

            {selectedUnit && selectedUnit.is_enabled && (
              <>
                {candidatesLoading && (
                  <div role="status" className="text-sm text-slate-500 py-2">
                    {t('common.loading')}
                  </div>
                )}
                {!candidatesLoading && candidates.length === 0 && (
                  <p className="text-sm text-slate-500 py-2">{t('admin.grants.empty')}</p>
                )}
                {!candidatesLoading && candidates.length > 0 && (
                  <ul aria-label={t('admin.grants.heading')} className="divide-y divide-slate-100">
                    {candidates.map(c => (
                      <li key={c.user_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                        <div className="min-w-0">
                          <span className="font-medium text-[#1E3A5F]">{c.username}</span>
                          <span className="text-sm text-slate-500 ml-2">{c.display_name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              c.already_granted ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {t(c.already_granted ? 'admin.grants.state.granted' : 'admin.grants.state.notGranted')}
                          </span>
                          {!c.already_granted && canCreate && c.user_id !== sessionUser?.id && (
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={savingCode === selectedUnit.code}
                              onClick={() => void runGrant(c.user_id, selectedUnit.code)}
                            >
                              {t('admin.grants.grant')}
                            </Button>
                          )}
                          {c.already_granted && canDelete && (
                            <Button
                              variant="danger"
                              size="sm"
                              disabled={savingCode === selectedUnit.code}
                              onClick={() => setConfirm({ type: 'revoke', code: selectedUnit.code, userId: c.user_id })}
                            >
                              {t('admin.grants.revoke')}
                            </Button>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </CardBody>
        </Card>
      )}

      <ConfirmDialog
        open={confirm !== null}
        onClose={() => setConfirm(null)}
        onConfirm={() => {
          if (confirm?.type === 'revoke') void runRevoke()
          else void runToggle()
        }}
        title={t(
          confirm?.type === 'disable'
            ? 'admin.units.disableConfirmTitle'
            : confirm?.type === 'revoke'
              ? 'admin.grants.revokeConfirmTitle'
              : 'admin.units.enableConfirmTitle',
        )}
        message={t(
          confirm?.type === 'disable'
            ? 'admin.units.disableConfirmMessage'
            : confirm?.type === 'revoke'
              ? 'admin.grants.revokeConfirmMessage'
              : 'admin.units.enableConfirmMessage',
        )}
        confirmLabel={t(
          confirm?.type === 'disable'
            ? 'admin.units.disable'
            : confirm?.type === 'revoke'
              ? 'admin.grants.revoke'
              : 'admin.units.enable',
        )}
        variant={confirm?.type === 'enable' ? 'primary' : 'danger'}
        showWarning={confirm?.type === 'disable'}
        loading={savingCode !== null}
      />
    </div>
  )
}
