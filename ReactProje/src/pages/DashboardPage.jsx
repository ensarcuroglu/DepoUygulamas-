import { useState, useEffect } from 'react';
import { useAsync } from '../hooks/useAsync';
import {
    Package, AlertTriangle, ArrowLeftRight, DollarSign,
    TrendingUp, TrendingDown, Clock, ArrowUpRight, ArrowDownRight,
    MoreVertical, Zap, Box, CheckCircle2
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats, getKritikUrunler, getStokHareketleri } from '../services/api';

// Yeni Modern Mobil-First Stat Card
function StatCard({ icon: Icon, label, value, trend, delay = 0, color = 'blue' }) {
    const isPositive = trend >= 0;

    const colorStyles = {
        blue: {
            bg: 'bg-blue-500',
            glow: 'shadow-blue-500/30',
            text: 'text-blue-600',
            lightBg: 'bg-blue-50',
            iconText: 'text-white'
        },
        red: {
            bg: 'bg-red-500',
            glow: 'shadow-red-500/30',
            text: 'text-red-600',
            lightBg: 'bg-red-50',
            iconText: 'text-white'
        },
        emerald: {
            bg: 'bg-emerald-500',
            glow: 'shadow-emerald-500/30',
            text: 'text-emerald-600',
            lightBg: 'bg-emerald-50',
            iconText: 'text-white'
        },
        indigo: {
            bg: 'bg-indigo-500',
            glow: 'shadow-indigo-500/30',
            text: 'text-indigo-600',
            lightBg: 'bg-indigo-50',
            iconText: 'text-white'
        }
    }[color];

    return (
        <div
            className="group bg-white rounded-3xl border border-slate-100 p-5 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 animate-fade-in flex items-center justify-between overflow-hidden relative"
            style={{ animationDelay: `${delay}ms` }}
        >
            {/* Dekoratif Arkaplan Blob */}
            <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full opacity-10 blur-xl group-hover:scale-150 transition-transform duration-500 pointer-events-none ${colorStyles.bg}`} />

            <div className="flex-1 relative z-10">
                <p className="text-[14px] font-extrabold text-slate-400 uppercase tracking-widest mb-1">{label}</p>
                <div className="flex items-end gap-3">
                    <p className="text-[32px] font-black text-slate-800 leading-none">{value}</p>
                    {trend !== undefined && (
                        <div className={`flex items-center gap-1 text-[12px] font-bold px-2 py-0.5 rounded-lg mb-1
                            ${isPositive ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-red-50 text-red-600 border border-red-100'}`}>
                            {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" strokeWidth={3} /> : <ArrowDownRight className="w-3.5 h-3.5" strokeWidth={3} />}
                            {Math.abs(trend)}%
                        </div>
                    )}
                </div>
            </div>
            <div className={`w-14 h-14 rounded-2xl ${colorStyles.bg} flex items-center justify-center flex-shrink-0 shadow-lg ${colorStyles.glow} relative z-10 group-hover:scale-110 transition-transform duration-300`}>
                <Icon className={`w-7 h-7 ${colorStyles.iconText}`} strokeWidth={2.5} />
            </div>
        </div>
    );
}

