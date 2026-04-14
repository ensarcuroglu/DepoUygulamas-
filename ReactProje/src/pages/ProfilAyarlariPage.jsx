import React, { useState } from 'react';
import { User, Mail, Lock, Camera, Shield, CheckCircle2, Loader2, Save, UserCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { updateKullanici } from '../services/api';
import { hataMetni } from '../utils/hata';
import { motion } from 'framer-motion';

const ROL_LABELS = {
    admin: 'Sistem Yöneticisi',
    depocu: 'Depo Sorumlusu',
    goruntuleyen: 'Görüntüleyici',
};

export default function ProfilAyarlariPage() {
    const { user } = useAuth();

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

    // Optimize edilmiş input stili (Erişilebilirlik ve modern odaklanma durumları)
    const labelClass = "text-xs font-semibold text-slate-500 mb-2 block tracking-wide";
    const inputClass = `w-full h-12 pl-11 pr-4 text-sm font-medium rounded-xl border border-slate-200 bg-white/50 
    text-slate-900 placeholder-slate-400 transition-all duration-200 shadow-sm
    focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 
    hover:border-slate-300 disabled:opacity-60 disabled:bg-slate-50`;

    // Animasyon varyantları
    const containerVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.4, staggerChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 15 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <div className="min-h-screen bg-slate-50/50 pb-24 sm:pb-12">
            <motion.div 
                className="max-w-5xl mx-auto px-4 sm:px-6 md:px-8 pt-8 sm:pt-12"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* Header Section */}
                <motion.div variants={itemVariants} className="flex items-center gap-4 mb-8 sm:mb-12">
                    <div className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-slate-200 flex items-center justify-center">
                        <UserCircle className="w-6 h-6 text-indigo-600" strokeWidth={2} />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-1">Hesap Ayarları</h1>
                        <p className="text-sm font-medium text-slate-500">Kişisel bilgilerinizi ve güvenliğinizi buradan yönetin.</p>
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

                    {/* Left Column: Profile Card (Sticky on Desktop) */}
                    <motion.div variants={itemVariants} className="lg:col-span-4 lg:sticky lg:top-8">
                        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm flex flex-col items-center text-center relative overflow-hidden">
                            {/* Dekoratif Arka Plan */}
                            <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-indigo-50/80 to-transparent" />

                            <div className="relative mb-6 z-10 group mt-4">
                                <div className="w-28 h-28 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 border-4 border-white transform transition-transform duration-300 group-hover:scale-105">
                                    <span className="text-3xl font-bold text-white tracking-tight">{initials}</span>
                                </div>
                                <motion.button 
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    className="absolute bottom-0 right-0 w-9 h-9 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-600 hover:text-indigo-600 hover:border-indigo-200 shadow-sm transition-colors"
                                    aria-label="Profil fotoğrafını değiştir"
                                >
                                    <Camera className="w-4 h-4" />
                                </motion.button>
                            </div>

                            <div className="relative z-10 w-full">
                                <h2 className="text-xl font-bold text-slate-900 truncate px-2">{user?.ad_soyad}</h2>
                                <p className="text-sm font-medium text-slate-500 mt-1 truncate px-2">@{user?.kullanici_adi}</p>

                                <div className="mt-6 flex justify-center">
                                    <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200">
                                        <Shield className="w-3.5 h-3.5 text-slate-600" strokeWidth={2.5} />
                                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                                            {ROL_LABELS[user?.rol] || user?.rol || 'Kullanıcı'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Right Column: Forms */}
                    <div className="lg:col-span-8 space-y-6">

                        {/* Personal Info Form */}
                        <motion.div variants={itemVariants} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                            <div className="px-6 sm:px-8 py-5 border-b border-slate-100 bg-white">
                                <h3 className="text-base font-bold text-slate-900">Kişisel Bilgiler</h3>
                                <p className="text-sm text-slate-500 mt-0.5">Sistemde görünecek profil detaylarınız.</p>
                            </div>

                            <form onSubmit={handleProfileSubmit} className="p-6 sm:p-8">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
                                    <div>
                                        <label className={labelClass} htmlFor="ad_soyad">Ad Soyad</label>
                                        <div className="relative group">
                                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-focus-within:text-indigo-500 transition-colors">
                                                <User className="w-4 h-4" />
                                            </div>
                                            <input
                                                id="ad_soyad"
                                                value={form.ad_soyad}
                                                onChange={e => setForm({ ...form, ad_soyad: e.target.value })}
                                                className={inputClass}
                                                disabled={saving}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className={labelClass} htmlFor="kullanici_adi">Kullanıcı Adı</label>
                                        <div className="relative group">
                                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-focus-within:text-indigo-500 transition-colors">
                                                <Mail className="w-4 h-4" />
                                            </div>
                                            <input
                                                id="kullanici_adi"
                                                value={form.kullanici_adi}
                                                onChange={e => setForm({ ...form, kullanici_adi: e.target.value })}
                                                className={inputClass}
                                                disabled={saving}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex sm:justify-end border-t border-slate-100 pt-6">
                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        type="submit"
                                        disabled={saving}
                                        className="w-full sm:w-auto h-11 px-6 bg-slate-900 text-white text-sm font-semibold rounded-xl
                                        hover:bg-slate-800 disabled:bg-slate-800/70 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 flex items-center justify-center gap-2"
                                    >
                                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                        Değişiklikleri Kaydet
                                    </motion.button>
                                </div>
                            </form>
                        </motion.div>

                        {/* Security Form */}
                        <motion.div variants={itemVariants} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                            <div className="px-6 sm:px-8 py-5 border-b border-slate-100 bg-white">
                                <h3 className="text-base font-bold text-slate-900">Güvenlik</h3>
                                <p className="text-sm text-slate-500 mt-0.5">Hesap erişim şifrenizi güncelleyin.</p>
                            </div>

                            <form onSubmit={handlePasswordSubmit} className="p-6 sm:p-8">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
                                    <div>
                                        <label className={labelClass} htmlFor="yeni_sifre">Yeni Şifre</label>
                                        <div className="relative group">
                                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-focus-within:text-indigo-500 transition-colors">
                                                <Lock className="w-4 h-4" />
                                            </div>
                                            <input
                                                id="yeni_sifre"
                                                type="password"
                                                value={passwordForm.yeni_sifre}
                                                onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre: e.target.value })}
                                                placeholder="En az 6 karakter"
                                                className={inputClass}
                                                disabled={passwordSaving}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className={labelClass} htmlFor="yeni_sifre_tekrar">Yeni Şifre (Tekrar)</label>
                                        <div className="relative group">
                                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none group-focus-within:text-indigo-500 transition-colors">
                                                <CheckCircle2 className="w-4 h-4" />
                                            </div>
                                            <input
                                                id="yeni_sifre_tekrar"
                                                type="password"
                                                value={passwordForm.yeni_sifre_tekrar}
                                                onChange={e => setPasswordForm({ ...passwordForm, yeni_sifre_tekrar: e.target.value })}
                                                placeholder="Şifreyi doğrulayın"
                                                className={inputClass}
                                                disabled={passwordSaving}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex sm:justify-end border-t border-slate-100 pt-6">
                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        type="submit"
                                        disabled={passwordSaving}
                                        className="w-full sm:w-auto h-11 px-6 bg-white border border-slate-200 text-slate-700 text-sm font-semibold rounded-xl
                                        hover:bg-slate-50 hover:text-indigo-600 hover:border-indigo-200 disabled:opacity-50 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 flex items-center justify-center gap-2"
                                    >
                                        {passwordSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                                        Şifreyi Güncelle
                                    </motion.button>
                                </div>
                            </form>
                        </motion.div>

                    </div>
                </div>
            </motion.div>
        </div>
    );
}