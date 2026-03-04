import { Settings, Database, Shield, Palette, ChevronRight, AlertCircle } from 'lucide-react';

export default function AyarlarPage() {
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
                { label: 'Auth Yöntemi', value: 'JWT (Faz 3)', isEditable: false },
                { label: 'Şifreleme Algoritması', value: 'bcrypt', isEditable: true },
                { label: 'Token Geçerlilik Süresi', value: '24 saat', isEditable: true },
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
        <div className="max-w-4xl space-y-8 pb-10 animate-fade-in">
            {/* Sayfa Başlığı */}
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Sistem Tercihleri</h1>
                <p className="mt-2 text-sm text-slate-500">
                    Depo yönetim sisteminin altyapı, güvenlik ve arayüz davranışlarını buradan yönetebilirsiniz.
                </p>
            </div>

            <div className="space-y-6">
                {ayarGruplari.map((grup, i) => {
                    const Icon = grup.icon;
                    return (
                        <div 
                            key={i} 
                            className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md animate-fade-in"
                            style={{ animationDelay: `${i * 100}ms` }}
                        >
                            {/* Grup Başlığı */}
                            <div className="flex items-center gap-4 p-5 sm:px-6 border-b border-slate-100 bg-slate-50/50">
                                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100/50 flex items-center justify-center flex-shrink-0 shadow-inner">
                                    <Icon className="w-5 h-5 text-blue-600" />
                                </div>
                                <div>
                                    <h3 className="text-base font-bold text-slate-800">{grup.title}</h3>
                                    <p className="text-xs text-slate-500 mt-0.5">{grup.desc}</p>
                                </div>
                            </div>

                            {/* Ayar Kalemleri */}
                            <div className="divide-y divide-slate-100">
                                {grup.items.map((item, j) => (
                                    <div 
                                        key={j} 
                                        className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 sm:px-6 py-4 transition-colors ${item.isEditable ? 'hover:bg-slate-50 cursor-pointer group' : ''}`}
                                    >
                                        <span className="text-[14px] font-medium text-slate-700">
                                            {item.label}
                                        </span>
                                        <div className="flex items-center gap-3">
                                            <span className={`text-[13px] px-3 py-1.5 rounded-lg border font-medium transition-colors
                                                ${item.isEditable 
                                                    ? 'bg-white border-slate-200 text-slate-700 group-hover:border-blue-300 group-hover:text-blue-700 group-hover:bg-blue-50/50' 
                                                    : 'bg-slate-100 border-transparent text-slate-500'}`}
                                            >
                                                {item.value}
                                            </span>
                                            {item.isEditable && (
                                                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors hidden sm:block" />
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
            <div 
                className="bg-gradient-to-br from-indigo-50/80 to-blue-50/50 border border-indigo-100/60 rounded-2xl p-5 sm:p-6 animate-fade-in relative overflow-hidden"
                style={{ animationDelay: '400ms' }}
            >
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Settings className="w-32 h-32 animate-[spin_10s_linear_infinite]" />
                </div>
                
                <div className="relative z-10 flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-indigo-100/80 flex items-center justify-center flex-shrink-0">
                        <AlertCircle className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div>
                        <h4 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                            Geliştirme Aşamasında
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                            </span>
                        </h4>
                        <p className="text-[13px] text-indigo-800/80 mt-1.5 leading-relaxed max-w-2xl">
                            Bu ayarlar sayfası Faz 3 ve Faz 4 güncellemelerinde tam etkileşimli hale gelecektir. 
                            Gelecek sürümlerde <strong>JWT kimlik doğrulama</strong>, gelişmiş kullanıcı yönetimi ve rol tabanlı yetkilendirme (RBAC) panelleri buraya entegre edilecektir.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}