import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import {
    Container, Plus, X, Barcode, Search, MapPin, PackageOpen,
    LayoutGrid, Scale, Clock, Trash2, List, SlidersHorizontal,
    ArrowUpDown, ChevronDown, Package, Weight, Layers, TrendingUp,
    Filter, RotateCcw
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
    getPaletler, createPalet, deletePalet, getSonrakiPaletNo,
    getLotlar, getPaletByBarkod
} from '../services/api';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

/* ═══════════════════════════════════════════
   PALET MODAL — Bottom Sheet (Mobile-first)
   ═══════════════════════════════════════════ */
function PaletModal({ isOpen, onClose, onSave, lotlar, sonrakiNo }) {
    const [form, setForm] = useState({
        lot_id: '', palet_no: '', raf_id: '', koli_adedi: 0, palet_kg: 0, vardiya: ''
    });

    useEffect(() => {
        if (isOpen) {
            setForm({ lot_id: '', palet_no: sonrakiNo || '', raf_id: '', koli_adedi: 0, palet_kg: 0, vardiya: '' });
            document.body.style.overflow = 'hidden';
        }
        return () => { document.body.style.overflow = ''; };
    }, [isOpen, sonrakiNo]);

    if (!isOpen) return null;

    const inputClass = `w-full h-[52px] px-4 text-[15px] font-semibold rounded-xl border border-slate-200
        bg-slate-50/80 text-slate-800 placeholder-slate-400
        focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white
        transition-all duration-200`;
    const labelClass = "text-[11px] font-bold text-slate-500 mb-1.5 block tracking-wider uppercase";

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center" onClick={onClose}>
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
            <div
                className="relative bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full max-w-lg max-h-[92vh] flex flex-col animate-slide-up sm:animate-fade-in sm:mx-4"
                onClick={e => e.stopPropagation()}
            >
                {/* Drag handle */}
                <div className="flex justify-center pt-3 pb-1 sm:hidden">
                    <div className="w-10 h-1 bg-slate-200 rounded-full" />
                </div>

                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
                    <div>
                        <h3 className="text-lg font-bold text-slate-900">Yeni Palet</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Depoya yeni bir palet girişi yapın</p>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Form */}
                <form
                    onSubmit={e => {
                        e.preventDefault();
                        onSave({
                            ...form,
                            lot_id: Number(form.lot_id),
                            raf_id: form.raf_id ? Number(form.raf_id) : null,
                            koli_adedi: Number(form.koli_adedi),
                            palet_kg: Number(form.palet_kg)
                        });
                    }}
                    className="flex-1 overflow-y-auto overscroll-contain p-5 space-y-4"
                >
                    <div>
                        <label className={labelClass}>Lot / Parti Seçimi <span className="text-red-400">*</span></label>
                        <select
                            className={`${inputClass} appearance-none`}
                            value={form.lot_id}
                            onChange={e => setForm({ ...form, lot_id: e.target.value })}
                            required
                        >
                            <option value="">Ürün veya LOT seçin...</option>
                            {lotlar.map(l => (
                                <option key={l.id} value={l.id}>
                                    LOT: {l.lot_no} — {l.urun?.isim || `Ürün #${l.urun_id}`}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className={labelClass}>Palet No <span className="text-red-400">*</span></label>
                            <input className={inputClass} value={form.palet_no} onChange={e => setForm({ ...form, palet_no: e.target.value })} required placeholder="PLT-X" />
                        </div>
                        <div>
                            <label className={labelClass}>Vardiya</label>
                            <input className={inputClass} value={form.vardiya} onChange={e => setForm({ ...form, vardiya: e.target.value })} placeholder="Gündüz" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className={labelClass}>Koli Adedi <span className="text-red-400">*</span></label>
                            <input type="number" min="0" className={inputClass} value={form.koli_adedi} onChange={e => setForm({ ...form, koli_adedi: e.target.value })} required />
                        </div>
                        <div>
                            <label className={labelClass}>Ağırlık (kg)</label>
                            <input type="number" min="0" step="0.01" className={inputClass} value={form.palet_kg} onChange={e => setForm({ ...form, palet_kg: e.target.value })} />
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-slate-100 sticky bottom-0 bg-white pb-safe">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 h-12 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 active:scale-[0.98] transition-all"
                        >
                            İptal
                        </button>
                        <button
                            type="submit"
                            className="flex-1 h-12 rounded-xl bg-blue-600 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 active:scale-[0.98] transition-all"
                        >
                            Kaydet
                        </button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}

/* ═══════════════════════════════════════════
   STAT CARD — Compact KPI display
   ═══════════════════════════════════════════ */
function StatCard({ icon: Icon, label, value, color, suffix }) {
    const colorMap = {
        blue: 'from-blue-500 to-blue-600 shadow-blue-500/20',
        indigo: 'from-indigo-500 to-indigo-600 shadow-indigo-500/20',
        emerald: 'from-emerald-500 to-emerald-600 shadow-emerald-500/20',
        amber: 'from-amber-500 to-amber-600 shadow-amber-500/20',
    };

    return (
        <div className="bg-white rounded-2xl border border-slate-100 p-4 flex items-center gap-3 min-w-0 shadow-sm">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[color]} shadow-lg flex-shrink-0 flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
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
    const [sonrakiNo, setSonrakiNo] = useState('');
    const { loading, run } = useAsync(true);

    // UI state
    const [modalOpen, setModalOpen] = useState(false);
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
                ...(pageNum === 0 ? [getLotlar({ limit: 200 }), getSonrakiPaletNo()] : [])
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
                setSonrakiNo(rest[1].data.palet_no);
            }
        } catch {
            toast.error('Veriler yüklenemedi');
            setLoadingMore(false);
        }
    }, [run, limit]);

    useEffect(() => { fetchData(0); }, []);

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
        isEnabled: !modalOpen && !cameraScannerOpen,
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
    const handleSave = async (data) => {
        try {
            await createPalet(data);
            toast.success('Palet sisteme eklendi!');
            setModalOpen(false);
            setPage(0);
            fetchData(0);
        } catch (err) {
            toast.error(hataMetni(err, 'Palet eklenemedi'));
        }
    };

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
                <button
                    onClick={() => setModalOpen(true)}
                    className="hidden sm:flex h-10 px-5 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-600/20 active:scale-[0.98] transition-all items-center gap-2"
                >
                    <Plus className="w-4 h-4" strokeWidth={2.5} /> Yeni Palet
                </button>
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

            {/* ── MOBILE FAB ── */}
            <button
                onClick={() => setModalOpen(true)}
                className="sm:hidden fixed bottom-20 right-5 w-14 h-14 bg-blue-600 text-white rounded-2xl shadow-lg shadow-blue-600/30 flex items-center justify-center hover:bg-blue-700 active:scale-95 transition-all z-40"
            >
                <Plus className="w-7 h-7" strokeWidth={2.5} />
            </button>

            {/* ── MODAL ── */}
            <PaletModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSave} lotlar={lotlar} sonrakiNo={sonrakiNo} />

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