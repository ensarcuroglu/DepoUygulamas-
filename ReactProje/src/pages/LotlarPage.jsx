import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Layers, Plus, Search, X, Calendar, Package, AlertTriangle, Clock, ChevronLeft, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { getLotlar, createLot, deleteLot, getSktYaklasanLotlar, getUrunler } from '../services/api';

function LotModal({ isOpen, onClose, onSave, urunler }) {
    const [form, setForm] = useState({ urun_id: '', lot_no: '', parti_no: '', uretim_tarihi: '', son_kullanma_tarihi: '', aciklama: '' });

    useEffect(() => {
        if (isOpen) setForm({ urun_id: '', lot_no: '', parti_no: '', uretim_tarihi: '', son_kullanma_tarihi: '', aciklama: '' });
    }, [isOpen]);

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
                        <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center">
                            <Layers className="w-5 h-5 text-amber-600" />
                        </div>
                        <div>
                            <h3 className="text-[18px] font-extrabold text-slate-900">Yeni LOT Kaydı</h3>
                            <p className="text-[12px] font-medium text-slate-500 mt-0.5">Üretim partisi ve SKT bilgilerini giriniz</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 flex items-center justify-center">
                        <X className="w-5 h-5 text-slate-500" />
                    </button>
                </div>

                <form onSubmit={e => { e.preventDefault(); onSave({ ...form, urun_id: Number(form.urun_id) }); }} className="p-6 space-y-5">
                    <div>
                        <label className={labelClass}>Ürün *</label>
                        <select className={`${inputClass} appearance-none`} value={form.urun_id} onChange={e => setForm({ ...form, urun_id: e.target.value })} required>
                            <option value="">Ürün seçin...</option>
                            {urunler.map(u => <option key={u.id} value={u.id}>{u.isim} ({u.marka?.isim || '-'})</option>)}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>LOT Numarası *</label>
                            <input className={inputClass} value={form.lot_no} onChange={e => setForm({ ...form, lot_no: e.target.value })} placeholder="8690684001039" required />
                        </div>
                        <div>
                            <label className={labelClass}>Parti Numarası</label>
                            <input className={inputClass} value={form.parti_no} onChange={e => setForm({ ...form, parti_no: e.target.value })} placeholder="P-2024" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Üretim Tarihi</label>
                            <input type="date" className={inputClass} value={form.uretim_tarihi} onChange={e => setForm({ ...form, uretim_tarihi: e.target.value })} />
                        </div>
                        <div>
                            <label className={labelClass}>Son Kullanma Tarihi</label>
                            <input type="date" className={inputClass} value={form.son_kullanma_tarihi} onChange={e => setForm({ ...form, son_kullanma_tarihi: e.target.value })} />
                        </div>
                    </div>

                    <div>
                        <label className={labelClass}>Açıklama</label>
                        <textarea className={`${inputClass} h-20 resize-none py-3`} value={form.aciklama} onChange={e => setForm({ ...form, aciklama: e.target.value })} placeholder="Parti hakkında not..." />
                    </div>

                    <div className="flex gap-3 pt-4 border-t border-slate-100">
                        <button type="button" onClick={onClose} className="flex-1 h-11 rounded-xl border border-slate-200 text-[14px] font-bold text-slate-600 hover:bg-slate-50">İptal</button>
                        <button type="submit" className="flex-1 h-11 rounded-xl bg-amber-600 text-[14px] font-bold text-white hover:bg-amber-700 shadow-lg hover:-translate-y-0.5 transition-all">LOT Kaydet</button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}

