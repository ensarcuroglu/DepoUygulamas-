import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { ArrowDownToLine, ArrowUpFromLine, Barcode, Check, Loader2, Package, Clock, Search, X, TrendingUp, TrendingDown, ArrowLeft, RefreshCw, AlertCircle, MapPin, Calendar, Hash, Box } from 'lucide-react';
import { getStokHareketleri, stokIslemleriPaletSorgula, stokIslemleriPaletGiris, stokIslemleriPaletCikis } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';

export default function StokHareketleriPage() {
    // ===== STATE =====
    const [step, setStep] = useState(1); // 1: Tip seç, 2: Palet No gir, 3: Önizle/Onayla
    const [hareketTipi, setHareketTipi] = useState('');

    // Palet bazlı state
    const [paletNo, setPaletNo] = useState('');
    const [paletBilgi, setPaletBilgi] = useState(null);
    const [paletSorguLoading, setPaletSorguLoading] = useState(false);

    // Çıkış ek alanları
    const [cikisMiktar, setCikisMiktar] = useState('');
    const [cikisSiparisNo, setCikisSiparisNo] = useState('');
    const [cikisAciklama, setCikisAciklama] = useState('');

    const [submitting, setSubmitting] = useState(false);

    // Kamera tarayıcı
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);

    // Son işlemler
    const [sonIslemler, setSonIslemler] = useState([]);
    const { loading: loadingHistory, run } = useAsync(true);

    const paletInputRef = useRef(null);

    // ===== VERİ YÜKLEME =====
    const fetchSonIslemler = async () => {
        try {
            const hRes = await run(() => getStokHareketleri({ limit: 20 }));
            setSonIslemler(hRes.data);
        } catch {
            toast.error('Son işlemler yüklenemedi');
        }
    };

    useEffect(() => { fetchSonIslemler(); }, []);

    // ===== BARKOD TARAMA (Fiziksel okuyucu) =====
    useBarcodeScanner({
        isEnabled: step === 2,
        onScan: (code) => {
            setPaletNo(code);
            handlePaletSorgula(code);
        }
    });

    // ===== PALET SORGULAMA =====
    const handlePaletSorgula = async (no) => {
        const hedefNo = (no || paletNo).trim();
        if (!hedefNo) return;

        setPaletSorguLoading(true);
        try {
            const res = await stokIslemleriPaletSorgula(hedefNo);
            setPaletBilgi(res.data);
            setPaletNo(hedefNo);
            setStep(3);
        } catch (err) {
            toast.error(hataMetni(err, 'Palet bulunamadı'));
        } finally {
            setPaletSorguLoading(false);
        }
    };

    // ===== SUBMIT =====
    const handleSubmit = async () => {
        if (!paletBilgi || !hareketTipi) return;
        setSubmitting(true);
        try {
            if (hareketTipi === 'giris') {
                await stokIslemleriPaletGiris({ palet_no: paletNo });
                toast.success(`Palet ${paletNo} giriş yapıldı`, { duration: 3000 });
            } else {
                await stokIslemleriPaletCikis({
                    palet_no: paletNo,
                    miktar: cikisMiktar ? Number(cikisMiktar) : undefined,
                    siparis_no: cikisSiparisNo || undefined,
                    aciklama: cikisAciklama || undefined,
                });
                const miktarText = cikisMiktar ? `${cikisMiktar} koli` : 'tam';
                toast.success(`Palet ${paletNo} çıkış yapıldı (${miktarText})`, { duration: 3000 });
            }
            resetForm();
            fetchSonIslemler();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        } finally {
            setSubmitting(false);
        }
    };

    const resetForm = () => {
        setStep(1);
        setHareketTipi('');
        setPaletNo('');
        setPaletBilgi(null);
        setCikisMiktar('');
        setCikisSiparisNo('');
        setCikisAciklama('');
    };

    // ===== RENDER =====
    return (
        <div className="max-w-2xl mx-auto px-2 sm:px-0 pb-8">

            {/* ==================== */}
            {/* ANA İŞLEM FORMU     */}
            {/* ==================== */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-lg mb-6 relative">

                {/* Progress Bar */}
                <div className="h-1.5 bg-slate-100 w-full rounded-t-[15px] overflow-hidden">
                    <div
                        className={`h-full transition-all duration-500 ease-out rounded-r-full ${step >= 3 ? 'bg-emerald-500' : 'bg-blue-500'}`}
                        style={{ width: `${(Math.min(step, 3) / 3) * 100}%` }}
                    />
                </div>

                <div className="p-4 sm:p-6">

                    {/* ===== ADIM 1: GİRİŞ / ÇIKIŞ SEÇ ===== */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <p className="text-center text-sm font-bold text-slate-500 uppercase tracking-wider">
                                İşlem Tipini Seçin
                            </p>
                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                <button
                                    onClick={() => { setHareketTipi('giris'); setStep(2); }}
                                    className="flex flex-col items-center justify-center gap-3 py-8 sm:py-10 rounded-2xl border-2 border-emerald-200 bg-emerald-50 hover:bg-emerald-100 hover:border-emerald-400 active:scale-[0.97] transition-all duration-200 group"
                                >
                                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/30 group-hover:shadow-emerald-500/50 transition-shadow">
                                        <ArrowDownToLine className="w-8 h-8 sm:w-10 sm:h-10 text-white" strokeWidth={2.5} />
                                    </div>
                                    <span className="text-lg sm:text-xl font-extrabold text-emerald-800 tracking-tight">
                                        GİRİŞ
                                    </span>
                                    <span className="text-xs font-semibold text-emerald-600/70">
                                        Palet Kabul
                                    </span>
                                </button>

                                <button
                                    onClick={() => { setHareketTipi('cikis'); setStep(2); }}
                                    className="flex flex-col items-center justify-center gap-3 py-8 sm:py-10 rounded-2xl border-2 border-red-200 bg-red-50 hover:bg-red-100 hover:border-red-400 active:scale-[0.97] transition-all duration-200 group"
                                >
                                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-red-500 flex items-center justify-center shadow-lg shadow-red-500/30 group-hover:shadow-red-500/50 transition-shadow">
                                        <ArrowUpFromLine className="w-8 h-8 sm:w-10 sm:h-10 text-white" strokeWidth={2.5} />
                                    </div>
                                    <span className="text-lg sm:text-xl font-extrabold text-red-800 tracking-tight">
                                        ÇIKIŞ
                                    </span>
                                    <span className="text-xs font-semibold text-red-600/70">
                                        Palet Sevk
                                    </span>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ===== ADIM 2: PALET NO GİR / TARA ===== */}
                    {step === 2 && (
                        <div className="space-y-4">
                            {/* Üst bilgi çubuğu */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center ${hareketTipi === 'giris' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
                                        {hareketTipi === 'giris' ? <ArrowDownToLine className="w-5 h-5 sm:w-6 sm:h-6" /> : <ArrowUpFromLine className="w-5 h-5 sm:w-6 sm:h-6" />}
                                    </div>
                                    <span className={`text-base sm:text-lg font-black uppercase tracking-widest ${hareketTipi === 'giris' ? 'text-emerald-700' : 'text-red-700'}`}>
                                        {hareketTipi === 'giris' ? 'Giriş' : 'Çıkış'}
                                    </span>
                                </div>
                                <button
                                    onClick={resetForm}
                                    className="flex items-center gap-2 h-10 px-3 sm:px-4 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm sm:text-base hover:bg-slate-200 active:scale-95 transition-all"
                                >
                                    <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="hidden sm:inline">Geri Dön</span>
                                </button>
                            </div>

                            {/* Palet No Girişi */}
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 block">
                                    Palet Numarası
                                </label>
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                                        <input
                                            ref={paletInputRef}
                                            autoFocus
                                            type="text"
                                            placeholder="Palet no girin veya okutun..."
                                            value={paletNo}
                                            onChange={e => setPaletNo(e.target.value)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') {
                                                    e.preventDefault();
                                                    handlePaletSorgula();
                                                }
                                            }}
                                            className="w-full h-14 pl-12 pr-4 text-base font-semibold rounded-xl border-2 border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setCameraScannerOpen(true)}
                                        className="h-14 w-14 flex items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition-all shadow-md flex-shrink-0"
                                        title="Kamera ile Barkod Oku"
                                    >
                                        <Barcode className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>

                            {/* Sorgula Butonu */}
                            <button
                                onClick={() => handlePaletSorgula()}
                                disabled={!paletNo.trim() || paletSorguLoading}
                                className={`w-full h-14 rounded-xl text-base font-extrabold text-white flex items-center justify-center gap-2 transition-all shadow-lg
                                    ${paletSorguLoading ? 'bg-blue-400 cursor-wait' : 'bg-blue-600 hover:bg-blue-700 active:scale-[0.97] shadow-blue-600/30'}
                                    ${!paletNo.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {paletSorguLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Search className="w-5 h-5" />
                                )}
                                {paletSorguLoading ? 'Sorgulanıyor...' : 'Palet Sorgula'}
                            </button>

                            <p className="text-center text-xs text-slate-400">
                                Fiziksel barkod okuyucu ile de tarama yapabilirsiniz
                            </p>
                        </div>
                    )}

                    {/* ===== ADIM 3: BİLGİ ÖNİZLEME + ONAYLA ===== */}
                    {step === 3 && paletBilgi && (
                        <div className="space-y-5">
                            {/* Üst bilgi çubuğu */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center ${hareketTipi === 'giris' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
                                        {hareketTipi === 'giris' ? <ArrowDownToLine className="w-5 h-5 sm:w-6 sm:h-6" /> : <ArrowUpFromLine className="w-5 h-5 sm:w-6 sm:h-6" />}
                                    </div>
                                    <span className={`text-base sm:text-lg font-black uppercase tracking-widest ${hareketTipi === 'giris' ? 'text-emerald-700' : 'text-red-700'}`}>
                                        {hareketTipi === 'giris' ? 'Giriş' : 'Çıkış'}
                                    </span>
                                </div>
                                <button
                                    onClick={() => { setPaletBilgi(null); setStep(2); }}
                                    className="flex items-center gap-2 h-10 px-3 sm:px-4 rounded-xl bg-orange-50 text-orange-600 font-bold text-sm sm:text-base hover:bg-orange-100 hover:text-orange-700 active:scale-95 transition-all"
                                >
                                    <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="hidden sm:inline">Paleti Değiştir</span>
                                </button>
                            </div>

                            {/* Palet Bilgi Kartı */}
                            <div className="rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
                                <div className="px-4 py-3 bg-slate-100 border-b border-slate-200 flex items-center gap-2">
                                    <Box className="w-5 h-5 text-blue-600" />
                                    <span className="text-sm font-extrabold text-slate-700">Palet Bilgisi</span>
                                    <span className="ml-auto text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                                        {paletBilgi.palet_no}
                                    </span>
                                </div>
                                <div className="p-4 space-y-3">
                                    {/* Ürün */}
                                    <div className="flex items-center gap-3">
                                        <Package className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-medium text-slate-400">Ürün</p>
                                            <p className="text-sm font-bold text-slate-800 truncate">{paletBilgi.urun_adi}</p>
                                        </div>
                                        {paletBilgi.urun_barkod && (
                                            <span className="text-xs font-semibold text-slate-400">{paletBilgi.urun_barkod}</span>
                                        )}
                                    </div>

                                    {/* Miktar + Lot */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="flex items-center gap-2">
                                            <Hash className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                            <div>
                                                <p className="text-xs font-medium text-slate-400">Miktar</p>
                                                <p className="text-sm font-bold text-slate-800">{paletBilgi.miktar} koli</p>
                                            </div>
                                        </div>
                                        {paletBilgi.lot_no && (
                                            <div className="flex items-center gap-2">
                                                <Hash className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                                <div>
                                                    <p className="text-xs font-medium text-slate-400">Lot No</p>
                                                    <p className="text-sm font-bold text-slate-800">{paletBilgi.lot_no}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Raf + Depo */}
                                    <div className="grid grid-cols-2 gap-3">
                                        {paletBilgi.raf_bilgi && (
                                            <div className="flex items-center gap-2">
                                                <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                                <div>
                                                    <p className="text-xs font-medium text-slate-400">Raf</p>
                                                    <p className="text-sm font-bold text-slate-800">{paletBilgi.raf_bilgi}</p>
                                                </div>
                                            </div>
                                        )}
                                        <div className="flex items-center gap-2">
                                            <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                            <div>
                                                <p className="text-xs font-medium text-slate-400">Depo</p>
                                                <p className="text-sm font-bold text-slate-800">{paletBilgi.depo_adi}</p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* SKT */}
                                    {paletBilgi.son_kullanma_tarihi && (
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                            <div>
                                                <p className="text-xs font-medium text-slate-400">Son Kullanma Tarihi</p>
                                                <p className="text-sm font-bold text-slate-800">
                                                    {new Date(paletBilgi.son_kullanma_tarihi).toLocaleDateString('tr-TR')}
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Durum + Kaynak */}
                                    <div className="flex items-center gap-2 pt-1 border-t border-slate-200">
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${paletBilgi.durum === 'aktif' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>
                                            {paletBilgi.durum === 'aktif' ? 'Aktif' : 'Pasif'}
                                        </span>
                                        <span className="text-xs font-semibold text-slate-400">
                                            Kaynak: {paletBilgi.kaynak}
                                        </span>
                                        {paletBilgi.giris_yapildi_mi && (
                                            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 ml-auto">
                                                Giriş Yapılmış
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Çıkış Ek Alanları */}
                            {hareketTipi === 'cikis' && (
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">
                                            Miktar <span className="text-slate-300 normal-case">(boş bırakılırsa tam çıkış)</span>
                                        </label>
                                        <div className="flex items-center gap-2 sm:gap-3">
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(Math.max(1, (Number(cikisMiktar) || 0) - 1)))}
                                                disabled={!cikisMiktar}
                                                className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white border border-slate-200 text-3xl font-light text-slate-600 hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100 active:scale-95 transition-all flex items-center justify-center shadow-sm select-none flex-shrink-0 disabled:opacity-30"
                                            >
                                                −
                                            </button>
                                            <input
                                                type="number"
                                                inputMode="numeric"
                                                min="1"
                                                max={paletBilgi.miktar}
                                                placeholder="Tam"
                                                value={cikisMiktar}
                                                onChange={e => {
                                                    const val = e.target.value;
                                                    if (val === '' || (Number(val) >= 1 && Number(val) <= paletBilgi.miktar)) {
                                                        setCikisMiktar(val);
                                                    }
                                                }}
                                                className="flex-1 w-full min-w-0 h-14 sm:h-16 text-center text-3xl sm:text-4xl font-black rounded-2xl border-2 border-slate-200 bg-white text-slate-800 placeholder-slate-300 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all shadow-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(Math.min(paletBilgi.miktar, (Number(cikisMiktar) || 0) + 1)))}
                                                className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white border border-slate-200 text-3xl font-light text-slate-600 hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100 active:scale-95 transition-all flex items-center justify-center shadow-sm select-none flex-shrink-0"
                                            >
                                                +
                                            </button>
                                        </div>

                                        {/* Hızlı Miktar Butonları */}
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {[5, 10, 50].filter(v => v <= paletBilgi.miktar).map(val => (
                                                <button
                                                    key={val}
                                                    type="button"
                                                    onClick={() => setCikisMiktar(String(Math.min(paletBilgi.miktar, (Number(cikisMiktar) || 0) + val)))}
                                                    className="flex-1 h-10 sm:h-11 rounded-xl bg-blue-50 text-blue-700 font-bold text-sm sm:text-base hover:bg-blue-100 active:scale-95 transition-all select-none"
                                                >
                                                    +{val}
                                                </button>
                                            ))}
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(paletBilgi.miktar))}
                                                className="flex-1 h-10 sm:h-11 rounded-xl bg-slate-800 text-white font-bold text-sm sm:text-base hover:bg-slate-900 active:scale-95 transition-all select-none"
                                            >
                                                MAX ({paletBilgi.miktar})
                                            </button>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">Sipariş No</label>
                                            <input type="text" value={cikisSiparisNo} onChange={e => setCikisSiparisNo(e.target.value)} className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all" placeholder="Örn: ORD-123" />
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">
                                                Açıklama <span className="text-slate-300 normal-case">(isteğe bağlı)</span>
                                            </label>
                                            <input type="text" value={cikisAciklama} onChange={e => setCikisAciklama(e.target.value)} className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all" placeholder="İrsaliye no, alıcı bilgisi..." />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Aksiyon butonları */}
                            <div className="grid grid-cols-2 gap-3 pt-2">
                                <button
                                    onClick={resetForm}
                                    className="h-14 rounded-xl border-2 border-slate-200 text-sm font-bold text-slate-600 hover:bg-slate-50 active:scale-[0.97] transition-all"
                                >
                                    İptal
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                    className={`h-14 rounded-xl text-base font-extrabold text-white active:scale-[0.97] transition-all shadow-lg flex items-center justify-center gap-2
                                        ${hareketTipi === 'giris'
                                            ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/30'
                                            : 'bg-red-600 hover:bg-red-700 shadow-red-600/30'}
                                        ${submitting ? 'opacity-70 cursor-wait' : ''}`}
                                >
                                    {submitting ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <Check className="w-5 h-5" strokeWidth={3} />
                                    )}
                                    {submitting ? 'Kaydediliyor...' : 'Onayla'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* ==================== */}
            {/* SON İŞLEMLER LİSTESİ */}
            {/* ==================== */}
            <div>
                <div className="flex items-center gap-2 mb-3 px-1">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Son İşlemler</h3>
                </div>

                {loadingHistory ? (
                    <div className="space-y-3">
                        {[...Array(4)].map((_, i) => (
                            <div key={i} className="h-16 bg-white rounded-xl border border-slate-100 animate-pulse" />
                        ))}
                    </div>
                ) : sonIslemler.length === 0 ? (
                    <div className="bg-white rounded-xl border border-slate-100 p-8 text-center">
                        <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-sm font-bold text-slate-500">Henüz işlem yok</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {sonIslemler.map(h => {
                            const isGiris = h.hareket_tipi === 'giris';
                            const tarih = new Date(h.tarih);
                            return (
                                <div key={h.id} className="flex items-center gap-3 px-4 py-3 bg-white rounded-xl border border-slate-100 hover:border-slate-200 transition-colors">
                                    {/* İkon */}
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${isGiris ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                                        {isGiris
                                            ? <ArrowDownToLine className="w-5 h-5" />
                                            : <ArrowUpFromLine className="w-5 h-5" />
                                        }
                                    </div>
                                    {/* İçerik */}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-bold text-slate-800 truncate">
                                            {h.palet_no ? `Palet: ${h.palet_no}` : `Ürün #${h.urun_id}`}
                                        </p>
                                        <p className="text-xs font-medium text-slate-400 mt-0.5">
                                            {tarih.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })} {tarih.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                                            {h.siparis_no ? ` • Sipariş: ${h.siparis_no}` : ''}
                                            {h.aciklama ? ` • ${h.aciklama}` : ''}
                                        </p>
                                    </div>
                                    {/* Miktar */}
                                    <span className={`text-lg font-extrabold tabular-nums flex-shrink-0 ${isGiris ? 'text-emerald-600' : 'text-red-500'}`}>
                                        {isGiris ? '+' : '−'}{h.miktar}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Kamera Tarama Modalı */}
            <ZXingBarcodeScanner
                isOpen={cameraScannerOpen}
                onClose={() => setCameraScannerOpen(false)}
                onScanSuccess={(code) => {
                    setCameraScannerOpen(false);
                    setPaletNo(code);
                    handlePaletSorgula(code);
                }}
            />
        </div>
    );
}

// HareketModal — Header'dan çağrılan hızlı işlem modalı (geriye dönük uyum)

export function HareketModal({ isOpen, onClose, onSave, urunler }) {
    const [form, setForm] = useState({ urun_id: '', hareket_tipi: 'giris', miktar: 1, aciklama: '' });

    useEffect(() => {
        if (isOpen) setForm({ urun_id: '', hareket_tipi: 'giris', miktar: 1, aciklama: '' });
    }, [isOpen]);

    if (!isOpen) return null;

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" />
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between p-5 border-b border-slate-100">
                    <h3 className="text-lg font-extrabold text-slate-900">Hızlı Stok İşlemi</h3>
                    <button onClick={onClose} className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center">
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>
                <form onSubmit={e => { e.preventDefault(); onSave({ ...form, urun_id: Number(form.urun_id), miktar: Number(form.miktar) }); }} className="p-5 space-y-4">
                    <select className="w-full h-12 px-4 text-sm font-semibold rounded-xl border border-slate-200 bg-slate-50" value={form.urun_id} onChange={e => setForm({ ...form, urun_id: e.target.value })} required>
                        <option value="">Ürün seçin...</option>
                        {urunler.map(u => <option key={u.id} value={u.id}>{u.isim} {u.barkod ? `[${u.barkod}]` : ''}</option>)}
                    </select>
                    <div className="grid grid-cols-2 gap-3">
                        {[{ v: 'giris', l: 'Giriş', c: 'emerald' }, { v: 'cikis', l: 'Çıkış', c: 'red' }].map(({ v, l, c }) => (
                            <button key={v} type="button" onClick={() => setForm({ ...form, hareket_tipi: v })}
                                className={`h-12 rounded-xl border-2 text-sm font-bold flex items-center justify-center gap-2 transition-all
                                    ${form.hareket_tipi === v ? `border-${c}-500 bg-${c}-50 text-${c}-700` : 'border-slate-200 text-slate-500'}`}>
                                {v === 'giris' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />} {l}
                            </button>
                        ))}
                    </div>
                    <input type="number" min="1" className="w-full h-12 px-4 text-lg font-bold text-center rounded-xl border border-slate-200 bg-slate-50" value={form.miktar} onChange={e => setForm({ ...form, miktar: e.target.value })} required />
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <button type="button" onClick={onClose} className="h-12 rounded-xl border border-slate-200 text-sm font-bold text-slate-600">İptal</button>
                        <button type="submit" className="h-12 rounded-xl bg-blue-600 text-sm font-bold text-white">Onayla</button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}
