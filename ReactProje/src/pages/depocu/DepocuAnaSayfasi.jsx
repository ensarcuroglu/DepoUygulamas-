/**
 * DepocuAnaSayfasi — Depo operatörü görev odaklı ana sayfa.
 *
 * Sektör standardı (WMS task-driven UX):
 * - Görev kuyruğu önce: "ne yapmalıyım?" sorusunu yanıtlar
 * - Quick action kartları: sık kullanılan işlemler tek tıkla
 * - Menü yok; navigasyon bottom tab bar üzerinden
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    AlertTriangle,
    PackageCheck,
    ArrowLeftRight,
    ClipboardCheck,
    HelpCircle,
    ArrowRight,
    RefreshCw,
    Scan,
    ClipboardList,
    BarChart2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { getBekleyenGorevOzet } from '../../services/api';
import { hataMetni } from '../../utils/hata';

const QUICK_ACTIONS = [
    {
        label: 'Mal Kabul',
        description: 'İrsaliye İşlemleri',
        icon: PackageCheck,
        to: '/depocu/mal-kabul',
        color: 'text-emerald-600',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20'
    },
    {
        label: 'Stok Sayım',
        description: 'Fiziksel Sayım',
        icon: ClipboardCheck,
        to: '/depocu/stok-sayim',
        color: 'text-violet-600',
        bg: 'bg-violet-500/10',
        border: 'border-violet-500/20'
    },
    {
        label: 'Stok Hareketi',
        description: 'Giriş / Çıkış',
        icon: ArrowLeftRight,
        to: '/depocu/stok',
        color: 'text-sky-600',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/20'
    },
    {
        label: 'Destek',
        description: 'Sorun Bildir',
        icon: HelpCircle,
        to: '/depocu/destek',
        color: 'text-amber-600',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/20'
    },
];

// Terminal giriş noktaları — saha tabletinde dark TerminalLayout açılır
const TERMINAL_GIRISLERI = [
    { label: 'Görev Listesi', icon: ClipboardList, to: '/terminal/gorevler' },
    { label: 'Yerleştir',     icon: Scan,          to: '/terminal/yerlestirme' },
    { label: 'Günlük Özet',   icon: BarChart2,     to: '/terminal/ozet' },
];

/**
 * TerminalModuKarti — Ana ekrandaki öne çıkan terminal giriş kartı.
 * Dark slate / amber tema: Premium ve odaklayıcı bir arayüz.
 */
