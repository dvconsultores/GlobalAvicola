/**
 * Administración de roles y permisos — `GA-REM-034`, hallazgo `R-92`.
 *
 * `docs/02 §3.1.3` pide «CRUD de roles con permisos granulares» y no existía ninguna
 * superficie: ni ruta ni componente. El backend ya sabía crear un rol con sus permisos, pero
 * nadie los enviaba —`authService.createRole` declaraba solo `{name, description}`—.
 *
 * Los módulos y las acciones vienen del catálogo del servidor (`AC01`) y no de una lista
 * escrita aquí: repetirlos a mano los desincronizaría al añadir un módulo.
 */
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2, X, ShieldCheck } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'

interface Permiso { module: string; action: string; scope_type?: string }
interface RolForm { name: string; description: string; permissions: Permiso[] }

const formVacio: RolForm = { name: '', description: '', permissions: [] }

export default function RolesPage() {
 const can = useCan()
  const { t } = useTranslation()
  const [roles, setRoles] = useState<any[]>([])
  const [catalogo, setCatalogo] = useState<{ modules: string[]; actions: string[] }>({ modules: [], actions: [] })
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<RolForm>(formVacio)
  const [saving, setSaving] = useState(false)
  // `R-212` · AC-04.
  const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [rr, cr] = await Promise.all([
        api.get('/roles'),
        api.get('/roles/permissions-catalog'),
      ])
      setRoles(rr.data || [])
      setCatalogo(cr.data || { modules: [], actions: [] })
      setEstado('ok')
    } catch (e: any) {
      console.error(e)
      setEstado(e?.response?.status === 403 ? 'prohibido' : 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  if (estado !== 'ok') {
    return (
      <div className="p-4 sm:p-6">
        <ErrorState kind={estado} onRetry={fetchData} />
      </div>
    )
  }

  const tiene = (module: string, action: string) =>
    form.permissions.some(p => p.module === module && p.action === action)

  const alternar = (module: string, action: string) => {
    setForm(f => tiene(module, action)
      ? { ...f, permissions: f.permissions.filter(p => !(p.module === module && p.action === action)) }
      : { ...f, permissions: [...f.permissions, { module, action, scope_type: 'all' }] })
  }

  const abrirNuevo = () => { setEditingId(null); setForm(formVacio); setShowModal(true) }

  const abrirEdicion = (rol: any) => {
    setEditingId(rol.id)
    setForm({
      name: rol.name ?? '',
      description: rol.description ?? '',
      // El conjunto actual se carga entero: el guardado **sustituye**, así que lo que no se
      // vea marcado se retira.
      permissions: (rol.permissions ?? []).map((p: any) => ({
        module: p.module, action: p.action, scope_type: p.scope_type ?? 'all',
      })),
    })
    setShowModal(true)
  }

  const guardar = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editingId) await api.put(`/roles/${editingId}`, form)
      else await api.post('/roles', form)
      setShowModal(false)
      await fetchData()
    } catch {
      alert(t('common.error', 'Error'))
    } finally {
      setSaving(false)
    }
  }

  const desactivar = async (rol: any) => {
    if (!confirm(t('roles.deactivateConfirm', '¿Desactivar este rol?'))) return
    try {
      await api.put(`/roles/${rol.id}`, { is_active: false })
      await fetchData()
    } catch {
      alert(t('common.error', 'Error'))
    }
  }

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <ShieldCheck size={20} className="text-blue-600" /> {t('roles.title', 'Roles y permisos')}
        </h1>
        {can({ permission: 'users:create' }) && <button
          onClick={abrirNuevo}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg px-4 py-2"
        >
          <Plus size={16} /> {t('roles.createRole', 'Nuevo rol')}
        </button>}
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">{t('common.loading', 'Cargando...')}</p>
      ) : roles.length === 0 ? (
        <p className="text-sm text-slate-500">{t('roles.noRoles', 'Sin roles')}</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3">{t('roles.name', 'Nombre')}</th>
                <th className="text-left px-4 py-3">{t('roles.description', 'Descripción')}</th>
                <th className="text-left px-4 py-3">{t('roles.permissions', 'Permisos')}</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {roles.map(rol => (
                <tr key={rol.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-800">{rol.name}</td>
                  <td className="px-4 py-3 text-slate-500">{rol.description}</td>
                  <td className="px-4 py-3 text-slate-500">{(rol.permissions ?? []).length}</td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {can({ permission: 'users:update' }) && <button
                      onClick={() => abrirEdicion(rol)}
                      aria-label={t('roles.editRole', 'Editar rol')}
                      className="text-slate-400 hover:text-blue-600 p-1"
                    >
                      <Pencil size={16} />
                    </button>}
                    {can({ permission: 'users:delete' }) && <button
                      onClick={() => desactivar(rol)}
                      aria-label={t('roles.deactivate', 'Desactivar rol')}
                      className="text-slate-400 hover:text-red-600 p-1 ml-1"
                    >
                      <Trash2 size={16} />
                    </button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
              <h2 className="font-semibold text-slate-800">
                {editingId ? t('roles.editRole', 'Editar rol') : t('roles.createRole', 'Nuevo rol')}
              </h2>
              <button onClick={() => setShowModal(false)} aria-label={t('common.close', 'Cerrar')}>
                <X size={18} className="text-slate-400" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <label htmlFor="rol-name" className="block text-xs font-semibold text-slate-500 mb-1">
                  {t('roles.name', 'Nombre')}
                </label>
                <input
                  id="rol-name"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label htmlFor="rol-desc" className="block text-xs font-semibold text-slate-500 mb-1">
                  {t('roles.description', 'Descripción')}
                </label>
                <input
                  id="rol-desc"
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2">
                  {t('roles.permissions', 'Permisos')}
                </p>
                <div className="border border-slate-200 rounded-lg overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>
                        <th className="text-left px-3 py-2">{t('roles.module', 'Módulo')}</th>
                        {catalogo.actions.map(a => (
                          <th key={a} className="px-2 py-2">{t(`roles.actions.${a}`, a)}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {catalogo.modules.map(m => (
                        <tr key={m} className="border-t border-slate-100">
                          <td className="px-3 py-2 font-medium text-slate-700">
                            {t(`roles.modules.${m}`, m)}
                          </td>
                          {catalogo.actions.map(a => (
                            <td key={a} className="text-center px-2 py-2">
                              <input
                                type="checkbox"
                                aria-label={`${m}:${a}`}
                                checked={tiene(m, a)}
                                onChange={() => alternar(m, a)}
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800"
              >
                {t('common.cancel', 'Cancelar')}
              </button>
              <button
                onClick={guardar}
                disabled={saving || !form.name.trim()}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-lg font-medium"
              >
                {t('common.save', 'Guardar')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
