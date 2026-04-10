import { useState, useEffect } from 'react';
import { Settings, Database, Shield, Palette, AlertCircle, Lock, Sun, Moon, Monitor, Check } from 'lucide-react';
import api from '../services/api';
import { useTheme, TEMALAR, MODLAR } from '../contexts/ThemeContext';

export default function AyarlarPage() {
    const [authConfig, setAuthConfig] = useState(null);
    const { tema, mod, setTema, setMod } = useTheme();

    useEffect(() => {
        api.get('/auth/config')
            .then(res => setAuthConfig(res.data))
            .catch(() => setAuthConfig(null));
    }, []);

    const formatTokenSuresi = (dakika) => {
        if (!dakika) return 'Yükleniyor...';
        if (dakika >= 60) {
            const saat = Math.floor(dakika / 60);
            const kalan = dakika % 60;
            return kalan > 0 ? `${saat} saat ${kalan} dk` : `${saat} saat`;
        }
        return `${dakika} dakika`;
    };

    const modIkonu = { sun: Sun, moon: Moon, monitor: Monitor };

    const statikAyarlar = [
        {
            icon: Database,
            title: 'Veritabanı',
            desc: 'Sistem veritabanı ve yedekleme yapılandırması',
            items: [
                { label: 'Veritabanı Tipi', value: 'MySQL', isEditable: false },
                { label: 'Toplam Tablo', value: '17', isEditable: false },
            ],
        },
        {
            icon: Shield,
            title: 'Güvenlik',
            desc: 'Kimlik doğrulama, yetkilendirme ve token ayarları',
            items: [
                { label: 'Auth Yöntemi', value: authConfig ? `JWT (${authConfig.algorithm})` : 'Yükleniyor...', isEditable: false },
                { label: 'Şifreleme Algoritması', value: authConfig?.password_hash || 'Yükleniyor...', isEditable: false },
                { label: 'Token Geçerlilik Süresi', value: formatTokenSuresi(authConfig?.access_token_expire_minutes), isEditable: false },
                { label: 'Refresh Token Süresi', value: authConfig ? `${authConfig.refresh_token_expire_days} gün` : 'Yükleniyor...', isEditable: false },
            ],
        },
    ];

    return (
        <div className="min-h-screen pb-12">
            <div className="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-8">

                {/* Sayfa Başlığı */}
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300 shrink-0">
                        <Settings className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                            Sistem Tercihleri
                        </h1>
                        <p className="mt-1 text-sm sm:text-base text-slate-500 dark:text-slate-400">
                            Depo yönetim sisteminin altyapı, güvenlik ve arayüz davranışlarını yönetin.
                        </p>
                    </div>
                </div>

                {/* ── Arayüz ve Görünüm (İnteraktif) ── */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl sm:rounded-3xl border border-slate-200/80 dark:border-slate-700/60 shadow-sm overflow-hidden">

                    {/* Bölüm Başlığı */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:p-6 border-b border-slate-100 dark:border-slate-800">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center shrink-0">
                            <Palette className="w-6 h-6 sm:w-7 sm:h-7 text-indigo-600 dark:text-indigo-400" />
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
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Arayüzün renk kimliğini seçin</p>
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                {TEMALAR.map((t) => {
                                    const aktif = tema === t.id;
                                    return (
                                        <button
                                            key={t.id}
                                            onClick={() => setTema(t.id)}
                                            className={`relative flex flex-col items-start p-4 rounded-2xl border-2 transition-all duration-200 text-left group
                                                ${aktif
                                                    ? 'border-[var(--color-primary-600)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-950)] shadow-md'
                                                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm'
                                                }`}
                                        >
                                            {/* Renk swatch */}
                                            <div className="flex items-center gap-1.5 mb-3">
                                                <div
                                                    className="w-7 h-7 rounded-lg shadow-sm"
                                                    style={{ backgroundColor: t.renkler.primary }}
                                                />
                                                <div
                                                    className="w-4 h-4 rounded-md opacity-70"
                                                    style={{ backgroundColor: t.renkler.secondary }}
                                                />
                                                <div
                                                    className="w-3 h-3 rounded-md opacity-60"
                                                    style={{ backgroundColor: t.renkler.accent }}
                                                />
                                            </div>

                                            <p className={`text-[13px] font-bold leading-tight ${aktif ? 'text-[var(--color-primary-700)] dark:text-[var(--color-primary-300)]' : 'text-slate-700 dark:text-slate-300'}`}>
                                                {t.ad}
                                            </p>
                                            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 font-medium">{t.aciklama}</p>

                                            {/* Aktif checkmark */}
                                            {aktif && (
                                                <div className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full flex items-center justify-center shadow-sm"
                                                    style={{ backgroundColor: t.renkler.primary }}
                                                >
                                                    <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                                </div>
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Mod Seçici */}
                        <div>
                            <div className="mb-4">
                                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Görüntüleme Modu</h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Açık, koyu veya sistem tercihini takip eden mod</p>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                                {MODLAR.map((m) => {
                                    const aktif = mod === m.id;
                                    const Icon = modIkonu[m.icon];
                                    return (
                                        <button
                                            key={m.id}
                                            onClick={() => setMod(m.id)}
                                            className={`flex-1 flex items-center gap-3 px-4 py-3.5 rounded-xl border-2 transition-all duration-200 text-left
                                                ${aktif
                                                    ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-950)] shadow-sm'
                                                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600'
                                                }`}
                                        >
                                            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                                                aktif
                                                    ? 'bg-[var(--color-primary-500)] text-white shadow-sm'
                                                    : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                                            }`}>
                                                <Icon className="w-4.5 h-4.5" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className={`text-[13px] font-bold leading-tight truncate ${aktif ? 'text-[var(--color-primary-700)] dark:text-[var(--color-primary-300)]' : 'text-slate-700 dark:text-slate-300'}`}>
                                                    {m.ad}
                                                </p>
                                                {m.id === 'sistem' && (
                                                    <p className="text-[11px] text-slate-400 dark:text-slate-500 font-medium mt-0.5 truncate">OS tercihini takip et</p>
                                                )}
                                            </div>
                                            {aktif && (
                                                <Check className="w-4 h-4 ml-auto shrink-0 text-[var(--color-primary-500)]" strokeWidth={2.5} />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Aktif kombinasyon özeti */}
                        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/40">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
                            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                                Aktif: <span className="text-slate-700 dark:text-slate-200">{TEMALAR.find(t => t.id === tema)?.ad}</span>
                                {' · '}
                                <span className="text-slate-700 dark:text-slate-200">{MODLAR.find(m => m.id === mod)?.ad}</span>
                            </p>
                        </div>
                    </div>
                </div>

                {/* ── Statik Ayar Grupları ── */}
                <div className="space-y-6 sm:space-y-8">
                    {statikAyarlar.map((grup, i) => {
                        const Icon = grup.icon;
                        return (
                            <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl sm:rounded-3xl border border-slate-200/80 dark:border-slate-700/60 shadow-sm overflow-hidden">
                                <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:p-6 border-b border-slate-100 dark:border-slate-800">
                                    <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center shrink-0">
                                        <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-indigo-600 dark:text-indigo-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{grup.title}</h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{grup.desc}</p>
                                    </div>
                                </div>
                                <div className="divide-y divide-slate-50 dark:divide-slate-800 bg-slate-50/30 dark:bg-slate-800/20">
                                    {grup.items.map((item, j) => (
                                        <div key={j} className="flex items-center justify-between gap-4 p-4 sm:px-6 sm:py-5 opacity-90">
                                            <span className="text-sm sm:text-base font-semibold text-slate-500 dark:text-slate-400 truncate">{item.label}</span>
                                            <div className="flex items-center gap-2 shrink-0">
                                                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-medium bg-slate-100 dark:bg-slate-800 border-transparent text-slate-500 dark:text-slate-400">
                                                    <Lock className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                                                    {item.value}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Bilgilendirme Banner'ı */}
                <div className="relative overflow-hidden bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-500/5 dark:to-blue-500/5 border border-indigo-100 dark:border-indigo-500/20 rounded-2xl sm:rounded-3xl p-5 sm:p-6 shadow-sm">
                    <div className="absolute -top-6 -right-6 p-8 opacity-[0.03] pointer-events-none">
                        <Settings className="w-48 h-48 animate-[spin_20s_linear_infinite]" />
                    </div>
                    <div className="relative z-10 flex flex-col sm:flex-row gap-4 sm:gap-5 items-start">
                        <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-500/10 flex items-center justify-center shrink-0 shadow-inner">
                            <AlertCircle className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div className="flex-1">
                            <h4 className="text-base font-bold text-indigo-900 dark:text-indigo-300 flex items-center gap-2.5 mb-1.5">
                                Geliştirme Aşamasında
                                <span className="flex h-2.5 w-2.5 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                                </span>
                            </h4>
                            <p className="text-sm text-indigo-800/80 dark:text-indigo-300/70 leading-relaxed max-w-3xl">
                                Bu ayarlar sayfası Faz 3 ve Faz 4 güncellemelerinde tam etkileşimli hale gelecektir.
                                Gelecek sürümlerde <strong className="font-semibold text-indigo-900 dark:text-indigo-200">JWT kimlik doğrulama</strong>,
                                gelişmiş kullanıcı yönetimi ve rol tabanlı yetkilendirme (RBAC) panelleri buraya entegre edilecektir.
                            </p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
