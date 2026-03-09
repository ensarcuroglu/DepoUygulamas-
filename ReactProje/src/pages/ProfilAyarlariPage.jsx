import React, { useState } from 'react';
import { User, Mail, Lock, Camera, Shield, CheckCircle2, Loader2, Save, UserCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { updateKullanici } from '../services/api';
import { hataMetni } from '../utils/hata';

const ROL_LABELS = {
    admin: 'Sistem Yöneticisi',
    depocu: 'Depo Sorumlusu',
    goruntuleyen: 'Görüntüleyici',
};

export default function ProfilAyarlariPage() {
    const { user, login } = useAuth();

    const [form, setForm] = useState({
        ad_soyad: user?.ad_soyad || '',
        kullanici_adi: user?.kullanici_adi || '',
    });

    const [passwordForm, setPasswordForm] = useState({
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
            toast.error('Lütfen ad soyad ve kullanıcı adı alanlarını doldurun.');
            return;
        }

        setSaving(true);
        try {
            await updateKullanici(user.id, form);
            toast.success('Profil bilgileriniz güncellendi. Yeniden giriş yapmanız gerekebilir.', { icon: '👏' });
        } catch (err) {
            toast.error(hataMetni(err, 'Profil güncellenemedi'));
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        if (passwordForm.yeni_sifre !== passwordForm.yeni_sifre_tekrar) {
            toast.error('Girdiğiniz yeni şifreler eşleşmiyor.');
            return;
        }
        if (passwordForm.yeni_sifre.length < 6) {
            toast.error('Şifreniz en az 6 karakter olmalıdır.');
            return;
        }

        setPasswordSaving(true);
        try {
            await updateKullanici(user.id, { sifre: passwordForm.yeni_sifre });
            toast.success('Şifreniz başarıyla değiştirildi.', { icon: '🔒' });
            setPasswordForm({ yeni_sifre: '', yeni_sifre_tekrar: '' });
        } catch (err) {
            toast.error(hataMetni(err, 'Şifre güncellenemedi'));
        } finally {
            setPasswordSaving(false);
        }
    };

    const labelClass = "text-[12px] font-extrabold text-slate-500 mb-2.5 block tracking-widest uppercase ml-1";
    const inputClass = `w-full h-14 pl-12 pr-5 text-[15px] font-bold rounded-2xl border-2 border-slate-100 bg-slate-50 
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10 
    focus:border-blue-500 focus:bg-white transition-all duration-300 shadow-sm`;

    return (
        <div className="max-w-[1000px] mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-24 sm:pb-8 space-y-6 md:space-y-8 animate-fade-in">

            {/* Header Section */}
            <div className="flex items-center gap-4 mb-4 sm:mb-8">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/30 flex items-center justify-center">
                    <UserCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="text-[24px] font-black tracking-tight text-slate-900 leading-none mb-1">Hesabım</h1>
                    <p className="text-[13px] font-medium text-slate-500">Kişisel bilgilerinizi ve güvenliğinizi yönetin.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">

                {/* Left Column: Profile Card */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-[32px] border border-slate-100 p-6 sm:p-8 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col items-center text-center relative overflow-hidden group">

                        {/* Decorative Background Blob */}
                        <div className="absolute -left-10 -top-10 w-40 h-40 rounded-full bg-gradient-to-br from-indigo-50 to-purple-50 opacity-40 group-hover:scale-150 transition-transform duration-700 pointer-events-none" />

                        <div className="relative mb-5 z-10">
                            <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/20 border-4 border-white transform group-hover:scale-105 transition-transform duration-300">
                                <span className="text-[36px] font-black text-white">{initials}</span>
                            </div>
                            <button className="absolute bottom-1 right-1 w-10 h-10 bg-white border-2 border-slate-100 rounded-full flex items-center justify-center text-slate-500 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50 transition-all shadow-sm active:scale-90">
                                <Camera className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="relative z-10">
                            <h2 className="text-[20px] font-black text-slate-900">{user?.ad_soyad}</h2>
                            <p className="text-[14px] font-bold text-slate-400 mt-0.5">@{user?.kullanici_adi}</p>

                            <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 border border-blue-100">
                                <Shield className="w-4 h-4 text-blue-500" strokeWidth={2.5} />
                                <span className="text-[13px] font-extrabold text-blue-700 uppercase tracking-wide">
                                    {ROL_LABELS[user?.rol] || user?.rol || 'Depo Görevlisi'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Forms */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Personal Info Form */}
                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-xl transition-shadow duration-300">
                        <div className="px-6 sm:px-8 py-5 sm:py-6 border-b border-slate-100 bg-slate-50/50">
                            <h3 className="text-[18px] font-black text-slate-900">Kişisel Bilgiler</h3>
                            <p className="text-[13px] font-medium text-slate-500 mt-1">Sistemde görünecek profil detaylarınız.</p>
                        </div>

                        <form onSubmit={handleProfileSubmit} className="p-6 sm:p-8 space-y-6 bg-white relative z-10">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div>
                                    <label className={labelClass}>Ad Soyad</label>
                                    <div className="relative group/input">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within/input:text-blue-500 transition-colors">
                                            <User className="w-5 h-5" />
                                        </div>
                                        <input
                                            value={form.ad_soyad}
                                            onChange={e => setForm({ ...form, ad_soyad: e.target.value })}
                                            className={inputClass}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>Kullanıcı Adı</label>
                                    <div className="relative group/input">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within/input:text-blue-500 transition-colors">
                                            <Mail className="w-5 h-5" />
                                        </div>
                                        <input
                                            value={form.kullanici_adi}
                                            onChange={e => setForm({ ...form, kullanici_adi: e.target.value })}
                                            className={inputClass}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="pt-2 sm:pt-4 flex sm:justify-end">
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="w-full sm:w-auto h-14 px-8 bg-slate-900 text-white text-[15px] font-bold rounded-2xl
                                        hover:bg-slate-800 transition-all shadow-[0_8px_20px_-6px_rgba(15,23,42,0.4)] active:scale-95 flex items-center justify-center gap-2">
                                    {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" strokeWidth={2.5} />}
                                    Profili Güncelle
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Security Form */}
                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-sm relative overflow-hidden group hover:shadow-xl transition-shadow duration-300">
                        <div className="px-6 sm:px-8 py-5 sm:py-6 border-b border-slate-100 bg-slate-50/50">
                            <h3 className="text-[18px] font-black text-slate-900">Güvenlik ve Şifre</h3>
                            <p className="text-[13px] font-medium text-slate-500 mt-1">Hesap giriş güvenliğinizi koruyun.</p>
                        </div>

                        <form onSubmit={handlePasswordSubmit} className="p-6 sm:p-8 space-y-6 bg-white relative z-10">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div>
                                    <label className={labelClass}>Yeni Şifreniz</label>
                                    <div className="relative group/input">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within/input:text-indigo-500 transition-colors">
                                            <Lock className="w-5 h-5" />
                                        </div>
                                        <input
                                            type="password"
                                            value={passwordForm.yeni_sifre}
                                            onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre: e.target.value })}
                                            placeholder="En az 6 karakter"
                                            className={inputClass}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>Şifre (Tekrar)</label>
                                    <div className="relative group/input">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within/input:text-indigo-500 transition-colors">
                                            <CheckCircle2 className="w-5 h-5" />
                                        </div>
                                        <input
                                            type="password"
                                            value={passwordForm.yeni_sifre_tekrar}
                                            onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre_tekrar: e.target.value })}
                                            placeholder="Tekrar girin"
                                            className={inputClass}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="pt-2 sm:pt-4 flex sm:justify-end">
                                <button
                                    type="submit"
                                    disabled={passwordSaving}
                                    className="w-full sm:w-auto h-14 px-8 bg-white border-2 border-slate-100 text-slate-700 text-[15px] font-bold rounded-2xl
                                        hover:border-indigo-600 hover:text-indigo-600 transition-all shadow-sm active:scale-95 flex items-center justify-center gap-2">
                                    {passwordSaving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Shield className="w-5 h-5" strokeWidth={2.5} />}
                                    Şifreyi Değiştir
                                </button>
                            </div>
                        </form>
                    </div>

                </div>
            </div>
        </div>
    );
}
