import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    Container, X, Barcode, Search, MapPin, PackageOpen,
    LayoutGrid, Scale, Clock, Trash2, List, SlidersHorizontal,
    ArrowUpDown, ChevronDown, Package, Weight, Layers, TrendingUp,
    Filter, RotateCcw, Hash
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
        <div className="bg-white rounded-2xl border border-slate-200 p-4 flex items-center gap-3.5 min-w-0 shadow-sm transition-shadow hover:shadow-md">
            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${colorMap[color]} shadow-lg flex-shrink-0 flex items-center justify-center`}>
                {React.createElement(IconComponent, { className: 'w-5 h-5 text-white' })}
            </div>
            <div className="min-w-0 flex-1">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider truncate mb-0.5">{label}</p>
                <p className="text-xl font-bold text-slate-900 leading-none tabular-nums">
                    {value}{suffix && <span className="text-sm font-medium text-slate-400 ml-1">{suffix}</span>}
                </p>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   FILTER PANEL — Collapsible, mobile-friendly
   ═══════════════════════════════════════════ */
function FilterPanel({ filters, setFilters, lotlar, paletler, onReset, onEanChange }) {
    const uniqueVardiyalar = useMemo(() =>
        [...new Set(paletler.map(p => p.vardiya).filter(Boolean))],
        [paletler]
    );

    const uniqueRaflar = useMemo(() => {
        const rafMap = new Map();
        paletler.forEach((p) => {
            if (p.raf?.id && p.raf?.kod) {
                rafMap.set(p.raf.id, { id: p.raf.id, kod: p.raf.kod });
            }
        });
        return Array.from(rafMap.values());
    }, [paletler]);

    const chipBase = "min-h-[36px] px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer select-none flex items-center justify-center";
    const chipActive = "bg-blue-50 border-blue-300 text-blue-700 shadow-sm";
    const chipInactive = "bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50";

    const hasActiveFilters = filters.lot_id || filters.vardiya || filters.raf_id || filters.ean;
    const eanValue = filters.ean || '';
    const eanValid = !eanValue || /^\d{8,14}$/.test(eanValue);

    return (
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 space-y-4 shadow-sm mb-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
                    <Filter className="w-4 h-4 text-blue-500" />
                    Gelişmiş Filtreler
                </div>
                {hasActiveFilters && (
                    <button onClick={onReset} className="flex items-center gap-1.5 text-xs font-semibold text-red-600 hover:text-red-700 transition-colors bg-red-50 px-2.5 py-1.5 rounded-lg">
                        <RotateCcw className="w-3.5 h-3.5" /> Temizle
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Sol Kolon */}
                <div className="space-y-4">
                    {/* EAN filter */}
                    <div>
                        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">EAN Numarası</p>
                        <div className="relative">
                            <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                inputMode="numeric"
                                placeholder="EAN-8 / EAN-13 / EAN-14..."
                                value={eanValue}
                                onChange={e => {
                                    const val = e.target.value.replace(/[^\d]/g, '').slice(0, 14);
                                    setFilters(f => ({ ...f, ean: val }));
                                    onEanChange(val);
                                }}
                                className={`w-full h-10 pl-9 pr-9 text-sm font-medium rounded-xl border bg-white
                                    focus:outline-none focus:ring-2 transition-all tabular-nums
                                    ${!eanValid
                                        ? 'border-red-300 focus:border-red-400 focus:ring-red-200/40'
                                        : eanValue
                                            ? 'border-blue-300 focus:border-blue-400 focus:ring-blue-200/40'
                                            : 'border-slate-200 focus:border-blue-400 focus:ring-blue-200/40'
                                    } text-slate-800 placeholder-slate-400`}
                            />
                            {eanValue && (
                                <button
                                    onClick={() => { setFilters(f => ({ ...f, ean: '' })); onEanChange(''); }}
                                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                        {eanValue && !eanValid && (
                            <p className="text-[11px] font-medium text-red-500 mt-1.5 flex items-center gap-1"><X className="w-3 h-3"/> EAN 8-14 haneli olmalıdır</p>
                        )}
                    </div>

                    {/* Lot filter */}
                    <div>
                        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Lot (Son 8)</p>
                        <div className="flex flex-wrap gap-2 max-h-[120px] overflow-y-auto pr-1 pb-1">
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
                </div>

                {/* Sağ Kolon */}
                <div className="space-y-4">
                    {/* Vardiya filter */}
                    {uniqueVardiyalar.length > 0 && (
                        <div>
                            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Vardiya</p>
                            <div className="flex flex-wrap gap-2">
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
                            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Raf Konumu</p>
                            <div className="flex flex-wrap gap-2 max-h-[120px] overflow-y-auto pr-1 pb-1">
                                <button
                                    onClick={() => setFilters(f => ({ ...f, raf_id: f.raf_id === '__none__' ? '' : '__none__' }))}
                                    className={`${chipBase} ${filters.raf_id === '__none__' ? chipActive : chipInactive}`}
                                >
                                    Raf Yok
                                </button>
                                {uniqueRaflar.map(r => (
                                    <button
                                        key={r.id}
                                        onClick={() => setFilters(f => ({ ...f, raf_id: f.raf_id === r.id ? '' : r.id }))}
                                        className={`${chipBase} ${filters.raf_id === r.id ? chipActive : chipInactive}`}
                                    >
                                        {r.kod}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   LIST VIEW — Compact table-like rows
   ═══════════════════════════════════════════ */
function PaletListView({ paletler, onDelete }) {
    return (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            {/* Desktop table header */}
            <div className="hidden sm:grid sm:grid-cols-[1.2fr_1.5fr_1fr_0.8fr_0.8fr_1fr_0.8fr_auto] gap-4 px-5 py-3.5 bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <span>Palet No</span>
                <span>Ürün / LOT</span>
                <span>EAN</span>
                <span className="text-center">Koli</span>
                <span className="text-center">Ağırlık</span>
                <span>Raf</span>
                <span>Vardiya</span>
                <span className="w-8 text-center">İşlem</span>
            </div>
            <div className="divide-y divide-slate-100">
                {paletler.map(palet => (
                    <div
                        key={palet.id}
                        className="group px-4 py-3.5 hover:bg-blue-50/40 transition-colors duration-200
                            grid grid-cols-[1fr_auto] sm:grid-cols-[1.2fr_1.5fr_1fr_0.8fr_0.8fr_1fr_0.8fr_auto] gap-3 items-center"
                    >
                        {/* Palet No */}
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-blue-100/50 flex items-center justify-center flex-shrink-0 sm:flex hidden">
                                <Container className="w-4 h-4 text-blue-600" />
                            </div>
                            <span className="text-sm font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
                                {palet.palet_no}
                            </span>
                        </div>

                        {/* Delete - mobile only (top right) */}
                        <div className="sm:hidden flex justify-end">
                            <button
                                onClick={() => onDelete(palet.id)}
                                className="w-9 h-9 rounded-xl bg-red-50 text-red-500 flex items-center justify-center hover:bg-red-500 hover:text-white transition-all active:scale-95"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Ürün / LOT */}
                        <div className="col-span-2 sm:col-span-1">
                            <p className="text-sm font-bold text-slate-700 truncate">{palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}</p>
                            <p className="text-[12px] text-slate-500 font-medium mt-0.5">LOT: {palet.lot?.lot_no || '-'}</p>
                        </div>

                        {/* Mobile: metrics row - better structured */}
                        <div className="col-span-2 sm:hidden grid grid-cols-2 gap-2 mt-1">
                             {palet.lot?.urun?.ean && (
                                <div className="col-span-2 flex items-center gap-1.5 text-xs font-mono text-violet-600 bg-violet-50 w-fit px-2 py-0.5 rounded border border-violet-100">
                                    <Hash className="w-3.5 h-3.5" /> {palet.lot.urun.ean}
                                </div>
                            )}
                            <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                                <PackageOpen className="w-4 h-4 text-indigo-400" /> {palet.koli_adedi} Koli
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                                <Scale className="w-4 h-4 text-emerald-400" /> {palet.palet_kg || '-'} kg
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                                <MapPin className="w-4 h-4 text-blue-400" /> <span className="truncate">{palet.raf?.kod || 'Yok'}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                                <Clock className="w-4 h-4 text-amber-400" /> <span className="truncate">{palet.vardiya || '-'}</span>
                            </div>
                        </div>

                        {/* Desktop only columns */}
                        <div className="hidden sm:flex items-center">
                            {palet.lot?.urun?.ean ? (
                                <span className="text-[13px] font-mono font-semibold text-violet-700 bg-violet-50 px-2 py-0.5 rounded-md border border-violet-200">
                                    {palet.lot.urun.ean}
                                </span>
                            ) : (
                                <span className="text-xs text-slate-400">—</span>
                            )}
                        </div>
                        <p className="hidden sm:block text-[15px] font-bold text-slate-700 text-center tabular-nums">{palet.koli_adedi}</p>
                        <p className="hidden sm:block text-[15px] font-bold text-slate-700 text-center tabular-nums">{palet.palet_kg || '-'}</p>
                        <div className="hidden sm:flex items-center gap-2">
                            <MapPin className={`w-4 h-4 ${palet.raf ? 'text-blue-500' : 'text-slate-300'}`} />
                            <span className={`text-sm font-bold ${palet.raf ? 'text-blue-700' : 'text-slate-400'}`}>
                                {palet.raf?.kod || 'Yok'}
                            </span>
                        </div>
                        <p className="hidden sm:block text-sm font-semibold text-slate-600 truncate">{palet.vardiya || '-'}</p>

                        {/* Delete - desktop (Made more discoverable) */}
                        <div className="hidden sm:flex justify-center">
                            <button
                                onClick={() => onDelete(palet.id)}
                                className="w-9 h-9 rounded-xl text-slate-400 opacity-60 group-hover:opacity-100 flex items-center justify-center hover:bg-red-50 hover:text-red-600 transition-all active:scale-95 border border-transparent hover:border-red-100"
                                title="Paleti Çıkar"
                            >
                                <Trash2 className="w-4.5 h-4.5" />
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
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 hover:shadow-md hover:border-blue-200 transition-all duration-200 group relative flex flex-col justify-between min-h-[220px]">
            {/* Header */}
            <div>
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0 border border-blue-100/50">
                            <Container className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider leading-none mb-1">Palet No</p>
                            <p className="text-sm font-extrabold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200 inline-block leading-tight">
                                {palet.palet_no}
                            </p>
                        </div>
                    </div>
                    {/* Trash Button - Better Discoverability */}
                    <button
                        onClick={() => onDelete(palet.id)}
                        className="w-9 h-9 rounded-xl text-slate-400 sm:opacity-50 sm:group-hover:opacity-100 flex items-center justify-center hover:bg-red-50 hover:text-red-600 transition-all active:scale-95 border border-transparent hover:border-red-100"
                        title="Paleti Çıkar"
                    >
                        <Trash2 className="w-4.5 h-4.5" />
                    </button>
                </div>

                {/* Product */}
                <h3 className="text-base font-bold text-slate-800 line-clamp-2 leading-snug mb-2">
                    {palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}
                </h3>
                <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="inline-flex items-center text-[11px] font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded-md">
                        LOT: {palet.lot?.lot_no || '-'}
                    </span>
                    {palet.lot?.urun?.ean && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-violet-700 bg-violet-50 px-2 py-1 rounded-md border border-violet-200">
                            <Hash className="w-3 h-3" /> {palet.lot.urun.ean}
                        </span>
                    )}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-3 mt-4">
                    <div className="bg-slate-50/80 rounded-xl p-3 text-center border border-slate-200">
                        <PackageOpen className="w-4 h-4 text-indigo-500 mx-auto mb-1" />
                        <p className="text-[17px] font-black text-slate-800 leading-none tabular-nums">{palet.koli_adedi}</p>
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-1">Koli</p>
                    </div>
                    <div className="bg-slate-50/80 rounded-xl p-3 text-center border border-slate-200">
                        <Scale className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                        <p className="text-[17px] font-black text-slate-800 leading-none tabular-nums">{palet.palet_kg || '-'}</p>
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-1">KG</p>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-3.5 mt-4 border-t border-slate-100">
                <div className="flex items-center gap-1.5">
                    <MapPin className={`w-4 h-4 ${palet.raf ? 'text-blue-500' : 'text-slate-300'}`} />
                    <span className={`text-[12px] font-bold ${palet.raf ? 'text-blue-700' : 'text-slate-500'}`}>
                        {palet.raf?.kod || 'Raf Yok'}
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="text-[12px] font-semibold text-slate-600 truncate max-w-[90px]">
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
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-[72px] border-b border-slate-100 animate-pulse bg-slate-50/50" />
                ))}
            </div>
        );
    }
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
            {[...Array(8)].map((_, i) => (
                <div key={i} className="h-[240px] bg-white rounded-2xl border border-slate-200 animate-pulse shadow-sm" />
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
        <div ref={ref} className="relative w-full sm:w-auto">
            <button
                onClick={() => setOpen(!open)}
                className="w-full sm:w-auto h-11 px-4 rounded-xl bg-white border border-slate-200 text-[13px] font-bold text-slate-700 hover:border-slate-300 transition-all flex items-center justify-between sm:justify-start gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
                <div className="flex items-center gap-2">
                    <ArrowUpDown className="w-4 h-4 text-slate-400" />
                    <span>{current.label}</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            {open && (
                <div className="absolute right-0 sm:right-auto sm:left-0 top-full mt-2 bg-white rounded-xl border border-slate-200 shadow-xl z-50 py-1.5 w-full sm:min-w-[180px]">
                    {options.map(opt => (
                        <button
                            key={opt.key}
                            onClick={() => { setSortKey(opt.key); setOpen(false); }}
                            className={`w-full text-left px-4 py-2.5 text-[13px] font-semibold transition-colors
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
    const [filters, setFilters] = useState({ lot_id: '', vardiya: '', raf_id: '', ean: '' });
    const [debouncedEan, setDebouncedEan] = useState('');
    const eanDebounceRef = useRef(null);
    const requestSeqRef = useRef(0);

    // Infinite scroll state
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const sentinelRef = useRef(null);
    const limit = 24;

    // Initial + paginated fetch
    const fetchData = useCallback(async (pageNum = 0, append = false) => {
        const requestSeq = ++requestSeqRef.current;
        try {
            const apiParams = { skip: pageNum * limit, limit };
            if (filters.lot_id) apiParams.lot_id = filters.lot_id;
            if (filters.raf_id && filters.raf_id !== '__none__') apiParams.raf_id = filters.raf_id;
            if (debouncedEan && /^\d{8,14}$/.test(debouncedEan)) {
                apiParams.ean = debouncedEan;
            }

            const fetcher = () => Promise.all([
                getPaletler(apiParams),
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
            if (requestSeq !== requestSeqRef.current) return;

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
        } catch (err) {
            if (requestSeq !== requestSeqRef.current) return;
            const status = err?.response?.status;
            if (status === 429) toast.error('Çok sık istek gönderildi, lütfen kısa süre sonra tekrar deneyin');
            else if (status === 403) toast.error('Bu listeye erişim yetkiniz yok');
            else toast.error('Veriler yüklenemedi');
            setLoadingMore(false);
        }
    }, [run, limit, filters.lot_id, filters.raf_id, debouncedEan]);

    useEffect(() => {
        setPage(0);
        setHasMore(true);
        setPaletler([]);
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
        } catch (err) {
            const status = err?.response?.status;
            if (status === 404) toast.error(`Aktif palet bulunamadı: ${code}`);
            else if (status === 429) toast.error('Çok sık sorgu yapıldı, lütfen kısa süre bekleyin');
            else toast.error(`Kayıtlı palet bulunamadı: ${code}`);
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
            const status = err?.response?.status;
            if (status === 403) toast.error('Bu işlem için yetkiniz yok');
            else if (status === 429) toast.error('Çok sık istek gönderildi, lütfen tekrar deneyin');
            else toast.error(hataMetni(err, 'Çıkarma işlemi başarısız'));
        }
    };

    const resetFilters = () => {
        setDebouncedEan('');
        setFilters({ lot_id: '', vardiya: '', raf_id: '', ean: '' });
    };

    const handleEanChange = useCallback((val) => {
        if (eanDebounceRef.current) clearTimeout(eanDebounceRef.current);
        eanDebounceRef.current = setTimeout(() => {
            if (!val || /^\d{8,14}$/.test(val)) {
                setDebouncedEan(val);
            }
        }, 500);
    }, []);

    // Filter + search + sort pipeline
    const processedPaletler = useMemo(() => {
        let result = paletler;

        // Search
        if (search) {
            const s = search.toLowerCase();
            result = result.filter(p =>
                p.palet_no?.toLowerCase().includes(s) ||
                p.lot?.urun?.isim?.toLowerCase().includes(s) ||
                p.lot?.lot_no?.toLowerCase().includes(s) ||
                p.lot?.urun?.ean?.toLowerCase().includes(s)
            );
        }

        // Filters
        if (filters.vardiya) result = result.filter(p => p.vardiya === filters.vardiya);
        if (filters.raf_id === '__none__') result = result.filter(p => !p.raf);

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

    // Stats
    const stats = useMemo(() => ({
        total: paletler.length,
        totalKoli: paletler.reduce((s, p) => s + (p.koli_adedi || 0), 0),
        totalKg: paletler.reduce((s, p) => s + (Number(p.palet_kg) || 0), 0),
        lotCount: new Set(paletler.map(p => p.lot_id)).size,
    }), [paletler]);

    const activeFilterCount = [filters.lot_id, filters.vardiya, filters.raf_id, filters.ean].filter(Boolean).length;

    return (
        <div className="pb-24 sm:pb-8 max-w-[1400px] mx-auto px-4 sm:px-6 pt-4 sm:pt-6">

            {/* ── HEADER ── */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/30 flex items-center justify-center flex-shrink-0">
                        <LayoutGrid className="w-[22px] h-[22px] text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-black text-slate-900 tracking-tight leading-none">Paletler</h1>
                        <p className="text-[13px] font-medium text-slate-500 mt-1">Depo lokasyon ve palet takibi</p>
                    </div>
                </div>
            </div>

            {/* ── STATS BAR ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
                <StatCard icon={Layers} label="Toplam Palet" value={stats.total} color="blue" />
                <StatCard icon={PackageOpen} label="Toplam Koli" value={stats.totalKoli.toLocaleString('tr-TR')} color="indigo" />
                <StatCard icon={Scale} label="Toplam Ağırlık" value={stats.totalKg.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} color="emerald" suffix="kg" />
                <StatCard icon={TrendingUp} label="Aktif Lot" value={stats.lotCount} color="amber" />
            </div>

            {/* ── SEARCH & TOOLBAR (Refactored for UX/Mobile Layout) ── */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-5">
                {/* Search & Barcode Block (Takes full width on mobile, flexible on desktop) */}
                <div className="flex items-center gap-2 flex-1">
                    <div className="relative flex-1">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Palet no, ürün veya LOT ara..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="w-full h-11 pl-11 pr-10 text-[14px] font-semibold rounded-xl border border-slate-200 bg-white
                                focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10
                                transition-all shadow-sm text-slate-800 placeholder-slate-400"
                        />
                        {search && (
                            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 bg-slate-100 p-1 rounded-full">
                                <X className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </div>

                    <button
                        onClick={() => setCameraScannerOpen(true)}
                        className="h-11 w-11 flex items-center justify-center rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all shadow-sm flex-shrink-0 active:scale-95"
                        title="Barkod Tara"
                    >
                        <Barcode className="w-5 h-5" />
                    </button>
                </div>

                {/* Filters, Sort & View Modes Block */}
                <div className="flex items-center gap-2 justify-between sm:justify-start">
                    <button
                        onClick={() => setFiltersOpen(!filtersOpen)}
                        className={`h-11 px-4 rounded-xl border text-[13px] font-bold flex items-center justify-center gap-2 shadow-sm transition-all active:scale-95 flex-1 sm:flex-none
                            ${filtersOpen || activeFilterCount > 0
                                ? 'bg-blue-50 border-blue-300 text-blue-700'
                                : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                            }`}
                    >
                        <SlidersHorizontal className="w-4 h-4" />
                        <span>Filtre</span>
                        {activeFilterCount > 0 && (
                            <span className="w-5 h-5 rounded-md bg-blue-600 text-white text-[11px] font-black flex items-center justify-center ml-1">
                                {activeFilterCount}
                            </span>
                        )}
                    </button>

                    <SortDropdown sortKey={sortKey} setSortKey={setSortKey} />

                    <div className="hidden sm:flex h-11 rounded-xl border border-slate-200 overflow-hidden shadow-sm bg-white">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`w-11 h-full flex items-center justify-center transition-colors ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
                            title="Grid Görünümü"
                        >
                            <LayoutGrid className="w-[18px] h-[18px]" />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={`w-11 h-full flex items-center justify-center border-l border-slate-200 transition-colors ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
                            title="Liste Görünümü"
                        >
                            <List className="w-[18px] h-[18px]" />
                        </button>
                    </div>
                </div>
            </div>

            {/* ── FILTER PANEL ── */}
            {filtersOpen && (
                <FilterPanel
                    filters={filters}
                    setFilters={setFilters}
                    lotlar={lotlar}
                    paletler={paletler}
                    onReset={resetFilters}
                    onEanChange={handleEanChange}
                />
            )}

            {/* ── RESULT COUNT ── */}
            {(search || activeFilterCount > 0) && !loading && (
                <p className="text-[13px] font-bold text-slate-500 mb-4 bg-slate-100 inline-block px-3 py-1 rounded-lg">
                    {processedPaletler.length} sonuç bulundu
                    {search && <span className="text-slate-400 font-medium ml-1">· "{search}"</span>}
                </p>
            )}

            {/* ── CONTENT ── */}
            {loading ? (
                <SkeletonGrid viewMode={viewMode} />
            ) : processedPaletler.length === 0 ? (
                <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center shadow-sm mt-4">
                    <div className="w-20 h-20 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-slate-100">
                        <Container className="w-10 h-10 text-slate-300" />
                    </div>
                    <p className="text-lg font-black text-slate-800">Eşleşen Palet Bulunamadı</p>
                    <p className="text-[14px] text-slate-500 mt-2 max-w-sm mx-auto">Arama kriterlerinize veya filtrelerinize uygun palet depoda yer almıyor.</p>
                    {(search || activeFilterCount > 0) && (
                        <button
                            onClick={() => { setSearch(''); resetFilters(); }}
                            className="mt-5 px-5 py-2.5 bg-blue-50 text-blue-700 text-[13px] font-bold rounded-xl hover:bg-blue-100 transition-colors"
                        >
                            Filtreleri ve Aramayı Temizle
                        </button>
                    )}
                </div>
            ) : viewMode === 'list' ? (
                <PaletListView paletler={processedPaletler} onDelete={handleDelete} />
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
                    {processedPaletler.map(palet => (
                        <PaletCard key={palet.id} palet={palet} onDelete={handleDelete} />
                    ))}
                </div>
            )}

            {/* ── INFINITE SCROLL SENTINEL ── */}
            {!loading && hasMore && (
                <div ref={sentinelRef} className="h-20 flex items-center justify-center mt-6">
                    {loadingMore && (
                        <div className="flex items-center gap-3 text-[14px] font-bold text-slate-400 bg-white px-5 py-2.5 rounded-full shadow-sm border border-slate-100">
                            <div className="w-5 h-5 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                            Daha fazla yükleniyor...
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
                    } catch (err) {
                        const status = err?.response?.status;
                        if (status === 404) toast.error(`Aktif palet bulunamadı: ${code}`);
                        else if (status === 429) toast.error('Çok sık sorgu yapıldı, lütfen kısa süre bekleyin');
                        else toast.error(`Kayıtlı palet bulunamadı: ${code}`);
                    }
                }}
            />
        </div>
    );
}