function TerminalModuKarti({ ozet, loading, onYenile, onNavigate }) {
    const bekleyen = ozet?.toplam_bekleyen ?? 0;
    const acil     = ozet?.acil ?? 0;
    const hasAcil  = acil > 0;

    return (
        <div className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-[24px] p-5 shadow-xl shadow-slate-900/20 border border-slate-700/50">
            {/* Arka plan parlama efekti */}
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/20 rounded-full blur-3xl pointer-events-none" />

            {/* Başlık ve Yenile */}
            <div className="relative flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-[14px] bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center shadow-lg shadow-amber-500/30">
                        <Scan className="w-5 h-5 text-white" strokeWidth={2.5} />
                    </div>
                    <div>
                        <h2 className="text-base font-extrabold text-white tracking-tight">Saha Terminali</h2>
                        <p className="text-[11px] font-medium text-slate-400 mt-0.5">Barkod okuma & saha akışı</p>
                    </div>
                </div>
                <button
                    onClick={onYenile}
                    disabled={loading}
                    className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-800/50 text-slate-400 hover:text-amber-400 border border-slate-700/50 transition-all active:scale-90 disabled:opacity-50"
                    aria-label="Yenile"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-400' : ''}`} />
                </button>
            </div>

            {/* İstatistikler */}
            {loading ? (
                <div className="relative flex gap-3 mb-5">
                    <div className="flex-1 h-[88px] bg-slate-800/80 rounded-2xl animate-pulse border border-slate-700/50" />
                    <div className="flex-1 h-[88px] bg-slate-800/80 rounded-2xl animate-pulse border border-slate-700/50" />
                </div>
            ) : (
                <div className="relative flex gap-3 mb-5">
                    {/* Bekleyen Görevler */}
                    <div className="flex-1 bg-slate-800/50 backdrop-blur-sm rounded-2xl p-4 flex flex-col justify-center border border-slate-700/50">
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Bekleyen</span>
                        <p className="text-3xl font-black text-white">{bekleyen}</p>
                    </div>

                    {/* Acil Görevler */}
                    <div className={`flex-1 backdrop-blur-sm rounded-2xl p-4 flex flex-col justify-center border transition-colors ${
                        hasAcil 
                        ? 'bg-red-500/10 border-red-500/30' 
                        : 'bg-slate-800/50 border-slate-700/50'
                    }`}>
                        <div className="flex items-center gap-1.5 mb-1">
                            {hasAcil && (
                                <span className="relative flex h-2.5 w-2.5">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                                </span>
                            )}
                            <span className={`text-[11px] font-bold uppercase tracking-wider ${hasAcil ? 'text-red-400' : 'text-slate-400'}`}>
                                Acil
                            </span>
                        </div>
                        <p className={`text-3xl font-black ${hasAcil ? 'text-white' : 'text-slate-500'}`}>
                            {acil}
                        </p>
                    </div>
                </div>
            )}

            {/* 3 Hızlı Giriş */}
            <div className="relative grid grid-cols-3 gap-2 mb-5">
                {TERMINAL_GIRISLERI.map((g) => {
                    const GIcon = g.icon;
                    return (
                        <button
                            key={g.to}
                            onClick={() => onNavigate(g.to)}
                            className="flex flex-col items-center justify-center gap-2 py-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700/50 transition-all active:scale-95"
                        >
                            <GIcon className="w-5 h-5 text-amber-400/90" strokeWidth={2} />
                            <span className="text-[10px] font-bold text-slate-300">
                                {g.label}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Ana Eylem Butonu */}
            <button
                onClick={() => onNavigate('/terminal/gorevler')}
                className="relative w-full flex items-center justify-center gap-2 py-4 rounded-[16px] bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-slate-900 font-black text-[15px] transition-all active:scale-[0.98] shadow-[0_8px_20px_-6px_rgba(245,158,11,0.5)]"
            >
                <span>Saha Modunu Başlat</span>
                <ArrowRight className="w-5 h-5" />
            </button>
        </div>
    );
}

// Yeni Quick Action Kartı (Bento Box Tarzı)
function QuickActionKarti({ action, onClick }) {
    const Icon = action.icon;
    return (
        <button
            onClick={() => onClick(action.to)}
            className="group relative flex flex-col items-start p-4 rounded-[20px] bg-white border border-slate-200/60 shadow-sm hover:shadow-md transition-all active:scale-[0.96] text-left overflow-hidden"
        >
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110 ${action.bg} ${action.color}`}>
                <Icon className="w-6 h-6" strokeWidth={2} />
            </div>
            <div>
                <p className="text-[15px] font-extrabold text-slate-800 leading-tight mb-0.5">{action.label}</p>
                <p className="text-[11px] font-medium text-slate-500 leading-tight">{action.description}</p>
            </div>
            {/* Sağ alt köşe ok ikonu (Kullanıcıyı yönlendirmeye teşvik eder) */}
            <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all">
                <ArrowRight className="w-4 h-4 text-slate-300" />
            </div>
        </button>
    );
}

export default function DepocuAnaSayfasi() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [ozet, setOzet] = useState(null);

    const yukle = useCallback(() =>
        getBekleyenGorevOzet()
            .then((res) => setOzet(res.data))
            .catch((err) => toast.error(hataMetni(err, 'Görev özeti yüklenemedi')))
            .finally(() => setLoading(false))
    , []);

    useEffect(() => { void yukle(); }, [yukle]);

    const handleYenile = () => {
        setLoading(true);
        void yukle();
    };

    const selamMetni = () => {
        const saat = new Date().getHours();
        if (saat < 12) return 'Günaydın';
        if (saat < 18) return 'İyi günler';
        return 'İyi akşamlar';
    };

    // Mevcut tarihi formatlama (Örn: 14 Kasım Perşembe)
    const tarihMetni = new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', weekday: 'long' }).format(new Date());

    return (
        <div className="p-4 sm:p-6 space-y-6 max-w-lg mx-auto">
            
            {/* Karşılama Alanı */}
            <div className="flex justify-between items-end mt-2">
                <div>
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-200/50 text-slate-600 text-[10px] font-bold uppercase tracking-wider mb-2">
                        {tarihMetni}
                    </div>
                    <h1 className="text-2xl font-black text-slate-800 tracking-tight leading-none">
                        {selamMetni()}, <span className="text-sky-600">{user?.ad_soyad?.split(' ')[0] || 'Operatör'}</span>
                    </h1>
                </div>
            </div>

            {/* Ana Odak: Terminal Modu */}
            <TerminalModuKarti
                ozet={ozet}
                loading={loading}
                onYenile={handleYenile}
                onNavigate={(to) => navigate(to)}
            />

            {/* Hızlı İşlemler Grid */}
            <div>
                <div className="flex items-center justify-between mb-3 px-1">
                    <h3 className="text-sm font-extrabold text-slate-800 tracking-tight">
                        Hızlı İşlemler
                    </h3>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    {QUICK_ACTIONS.map((action) => (
                        <QuickActionKarti
                            key={action.to}
                            action={action}
                            onClick={(to) => navigate(to)}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}