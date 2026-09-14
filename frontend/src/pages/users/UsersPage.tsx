import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2, X, Users, Monitor, Smartphone, Building2 } from 'lucide-react'
import api from '../../services/api'
import UserBusinessUnitsButton from './UserBusinessUnitsButton'
// GA-FE-04 · R-98/P-13: la autoridad de ACCIÓN es del permiso de la acción, no de la página.
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'


interface UserForm { username: string; first_name: string; last_name: string; email: string; phone: string; password: string; role_id: number | null; area_id: number | null; company_id: number | null; view_type: string; is_active: boolean }
type EstadoCarga = 'cargando' | 'ok' | 'prohibido' | 'error'

const emptyForm: UserForm = { username: '', first_name: '', last_name: '', email: '', phone: '', password: '', role_id: null, area_id: null, company_id: null, view_type: 'web', is_active: true }

export default function UsersPage() {
 const { t } = useTranslation()
 const can = useCan()
 const toast = useToast()
 const [users, setUsers] = useState<any[]>([])
 const [roles, setRoles] = useState<any[]>([])
 // `GA-REM-039`. Desde el maestro real: nunca una lista fija de nombres de área.
 const [areas, setAreas] = useState<any[]>([])
 const [companies, setCompanies] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [estado, setEstado] = useState<EstadoCarga>('cargando')
 const [catalogosParciales, setCatalogosParciales] = useState(false)
 const [showModal, setShowModal] = useState(false)
 const [editingId, setEditingId] = useState<number | null>(null)
 const [form, setForm] = useState<UserForm>(emptyForm)
 const [saving, setSaving] = useState(false)

 // `GA-REM-002` enmienda B · `AC16`. Los cuatro recursos **no** son iguales y por eso ya no
 // viajan juntos en un `Promise.all`: `/users` **es** la página, mientras que roles, empresas
 // y áreas solo rellenan desplegables del formulario. Antes una sola de las cuatro fallando
 // vaciaba la tabla entera y el `catch` lo escribía en consola, de modo que «no tienes
 // permiso» y «no hay usuarios» se veían exactamente igual. Esa confusión es lo que mantuvo
 // cuatro P0 de aislamiento invisibles.
 const fetchData = useCallback(async () => {
   setLoading(true); setEstado('cargando'); setCatalogosParciales(false)
   try {
     const ur = await api.get('/users')
     setUsers(ur.data || [])
     setEstado('ok')
   } catch (e: any) {
     const codigo = e?.response?.status
     // 403 y 401 son denegación; cualquier otra cosa es un fallo que el usuario debe poder
     // reintentar. Ninguno de los dos es una lista vacía.
     setEstado(codigo === 403 || codigo === 401 ? 'prohibido' : 'error')
     setUsers([])
     setLoading(false)
     return
   }
   // Los auxiliares se piden aparte y se toleran: que falte el catálogo de áreas degrada un
   // desplegable, no invalida la pantalla.
   const aux = await Promise.allSettled([
     api.get('/roles'), api.get('/masters/companies?limit=100'), api.get('/masters/areas?limit=100'),
   ])
   const [rr, cr, ar] = aux
   setRoles(rr.status === 'fulfilled' ? rr.value.data || [] : [])
   setCompanies(cr.status === 'fulfilled' ? cr.value.data || [] : [])
   setAreas(ar.status === 'fulfilled' ? ar.value.data || [] : [])
   if (aux.some(r => r.status === 'rejected')) setCatalogosParciales(true)
   setLoading(false)
 }, [])
 // eslint-disable-next-line react-hooks/set-state-in-effect
 useEffect(() => { fetchData() }, [fetchData])

 const openCreate = () => { setEditingId(null); setForm(emptyForm); setShowModal(true) }
 const openEdit = (user: any) => { setEditingId(user.id); setForm({ username: user.username, first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '', phone: user.phone || '', password: '', role_id: user.role_id, area_id: user.area_id ?? null, company_id: user.company_id, view_type: user.view_type || 'web', is_active: user.is_active }); setShowModal(true) }

 const handleSave = async () => {
 if (!form.username || !form.first_name || !form.email) return alert(t('users.fieldsRequired'))
 setSaving(true)
 try {
 // La contraseña no viaja en el cuerpo de edición: `UserUpdate` la rechaza. Enviarla ahí
 // devolvía 200 sin cambiar nada (P0-13). El restablecimiento tiene endpoint propio.
 const { password, ...datos } = form
 const payload: any = { ...datos, role_id: form.role_id || null, area_id: form.area_id || null }
 if (editingId) {
 await api.put(`/users/${editingId}`, payload)
 if (password) await api.post(`/users/${editingId}/password`, { new_password: password })
 } else {
 if (!password) return alert(t('users.passwordRequired'))
 await api.post('/users', { ...payload, password })
 }
 setShowModal(false); fetchData() } catch (err: any) {
      // `R-215`. Antes: `alert(detail)` con la lista cruda ⇒ «[object Object]».
      toast.error(getErrorMessage(err, t('common.error')))
    } finally { setSaving(false) }
 }

 const handleDelete = async (userId: number) => { if (!confirm(t('users.deleteConfirm'))) return; try { await api.delete(`/users/${userId}`); fetchData() } catch { alert(t('users.deleteError')) } }
 // Solo se envían los campos que `UserUpdate` admite: propagar el usuario entero
 // arrastraba `id`, `created_at` y demás, que el contrato rechaza.
 const handleToggleActive = async (user: any) => { try { await api.put(`/users/${user.id}`, { is_active: !user.is_active }); fetchData() } catch { alert(t('common.error')) } }

 if (loading) return <div className="py-4 sm:py-6 text-slate-500">{t('common.loading')}</div>

 return (<div className="py-4 sm:py-6">
 <div className="flex items-center justify-between mb-6"><div><h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2"><Users size={24} /> {t('nav.users')}</h1>{!can({ permission: 'users:create' }) && !can({ permission: 'users:update' }) && !can({ permission: 'users:delete' }) && (<p className="text-xs text-slate-400 mt-1">{t('actions.readOnlyViewer')}</p>)}</div>{can({ permission: 'users:create' }) && <button onClick={openCreate} className="bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5"><Plus size={16} /> {t('common.create')}</button>}</div>
 {loading && <div role="status" className="bg-white rounded-xl border border-slate-200 p-8 text-center text-sm text-slate-500">{t('common.loading')}</div>}

 {!loading && estado === 'prohibido' && <div role="alert" className="bg-amber-50 border border-amber-200 rounded-xl p-8 text-center"><p className="text-sm font-medium text-amber-800">{t('users.forbidden')}</p></div>}

 {!loading && estado === 'error' && <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-8 text-center"><p className="text-sm font-medium text-red-800 mb-3">{t('users.loadError')}</p><button onClick={fetchData} className="bg-white border border-red-300 text-red-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-100 transition">{t('common.retry')}</button></div>}

 {!loading && estado === 'ok' && users.length === 0 && <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-sm text-slate-500">{t('users.noUsers')}</div>}

 {!loading && estado === 'ok' && catalogosParciales && <div role="alert" className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-3 text-xs text-amber-800">{t('users.partialCatalogs')}</div>}

 {!loading && estado === 'ok' && users.length > 0 && <>
 <div className="hidden lg:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"><table className="w-full text-sm"><thead className="bg-slate-50 border-b border-slate-200"><tr><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.username')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.firstName')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.email')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.role')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.view')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('users.status')}</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.actions')}</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((u: any) => { const role = roles.find((r: any) => r.id === u.role_id); return <tr key={u.id} className="hover:bg-slate-50 transition"><td className="px-4 py-3 font-medium text-[#1E3A5F]">{u.username}</td><td className="px-4 py-3">{u.first_name} {u.last_name}</td><td className="px-4 py-3 text-slate-500">{u.email}</td><td className="px-4 py-3 text-slate-500">{role?.name || '—'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 w-fit ${u.view_type === 'mobile' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>{u.view_type === 'mobile' ? <Smartphone size={12} /> : <Monitor size={12} />} {u.view_type === 'mobile' ? t('users.mobile') : t('users.web')}</span></td><td className="px-4 py-3">{can({ permission: 'users:update' }) ? <button onClick={() => handleToggleActive(u)} className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{u.is_active ? t('users.active') : t('users.inactive')}</button> : <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{u.is_active ? t('users.active') : t('users.inactive')}</span>}</td><td className="px-4 py-3"><div className="flex gap-1.5">{can({ permission: 'users:update' }) && <button onClick={() => openEdit(u)} className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"><Pencil size={14} /></button>}{can({ permission: 'users:delete' }) && <button onClick={() => handleDelete(u.id)} className="p-1.5 rounded-lg text-red-500 hover:bg-red-50"><Trash2 size={14} /></button>}<UserBusinessUnitsButton user={u} /></div></td></tr> })}</tbody></table></div>

 <div className="lg:hidden space-y-3">{users.map((u: any) => { const role = roles.find((r: any) => r.id === u.role_id); return <div key={u.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4"><div className="flex items-center justify-between mb-2"><span className="font-semibold text-[#1E3A5F]">{u.username}</span>{can({ permission: 'users:update' }) && <button onClick={() => handleToggleActive(u)} className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{u.is_active ? t('users.active') : t('users.inactive')}</button>}</div><p className="text-sm text-slate-600">{u.first_name} {u.last_name}</p><p className="text-xs text-slate-400">{u.email} · {role?.name || t('users.noRole')} · {u.view_type === 'mobile'
 ? <><Smartphone size={12} className="inline-block mr-0.5 -mt-0.5" aria-hidden="true" />{t('users.mobile')}</>
 : <><Monitor size={12} className="inline-block mr-0.5 -mt-0.5" aria-hidden="true" />{t('users.web')}</>}</p><div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">{can({ permission: 'users:update' }) && <button onClick={() => openEdit(u)} className="flex-1 bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-slate-200 transition flex items-center justify-center gap-1"><Pencil size={12} /> {t('users.editUser')}</button>}{can({ permission: 'users:delete' }) && <button onClick={() => handleDelete(u.id)} className="flex-1 bg-red-50 text-red-600 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-red-100 transition flex items-center justify-center gap-1"><Trash2 size={12} /> {t('users.deleteUser')}</button>}</div></div> })}</div>
 </>}

 {showModal && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowModal(false)}><div className="bg-white rounded-2xl shadow-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}><div className="flex items-center justify-between mb-4"><h2 className="text-lg font-bold text-[#1E3A5F]">{editingId ? t('users.editUserTitle') : t('users.createUser')}</h2><button onClick={() => setShowModal(false)} className="p-1 rounded-lg hover:bg-slate-100"><X size={20} /></button></div><div className="space-y-3">
 <input placeholder={t('users.usernamePlaceholder')} value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <div className="grid grid-cols-2 gap-3"><input placeholder={t('users.firstNamePlaceholder')} value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /><input placeholder={t('users.lastNamePlaceholder')} value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /></div>
 <input placeholder={t('users.emailPlaceholder')} type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input placeholder={t('users.phonePlaceholder')} value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input placeholder={editingId ? t('users.newPasswordHint') : t('users.passwordPlaceholder')} type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <select value={form.role_id || ''} onChange={e => setForm({ ...form, role_id: e.target.value ? Number(e.target.value) : null })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"><option value="">{t('users.noRole')}</option>{roles.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>
 <div><label className="block text-sm font-medium text-slate-700 mb-1.5">{t('users.area')}</label><select value={form.area_id || ''} onChange={e => setForm({ ...form, area_id: e.target.value ? Number(e.target.value) : null })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"><option value="">{t('users.noArea')}</option>{areas.map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
 <div>
 <label className="block text-sm font-medium text-slate-700 mb-1.5 flex items-center gap-1.5"><Building2 size={14} /> {t('masters.companies', 'Empresa')}</label>
 <select value={form.company_id || ''} onChange={e => setForm({ ...form, company_id: e.target.value ? Number(e.target.value) : null })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"><option value="">{t('company.noCompany')}</option>{companies.filter((c: any) => c.is_active !== false).map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
 </div>
 <div className="grid grid-cols-2 gap-3"><input placeholder={t('users.firstNamePlaceholder')} value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /><input placeholder={t('users.lastNamePlaceholder')} value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /></div>
 <input placeholder={t('users.emailPlaceholder')} type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input placeholder={t('users.phonePlaceholder')} value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input placeholder={editingId ? t('users.newPasswordHint') : t('users.passwordPlaceholder')} type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <div><label className="block text-sm font-medium text-slate-700 mb-1.5">{t('users.viewType')}</label><div className="flex gap-3"><label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition ${form.view_type === 'mobile' ? 'border-[#5a9bba] bg-blue-50' : 'border-slate-200'}`}><input type="radio" name="view_type" value="mobile" checked={form.view_type === 'mobile'} onChange={e => setForm({ ...form, view_type: e.target.value })} className="sr-only" /><Smartphone size={20} className={form.view_type === 'mobile' ? 'text-[#5a9bba]' : 'text-slate-400'} /><span className="text-sm font-medium">{t('users.mobile')}</span></label><label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition ${form.view_type === 'web' ? 'border-[#5a9bba] bg-blue-50' : 'border-slate-200'}`}><input type="radio" name="view_type" value="web" checked={form.view_type === 'web'} onChange={e => setForm({ ...form, view_type: e.target.value })} className="sr-only" /><Monitor size={20} className={form.view_type === 'web' ? 'text-[#5a9bba]' : 'text-slate-400'} /><span className="text-sm font-medium">{t('users.web')}</span></label></div></div>
 </div><div className="flex gap-3 mt-5"><button onClick={handleSave} disabled={saving} className="flex-1 bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition disabled:opacity-50">{saving ? t('common.saving') : t('common.save')}</button><button onClick={() => setShowModal(false)} className="flex-1 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">{t('common.cancel')}</button></div></div></div>}
 </div>)
}