export default function LotlarPage() {
    const [lotlar, setLotlar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [tab, setTab] = useState('tumu'); // 'tumu' | 'skt'
    const [sktLotlar, setSktLotlar] = useState([]);
    const [page, setPage] = useState(0);
    const limit = 20;

    const fetchData = () => {
        setLoading(true);
        Promise.all([
            getLotlar({ skip: page * limit, limit }),
            getUrunler({ limit: 200 }),
            getSktYaklasanLotlar(60)
        ]).then(([lotRes, urunRes, sktRes]) => {
            setLotlar(lotRes.data);
            setUrunler(urunRes.data);
            setSktLotlar(sktRes.data);
        }).catch(() => toast.error('Veriler yüklenemedi'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [page]);

    const handleSave = async (data) => {
        try {
            await createLot(data);
            toast.success('LOT başarıyla oluşturuldu');
            setModalOpen(false);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'LOT oluşturulamadı');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Bu LOT kaydını pasife almak istiyor musunuz?')) return;
        try {
            await deleteLot(id);
            toast.success('LOT pasife alındı');
            fetchData();
        } catch { toast.error('İşlem başarısız'); }
    };

    const displayLotlar = tab === 'skt' ? sktLotlar : lotlar;

    const formatDate = (d) => d ? new Date(d).toLocaleDateString('tr-TR') : '—';

    const sktStatus = (skt) => {
        if (!skt) return null;
        const days = Math.ceil((new Date(skt) - new Date()) / (1000 * 60 * 60 * 24));
        if (days < 0) return { label: 'SÜRESI DOLDU', cls: 'bg-red-100 text-red-700 border-red-200' };
        if (days <= 30) return { label: `${days} GÜN`, cls: 'bg-red-50 text-red-600 border-red-200 animate-pulse' };
        if (days <= 90) return { label: `${days} GÜN`, cls: 'bg-amber-50 text-amber-700 border-amber-200' };
        return { label: `${days} GÜN`, cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    };

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center">
                        <Layers className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                        <h2 className="text-[17px] font-extrabold text-slate-800">LOT / Parti Takibi</h2>
                        <p className="text-[12px] font-medium text-slate-500">Üretim partileri ve son kullanma tarihlerini yönetin</p>
                    </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                    {/* Tab toggle */}
                    <div className="flex bg-slate-100 rounded-xl p-1 border border-slate-200">
                        <button onClick={() => setTab('tumu')} className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all ${tab === 'tumu' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                            Tüm LOT'lar
                        </button>
                        <button onClick={() => setTab('skt')} className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all flex items-center gap-1.5 ${tab === 'skt' ? 'bg-white text-red-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                            <AlertTriangle className="w-3.5 h-3.5" /> SKT Uyarı
                            {sktLotlar.length > 0 && <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">{sktLotlar.length}</span>}
                        </button>
                    </div>

                    <button onClick={() => setModalOpen(true)}
                        className="h-11 px-5 bg-amber-600 text-white text-[14px] font-bold rounded-xl whitespace-nowrap hover:bg-amber-700 shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2">
                        <Plus className="w-5 h-5 stroke-[2.5px]" /> <span className="hidden sm:inline">Yeni LOT</span>
                    </button>
                </div>
            </div>

            {/* Tablo */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div className="overflow-x-auto min-h-[350px]">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200/80">
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">Ürün</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">LOT No</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest hidden md:table-cell">Parti</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest hidden sm:table-cell">Üretim</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">SKT</th>
                                <th className="px-5 py-3.5 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest text-right">İşlem</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                [...Array(5)].map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td className="px-5 py-4"><div className="h-4 bg-slate-200 rounded w-28" /></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-slate-200 rounded w-24" /></td>
                                        <td className="px-5 py-4 hidden md:table-cell"><div className="h-4 bg-slate-200 rounded w-16" /></td>
                                        <td className="px-5 py-4 hidden sm:table-cell"><div className="h-4 bg-slate-200 rounded w-20" /></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-slate-200 rounded w-20" /></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-slate-200 rounded w-12" /></td>
                                    </tr>
                                ))
                            ) : displayLotlar.length === 0 ? (
                                <tr>
                                    <td colSpan={6}>
                                        <div className="flex flex-col items-center justify-center py-20 text-center">
                                            <Layers className="w-12 h-12 text-slate-200 mb-3" />
                                            <p className="text-[14px] font-bold text-slate-600">Kayıtlı LOT bulunamadı</p>
                                            <p className="text-[13px] text-slate-400">Yeni LOT ekleyerek başlayın</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                displayLotlar.map(lot => {
                                    const status = sktStatus(lot.son_kullanma_tarihi);
                                    return (
                                        <tr key={lot.id} className="hover:bg-blue-50/30 transition-colors group">
                                            <td className="px-5 py-4">
                                                <p className="text-[14px] font-bold text-slate-800">{lot.urun?.isim || `Ürün #${lot.urun_id}`}</p>
                                                <p className="text-[11px] text-slate-400 mt-0.5">{lot.urun?.marka?.isim || ''}</p>
                                            </td>
                                            <td className="px-5 py-4">
                                                <code className="text-[12px] font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">{lot.lot_no}</code>
                                            </td>
                                            <td className="px-5 py-4 hidden md:table-cell">
                                                <span className="text-[13px] text-slate-600">{lot.parti_no || '—'}</span>
                                            </td>
                                            <td className="px-5 py-4 hidden sm:table-cell">
                                                <span className="text-[13px] text-slate-600">{formatDate(lot.uretim_tarihi)}</span>
                                            </td>
                                            <td className="px-5 py-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[13px] font-medium text-slate-700">{formatDate(lot.son_kullanma_tarihi)}</span>
                                                    {status && (
                                                        <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${status.cls}`}>{status.label}</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-5 py-4 text-right">
                                                <button onClick={() => handleDelete(lot.id)}
                                                    className="text-[12px] font-bold text-slate-400 hover:text-red-600 transition-colors">
                                                    Pasife Al
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {tab === 'tumu' && (
                    <div className="bg-slate-50 border-t border-slate-200/80 px-5 py-3 flex items-center justify-between">
                        <p className="text-[13px] text-slate-500">{displayLotlar.length} kayıt</p>
                        <div className="flex items-center gap-2">
                            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                                className="h-8 px-3 rounded-lg bg-white border border-slate-200 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 transition-all">
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <span className="text-[13px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1 rounded-lg">{page + 1}</span>
                            <button onClick={() => displayLotlar.length === limit && setPage(page + 1)} disabled={displayLotlar.length < limit}
                                className="h-8 px-3 rounded-lg bg-white border border-slate-200 text-[13px] font-bold text-slate-600 disabled:opacity-40 hover:border-blue-400 transition-all">
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <LotModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSave} urunler={urunler} />
        </div>
    );
}
