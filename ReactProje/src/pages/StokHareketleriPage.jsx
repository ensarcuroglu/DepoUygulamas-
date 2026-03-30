import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { ArrowDownToLine, ArrowUpFromLine, Barcode, Check, Loader2, Package, Clock, Search, X, TrendingUp, TrendingDown, ArrowLeft, RefreshCw, MapPin, Calendar, Hash, Box, ChevronDown, ChevronUp } from 'lucide-react';
import { getStokHareketleri, stokIslemleriPaletSorgula, stokIslemleriPaletGiris, stokIslemleriPaletCikis } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';


export default function StokHareketleriPage() {
    // ===== STATE =====
    const [step, setStep] = useState(1);
    const [hareketTipi, setHareketTipi] = useState('');

    const [paletNo, setPaletNo] = useState('');
    const [paletBilgi, setPaletBilgi] = useState(null);
    const [cikisMiktar, setCikisMiktar] = useState('');
    const [cikisSiparisNo, setCikisSiparisNo] = useState('');
    const [cikisAciklama, setCikisAciklama] = useState('');
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);
    const [sonIslemler, setSonIslemler] = useState([]);

    const { loading: loadingHistory, run: runHistory } = useAsync(true);
    const { loading: paletSorguLoading, run: runSorgu } = useAsync(false);
    const { loading: submitting, run: runSubmit } = useAsync(false);

    const paletInputRef = useRef(null);

    const [visibleCount, setVisibleCount] = useState(5); // Son işlemler için görünür satır sayısı

    // ===== VERİ YÜKLEME =====
    const fetchSonIslemler = async () => {
        try {
            const hRes = await runHistory(() => getStokHareketleri({ limit: 20 }));
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

        try {
            const res = await runSorgu(() => stokIslemleriPaletSorgula(hedefNo));
            setPaletBilgi(res.data);
            setPaletNo(hedefNo);
            setStep(3);
        } catch (err) {
            toast.error(hataMetni(err, 'Palet bulunamadı'));
        }
    };

    // ===== SUBMIT =====
    const handleSubmit = async () => {
        if (!paletBilgi || !hareketTipi) return;
        try {
            await runSubmit(async () => {
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
            });
            resetForm();
            fetchSonIslemler();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
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

    // ===== STEP INDICATOR =====
    const StepIndicator = () => (
        <div className="flex items-center justify-center gap-2 py-4">
            {[1, 2, 3].map((s) => (
                <div key={s} className="flex items-center gap-2">
                    <div className={`
                        w-10 h-10 rounded-full flex items-center justify-center text-sm font-black transition-all duration-300
                        ${step >= s
                            ? step === s
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/40 scale-110'
                                : 'bg-emerald-500 text-white'
                            : 'bg-slate-200 text-slate-400'
                        }
                    `}>
                        {step > s ? <Check className="w-5 h-5" strokeWidth={3} /> : s}
                    </div>
                    {s < 3 && (
                        <div className={`w-8 sm:w-12 h-1 rounded-full transition-all duration-500 ${step > s ? 'bg-emerald-500' : 'bg-slate-200'}`} />
                    )}
                </div>
            ))}
        </div>
    );

    // ===== STEP HEADER =====
    const StepHeader = ({ onBack, backLabel }) => (
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
                <div className={`
                    w-12 h-12 sm:w-14 sm:h-14 rounded-2xl flex items-center justify-center shadow-md
                    ${hareketTipi === 'giris'
                        ? 'bg-emerald-500 text-white shadow-emerald-500/30'
                        : 'bg-red-500 text-white shadow-red-500/30'
                    }
                `}>
                    {hareketTipi === 'giris'
                        ? <ArrowDownToLine className="w-6 h-6 sm:w-7 sm:h-7" strokeWidth={2.5} />
                        : <ArrowUpFromLine className="w-6 h-6 sm:w-7 sm:h-7" strokeWidth={2.5} />
                    }
                </div>
                <div>
                    <span className={`
                        text-xl sm:text-2xl font-black uppercase tracking-tight
                        ${hareketTipi === 'giris' ? 'text-emerald-700' : 'text-red-700'}
                    `}>
                        {hareketTipi === 'giris' ? 'Giriş' : 'Çıkış'}
                    </span>
                    <p className="text-xs font-semibold text-slate-400 -mt-0.5">
                        {hareketTipi === 'giris' ? 'Palet Kabul İşlemi' : 'Palet Sevk İşlemi'}
                    </p>
                </div>
            </div>
            <button
                onClick={onBack}
                className="flex items-center gap-2 h-12 px-4 sm:px-5 rounded-2xl font-bold text-sm
                    bg-slate-100 text-slate-600 hover:bg-slate-200 active:scale-95 transition-all
                    min-w-[48px] justify-center"
            >
                <ArrowLeft className="w-5 h-5" />
                <span className="hidden sm:inline">{backLabel}</span>
            </button>
        </div>
    );

    // ===== İŞ AKIŞI KONTROLLERİ (WMS KURALLARI) =====
    const isGirisEngelli = hareketTipi === 'giris' && paletBilgi?.giris_yapildi_mi;
    const isCikisEngelli = hareketTipi === 'cikis' && !paletBilgi?.giris_yapildi_mi;
    const isOnayDisabled = submitting || isGirisEngelli || isCikisEngelli;

    return (
        <div className="max-w-2xl mx-auto px-3 sm:px-0 pb-8">

            {/* ==================== */}
            {/* ANA İŞLEM FORMU     */}
            {/* ==================== */}
            <div className="bg-white rounded-3xl border-2 border-slate-200 shadow-xl mb-6 overflow-hidden">

                {/* Step Indicator */}
                <div className="bg-slate-50 border-b border-slate-200">
                    <StepIndicator />
                </div>

                <div className="p-4 sm:p-6">

                    {/* ===== ADIM 1: GİRİŞ / ÇIKIŞ SEÇ ===== */}
                    {step === 1 && (
                        <div className="space-y-5">
                            <p className="text-center text-sm font-black text-slate-400 uppercase tracking-[0.2em]">
                                İşlem Tipini Seçin
                            </p>
                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                {/* GİRİŞ Butonu */}
                                <button
                                    onClick={() => { setHareketTipi('giris'); setStep(2); }}
                                    className="flex flex-col items-center justify-center gap-4 py-10 sm:py-12 rounded-3xl
                                        border-3 border-emerald-300 bg-gradient-to-b from-emerald-50 to-white
                                        hover:border-emerald-500 hover:shadow-lg hover:shadow-emerald-500/20
                                        active:scale-[0.96] transition-all duration-200 group"
                                >
                                    <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-3xl bg-emerald-500
                                        flex items-center justify-center shadow-xl shadow-emerald-500/30
                                        group-hover:shadow-emerald-500/50 group-hover:scale-105 transition-all duration-300">
                                        <ArrowDownToLine className="w-10 h-10 sm:w-12 sm:h-12 text-white" strokeWidth={2.5} />
                                    </div>
                                    <div className="text-center">
                                        <span className="block text-2xl sm:text-3xl font-black text-emerald-800 tracking-tight">
                                            GİRİŞ
                                        </span>
                                        <span className="block text-xs sm:text-sm font-bold text-emerald-600/60 mt-1">
                                            Palet Kabul
                                        </span>
                                    </div>
                                </button>

                                {/* ÇIKIŞ Butonu */}
                                <button
                                    onClick={() => { setHareketTipi('cikis'); setStep(2); }}
                                    className="flex flex-col items-center justify-center gap-4 py-10 sm:py-12 rounded-3xl
                                        border-3 border-red-300 bg-gradient-to-b from-red-50 to-white
                                        hover:border-red-500 hover:shadow-lg hover:shadow-red-500/20
                                        active:scale-[0.96] transition-all duration-200 group"
                                >
                                    <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-3xl bg-red-500
                                        flex items-center justify-center shadow-xl shadow-red-500/30
                                        group-hover:shadow-red-500/50 group-hover:scale-105 transition-all duration-300">
                                        <ArrowUpFromLine className="w-10 h-10 sm:w-12 sm:h-12 text-white" strokeWidth={2.5} />
                                    </div>
                                    <div className="text-center">
                                        <span className="block text-2xl sm:text-3xl font-black text-red-800 tracking-tight">
                                            ÇIKIŞ
                                        </span>
                                        <span className="block text-xs sm:text-sm font-bold text-red-600/60 mt-1">
                                            Palet Sevk
                                        </span>
                                    </div>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ===== ADIM 2: PALET NO GİR / TARA ===== */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <StepHeader onBack={resetForm} backLabel="Geri Dön" />

                            {/* Palet No Girişi */}
                            <div>
                                <label className="text-xs font-black text-slate-500 uppercase tracking-[0.15em] mb-3 block">
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
                                            className="w-full h-16 pl-12 pr-4 text-lg font-bold rounded-2xl
                                                border-2 border-slate-200 bg-slate-50 text-slate-800
                                                placeholder-slate-400
                                                focus:outline-none focus:border-blue-500 focus:bg-white
                                                focus:ring-4 focus:ring-blue-500/10 transition-all"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setCameraScannerOpen(true)}
                                        className="h-16 w-16 flex items-center justify-center rounded-2xl
                                            bg-blue-600 text-white hover:bg-blue-700
                                            active:scale-95 transition-all shadow-lg shadow-blue-600/30
                                            flex-shrink-0"
                                        title="Kamera ile Barkod Oku"
                                    >
                                        <Barcode className="w-7 h-7" />
                                    </button>
                                </div>
                            </div>

                            {/* Sorgula Butonu */}
                            <button
                                onClick={() => handlePaletSorgula()}
                                disabled={!paletNo.trim() || paletSorguLoading}
                                className={`w-full h-16 rounded-2xl text-lg font-black text-white
                                    flex items-center justify-center gap-3 transition-all shadow-lg
                                    ${paletSorguLoading
                                        ? 'bg-blue-400 cursor-wait'
                                        : 'bg-blue-600 hover:bg-blue-700 active:scale-[0.97] shadow-blue-600/30'
                                    }
                                    ${!paletNo.trim() ? 'opacity-40 cursor-not-allowed' : ''}`}
                            >
                                {paletSorguLoading ? (
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                ) : (
                                    <Search className="w-6 h-6" />
                                )}
                                {paletSorguLoading ? 'Sorgulanıyor...' : 'Palet Sorgula'}
                            </button>

                            <div className="flex items-center justify-center gap-2 py-2">
                                <div className="h-px flex-1 bg-slate-200" />
                                <span className="text-xs font-bold text-slate-400 uppercase">veya</span>
                                <div className="h-px flex-1 bg-slate-200" />
                            </div>

                            <p className="text-center text-sm font-semibold text-slate-400">
                                Fiziksel barkod okuyucu ile tarayın
                            </p>
                        </div>
                    )}

                    {/* ===== ADIM 3: BİLGİ ÖNİZLEME + ONAYLA ===== */}
                    {step === 3 && paletBilgi && (
                        <div className="space-y-5">
                            <StepHeader
                                onBack={() => { setPaletBilgi(null); setStep(2); }}
                                backLabel="Paleti Değiştir"
                            />

                            {/* Palet Bilgi Kartı */}
                            <div className="rounded-2xl border-2 border-slate-200 bg-slate-50 overflow-hidden">
                                {/* Kart Header */}
                                <div className="px-4 py-3.5 bg-slate-800 flex items-center gap-3">
                                    <Box className="w-5 h-5 text-slate-300" />
                                    <span className="text-sm font-black text-white tracking-wide">Palet Bilgisi</span>
                                    <span className="ml-auto text-sm font-black text-blue-300 bg-blue-900/40 px-3 py-1 rounded-lg">
                                        {paletBilgi.palet_no}
                                    </span>
                                </div>

                                <div className="p-4 space-y-3">
                                    {/* Ürün */}
                                    <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200">
                                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                                            <Package className="w-5 h-5 text-blue-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ürün</p>
                                            <p className="text-sm font-black text-slate-800 truncate">{paletBilgi.urun_adi}</p>
                                        </div>
                                        {paletBilgi.urun_barkod && (
                                            <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-lg">
                                                {paletBilgi.urun_barkod}
                                            </span>
                                        )}
                                    </div>

                                    {/* Miktar + Lot */}
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="p-3 bg-white rounded-xl border border-slate-200">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Hash className="w-3.5 h-3.5 text-slate-400" />
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Miktar</p>
                                            </div>
                                            <p className="text-lg font-black text-slate-800">{paletBilgi.miktar} <span className="text-xs font-bold text-slate-400">koli</span></p>
                                        </div>
                                        {paletBilgi.lot_no && (
                                            <div className="p-3 bg-white rounded-xl border border-slate-200">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <Hash className="w-3.5 h-3.5 text-slate-400" />
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Lot No</p>
                                                </div>
                                                <p className="text-sm font-black text-slate-800">{paletBilgi.lot_no}</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Raf + Depo */}
                                    <div className="grid grid-cols-2 gap-2">
                                        {paletBilgi.raf_bilgi && (
                                            <div className="p-3 bg-white rounded-xl border border-slate-200">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Raf</p>
                                                </div>
                                                <p className="text-sm font-black text-slate-800">{paletBilgi.raf_bilgi}</p>
                                            </div>
                                        )}
                                        <div className="p-3 bg-white rounded-xl border border-slate-200">
                                            <div className="flex items-center gap-2 mb-1">
                                                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Depo</p>
                                            </div>
                                            <p className="text-sm font-black text-slate-800">{paletBilgi.depo_adi}</p>
                                        </div>
                                    </div>

                                    {/* SKT */}
                                    {paletBilgi.son_kullanma_tarihi && (
                                        <div className="p-3 bg-white rounded-xl border border-slate-200">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Son Kullanma Tarihi</p>
                                            </div>
                                            <p className="text-sm font-black text-slate-800">
                                                {new Date(paletBilgi.son_kullanma_tarihi).toLocaleDateString('tr-TR')}
                                            </p>
                                        </div>
                                    )}

                                    {/* Durum + Kaynak */}
                                    <div className="flex items-center gap-2 pt-2 border-t border-slate-200">
                                        <span className={`text-xs font-black px-3 py-1.5 rounded-lg
                                            ${paletBilgi.durum === 'aktif'
                                                ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                                                : 'bg-slate-200 text-slate-600 border border-slate-300'
                                            }`}>
                                            {paletBilgi.durum === 'aktif' ? 'Aktif' : 'Pasif'}
                                        </span>
                                        <span className="text-xs font-bold text-slate-400">
                                            Kaynak: {paletBilgi.kaynak}
                                        </span>
                                        {paletBilgi.giris_yapildi_mi && (
                                            <span className="text-xs font-black px-3 py-1.5 rounded-lg
                                                bg-amber-100 text-amber-700 border border-amber-200 ml-auto">
                                                Giriş Yapılmış
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Çıkış Ek Alanları */}
                            {hareketTipi === 'cikis' && (
                                <div className="space-y-4">
                                    {/* Miktar */}
                                    <div>
                                        <label className="text-xs font-black text-slate-500 uppercase tracking-[0.15em] mb-3 block">
                                            Miktar <span className="text-slate-300 normal-case tracking-normal">(boş = tam çıkış)</span>
                                        </label>
                                        <div className="flex items-center gap-3">
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(Math.max(1, (Number(cikisMiktar) || 0) - 1)))}
                                                disabled={!cikisMiktar}
                                                className="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl bg-white border-2 border-slate-200
                                                    text-3xl font-light text-slate-600
                                                    hover:bg-slate-50 hover:border-slate-300
                                                    active:bg-slate-100 active:scale-95 transition-all
                                                    flex items-center justify-center shadow-sm select-none flex-shrink-0
                                                    disabled:opacity-30"
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
                                                className="flex-1 w-full min-w-0 h-16 sm:h-18 text-center text-4xl sm:text-5xl
                                                    font-black rounded-2xl border-2 border-slate-200 bg-white text-slate-800
                                                    placeholder-slate-300
                                                    focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10
                                                    transition-all shadow-sm
                                                    [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(Math.min(paletBilgi.miktar, (Number(cikisMiktar) || 0) + 1)))}
                                                className="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl bg-white border-2 border-slate-200
                                                    text-3xl font-light text-slate-600
                                                    hover:bg-slate-50 hover:border-slate-300
                                                    active:bg-slate-100 active:scale-95 transition-all
                                                    flex items-center justify-center shadow-sm select-none flex-shrink-0"
                                            >
                                                +
                                            </button>
                                        </div>

                                        {/* Hızlı Miktar Butonları */}
                                        <div className="flex flex-wrap gap-2 mt-3">
                                            {[5, 10, 50].filter(v => v <= paletBilgi.miktar).map(val => (
                                                <button
                                                    key={val}
                                                    type="button"
                                                    onClick={() => setCikisMiktar(String(Math.min(paletBilgi.miktar, (Number(cikisMiktar) || 0) + val)))}
                                                    className="flex-1 h-12 sm:h-14 rounded-2xl bg-blue-50 text-blue-700
                                                        font-black text-base sm:text-lg border-2 border-blue-200
                                                        hover:bg-blue-100 active:scale-95 transition-all select-none"
                                                >
                                                    +{val}
                                                </button>
                                            ))}
                                            <button
                                                type="button"
                                                onClick={() => setCikisMiktar(String(paletBilgi.miktar))}
                                                className="flex-1 h-12 sm:h-14 rounded-2xl bg-slate-800 text-white
                                                    font-black text-base sm:text-lg border-2 border-slate-700
                                                    hover:bg-slate-900 active:scale-95 transition-all select-none"
                                            >
                                                MAX ({paletBilgi.miktar})
                                            </button>
                                        </div>
                                    </div>

                                    {/* Sipariş No + Açıklama */}
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs font-black text-slate-500 uppercase tracking-[0.15em] mb-2 block">
                                                Sipariş No
                                            </label>
                                            <input
                                                type="text"
                                                value={cikisSiparisNo}
                                                onChange={e => setCikisSiparisNo(e.target.value)}
                                                className="w-full h-14 px-4 text-base font-bold rounded-2xl
                                                    border-2 border-slate-200 bg-slate-50 text-slate-800
                                                    focus:outline-none focus:border-blue-500 focus:bg-white
                                                    focus:ring-4 focus:ring-blue-500/10 transition-all"
                                                placeholder="Örn: ORD-123"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs font-black text-slate-500 uppercase tracking-[0.15em] mb-2 block">
                                                Açıklama <span className="text-slate-300 normal-case tracking-normal">(opsiyonel)</span>
                                            </label>
                                            <input
                                                type="text"
                                                value={cikisAciklama}
                                                onChange={e => setCikisAciklama(e.target.value)}
                                                className="w-full h-14 px-4 text-base font-bold rounded-2xl
                                                    border-2 border-slate-200 bg-slate-50 text-slate-800
                                                    placeholder-slate-400
                                                    focus:outline-none focus:border-blue-500 focus:bg-white
                                                    focus:ring-4 focus:ring-blue-500/10 transition-all"
                                                placeholder="İrsaliye no, alıcı..."
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* ===== WMS İŞ AKIŞI UYARILARI ===== */}
                            {(isGirisEngelli || isCikisEngelli) && (
                                <div className="relative overflow-hidden p-4 sm:p-5 rounded-2xl bg-amber-50 border-2 border-amber-200/60 shadow-sm flex items-start gap-3 sm:gap-4 mb-2">
                                    {/* Dekoratif Arka Plan Parlaması */}
                                    <div className="absolute -right-6 -top-6 w-32 h-32 bg-amber-400/10 rounded-full blur-2xl pointer-events-none" />

                                    {/* İkon Kutusu */}
                                    <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-white shadow-sm border border-amber-100 flex items-center justify-center text-amber-500 relative z-10">
                                        <X className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={3} />
                                    </div>

                                    {/* Metin İçeriği */}
                                    <div className="flex-1 relative z-10 pt-0.5 sm:pt-1">
                                        <div className="flex items-center gap-2 mb-1.5">
                                            <h4 className="text-sm sm:text-base font-black text-amber-900 tracking-tight">
                                                İşlem Kuralı İhlali
                                            </h4>
                                            <span className="hidden sm:flex px-2 py-0.5 rounded-lg bg-amber-200/50 text-[10px] font-black text-amber-800 uppercase tracking-widest">
                                                WMS KONTROL
                                            </span>
                                        </div>
                                        <p className="text-xs sm:text-sm font-semibold text-amber-700/90 leading-relaxed">
                                            {isGirisEngelli ? (
                                                <>
                                                    Bu paletin mal kabulü <strong className="text-amber-950 bg-amber-200/50 px-1.5 py-0.5 rounded-md">zaten yapılmış</strong>. 
                                                    Devam etmek için işlemi <span className="font-black text-amber-900 underline decoration-amber-400/80 underline-offset-4">ÇIKIŞ (Sevk)</span> olarak değiştirmelisiniz.
                                                </>
                                            ) : (
                                                <>
                                                    Bu palet <strong className="text-amber-950 bg-amber-200/50 px-1.5 py-0.5 rounded-md">henüz depoya alınmamış</strong>. 
                                                    Çıkış yapabilmek için önce <span className="font-black text-amber-900 underline decoration-amber-400/80 underline-offset-4">GİRİŞ (Mal Kabul)</span> işlemini tamamlamalısınız.
                                                </>
                                            )}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Aksiyon butonları */}
                            <div className="grid grid-cols-2 gap-3 pt-2">
                                <button
                                    onClick={resetForm}
                                    className="h-16 rounded-2xl border-2 border-slate-300 text-base font-black text-slate-600
                                        hover:bg-slate-50 active:scale-[0.97] transition-all"
                                >
                                    İptal
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={isOnayDisabled}
                                    className={`h-16 rounded-2xl text-lg font-black text-white
                                        active:scale-[0.97] transition-all shadow-xl
                                        flex items-center justify-center gap-3
                                        ${isOnayDisabled 
                                            ? 'bg-slate-300 shadow-none cursor-not-allowed text-slate-500' 
                                            : hareketTipi === 'giris'
                                                ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/30'
                                                : 'bg-red-600 hover:bg-red-700 shadow-red-600/30'
                                        }`}
                                >
                                    {submitting ? (
                                        <Loader2 className="w-6 h-6 animate-spin" />
                                    ) : (
                                        <Check className="w-6 h-6" strokeWidth={3} />
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
                <div className="flex items-center justify-between mb-3 px-1">
                    <div className="flex items-center gap-2.5">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.15em]">Son İşlemler</h3>
                    </div>
                    {/* Toplam işlem sayısını ufak bir badge olarak göstermek modern bir dokunuştur */}
                    {!loadingHistory && sonIslemler.length > 0 && (
                        <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-lg">
                            Son {sonIslemler.length} İşlem
                        </span>
                    )}
                </div>

                {loadingHistory ? (
                    <div className="space-y-2">
                        {[...Array(4)].map((_, i) => (
                            <div key={i} className="h-20 bg-white rounded-2xl border border-slate-100 animate-pulse" />
                        ))}
                    </div>
                ) : sonIslemler.length === 0 ? (
                    <div className="bg-white rounded-2xl border-2 border-dashed border-slate-200 p-10 text-center">
                        <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                        <p className="text-base font-bold text-slate-400">Henüz işlem yok</p>
                    </div>
                ) : (
                    <>
                        <div className="space-y-2">
                            {/* Burada listeyi visibleCount kadar sınırlandırıyoruz */}
                            {sonIslemler.slice(0, visibleCount).map(h => {
                                const isGiris = h.hareket_tipi === 'giris';
                                const tarih = new Date(h.tarih);
                                return (
                                    <div key={h.id} className="flex items-center gap-3 px-4 py-3.5
                                        bg-white rounded-2xl border border-slate-100
                                        hover:border-slate-200 transition-colors shadow-sm">
                                        {/* İkon */}
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0
                                            ${isGiris
                                                ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                                                : 'bg-red-50 text-red-600 border border-red-200'
                                            }`}>
                                            {isGiris
                                                ? <ArrowDownToLine className="w-5 h-5" strokeWidth={2.5} />
                                                : <ArrowUpFromLine className="w-5 h-5" strokeWidth={2.5} />
                                            }
                                        </div>
                                        {/* İçerik */}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-black text-slate-800 truncate">
                                                {h.palet_no ? `Palet: ${h.palet_no}` : `Ürün #${h.urun_id}`}
                                            </p>
                                            <p className="text-xs font-semibold text-slate-400 mt-1">
                                                {tarih.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })} {tarih.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                                                {h.siparis_no ? ` · ${h.siparis_no}` : ''}
                                                {h.aciklama ? ` · ${h.aciklama}` : ''}
                                            </p>
                                        </div>
                                        {/* Miktar */}
                                        <span className={`text-xl font-black tabular-nums flex-shrink-0
                                            ${isGiris ? 'text-emerald-600' : 'text-red-500'}`}>
                                            {isGiris ? '+' : '−'}{h.miktar}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Daha Fazla / Daha Az Göster Butonları - Mobile First Tasarım */}
                        {sonIslemler.length > 3 && (
                            <div className="mt-4 flex justify-center">
                                {visibleCount < sonIslemler.length ? (
                                    <button
                                        type="button"
                                        onClick={() => setVisibleCount(prev => prev + 5)}
                                        className="h-12 w-full sm:w-auto px-6 rounded-2xl flex items-center justify-center gap-2
                                            bg-blue-50 text-blue-600 text-sm font-black border-2 border-blue-100/50
                                            hover:bg-blue-100 hover:border-blue-200 active:scale-95 transition-all"
                                    >
                                        Daha Fazla Göster
                                        <ChevronDown className="w-4 h-4" strokeWidth={3} />
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        onClick={() => setVisibleCount(3)}
                                        className="h-12 w-full sm:w-auto px-6 rounded-2xl flex items-center justify-center gap-2
                                            bg-slate-100 text-slate-600 text-sm font-black border-2 border-slate-200/50
                                            hover:bg-slate-200 active:scale-95 transition-all"
                                    >
                                        Daha Az Göster
                                        <ChevronUp className="w-4 h-4" strokeWidth={3} />
                                    </button>
                                )}
                            </div>
                        )}
                    </>
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
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" />
            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-md border-2 border-slate-200" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between p-5 border-b border-slate-100">
                    <h3 className="text-xl font-black text-slate-900">Hızlı Stok İşlemi</h3>
                    <button onClick={onClose} className="w-10 h-10 rounded-xl hover:bg-slate-100
                        flex items-center justify-center active:scale-95 transition-all">
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>
                <form onSubmit={e => { e.preventDefault(); onSave({ ...form, urun_id: Number(form.urun_id), miktar: Number(form.miktar) }); }} className="p-5 space-y-4">
                    <select
                        className="w-full h-14 px-4 text-base font-bold rounded-2xl border-2 border-slate-200 bg-slate-50"
                        value={form.urun_id}
                        onChange={e => setForm({ ...form, urun_id: e.target.value })}
                        required
                    >
                        <option value="">Ürün seçin...</option>
                        {urunler.map(u => <option key={u.id} value={u.id}>{u.isim} {u.barkod ? `[${u.barkod}]` : ''}</option>)}
                    </select>
                    <div className="grid grid-cols-2 gap-3">
                        {[{ v: 'giris', l: 'Giriş', c: 'emerald' }, { v: 'cikis', l: 'Çıkış', c: 'red' }].map(({ v, l, c }) => (
                            <button key={v} type="button" onClick={() => setForm({ ...form, hareket_tipi: v })}
                                className={`h-14 rounded-2xl border-2 text-base font-black flex items-center justify-center gap-2 transition-all
                                    ${form.hareket_tipi === v
                                        ? `border-${c}-500 bg-${c}-50 text-${c}-700`
                                        : 'border-slate-200 text-slate-500'
                                    }`}>
                                {v === 'giris' ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />} {l}
                            </button>
                        ))}
                    </div>
                    <input type="number" min="1"
                        className="w-full h-14 px-4 text-2xl font-black text-center rounded-2xl border-2 border-slate-200 bg-slate-50"
                        value={form.miktar}
                        onChange={e => setForm({ ...form, miktar: e.target.value })}
                        required
                    />
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <button type="button" onClick={onClose}
                            className="h-14 rounded-2xl border-2 border-slate-200 text-base font-black text-slate-600
                                active:scale-95 transition-all">
                            İptal
                        </button>
                        <button type="submit"
                            className="h-14 rounded-2xl bg-blue-600 text-base font-black text-white
                                active:scale-95 transition-all shadow-lg shadow-blue-600/30">
                            Onayla
                        </button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}