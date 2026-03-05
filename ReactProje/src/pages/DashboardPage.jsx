import { useState, useEffect } from 'react';
import {
    Package, AlertTriangle, ArrowLeftRight, DollarSign,
    TrendingUp, TrendingDown, Clock, ArrowUpRight, ArrowDownRight,
    MoreVertical
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats, getKritikUrunler, getStokHareketleri } from '../services/api';

// Minimal Stat Card
function StatCard({ icon: Icon, label, value, trend, delay = 0 }) {
    return (
        <div
            className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-shadow duration-300 animate-fade-in flex flex-col justify-between"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-full bg-gray-50/80 flex items-center justify-center border border-gray-100/50 text-gray-600">
                    <Icon className="w-5 h-5" strokeWidth={1.5} />
                </div>
                {trend !== undefined && (
                    <div className={`flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full 
                        ${trend >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                        {trend >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                        {Math.abs(trend)}%
                    </div>
                )}
            </div>
            <div>
                <p className="text-3xl font-semibold text-gray-800 tracking-tight mb-1">{value}</p>
                <p className="text-sm font-medium text-gray-400">{label}</p>
            </div>
        </div>
    );
}

// Minimal Kritik Stok Satırı
function KritikRow({ urun, index }) {
    const yuzde = urun.min_stok > 0 ? Math.round((urun.stok_miktari / urun.min_stok) * 100) : 0;

    return (
        <div className="flex items-center justify-between py-3.5 border-b border-gray-50 last:border-0 hover:bg-gray-50/50 px-2 -mx-2 rounded-lg transition-colors cursor-pointer animate-fade-in"
            style={{ animationDelay: `${index * 60}ms` }}>
            <div className="flex items-center gap-4 min-w-0">
                <div className="w-9 h-9 rounded-full bg-red-50/50 flex items-center justify-center flex-shrink-0">
                    <AlertTriangle className="w-4 h-4 text-red-500" strokeWidth={1.5} />
                </div>
                <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{urun.isim}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{urun.marka?.isim || 'Marka belirtilmemiş'}</p>
                </div>
            </div>
            <div className="text-right flex-shrink-0 flex flex-col items-end w-24">
                <p className="text-sm font-semibold text-gray-800">{urun.stok_miktari} <span className="text-xs font-normal text-gray-400">{urun.birim}</span></p>
                <div className="w-full h-1.5 bg-gray-100 rounded-full mt-2 overflow-hidden">
                    <div className="h-full bg-red-400 rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${Math.min(yuzde, 100)}%` }} />
                </div>
            </div>
        </div>
    );
}

// Minimal Son Hareket Satırı
function HareketRow({ hareket, index }) {
    const isGiris = hareket.hareket_tipi === 'giris';

    return (
        <div className="flex items-center justify-between py-3.5 border-b border-gray-50 last:border-0 hover:bg-gray-50/50 px-2 -mx-2 rounded-lg transition-colors animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}>
            <div className="flex items-center gap-4 min-w-0">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0
                    ${isGiris ? 'bg-emerald-50/50 text-emerald-600' : 'bg-gray-50 text-gray-500'}`}>
                    {isGiris ? <TrendingUp className="w-4 h-4" strokeWidth={1.5} /> : <TrendingDown className="w-4 h-4" strokeWidth={1.5} />}
                </div>
                <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{hareket.aciklama || (isGiris ? 'Stok Girişi' : 'Stok Çıkışı')}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400">ID: {hareket.urun_id}</span>
                        <span className="text-xs text-gray-300">•</span>
                        <span className="text-xs text-gray-400">
                            {new Date(hareket.tarih).toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                </div>
            </div>
            <div className="flex items-center gap-3">
                <span className={`text-sm font-semibold ${isGiris ? 'text-emerald-600' : 'text-gray-600'}`}>
                    {isGiris ? '+' : '-'}{hareket.miktar}
                </span>
                <button className="text-gray-300 hover:text-gray-500 transition-colors p-1 rounded-md hover:bg-gray-100">
                    <MoreVertical className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}

// Mock chart datası (Aynı bırakıldı)
const chartData = [
    { day: '01', giris: 120, cikis: 80 },
    { day: '02', giris: 180, cikis: 140 },
    { day: '03', giris: 150, cikis: 160 },
    { day: '04', giris: 220, cikis: 110 },
    { day: '05', giris: 280, cikis: 190 },
    { day: '06', giris: 160, cikis: 120 },
    { day: '07', giris: 210, cikis: 170 },
    { day: '08', giris: 310, cikis: 220 },
];

export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [kritikler, setKritikler] = useState([]);
    const [hareketler, setHareketler] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getDashboardStats(),
            getKritikUrunler(),
            getStokHareketleri({ limit: 6 }),
        ]).then(([statsRes, kritikRes, hareketRes]) => {
            setStats(statsRes.data);
            setKritikler(kritikRes.data);
            setHareketler(hareketRes.data);
        }).catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    // Zarif Yükleniyor Durumu
    if (loading) {
        return (
            <div className="space-y-6 md:space-y-8">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="bg-gray-100/50 animate-pulse h-36 rounded-2xl border border-gray-100" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 md:space-y-8 pb-10 bg-[#FAFAFA] min-h-screen">

            {/* 4 Ana KPI */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
                <StatCard icon={Package} label="Sistemdeki Toplam Ürün" value={stats?.toplam_urun || 0} trend={2} delay={0} />
                <StatCard icon={AlertTriangle} label="Acil Re-order Gereken" value={stats?.kritik_stok_sayisi || 0} trend={-5} delay={100} />
                <StatCard icon={ArrowLeftRight} label="Bugün Yapılan İşlem" value={stats?.bugunku_hareket || 0} trend={14} delay={200} />
                <StatCard icon={DollarSign} label="Toplam Envanter Değeri"
                    value={`₺${((stats?.toplam_deger || 0) / 1000).toFixed(1)}K`} delay={300} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">

                {/* Minimal Area Chart */}
                <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-6 md:p-8 shadow-sm animate-fade-in"
                    style={{ animationDelay: '400ms' }}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800">Envanter Akışı</h3>
                            <p className="text-sm text-gray-400 mt-1">Son 8 günlük giriş ve çıkış eğilimleri</p>
                        </div>
                        <div className="flex items-center gap-5">
                            <div className="flex items-center gap-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                                <span className="text-sm font-medium text-gray-500">Girişler</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-gray-300" />
                                <span className="text-sm font-medium text-gray-500">Çıkışlar</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-[240px] sm:h-[280px] w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorGiris" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorCikis" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.1} />
                                        <stop offset="95%" stopColor="#9ca3af" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: '1px solid #f1f5f9', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', fontSize: '12px' }}
                                />
                                <Area type="monotone" dataKey="giris" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorGiris)" />
                                <Area type="monotone" dataKey="cikis" stroke="#9ca3af" strokeWidth={2} fillOpacity={1} fill="url(#colorCikis)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Sade Kritik Stok Uyarıları */}
                <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8 shadow-sm flex flex-col animate-fade-in"
                    style={{ animationDelay: '500ms' }}>
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800">Re-order Alarmı</h3>
                            <p className="text-sm text-gray-400 mt-1">Stok seviyesi düşenler</p>
                        </div>
                        <span className="text-xs font-medium text-red-600 bg-red-50 px-2.5 py-1 rounded-full">
                            {kritikler.length} Ürün
                        </span>
                    </div>
                    <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
                        {kritikler.length > 0 ? (
                            <div className="space-y-1">
                                {kritikler.map((urun, i) => <KritikRow key={urun.id} urun={urun} index={i} />)}
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-center py-10">
                                <Package className="w-12 h-12 text-gray-200 mb-3" strokeWidth={1} />
                                <p className="text-sm font-medium text-gray-500">Kritik stok uyarısı yok</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Sadeleştirilmiş Aktivite Akışı */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8 shadow-sm animate-fade-in"
                style={{ animationDelay: '600ms' }}>
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center border border-gray-100 text-gray-600">
                            <Clock className="w-5 h-5" strokeWidth={1.5} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800">Aktivite Akışı</h3>
                            <p className="text-sm text-gray-400 mt-1">Son depo operasyonları</p>
                        </div>
                    </div>
                    <button className="text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors">
                        Tümünü Gör
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-1 mt-2">
                    {hareketler.map((h, i) => <HareketRow key={h.id} hareket={h} index={i} />)}
                    {hareketler.length === 0 && (
                        <p className="col-span-2 text-center text-sm font-medium text-gray-400 py-8">Henüz kaydedilmiş bir hareket bulunmuyor.</p>
                    )}
                </div>
            </div>
        </div>
    );
}