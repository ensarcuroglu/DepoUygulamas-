import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Container, Plus, X, Barcode, Search, ChevronLeft, ChevronRight, MapPin, PackageOpen, LayoutGrid, Scale, Clock, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { getPaletler, createPalet, deletePalet, getSonrakiPaletNo, getLotlar, getPaletByBarkod } from '../services/api';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';

function PaletModal({ isOpen, onClose, onSave, lotlar, sonrakiNo }) {
    const [form, setForm] = useState({ lot_id: '', palet_no: '', raf_id: '', koli_adedi: 0, palet_kg: 0, vardiya: '' });

    useEffect(() => {
        if (isOpen) setForm({ lot_id: '', palet_no: sonrakiNo || '', raf_id: '', koli_adedi: 0, palet_kg: 0, vardiya: '' });
    }, [isOpen, sonrakiNo]);

    if (!isOpen) return null;

    const inputClass = `w-full h-14 px-5 text-[15px] font-bold rounded-2xl border-2 border-slate-100 bg-slate-50
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10
    focus:border-blue-500 focus:bg-white transition-all duration-300 shadow-sm`;
    const labelClass = "text-[12px] font-extrabold text-slate-500 mb-2.5 block tracking-widest uppercase ml-1";

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-6" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" />
            <div className="relative bg-white rounded-t-[32px] sm:rounded-[32px] shadow-2xl w-full max-w-lg overflow-hidden animate-slide-up sm:animate-fade-in" onClick={e => e.stopPropagation()}>

                {/* Mobile Drag Handle */}
                <div className="w-12 h-1.5 bg-slate-200 rounded-full mx-auto mt-4 sm:hidden" />

                <div className="flex items-center justify-between px-6 py-5 sm:mt-0">
                    <div>
                        <h3 className="text-[22px] font-black text-slate-900 tracking-tight">Yeni Palet</h3>
                        <p className="text-[13px] font-medium text-slate-500 mt-1">Depoya yeni bir palet girişi yapın.</p>
                    </div>
                </div>

                <form onSubmit={e => {
                    e.preventDefault();
                    const data = {
                        ...form,
                        lot_id: Number(form.lot_id),
                        raf_id: form.raf_id ? Number(form.raf_id) : null,
                        koli_adedi: Number(form.koli_adedi),
                        palet_kg: Number(form.palet_kg)
                    };
                    onSave(data);
                }} className="p-6 pt-2 space-y-6 max-h-[75vh] overflow-y-auto">
                    <div>
                        <label className={labelClass}>LOT / Parti Seçimi <span className="text-red-500">*</span></label>
                        <select className={`${inputClass} appearance-none`} value={form.lot_id} onChange={e => setForm({ ...form, lot_id: e.target.value })} required>
                            <option value="">Ürün veya LOT seçin...</option>
                            {lotlar.map(l => <option key={l.id} value={l.id}>LOT: {l.lot_no} — {l.urun?.isim || `Ürün #${l.urun_id}`}</option>)}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Palet No <span className="text-red-500">*</span></label>
                            <input className={inputClass} value={form.palet_no} onChange={e => setForm({ ...form, palet_no: e.target.value })} required placeholder="PLT-X" />
                        </div>
                        <div>
                            <label className={labelClass}>Vardiya</label>
                            <input className={inputClass} value={form.vardiya} onChange={e => setForm({ ...form, vardiya: e.target.value })} placeholder="Örn: Gündüz" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Koli <span className="text-red-500">*</span></label>
                            <input type="number" min="0" className={inputClass} value={form.koli_adedi} onChange={e => setForm({ ...form, koli_adedi: e.target.value })} required />
                        </div>
                        <div>
                            <label className={labelClass}>Ağırlık (kg)</label>
                            <input type="number" min="0" step="0.01" className={inputClass} value={form.palet_kg} onChange={e => setForm({ ...form, palet_kg: e.target.value })} />
                        </div>
                    </div>

                    <div className="flex gap-3 pt-6 border-t border-slate-100">
                        <button type="button" onClick={onClose} className="flex-1 h-14 rounded-2xl border-2 border-slate-100 text-[15px] font-bold text-slate-600 hover:bg-slate-50 active:scale-95 transition-all">
                            İptal
                        </button>
                        <button type="submit" className="flex-1 h-14 rounded-2xl bg-blue-600 text-[15px] font-bold text-white shadow-[0_8px_16px_-6px_rgba(37,99,235,0.4)] hover:bg-blue-700 active:scale-95 hover:-translate-y-0.5 transition-all">
                            Kaydet
                        </button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}

