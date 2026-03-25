import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Layers, Plus, Search, X, AlertTriangle, ChevronLeft, ChevronRight, ChevronDown, Trash2, Calendar, Hash } from 'lucide-react';
import toast from 'react-hot-toast';
import { getLotlar, createLot, deleteLot, getSktYaklasanLotlar, getUrunler } from '../services/api';
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
        @keyframes lotV2ModalUp {
            from { transform:translateY(100%) }
            to   { transform:translateY(0) }
        }
        @keyframes lotV2ModalCenter {
            from { opacity:0; transform:scale(.96) translateY(10px) }
            to   { opacity:1; transform:scale(1) translateY(0) }
        }
        @keyframes lotV2Overlay {
            from { opacity:0 }
            to   { opacity:1 }
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

    const handleConfirmDelete = () => { reset(); onDelete(lot.id); };

    return (
        <div className="relative lotv2-enter overflow-hidden rounded-2xl" style={{ animationDelay: `${index * 35}ms` }}>
            {/* Swipe delete action */}
            <div className="absolute inset-y-0 right-0 w-20 bg-red-500 flex items-center justify-center rounded-r-2xl">
                <button onClick={handleConfirmDelete} className="flex flex-col items-center gap-0.5">
                    <Trash2 className="w-4 h-4 text-white" />
                    <span className="text-[10px] font-bold text-white/90">Pasif</span>
                </button>
            </div>

            {/* Card body */}
            <div ref={ref} className={`relative bg-white border rounded-2xl p-4 active:bg-slate-50/50 transition-colors z-10
                ${isUrgent ? `${c.border} border-l-[3px]` : 'border-slate-200/80'}`}>
                {revealed && <div className="absolute inset-0 z-20 rounded-2xl" onClick={() => reset()} />}

                {/* Row 1: Product name + SKT pill */}
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

                {/* Row 2: Info chips */}
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
                <p className="text-[14px] font-bold text-slate-800">{lot.urun?.isim || `Ürün #${lot.urun_id}`}</p>
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
function EmptyState({ searching, query }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 sm:py-20 text-center px-6">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-slate-200/60 flex items-center justify-center mb-4">
                {searching ? <Search className="w-6 h-6 text-slate-300" /> : <Layers className="w-6 h-6 text-slate-300" />}
            </div>
            <p className="text-[15px] font-bold text-slate-600">{searching ? 'Sonuç bulunamadı' : 'Kayıtlı LOT bulunamadı'}</p>
            <p className="text-[13px] text-slate-400 mt-1.5 max-w-[240px]">{searching ? `"${query}" ile eşleşen kayıt yok` : 'Yeni LOT ekleyerek başlayın'}</p>
        </div>
    );
}

/* ─── Modal ─── */
function LotModal({ isOpen, onClose, onSave, urunler }) {
    const [form, setForm] = useState({ urun_id: '', lot_no: '', parti_no: '', uretim_tarihi: '', son_kullanma_tarihi: '', aciklama: '' });

    useEffect(() => { if (isOpen) setForm({ urun_id: '', lot_no: '', parti_no: '', uretim_tarihi: '', son_kullanma_tarihi: '', aciklama: '' }); }, [isOpen]);
    useEffect(() => { if (isOpen) { document.body.style.overflow = 'hidden'; return () => { document.body.style.overflow = ''; }; } }, [isOpen]);

    if (!isOpen) return null;

    const inp = `w-full h-12 px-4 text-[14px] font-medium rounded-xl border border-slate-200 bg-slate-50/50
        text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-[3px] focus:ring-amber-500/15
        focus:border-amber-400 focus:bg-white transition-all duration-200`;
    const lbl = "text-[11px] font-extrabold text-slate-500 mb-1.5 block tracking-widest uppercase";

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-6" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" style={{ animation: 'lotV2Overlay .2s ease both' }} />
            <div
                className="relative bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-[20px] shadow-2xl ring-1 ring-slate-900/5 max-h-[90vh] overflow-y-auto"
                style={{ animation: typeof window !== 'undefined' && window.innerWidth < 640 ? 'lotV2ModalUp .32s cubic-bezier(.22,1,.36,1) both' : 'lotV2ModalCenter .28s cubic-bezier(.22,1,.36,1) both' }}
                onClick={e => e.stopPropagation()}
            >
                <div className="sm:hidden flex justify-center pt-3 pb-1"><div className="w-10 h-1 rounded-full bg-slate-300" /></div>

                <div className="flex items-center justify-between px-5 sm:px-6 py-4 sm:py-5 border-b border-slate-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-100 to-amber-50 border border-amber-200/80 flex items-center justify-center">
                            <Layers className="w-5 h-5 text-amber-600" />
                        </div>
                        <div>
                            <h3 className="text-[17px] font-extrabold text-slate-900">Yeni LOT</h3>
                            <p className="text-[11px] font-medium text-slate-400 mt-0.5">Parti ve SKT bilgileri</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors">
                        <X className="w-4 h-4 text-slate-500" />
                    </button>
                </div>

                <form onSubmit={e => { e.preventDefault(); onSave({ ...form, urun_id: Number(form.urun_id) }); }} className="p-5 sm:p-6 space-y-4">
                    <div>
                        <label className={lbl}>Ürün *</label>
                        <div className="relative">
                            <select className={`${inp} appearance-none pr-10`} value={form.urun_id} onChange={e => setForm({ ...form, urun_id: e.target.value })} required>
                                <option value="">Ürün seçin...</option>
                                {urunler.map(u => <option key={u.id} value={u.id}>{u.isim} ({u.marka?.isim || '-'})</option>)}
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div><label className={lbl}>LOT No *</label><input className={inp} value={form.lot_no} onChange={e => setForm({ ...form, lot_no: e.target.value })} placeholder="8690684001039" required /></div>
                        <div><label className={lbl}>Parti No</label><input className={inp} value={form.parti_no} onChange={e => setForm({ ...form, parti_no: e.target.value })} placeholder="P-2024" /></div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div><label className={lbl}>Üretim Tarihi</label><input type="date" className={inp} value={form.uretim_tarihi} onChange={e => setForm({ ...form, uretim_tarihi: e.target.value })} /></div>
                        <div><label className={lbl}>SKT</label><input type="date" className={inp} value={form.son_kullanma_tarihi} onChange={e => setForm({ ...form, son_kullanma_tarihi: e.target.value })} /></div>
                    </div>
                    <div><label className={lbl}>Açıklama</label><textarea className={`${inp} h-20 resize-none py-3`} value={form.aciklama} onChange={e => setForm({ ...form, aciklama: e.target.value })} placeholder="Parti hakkında not..." /></div>
                    <div className="flex gap-3 pt-3 border-t border-slate-100">
                        <button type="button" onClick={onClose} className="flex-1 h-12 rounded-xl border border-slate-200 text-[14px] font-bold text-slate-600 hover:bg-slate-50 active:scale-[0.98] transition-all duration-200">İptal</button>
                        <button type="submit" className="flex-1 h-12 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 text-[14px] font-bold text-white shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 active:scale-[0.98] transition-all duration-200">Kaydet</button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}

/* ─── Main Page ─── */
export default function LotlarPage() {
    const [lotlar, setLotlar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const { loading, run } = useAsync(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [tab, setTab] = useState('tumu');
    const [sktLotlar, setSktLotlar] = useState([]);
    const [page, setPage] = useState(0);
    const limit = 20;
    const [searchQuery, setSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const searchRef = useRef(null);

    const fetchData = async () => {
        try {
            const [lotRes, urunRes, sktRes] = await run(() => Promise.all([
                getLotlar({ skip: page * limit, limit }),
                getUrunler({ limit: 200 }),
                getSktYaklasanLotlar(60)
            ]));
            setLotlar(lotRes.data);
            setUrunler(urunRes.data);
            setSktLotlar(sktRes.data);
        } catch {
            toast.error('Veriler yüklenemedi');
        }
    };

    useEffect(() => { fetchData(); }, [page]);
    useEffect(() => { if (searchOpen && searchRef.current) searchRef.current.focus(); }, [searchOpen]);

    const handleSave = async (data) => {
        try { await createLot(data); toast.success('LOT başarıyla oluşturuldu'); setModalOpen(false); fetchData(); }
        catch (err) { toast.error(hataMetni(err, 'LOT oluşturulamadı')); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Bu LOT kaydını pasife almak istiyor musunuz?')) return;
        try { await deleteLot(id); toast.success('LOT pasife alındı'); fetchData(); }
        catch (err) { toast.error(hataMetni(err, 'LOT pasife alınamadı')); }
    };

    const formatDate = useCallback((d) => d ? new Date(d).toLocaleDateString('tr-TR') : '—', []);

    const baseLotlar = tab === 'skt' ? sktLotlar : lotlar;
    const displayLotlar = useMemo(() => {
        if (!searchQuery.trim()) return baseLotlar;
        const q = searchQuery.toLowerCase();
        return baseLotlar.filter(lot =>
            (lot.urun?.isim || '').toLowerCase().includes(q) ||
            (lot.lot_no || '').toLowerCase().includes(q) ||
            (lot.parti_no || '').toLowerCase().includes(q) ||
            (lot.urun?.marka?.isim || '').toLowerCase().includes(q)
        );
    }, [baseLotlar, searchQuery]);

    const searching = searchQuery.trim().length > 0;

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
                <button onClick={() => setModalOpen(true)}
                    className="h-10 sm:h-11 px-4 sm:px-5 bg-gradient-to-r from-amber-600 to-amber-500 text-white text-[13px] sm:text-[14px] font-bold rounded-xl
                        shadow-lg shadow-amber-500/20 hover:shadow-amber-500/35 active:scale-[0.97] transition-all duration-200 flex items-center gap-2">
                    <Plus className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5px]" />
                    <span className="hidden sm:inline">Yeni LOT</span>
                </button>
            </div>

            {/* ════ Controls ════ */}
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
                    onClick={() => { setSearchOpen(!searchOpen); if (searchOpen) setSearchQuery(''); }}
                    className={`w-10 h-10 rounded-xl border flex items-center justify-center shrink-0 transition-all duration-200
                        ${searchOpen ? 'bg-amber-50 border-amber-200 text-amber-600' : 'bg-white border-slate-200 text-slate-400 hover:text-amber-600 hover:border-amber-300'}`}>
                    {searchOpen ? <X className="w-4 h-4" /> : <Search className="w-4 h-4" />}
                </button>
            </div>

            {/* ════ Search ════ */}
            <div className="overflow-hidden transition-all duration-300 ease-out" style={{ maxHeight: searchOpen ? 52 : 0, opacity: searchOpen ? 1 : 0 }}>
                <div className="relative">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input ref={searchRef} type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Ürün, LOT no veya marka ara..."
                        className="w-full h-11 pl-10 pr-10 text-[14px] font-medium rounded-xl border border-slate-200 bg-white
                            text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-[3px] focus:ring-amber-500/10 focus:border-amber-400 transition-all duration-200" />
                    {searchQuery && (
                        <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center transition-colors">
                            <X className="w-3 h-3 text-slate-500" />
                        </button>
                    )}
                </div>
            </div>

            {/* ════ MOBILE: Cards ════ */}
            <div className="md:hidden space-y-2.5">
                {loading ? (
                    [...Array(4)].map((_, i) => <ShimmerCard key={i} />)
                ) : displayLotlar.length === 0 ? (
                    <div className="bg-white rounded-2xl border border-slate-200/80">
                        <EmptyState searching={searching} query={searchQuery} />
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
                                <tr><td colSpan={6}><EmptyState searching={searching} query={searchQuery} /></td></tr>
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
                        {searching ? `${displayLotlar.length} sonuç` : `${displayLotlar.length} kayıt`}
                    </p>
                    <div className="flex items-center gap-1.5">
                        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                            className="h-9 w-9 rounded-xl bg-white border border-slate-200 text-slate-600 disabled:opacity-30 hover:border-amber-300 active:scale-95 transition-all duration-200 flex items-center justify-center">
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-[13px] font-bold text-amber-700 bg-amber-50 border border-amber-200/80 px-3 py-1.5 rounded-xl min-w-[36px] text-center">{page + 1}</span>
                        <button onClick={() => displayLotlar.length === limit && setPage(page + 1)} disabled={displayLotlar.length < limit}
                            className="h-9 w-9 rounded-xl bg-white border border-slate-200 text-slate-600 disabled:opacity-30 hover:border-amber-300 active:scale-95 transition-all duration-200 flex items-center justify-center">
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            <LotModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSave} urunler={urunler} />
        </div>
    );
}