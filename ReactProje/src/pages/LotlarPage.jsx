import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    Layers, Search, X, AlertTriangle, ChevronLeft, ChevronRight,
    Hash, Calendar, Trash2, SlidersHorizontal, RotateCcw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getLotlar, deleteLot, getSktYaklasanLotlar, getMarkalar } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

/* ─── Animations (injected once) ─── */
const STYLE_ID = 'lotlar-v2-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
    const s = document.createElement('style');
    s.id = STYLE_ID;
    s.textContent = `
        @keyframes lotV2FadeUp {
            from { opacity:0; transform:translateY(10px) }
            to   { opacity:1; transform:translateY(0) }
        }
        @keyframes lotV2Shimmer {
            0%   { background-position:-200% 0 }
            100% { background-position:200% 0 }
        }
        @keyframes lotV2Pulse {
            0%,100% { opacity:1 }
            50%     { opacity:.5 }
        }
        .lotv2-enter   { animation: lotV2FadeUp .32s cubic-bezier(.22,1,.36,1) both }
        .lotv2-shimmer { background:linear-gradient(90deg,#f1f5f9 25%,#e2e8f0 50%,#f1f5f9 75%); background-size:200% 100%; animation:lotV2Shimmer 1.4s ease infinite; border-radius:8px }
        .lotv2-pulse   { animation: lotV2Pulse 2s ease-in-out infinite }
    `;
    document.head.appendChild(s);
}

/* ─── Swipe Hook ─── */
function useSwipe(onSwipeLeft, threshold = 60) {
    const ref = useRef(null);
    const start = useRef(0);
    const cur = useRef(0);
    const active = useRef(false);
    const [revealed, setRevealed] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const ts = (e) => { start.current = e.touches[0].clientX; cur.current = start.current; active.current = true; el.style.transition = 'none'; };
        const tm = (e) => { if (!active.current) return; cur.current = e.touches[0].clientX; const d = start.current - cur.current; if (d > 0) el.style.transform = `translateX(${-Math.min(d, 88)}px)`; };
        const te = () => { active.current = false; const d = start.current - cur.current; el.style.transition = 'transform .28s cubic-bezier(.22,1,.36,1)'; if (d > threshold) { el.style.transform = 'translateX(-80px)'; setRevealed(true); onSwipeLeft?.(); } else { el.style.transform = 'translateX(0)'; setRevealed(false); } };
        el.addEventListener('touchstart', ts, { passive: true });
        el.addEventListener('touchmove', tm, { passive: true });
        el.addEventListener('touchend', te, { passive: true });
        return () => { el.removeEventListener('touchstart', ts); el.removeEventListener('touchmove', tm); el.removeEventListener('touchend', te); };
    }, [onSwipeLeft, threshold]);

    const reset = useCallback(() => {
        if (ref.current) { ref.current.style.transition = 'transform .28s cubic-bezier(.22,1,.36,1)'; ref.current.style.transform = 'translateX(0)'; }
        setRevealed(false);
    }, []);

    return { ref, revealed, reset };
}

/* ─── SKT helpers ─── */
function getSktInfo(skt) {
    if (!skt) return null;
    const days = Math.ceil((new Date(skt) - new Date()) / 864e5);
    if (days < 0) return { days, label: 'Süresi doldu', level: 'expired' };
    if (days <= 30) return { days, label: `${days}g`, level: 'critical' };
    if (days <= 90) return { days, label: `${days}g`, level: 'warning' };
    return { days, label: `${days}g`, level: 'safe' };
}

