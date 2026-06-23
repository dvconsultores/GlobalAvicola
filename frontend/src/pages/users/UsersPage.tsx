import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2, X, Users, Monitor, Smartphone } from 'lucide-react'
import api from '../../services/api'


interface UserForm { username: string; first_name: string; last_name: string; email: string; phone: string; password: string; role_id: number | null; company_id: number | null; view_type: string; is_active: boolean }
const emptyForm: UserForm = { username: '', first_name: '', last_name: '', email: '', phone: '', password: '', role_id: null, company_id: null, view_type: 'web', is_active: true }

export default function UsersPage() {
  const { t } = useTranslation()
  const [users, setUsers] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<UserForm>(emptyForm)
  const [saving, setSaving] = useState(false)

  const fetchData = async () => { setLoading(true); try { const [ur, rr] = await Promise.all([api.get('/users'), api.get('/roles')]); setUsers(ur.data || []); setRoles(rr.data || []) } catch (err) { console.error(err) } finally { setLoading(false) } }
  useEffect(() => { fetchData() }, [])

  const openCreate = () => { setEditingId(null); setForm(emptyForm); setShowModal(true) }
  const openEdit = (user: any) => { setEditingId(user.id); setForm({ username: user.username, first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '', phone: user.phone || '', password: '', role_id: user.role_id, company_id: user.company_id, view_type: user.view_type || 'web', is_active: user.is_active }); setShowModal(true) }

  const handleSave = async () => {
    if (!form.username || !form.first_name || !form.email) return alert('Campos requeridos')
    setSaving(true)
    try { const payload: any = { ...form }; if (!payload.password) delete payload.password; if (!payload.role_id) payload.role_id = null
      if (editingId) { await api.put(`/users/${editingId}`, payload) } else { if (!form.password) return alert('Contraseña requerida'); await api.post('/users', payload) }
      setShowModal(false); fetchData() } catch (err: any) { alert(err.response?.data?.detail || 'Error') } finally { setSaving(false) }
  }

  const handleDelete = async (userId: number) => { if (!confirm('¿Eliminar usuario?')) return; try { await api.delete(`/users/${userId}`); fetchData() } catch (err: any) { alert(err.response?.data?.detail || 'Error') } }
  const handleToggleActive = async (user: any) => { try { await api.put(`/users/${user.id}`, { ...user, is_active: !user.is_active, password: undefined }); fetchData() } catch (err: any) { alert('Error') } }

  if (loading) return <div className="p-6 text-slate-500">{t('common.loading')}</div>

  return (<div className="p-4 sm:p-6 max-w-6xl mx-auto">
    <div className="flex items-center justify-between mb-6"><h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2"><Users size={24} /> {t('nav.users')}</h1><button onClick={openCreate} className="bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5"><Plus size={16} /> {t('common.create')}</button></div>
    <div className="hidden lg:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"><table className="w-full text-sm"><thead className="bg-slate-50 border-b border-slate-200"><tr><th className="px-4 py-3 text-left font-semibold text-slate-600">Usuario</th><th className="px-4 py-3 text-left font-semibold text-slate-600">Nombre</th><th className="px-4 py-3 text-left font-semibold text-slate-600">Email</th><th className="px-4 py-3 text-left font-semibold text-slate-600">Rol</th><th className="px-4 py-3 text-left font-semibold text-slate-600">Vista</th><th className="px-4 py-3 text-left font-semibold text-slate-600">Estado</th><th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.actions')}</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((u: any) => { const role = roles.find((r: any) => r.id === u.role_id); return <tr key={u.id} className="hover:bg-slate-50 transition"><td className="px-4 py-3 font-medium text-[#1E3A5F]">{u.username}</td><td className="px-4 py-3">{u.first_name} {u.last_name}</td><td className="px-4 py-3 text-slate-500">{u.email}</td><td className="px-4 py-3 text-slate-500">{role?.name || '—'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 w-fit ${u.view_type === 'mobile' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>{u.view_type === 'mobile' ? <Smartphone size={12} /> : <Monitor size={12} />} {u.view_type === 'mobile' ? 'Mobile' : 'Web'}</span></td><td className="px-4 py-3"><button onClick={() => handleToggleActive(u)} className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{u.is_active ? 'Activo' : 'Inactivo'}</button></td><td className="px-4 py-3"><div className="flex gap-1.5"><button onClick={() => openEdit(u)} className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"><Pencil size={14} /></button><button onClick={() => handleDelete(u.id)} className="p-1.5 rounded-lg text-red-500 hover:bg-red-50"><Trash2 size={14} /></button></div></td></tr> })}</tbody></table></div>

    <div className="lg:hidden space-y-3">{users.map((u: any) => { const role = roles.find((r: any) => r.id === u.role_id); return <div key={u.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4"><div className="flex items-center justify-between mb-2"><span className="font-semibold text-[#1E3A5F]">{u.username}</span><button onClick={() => handleToggleActive(u)} className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{u.is_active ? 'Activo' : 'Inactivo'}</button></div><p className="text-sm text-slate-600">{u.first_name} {u.last_name}</p><p className="text-xs text-slate-400">{u.email} · {role?.name || 'Sin rol'} · {u.view_type === 'mobile' ? '📱 Mobile' : '🖥️ Web'}</p><div className="flex gap-2 mt-3 border-t border-slate-100 pt-3"><button onClick={() => openEdit(u)} className="flex-1 bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-slate-200 transition flex items-center justify-center gap-1"><Pencil size={12} /> Editar</button><button onClick={() => handleDelete(u.id)} className="flex-1 bg-red-50 text-red-600 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-red-100 transition flex items-center justify-center gap-1"><Trash2 size={12} /> Eliminar</button></div></div> })}</div>

    {showModal && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowModal(false)}><div className="bg-white rounded-2xl shadow-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}><div className="flex items-center justify-between mb-4"><h2 className="text-lg font-bold text-[#1E3A5F]">{editingId ? t('common.edit') : t('common.create')} Usuario</h2><button onClick={() => setShowModal(false)} className="p-1 rounded-lg hover:bg-slate-100"><X size={20} /></button></div><div className="space-y-3">
    <input placeholder="Usuario *" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
    <div className="grid grid-cols-2 gap-3"><input placeholder="Nombre *" value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /><input placeholder="Apellido *" value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} className="border border-slate-300 rounded-lg px-3 py-2.5 text-sm" /></div>
    <input placeholder="Email *" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
    <input placeholder="Teléfono" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
    <input placeholder={editingId ? 'Nueva contraseña (vacío = no cambiar)' : 'Contraseña *'} type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
    <select value={form.role_id || ''} onChange={e => setForm({ ...form, role_id: e.target.value ? Number(e.target.value) : null })} className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"><option value="">Sin rol</option>{roles.map((r: any) => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
    <div><label className="block text-sm font-medium text-slate-700 mb-1.5">Tipo de Vista</label><div className="flex gap-3"><label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition ${form.view_type === 'mobile' ? 'border-[#2563EB] bg-blue-50' : 'border-slate-200'}`}><input type="radio" name="view_type" value="mobile" checked={form.view_type === 'mobile'} onChange={e => setForm({ ...form, view_type: e.target.value })} className="sr-only" /><Smartphone size={20} className={form.view_type === 'mobile' ? 'text-[#2563EB]' : 'text-slate-400'} /><span className="text-sm font-medium">Mobile</span></label><label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition ${form.view_type === 'web' ? 'border-[#2563EB] bg-blue-50' : 'border-slate-200'}`}><input type="radio" name="view_type" value="web" checked={form.view_type === 'web'} onChange={e => setForm({ ...form, view_type: e.target.value })} className="sr-only" /><Monitor size={20} className={form.view_type === 'web' ? 'text-[#2563EB]' : 'text-slate-400'} /><span className="text-sm font-medium">Web</span></label></div></div>
    </div><div className="flex gap-3 mt-5"><button onClick={handleSave} disabled={saving} className="flex-1 bg-[#1E3A5F] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition disabled:opacity-50">{saving ? t('common.saving') : t('common.save')}</button><button onClick={() => setShowModal(false)} className="flex-1 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">{t('common.cancel')}</button></div></div></div>}
  </div>)
}
