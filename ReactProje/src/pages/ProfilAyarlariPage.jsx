import React, { useState } from 'react';
import { User, Mail, Lock, Camera, Shield, CheckCircle2, Loader2, Save } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { updateKullanici } from '../services/api';

const ROL_LABELS = {
    admin: 'Sistem Yöneticisi',
    depocu: 'Depo Sorumlusu',
    goruntuleyen: 'Görüntüleyici',
};

export default function ProfilAyarlariPage() {
    const { user, login } = useAuth(); // Assuming login or updateUser would update context if needed

    const [form, setForm] = useState({
        ad_soyad: user?.ad_soyad || '',
        kullanici_adi: user?.kullanici_adi || '',
    });

    const [passwordForm, setPasswordForm] = useState({
        mevcut_sifre: '',
        yeni_sifre: '',
        yeni_sifre_tekrar: '',
    });

    const [saving, setSaving] = useState(false);
    const [passwordSaving, setPasswordSaving] = useState(false);

    const initials = user?.ad_soyad
        ? user.ad_soyad.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : 'U';

    const handleProfileSubmit = async (e) => {
        e.preventDefault();
        if (!form.ad_soyad.trim() || !form.kullanici_adi.trim()) {
            toast.error('Gerekli alanları doldurunuz.');
            return;
        }

        setSaving(true);
        try {
            await updateKullanici(user.id, form);
            toast.success('Profil bilgileriniz güncellendi. Yeniden giriş yapmanız gerekebilir.');
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Profil güncellenemedi.');
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        if (passwordForm.yeni_sifre !== passwordForm.yeni_sifre_tekrar) {
            toast.error('Yeni şifreler eşleşmiyor.');
            return;
        }
        if (passwordForm.yeni_sifre.length < 6) {
            toast.error('Şifre en az 6 karakter olmalıdır.');
            return;
        }

        setPasswordSaving(true);
        try {
            await updateKullanici(user.id, { sifre: passwordForm.yeni_sifre });
            toast.success('Şifreniz başarıyla güncellendi.');
            setPasswordForm({ mevcut_sifre: '', yeni_sifre: '', yeni_sifre_tekrar: '' });
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Şifre güncellenemedi.');
        } finally {
            setPasswordSaving(false);
        }
    };

    return (
        <>
            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
            `}} />

            <div className="max-w-[1000px] mx-auto space-y-8 animate-[scaleIn_0.3s_ease-out]">

                {/* Header Section */}
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Profil Ayarları</h1>
                    <p className="mt-2 text-sm text-slate-500">
                        Kişisel bilgilerinizi, sistem tercihlerinizi ve güvenlik ayarlarınızı yönetin.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Left Column: Profile Card */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden p-6 sm:p-8 flex flex-col items-center text-center">

                            <div className="relative mb-6">
                                <div className="w-28 h-28 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg border-4 border-white">
                                    <span className="text-3xl font-extrabold text-white">{initials}</span>
                                </div>
                                <button className="absolute bottom-0 right-0 w-9 h-9 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-600 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50 transition-all shadow-sm">
                                    <Camera className="w-4 h-4" />
                                </button>
                            </div>

                            <h2 className="text-xl font-bold text-slate-900">{user?.ad_soyad}</h2>
                            <p className="text-sm font-medium text-slate-500 mt-1">@{user?.kullanici_adi}</p>

                            <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 border border-blue-100 text-[13px] font-bold tracking-wide">
                                <Shield className="w-4 h-4" />
                                {ROL_LABELS[user?.rol] || user?.rol || 'Kullanıcı'}
                            </div>

                        </div>
                    </div>

                    {/* Right Column: Forms */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Personal Info Form */}
                        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
                            <div className="px-6 py-5 border-b border-slate-200/80 bg-slate-50/50">
                                <h3 className="text-lg font-bold text-slate-900">Kişisel Bilgiler</h3>
                                <p className="text-sm text-slate-500 mt-0.5">Sistemde görünecek profil detaylarınız.</p>
                            </div>

                            <form onSubmit={handleProfileSubmit} className="p-6 space-y-5">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                    <div className="space-y-1.5">
                                        <label className="text-[13px] font-semibold text-slate-700 ml-1">Ad Soyad</label>
                                        <div className="relative group">
                                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                                <User className="w-4.5 h-4.5" />
                                            </div>
                                            <input
                                                value={form.ad_soyad}
                                                onChange={e => setForm({ ...form, ad_soyad: e.target.value })}
                                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all pl-11 pr-4"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-[13px] font-semibold text-slate-700 ml-1">Kullanıcı Adı</label>
                                        <div className="relative group">
                                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                                <Mail className="w-4.5 h-4.5" />
                                            </div>
                                            <input
                                                value={form.kullanici_adi}
                                                onChange={e => setForm({ ...form, kullanici_adi: e.target.value })}
                                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all pl-11 pr-4"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <button
                                        type="submit"
                                        disabled={saving}
                                        className="group relative h-11 px-6 bg-slate-900 text-white text-[14px] font-bold rounded-xl whitespace-nowrap
                                            hover:bg-slate-800 transition-all shadow-md hover:shadow-lg active:scale-95 flex items-center gap-2">
                                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                        Profili Güncelle
                                    </button>
                                </div>
                            </form>
                        </div>

                        {/* Security Form */}
                        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
                            <div className="px-6 py-5 border-b border-slate-200/80 bg-slate-50/50">
                                <h3 className="text-lg font-bold text-slate-900">Güvenlik ve Şifre</h3>
                                <p className="text-sm text-slate-500 mt-0.5">Hesabınızın güvenliğini sağlamak için şifrenizi güçlü tutun.</p>
                            </div>

                            <form onSubmit={handlePasswordSubmit} className="p-6 space-y-5">
                                <div className="space-y-1.5">
                                    <label className="text-[13px] font-semibold text-slate-700 ml-1">Yeni Şifre</label>
                                    <div className="relative group">
                                        <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                            <Lock className="w-4.5 h-4.5" />
                                        </div>
                                        <input
                                            type="password"
                                            value={passwordForm.yeni_sifre}
                                            onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre: e.target.value })}
                                            placeholder="En az 6 karakter girin"
                                            className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all pl-11 pr-4"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-[13px] font-semibold text-slate-700 ml-1">Yeni Şifre (Tekrar)</label>
                                    <div className="relative group">
                                        <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                            <CheckCircle2 className="w-4.5 h-4.5" />
                                        </div>
                                        <input
                                            type="password"
                                            value={passwordForm.yeni_sifre_tekrar}
                                            onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre_tekrar: e.target.value })}
                                            placeholder="Yeni şifrenizi tekrar girin"
                                            className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all pl-11 pr-4"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <button
                                        type="submit"
                                        disabled={passwordSaving}
                                        className="group relative h-11 px-6 bg-white border-2 border-slate-200 text-slate-700 text-[14px] font-bold rounded-xl whitespace-nowrap
                                            hover:border-indigo-600 hover:text-indigo-600 transition-all shadow-sm active:scale-95 flex items-center gap-2">
                                        {passwordSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                                        Şifreyi Değiştir
                                    </button>
                                </div>
                            </form>
                        </div>

                    </div>
                </div>
            </div>
        </>
    );
}