const sktColors = {
    expired:  { dot: 'bg-red-500', text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
    critical: { dot: 'bg-red-500', text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
    warning:  { dot: 'bg-amber-500', text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
    safe:     { dot: 'bg-emerald-500', text: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200' },
};

const SKT_FILTER_OPTIONS = [
    { key: 'expired', label: 'Süresi Dolmuş', dot: 'bg-red-500', activeBg: 'bg-red-50 border-red-300 text-red-700' },
    { key: 'critical', label: 'Kritik (<30g)', dot: 'bg-red-400', activeBg: 'bg-red-50 border-red-300 text-red-700' },
    { key: 'warning', label: 'Uyarı (<90g)', dot: 'bg-amber-500', activeBg: 'bg-amber-50 border-amber-300 text-amber-700' },
    { key: 'safe', label: 'Güvenli', dot: 'bg-emerald-500', activeBg: 'bg-emerald-50 border-emerald-300 text-emerald-700' },
];

/* ─── Minimal SKT Badge ─── */
function SktBadge({ skt, size = 'sm' }) {
    const info = getSktInfo(skt);
    if (!info) return <span className="text-[11px] text-slate-300">—</span>;
    const c = sktColors[info.level];
    const isSm = size === 'sm';
    return (
        <span className={`inline-flex items-center gap-1.5 ${isSm ? 'text-[11px]' : 'text-[12px]'} font-bold ${c.text}`}>
            <span className={`${isSm ? 'w-1.5 h-1.5' : 'w-2 h-2'} rounded-full ${c.dot} ${info.level === 'critical' || info.level === 'expired' ? 'lotv2-pulse' : ''}`} />
            {info.label}
        </span>
    );
}

/* ─── Mobile Card ─── */
function LotCard({ lot, formatDate, onDelete, index }) {
    const { ref, revealed, reset } = useSwipe(() => {});
    const info = getSktInfo(lot.son_kullanma_tarihi);
    const c = info ? sktColors[info.level] : null;
    const isUrgent = info && (info.level === 'critical' || info.level === 'expired');

    return (
        <div className="relative lotv2-enter overflow-hidden rounded-2xl" style={{ animationDelay: `${index * 35}ms` }}>
            <div className="absolute inset-y-0 right-0 w-20 bg-red-500 flex items-center justify-center rounded-r-2xl">
                <button onClick={() => { reset(); onDelete(lot.id); }} className="flex flex-col items-center gap-0.5">
                    <Trash2 className="w-4 h-4 text-white" />
                    <span className="text-[10px] font-bold text-white/90">Pasif</span>
                </button>
            </div>
            <div ref={ref} className={`relative bg-white border rounded-2xl p-4 active:bg-slate-50/50 transition-colors z-10
                ${isUrgent ? `${c.border} border-l-[3px]` : 'border-slate-200/80'}`}>
                {revealed && <div className="absolute inset-0 z-20 rounded-2xl" onClick={() => reset()} />}
                <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex-1 min-w-0">
                        <p className="text-[15px] font-bold text-slate-800 leading-snug truncate">
                            {lot.urun?.isim || `Ürün #${lot.urun_id}`}
                        </p>
                        {lot.urun?.marka?.isim && (
                            <p className="text-[12px] text-slate-400 mt-0.5 truncate">{lot.urun.marka.isim}</p>
                        )}
                    </div>
                    {info && (
                        <span className={`shrink-0 inline-flex items-center gap-1.5 text-[11px] font-extrabold px-2.5 py-1 rounded-full ${c.bg} ${c.text} ${c.border} border
                            ${isUrgent ? 'lotv2-pulse' : ''}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
                            {info.label}
                        </span>
                    )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-slate-500 bg-slate-50 border border-slate-100 rounded-lg px-2.5 py-1">
                        <Hash className="w-3 h-3 text-slate-400" />
                        <span className="truncate max-w-[120px]">{lot.lot_no}</span>
                    </span>
                    {lot.parti_no && (
                        <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-slate-500 bg-slate-50 border border-slate-100 rounded-lg px-2.5 py-1">
                            P: {lot.parti_no}
                        </span>
                    )}
                    {lot.son_kullanma_tarihi && (
                        <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-slate-500 bg-slate-50 border border-slate-100 rounded-lg px-2.5 py-1">
                            <Calendar className="w-3 h-3 text-slate-400" />
                            {formatDate(lot.son_kullanma_tarihi)}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

/* ─── Desktop Table Row ─── */
function DesktopRow({ lot, formatDate, onDelete, index }) {
    return (
        <tr className="lotv2-enter hover:bg-amber-50/30 transition-colors duration-150 group" style={{ animationDelay: `${index * 30}ms` }}>
            <td className="px-5 py-4">
                <p className="text-[14px] font-bold text-slate-800">{lot.urun?.isim || `Urun #${lot.urun_id}`}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">{lot.urun?.marka?.isim || ''}</p>
            </td>
            <td className="px-5 py-4">
                <code className="text-[12px] font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">{lot.lot_no}</code>
            </td>
            <td className="px-5 py-4 hidden lg:table-cell">
                <span className="text-[13px] text-slate-600">{lot.parti_no || '—'}</span>
            </td>
            <td className="px-5 py-4 hidden lg:table-cell">
                <span className="text-[13px] text-slate-600">{formatDate(lot.uretim_tarihi)}</span>
            </td>
            <td className="px-5 py-4">
                <div className="flex items-center gap-2.5">
                    <span className="text-[13px] font-medium text-slate-700">{formatDate(lot.son_kullanma_tarihi)}</span>
                    <SktBadge skt={lot.son_kullanma_tarihi} size="md" />
                </div>
            </td>
            <td className="px-5 py-4 text-right">
                <button onClick={() => onDelete(lot.id)}
                    className="text-[12px] font-bold text-slate-400 hover:text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100">
                    Pasife Al
                </button>
            </td>
        </tr>
    );
}

/* ─── Shimmer Skeletons ─── */
function ShimmerCard() {
    return (
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 space-y-3">
            <div className="flex justify-between items-start">
                <div className="space-y-2 flex-1"><div className="h-4 lotv2-shimmer w-32" /><div className="h-3 lotv2-shimmer w-20" /></div>
                <div className="h-6 lotv2-shimmer w-14 rounded-full" />
            </div>
            <div className="flex gap-2"><div className="h-7 lotv2-shimmer w-24 rounded-lg" /><div className="h-7 lotv2-shimmer w-20 rounded-lg" /></div>
        </div>
    );
}
function ShimmerRow() {
    return (
        <tr>
            <td className="px-5 py-4"><div className="h-4 lotv2-shimmer w-28" /></td>
            <td className="px-5 py-4"><div className="h-4 lotv2-shimmer w-24" /></td>
            <td className="px-5 py-4 hidden lg:table-cell"><div className="h-4 lotv2-shimmer w-16" /></td>
            <td className="px-5 py-4 hidden lg:table-cell"><div className="h-4 lotv2-shimmer w-20" /></td>
            <td className="px-5 py-4"><div className="h-4 lotv2-shimmer w-20" /></td>
            <td className="px-5 py-4"><div className="h-4 lotv2-shimmer w-14" /></td>
        </tr>
    );
}

/* ─── Empty State ─── */
function EmptyState({ hasFilters, query }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 sm:py-20 text-center px-6">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-slate-200/60 flex items-center justify-center mb-4">
                {hasFilters ? <Search className="w-6 h-6 text-slate-300" /> : <Layers className="w-6 h-6 text-slate-300" />}
            </div>
            <p className="text-[15px] font-bold text-slate-600">{hasFilters ? 'Sonuç bulunamadı' : 'Kayıtlı LOT bulunamadı'}</p>
            <p className="text-[13px] text-slate-400 mt-1.5 max-w-[240px]">
                {hasFilters
                    ? query ? `"${query}" ile eşleşen kayıt yok` : 'Seçili filtrelere uygun kayıt bulunamadı'
                    : 'Henüz LOT kaydedilmemiş'}
            </p>
        </div>
    );
}

/* ─── Form class constants ─── */
const INPUT_CLS = `w-full h-10 px-3 text-[13px] font-medium rounded-xl border border-slate-200 bg-white
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-[3px] focus:ring-amber-500/10
    focus:border-amber-400 transition-all duration-200`;
const LABEL_CLS = "text-[10px] font-extrabold text-slate-400 mb-1.5 block tracking-widest uppercase";

/* ─── Filter Chip (active filters bar) ─── */
function ActiveFilterChip({ label, onRemove }) {
    return (
        <span className="inline-flex items-center gap-1.5 text-[11px] sm:text-[12px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1 lotv2-enter">
            {label}
            <button onClick={onRemove} className="w-4 h-4 rounded-full bg-amber-200/60 hover:bg-amber-300 flex items-center justify-center transition-colors">
                <X className="w-2.5 h-2.5 text-amber-700" />
            </button>
        </span>
    );
}

/* ─── Main Page ─── */
export default function LotlarPage() {
    const [lotlar, setLotlar] = useState([]);
    const [markalar, setMarkalar] = useState([]);
    const [totalCount, setTotalCount] = useState(0);
    const { loading, run } = useAsync(true);
    const [sktLotlar, setSktLotlar] = useState([]);
    const [page, setPage] = useState(0);
    const limit = 20;

    /* Filter states */
    const [filterOpen, setFilterOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedMarka, setSelectedMarka] = useState('');
    const [sktFilters, setSktFilters] = useState([]);
    const [tarihTuru, setTarihTuru] = useState('skt');
    const [tarihBaslangic, setTarihBaslangic] = useState('');
    const [tarihBitis, setTarihBitis] = useState('');
    const [tab, setTab] = useState('tumu');

    const searchRef = useRef(null);

    const refreshData = useCallback(async () => {
        try {
            const [lotRes, sktRes] = await run(() => Promise.all([
                getLotlar({ skip: page * limit, limit }),
                getSktYaklasanLotlar(60)
            ]));
            setLotlar(lotRes.data);
            setTotalCount(Number(lotRes.headers?.['x-total-count'] || 0));
            setSktLotlar(sktRes.data);
        } catch {
            toast.error('Veriler yüklenemedi');
        }
    }, [run, page, limit]);

    useEffect(() => {
        let aktif = true;
        run(() => Promise.all([
            getLotlar({ skip: page * limit, limit }),
            getSktYaklasanLotlar(60)
        ]))
            .then(([lotRes, sktRes]) => {
                if (!aktif) return;
                setLotlar(lotRes.data);
                setTotalCount(Number(lotRes.headers?.['x-total-count'] || 0));
                setSktLotlar(sktRes.data);
            })
            .catch(() => {
                if (aktif) {
                    toast.error('Veriler yüklenemedi');
                }
            });
        return () => {
            aktif = false;
        };
    }, [run, page, limit]);
    useEffect(() => {
        getMarkalar()
            .then(res => setMarkalar(res.data))
            .catch(() => {
                toast.error('Marka listesi yüklenemedi');
            });
    }, []);
    useEffect(() => {
        if (filterOpen && searchRef.current) searchRef.current.focus();
    }, [filterOpen]);

    const handleDelete = useCallback(async (id) => {
        if (!confirm('Bu LOT kaydını pasife almak istiyor musunuz?')) return;
        try { await deleteLot(id); toast.success('LOT pasife alındı'); refreshData(); }
        catch (err) { toast.error(hataMetni(err, 'LOT pasife alınamadı')); }
    }, [refreshData]);

    const formatDate = useCallback((d) => d ? new Date(d).toLocaleDateString('tr-TR') : '—', []);

    const toggleSktFilter = (key) => {
        setSktFilters(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
    };

    const clearAllFilters = () => {
        setSearchQuery('');
        setSelectedMarka('');
        setSktFilters([]);
        setTarihBaslangic('');
        setTarihBitis('');
        setTarihTuru('skt');
    };

    /* Active filter count */
    const activeFilterCount = useMemo(() => {
        let count = 0;
        if (searchQuery.trim()) count++;
        if (selectedMarka) count++;
        if (sktFilters.length > 0) count++;
        if (tarihBaslangic || tarihBitis) count++;
        return count;
    }, [searchQuery, selectedMarka, sktFilters, tarihBaslangic, tarihBitis]);

    /* Filter logic */
    const baseLotlar = tab === 'skt' ? sktLotlar : lotlar;
    const displayLotlar = useMemo(() => {
        let result = baseLotlar;

        // Text search
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            result = result.filter(lot =>
                (lot.urun?.isim || '').toLowerCase().includes(q) ||
                (lot.lot_no || '').toLowerCase().includes(q) ||
                (lot.parti_no || '').toLowerCase().includes(q) ||
                (lot.urun?.marka?.isim || '').toLowerCase().includes(q)
            );
        }

        // Marka filter
        if (selectedMarka) {
            result = result.filter(lot => lot.urun?.marka?.id === Number(selectedMarka));
        }

        // SKT status filter
        if (sktFilters.length > 0) {
            result = result.filter(lot => {
                const info = getSktInfo(lot.son_kullanma_tarihi);
                return info && sktFilters.includes(info.level);
            });
        }

        // Date range filter
        if (tarihBaslangic || tarihBitis) {
            const dateField = tarihTuru === 'uretim' ? 'uretim_tarihi' : 'son_kullanma_tarihi';
            const startDate = tarihBaslangic ? new Date(tarihBaslangic) : null;
            const endDate = tarihBitis ? new Date(tarihBitis + 'T23:59:59') : null;
            result = result.filter(lot => {
                const val = lot[dateField];
                if (!val) return false;
                const d = new Date(val);
                if (startDate && d < startDate) return false;
                if (endDate && d > endDate) return false;
                return true;
            });
        }

        return result;
    }, [baseLotlar, searchQuery, selectedMarka, sktFilters, tarihTuru, tarihBaslangic, tarihBitis]);

    const hasFilters = activeFilterCount > 0;
    const toplamSayfa = Math.max(1, Math.ceil(totalCount / limit));
    const canNextPage = page + 1 < toplamSayfa;

    /* Active filter labels for chips */
    const activeFilterChips = useMemo(() => {
        const chips = [];
        if (searchQuery.trim()) {
            chips.push({ key: 'search', label: `Arama: "${searchQuery}"`, clear: () => setSearchQuery('') });
        }
        if (selectedMarka) {
            const marka = markalar.find(item => item.id === Number(selectedMarka));
            chips.push({ key: 'marka', label: `Marka: ${marka?.isim || selectedMarka}`, clear: () => setSelectedMarka('') });
        }
        if (sktFilters.length > 0) {
            const labels = sktFilters.map(k => SKT_FILTER_OPTIONS.find(o => o.key === k)?.label).filter(Boolean);
            chips.push({ key: 'skt', label: `SKT: ${labels.join(', ')}`, clear: () => setSktFilters([]) });
        }
        if (tarihBaslangic || tarihBitis) {
            const parts = [];
            if (tarihBaslangic) parts.push(new Date(tarihBaslangic).toLocaleDateString('tr-TR'));
            if (tarihBitis) parts.push(new Date(tarihBitis).toLocaleDateString('tr-TR'));
            const fieldLabel = tarihTuru === 'uretim' ? 'Üretim' : 'SKT';
            chips.push({
                key: 'tarih',
                label: `${fieldLabel}: ${parts.join(' - ')}`,
                clear: () => { setTarihBaslangic(''); setTarihBitis(''); }
            });
        }
        return chips;
    }, [searchQuery, selectedMarka, sktFilters, tarihBaslangic, tarihBitis, tarihTuru, markalar]);

    return (
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-4 sm:py-6 space-y-4 sm:space-y-5">

            {/* ════ Header ════ */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-amber-100 to-amber-50 border border-amber-200/80 flex items-center justify-center shadow-sm">
                        <Layers className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                        <h2 className="text-[16px] sm:text-[17px] font-extrabold text-slate-800 leading-tight">LOT Takibi</h2>
                        <p className="text-[11px] sm:text-[12px] font-medium text-slate-400 mt-0.5 hidden sm:block">Üretim partileri ve SKT yönetimi</p>
                    </div>
                </div>
            </div>

            {/* ════ Tab + Filter Toggle ════ */}
            <div className="flex items-center gap-2">
                <div className="flex bg-slate-100 rounded-xl p-0.5 border border-slate-200/80 flex-1 sm:flex-none">
                    <button onClick={() => setTab('tumu')}
                        className={`flex-1 sm:flex-none px-4 py-2 rounded-[10px] text-[13px] font-bold transition-all duration-200
                            ${tab === 'tumu' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'}`}>
                        Tümü
                    </button>
                    <button onClick={() => setTab('skt')}
                        className={`flex-1 sm:flex-none px-4 py-2 rounded-[10px] text-[13px] font-bold transition-all duration-200 flex items-center justify-center gap-1.5
                            ${tab === 'skt' ? 'bg-white text-red-600 shadow-sm' : 'text-slate-500'}`}>
                        <AlertTriangle className="w-3.5 h-3.5" />
                        SKT
                        {sktLotlar.length > 0 && (
                            <span className="bg-red-500 text-white text-[9px] font-bold min-w-[18px] h-[18px] flex items-center justify-center px-1 rounded-full">{sktLotlar.length}</span>
                        )}
                    </button>
                </div>

                <button
                    onClick={() => setFilterOpen(!filterOpen)}
                    className={`relative h-10 px-3 sm:px-4 rounded-xl border flex items-center gap-2 shrink-0 transition-all duration-200 text-[13px] font-bold
                        ${filterOpen || hasFilters
                            ? 'bg-amber-50 border-amber-200 text-amber-700'
                            : 'bg-white border-slate-200 text-slate-500 hover:text-amber-600 hover:border-amber-300'}`}>
                    <SlidersHorizontal className="w-4 h-4" />
                    <span className="hidden sm:inline">Filtreler</span>
                    {activeFilterCount > 0 && (
                        <span className="absolute -top-1.5 -right-1.5 bg-amber-500 text-white text-[9px] font-bold w-5 h-5 flex items-center justify-center rounded-full shadow-sm">
                            {activeFilterCount}
                        </span>
                    )}
                </button>
            </div>

            {/* ════ Filter Panel ════ */}
            <div
                className="overflow-hidden transition-all duration-300 ease-out"
                style={{ maxHeight: filterOpen ? 600 : 0, opacity: filterOpen ? 1 : 0 }}
            >
                <div className="bg-white border border-slate-200/80 rounded-2xl p-4 sm:p-5 space-y-4 shadow-sm">
                    {/* Row 1: Search + Marka */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label className={LABEL_CLS}>Arama</label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <input
                                    ref={searchRef}
                                    type="text"
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    placeholder="Ürün, LOT no, parti no veya marka..."
                                    className={`${INPUT_CLS} pl-9 pr-9`}
                                />
                                {searchQuery && (
                                    <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center transition-colors">
                                        <X className="w-3 h-3 text-slate-500" />
                                    </button>
                                )}
                            </div>
                        </div>
                        <div>
                            <label className={LABEL_CLS}>Marka</label>
                            <select
                                value={selectedMarka}
                                onChange={e => setSelectedMarka(e.target.value)}
                                className={`${INPUT_CLS} appearance-none`}
                            >
                                <option value="">Tüm markalar</option>
                                {markalar.map(m => <option key={m.id} value={m.id}>{m.isim}</option>)}
                            </select>
                        </div>
                    </div>

                    {/* Row 2: SKT Status Chips */}
                    <div>
                        <label className={LABEL_CLS}>SKT Durumu</label>
                        <div className="flex flex-wrap gap-2">
                            {SKT_FILTER_OPTIONS.map(opt => {
                                const isActive = sktFilters.includes(opt.key);
                                return (
                                    <button
                                        key={opt.key}
                                        onClick={() => toggleSktFilter(opt.key)}
                                        className={`inline-flex items-center gap-1.5 text-[12px] font-semibold px-3 py-1.5 rounded-lg border transition-all duration-200
                                            ${isActive
                                                ? opt.activeBg
                                                : 'bg-slate-50 border-slate-200 text-slate-500 hover:border-slate-300'}`}
                                    >
                                        <span className={`w-2 h-2 rounded-full ${opt.dot}`} />
                                        {opt.label}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Row 3: Date Range */}
                    <div>
                        <label className={LABEL_CLS}>Tarih Aralığı</label>
                        <div className="flex flex-col sm:flex-row items-start sm:items-end gap-3">
                            <div className="flex bg-slate-100 rounded-lg p-0.5 border border-slate-200/80 shrink-0">
                                <button
                                    onClick={() => setTarihTuru('skt')}
                                    className={`px-3 py-1.5 rounded-md text-[12px] font-bold transition-all duration-200
                                        ${tarihTuru === 'skt' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'}`}
                                >
                                    SKT
                                </button>
                                <button
                                    onClick={() => setTarihTuru('uretim')}
                                    className={`px-3 py-1.5 rounded-md text-[12px] font-bold transition-all duration-200
                                        ${tarihTuru === 'uretim' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'}`}
                                >
                                    Üretim
                                </button>
                            </div>
                            <div className="flex items-center gap-2 flex-1 w-full sm:w-auto">
                                <input
                                    type="date"
                                    value={tarihBaslangic}
                                    onChange={e => setTarihBaslangic(e.target.value)}
                                    className={`${INPUT_CLS} flex-1`}
                                />
                                <span className="text-[12px] font-bold text-slate-300 shrink-0">-</span>
                                <input
                                    type="date"
                                    value={tarihBitis}
                                    onChange={e => setTarihBitis(e.target.value)}
                                    className={`${INPUT_CLS} flex-1`}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Filter actions */}
                    {hasFilters && (
                        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                            <p className="text-[12px] text-slate-400 font-medium">
                                {displayLotlar.length} sonuç bulundu
                            </p>
                            <button
                                onClick={clearAllFilters}
                                className="inline-flex items-center gap-1.5 text-[12px] font-bold text-slate-500 hover:text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-all duration-200"
                            >
                                <RotateCcw className="w-3.5 h-3.5" />
                                Temizle
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* ════ Active Filter Chips ════ */}
            {!filterOpen && activeFilterChips.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                    {activeFilterChips.map(chip => (
                        <ActiveFilterChip key={chip.key} label={chip.label} onRemove={chip.clear} />
                    ))}
                    <button
                        onClick={clearAllFilters}
                        className="text-[11px] font-bold text-slate-400 hover:text-red-500 px-2 py-1 rounded-lg hover:bg-red-50 transition-all duration-200"
                    >
                        Tümünü temizle
                    </button>
                </div>
            )}

            {/* ════ MOBILE: Cards ════ */}
            <div className="md:hidden space-y-2.5">
                {loading ? (
                    [...Array(4)].map((_, i) => <ShimmerCard key={i} />)
                ) : displayLotlar.length === 0 ? (
                    <div className="bg-white rounded-2xl border border-slate-200/80">
                        <EmptyState hasFilters={hasFilters} query={searchQuery} />
                    </div>
                ) : (
                    <>
                        <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1 px-1 pb-0.5">
                            <ChevronLeft className="w-3 h-3" /> Sola kaydırarak pasife alın
                        </p>
                        {displayLotlar.map((lot, i) => (
                            <LotCard key={lot.id} lot={lot} formatDate={formatDate} onDelete={handleDelete} index={i} />
                        ))}
                    </>
                )}
            </div>

            {/* ════ DESKTOP: Table ════ */}
            <div className="hidden md:block bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-slate-50/80 border-b border-slate-200/80">
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">Ürün</th>
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">LOT No</th>
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest hidden lg:table-cell">Parti</th>
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest hidden lg:table-cell">Üretim</th>
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">SKT</th>
                                <th className="px-5 py-3.5 text-[11px] font-extrabold text-slate-400 uppercase tracking-widest text-right">İşlem</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100/80">
                            {loading ? (
                                [...Array(5)].map((_, i) => <ShimmerRow key={i} />)
                            ) : displayLotlar.length === 0 ? (
                                <tr><td colSpan={6}><EmptyState hasFilters={hasFilters} query={searchQuery} /></td></tr>
                            ) : (
                                displayLotlar.map((lot, i) => <DesktopRow key={lot.id} lot={lot} formatDate={formatDate} onDelete={handleDelete} index={i} />)
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ════ Pagination ════ */}
            {tab === 'tumu' && (
                <div className="flex items-center justify-between px-1">
                    <p className="text-[12px] sm:text-[13px] text-slate-400 font-medium">
                        {hasFilters ? `${displayLotlar.length} sonuç` : `${displayLotlar.length} kayıt`}
                    </p>
                    <div className="flex items-center gap-1.5">
                        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                            className="h-9 w-9 rounded-xl bg-white border border-slate-200 text-slate-600 disabled:opacity-30 hover:border-amber-300 active:scale-95 transition-all duration-200 flex items-center justify-center">
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-[13px] font-bold text-amber-700 bg-amber-50 border border-amber-200/80 px-3 py-1.5 rounded-xl min-w-[36px] text-center">{page + 1}</span>
                        <button onClick={() => canNextPage && setPage(page + 1)} disabled={!canNextPage}
                            className="h-9 w-9 rounded-xl bg-white border border-slate-200 text-slate-600 disabled:opacity-30 hover:border-amber-300 active:scale-95 transition-all duration-200 flex items-center justify-center">
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
