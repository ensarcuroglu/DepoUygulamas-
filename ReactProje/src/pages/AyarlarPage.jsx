import { useState, useEffect, useMemo } from 'react';
import { Settings, Database, Shield, Palette, AlertCircle, Lock, Sun, Moon, Monitor, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { useTheme, TEMALAR, MODLAR } from '../contexts/ThemeContext';

// Yeniden kullanılabilir Skeleton bileşeni (Yüklenme durumu için)
const Skeleton = ({ className }) => (
    <div className={`animate-pulse bg-slate-200/80 dark:bg-slate-700/50 rounded-md ${className}`} />
);

// Sayfa geneli animasyon varyantları
const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.1 }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 400, damping: 30 } }
};

export default function AyarlarPage() {
    const [authConfig, setAuthConfig] = useState(null);
    const { tema, mod, setTema, setMod } = useTheme();

    useEffect(() => {
        api.get('/auth/config')
            .then(res => setAuthConfig(res.data))
            .catch(() => setAuthConfig(null));
    }, []);

    const formatTokenSuresi = (dakika) => {
        if (!dakika) return null;
        if (dakika >= 60) {
            const saat = Math.floor(dakika / 60);
            const kalan = dakika % 60;
            return kalan > 0 ? `${saat} saat ${kalan} dk` : `${saat} saat`;
        }
        return `${dakika} dakika`;
    };

    const modIkonu = { sun: Sun, moon: Moon, monitor: Monitor };

    // Performans: authConfig değişmediği sürece bu diziyi yeniden oluşturma
    const statikAyarlar = useMemo(() => [
        {
            icon: Database,
            title: 'Veritabanı',
            desc: 'Sistem veritabanı ve yedekleme yapılandırması',
            items: [
                { label: 'Veritabanı Tipi', value: 'MySQL' },
                { label: 'Toplam Tablo', value: '17' },
            ],
        },
        {
            icon: Shield,
            title: 'Güvenlik',
            desc: 'Kimlik doğrulama, yetkilendirme ve token ayarları',
            items: [
                { 
                    label: 'Auth Yöntemi', 
                    value: authConfig ? `JWT (${authConfig.algorithm})` : <Skeleton className="h-5 w-24" /> 
                },
                { 
                    label: 'Şifreleme Algoritması', 
                    value: authConfig?.password_hash || <Skeleton className="h-5 w-20" /> 
                },
                { 
                    label: 'Token Geçerlilik Süresi', 
                    value: authConfig ? formatTokenSuresi(authConfig.access_token_expire_minutes) : <Skeleton className="h-5 w-28" /> 
                },
                { 
                    label: 'Refresh Token Süresi', 
                    value: authConfig ? `${authConfig.refresh_token_expire_days} gün` : <Skeleton className="h-5 w-16" /> 
                },
            ],
        },
    ], [authConfig]);

    const aktifTemaData = useMemo(() => TEMALAR.find(t => t.id === tema), [tema]);
    const aktifModData = useMemo(() => MODLAR.find(m => m.id === mod), [mod]);

    return (
        <div className="min-h-screen pb-12 overflow-hidden selection:bg-[var(--color-primary-500)] selection:text-white">
            <motion.div 
                className="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-8"
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                {/* Sayfa Başlığı */}
                <motion.div variants={itemVariants} className="flex items-center gap-4 sm:gap-5">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/80 dark:border-slate-700/60 flex items-center justify-center text-slate-700 dark:text-slate-300 shrink-0">
                        <Settings className="w-6 h-6 sm:w-7 sm:h-7" strokeWidth={1.5} />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                            Sistem Tercihleri
                        </h1>
                        <p className="mt-1 text-sm sm:text-base text-slate-500 dark:text-slate-400">
                            Depo yönetim sisteminin altyapı, güvenlik ve arayüz davranışlarını yönetin.
                        </p>
                    </div>
                </motion.div>

                {/* ── Arayüz ve Görünüm (İnteraktif) ── */}
                <motion.div variants={itemVariants} className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-3xl border border-slate-200/60 dark:border-slate-700/50 shadow-sm overflow-hidden transition-colors duration-300">
                    {/* Bölüm Başlığı */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:p-6 border-b border-slate-100 dark:border-slate-800/80">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center shrink-0">
                            <Palette className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Arayüz ve Görünüm</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Renk teması ve görüntüleme modunu kişiselleştirin</p>
                        </div>
                    </div>

                    <div className="p-5 sm:p-6 space-y-8">
                        {/* Tema Seçici */}
                        <div>
                            <div className="mb-4">
                                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Renk Teması</h4>
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                                {TEMALAR.map((t) => {
                                    const aktif = tema === t.id;
                                    return (
                                        <motion.button
                                            key={t.id}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.97 }}
                                            onClick={() => setTema(t.id)}
                                            className={`relative flex flex-col items-start p-4 rounded-2xl border-2 transition-all duration-200 text-left group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900
                                                ${aktif
                                                    ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 shadow-[0_4px_20px_-4px_var(--color-primary-500)]'
                                                    : 'border-slate-200/80 dark:border-slate-700/60 bg-white dark:bg-slate-800/50 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm'
                                                }`}
                                        >
                                            {/* Renk swatch */}
                                            <div className="flex items-center gap-1.5 mb-3">
                                                <div className="w-7 h-7 rounded-full shadow-inner" style={{ backgroundColor: t.renkler.primary }} />
                                                <div className="w-4 h-4 rounded-full opacity-80 shadow-inner" style={{ backgroundColor: t.renkler.secondary }} />
                                            </div>

                                            <p className={`text-[13px] font-bold leading-tight transition-colors ${aktif ? 'text-[var(--color-primary-700)] dark:text-[var(--color-primary-300)]' : 'text-slate-700 dark:text-slate-300'}`}>
                                                {t.ad}
                                            </p>
                                            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 font-medium">{t.aciklama}</p>

                                            {/* Animasyonlu Aktif Checkmark */}
                                            <AnimatePresence>
                                                {aktif && (
                                                    <motion.div 
                                                        initial={{ scale: 0, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        exit={{ scale: 0, opacity: 0 }}
                                                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                                        className="absolute top-3 right-3 w-5 h-5 rounded-full flex items-center justify-center shadow-sm"
                                                        style={{ backgroundColor: t.renkler.primary }}
                                                    >
                                                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Mod Seçici */}
                        <div>
                            <div className="mb-4">
                                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Görüntüleme Modu</h4>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-3">
                                {MODLAR.map((m) => {
                                    const aktif = mod === m.id;
                                    const Icon = modIkonu[m.icon];
                                    return (
                                        <motion.button
                                            key={m.id}
                                            whileHover={{ scale: 1.01 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => setMod(m.id)}
                                            className={`flex-1 flex items-center gap-3.5 px-4 py-4 rounded-2xl border-2 transition-all duration-200 text-left min-h-[64px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900
                                                ${aktif
                                                    ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 shadow-[0_4px_15px_-3px_var(--color-primary-500)]'
                                                    : 'border-slate-200/80 dark:border-slate-700/60 bg-white dark:bg-slate-800/50 hover:border-slate-300 dark:hover:border-slate-600'
                                                }`}
                                        >
                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 ${
                                                aktif
                                                    ? 'bg-[var(--color-primary-500)] text-white shadow-md scale-105'
                                                    : 'bg-slate-100 dark:bg-slate-700/80 text-slate-500 dark:text-slate-400'
                                            }`}>
                                                <Icon className="w-5 h-5" strokeWidth={aktif ? 2.5 : 2} />
                                            </div>
                                            <div className="min-w-0">
                                                <p className={`text-sm font-bold leading-tight truncate transition-colors ${aktif ? 'text-[var(--color-primary-700)] dark:text-[var(--color-primary-300)]' : 'text-slate-700 dark:text-slate-300'}`}>
                                                    {m.ad}
                                                </p>
                                                {m.id === 'sistem' && (
                                                    <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mt-0.5 truncate">OS tercihini takip et</p>
                                                )}
                                            </div>
                                        </motion.button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Aktif kombinasyon özeti */}
                        <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-700/30">
                            <span className="relative flex h-2.5 w-2.5 shrink-0">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary-400)] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[var(--color-primary-500)]"></span>
                            </span>
                            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex flex-wrap gap-1">
                                Aktif Profil: 
                                <span className="text-slate-800 dark:text-slate-200">{aktifTemaData?.ad}</span>
                                <span className="text-slate-400 dark:text-slate-500 mx-0.5">/</span>
                                <span className="text-slate-800 dark:text-slate-200">{aktifModData?.ad}</span>
                            </p>
                        </div>
                    </div>
                </motion.div>

                {/* ── Statik Ayar Grupları ── */}
                <div className="space-y-6 sm:space-y-8">
                    {statikAyarlar.map((grup, i) => {
                        const Icon = grup.icon;
                        return (
                            <motion.div key={i} variants={itemVariants} className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-3xl border border-slate-200/60 dark:border-slate-700/50 shadow-sm overflow-hidden">
                                <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:p-6 border-b border-slate-100 dark:border-slate-800/80">
                                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center shrink-0">
                                        <Icon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{grup.title}</h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{grup.desc}</p>
                                    </div>
                                </div>
                                <div className="divide-y divide-slate-100 dark:divide-slate-800/50 bg-slate-50/50 dark:bg-slate-800/20">
                                    {grup.items.map((item, j) => (
                                        <div key={j} className="flex items-center justify-between gap-4 p-4 sm:px-6 sm:py-4 hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors">
                                            <span className="text-sm sm:text-base font-medium text-slate-600 dark:text-slate-300 truncate">{item.label}</span>
                                            <div className="flex items-center gap-2 shrink-0">
                                                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-slate-600 dark:text-slate-300">
                                                    <Lock className="w-3.5 h-3.5 text-slate-400" strokeWidth={2.5} />
                                                    {item.value}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Bilgilendirme Banner'ı */}
                <motion.div variants={itemVariants} className="relative overflow-hidden bg-gradient-to-br from-indigo-50 to-blue-50/50 dark:from-indigo-500/10 dark:to-blue-500/5 border border-indigo-100/80 dark:border-indigo-500/20 rounded-3xl p-6 sm:p-8 shadow-sm">
                    <div className="absolute -top-10 -right-10 p-8 opacity-[0.02] dark:opacity-[0.04] pointer-events-none">
                        <Settings className="w-64 h-64 animate-[spin_30s_linear_infinite]" />
                    </div>
                    <div className="relative z-10 flex flex-col sm:flex-row gap-5 sm:gap-6 items-start">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-100/80 dark:bg-indigo-500/20 flex items-center justify-center shrink-0 shadow-inner">
                            <AlertCircle className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div className="flex-1">
                            <h4 className="text-base font-bold text-indigo-900 dark:text-indigo-200 flex items-center gap-2.5 mb-2">
                                Geliştirme Aşamasında
                            </h4>
                            <p className="text-sm sm:text-base text-indigo-800/80 dark:text-indigo-300/80 leading-relaxed max-w-3xl">
                                Bu ayarlar sayfası <strong className="font-semibold text-indigo-900 dark:text-indigo-100">Faz 3 ve Faz 4</strong> güncellemelerinde tam etkileşimli hale gelecektir. Gelecek sürümlerde JWT kimlik doğrulama, gelişmiş kullanıcı yönetimi ve rol tabanlı yetkilendirme (RBAC) panelleri buraya entegre edilecektir.
                            </p>
                        </div>
                    </div>
                </motion.div>

            </motion.div>
        </div>
    );
}