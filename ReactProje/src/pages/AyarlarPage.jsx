import { useState, useEffect } from 'react';
import { Settings, Database, Shield, Palette, ChevronRight, AlertCircle, Lock } from 'lucide-react';
import api from '../services/api';

export default function AyarlarPage() {
    const [authConfig, setAuthConfig] = useState(null);

    useEffect(() => {
        api.get('/auth/config')
            .then(res => setAuthConfig(res.data))
            .catch(() => setAuthConfig(null));
    }, []);

    // Token süresini okunabilir formata çevir
    const formatTokenSuresi = (dakika) => {
        if (!dakika) return 'Yükleniyor...';
        if (dakika >= 60) {
            const saat = Math.floor(dakika / 60);
            const kalan = dakika % 60;
            return kalan > 0 ? `${saat} saat ${kalan} dk` : `${saat} saat`;
        }
        return `${dakika} dakika`;
    };

    const ayarGruplari = [
        {
            icon: Database,
            title: 'Veritabanı',
            desc: 'Sistem veritabanı ve yedekleme yapılandırması',
            items: [
                { label: 'Veritabanı Tipi', value: 'SQLite', isEditable: false },
                { label: 'Dosya Yolu', value: './depo.db', isEditable: true },
                { label: 'Toplam Tablo', value: '5', isEditable: false },
            ]
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
            ]
        },
        {
            icon: Palette,
            title: 'Arayüz ve Görünüm',
            desc: 'Kullanıcı paneli tasarım ve dil tercihleri',
            items: [
                { label: 'Aktif Tema', value: 'Kurumsal Açık', isEditable: true },
                { label: 'Sistem Fontu', value: 'Inter', isEditable: true },
                { label: 'Varsayılan Dil', value: 'Türkçe', isEditable: true },
            ]
        },
    ];

    return (
        <div className="min-h-screen bg-slate-50 pb-12">
            <div className="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-8">
                
                {/* Sayfa Başlığı */}
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white rounded-xl shadow-sm border border-slate-200 flex items-center justify-center text-slate-700 shrink-0">
                        <Settings className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
                            Sistem Tercihleri
                        </h1>
                        <p className="mt-1 text-sm sm:text-base text-slate-500">
                            Depo yönetim sisteminin altyapı, güvenlik ve arayüz davranışlarını yönetin.
                        </p>
                    </div>
                </div>

                {/* Ayar Grupları Listesi */}
                <div className="space-y-6 sm:space-y-8">
                    {ayarGruplari.map((grup, i) => {
                        const Icon = grup.icon;
                        return (
                            <div 
                                key={i} 
                                className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden"
                            >
                                {/* Grup Başlığı */}
                                <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 sm:p-6 border-b border-slate-100 bg-white">
                                    <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-indigo-50 flex items-center justify-center shrink-0">
                                        <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-indigo-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900">{grup.title}</h3>
                                        <p className="text-sm text-slate-500 mt-0.5">{grup.desc}</p>
                                    </div>
                                </div>

                                {/* Ayar Kalemleri */}
                                <div className="divide-y divide-slate-50 bg-slate-50/30">
                                    {grup.items.map((item, j) => (
                                        <div 
                                            key={j} 
                                            className={`flex items-center justify-between gap-4 p-4 sm:px-6 sm:py-5 transition-colors duration-200 ${
                                                item.isEditable 
                                                    ? 'hover:bg-indigo-50/50 cursor-pointer group active:bg-indigo-100/50' 
                                                    : 'opacity-90'
                                            }`}
                                        >
                                            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 flex-1 min-w-0">
                                                <span className={`text-sm sm:text-base font-semibold truncate ${
                                                    item.isEditable ? 'text-slate-700 group-hover:text-indigo-900' : 'text-slate-500'
                                                }`}>
                                                    {item.label}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-3 shrink-0">
                                                {/* Değer Rozeti (Badge) */}
                                                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
                                                    item.isEditable 
                                                        ? 'bg-white border-slate-200 text-slate-700 shadow-sm group-hover:border-indigo-300 group-hover:text-indigo-700' 
                                                        : 'bg-slate-100 border-transparent text-slate-500'
                                                }`}>
                                                    {!item.isEditable && <Lock className="w-3.5 h-3.5 text-slate-400" />}
                                                    {item.value}
                                                </div>

                                                {/* Yön Ok İşareti (Sadece mobilde her zaman görünür, masaüstünde hover ile) */}
                                                {item.isEditable ? (
                                                    <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                                                ) : (
                                                    <div className="w-5 h-5 hidden sm:block"></div> /* Hizalama için boşluk */
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Bilgilendirme Banner'ı */}
                <div className="relative overflow-hidden bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100 rounded-2xl sm:rounded-3xl p-5 sm:p-6 shadow-sm mt-8">
                    {/* Arka Plan Dekoratif İkon */}
                    <div className="absolute -top-6 -right-6 p-8 opacity-[0.03] pointer-events-none">
                        <Settings className="w-48 h-48 animate-[spin_20s_linear_infinite]" />
                    </div>
                    
                    <div className="relative z-10 flex flex-col sm:flex-row gap-4 sm:gap-5 items-start">
                        <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 shadow-inner">
                            <AlertCircle className="w-6 h-6 text-indigo-600" />
                        </div>
                        <div className="flex-1">
                            <h4 className="text-base font-bold text-indigo-900 flex items-center gap-2.5 mb-1.5">
                                Geliştirme Aşamasında
                                <span className="flex h-2.5 w-2.5 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                                </span>
                            </h4>
                            <p className="text-sm text-indigo-800/80 leading-relaxed max-w-3xl">
                                Bu ayarlar sayfası Faz 3 ve Faz 4 güncellemelerinde tam etkileşimli hale gelecektir. 
                                Gelecek sürümlerde <strong className="font-semibold text-indigo-900">JWT kimlik doğrulama</strong>, 
                                gelişmiş kullanıcı yönetimi ve rol tabanlı yetkilendirme (RBAC) panelleri buraya entegre edilecektir.
                            </p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}