import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
    Package, Search, Plus, Edit3, Trash2, ChevronLeft, ChevronRight,
    X, Info, Wallet, Layers, Box, SlidersHorizontal, Tag, Barcode,
    AlignLeft, Banknote, Scale, AlertTriangle, CheckCircle2, Download, FileSpreadsheet, FileText,
    Award, Hash, Weight
} from 'lucide-react';
import toast from 'react-hot-toast';
import { exportToExcel, exportToPDF } from '../utils/exportUtils';

import { getUrunler, deleteUrun, getKategoriler, createUrun, updateUrun, getUrunByBarkod, getMarkalar } from '../services/api';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';

// Özel Input Bileşeni (UI/UX Geliştirmesi İçin)
const CustomInput = ({ label, icon: Icon, required, ...props }) => {
    return (
        <div className="flex flex-col gap-1.5 w-full">
            <label className="text-[13px] font-semibold text-slate-700 flex items-center gap-1.5 ml-1">
                {label} {required && <span className="text-red-500 font-bold">*</span>}
            </label>
            <div className="relative group">
                {Icon && (
                    <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors duration-300">
                        <Icon className="w-4.5 h-4.5" />
                    </div>
                )}
                {props.type === 'textarea' ? (
                    <textarea
                        {...props}
                        className={`w-full bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300 placeholder:text-slate-400 resize-none ${Icon ? 'pl-11' : 'pl-4'} pr-4 py-3`}
                    />
                ) : props.type === 'select' ? (
                    <>
                        <select
                            {...props}
                            className={`w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300 appearance-none cursor-pointer ${Icon ? 'pl-11' : 'pl-4'} pr-10`}
                        >
                            {props.children}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 group-focus-within:text-blue-500 transition-colors">
                            <ChevronRight className="w-4 h-4 rotate-90" />
                        </div>
                    </>
                ) : (
                    <input
                        {...props}
                        className={`w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300 placeholder:text-slate-400 ${Icon ? 'pl-11' : 'pl-4'} pr-4`}
                    />
                )}
            </div>
        </div>
    );
};

