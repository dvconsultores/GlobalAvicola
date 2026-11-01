/**
 * GA-FE-02 · Acción «Unidades de negocio» por usuario dentro de la administración de usuarios.
 *
 * Componente autocontenido: botón de fila + modal de concesiones. Separa visualmente el estado
 * de la EMPRESA (unidad habilitada/inactiva) del estado del USUARIO (concedida / efectiva /
 * revocada histórica / no concedida) — `OD-16.d` no colapsa «encender» con «conceder».
 *
 * Sin autorización por nombre de rol: todo se decide por permiso (`hasPermission`).
 * El backend sigue siendo la autoridad (aquí solo se evita ofrecer acciones prohibidas).
 */
import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Layers } from 'lucide-react'
import { Button, ConfirmDialog, Modal } from '../../components/ui'
import { useToast } from '../../components/Toast'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { hasPermission } from '../../auth/permissions'
import { businessUnitsService, type CompanyBusinessUnit, type UserBusinessUnit } from '../../services/businessUnits.service'
import { businessUnitName, isLiveGrant } from '../../data/businessUnits'

interface TargetUser {
  id: number
  username: string
  first_name?: string | null
  last_name?: string | null
  company_name?: string | null
}

/**
 * Puerta mínima (sin hooks que requieran providers): decide por PERMISO si existe la acción.
 * El panel real se monta solo al pasar la puerta — así las pantallas que no tienen permiso
 * (o entornos sin ToastProvider) no cargan dependencias que no necesitan.
 */
export default function UserBusinessUnitsButton({ user }: { user: TargetUser }) {
  const sessionUser = useAuthStore(s => s.user)
  if (!hasPermission(sessionUser, 'business_units:read')) return null
  return <UserBusinessUnitsPanel user={user} />
}

