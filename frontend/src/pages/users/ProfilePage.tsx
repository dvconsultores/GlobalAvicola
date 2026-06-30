import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { User, Lock, Save, Building2 } from 'lucide-react'
import api from '../../services/api'

export default function ProfilePage() {
 const { t } = useTranslation()
 const { user } = useAuthStore()
 const { activeCompanyName } = useCompanyStore()
 const [currentPassword, setCurrentPassword] = useState('')
 const [newPassword, setNewPassword] = useState('')
 const [confirmPassword, setConfirmPassword] = useState('')
 const [message, setMessage] = useState('')
 const [saving, setSaving] = useState(false)

 const handleChangePassword = async (e: React.FormEvent) => {
 e.preventDefault()
 if (newPassword !== confirmPassword) return setMessage(t('profile.passwordMismatch'))
 if (newPassword.length < 6) return setMessage(t('profile.passwordMinLength'))
 setSaving(true)
 try {
 await api.put(`/users/${user?.id}`, { password: newPassword })
 setMessage(t('profile.passwordUpdated'))
 setCurrentPassword(''); setNewPassword(''); setConfirmPassword('')
 } catch (err: any) {
 setMessage(t('profile.passwordError'))
 } finally { setSaving(false) }
 }

 return (
 <div className="py-4 sm:py-6">
 <h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2 mb-6"><User size={24} aria-hidden="true" /> {t('profile.title')}</h1>

 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
 <h2 className="font-semibold text-slate-700 mb-4">{t('profile.personalInfo')}</h2>
 <dl className="space-y-3 text-sm">
 <div className="flex justify-between py-2 border-b border-slate-50"><dt className="text-slate-500">{t('profile.username')}</dt><dd className="font-medium">{user?.username}</dd></div>
 <div className="flex justify-between py-2 border-b border-slate-50"><dt className="text-slate-500">{t('profile.name')}</dt><dd className="font-medium">{user?.first_name} {user?.last_name}</dd></div>
 <div className="flex justify-between py-2 border-b border-slate-50"><dt className="text-slate-500">{t('profile.email')}</dt><dd className="font-medium">{user?.email}</dd></div>
 {(activeCompanyName || user?.company_name) && (
 <div className="flex justify-between py-2 border-b border-slate-50">
 <dt className="text-slate-500 flex items-center gap-1.5"><Building2 size={14} /> {t('company.selector', 'Empresa')}</dt>
 <dd className="font-medium text-[#5a9bba]">{activeCompanyName || user?.company_name}</dd>
 </div>
 )}
 </dl>
 </div>

 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
 <h2 className="font-semibold text-slate-700 mb-4 flex items-center gap-2"><Lock size={18} aria-hidden="true" /> {t('profile.changePassword')}</h2>
 <form onSubmit={handleChangePassword} className="space-y-3">
 <input type="password" placeholder={t('profile.currentPassword')} value={currentPassword} onChange={e => setCurrentPassword(e.target.value)}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input type="password" placeholder={t('profile.newPassword')} value={newPassword} onChange={e => setNewPassword(e.target.value)}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 <input type="password" placeholder={t('profile.confirmPassword')} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm" />
 {message && <p className={`text-sm ${message === t('profile.passwordUpdated') ? 'text-emerald-600' : 'text-red-600'}`}>{message}</p>}
 <button type="submit" disabled={saving}
 className="bg-[#1E3A5F] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5 disabled:opacity-50">
 <Save size={16} aria-hidden="true" /> {saving ? t('common.saving') : t('profile.updatePassword')}
 </button>
 </form>
 </div>
 </div>
 )
}
