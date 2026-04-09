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
        description: 'Gelen irsaliyeleri işle',
        icon: PackageCheck,
        to: '/depocu/mal-kabul',
        color: 'bg-emerald-50 text-emerald-600 border-emerald-100',
        iconBg: 'bg-emerald-100',
    },
    {
        label: 'Stok Sayımı',
        description: 'Fiziksel stok say',
        icon: ClipboardCheck,
        to: '/depocu/stok-sayim',
        color: 'bg-violet-50 text-violet-600 border-violet-100',
        iconBg: 'bg-violet-100',
    },
    {
        label: 'Stok Hareketi',
        description: 'Giriş / çıkış ekle',
        icon: ArrowLeftRight,
        to: '/depocu/stok',
        color: 'bg-sky-50 text-sky-600 border-sky-100',
        iconBg: 'bg-sky-100',
    },
    {
        label: 'Destek Talebi',
        description: 'Sorun bildir',
        icon: HelpCircle,
        to: '/depocu/destek',
        color: 'bg-amber-50 text-amber-600 border-amber-100',
        iconBg: 'bg-amber-100',
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
 * Dark slate / amber tema: TerminalLayout'u sezdirir, bilinçli mod geçişi.
 */
function TerminalModuKarti({ ozet, loading, onYenile, onNavigate }) {
    const bekleyen = ozet?.toplam_bekleyen ?? 0;
    const acil     = ozet?.acil ?? 0;

    return (
        <div className="bg-slate-800 rounded-2xl p-5 shadow-lg shadow-slate-800/20">
            {/* Başlık */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center shadow-sm shadow-amber-500/40">
                        <Scan className="w-4 h-4 text-white" strokeWidth={2.2} />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-white leading-tight">Saha Terminali</p>
                        <p className="text-[10px] text-slate-400 leading-none mt-0.5">Barkod tarama & görev akışı</p>
                    </div>
                </div>
                <button
                    onClick={onYenile}
                    disabled={loading}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-amber-400 hover:bg-slate-700 transition-colors disabled:opacity-40"
                    aria-label="Yenile"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Görev sayaçları */}
            {loading ? (
                <div className="flex gap-3 mb-4">
                    <div className="flex-1 h-16 bg-slate-700 rounded-xl animate-pulse" />
                    <div className="flex-1 h-16 bg-slate-700 rounded-xl animate-pulse" />
                </div>
            ) : (
                <div className="flex gap-3 mb-4">
                    <div className="flex-1 bg-slate-700/60 rounded-xl p-3 text-center border border-slate-700">
                        <p className="text-3xl font-black text-slate-100">{bekleyen}</p>
                        <p className="text-xs text-slate-400 font-medium mt-0.5">Bekleyen</p>
                    </div>
                    <div className={`flex-1 rounded-xl p-3 text-center border ${
                        acil > 0
                            ? 'bg-red-500/20 border-red-500/40'
                            : 'bg-slate-700/60 border-slate-700'
                    }`}>
                        <p className={`text-3xl font-black ${acil > 0 ? 'text-red-400' : 'text-slate-500'}`}>
                            {acil}
                        </p>
                        <div className="flex items-center justify-center gap-1 mt-0.5">
                            {acil > 0 && <AlertTriangle className="w-3 h-3 text-red-400" />}
                            <p className={`text-xs font-medium ${acil > 0 ? 'text-red-400' : 'text-slate-500'}`}>Acil</p>
                        </div>
                    </div>
                </div>
            )}

            {/* 3 hızlı giriş butonu */}
            <div className="flex gap-2 mb-3">
                {TERMINAL_GIRISLERI.map((g) => {
                    const GIcon = g.icon;
                    return (
                        <button
                            key={g.to}
                            onClick={() => onNavigate(g.to)}
                            className="flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl bg-slate-700 hover:bg-slate-600 active:bg-slate-500 transition-colors border border-slate-600"
                        >
                            <GIcon className="w-4 h-4 text-amber-400" strokeWidth={2} />
                            <span className="text-[10px] font-semibold text-slate-300 leading-none text-center">
                                {g.label}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Ana CTA */}
            <button
                onClick={() => onNavigate('/terminal/gorevler')}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-slate-900 font-black text-sm transition-colors shadow-md shadow-amber-500/30"
            >
                <span>Sahaya Çık</span>
                <ArrowRight className="w-4 h-4" />
            </button>
        </div>
    );
}

function QuickActionKarti({ action, onClick }) {
    const Icon = action.icon;
    return (
        <button
            onClick={() => onClick(action.to)}
            className={`flex flex-col items-start gap-3 p-4 rounded-2xl border bg-white shadow-sm hover:shadow-md active:scale-[0.98] transition-all text-left ${action.color}`}
        >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${action.iconBg}`}>
                <Icon className="w-5 h-5" strokeWidth={2} />
            </div>
            <div>
                <p className="text-sm font-bold leading-tight">{action.label}</p>
                <p className="text-xs opacity-70 mt-0.5 leading-tight">{action.description}</p>
            </div>
        </button>
    );
}

export default function DepocuAnaSayfasi() {
    const { user } = useAuth();
    const navigate = useNavigate();
    // loading=true başlangıçta, yenile butonunda onClick'te true yapılır.
    // Effect body'de senkron setState yok — tüm state güncellemeleri Promise callback'inde.
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

    return (
        <div className="p-4 space-y-5 max-w-lg mx-auto pt-5">
            {/* Selam */}
            <div>
                <p className="text-slate-500 text-sm">{selamMetni()},</p>
                <h1 className="text-2xl font-black text-slate-800 leading-tight">
                    {user?.ad_soyad?.split(' ')[0] || 'Operatör'}
                </h1>
            </div>

            {/* Terminal Modu — ana öne çıkan kart */}
            <TerminalModuKarti
                ozet={ozet}
                loading={loading}
                onYenile={handleYenile}
                onNavigate={(to) => navigate(to)}
            />

            {/* Quick Actions */}
            <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-1">
                    Hızlı İşlemler
                </p>
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
