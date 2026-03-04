import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeftRight, TrendingUp, TrendingDown, Plus, X, Filter, Activity, Download, FileSpreadsheet, FileText } from 'lucide-react';
import { getStokHareketleri, createStokHareketi, getUrunler, getUrunByBarkod } from '../services/api';
import toast from 'react-hot-toast';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';
import { Barcode } from 'lucide-react';
import { exportToExcel, exportToPDF } from '../utils/exportUtils';

export function HareketModal({ isOpen, onClose, onSave, urunler }) {
    const [form, setForm] = useState({ urun_id: '', hareket_tipi: 'giris', miktar: 1, aciklama: '' });
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);

    useEffect(() => {
        if (isOpen) setForm({ urun_id: '', hareket_tipi: 'giris', miktar: 1, aciklama: '' });
    }, [isOpen]);

    // Klavye dinleyici Hook (Modal açıkken fiziksel okuyucu ile okutulursa)
    useBarcodeScanner({
        isEnabled: isOpen, // Sadece modal açıkken aktif
        onScan: async (scannedCode) => {
            try {
                const res = await getUrunByBarkod(scannedCode);
                setForm(prev => ({ ...prev, urun_id: res.data.id }));
                toast.success(`${res.data.isim} seçildi`, { icon: '📦' });
            } catch {
                toast.error(`Kayıtlı ürün bulunamadı: ${scannedCode}`);
            }
        }
    });

    if (!isOpen) return null;

    const inputClass = `w-full h-11 px-4 text-[14px] font-medium rounded-xl border border-slate-200 bg-slate-50/50
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10
    focus:border-blue-500 focus:bg-white transition-all duration-300 ease-out shadow-inner`;

    const labelClass = "text-[12px] font-bold text-slate-700 mb-2 block tracking-wide uppercase";

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-md transition-opacity" />
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-fade-in ring-1 ring-slate-900/10" onClick={e => e.stopPropagation()}>

                <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-100 border border-blue-200 flex items-center justify-center">
                            <Activity className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="text-[18px] font-extrabold text-slate-900 leading-tight">Terminal İşlemi</h3>
                            <p className="text-[12px] font-medium text-slate-500 mt-0.5">Stok giriş/çıkış beyanı giriniz</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 hover:text-slate-800 flex items-center justify-center transition-all">
                        <X className="w-5 h-5 text-slate-500" />
                    </button>
                </div>

                <form onSubmit={e => { e.preventDefault(); onSave({ ...form, urun_id: Number(form.urun_id), miktar: Number(form.miktar) }); }}
                    className="p-6 space-y-6">

                    <div>
                        <label className={labelClass}>İşlem Yapılacak Ürün *</label>
                        <div className="flex gap-2 relative">
                            <div className="relative flex-1">
                                <select className={`${inputClass} appearance-none pr-10`} value={form.urun_id} onChange={e => setForm({ ...form, urun_id: e.target.value })} required>
                                    <option value="">Depo listesinden ürün seçin...</option>
                                    {urunler.map(u => <option key={u.id} value={u.id}>
                                        {u.isim} {u.barkod ? `[${u.barkod}]` : ''} — Mevcut: {u.stok_miktari} {u.birim}
                                    </option>)}
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setCameraScannerOpen(true)}
                                className="h-11 w-11 flex items-center justify-center rounded-xl bg-slate-100 border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all flex-shrink-0"
                                title="Kamera ile Barkod Oku"
                            >
                                <Barcode className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className={labelClass}>Hareket Tipi (Yön) *</label>
                        <div className="grid grid-cols-2 gap-4">
                            {[{ val: 'giris', label: 'Tedarik / Giriş', icon: TrendingUp, color: 'emerald' },
                            { val: 'cikis', label: 'Sevk / Çıkış', icon: TrendingDown, color: 'red' }].map(({ val, label, icon: Icon, color }) => (
                                <button key={val} type="button" onClick={() => setForm({ ...form, hareket_tipi: val })}
                                    className={`h-12 rounded-xl border-2 text-[14px] font-bold flex items-center justify-center gap-2.5
                    transition-all duration-300 shadow-sm
                    ${form.hareket_tipi === val
                                            ? `border-${color}-500 bg-${color}-50 text-${color}-700 shadow-[0_4px_12px_0_rgba(0,0,0,0.05)]`
                                            : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50 text-slate-600'}`}>
                                    <Icon className={`w-5 h-5 ${form.hareket_tipi === val ? '' : 'opacity-70'}`} /> {label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className={labelClass}>Beyan Edilen Miktar *</label>
                        <input type="number" min="1" className={inputClass} value={form.miktar}
                            onChange={e => setForm({ ...form, miktar: e.target.value })} required />
                    </div>

                    <div>
                        <label className={labelClass}>İşlem Referans Notu (Opsiyonel)</label>
                        <textarea className={`${inputClass} h-24 resize-none py-3`} value={form.aciklama}
                            onChange={e => setForm({ ...form, aciklama: e.target.value })} placeholder="İrsaliye no, alıcı/teslim eden bilgisi vs." />
                    </div>

                    <div className="flex gap-3 pt-4 border-t border-slate-100">
                        <button type="button" onClick={onClose}
                            className="flex-1 h-11 rounded-xl border border-slate-200 text-[14px] font-bold text-slate-600 hover:bg-slate-50 transition-colors">
                            İptal
                        </button>
                        <button type="submit"
                            className="flex-1 h-11 rounded-xl bg-blue-600 text-[14px] font-bold text-white hover:bg-blue-700 transition-all shadow-[0_4px_14px_0_rgba(37,99,235,0.39)] hover:-translate-y-0.5">
                            İşlemi Tamamla
                        </button>
                    </div>
                </form>
            </div>

            {/* Kamera Tarama Modalı (HareketModal'ın üstünde z-index ile açılacak) */}
            <ZXingBarcodeScanner
                isOpen={cameraScannerOpen}
                onClose={() => setCameraScannerOpen(false)}
                onScanSuccess={async (code) => {
                    try {
                        const res = await getUrunByBarkod(code);
                        setForm(prev => ({ ...prev, urun_id: res.data.id }));
                        toast.success(`${res.data.isim} eklendi`, { icon: '📷' });
                    } catch {
                        toast.error(`Kayıtlı ürün bulunamadı: ${code}`);
                    }
                }}
            />
        </div>,
        document.body
    );
}

export default function StokHareketleriPage() {
    const [hareketler, setHareketler] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [filterTip, setFilterTip] = useState('');
    const [exportMenuOpen, setExportMenuOpen] = useState(false);

    const fetchData = () => {
        setLoading(true);
        Promise.all([getStokHareketleri({ limit: 100 }), getUrunler({ limit: 200 })])
            .then(([hRes, uRes]) => {
                setHareketler(hRes.data);
                setUrunler(uRes.data);
            })
            .catch(() => toast.error('Kayıtlı loglara ulaşılamadı. Sunucu bağlantısı kopuk olabilir.'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async (data) => {
        try {
            await createStokHareketi(data);
            toast.success(data.hareket_tipi === 'giris'
                ? `Başarılı: Tedarik işlemi (+${data.miktar}) onandı.`
                : `Başarılı: Sevkiyat işlemi (-${data.miktar}) onandı.`);
            setModalOpen(false);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Hata: Stok yetersiz veya veri uyumsuz.');
        }
    };

    const filteredHareketler = filterTip
        ? hareketler.filter(h => h.hareket_tipi === filterTip)
        : hareketler;

    // Excel ve PDF'e dönüştürülecek verinin (Filtrelenmiş Veriler Üzerinden) Formatlanması
    const getFormattedExportData = () => {
        return filteredHareketler.map(h => {
            const urun = urunler.find(u => u.id === h.urun_id);
            const isGiris = h.hareket_tipi === 'giris';
            const tarihObj = new Date(h.tarih);
            return {
                'Kayıt ID': h.id,
                'İşlem Tipi': isGiris ? 'TEDARİK / GİRİŞ' : 'SEVKİYAT / ÇIKIŞ',
                'Ürün Tanımı': urun ? urun.isim : 'Bilinmeyen Ürün',
                'Barkod': urun ? (urun.barkod || '-') : '-',
                'Miktar': `${isGiris ? '+' : '-'}${h.miktar} Birim`,
                'Referans/Açıklama': h.aciklama || 'Belirtilmedi',
                'Tarih': tarihObj.toLocaleDateString('tr-TR'),
                'Saat': tarihObj.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
            };
        });
    };

    const handleExportExcel = () => {
        setExportMenuOpen(false);
        const data = getFormattedExportData();
        exportToExcel(data, `Stok_Hareket_Raporu`);
    };

    const handleExportPDF = () => {
        setExportMenuOpen(false);
        const data = getFormattedExportData();
        const columns = ['Kayıt ID', 'İşlem Tipi', 'Ürün Tanımı', 'Barkod', 'Miktar', 'Referans', 'Tarih', 'Saat'];
        exportToPDF(data, columns, `Stok_Hareket_Raporu`, 'Terminal Stok Hareketleri (Giriş & Çıkış)');
    };

    return (
        <div className="space-y-6 max-w-[1400px]">

            {/* Top Controls Container */}
            <div className="flex flex-col sm:flex-row items-end sm:items-center justify-between gap-4">

                <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 bg-white px-4 sm:px-5 py-3 sm:py-2.5 rounded-xl border border-slate-200/80 shadow-sm w-full sm:w-auto">
                    <div className="flex items-center gap-3 sm:gap-4 w-full sm:w-auto">
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-indigo-50 flex items-center justify-center border border-indigo-100 flex-shrink-0">
                            <ArrowLeftRight className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600" />
                        </div>
                        <div>
                            <h2 className="text-[14px] sm:text-[15px] font-bold text-slate-800 leading-none mb-1">Log Kayıtları</h2>
                            <p className="text-[11px] sm:text-[12px] font-medium text-slate-500 leading-none">Toplam {filteredHareketler.length} hareket listeleniyor</p>
                        </div>
                    </div>
                    <div className="w-full sm:w-px h-px sm:h-8 bg-slate-200 sm:ml-4"></div>

                    <div className="relative w-full sm:flex-1">
                        <select value={filterTip} onChange={e => setFilterTip(e.target.value)}
                            className="h-10 pl-4 pr-10 text-[13px] font-bold rounded-lg border border-slate-200 bg-slate-50 text-slate-700
                focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 appearance-none cursor-pointer w-full min-w-[140px]">
                            <option value="">Tümü Filtresi</option>
                            <option value="giris">Sadece Girişler</option>
                            <option value="cikis">Sadece Çıkışlar</option>
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                            <Filter className="w-3.5 h-3.5" />
                        </div>
                    </div>
                </div>

                {/* Sağ Taraf - Aksiyon Butonları */}
                <div className="flex items-center gap-3 w-full sm:w-auto mt-4 sm:mt-0">
                    {/* Export Modülü */}
                    <div className="relative">
                        <button
                            onClick={() => setExportMenuOpen(!exportMenuOpen)}
                            className="h-11 px-4 sm:px-5 bg-white border border-slate-200 text-slate-700 text-[14px] font-bold rounded-xl flex items-center justify-center gap-2 transition-all hover:bg-slate-50 hover:border-slate-300 shadow-sm active:scale-95"
                        >
                            <Download className="w-4.5 h-4.5 text-slate-500" />
                            <span className="hidden sm:block">Dışa Aktar</span>
                        </button>

                        {exportMenuOpen && (
                            <div className="absolute left-0 sm:right-0 sm:left-auto top-[calc(100%+8px)] w-[200px] bg-white rounded-2xl border border-slate-200 shadow-xl py-2 z-[60] animate-[fadeIn_0.15s_ease-out]">
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

                    <button onClick={() => setModalOpen(true)}
                        className="h-11 px-5 sm:px-6 bg-blue-600 text-white text-[14px] font-bold rounded-xl whitespace-nowrap
                        hover:bg-blue-700 transition-all shadow-[0_4px_14px_0_rgba(37,99,235,0.39)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.23)] hover:-translate-y-0.5
                        flex items-center justify-center gap-2 flex-1 sm:flex-none">
                        <Plus className="w-5 h-5 stroke-[2.5px]" /> <span className="hidden sm:inline">Yeni Terminal Fişi</span><span className="sm:hidden">Yeni Fiş</span>
                    </button>
                </div>
            </div>

            {/* Main Table Layout */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] overflow-hidden">
                <div className="overflow-x-auto min-h-[300px] sm:min-h-[400px]">
                    <table className="w-full text-left min-w-0">
                        <thead>
                            <tr className="bg-slate-50/80 border-b border-slate-200/80">
                                <th className="px-4 sm:px-6 py-3 sm:py-4 text-[11px] sm:text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">Özellik</th>
                                <th className="px-4 sm:px-6 py-3 sm:py-4 text-[11px] sm:text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">İşlem Kalemi</th>
                                <th className="px-4 sm:px-6 py-3 sm:py-4 text-[11px] sm:text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap">Miktar</th>
                                <th className="px-4 sm:px-6 py-3 sm:py-4 text-[11px] sm:text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden md:table-cell">Referans</th>
                                <th className="px-4 sm:px-6 py-3 sm:py-4 text-[11px] sm:text-[12px] font-extrabold text-slate-500 uppercase tracking-widest whitespace-nowrap hidden sm:table-cell">Zaman</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                [...Array(10)].map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td className="px-4 sm:px-6 py-4"><div className="h-4 bg-slate-200 rounded-md w-20" /></td>
                                        <td className="px-4 sm:px-6 py-4"><div className="h-4 bg-slate-200 rounded-md w-24" /></td>
                                        <td className="px-4 sm:px-6 py-4"><div className="h-4 bg-slate-200 rounded-md w-12" /></td>
                                        <td className="px-4 sm:px-6 py-4 hidden md:table-cell"><div className="h-4 bg-slate-200 rounded-md w-28" /></td>
                                        <td className="px-4 sm:px-6 py-4 hidden sm:table-cell"><div className="h-4 bg-slate-200 rounded-md w-20" /></td>
                                    </tr>
                                ))
                            ) : filteredHareketler.length === 0 ? (
                                <tr>
                                    <td colSpan={5}>
                                        <div className="flex flex-col items-center justify-center py-24 text-center">
                                            <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center mb-4 border border-slate-100 shadow-inner">
                                                <Activity className="w-10 h-10 text-slate-300" />
                                            </div>
                                            <h3 className="text-[16px] font-bold text-slate-800 mb-1">Hiçbir log kaydı yok</h3>
                                            <p className="text-[13px] text-slate-500 font-medium max-w-sm">
                                                Sistemde henüz bir stok giriş çıkışı olmamış veya filtreye uygun bir kayıt bulunmuyor.
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredHareketler.map((h, i) => {
                                    const isGiris = h.hareket_tipi === 'giris';
                                    const urun = urunler.find(u => u.id === h.urun_id);
                                    return (
                                        <tr key={h.id}
                                            className="hover:bg-blue-50/30 transition-colors animate-fade-in group">
                                            <td className="px-4 sm:px-6 py-3 sm:py-4">
                                                <div className={`inline-flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg border text-[10px] sm:text-[12px] font-extrabold shadow-sm
                          ${isGiris
                                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 shadow-emerald-500/10'
                                                        : 'bg-red-50 text-red-700 border-red-200 shadow-red-500/10'}`}>
                                                    {isGiris ? <TrendingUp className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> : <TrendingDown className="w-3.5 h-3.5 sm:w-4 sm:h-4" />}
                                                    <span className="hidden sm:inline">{isGiris ? 'TEDARİK GİRİŞ' : 'SEVKİYAT ÇIKIŞ'}</span>
                                                    <span className="sm:hidden">{isGiris ? 'GİRİŞ' : 'ÇIKIŞ'}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 sm:px-6 py-3 sm:py-4">
                                                <p className="text-[13px] sm:text-[14px] font-bold text-slate-800 truncate max-w-[120px] sm:max-w-none">{urun?.isim || `Silinmiş Ürün (#${h.urun_id})`}</p>
                                                <p className="text-[10px] sm:text-[11px] font-medium text-slate-400 mt-0.5 hidden sm:block">Sistem UUID: {h.id}</p>
                                            </td>
                                            <td className="px-4 sm:px-6 py-3 sm:py-4">
                                                <span className={`text-[15px] sm:text-[18px] font-extrabold tracking-tight ${isGiris ? 'text-emerald-600' : 'text-red-500'}`}>
                                                    {isGiris ? '+' : '-'}{h.miktar} <span className="text-[10px] sm:text-[12px] font-bold opacity-60">BR.</span>
                                                </span>
                                            </td>
                                            <td className="px-4 sm:px-6 py-3 sm:py-4 hidden md:table-cell">
                                                <p className="text-[13px] font-medium text-slate-600 line-clamp-2 max-w-[300px]" title={h.aciklama}>
                                                    {h.aciklama || '—'}
                                                </p>
                                            </td>
                                            <td className="px-4 sm:px-6 py-3 sm:py-4 hidden sm:table-cell">
                                                <div className="flex flex-col">
                                                    <span className="text-[12px] sm:text-[13px] font-bold text-slate-700">
                                                        {new Date(h.tarih).toLocaleDateString('tr-TR', { day: '2-digit', month: 'long', year: 'numeric' })}
                                                    </span>
                                                    <span className="text-[10px] sm:text-[11px] font-bold text-slate-400">
                                                        SAAT: {new Date(h.tarih).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <HareketModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSave} urunler={urunler} />
        </div>
    );
}
