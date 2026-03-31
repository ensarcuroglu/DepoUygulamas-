import { useState, useEffect, useRef, useCallback } from 'react';
import { useAsync } from '../hooks/useAsync';
import {
    Package, AlertTriangle, ArrowLeftRight, DollarSign,
    TrendingUp, TrendingDown, Clock, ArrowUpRight, ArrowDownRight,
    MoreVertical, Zap, Box, CheckCircle2, RefreshCcw
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats, getKritikUrunler, getStokHareketleri } from '../services/api';

/* ─────────────────────────────────────────────
   CSS-in-JS Style Block (injected once)
   ───────────────────────────────────────────── */
const STYLE_ID = 'dashboard-v2-styles';

function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
        /* ── Keyframes ── */
        @keyframes dsh-fadeUp {
            from { opacity: 0; transform: translateY(24px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes dsh-fadeIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
        @keyframes dsh-scaleIn {
            from { opacity: 0; transform: scale(0.92); }
            to   { opacity: 1; transform: scale(1); }
        }
        @keyframes dsh-slideRight {
            from { opacity: 0; transform: translateX(-16px); }
            to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes dsh-countUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes dsh-pulse-ring {
            0%   { transform: scale(1); opacity: 0.4; }
            100% { transform: scale(1.8); opacity: 0; }
        }
        @keyframes dsh-shimmer {
            0%   { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        @keyframes dsh-progressFill {
            from { width: 0%; }
        }
        @keyframes dsh-float {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-6px); }
        }

        /* ── Utility Classes ── */
        .dsh-fade-up {
            opacity: 0;
            animation: dsh-fadeUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .dsh-fade-in {
            opacity: 0;
            animation: dsh-fadeIn 0.5s ease forwards;
        }
        .dsh-scale-in {
            opacity: 0;
            animation: dsh-scaleIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .dsh-slide-right {
            opacity: 0;
            animation: dsh-slideRight 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .dsh-count-up {
            animation: dsh-countUp 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }

        /* ── Skeleton ── */
        .dsh-skeleton {
            background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
            background-size: 200% 100%;
            animation: dsh-shimmer 1.5s ease-in-out infinite;
        }

        /* ── Progress bar fill ── */
        .dsh-progress-fill {
            animation: dsh-progressFill 1s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }

        /* ── Scroll-triggered visibility ── */
        .dsh-observe {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                        transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .dsh-observe.dsh-visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* ── Glass morphism card ── */
        .dsh-glass {
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        /* ── Custom Scrollbar ── */
        .dsh-scroll::-webkit-scrollbar { width: 4px; }
        .dsh-scroll::-webkit-scrollbar-track { background: transparent; }
        .dsh-scroll::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 100px;
        }
        .dsh-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

        /* ── Tooltip custom ── */
        .dsh-chart-tooltip {
            background: rgba(255,255,255,0.95) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(241,245,249,0.8) !important;
            border-radius: 16px !important;
            box-shadow: 0 20px 40px -12px rgba(0,0,0,0.12) !important;
            padding: 12px 16px !important;
        }

        /* ── Floating dot ── */
        .dsh-float { animation: dsh-float 3s ease-in-out infinite; }
    `;
    document.head.appendChild(style);
}

/* ─────────────────────────────────────────────
   Intersection Observer Hook (scroll-triggered)
   ───────────────────────────────────────────── */
function useScrollReveal() {
    const ref = useRef(null);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    el.classList.add('dsh-visible');
                    observer.unobserve(el);
                }
            },
            { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    return ref;
}

/* ─────────────────────────────────────────────
   Animated Number Counter
   ───────────────────────────────────────────── */
function AnimatedValue({ value, suffix = '', prefix = '' }) {
    const [display, setDisplay] = useState(0);
    const numericValue = typeof value === 'string' ? parseFloat(value) : value;

    useEffect(() => {
        if (isNaN(numericValue)) { setDisplay(value); return; }
        const duration = 800;
        const steps = 30;
        const increment = numericValue / steps;
        let current = 0;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            current = Math.min(current + increment, numericValue);
            // Easing: decelerate
            const progress = step / steps;
            const eased = 1 - Math.pow(1 - progress, 3);
            setDisplay(Math.round(numericValue * eased));

            if (step >= steps) {
                setDisplay(numericValue);
                clearInterval(timer);
            }
        }, duration / steps);

        return () => clearInterval(timer);
    }, [numericValue]);

    if (typeof value === 'string' && isNaN(parseFloat(value))) {
        return <>{value}</>;
    }

    return <>{prefix}{typeof value === 'string' ? value : display}{suffix}</>;
}

/* ─────────────────────────────────────────────
   Stat Card – Redesigned
   ───────────────────────────────────────────── */
function StatCard({ icon: Icon, label, value, trend, delay = 0, color = 'blue' }) {
    const isPositive = trend >= 0;
    const ref = useRef(null);

    const palette = {
        blue: {
            gradient: 'from-blue-500 to-blue-600',
            ring: 'ring-blue-500/20',
            trendPos: 'text-emerald-600 bg-emerald-50',
            trendNeg: 'text-red-600 bg-red-50',
            blob: 'bg-blue-400',
            iconBg: 'bg-gradient-to-br from-blue-500 to-blue-600',
            accent: '#3b82f6',
        },
        red: {
            gradient: 'from-rose-500 to-red-600',
            ring: 'ring-rose-500/20',
            trendPos: 'text-emerald-600 bg-emerald-50',
            trendNeg: 'text-red-600 bg-red-50',
            blob: 'bg-rose-400',
            iconBg: 'bg-gradient-to-br from-rose-500 to-red-600',
            accent: '#f43f5e',
        },
        emerald: {
            gradient: 'from-emerald-500 to-emerald-600',
            ring: 'ring-emerald-500/20',
            trendPos: 'text-emerald-600 bg-emerald-50',
            trendNeg: 'text-red-600 bg-red-50',
            blob: 'bg-emerald-400',
            iconBg: 'bg-gradient-to-br from-emerald-500 to-emerald-600',
            accent: '#10b981',
        },
        indigo: {
            gradient: 'from-indigo-500 to-indigo-600',
            ring: 'ring-indigo-500/20',
            trendPos: 'text-emerald-600 bg-emerald-50',
            trendNeg: 'text-red-600 bg-red-50',
            blob: 'bg-indigo-400',
            iconBg: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
            accent: '#6366f1',
        },
    }[color];

    return (
        <div
            ref={ref}
            className="dsh-fade-up group relative bg-white rounded-[20px] border border-slate-100/80 p-5 sm:p-6
                       hover:shadow-2xl hover:shadow-slate-200/60 hover:-translate-y-1.5
                       transition-all duration-500 ease-out cursor-default overflow-hidden"
            style={{ animationDelay: `${delay}ms` }}
        >
            {/* Decorative corner blob */}
            <div className={`absolute -right-8 -top-8 w-28 h-28 rounded-full ${palette.blob} opacity-[0.07] blur-2xl
                            group-hover:opacity-[0.14] group-hover:scale-[1.6] transition-all duration-700 pointer-events-none`} />

            {/* Subtle bottom accent line */}
            <div className={`absolute bottom-0 left-6 right-6 h-[2px] rounded-full bg-gradient-to-r ${palette.gradient} opacity-0 group-hover:opacity-40 transition-opacity duration-500`} />

            <div className="relative z-10 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <p className="text-[11px] sm:text-[12px] font-bold text-slate-400 uppercase tracking-[0.12em] mb-2 truncate">
                        {label}
                    </p>
                    <div className="flex items-end gap-2.5 flex-wrap">
                        <p className="text-[28px] sm:text-[32px] font-black text-slate-900 leading-none tracking-tight tabular-nums dsh-count-up">
                            <AnimatedValue value={value} />
                        </p>
                        {trend !== undefined && (
                            <span className={`inline-flex items-center gap-0.5 text-[11px] font-bold px-2 py-0.5 rounded-full mb-0.5
                                ${isPositive ? palette.trendPos : palette.trendNeg}
                                transition-transform duration-300 group-hover:scale-105`}>
                                {isPositive
                                    ? <ArrowUpRight className="w-3 h-3" strokeWidth={3} />
                                    : <ArrowDownRight className="w-3 h-3" strokeWidth={3} />}
                                {Math.abs(trend)}%
                            </span>
                        )}
                    </div>
                </div>

                {/* Icon container with pulse ring on hover */}
                <div className="relative flex-shrink-0">
                    <div className={`absolute inset-0 rounded-2xl ${palette.iconBg} opacity-0 group-hover:opacity-30
                                    group-hover:animate-[dsh-pulse-ring_1.2s_ease-out]
                                    transition-opacity duration-300 pointer-events-none`} />
                    <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-2xl ${palette.iconBg}
                                    flex items-center justify-center shadow-lg
                                    group-hover:scale-110 group-hover:rotate-3
                                    transition-all duration-500 ease-out`}
                         style={{ boxShadow: `0 8px 24px -4px ${palette.accent}40` }}>
                        <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-white" strokeWidth={2.2} />
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────
   Kritik Stok Row – Redesigned
   ───────────────────────────────────────────── */
function KritikRow({ urun, index }) {
    const isTehlikeli = urun.stok_miktari === 0;
    const yuzde = urun.min_stok > 0 ? Math.round((urun.stok_miktari / urun.min_stok) * 100) : 0;

    return (
        <div
            className="dsh-slide-right group flex flex-col sm:flex-row sm:items-center justify-between gap-3
                       p-3.5 sm:p-4 bg-white border border-slate-100/80 rounded-2xl
                       hover:border-slate-200 hover:shadow-lg hover:shadow-slate-100/80
                       transition-all duration-400 cursor-pointer"
            style={{ animationDelay: `${index * 80}ms` }}
        >
            <div className="flex items-center gap-3.5 min-w-0">
                {/* Status indicator with animated ring */}
                <div className="relative flex-shrink-0">
                    {isTehlikeli && (
                        <div className="absolute inset-0 rounded-xl bg-red-400 opacity-30 animate-[dsh-pulse-ring_2s_ease-out_infinite]" />
                    )}
                    <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center
                        ${isTehlikeli
                            ? 'bg-gradient-to-br from-red-50 to-red-100 text-red-500'
                            : 'bg-gradient-to-br from-amber-50 to-amber-100 text-amber-500'}`}>
                        {isTehlikeli
                            ? <AlertTriangle className="w-5 h-5" strokeWidth={2.5} />
                            : <Zap className="w-5 h-5" strokeWidth={2.5} />}
                    </div>
                </div>

                <div className="min-w-0 flex-1">
                    <p className="text-[14px] font-bold text-slate-800 truncate leading-tight
                                  group-hover:text-blue-600 transition-colors duration-300">
                        {urun.isim}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                        <span className="text-[11px] font-semibold text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded-md">
                            {urun.marka?.isim || 'Markasız'}
                        </span>
                        {isTehlikeli && (
                            <span className="text-[9px] font-extrabold text-red-600 uppercase tracking-wider bg-red-50 px-1.5 py-0.5 rounded-md border border-red-100">
                                Tükendi
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Right: Stock + Progress */}
            <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center
                            w-full sm:w-28 pl-14 sm:pl-0">
                <p className="text-[15px] font-black text-slate-800 tabular-nums">
                    {urun.stok_miktari}
                    <span className="text-[11px] font-semibold text-slate-400 ml-1">{urun.birim}</span>
                </p>
                <div className="w-20 sm:w-full h-1.5 bg-slate-100 rounded-full sm:mt-1.5 overflow-hidden flex-shrink-0">
                    <div
                        className={`h-full rounded-full dsh-progress-fill
                            ${isTehlikeli
                                ? 'bg-gradient-to-r from-red-400 to-red-500'
                                : 'bg-gradient-to-r from-amber-300 to-amber-400'}`}
                        style={{ width: `${Math.min(yuzde, 100)}%` }}
                    />
                </div>
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────
   Hareket Row – Redesigned
   ───────────────────────────────────────────── */
function HareketRow({ hareket, index }) {
    const isGiris = hareket.hareket_tipi === 'giris';

    return (
        <div
            className="dsh-fade-up group flex items-center justify-between gap-4
                       p-4 bg-white border border-slate-100/80 rounded-2xl
                       hover:border-slate-200 hover:shadow-lg hover:shadow-slate-100/80
                       transition-all duration-400"
            style={{ animationDelay: `${600 + index * 70}ms` }}
        >
            <div className="flex items-center gap-3.5 min-w-0">
                {/* Direction icon */}
                <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center flex-shrink-0
                    transition-transform duration-300 group-hover:scale-110
                    ${isGiris
                        ? 'bg-gradient-to-br from-emerald-50 to-emerald-100 text-emerald-600'
                        : 'bg-gradient-to-br from-rose-50 to-rose-100 text-rose-500'}`}>
                    {isGiris
                        ? <TrendingUp className="w-5 h-5" strokeWidth={2.5} />
                        : <TrendingDown className="w-5 h-5" strokeWidth={2.5} />}
                </div>

                <div className="min-w-0">
                    <p className="text-[14px] font-bold text-slate-800 truncate leading-snug">
                        {hareket.aciklama || (isGiris ? 'Tedarikçi Girişi' : 'Depo Çıkışı')}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-[11px] font-semibold text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded-md">
                            #{hareket.urun_id}
                        </span>
                        <span className="text-[11px] font-medium text-slate-400">
                            {new Date(hareket.tarih).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                </div>
            </div>

            {/* Amount badge */}
            <div className="flex-shrink-0">
                <span className={`inline-flex items-center text-[16px] font-black tabular-nums px-3 py-1.5 rounded-xl
                    transition-transform duration-300 group-hover:scale-105
                    ${isGiris
                        ? 'text-emerald-600 bg-emerald-50 border border-emerald-100'
                        : 'text-rose-600 bg-rose-50 border border-rose-100'}`}>
                    {isGiris ? '+' : '−'}{hareket.miktar}
                </span>
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────
   Custom Chart Tooltip
   ───────────────────────────────────────────── */
function ChartTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;

    return (
        <div className="dsh-chart-tooltip px-4 py-3">
            <p className="text-[12px] font-bold text-slate-500 mb-2">{label}</p>
            {payload.map((p, i) => (
                <div key={i} className="flex items-center justify-between gap-6 mb-1 last:mb-0">
                    <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: p.stroke }} />
                        <span className="text-[12px] font-semibold text-slate-600">
                            {p.dataKey === 'giris' ? 'Giriş' : 'Çıkış'}
                        </span>
                    </div>
                    <span className="text-[13px] font-black text-slate-800 tabular-nums">{p.value}</span>
                </div>
            ))}
        </div>
    );
}

/* ─────────────────────────────────────────────
   Section Wrapper with Scroll Reveal
   ───────────────────────────────────────────── */
function RevealSection({ children, className = '', delay = 0 }) {
    const ref = useScrollReveal();
    return (
        <div
            ref={ref}
            className={`dsh-observe ${className}`}
            style={{ transitionDelay: `${delay}ms` }}
        >
            {children}
        </div>
    );
}

/* ─────────────────────────────────────────────
   Skeleton Loader
   ───────────────────────────────────────────── */
function DashboardSkeleton() {
    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 space-y-6 md:space-y-8 min-h-screen">
            {/* Header skeleton */}
            <div className="space-y-2">
                <div className="dsh-skeleton h-8 w-48 rounded-xl" />
                <div className="dsh-skeleton h-4 w-72 rounded-lg" />
            </div>

            {/* KPI skeleton */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-5">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="dsh-skeleton h-[108px] rounded-[20px]"
                         style={{ animationDelay: `${i * 150}ms` }} />
                ))}
            </div>

            {/* Chart + Kritik skeleton */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <div className="lg:col-span-3 dsh-skeleton h-[400px] rounded-[24px]" />
                <div className="lg:col-span-2 dsh-skeleton h-[400px] rounded-[24px]" />
            </div>

            {/* Activity skeleton */}
            <div className="dsh-skeleton h-[280px] rounded-[24px]" />
        </div>
    );
}

/* ─────────────────────────────────────────────
   Chart Data (Mock — gerçek API'den gelecek)
   ───────────────────────────────────────────── */
/* ─────────────────────────────────────────────
   Chart Data Artık Backend'den Geliyor
   ───────────────────────────────────────────── */

/* ═════════════════════════════════════════════
   MAIN DASHBOARD PAGE
   ═════════════════════════════════════════════ */
export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [kritikler, setKritikler] = useState([]);
    const [hareketler, setHareketler] = useState([]);
    const { loading, run } = useAsync(true);

    // Inject styles once
    useEffect(() => { injectStyles(); }, []);

    const fetchData = useCallback(() => {
        run(() => Promise.all([
            getDashboardStats(),
            getKritikUrunler(),
            getStokHareketleri({ limit: 4 }),
        ])).then(([statsRes, kritikRes, hareketRes]) => {
            setStats(statsRes.data);
            setKritikler(kritikRes.data);
            setHareketler(hareketRes.data);
        }).catch(() => {});
    }, [run]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Greeting based on time of day
    const getGreeting = useCallback(() => {
        const hour = new Date().getHours();
        if (hour < 6)  return 'İyi Geceler';
        if (hour < 12) return 'Günaydın';
        if (hour < 18) return 'İyi Günler';
        return 'İyi Akşamlar';
    }, []);

    if (loading && !stats) return <DashboardSkeleton />;

    return (
        <div className="max-w-[1400px] mx-auto p-4 sm:p-6 pb-28 sm:pb-8 space-y-6 md:space-y-8 min-h-screen">

            {/* ── Header ── */}
            <div className="dsh-fade-up flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h1 className="text-[24px] sm:text-[28px] font-black text-slate-900 tracking-tight leading-none">
                            {getGreeting()} 👋
                        </h1>
                    </div>
                    <p className="text-[13px] sm:text-[14px] font-medium text-slate-400 leading-relaxed">
                        Deponuzun bugünkü genel durumuna göz atın.
                    </p>
                </div>
                
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="flex-shrink-0 flex items-center justify-center gap-2 bg-white border border-slate-200 text-slate-600 px-4 py-2.5 rounded-xl font-semibold text-[14px] hover:bg-slate-50 hover:text-blue-600 transition-colors shadow-sm disabled:opacity-50"
                >
                    <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-500' : ''}`} />
                    <span className="hidden sm:inline">Verileri Yenile</span>
                </button>
            </div>

            {/* ── 4 KPI Cards ── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-5">
                <StatCard
                    color="blue"
                    icon={Box}
                    label="Toplam Ürün"
                    value={stats?.toplam_urun || 0}
                    trend={2}
                    delay={0}
                />
                <StatCard
                    color="red"
                    icon={AlertTriangle}
                    label="Kritik Stoklar"
                    value={stats?.kritik_stok_sayisi || 0}
                    trend={-5}
                    delay={80}
                />
                <StatCard
                    color="emerald"
                    icon={ArrowLeftRight}
                    label="Bugünkü İşlem"
                    value={stats?.bugunku_hareket || 0}
                    trend={14}
                    delay={160}
                />
                <StatCard
                    color="indigo"
                    icon={DollarSign}
                    label="Envanter (₺)"
                    value={((stats?.toplam_deger || 0) / 1000).toFixed(1) + 'K'}
                    delay={240}
                />
            </div>

            {/* ── Chart + Kritik Stoklar Grid ── */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 md:gap-6">

                {/* Chart */}
                <RevealSection className="lg:col-span-3" delay={100}>
                    <div className="bg-white rounded-[24px] border border-slate-100/80 p-5 sm:p-7 shadow-sm
                                    hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-500">

                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
                            <div>
                                <h3 className="text-[18px] sm:text-[20px] font-black text-slate-800 tracking-tight">
                                    Stok Akışı
                                </h3>
                                <p className="text-[12px] sm:text-[13px] font-medium text-slate-400 mt-0.5">
                                    Son 7 günlük giriş-çıkış analizi
                                </p>
                            </div>

                            {/* Legend */}
                            <div className="flex items-center gap-4 bg-slate-50/80 px-3.5 py-2 rounded-xl border border-slate-100 w-max">
                                <div className="flex items-center gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm shadow-blue-500/40" />
                                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Giriş</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Çıkış</span>
                                </div>
                            </div>
                        </div>

                        <div className="h-[220px] sm:h-[280px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={stats?.stok_akisi || []} margin={{ top: 8, right: 4, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="gradGiris" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
                                            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="gradCikis" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#94a3b8" stopOpacity={0.12} />
                                            <stop offset="100%" stopColor="#94a3b8" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis
                                        dataKey="day"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
                                        dy={10}
                                    />
                                    <YAxis
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
                                    />
                                    <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#e2e8f0', strokeWidth: 1 }} />
                                    <Area
                                        type="monotone"
                                        dataKey="giris"
                                        stroke="#3b82f6"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#gradGiris)"
                                        activeDot={{ r: 5, strokeWidth: 3, stroke: '#fff', fill: '#3b82f6' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="cikis"
                                        stroke="#94a3b8"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#gradCikis)"
                                        activeDot={{ r: 5, strokeWidth: 3, stroke: '#fff', fill: '#94a3b8' }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </RevealSection>

                {/* Kritik Stoklar */}
                <RevealSection className="lg:col-span-2" delay={200}>
                    <div className="bg-white rounded-[24px] border border-slate-100/80 p-5 sm:p-7 shadow-sm
                                    flex flex-col h-full min-h-[400px]
                                    hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-500">

                        <div className="flex items-center justify-between mb-5">
                            <div>
                                <h3 className="text-[18px] sm:text-[20px] font-black text-slate-800 tracking-tight">
                                    Kritik Stoklar
                                </h3>
                                <p className="text-[12px] sm:text-[13px] font-medium text-slate-400 mt-0.5">
                                    Acil tedarik bekleyen ürünler
                                </p>
                            </div>

                            {/* Count badge */}
                            <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center border shadow-sm
                                ${kritikler.length > 0
                                    ? 'bg-gradient-to-br from-rose-50 to-rose-100 border-rose-100 text-rose-500'
                                    : 'bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-100 text-emerald-500'}`}>
                                <span className="text-[15px] font-black">{kritikler.length}</span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto dsh-scroll pr-1 -mr-1">
                            {kritikler.length > 0 ? (
                                <div className="space-y-2.5">
                                    {kritikler.map((urun, i) => (
                                        <KritikRow key={urun.id} urun={urun} index={i} />
                                    ))}
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center py-8">
                                    <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-3 dsh-float">
                                        <CheckCircle2 className="w-8 h-8 text-emerald-500" strokeWidth={2} />
                                    </div>
                                    <p className="text-[15px] font-black text-slate-800">Her Şey Yolunda!</p>
                                    <p className="text-[12px] font-medium text-slate-400 mt-1">
                                        Kritik seviyeye düşen ürün yok.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </RevealSection>
            </div>

            {/* ── Son Aktiviteler ── */}
            <RevealSection delay={300}>
                <div className="bg-white rounded-[24px] border border-slate-100/80 p-5 sm:p-7 shadow-sm
                                hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-500">

                    <div className="flex items-center gap-3.5 mb-5 sm:mb-6">
                        <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-indigo-50 to-indigo-100
                                        flex items-center justify-center border border-indigo-100 text-indigo-600">
                            <Clock className="w-5 h-5" strokeWidth={2.5} />
                        </div>
                        <div>
                            <h3 className="text-[18px] sm:text-[20px] font-black text-slate-800 tracking-tight">
                                Son Aktiviteler
                            </h3>
                            <p className="text-[12px] sm:text-[13px] font-medium text-slate-400 mt-0.5">
                                En son gerçekleşen {hareketler.length} hareket
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        {hareketler.map((h, i) => (
                            <HareketRow key={h.id} hareket={h} index={i} />
                        ))}
                        {hareketler.length === 0 && (
                            <div className="col-span-full py-14 text-center">
                                <div className="w-14 h-14 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3 dsh-float">
                                    <Box className="w-7 h-7 text-slate-300" />
                                </div>
                                <p className="text-[14px] font-bold text-slate-400">
                                    Henüz kaydedilmiş hareket yok.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </RevealSection>
        </div>
    );
}