export default function PaletlerPage() {
    const [paletler, setPaletler] = useState([]);
    const [lotlar, setLotlar] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [sonrakiNo, setSonrakiNo] = useState('');
    const [search, setSearch] = useState('');
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);
    const [page, setPage] = useState(0);
    const limit = 24;

    const fetchData = () => {
        setLoading(true);
        Promise.all([
            getPaletler({ skip: page * limit, limit }),
            getLotlar({ limit: 200 }),
            getSonrakiPaletNo()
        ]).then(([palRes, lotRes, noRes]) => {
            setPaletler(palRes.data);
            setLotlar(lotRes.data);
            setSonrakiNo(noRes.data.palet_no);
        }).catch(() => toast.error('Veriler yüklenemedi'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [page]);

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

    const handleSave = async (data) => {
        try {
            await createPalet(data);
            toast.success('Palet sisteme eklendi!');
            setModalOpen(false);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Palet eklenemedi');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Bu paleti depodan çıkarmak (pasif yapmak) istiyor musunuz?')) return;
        try {
            await deletePalet(id);
            toast.success('Palet pasife alındı');
            fetchData();
        } catch { toast.error('Çıkarma işlemi başarısız'); }
    };

    const filtered = search
        ? paletler.filter(p => p.palet_no?.includes(search) || p.lot?.urun?.isim?.toLowerCase().includes(search.toLowerCase()))
        : paletler;

    return (
        <div className="pb-24 sm:pb-8 max-w-[1400px] mx-auto px-4 sm:px-6 pt-4 sm:pt-6">
            {/* Header & Search Toolbar */}
            <div className="flex flex-col gap-5 mb-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30 flex items-center justify-center">
                            <LayoutGrid className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-[24px] font-black text-slate-900 tracking-tight leading-none">Paletler</h1>
                            <p className="text-[13px] font-medium text-slate-500 mt-1">Depo içi lokasyon ve palet takibi</p>
                        </div>
                    </div>

                    {/* Desktop Button */}
                    <button
                        onClick={() => setModalOpen(true)}
                        className="hidden sm:flex h-12 px-6 bg-slate-900 text-white text-[14px] font-bold rounded-2xl hover:bg-slate-800 shadow-xl shadow-slate-900/20 active:scale-95 transition-all items-center gap-2"
                    >
                        <Plus className="w-5 h-5" strokeWidth={3} /> <span>Yeni Palet</span>
                    </button>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Palet no veya ürün ara..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="w-full h-14 pl-12 pr-4 text-[15px] font-bold rounded-2xl border-2 border-slate-100 bg-white focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all shadow-sm text-slate-800 placeholder-slate-400"
                        />
                    </div>
                    <button
                        onClick={() => setCameraScannerOpen(true)}
                        className="h-14 w-14 flex items-center justify-center rounded-2xl bg-white border-2 border-slate-100 text-slate-600 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50 transition-all shadow-sm flex-shrink-0 active:scale-95"
                    >
                        <Barcode className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="h-56 bg-white rounded-3xl border border-slate-100 animate-pulse" />
                    ))}
                </div>
            ) : filtered.length === 0 ? (
                <div className="bg-white rounded-3xl border border-slate-100 p-12 text-center shadow-sm">
                    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Container className="w-10 h-10 text-slate-300" />
                    </div>
                    <p className="text-[16px] font-bold text-slate-700">Palet bulunamadı</p>
                    <p className="text-[13px] font-medium text-slate-400 mt-1">Farklı bir arama yapın veya yeni kayıt oluşturun.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
                    {filtered.map(palet => (
                        <div key={palet.id} className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100/80 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden flex flex-col justify-between min-h-[220px]">

                            {/* Decorative background circle */}
                            <div className="absolute -right-6 -top-6 w-24 h-24 rounded-full bg-gradient-to-br from-blue-50 to-cyan-50 opacity-50 group-hover:scale-150 transition-transform duration-500 pointer-events-none" />

                            <div>
                                {/* Top row: Palet no and actions */}
                                <div className="flex items-center justify-between mb-4 relative z-10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                                            <Container className="w-5 h-5 text-blue-600" />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest">Palet No</p>
                                            <p className="text-[15px] font-black text-slate-800 leading-tight bg-slate-100 px-2 py-0.5 rounded-lg border border-slate-200 inline-block mt-0.5">{palet.palet_no}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(palet.id)}
                                        className="w-10 h-10 rounded-xl bg-red-50 text-red-500 flex items-center justify-center opacity-100 sm:opacity-0 sm:group-hover:opacity-100 hover:bg-red-500 hover:text-white transition-all active:scale-95"
                                        title="Paleti Çıkar"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>

                                {/* Product Info */}
                                <div className="mb-4 relative z-10">
                                    <h3 className="text-[16px] font-extrabold text-slate-900 line-clamp-2 leading-snug">{palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}</h3>
                                    <div className="flex items-center gap-2 mt-2">
                                        <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                                            LOT: {palet.lot?.lot_no || '-'}
                                        </span>
                                    </div>
                                </div>

                                {/* Metrics Grid */}
                                <div className="grid grid-cols-2 gap-2 mb-4 relative z-10">
                                    <div className="bg-slate-50 border border-slate-100 rounded-2xl p-3 flex flex-col items-center justify-center text-center">
                                        <PackageOpen className="w-5 h-5 text-indigo-500 mb-1" />
                                        <p className="text-[18px] font-black text-slate-800 leading-none">{palet.koli_adedi}</p>
                                        <p className="text-[9px] font-extrabold text-slate-400 uppercase tracking-widest mt-1">Koli Adedi</p>
                                    </div>
                                    <div className="bg-slate-50 border border-slate-100 rounded-2xl p-3 flex flex-col items-center justify-center text-center">
                                        <Scale className="w-5 h-5 text-emerald-500 mb-1" />
                                        <p className="text-[18px] font-black text-slate-800 leading-none">{palet.palet_kg ? palet.palet_kg : '-'}</p>
                                        <p className="text-[9px] font-extrabold text-slate-400 uppercase tracking-widest mt-1">Ağırlık (KG)</p>
                                    </div>
                                </div>
                            </div>

                            {/* Footer info: Raf and Vardiya */}
                            <div className="flex items-center justify-between pt-3 border-t border-slate-100 relative z-10">
                                <div className="flex items-center gap-1.5">
                                    <MapPin className={`w-4 h-4 ${palet.raf ? 'text-blue-500' : 'text-slate-300'}`} />
                                    <span className={`text-[12px] font-bold ${palet.raf ? 'text-blue-700' : 'text-slate-400'}`}>
                                        {palet.raf ? palet.raf.kod : 'Raf Yok'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <Clock className="w-4 h-4 text-slate-300" />
                                    <span className="text-[12px] font-bold text-slate-500 line-clamp-1">{palet.vardiya || 'Belirtilmedi'}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {!loading && filtered.length > 0 && (
                <div className="mt-8 flex items-center justify-center gap-3">
                    <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                        className="h-10 px-4 rounded-xl bg-white border-2 border-slate-100 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 hover:text-blue-600 transition-all flex items-center justify-center">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="h-10 px-4 flex items-center justify-center rounded-xl bg-blue-50 border-2 border-blue-100">
                        <span className="text-[13px] font-black text-blue-700">Sayfa {page + 1}</span>
                    </div>
                    <button onClick={() => filtered.length === limit && setPage(page + 1)} disabled={filtered.length < limit}
                        className="h-10 px-4 rounded-xl bg-white border-2 border-slate-100 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 hover:text-blue-600 transition-all flex items-center justify-center">
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            )}

            {/* Mobile Floating Action Button (FAB) */}
            <button
                onClick={() => setModalOpen(true)}
                className="sm:hidden fixed bottom-6 right-6 w-16 h-16 bg-blue-600 text-white rounded-full shadow-[0_8px_30px_rgb(37,99,235,0.4)] flex items-center justify-center hover:bg-blue-700 active:scale-95 transition-all z-40"
            >
                <Plus className="w-8 h-8" strokeWidth={2.5} />
            </button>

            <PaletModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSave} lotlar={lotlar} sonrakiNo={sonrakiNo} />

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