// Modern Kritik Stok Satırı
function KritikRow({ urun, index }) {
    const isTehlikeli = urun.stok_miktari === 0;
    const isWarning = !isTehlikeli;
    const yuzde = urun.min_stok > 0 ? Math.round((urun.stok_miktari / urun.min_stok) * 100) : 0;

    return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-white border border-slate-100 rounded-2xl hover:border-slate-300 hover:shadow-md transition-all cursor-pointer group animate-fade-in"
            style={{ animationDelay: `${index * 60}ms` }}>

            <div className="flex items-center gap-4 min-w-0">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-sm
                    ${isTehlikeli ? 'bg-red-50 text-red-500' : 'bg-amber-50 text-amber-500'}`}>
                    {isTehlikeli ? <AlertTriangle className="w-6 h-6" strokeWidth={2.5} /> : <Zap className="w-6 h-6" strokeWidth={2.5} />}
                </div>
                <div className="min-w-0 flex-1">
                    <p className="text-[15px] font-black text-slate-800 truncate leading-tight group-hover:text-blue-600 transition-colors">
                        {urun.isim}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-[12px] font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">
                            {urun.marka?.isim || 'Markasız'}
                        </span>
                        {isTehlikeli && (
                            <span className="text-[10px] font-extrabold text-red-600 uppercase tracking-widest bg-red-50 px-2 py-0.5 rounded-md">
                                TÜKENDİ
                            </span>
                        )}
                    </div>
                </div>
            </div>

            <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center w-full sm:w-28 pl-16 sm:pl-0 mt-1 sm:mt-0">
                <p className="text-[16px] font-black text-slate-800 tabular-nums">
                    {urun.stok_miktari} <span className="text-[12px] font-bold text-slate-400">{urun.birim}</span>
                </p>
                <div className="w-24 sm:w-full h-2 bg-slate-100 rounded-full sm:mt-2 overflow-hidden flex-shrink-0">
                    <div className={`h-full rounded-full transition-all duration-1000 ease-out 
                        ${isTehlikeli ? 'bg-red-500' : 'bg-amber-400'}`}
                        style={{ width: `${Math.min(yuzde, 100)}%` }} />
                </div>
            </div>
        </div>
    );
}

// Modern Son Hareket Satırı
function HareketRow({ hareket, index }) {
    const isGiris = hareket.hareket_tipi === 'giris';

    return (
        <div className="flex items-center justify-between p-4 bg-white border border-slate-100 rounded-2xl hover:border-slate-300 hover:shadow-md transition-all animate-fade-in group"
            style={{ animationDelay: `${index * 50}ms` }}>
            <div className="flex items-center gap-4 min-w-0">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0
                    ${isGiris ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                    {isGiris ? <TrendingUp className="w-6 h-6" strokeWidth={2.5} /> : <TrendingDown className="w-6 h-6" strokeWidth={2.5} />}
                </div>
                <div className="min-w-0">
                    <p className="text-[15px] font-black text-slate-800 truncate leading-snug">
                        {hareket.aciklama || (isGiris ? 'Tedarikçi Girişi' : 'Depo Çıkışı')}
                    </p>
                    <div className="flex items-center flex-wrap gap-2 mt-1 line-clamp-1">
                        <span className="text-[12px] font-bold text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">
                            Ürün: #{hareket.urun_id}
                        </span>
                        <span className="text-[12px] font-medium text-slate-400">
                            {new Date(hareket.tarih).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                </div>
            </div>

            <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <span className={`text-[18px] font-black tabular-nums bg-opacity-10 px-3 py-1 rounded-xl
                    ${isGiris ? 'text-emerald-600 bg-emerald-500' : 'text-rose-600 bg-rose-500'}`}>
                    {isGiris ? '+' : '−'}{hareket.miktar}
                </span>
            </div>
        </div>
    );
}

// Mock chart datası (Gerçekçi ve yumuşatılmış)
const chartData = [
    { day: '01 Şub', giris: 120, cikis: 80 },
    { day: '02 Şub', giris: 135, cikis: 90 },
    { day: '03 Şub', giris: 190, cikis: 160 },
    { day: '04 Şub', giris: 220, cikis: 140 },
    { day: '05 Şub', giris: 280, cikis: 190 },
    { day: '06 Şub', giris: 210, cikis: 220 },
    { day: '07 Şub', giris: 310, cikis: 250 },
];

export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [kritikler, setKritikler] = useState([]);
    const [hareketler, setHareketler] = useState([]);
    const { loading, run } = useAsync(true);

    useEffect(() => {
        run(() => Promise.all([
            getDashboardStats(),
            getKritikUrunler(),
            getStokHareketleri({ limit: 4 }),
        ])).then(([statsRes, kritikRes, hareketRes]) => {
            setStats(statsRes.data);
            setKritikler(kritikRes.data);
            setHareketler(hareketRes.data);
        }).catch(() => {/* skeleton kalır, toast gereksiz — dashboard ana sayfa */});
    }, []);

    // Skeleton Loaders
    if (loading) {
        return (
            <div className="max-w-[1400px] mx-auto p-4 sm:p-6 space-y-6 md:space-y-8 min-h-screen">
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="bg-white animate-pulse h-[116px] rounded-3xl border border-slate-100 shadow-sm" />
                    ))}
                </div>
                <div className="bg-white animate-pulse h-[350px] rounded-3xl border border-slate-100 shadow-sm" />
            </div>
        );
    }

    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 pb-24 sm:pb-8 space-y-6 md:space-y-8 min-h-screen">

            {/* Header */}
            <div>
                <h1 className="text-[26px] font-black text-slate-900 tracking-tight leading-none mb-1">Hoş Geldiniz</h1>
                <p className="text-[14px] font-medium text-slate-500">Deponuzun bugünkü genel özeti.</p>
            </div>

            {/* 4 Ana KPI */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6">
                <StatCard color="blue" icon={Box} label="Toplam Ürün" value={stats?.toplam_urun || 0} trend={2} delay={0} />
                <StatCard color="red" icon={AlertTriangle} label="Kritik Stoklar" value={stats?.kritik_stok_sayisi || 0} trend={-5} delay={100} />
                <StatCard color="emerald" icon={ArrowLeftRight} label="Bugünkü İşlem" value={stats?.bugunku_hareket || 0} trend={14} delay={200} />
                <StatCard color="indigo" icon={DollarSign} label="Envanter (₺)"
                    value={((stats?.toplam_deger || 0) / 1000).toFixed(1) + 'K'} delay={300} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 md:gap-8">

                {/* Modern Area Chart Box */}
                <div className="lg:col-span-3 bg-white rounded-[32px] border border-slate-100 p-6 sm:p-8 shadow-sm animate-fade-in"
                    style={{ animationDelay: '400ms' }}>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                        <div>
                            <h3 className="text-[20px] font-black text-slate-800 tracking-tight">Stok Akışı</h3>
                            <p className="text-[13px] font-medium text-slate-400 mt-1">Son 7 günlük depo giriş-çıkış analizi.</p>
                        </div>

                        <div className="flex items-center gap-5 bg-slate-50 px-4 py-2.5 rounded-2xl border border-slate-100 w-max">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm shadow-blue-500/50" />
                                <span className="text-[12px] font-bold text-slate-600 uppercase tracking-widest">Grup</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-slate-300" />
                                <span className="text-[12px] font-bold text-slate-600 uppercase tracking-widest">Çıkış</span>
                            </div>
                        </div>
                    </div>

                    <div className="h-[250px] sm:h-[300px] w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorGiris2" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorCikis2" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#94a3b8" stopOpacity={0.15} />
                                        <stop offset="100%" stopColor="#94a3b8" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 700 }} dy={12} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 700 }} />
                                <Tooltip
                                    cursor={{ stroke: '#e2e8f0', strokeWidth: 1, strokeDasharray: '3 3' }}
                                    contentStyle={{ borderRadius: '16px', border: '1px solid #f1f5f9', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)', fontSize: '13px', fontWeight: 'bold' }}
                                    itemStyle={{ fontWeight: 'black' }}
                                />
                                <Area type="monotone" dataKey="giris" stroke="#3b82f6" strokeWidth={4} fillOpacity={1} fill="url(#colorGiris2)" activeDot={{ r: 6, strokeWidth: 0, fill: '#3b82f6' }} />
                                <Area type="monotone" dataKey="cikis" stroke="#94a3b8" strokeWidth={4} fillOpacity={1} fill="url(#colorCikis2)" activeDot={{ r: 6, strokeWidth: 0, fill: '#94a3b8' }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="lg:col-span-2 space-y-6">
                    {/* Modern Kritik Stok Alarmı */}
                    <div className="bg-white rounded-[32px] border border-slate-100 p-6 sm:p-8 shadow-sm flex flex-col h-full min-h-[400px] animate-fade-in"
                        style={{ animationDelay: '500ms' }}>

                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-[20px] font-black text-slate-800 tracking-tight">Kritik Stoklar</h3>
                                <p className="text-[13px] font-medium text-slate-400 mt-1">Acil tedarik bekleyenürünler.</p>
                            </div>
                            <div className="w-12 h-12 bg-rose-50 rounded-2xl flex items-center justify-center border border-rose-100 text-rose-500 shadow-sm">
                                <span className="text-[16px] font-black">{kritikler.length}</span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto pr-1">
                            {kritikler.length > 0 ? (
                                <div className="space-y-3">
                                    {kritikler.map((urun, i) => <KritikRow key={urun.id} urun={urun} index={i} />)}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center py-10">
                                    <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-4">
                                        <CheckCircle2 className="w-10 h-10 text-emerald-500" strokeWidth={2} />
                                    </div>
                                    <p className="text-[16px] font-black text-slate-800">Her Şey Harika!</p>
                                    <p className="text-[13px] font-medium text-slate-400 mt-1">Kritik seviyeye düşen ürün yok.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

            </div>

            {/* Alt Sekme: Aktivite */}
            <div className="bg-white rounded-[32px] border border-slate-100 p-6 sm:p-8 shadow-sm animate-fade-in"
                style={{ animationDelay: '600ms' }}>
                <div className="flex items-center justify-between mb-6 sm:mb-8">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center border border-indigo-100 text-indigo-600 shadow-sm shadow-indigo-500/20">
                            <Clock className="w-6 h-6" strokeWidth={2.5} />
                        </div>
                        <div>
                            <h3 className="text-[20px] font-black text-slate-800 tracking-tight">Son Aktiviteler</h3>
                            <p className="text-[13px] font-medium text-slate-400 mt-1">Depoda gerçekleşen en son 4 hareket.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {hareketler.map((h, i) => <HareketRow key={h.id} hareket={h} index={i} />)}
                    {hareketler.length === 0 && (
                        <div className="col-span-full py-12 text-center">
                            <Box className="w-12 h-12 text-slate-200 mx-auto mb-3" />
                            <p className="text-[15px] font-bold text-slate-400">Henüz kaydedilmiş hareket yok.</p>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
}