// Ürün Formu Modal (Profesyonel Tasarım - Mobil & Web Uyumlu)
export function UrunModal({ isOpen, onClose, onSave, urun, kategoriler, markalar }) {
    const [form, setForm] = useState({
        isim: '', barkod: '', ean: '', aciklama: '', kategori_id: '', marka_id: '',
        min_stok: 10, birim: 'Adet', fiyat: 0, ic_adet: 1, gramaj: 0,
    });

    useEffect(() => {
        if (urun) {
            setForm({
                isim: urun.isim || '', barkod: urun.barkod || '', ean: urun.ean || '',
                aciklama: urun.aciklama || '',
                kategori_id: urun.kategori?.id || urun.kategori_id || '',
                marka_id: urun.marka?.id || urun.marka_id || '',
                min_stok: urun.min_stok || 10, birim: urun.birim || 'Adet', fiyat: urun.fiyat || 0,
                ic_adet: urun.ic_adet || 1, gramaj: urun.gramaj || 0,
            });
        } else {
            setForm({ isim: '', barkod: '', ean: '', aciklama: '', kategori_id: '', marka_id: '', min_stok: 10, birim: 'Adet', fiyat: 0, ic_adet: 1, gramaj: 0 });
        }
    }, [urun, isOpen]);

    // Scroll kilitleme
    useEffect(() => {
        if (isOpen) document.body.style.overflow = 'hidden';
        else document.body.style.overflow = 'unset';
        return () => { document.body.style.overflow = 'unset'; };
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSubmit = (e) => {
        e.preventDefault();
        const data = {
            ...form,
            kategori_id: form.kategori_id ? Number(form.kategori_id) : null,
            marka_id: form.marka_id ? Number(form.marka_id) : null,
            ic_adet: Number(form.ic_adet),
            gramaj: Number(form.gramaj),
        };
        onSave(data);
    };

    return createPortal(
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center sm:p-6" style={{ perspective: '1000px' }}>
            {/* Arka plan overlay */}
            <div
                className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300"
                onClick={onClose}
            />

            {/* Modal Kartı */}
            <div
                className="relative bg-slate-100/50 sm:bg-slate-50 w-full max-w-[900px] h-[95vh] sm:h-auto sm:max-h-[90vh] flex flex-col shadow-2xl overflow-hidden
                           rounded-t-[2rem] sm:rounded-[2rem] ring-1 ring-slate-900/5 
                           animate-[slideUp_0.3s_ease-out] sm:animate-[scaleIn_0.3s_ease-out] origin-bottom sm:origin-center"
                onClick={e => e.stopPropagation()}
            >
                {/* Mobilde Çekme Tutamacı (Visual only) */}
                <div className="w-full flex justify-center pt-3 pb-1 sm:hidden absolute top-0 z-20">
                    <div className="w-12 h-1.5 bg-slate-300/60 rounded-full"></div>
                </div>

                {/* Header Alanı (Sabit) */}
                <div className="relative flex items-center justify-between px-6 sm:px-10 py-5 sm:py-6 bg-white border-b border-slate-200/80 z-10 pt-8 sm:pt-6 shrink-0">
                    <div className="flex items-center gap-4 sm:gap-5">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100/60 flex items-center justify-center flex-shrink-0 shadow-[inset_0_2px_10px_rgba(59,130,246,0.08)]">
                            {urun ? <Edit3 className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" /> : <Package className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />}
                        </div>
                        <div>
                            <h3 className="text-[18px] sm:text-[22px] font-extrabold text-slate-900 leading-tight tracking-tight">
                                {urun ? 'Stok Kartını Düzenle' : 'Yeni Stok Kartı Oluştur'}
                            </h3>
                            <p className="text-[13px] sm:text-[14px] font-medium text-slate-500 mt-0.5">
                                {urun ? 'Mevcut ürün detaylarını güncelliyorsunuz.' : 'Envanterinize yeni bir öğe ekleyin.'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-10 h-10 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors shrink-0"
                    >
                        <X className="w-5 h-5 sm:w-6 sm:h-6" />
                    </button>
                </div>

                {/* Form Gövdesi (Kaydırılabilir) */}
                <form id="urun-form" onSubmit={handleSubmit} className="flex-1 overflow-y-auto bg-slate-50/50 p-4 sm:p-8 custom-scrollbar">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-8 max-w-5xl mx-auto">

                        {/* Sol Kolon: Temel Bilgiler */}
                        <div className="bg-white rounded-3xl p-5 sm:p-7 border border-slate-200/60 shadow-sm space-y-6">
                            <div className="flex items-center gap-2 mb-2 pb-4 border-b border-slate-100">
                                <div className="p-1.5 bg-blue-50 rounded-lg text-blue-600">
                                    <Info className="w-5 h-5" />
                                </div>
                                <h4 className="text-[16px] font-bold text-slate-800 tracking-tight">Temel Bilgiler</h4>
                            </div>

                            <div className="space-y-5">
                                <CustomInput
                                    label="Ürün Adı"
                                    icon={Tag}
                                    required
                                    autoFocus
                                    value={form.isim}
                                    onChange={e => setForm({ ...form, isim: e.target.value })}
                                    placeholder="Örn: Yüksük Makarna 500g"
                                />

                                <div className="grid grid-cols-2 gap-4">
                                    <CustomInput
                                        label="Barkod / Ürün Kodu"
                                        icon={Barcode}
                                        value={form.barkod}
                                        onChange={e => setForm({ ...form, barkod: e.target.value })}
                                        placeholder="ARB-001"
                                    />
                                    <CustomInput
                                        label="EAN Numarası"
                                        icon={Hash}
                                        value={form.ean}
                                        onChange={e => setForm({ ...form, ean: e.target.value })}
                                        placeholder="8697430089416"
                                    />
                                </div>

                                <CustomInput
                                    type="select"
                                    label="Marka"
                                    icon={Award}
                                    value={form.marka_id}
                                    onChange={e => setForm({ ...form, marka_id: e.target.value })}
                                >
                                    <option value="">Marka Seçiniz</option>
                                    {markalar.map(m => <option key={m.id} value={m.id}>{m.isim}</option>)}
                                </CustomInput>

                                <CustomInput
                                    type="select"
                                    label="Kategori Sınıfı"
                                    icon={Layers}
                                    value={form.kategori_id}
                                    onChange={e => setForm({ ...form, kategori_id: e.target.value })}
                                >
                                    <option value="">Kategori Seçiniz</option>
                                    {kategoriler.map(k => <option key={k.id} value={k.id}>{k.isim}</option>)}
                                </CustomInput>

                                <CustomInput
                                    type="textarea"
                                    label="Ek Açıklamalar"
                                    icon={AlignLeft}
                                    value={form.aciklama}
                                    onChange={e => setForm({ ...form, aciklama: e.target.value })}
                                    placeholder="Ürün hakkında teknik özellikler veya lokasyon detayları..."
                                    rows="3"
                                />
                            </div>
                        </div>

                        {/* Sağ Kolon: Finans, Stok & Ambalaj */}
                        <div className="bg-white rounded-3xl p-5 sm:p-7 border border-slate-200/60 shadow-sm h-fit space-y-6">
                            <div className="flex items-center gap-2 mb-2 pb-4 border-b border-slate-100">
                                <div className="p-1.5 bg-emerald-50 rounded-lg text-emerald-600">
                                    <Wallet className="w-5 h-5" />
                                </div>
                                <h4 className="text-[16px] font-bold text-slate-800 tracking-tight">Finans, Stok & Ambalaj</h4>
                            </div>

                            <div className="space-y-5">
                                {/* Ambalaj Bilgileri */}
                                <div className="grid grid-cols-2 gap-4">
                                    <CustomInput
                                        type="number"
                                        label="Koli İçi Adet"
                                        icon={Box}
                                        value={form.ic_adet}
                                        onChange={e => setForm({ ...form, ic_adet: Number(e.target.value) })}
                                        min="1"
                                    />
                                    <CustomInput
                                        type="number"
                                        label="Gramaj (kg)"
                                        icon={Weight}
                                        value={form.gramaj}
                                        onChange={e => setForm({ ...form, gramaj: Number(e.target.value) })}
                                        min="0"
                                        step="0.001"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <CustomInput
                                        type="number"
                                        label="Kritik Stok Limiti"
                                        icon={AlertTriangle}
                                        value={form.min_stok}
                                        onChange={e => setForm({ ...form, min_stok: Number(e.target.value) })}
                                        min="0"
                                    />
                                    <CustomInput
                                        type="select"
                                        label="Ölçü Birimi"
                                        icon={Scale}
                                        value={form.birim}
                                        onChange={e => setForm({ ...form, birim: e.target.value })}
                                    >
                                        {['Adet', 'Kg', 'Metre', 'Rulo', 'Kutu', 'Litre'].map(b => <option key={b} value={b}>{b}</option>)}
                                    </CustomInput>
                                </div>

                                <div className="pt-2">
                                    <div className="flex flex-col gap-1.5 w-full">
                                        <label className="text-[13px] font-semibold text-slate-700 flex items-center ml-1">Birim Fiyat</label>
                                        <div className="relative group flex items-center">
                                            <div className="absolute left-0 top-0 bottom-0 w-12 flex items-center justify-center bg-slate-100 border-r border-slate-200 rounded-l-xl text-slate-500 font-bold group-focus-within:bg-blue-50 group-focus-within:text-blue-600 group-focus-within:border-blue-200 transition-colors">
                                                ₺
                                            </div>
                                            <input
                                                type="number" step="0.01" min="0"
                                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all duration-300 pl-14 pr-4 rounded-l-none border-l-0"
                                                value={form.fiyat}
                                                onChange={e => setForm({ ...form, fiyat: Number(e.target.value) })}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Görsel ipucu: Bilgi Notu */}
                            <div className="mt-6 bg-amber-50 rounded-2xl p-4 border border-amber-100 flex items-start gap-3">
                                <CheckCircle2 className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
                                <p className="text-[13px] text-amber-700 font-medium leading-relaxed">
                                    Stok miktarı artık otomatik hesaplanır. Yeni stok girişi yapmak için <strong>LOT</strong> oluşturun ve <strong>Palet</strong> tanımlayın.
                                </p>
                            </div>
                        </div>
                    </div>
                </form>

                {/* Footer Alanı (Sabit) */}
                <div className="bg-white/90 backdrop-blur-md border-t border-slate-200/80 p-5 sm:px-10 flex flex-col-reverse sm:flex-row items-center justify-end gap-3 z-10 shrink-0 pb-8 sm:pb-5">
                    <button
                        type="button"
                        onClick={onClose}
                        className="w-full sm:w-[140px] h-12 rounded-xl border-2 border-slate-200 text-[14px] font-bold text-slate-600
                                 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-800 transition-all active:scale-95"
                    >
                        İptal Et
                    </button>
                    <button
                        type="submit"
                        form="urun-form"
                        className="group relative w-full sm:w-[220px] h-12 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-[14px] font-bold text-white
                                 hover:from-blue-500 hover:to-indigo-500 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 overflow-hidden active:scale-95"
                    >
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out"></div>
                        <span className="relative z-10 flex items-center justify-center gap-2">
                            {urun ? 'Değişiklikleri Kaydet' : 'Stok Kartını Kaydet'}
                        </span>
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
}

// Durum Etiketi
function DurumBadge({ durum }) {
    const map = {
        'Yeterli': 'bg-emerald-50 text-emerald-700 border-emerald-200 shadow-sm shadow-emerald-500/10',
        'Kritik Stok': 'bg-red-50 text-red-700 border-red-200 shadow-sm shadow-red-500/10 animate-pulse',
        'Stok Yok': 'bg-slate-100 text-slate-600 border-slate-300',
    };
    return (
        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-extrabold tracking-wider uppercase border ${map[durum] || map['Yeterli']}`}>
            {durum}
        </span>
    );
}

// Stok Durumunu Belirle (computed stok_miktari vs min_stok)
function stokDurumu(urun) {
    const stok = urun.stok_miktari ?? 0;
    if (stok <= 0) return 'Stok Yok';
    if (stok <= (urun.min_stok ?? 0)) return 'Kritik Stok';
    return 'Yeterli';
}

// Ana Sayfa Bileşeni
export default function App() {
    const [urunler, setUrunler] = useState([]);
    const [kategoriler, setKategoriler] = useState([]);
    const [markalar, setMarkalar] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filterKategori, setFilterKategori] = useState('');
    const [filterMarka, setFilterMarka] = useState('');
    const [modalOpen, setModalOpen] = useState(false);
    const [editUrun, setEditUrun] = useState(null);
    const [page, setPage] = useState(0);
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);
    const [exportMenuOpen, setExportMenuOpen] = useState(false);
    const limit = 10;

    // Excel ve PDF'e dönüştürülecek verinin formatı
    const getFormattedExportData = () => {
        return urunler.map(u => ({
            'Barkod/Kod': u.barkod || '-',
            'EAN': u.ean || '-',
            'Ürün Adı': u.isim,
            'Marka': u.marka?.isim || '-',
            'Kategori': u.kategori?.isim || 'Kategorisiz',
            'Stok (Koli)': u.stok_miktari ?? 0,
            'İç Adet': u.ic_adet || '-',
            'Gramaj': u.gramaj ? `${u.gramaj} kg` : '-',
            'Birim Fiyat': `${u.fiyat} ₺`,
            'Durum': stokDurumu(u),
        }));
    };

    const handleExportExcel = () => {
        setExportMenuOpen(false);
        const data = getFormattedExportData();
        exportToExcel(data, `Urun_Katalogu`);
    };

    const handleExportPDF = () => {
        setExportMenuOpen(false);
        const data = getFormattedExportData();
        const columns = ['Barkod/Kod', 'EAN', 'Ürün Adı', 'Marka', 'Kategori', 'Stok (Koli)', 'Birim Fiyat', 'Durum'];
        exportToPDF(data, columns, `Urun_Katalogu`, 'Güncel Ürün Kartları ve Envanter Raporu');
    };

    // Arka plan klavye dinleyicisi: PC ortamında fiziksel barkod okuyucusu için
    useBarcodeScanner({
        isEnabled: !modalOpen && !cameraScannerOpen,
        onScan: async (scannedCode) => {
            setSearch(scannedCode);
            setPage(0);
            try {
                const res = await getUrunByBarkod(scannedCode);
                toast.success(`Bulundu: ${res.data.isim}`, { icon: '🔍' });
            } catch {
                toast.success(`Aranıyor: ${scannedCode}`, { icon: '🔍' });
            }
        }
    });

    const fetchData = () => {
        setLoading(true);
        const params = { skip: page * limit, limit };
        if (search) params.search = search;
        if (filterKategori) params.kategori_id = filterKategori;
        if (filterMarka) params.marka_id = filterMarka;

        Promise.all([getUrunler(params), getKategoriler(), getMarkalar()])
            .then(([urunRes, katRes, markaRes]) => {
                setUrunler(urunRes.data);
                setKategoriler(katRes.data);
                setMarkalar(markaRes.data);
            })
            .catch(() => toast.error('Veri tabanına ulaşılamadı. Sunucu bağlantısını kontrol edin.'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [page, search, filterKategori, filterMarka]);

    const handleDelete = async (id, isim) => {
        if (!confirm(`"${isim}" ürününü pasife almak istediğinize emin misiniz? (Stok geçmişi korunur)`)) return;
        try {
            await deleteUrun(id);
            toast.success('Ürün başarıyla pasife alındı');
            fetchData();
        } catch { toast.error('İşlem reddedildi. Ürün bir siparişe veya harekete bağlı olabilir.'); }
    };

    const handleSave = async (data) => {
        try {
            if (editUrun) {
                await updateUrun(editUrun.id, data);
                toast.success('Değişiklikler kaydedildi');
            } else {
                await createUrun(data);
                toast.success('Yeni ürün oluşturuldu');
            }
            setModalOpen(false);
            setEditUrun(null);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'İşlem başarısız');
        }
    };

    return (
        <>
            <style dangerouslySetInnerHTML={{
                __html: `
                .custom-scrollbar::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
                @keyframes slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
            `}} />

            <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6 animate-[scaleIn_0.3s_ease-out]">

                {/* Profesyonel Toolbar Kontrol Paneli */}
                <div className="bg-white p-4 sm:p-5 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 sm:gap-5">

                    {/* Sol Alan: Araçlar (Arama & Filtre) */}
                    <div className="flex flex-col sm:flex-row items-center gap-4 w-full lg:flex-1 lg:max-w-4xl">
                        <div className="relative group w-full flex-1 flex gap-2">
                            <div className="relative flex-1">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                <input type="text" placeholder="Barkod, EAN, model no veya ürün ismi ile arayın..." value={search}
                                    onChange={e => { setSearch(e.target.value); setPage(0); }}
                                    className="w-full h-12 pl-11 pr-4 text-[14px] font-medium rounded-2xl border border-slate-200 bg-slate-50
                                    text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all" />
                            </div>
                            <button
                                onClick={() => setCameraScannerOpen(true)}
                                className="h-12 w-12 flex items-center justify-center rounded-2xl bg-slate-100 border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all flex-shrink-0"
                                title="Kamera ile Barkod Okut">
                                <Barcode className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex items-center gap-3 w-full sm:w-auto">
                            <div className="relative flex-1 sm:w-[200px] group">
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center justify-center bg-slate-100 rounded-md p-1">
                                    <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <select value={filterKategori} onChange={e => { setFilterKategori(e.target.value); setPage(0); }}
                                    className="w-full h-12 pl-12 pr-10 text-[14px] font-medium rounded-2xl border border-slate-200 bg-slate-50
                                    text-slate-800 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 appearance-none cursor-pointer transition-all">
                                    <option value="">Tüm Kategoriler</option>
                                    {kategoriler.map(k => <option key={k.id} value={k.id}>{k.isim}</option>)}
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
                                    <ChevronRight className="w-4 h-4 rotate-90" />
                                </div>
                            </div>

                            <div className="relative flex-1 sm:w-[180px] group">
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center justify-center bg-slate-100 rounded-md p-1">
                                    <Award className="w-3.5 h-3.5 text-slate-500 group-focus-within:text-blue-500 transition-colors" />
                                </div>
                                <select value={filterMarka} onChange={e => { setFilterMarka(e.target.value); setPage(0); }}
                                    className="w-full h-12 pl-12 pr-10 text-[14px] font-medium rounded-2xl border border-slate-200 bg-slate-50
                                    text-slate-800 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 appearance-none cursor-pointer transition-all">
                                    <option value="">Tüm Markalar</option>
                                    {markalar.map(m => <option key={m.id} value={m.id}>{m.isim}</option>)}
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
                                    <ChevronRight className="w-4 h-4 rotate-90" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sağ Alan: Aksiyon Butonları (Export & Yeni Ürün) */}
                    <div className="flex items-center gap-3 w-full lg:w-auto">

                        {/* Export Dropdown */}
                        <div className="relative flex-1 lg:flex-none">
                            <button
                                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                                className="w-full h-12 px-4 sm:px-5 bg-white border border-slate-200 text-slate-700 text-[14px] font-bold rounded-2xl flex items-center justify-center gap-2 transition-all hover:bg-slate-50 hover:border-slate-300 shadow-sm active:scale-95"
                            >
                                <Download className="w-5 h-5 text-slate-500" />
                                <span className="hidden sm:block">Dışa Aktar</span>
                            </button>

                            {exportMenuOpen && (
                                <div className="absolute left-0 lg:right-0 lg:left-auto top-[calc(100%+8px)] w-[200px] bg-white rounded-2xl border border-slate-200 shadow-xl py-2 z-[60] animate-[fadeIn_0.15s_ease-out]">
                                    <div className="px-4 py-2 border-b border-slate-50 mb-1">
                                        <p className="text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">Rapor İndir</p>
                                    </div>
                                    <button onClick={handleExportExcel} className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-emerald-50 text-slate-700 hover:text-emerald-700 transition-colors text-left text-[13px] font-bold">
                                        <FileSpreadsheet className="w-4.5 h-4.5 text-emerald-500" /> Excel (.xlsx)
                                    </button>
                                    <button onClick={handleExportPDF} className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-red-50 text-slate-700 hover:text-red-700 transition-colors text-left text-[13px] font-bold">
                                        <FileText className="w-4.5 h-4.5 text-red-500" /> PDF Belgesi
                                    </button>
                                </div>
                            )}
                        </div>

                        <button onClick={() => { setEditUrun(null); setModalOpen(true); }}
                            className="group relative h-12 px-5 sm:px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[14px] font-bold rounded-2xl whitespace-nowrap
                            hover:from-blue-500 hover:to-indigo-500 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5
                            flex items-center justify-center gap-2 flex-1 lg:flex-none overflow-hidden active:scale-95">
                            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out"></div>
                            <Plus className="relative z-10 w-5 h-5 stroke-[2.5px] transition-transform group-hover:rotate-90 duration-300" />
                            <span className="relative z-10 hidden sm:block">Yeni Ürün Ekle</span>
                            <span className="relative z-10 sm:hidden">Yeni</span>
                        </button>
                    </div>
                </div>

                {/* Modern Table Container */}
                <div className="bg-white rounded-3xl border border-slate-200/80 shadow-[0_2px_15px_-3px_rgba(6,81,237,0.05)] overflow-hidden">

                    {/* MOBİL GÖRÜNÜM: Kart Listesi (sm ve altı ekranlar) */}
                    <div className="md:hidden divide-y divide-slate-100">
                        {loading ? (
                            [...Array(4)].map((_, i) => (
                                <div key={i} className="p-4 sm:p-5 animate-pulse flex flex-col gap-3">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="h-4 bg-slate-200 rounded w-32 mb-2"></div>
                                            <div className="h-3 bg-slate-100 rounded w-24"></div>
                                        </div>
                                        <div className="h-6 bg-slate-200 rounded-full w-16"></div>
                                    </div>
                                    <div className="h-4 bg-slate-100 rounded w-1/2"></div>
                                </div>
                            ))
                        ) : urunler.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
                                <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4 border border-slate-100 shadow-inner">
                                    <Package className="w-8 h-8 text-slate-300" />
                                </div>
                                <h3 className="text-[16px] font-bold text-slate-800 mb-1">Eşleşen ürün bulunamadı</h3>
                                <p className="text-[13px] text-slate-500 font-medium max-w-xs mx-auto">
                                    Arama kriterlerinize uyan kayıt yok veya depo tamamen boş.
                                </p>
                            </div>
                        ) : (
                            urunler.map((urun) => (
                                <div key={urun.id} className="p-4 sm:p-5 hover:bg-slate-50/50 transition-colors">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="text-[15px] font-bold text-slate-900 leading-tight pr-2">{urun.isim}</h4>
                                            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                                                <code className="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-bold border border-slate-200/60 break-all">
                                                    {urun.barkod || 'Kodsuz'}
                                                </code>
                                                {urun.marka?.isim && (
                                                    <span className="text-[11px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 font-bold border border-indigo-100">
                                                        {urun.marka.isim}
                                                    </span>
                                                )}
                                                <span className="text-[12px] font-medium text-slate-500 whitespace-nowrap">
                                                    {urun.kategori?.isim || 'Kategorisiz'}
                                                </span>
                                            </div>
                                        </div>
                                        <DurumBadge durum={stokDurumu(urun)} />
                                    </div>

                                    <div className="flex items-end justify-between mt-4">
                                        <div className="flex flex-col gap-1">
                                            <span className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider">Stok / Fiyat</span>
                                            <div className="flex items-baseline gap-2">
                                                <p className="text-[15px] font-extrabold text-slate-800">{urun.stok_miktari ?? 0} <span className="text-[11px] font-bold text-slate-500">koli</span></p>
                                                <span className="text-slate-300">•</span>
                                                <p className="text-[14px] font-bold text-emerald-600">₺{urun.fiyat?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}</p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button onClick={() => { setEditUrun(urun); setModalOpen(true); }}
                                                className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center active:scale-95 transition-transform">
                                                <Edit3 className="w-4.5 h-4.5" />
                                            </button>
                                            <button onClick={() => handleDelete(urun.id, urun.isim)}
                                                className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center active:scale-95 transition-transform">
                                                <Trash2 className="w-4.5 h-4.5" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* MASAÜSTÜ GÖRÜNÜM: Klasik Tablo (md ve üzeri ekranlar) */}
                    <div className="hidden md:block overflow-x-auto min-h-[400px]">
                        <table className="w-full text-left min-w-0">
                            <thead>
                                <tr className="bg-slate-50 border-b border-slate-200/80">
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">Öğe Tanımı</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden sm:table-cell">Barkod</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden lg:table-cell">Marka</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden lg:table-cell">Kategori</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">Stok</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden md:table-cell">Fiyat</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">Durum</th>
                                    <th className="px-4 sm:px-6 py-4 text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap text-right">İşlem</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {loading ? (
                                    [...Array(3)].map((_, i) => (
                                        <tr key={i} className="animate-pulse">
                                            <td className="px-4 sm:px-6 py-4"><div className="h-4 bg-slate-200 rounded-md w-32 mb-2" /><div className="h-3 bg-slate-100 rounded-md w-24" /></td>
                                            <td className="px-4 sm:px-6 py-4 hidden sm:table-cell"><div className="h-4 bg-slate-200 rounded-md w-16" /></td>
                                            <td className="px-4 sm:px-6 py-4 hidden lg:table-cell"><div className="h-4 bg-slate-200 rounded-md w-16" /></td>
                                            <td className="px-4 sm:px-6 py-4 hidden lg:table-cell"><div className="h-4 bg-slate-200 rounded-md w-20" /></td>
                                            <td className="px-4 sm:px-6 py-4"><div className="h-5 bg-slate-200 rounded-md w-12" /></td>
                                            <td className="px-4 sm:px-6 py-4 hidden md:table-cell"><div className="h-5 bg-slate-200 rounded-md w-16" /></td>
                                            <td className="px-4 sm:px-6 py-4"><div className="h-5 bg-slate-200 rounded-full w-16" /></td>
                                            <td className="px-4 sm:px-6 py-4 flex justify-end"><div className="h-8 bg-slate-200 rounded-md w-16" /></td>
                                        </tr>
                                    ))
                                ) : urunler.length === 0 ? (
                                    <tr>
                                        <td colSpan={8}>
                                            <div className="flex flex-col items-center justify-center py-24 text-center">
                                                <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center mb-4 border border-slate-100 shadow-inner">
                                                    <Package className="w-10 h-10 text-slate-300" />
                                                </div>
                                                <h3 className="text-[16px] font-bold text-slate-800 mb-1">Eşleşen ürün bulunamadı</h3>
                                                <p className="text-[13px] text-slate-500 font-medium max-w-sm">
                                                    Arama kriterlerinize uyan kayıt yok veya depo şu an tamamen boş. Yukarıdan "Yeni Ürün Ekle" ile başlayabilirsiniz.
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    urunler.map((urun) => (
                                        <tr key={urun.id} className="hover:bg-blue-50/40 transition-colors group">
                                            <td className="px-4 sm:px-6 py-4">
                                                <p className="text-[14px] font-bold text-slate-900 group-hover:text-blue-700 transition-colors">{urun.isim}</p>
                                                <p className="text-[12px] font-medium text-slate-400 mt-0.5 line-clamp-1 max-w-[160px] sm:max-w-[240px]" title={urun.aciklama}>{urun.aciklama || 'Açıklama girilmemiş'}</p>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 hidden sm:table-cell">
                                                <code className="text-[12px] font-bold tracking-wider text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/60">
                                                    {urun.barkod || 'Yok'}
                                                </code>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 hidden lg:table-cell">
                                                {urun.marka?.isim ? (
                                                    <span className="text-[12px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">
                                                        {urun.marka.isim}
                                                    </span>
                                                ) : (
                                                    <span className="text-[12px] text-slate-400">—</span>
                                                )}
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 hidden lg:table-cell">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-2 h-2 rounded-full bg-indigo-400" />
                                                    <span className="text-[13px] font-medium text-slate-700">{urun.kategori?.isim || 'Kategorisiz'}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4">
                                                <div className="flex items-baseline gap-1">
                                                    <span className="text-[15px] sm:text-[16px] font-extrabold text-slate-800">{urun.stok_miktari ?? 0}</span>
                                                    <span className="text-[11px] font-bold text-slate-400 uppercase">koli</span>
                                                </div>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 hidden md:table-cell">
                                                <span className="text-[13px] sm:text-[14px] font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-xl">
                                                    ₺{urun.fiyat?.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                                                </span>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4"><DurumBadge durum={stokDurumu(urun)} /></td>
                                            <td className="px-4 sm:px-6 py-4">
                                                <div className="flex items-center justify-end gap-2 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => { setEditUrun(urun); setModalOpen(true); }}
                                                        className="w-8 h-8 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-slate-500 hover:text-blue-600 flex items-center justify-center transition-all shadow-sm"
                                                        title="Detay & Düzenle">
                                                        <Edit3 className="w-4 h-4" />
                                                    </button>
                                                    <button onClick={() => handleDelete(urun.id, urun.isim)}
                                                        className="w-8 h-8 rounded-xl bg-white border border-slate-200 hover:border-red-300 hover:bg-red-50 text-slate-500 hover:text-red-600 flex items-center justify-center transition-all shadow-sm"
                                                        title="Pasife Al">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Toolbar */}
                    <div className="bg-slate-50 border-t border-slate-200/80 px-4 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                        <p className="text-[13px] font-medium text-slate-500">
                            Toplam <span className="text-slate-800 font-bold">{urunler.length}</span> kayıt listeleniyor
                        </p>
                        <div className="flex items-center gap-2">
                            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                                className="h-9 px-3.5 rounded-xl bg-white border border-slate-200 flex items-center justify-center gap-1
                                text-[13px] font-bold text-slate-600 shadow-sm
                                hover:border-blue-400 hover:text-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
                                <ChevronLeft className="w-4 h-4" /> <span className="hidden sm:inline">Önceki</span>
                            </button>
                            <div className="h-9 min-w-[36px] px-2 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center
                                text-[13px] font-extrabold text-blue-700 shadow-sm">
                                {page + 1}
                            </div>
                            <button onClick={() => urunler.length === limit && setPage(page + 1)} disabled={urunler.length < limit}
                                className="h-9 px-3.5 rounded-xl bg-white border border-slate-200 flex items-center justify-center gap-1
                                text-[13px] font-bold text-slate-600 shadow-sm
                                hover:border-blue-400 hover:text-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
                                <span className="hidden sm:inline">Sonraki</span> <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>

            </div>
            {/* Modal'ı ana animasyonlu alanın dışına çıkardık (Sabit hizalama sorunu çözümü) */}
            <UrunModal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditUrun(null); }}
                onSave={handleSave} urun={editUrun} kategoriler={kategoriler} markalar={markalar} />

            <ZXingBarcodeScanner
                isOpen={cameraScannerOpen}
                onClose={() => setCameraScannerOpen(false)}
                onScanSuccess={async (code) => {
                    setSearch(code);
                    setPage(0);
                    try {
                        const res = await getUrunByBarkod(code);
                        toast.success(`Bulundu: ${res.data.isim}`, { icon: '📷' });
                    } catch {
                        toast.success(`Aranıyor: ${code}`, { icon: '📷' });
                    }
                }}
            />
        </>
    );
}