import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Container, Plus, X, Barcode, Search, ChevronLeft, ChevronRight, MapPin } from 'lucide-react';
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

    const inputClass = `w-full h-11 px-4 text-[14px] font-medium rounded-xl border border-slate-200 bg-slate-50/50
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10
    focus:border-blue-500 focus:bg-white transition-all duration-300`;
    const labelClass = "text-[12px] font-bold text-slate-700 mb-2 block tracking-wide uppercase";

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-md" />
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-fade-in ring-1 ring-slate-900/10" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-cyan-100 border border-cyan-200 flex items-center justify-center">
                            <Container className="w-5 h-5 text-cyan-600" />
                        </div>
                        <div>
                            <h3 className="text-[18px] font-extrabold text-slate-900">Yeni Palet Kaydı</h3>
                            <p className="text-[12px] font-medium text-slate-500 mt-0.5">LOT, koli ve raf bilgilerini giriniz</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 flex items-center justify-center">
                        <X className="w-5 h-5 text-slate-500" />
                    </button>
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
                }} className="p-6 space-y-5">
                    <div>
                        <label className={labelClass}>LOT / Parti *</label>
                        <select className={`${inputClass} appearance-none`} value={form.lot_id} onChange={e => setForm({ ...form, lot_id: e.target.value })} required>
                            <option value="">LOT seçin...</option>
                            {lotlar.map(l => <option key={l.id} value={l.id}>LOT: {l.lot_no} — {l.urun?.isim || `Ürün #${l.urun_id}`}</option>)}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Palet Barkod No *</label>
                            <input className={inputClass} value={form.palet_no} onChange={e => setForm({ ...form, palet_no: e.target.value })} required />
                        </div>
                        <div>
                            <label className={labelClass}>Vardiya</label>
                            <input className={inputClass} value={form.vardiya} onChange={e => setForm({ ...form, vardiya: e.target.value })} placeholder="A / B / C" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Koli Adedi *</label>
                            <input type="number" min="0" className={inputClass} value={form.koli_adedi} onChange={e => setForm({ ...form, koli_adedi: e.target.value })} required />
                        </div>
                        <div>
                            <label className={labelClass}>Palet Ağırlığı (kg)</label>
                            <input type="number" min="0" step="0.01" className={inputClass} value={form.palet_kg} onChange={e => setForm({ ...form, palet_kg: e.target.value })} />
                        </div>
                    </div>

                    <div className="flex gap-3 pt-4 border-t border-slate-100">
                        <button type="button" onClick={onClose} className="flex-1 h-11 rounded-xl border border-slate-200 text-[14px] font-bold text-slate-600 hover:bg-slate-50">İptal</button>
                        <button type="submit" className="flex-1 h-11 rounded-xl bg-cyan-600 text-[14px] font-bold text-white hover:bg-cyan-700 shadow-lg hover:-translate-y-0.5 transition-all">Paleti Kaydet</button>
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
    const limit = 20;

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

    // Fiziksel barkod okuyucu ile arama
    useBarcodeScanner({
        isEnabled: !modalOpen && !cameraScannerOpen,
        onScan: async (code) => {
            setSearch(code);
            try {
                const res = await getPaletByBarkod(code);
                toast.success(`Palet bulundu: ${res.data.palet_no}`, { icon: '📦' });
            } catch {
                toast.error(`Bu barkoda ait palet bulunamadı: ${code}`);
            }
        }
    });

    const handleSave = async (data) => {
        try {
            await createPalet(data);
            toast.success('Palet başarıyla oluşturuldu');
            setModalOpen(false);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Palet oluşturulamadı');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Bu paleti pasife almak (depodan çıkarmak) istiyor musunuz?')) return;
        try {
            await deletePalet(id);
            toast.success('Palet pasife alındı');
            fetchData();
        } catch { toast.error('İşlem başarısız'); }
    };

    const filtered = search
        ? paletler.filter(p => p.palet_no?.includes(search) || p.lot?.urun?.isim?.toLowerCase().includes(search.toLowerCase()))
        : paletler;

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-cyan-100 border border-cyan-200 flex items-center justify-center">
                        <Container className="w-5 h-5 text-cyan-600" />
                    </div>
                    <div>
                        <h2 className="text-[17px] font-extrabold text-slate-800">Palet Yönetimi</h2>
                        <p className="text-[12px] font-medium text-slate-500">Palet barkodları ve lokasyonlarını yönetin</p>
                    </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <div className="relative flex-1 sm:w-[260px]">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input type="text" placeholder="Palet no veya ürün ara..." value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="w-full h-11 pl-10 pr-4 text-[14px] rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10" />
                    </div>
                    <button onClick={() => setCameraScannerOpen(true)}
                        className="h-11 w-11 flex items-center justify-center rounded-xl bg-slate-100 border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all flex-shrink-0"
                        title="Kamera ile Barkod Oku">
                        <Barcode className="w-5 h-5" />
                    </button>
                    <button onClick={() => setModalOpen(true)}
                        className="h-11 px-5 bg-cyan-600 text-white text-[14px] font-bold rounded-xl whitespace-nowrap hover:bg-cyan-700 shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2">
                        <Plus className="w-5 h-5 stroke-[2.5px]" /> <span className="hidden sm:inline">Yeni Palet</span>
                    </button>
                </div>
            </div>

            {/* Tablo */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div className="overflow-x-auto min-h-[350px]">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200/80">
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">Palet No</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">Ürün / LOT</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">Koli</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest hidden md:table-cell">Ağırlık</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest hidden sm:table-cell">Raf</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest hidden lg:table-cell">Vardiya</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest text-right">İşlem</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                [...Array(5)].map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        {[...Array(7)].map((_, j) => <td key={j} className="px-5 py-4"><div className="h-4 bg-slate-200 rounded w-20" /></td>)}
                                    </tr>
                                ))
                            ) : filtered.length === 0 ? (
                                <tr>
                                    <td colSpan={7}>
                                        <div className="flex flex-col items-center justify-center py-20 text-center">
                                            <Container className="w-12 h-12 text-slate-200 mb-3" />
                                            <p className="text-[14px] font-bold text-slate-600">Palet bulunamadı</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filtered.map(palet => (
                                    <tr key={palet.id} className="hover:bg-blue-50/30 transition-colors group">
                                        <td className="px-5 py-4">
                                            <code className="text-[13px] font-bold text-cyan-700 bg-cyan-50 px-2.5 py-1 rounded-lg border border-cyan-200">{palet.palet_no}</code>
                                        </td>
                                        <td className="px-5 py-4">
                                            <p className="text-[14px] font-bold text-slate-800">{palet.lot?.urun?.isim || `LOT #${palet.lot_id}`}</p>
                                            <p className="text-[11px] text-slate-400 mt-0.5">LOT: {palet.lot?.lot_no || '-'}</p>
                                        </td>
                                        <td className="px-5 py-4">
                                            <span className="text-[16px] font-extrabold text-slate-800">{palet.koli_adedi}</span>
                                        </td>
                                        <td className="px-5 py-4 hidden md:table-cell">
                                            <span className="text-[13px] text-slate-600">{palet.palet_kg ? `${palet.palet_kg} kg` : '—'}</span>
                                        </td>
                                        <td className="px-5 py-4 hidden sm:table-cell">
                                            {palet.raf ? (
                                                <div className="flex items-center gap-1.5">
                                                    <MapPin className="w-3.5 h-3.5 text-emerald-500" />
                                                    <span className="text-[13px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-200">{palet.raf.kod}</span>
                                                </div>
                                            ) : <span className="text-[13px] text-slate-400">Atanmamış</span>}
                                        </td>
                                        <td className="px-5 py-4 hidden lg:table-cell">
                                            <span className="text-[13px] text-slate-600">{palet.vardiya || '—'}</span>
                                        </td>
                                        <td className="px-5 py-4 text-right">
                                            <button onClick={() => handleDelete(palet.id)}
                                                className="text-[12px] font-bold text-slate-400 hover:text-red-600 transition-colors">
                                                Çıkar
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="bg-slate-50 border-t border-slate-200/80 px-5 py-3 flex items-center justify-between">
                    <p className="text-[13px] text-slate-500">{filtered.length} palet</p>
                    <div className="flex items-center gap-2">
                        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                            className="h-8 px-3 rounded-lg bg-white border border-slate-200 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 transition-all">
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-[13px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1 rounded-lg">{page + 1}</span>
                        <button onClick={() => filtered.length === limit && setPage(page + 1)} disabled={filtered.length < limit}
                            className="h-8 px-3 rounded-lg bg-white border border-slate-200 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 transition-all">
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

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
                        toast.error(`Bu numaraya ait palet yok: ${code}`);
                    }
                }}
            />
        </div>
    );
}