function UserBusinessUnitsPanel({ user }: { user: TargetUser }) {
  const { t } = useTranslation()
  const toast = useToast()
  const sessionUser = useAuthStore(s => s.user)
  const activeCompanyName = useCompanyStore(s => s.activeCompanyName)

  const canCreate = hasPermission(sessionUser, 'business_units:create')
  const canDelete = hasPermission(sessionUser, 'business_units:delete')
  const isSelf = sessionUser?.id === user.id

  const [open, setOpen] = useState(false)
  const [units, setUnits] = useState<CompanyBusinessUnit[]>([])
  const [grants, setGrants] = useState<UserBusinessUnit[]>([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [revokeCode, setRevokeCode] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [u, g] = await Promise.all([
        businessUnitsService.getCompanyBusinessUnits(),
        businessUnitsService.getUserBusinessUnits(user.id),
      ])
      setUnits(u)
      setGrants(g)
    } catch {
      toast.error(t('users.businessUnits.loadError'))
    } finally {
      setLoading(false)
    }
  }, [user.id, t, toast])

  const openPanel = () => {
    setOpen(true)
    void load()
  }

  const closePanel = () => {
    setOpen(false)
    setRevokeCode(null)
  }

  const grant = async (code: string) => {
    setBusy(true)
    try {
      await businessUnitsService.grantBusinessUnit(user.id, code)
      toast.success(t('admin.grants.grantedSuccess'))
    } catch {
      toast.error(t('admin.grants.saveError'))
    } finally {
      setBusy(false)
      await load()
    }
  }

  const revoke = async () => {
    if (!revokeCode) return
    setBusy(true)
    try {
      await businessUnitsService.revokeBusinessUnit(user.id, revokeCode)
      toast.success(t('admin.grants.revokedSuccess'))
    } catch {
      toast.error(t('admin.grants.saveError'))
    } finally {
      setBusy(false)
      setRevokeCode(null)
      await load()
    }
  }

  /**
   * Tras revocar y volver a conceder, el backend devuelve DOS filas para el mismo código (la
   * revocada histórica y la viva) ordenadas por id. Quedarse con la primera (`find`) mostraba
   * «Revocada (histórica)» y ofrecía Conceder aunque la concesión viva existiera
   * (`SPEC 013` · AC-UI-02). Se prefiere la VIVA; si no hay, la revocada MÁS RECIENTE
   * (mayor `granted_at`; a igualdad, la última del arreglo).
   */
  const grantFor = (code: string): UserBusinessUnit | undefined => {
    const matching = grants.filter(x => x.code === code)
    const live = matching.filter(isLiveGrant)
    if (live.length > 0) return live[live.length - 1]
    let latest: UserBusinessUnit | undefined
    for (const g of matching) {
      if (!latest || new Date(g.granted_at).getTime() >= new Date(latest.granted_at).getTime()) latest = g
    }
    return latest
  }

  const stateFor = (code: string): { key: string; live: boolean; effective?: boolean } => {
    const g = grantFor(code)
    if (!g) return { key: 'admin.grants.state.notGranted', live: false }
    if (!isLiveGrant(g)) return { key: 'users.businessUnits.revokedHistoric', live: false }
    return { key: 'admin.grants.state.granted', live: true, effective: g.is_effective }
  }

  /**
   * `SPEC 013` · AC-UI-03 (`AR-15`/Y-1.1): el panel debe IDENTIFICAR a quién y en qué empresa
   * se está concediendo. Los rótulos de las columnas son de ESTADO; la identidad va en la
   * descripción del modal. Empresa: la activa del contexto (o la del propio usuario, o «—»).
   * Usuario: nombre completo; si no lo hay, el login (nunca una línea vacía).
   */
  const companyLabel = activeCompanyName || user.company_name || '—'
  const fullName = `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim()
  const nombre = fullName || user.username
  const panelDescription =
    `${t('users.businessUnits.companyLabel')}: ${companyLabel} · ` +
    `${t('users.businessUnits.userLabel')}: ${nombre} (${user.username})`

  /** Nombre visible de la unidad que se va a revocar (centinela si aún no se resolvió). */
  const revokeUnitLabel = (code: string | null): string => {
    if (!code) return '—'
    const unit = units.find(u => u.code === code)
    return businessUnitName(code, unit?.name_key, t)
  }

  return (
    <>
      <button
        type="button"
        aria-label={`${t('users.businessUnits.open')} — ${user.username}`}
        onClick={openPanel}
        className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"
      >
        <Layers size={14} />
      </button>

      <Modal
        open={open}
        onClose={closePanel}
        title={t('users.businessUnits.title')}
        description={panelDescription}
        size="lg"
      >
        {loading ? (
          <div role="status" className="py-6 text-center text-sm text-slate-500">
            {t('common.loading')}
          </div>
        ) : (
          <>
            {isSelf && (
              <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
                {t('users.businessUnits.selfNote')}
              </p>
            )}
            <div className="flex gap-4 text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
              <span>{t('users.businessUnits.companyState')}</span>
              <span>{t('users.businessUnits.userState')}</span>
            </div>
            <ul className="divide-y divide-slate-100">
              {units.map(u => {
                const st = stateFor(u.code)
                return (
                  <li key={u.code} className="py-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-[#1E3A5F]">{businessUnitName(u.code, u.name_key, t)}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          u.is_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {t(u.is_enabled ? 'admin.units.state.enabled' : 'admin.units.state.disabled')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          st.live ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {t(st.key)}
                      </span>
                      {st.live && st.effective && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          {t('admin.grants.state.effective')}
                        </span>
                      )}
                      {!st.live && !isSelf && canCreate && u.is_enabled && (
                        <Button variant="secondary" size="sm" disabled={busy} onClick={() => void grant(u.code)}>
                          {t('admin.grants.grant')}
                        </Button>
                      )}
                      {st.live && canDelete && (
                        <Button variant="danger" size="sm" disabled={busy} onClick={() => setRevokeCode(u.code)}>
                          {t('admin.grants.revoke')}
                        </Button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </>
        )}
      </Modal>

      <ConfirmDialog
        open={revokeCode !== null}
        onClose={() => setRevokeCode(null)}
        onConfirm={() => void revoke()}
        title={t('admin.grants.revokeConfirmTitle')}
        message={t('admin.grants.revokeConfirmMessage', {
          user: `${nombre} (${user.username})`,
          unit: revokeUnitLabel(revokeCode),
        })}
        confirmLabel={t('admin.grants.revoke')}
        variant="danger"
        loading={busy}
      />
    </>
  )
}
