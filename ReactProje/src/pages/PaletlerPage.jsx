import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    Container, X, Barcode, Search, MapPin, PackageOpen,
    LayoutGrid, Scale, Clock, Trash2, List, SlidersHorizontal,
    ArrowUpDown, ChevronDown, Package, Weight, Layers, TrendingUp,
    Filter, RotateCcw
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
    getPaletler, deletePalet, getLotlar, getPaletByBarkod
} from '../services/api';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

/* ═══════════════════════════════════════════
   STAT CARD — Compact KPI display
   ═══════════════════════════════════════════ */
function StatCard({ icon: IconComponent, label, value, color, suffix }) {
    const colorMap = {
        blue: 'from-blue-500 to-blue-600 shadow-blue-500/20',
        indigo: 'from-indigo-500 to-indigo-600 shadow-indigo-500/20',
        emerald: 'from-emerald-500 to-emerald-600 shadow-emerald-500/20',
        amber: 'from-amber-500 to-amber-600 shadow-amber-500/20',
    };

    return (
        <div className="bg-white rounded-2xl border border-slate-100 p-4 flex items-center gap-3 min-w-0 shadow-sm">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[color]} shadow-lg flex-shrink-0 flex items-center justify-center`}>
                {React.createElement(IconComponent, { className: 'w-5 h-5 text-white' })}
            </div>
            <div className="min-w-0">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">{label}</p>
                <p className="text-xl font-bold text-slate-900 leading-tight tabular-nums">
                    {value}{suffix && <span className="text-sm font-medium text-slate-400 ml-0.5">{suffix}</span>}
                </p>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   FILTER PANEL — Collapsible, mobile-friendly
   ═══════════════════════════════════════════ */
function FilterPanel({ filters, setFilters, lotlar, paletler, onReset }) {
    const uniqueVardiyalar = useMemo(() =>
        [...new Set(paletler.map(p => p.vardiya).filter(Boolean))],
        [paletler]
    );

    const uniqueRaflar = useMemo(() =>
        [...new Set(paletler.map(p => p.raf?.kod).filter(Boolean))],
        [paletler]
    );

    const chipBase = "h-8 px-3 rounded-lg text-xs font-semibold border transition-all cursor-pointer select-none";
    const chipActive = "bg-blue-50 border-blue-200 text-blue-700";
    const chipInactive = "bg-white border-slate-200 text-slate-600 hover:border-slate-300";

    const hasActiveFilters = filters.lot_id || filters.vardiya || filters.raf;

    return (
        <div className="bg-white rounded-2xl border border-slate-100 p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <Filter className="w-4 h-4 text-slate-400" />
                    Filtreler
                </div>
                {hasActiveFilters && (
                    <button onClick={onReset} className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors">
                        <RotateCcw className="w-3 h-3" /> Temizle
                    </button>
                )}
            </div>

            {/* Lot filter */}
            <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Lot</p>
                <div className="flex flex-wrap gap-1.5">
                    {lotlar.slice(0, 8).map(l => (
                        <button
                            key={l.id}
                            onClick={() => setFilters(f => ({ ...f, lot_id: f.lot_id === l.id ? '' : l.id }))}
                            className={`${chipBase} ${filters.lot_id === l.id ? chipActive : chipInactive}`}
                        >
                            {l.lot_no}
                        </button>
                    ))}
                </div>
            </div>

            {/* Vardiya filter */}
            {uniqueVardiyalar.length > 0 && (
                <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Vardiya</p>
                    <div className="flex flex-wrap gap-1.5">
                        {uniqueVardiyalar.map(v => (
                            <button
                                key={v}
                                onClick={() => setFilters(f => ({ ...f, vardiya: f.vardiya === v ? '' : v }))}
                                className={`${chipBase} ${filters.vardiya === v ? chipActive : chipInactive}`}
                            >
                                {v}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Raf filter */}
            {uniqueRaflar.length > 0 && (
                <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Raf</p>
                    <div className="flex flex-wrap gap-1.5">
                        <button
                            onClick={() => setFilters(f => ({ ...f, raf: f.raf === '__none__' ? '' : '__none__' }))}
                            className={`${chipBase} ${filters.raf === '__none__' ? chipActive : chipInactive}`}
                        >
                            Raf Yok
                        </button>
                        {uniqueRaflar.map(r => (
                            <button
                                key={r}
                                onClick={() => setFilters(f => ({ ...f, raf: f.raf === r ? '' : r }))}
                                className={`${chipBase} ${filters.raf === r ? chipActive : chipInactive}`}
                            >
                                {r}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════
   LIST VIEW — Compact table-like rows
   ═══════════════════════════════════════════ */
function PaletListView({ paletler, onDelete }) {
    return (
        <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
            {/* Desktop table header */}
            <div className="hidden sm:grid sm:grid-cols-[1fr_1.2fr_0.7fr_0.7fr_0.8fr_0.7fr_auto] gap-3 px-4 py-3 bg-slate-50 border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Palet No</span>
                <span>Ürün / LOT</span>
                <span className="text-center">Koli</span>
                <span className="text-center">Ağırlık</span>
                <span>Raf</span>
                <span>Vardiya</span>
                <span></span>
            </div>
            <div className="divide-y divide-slate-50">
                {paletler.map(palet => (
                    <div
                        key={palet.id}
                        className="group px-4 py-3 hover:bg-blue-50/30 transition-colors duration-150
                            grid grid-cols-[1fr_auto] sm:grid-cols-[1fr_1.2fr_0.7fr_0.7fr_0.8fr_0.7fr_auto] gap-2 sm:gap-3 items-center"
                    >
                        {/* Palet No */}
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0 sm:flex hidden">
                                <Container className="w-4 h-4 text-blue-500" />
                            </div>
                            <span className="text-sm font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200/60">
                                {palet.palet_no}
                            </span>
                        </div>

                        {/* Delete - mobile only (top right) */}
                        <div className="sm:hidden flex justify-end">
                            <button
                                onClick={() => onDelete(palet.id)}
                                className="w-8 h-8 rounded-lg bg-red-50 text-red-400 flex items-center justify-center hover:bg-red-500 hover:text-white transition-all active:scale-95"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                            </button>
                        </div>

                        {/* Ürün / LOT */}
                        <div className="col-span-2 sm:col-span-1">
                            <p className="text-sm font-semibold text-slate-700 truncate">{palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}</p>
                            <p className="text-[11px] text-slate-400 font-medium">LOT: {palet.lot?.lot_no || '-'}</p>
                        </div>

                        {/* Mobile: metrics row */}
                        <div className="col-span-2 sm:hidden flex items-center gap-3 text-xs text-slate-500">
                            <span className="flex items-center gap-1"><PackageOpen className="w-3.5 h-3.5 text-indigo-400" /> {palet.koli_adedi} koli</span>
                            <span className="flex items-center gap-1"><Scale className="w-3.5 h-3.5 text-emerald-400" /> {palet.palet_kg || '-'} kg</span>
                            <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-blue-400" /> {palet.raf?.kod || 'Raf Yok'}</span>
                            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-slate-300" /> {palet.vardiya || '-'}</span>
                        </div>

                        {/* Desktop only columns */}
                        <p className="hidden sm:block text-sm font-semibold text-slate-700 text-center tabular-nums">{palet.koli_adedi}</p>
                        <p className="hidden sm:block text-sm font-medium text-slate-500 text-center tabular-nums">{palet.palet_kg || '-'}</p>
                        <div className="hidden sm:flex items-center gap-1.5">
                            <MapPin className={`w-3.5 h-3.5 ${palet.raf ? 'text-blue-500' : 'text-slate-300'}`} />
                            <span className={`text-xs font-semibold ${palet.raf ? 'text-blue-700' : 'text-slate-400'}`}>
                                {palet.raf?.kod || 'Yok'}
                            </span>
                        </div>
                        <p className="hidden sm:block text-xs font-medium text-slate-500 truncate">{palet.vardiya || '-'}</p>

                        {/* Delete - desktop */}
                        <div className="hidden sm:flex justify-end">
                            <button
                                onClick={() => onDelete(palet.id)}
                                className="w-8 h-8 rounded-lg text-slate-300 flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all active:scale-95"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   CARD VIEW — Refined palet card
   ═══════════════════════════════════════════ */
function PaletCard({ palet, onDelete }) {
    return (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md hover:border-slate-200 transition-all duration-200 group relative flex flex-col justify-between min-h-[200px]">
            {/* Header */}
            <div>
                <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                            <Container className="w-[18px] h-[18px] text-blue-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider leading-none">Palet</p>
                            <p className="text-sm font-bold text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded-md border border-slate-200/60 mt-0.5 inline-block leading-tight">
                                {palet.palet_no}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => onDelete(palet.id)}
                        className="w-8 h-8 rounded-lg text-slate-300 flex items-center justify-center opacity-100 sm:opacity-0 sm:group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all active:scale-95"
                        title="Paleti Çıkar"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>

                {/* Product */}
                <h3 className="text-[15px] font-bold text-slate-800 line-clamp-2 leading-snug mb-1">
                    {palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}
                </h3>
                <span className="inline-flex text-[10px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    LOT: {palet.lot?.lot_no || '-'}
                </span>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                    <div className="bg-slate-50 rounded-xl p-2.5 text-center border border-slate-100/80">
                        <PackageOpen className="w-4 h-4 text-indigo-500 mx-auto mb-0.5" />
                        <p className="text-base font-bold text-slate-800 leading-none tabular-nums">{palet.koli_adedi}</p>
                        <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Koli</p>
                    </div>
                    <div className="bg-slate-50 rounded-xl p-2.5 text-center border border-slate-100/80">
                        <Scale className="w-4 h-4 text-emerald-500 mx-auto mb-0.5" />
                        <p className="text-base font-bold text-slate-800 leading-none tabular-nums">{palet.palet_kg || '-'}</p>
                        <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">KG</p>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100">
                <div className="flex items-center gap-1">
                    <MapPin className={`w-3.5 h-3.5 ${palet.raf ? 'text-blue-500' : 'text-slate-300'}`} />
                    <span className={`text-[11px] font-semibold ${palet.raf ? 'text-blue-700' : 'text-slate-400'}`}>
                        {palet.raf?.kod || 'Raf Yok'}
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-300" />
                    <span className="text-[11px] font-medium text-slate-500 truncate max-w-[80px]">
                        {palet.vardiya || '-'}
                    </span>
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   SKELETON LOADER
   ═══════════════════════════════════════════ */
function SkeletonGrid({ viewMode }) {
    if (viewMode === 'list') {
        return (
            <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-16 border-b border-slate-50 animate-pulse bg-slate-50/50" />
                ))}
            </div>
        );
    }
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
                <div key={i} className="h-52 bg-white rounded-2xl border border-slate-100 animate-pulse" />
            ))}
        </div>
    );
}

/* ═══════════════════════════════════════════
   SORT DROPDOWN
   ═══════════════════════════════════════════ */
function SortDropdown({ sortKey, setSortKey }) {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const options = [
        { key: 'default', label: 'Varsayılan' },
        { key: 'palet_no_asc', label: 'Palet No (A→Z)' },
        { key: 'palet_no_desc', label: 'Palet No (Z→A)' },
        { key: 'koli_desc', label: 'En Çok Koli' },
        { key: 'koli_asc', label: 'En Az Koli' },
        { key: 'kg_desc', label: 'En Ağır' },
        { key: 'kg_asc', label: 'En Hafif' },
    ];

    const current = options.find(o => o.key === sortKey) || options[0];

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => setOpen(!open)}
                className="h-10 px-3 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-600 hover:border-slate-300 transition-all flex items-center gap-1.5 shadow-sm"
            >
                <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                <span className="hidden sm:inline">{current.label}</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            {open && (
                <div className="absolute right-0 top-full mt-1.5 bg-white rounded-xl border border-slate-200 shadow-xl z-30 py-1 min-w-[160px]">
                    {options.map(opt => (
                        <button
                            key={opt.key}
                            onClick={() => { setSortKey(opt.key); setOpen(false); }}
                            className={`w-full text-left px-3 py-2 text-xs font-medium transition-colors
                                ${sortKey === opt.key ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            {opt.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════
   MAIN PAGE COMPONENT
   ═══════════════════════════════════════════ */
export default function PaletlerPage() {
    // Data state
    const [paletler, setPaletler] = useState([]);
    const [lotlar, setLotlar] = useState([]);
    const { loading, run } = useAsync(true);

    // UI state
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);
    const [search, setSearch] = useState('');
    const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
    const [sortKey, setSortKey] = useState('default');
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [filters, setFilters] = useState({ lot_id: '', vardiya: '', raf: '' });

    // Infinite scroll state
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const sentinelRef = useRef(null);
    const limit = 24;

    // Initial + paginated fetch
    const fetchData = useCallback(async (pageNum = 0, append = false) => {
        try {
            const fetcher = () => Promise.all([
                getPaletler({ skip: pageNum * limit, limit }),
                ...(pageNum === 0 ? [getLotlar({ limit: 200 })] : [])
            ]);

            let results;
            if (pageNum === 0) {
                results = await run(fetcher);
            } else {
                setLoadingMore(true);
                results = await fetcher();
                setLoadingMore(false);
            }

            const [palRes, ...rest] = results;
            const newPaletler = palRes.data;

            if (append) {
                setPaletler(prev => {
                    const ids = new Set(prev.map(p => p.id));
                    const unique = newPaletler.filter(p => !ids.has(p.id));
                    return [...prev, ...unique];
                });
            } else {
                setPaletler(newPaletler);
            }

            setHasMore(newPaletler.length === limit);

            if (rest.length) {
                setLotlar(rest[0].data);
            }
        } catch {
            toast.error('Veriler yüklenemedi');
            setLoadingMore(false);
        }
    }, [run, limit]);

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            void fetchData(0);
        }, 0);

        return () => clearTimeout(timeoutId);
    }, [fetchData]);

    // Infinite scroll observer
    useEffect(() => {
        if (!sentinelRef.current || !hasMore || loading) return;
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !loadingMore && hasMore) {
                    const nextPage = page + 1;
                    setPage(nextPage);
                    fetchData(nextPage, true);
                }
            },
            { rootMargin: '200px' }
        );
        observer.observe(sentinelRef.current);
        return () => observer.disconnect();
    }, [hasMore, loading, loadingMore, page, fetchData]);

    // Barcode scanner hook
    useBarcodeScanner({
        isEnabled: !cameraScannerOpen,
        onScan: async (code) => {
            setSearch(code);
            try {
                const res = await getPaletByBarkod(code);
                toast.success(`${res.data.palet_no} No'lu palet bulundu!`, { icon: '📦' });
            } catch {
                toast.error(`Kayıtlı palet bulunamadı: ${code}`);
            }
        }
    });

    // Handlers
    const handleDelete = async (id) => {
        if (!confirm('Bu paleti depodan çıkarmak (pasif yapmak) istiyor musunuz?')) return;
        try {
            await deletePalet(id);
            toast.success('Palet pasife alındı');
            setPaletler(prev => prev.filter(p => p.id !== id));
        } catch (err) {
            toast.error(hataMetni(err, 'Çıkarma işlemi başarısız'));
        }
    };

    const resetFilters = () => setFilters({ lot_id: '', vardiya: '', raf: '' });

    // Filter + search + sort pipeline (memoized)
    const processedPaletler = useMemo(() => {
        let result = paletler;

        // Search
        if (search) {
            const s = search.toLowerCase();
            result = result.filter(p =>
                p.palet_no?.toLowerCase().includes(s) ||
                p.lot?.urun?.isim?.toLowerCase().includes(s) ||
                p.lot?.lot_no?.toLowerCase().includes(s)
            );
        }

        // Filters
        if (filters.lot_id) result = result.filter(p => p.lot_id === filters.lot_id);
        if (filters.vardiya) result = result.filter(p => p.vardiya === filters.vardiya);
        if (filters.raf === '__none__') result = result.filter(p => !p.raf);
        else if (filters.raf) result = result.filter(p => p.raf?.kod === filters.raf);

        // Sort
        switch (sortKey) {
            case 'palet_no_asc': result = [...result].sort((a, b) => (a.palet_no || '').localeCompare(b.palet_no || '')); break;
            case 'palet_no_desc': result = [...result].sort((a, b) => (b.palet_no || '').localeCompare(a.palet_no || '')); break;
            case 'koli_desc': result = [...result].sort((a, b) => (b.koli_adedi || 0) - (a.koli_adedi || 0)); break;
            case 'koli_asc': result = [...result].sort((a, b) => (a.koli_adedi || 0) - (b.koli_adedi || 0)); break;
            case 'kg_desc': result = [...result].sort((a, b) => (b.palet_kg || 0) - (a.palet_kg || 0)); break;
            case 'kg_asc': result = [...result].sort((a, b) => (a.palet_kg || 0) - (b.palet_kg || 0)); break;
            default: break;
        }

        return result;
    }, [paletler, search, filters, sortKey]);

    // Stats (memoized)
    const stats = useMemo(() => ({
        total: paletler.length,
        totalKoli: paletler.reduce((s, p) => s + (p.koli_adedi || 0), 0),
        totalKg: paletler.reduce((s, p) => s + (Number(p.palet_kg) || 0), 0),
        lotCount: new Set(paletler.map(p => p.lot_id)).size,
    }), [paletler]);

    const activeFilterCount = [filters.lot_id, filters.vardiya, filters.raf].filter(Boolean).length;

    return (
        <div className="pb-24 sm:pb-8 max-w-[1400px] mx-auto px-4 sm:px-6 pt-4 sm:pt-6">

            {/* ── HEADER ── */}
            <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/25 flex items-center justify-center flex-shrink-0">
                        <LayoutGrid className="w-[22px] h-[22px] text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-slate-900 tracking-tight leading-none">Paletler</h1>
                        <p className="text-xs text-slate-500 mt-0.5">Depo lokasyon ve palet takibi</p>
                    </div>
                </div>
            </div>

            {/* ── STATS BAR ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
                <StatCard icon={Layers} label="Toplam Palet" value={stats.total} color="blue" />
                <StatCard icon={PackageOpen} label="Toplam Koli" value={stats.totalKoli.toLocaleString('tr-TR')} color="indigo" />
                <StatCard icon={Scale} label="Toplam Ağırlık" value={stats.totalKg.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} color="emerald" suffix="kg" />
                <StatCard icon={TrendingUp} label="Aktif Lot" value={stats.lotCount} color="amber" />
            </div>

            {/* ── SEARCH & TOOLBAR ── */}
            <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Palet no, ürün veya LOT ara..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full h-10 pl-10 pr-4 text-sm font-medium rounded-xl border border-slate-200 bg-white
                            focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10
                            transition-all shadow-sm text-slate-800 placeholder-slate-400"
                    />
                    {search && (
                        <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Barcode scan */}
                <button
                    onClick={() => setCameraScannerOpen(true)}
                    className="h-10 w-10 flex items-center justify-center rounded-xl bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-200 transition-all shadow-sm flex-shrink-0 active:scale-95"
                    title="Barkod Tara"
                >
                    <Barcode className="w-[18px] h-[18px]" />
                </button>

                {/* Filter toggle */}
                <button
                    onClick={() => setFiltersOpen(!filtersOpen)}
                    className={`h-10 px-3 rounded-xl border text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all active:scale-95
                        ${filtersOpen || activeFilterCount > 0
                            ? 'bg-blue-50 border-blue-200 text-blue-700'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                >
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Filtre</span>
                    {activeFilterCount > 0 && (
                        <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
                            {activeFilterCount}
                        </span>
                    )}
                </button>

                {/* Sort */}
                <SortDropdown sortKey={sortKey} setSortKey={setSortKey} />

                {/* View toggle */}
                <div className="hidden sm:flex h-10 rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={`w-10 h-full flex items-center justify-center transition-colors ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-400 hover:text-slate-600'}`}
                    >
                        <LayoutGrid className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`w-10 h-full flex items-center justify-center border-l border-slate-200 transition-colors ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-400 hover:text-slate-600'}`}
                    >
                        <List className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* ── FILTER PANEL ── */}
            {filtersOpen && (
                <div className="mb-4">
                    <FilterPanel
                        filters={filters}
                        setFilters={setFilters}
                        lotlar={lotlar}
                        paletler={paletler}
                        onReset={resetFilters}
                    />
                </div>
            )}

            {/* ── RESULT COUNT ── */}
            {(search || activeFilterCount > 0) && !loading && (
                <p className="text-xs font-medium text-slate-500 mb-3">
                    {processedPaletler.length} sonuç bulundu
                    {search && <span className="text-slate-400"> · "{search}"</span>}
                </p>
            )}

            {/* ── CONTENT ── */}
            {loading ? (
                <SkeletonGrid viewMode={viewMode} />
            ) : processedPaletler.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-100 p-10 text-center shadow-sm">
                    <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Container className="w-8 h-8 text-slate-300" />
                    </div>
                    <p className="text-sm font-bold text-slate-700">Palet bulunamadı</p>
                    <p className="text-xs text-slate-400 mt-1">Farklı bir arama yapın veya yeni kayıt oluşturun.</p>
                    {(search || activeFilterCount > 0) && (
                        <button
                            onClick={() => { setSearch(''); resetFilters(); }}
                            className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-700"
                        >
                            Filtreleri Temizle
                        </button>
                    )}
                </div>
            ) : viewMode === 'list' ? (
                <PaletListView paletler={processedPaletler} onDelete={handleDelete} />
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {processedPaletler.map(palet => (
                        <PaletCard key={palet.id} palet={palet} onDelete={handleDelete} />
                    ))}
                </div>
            )}

            {/* ── INFINITE SCROLL SENTINEL ── */}
            {!loading && hasMore && (
                <div ref={sentinelRef} className="h-16 flex items-center justify-center mt-4">
                    {loadingMore && (
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                            <div className="w-5 h-5 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                            Yükleniyor...
                        </div>
                    )}
                </div>
            )}

            {/* ── BARCODE SCANNER ── */}
            <ZXingBarcodeScanner
                isOpen={cameraScannerOpen}
                onClose={() => setCameraScannerOpen(false)}
                onScanSuccess={async (code) => {
                    setSearch(code);
                    try {
                        const res = await getPaletByBarkod(code);
                        toast.success(`Palet bulundu: ${res.data.palet_no}`, { icon: '📦' });
                    } catch {
                        toast.error(`Kayıtlı palet bulunamadı: ${code}`);
                    }
                }}
            />
        </div>
    );
}
