import { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    ArrowDownToLine, ArrowUpFromLine, Barcode, Check, Loader2, Package, Clock,
    Search, X, TrendingUp, TrendingDown, ArrowLeft, MapPin, Calendar, Hash, Box,
    ChevronDown, ChevronUp, Trash2, Scissors, AlertTriangle, Layers,
} from 'lucide-react';
import {
    getStokHareketleri, stokIslemleriPaletSorgula,
    stokIslemleriTopluGiris, stokIslemleriTopluCikis,
} from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';

const MAKS_PALET = 50;

export default function StokHareketleriPage() {
    // ===== STATE =====
    const [step, setStep] = useState(1);
    const [hareketTipi, setHareketTipi] = useState('');

    // Toplu tarama listesi: [{palet_no, bilgi, durum:'yukleniyor'|'gecerli'|'hata', hataMesaji?}]
    const [taramaListesi, setTaramaListesi] = useState([]);
    const [paletNo, setPaletNo] = useState('');
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);

    // Çıkış: per-palet miktar düzenleme
    const [parcalaModu, setParcalaModu] = useState(null); // palet_no veya null
    const [parcalaMiktar, setParcalaMiktar] = useState('');

    // Çıkış: ortak alanlar
    const [cikisSiparisNo, setCikisSiparisNo] = useState('');
    const [cikisAciklama, setCikisAciklama] = useState('');

    // Son işlemler
    const [sonIslemler, setSonIslemler] = useState([]);
    const [visibleCount, setVisibleCount] = useState(5);

    const { loading: loadingHistory, run: runHistory } = useAsync(true);
    const { loading: submitting, run: runSubmit } = useAsync(false);

    const paletInputRef = useRef(null);

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
            handlePaletEkle(code);
        }
    });

    // ===== PALET EKLEME (tarama listesine) =====
    const handlePaletEkle = useCallback(async (no) => {
        const hedefNo = (no || paletNo).trim();
        if (!hedefNo) return;

        // Duplicate kontrolü
        if (taramaListesi.some(t => t.palet_no === hedefNo)) {
            toast.error(`${hedefNo} zaten listede`);
            return;
        }

        // Limit kontrolü
        if (taramaListesi.length >= MAKS_PALET) {
            toast.error(`Tek seferde en fazla ${MAKS_PALET} palet eklenebilir`);
            return;
        }

        // Listeye yükleniyor durumunda ekle
        const yeniKalem = { palet_no: hedefNo, bilgi: null, durum: 'yukleniyor', hataMesaji: null, miktar: null };
        setTaramaListesi(prev => [...prev, yeniKalem]);
        setPaletNo('');
        paletInputRef.current?.focus();

        // Arka planda sorgula
        try {
            const res = await stokIslemleriPaletSorgula(hedefNo);
            const bilgi = res.data;

            // Pre-validation
            let hata = null;
            if (hareketTipi === 'giris' && bilgi.giris_yapildi_mi) {
                hata = 'Bu palet zaten sisteme kaydedilmiş';
            } else if (hareketTipi === 'cikis' && !bilgi.giris_yapildi_mi) {
                hata = 'Henüz depoya alınmamış — önce giriş yapılmalı';
            } else if (hareketTipi === 'cikis' && bilgi.durum !== 'aktif') {
                hata = 'Bu palette stok bulunmuyor';
            }

            setTaramaListesi(prev => prev.map(t =>
                t.palet_no === hedefNo
                    ? { ...t, bilgi, durum: hata ? 'hata' : 'gecerli', hataMesaji: hata }
                    : t
            ));
        } catch (err) {
            setTaramaListesi(prev => prev.map(t =>
                t.palet_no === hedefNo
                    ? { ...t, durum: 'hata', hataMesaji: hataMetni(err, 'Palet bulunamadı') }
                    : t
            ));
        }
    }, [paletNo, taramaListesi, hareketTipi]);

    // ===== PALET SİLME =====
    const handlePaletSil = (paletNoSil) => {
        setTaramaListesi(prev => prev.filter(t => t.palet_no !== paletNoSil));
        if (parcalaModu === paletNoSil) setParcalaModu(null);
    };

    // ===== PARÇALA (kısmi miktar) =====
    const handleParcalaOnayla = (paletNoHedef) => {
        const miktar = Number(parcalaMiktar);
        const kalem = taramaListesi.find(t => t.palet_no === paletNoHedef);
        if (!miktar || miktar <= 0 || (kalem?.bilgi && miktar > kalem.bilgi.miktar)) {
            toast.error('Geçersiz miktar');
            return;
        }
        setTaramaListesi(prev => prev.map(t =>
            t.palet_no === paletNoHedef ? { ...t, miktar } : t
        ));
        setParcalaModu(null);
        setParcalaMiktar('');
    };

    // ===== SUBMIT (TOPLU) =====
    const gecerliPaletler = taramaListesi.filter(t => t.durum === 'gecerli');
    const hataliPaletler = taramaListesi.filter(t => t.durum === 'hata');
    const yukleniyor = taramaListesi.some(t => t.durum === 'yukleniyor');

    const handleSubmit = async () => {
        if (gecerliPaletler.length === 0 || yukleniyor) return;

        try {
            const basarili = await runSubmit(async () => {
                if (hareketTipi === 'giris') {
                    const res = await stokIslemleriTopluGiris({
                        palet_no_listesi: gecerliPaletler.map(t => t.palet_no),
                    });
                    const sonuc = res.data;
                    if (sonuc.basarisiz > 0) {
                        // Pre-validation hatası döndü — listeyi güncelle
                        setTaramaListesi(prev => prev.map(t => {
                            const s = sonuc.sonuclar.find(r => r.palet_no === t.palet_no);
                            if (s && !s.basarili) {
                                return { ...t, durum: 'hata', hataMesaji: s.hata_mesaji };
                            }
                            return t;
                        }));
                        toast.error(`${sonuc.basarisiz} palet hatalı — düzeltip tekrar deneyin`);
                        return false;
                    }
                    toast.success(`${sonuc.basarili} palet giriş yapıldı`, { duration: 4000 });
                    return true;
                } else {
                    const res = await stokIslemleriTopluCikis({
                        kalemler: gecerliPaletler.map(t => ({
                            palet_no: t.palet_no,
                            miktar: t.miktar || undefined,
                        })),
                        siparis_no: cikisSiparisNo || undefined,
                        aciklama: cikisAciklama || undefined,
                    });
                    const sonuc = res.data;
                    if (sonuc.basarisiz > 0) {
                        setTaramaListesi(prev => prev.map(t => {
                            const s = sonuc.sonuclar.find(r => r.palet_no === t.palet_no);
                            if (s && !s.basarili) {
                                return { ...t, durum: 'hata', hataMesaji: s.hata_mesaji };
                            }
                            return t;
                        }));
                        toast.error(`${sonuc.basarisiz} palet hatalı — düzeltip tekrar deneyin`);
                        return false;
                    }
                    toast.success(`${sonuc.basarili} palet çıkış yapıldı`, { duration: 4000 });
                    return true;
                }
                return false;
            });

            if (!basarili) return;

            resetForm();
            fetchSonIslemler();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        }
    };

    const resetForm = () => {
        setStep(1);
        setHareketTipi('');
        setTaramaListesi([]);
        setPaletNo('');
        setParcalaModu(null);
        setParcalaMiktar('');
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
                        {hareketTipi === 'giris' ? 'Toplu Giriş' : 'Toplu Çıkış'}
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

    // ===== PALET BİLGİ KARTI (kompakt — liste içinde) =====
    const PaletKarti = ({ kalem }) => {
        const { palet_no, bilgi, durum, hataMesaji, miktar: ozelMiktar } = kalem;
        const isHata = durum === 'hata';
        const isYukleniyor = durum === 'yukleniyor';
        const isParcalaAcik = parcalaModu === palet_no;

        return (
            <div className={`rounded-2xl border-2 overflow-hidden transition-all ${
                isHata ? 'border-red-200 bg-red-50/50' :
                isYukleniyor ? 'border-slate-200 bg-slate-50 animate-pulse' :
                'border-slate-200 bg-white'
            }`}>
                {/* Üst satır */}
                <div className="flex items-center gap-3 px-4 py-3">
                    {/* Durum ikonu */}
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        isHata ? 'bg-red-100 text-red-500' :
                        isYukleniyor ? 'bg-slate-200 text-slate-400' :
                        'bg-emerald-100 text-emerald-600'
                    }`}>
                        {isYukleniyor ? <Loader2 className="w-5 h-5 animate-spin" /> :
                         isHata ? <AlertTriangle className="w-5 h-5" /> :
                         <Check className="w-5 h-5" strokeWidth={3} />}
                    </div>

                    {/* Palet bilgi */}
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-black text-slate-800 truncate">{palet_no}</p>
                        {isHata && <p className="text-xs font-semibold text-red-500 truncate">{hataMesaji}</p>}
                        {bilgi && !isHata && (
                            <p className="text-xs font-semibold text-slate-400 truncate">
                                {bilgi.urun_adi} · {ozelMiktar || bilgi.miktar} koli
                                {ozelMiktar && ozelMiktar !== bilgi.miktar && (
                                    <span className="text-amber-600 font-black"> (kısmi)</span>
                                )}
                            </p>
                        )}
                    </div>

                    {/* Aksiyonlar */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                        {/* Parçala butonu — sadece çıkışta, geçerli paletlerde */}
                        {hareketTipi === 'cikis' && durum === 'gecerli' && bilgi && (
                            <button
                                type="button"
                                onClick={() => {
                                    if (isParcalaAcik) {
                                        setParcalaModu(null);
                                    } else {
                                        setParcalaModu(palet_no);
                                        setParcalaMiktar(ozelMiktar ? String(ozelMiktar) : '');
                                    }
                                }}
                                className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                                    isParcalaAcik || ozelMiktar
                                        ? 'bg-amber-100 text-amber-600 border border-amber-200'
                                        : 'hover:bg-slate-100 text-slate-400'
                                }`}
                                title="Kısmi Miktar"
                            >
                                <Scissors className="w-4 h-4" />
                            </button>
                        )}
                        {/* Sil butonu */}
                        <button
                            type="button"
                            onClick={() => handlePaletSil(palet_no)}
                            className="w-9 h-9 rounded-xl flex items-center justify-center
                                hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all"
                            title="Listeden Kaldır"
                        >
                            <X className="w-4 h-4" strokeWidth={3} />
                        </button>
                    </div>
                </div>

                {/* Parçala paneli */}
                {isParcalaAcik && bilgi && (
                    <div className="px-4 py-3 border-t border-amber-200 bg-amber-50/50">
                        <p className="text-xs font-black text-amber-700 uppercase tracking-wider mb-2">
                            Kısmi Çıkış Miktarı <span className="normal-case tracking-normal font-semibold text-amber-500">(maks: {bilgi.miktar})</span>
                        </p>
                        <div className="flex items-center gap-2">
                            <input
                                type="number"
                                inputMode="numeric"
                                min="1"
                                max={bilgi.miktar}
                                value={parcalaMiktar}
                                onChange={e => {
                                    const val = e.target.value;
                                    if (val === '' || (Number(val) >= 1 && Number(val) <= bilgi.miktar)) {
                                        setParcalaMiktar(val);
                                    }
                                }}
                                placeholder="Tam"
                                className="flex-1 h-12 text-center text-xl font-black rounded-xl
                                    border-2 border-amber-200 bg-white text-slate-800
                                    placeholder-amber-300
                                    focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-400/20
                                    transition-all
                                    [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                            />
                            <button
                                type="button"
                                onClick={() => handleParcalaOnayla(palet_no)}
                                className="h-12 px-5 rounded-xl bg-amber-500 text-white font-black text-sm
                                    hover:bg-amber-600 active:scale-95 transition-all shadow-sm"
                            >
                                Uygula
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    // Tam çıkışa geri dön
                                    setTaramaListesi(prev => prev.map(t =>
                                        t.palet_no === palet_no ? { ...t, miktar: null } : t
                                    ));
                                    setParcalaModu(null);
                                    setParcalaMiktar('');
                                }}
                                className="h-12 px-4 rounded-xl bg-slate-200 text-slate-600 font-bold text-sm
                                    hover:bg-slate-300 active:scale-95 transition-all"
                            >
                                Tam
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    };

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
                                            Toplu Palet Kabul
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
                                            Toplu Palet Sevk
                                        </span>
                                    </div>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ===== ADIM 2: ÇOKLU PALET TARAMA ===== */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <StepHeader onBack={resetForm} backLabel="Geri Dön" />

                            {/* Palet No Girişi */}
                            <div>
                                <label className="text-xs font-black text-slate-500 uppercase tracking-[0.15em] mb-3 block">
                                    Palet Numarası Ekle
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
                                                    handlePaletEkle();
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

                            {/* Ekle Butonu */}
                            <button
                                onClick={() => handlePaletEkle()}
                                disabled={!paletNo.trim()}
                                className={`w-full h-14 rounded-2xl text-base font-black text-white
                                    flex items-center justify-center gap-3 transition-all shadow-lg
                                    bg-blue-600 hover:bg-blue-700 active:scale-[0.97] shadow-blue-600/30
                                    ${!paletNo.trim() ? 'opacity-40 cursor-not-allowed' : ''}`}
                            >
                                <Layers className="w-5 h-5" />
                                Listeye Ekle
                            </button>

                            <div className="flex items-center justify-center gap-2 py-1">
                                <div className="h-px flex-1 bg-slate-200" />
                                <span className="text-xs font-bold text-slate-400 uppercase">veya fiziksel barkod okuyucu ile tarayın</span>
                                <div className="h-px flex-1 bg-slate-200" />
                            </div>

                            {/* Tarama Listesi */}
                            {taramaListesi.length > 0 && (
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <h4 className="text-xs font-black text-slate-500 uppercase tracking-[0.15em]">
                                            Tarama Listesi
                                        </h4>
                                        <div className="flex items-center gap-2">
                                            {hataliPaletler.length > 0 && (
                                                <span className="text-xs font-black text-red-500 bg-red-50 px-2 py-1 rounded-lg border border-red-100">
                                                    {hataliPaletler.length} hatalı
                                                </span>
                                            )}
                                            <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-lg">
                                                {taramaListesi.length} / {MAKS_PALET}
                                            </span>
                                        </div>
                                    </div>

                                    {taramaListesi.map(kalem => (
                                        <PaletKarti key={kalem.palet_no} kalem={kalem} />
                                    ))}
                                </div>
                            )}

                            {/* Devam Et Butonu */}
                            {taramaListesi.length > 0 && (
                                <button
                                    onClick={() => setStep(3)}
                                    disabled={gecerliPaletler.length === 0 || yukleniyor}
                                    className={`w-full h-16 rounded-2xl text-lg font-black text-white
                                        flex items-center justify-center gap-3 transition-all shadow-xl
                                        ${gecerliPaletler.length === 0 || yukleniyor
                                            ? 'bg-slate-300 shadow-none cursor-not-allowed text-slate-500'
                                            : hareketTipi === 'giris'
                                                ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/30 active:scale-[0.97]'
                                                : 'bg-red-600 hover:bg-red-700 shadow-red-600/30 active:scale-[0.97]'
                                        }`}
                                >
                                    <Check className="w-6 h-6" strokeWidth={3} />
                                    Devam Et ({gecerliPaletler.length} palet)
                                </button>
                            )}
                        </div>
                    )}

                    {/* ===== ADIM 3: TOPLU ÖNİZLEME + ONAYLA ===== */}
                    {step === 3 && (
                        <div className="space-y-5">
                            <StepHeader
                                onBack={() => setStep(2)}
                                backLabel="Listeye Dön"
                            />

                            {/* Özet Kart */}
                            <div className="rounded-2xl border-2 border-slate-200 bg-slate-50 overflow-hidden">
                                <div className="px-4 py-3.5 bg-slate-800 flex items-center gap-3">
                                    <Layers className="w-5 h-5 text-slate-300" />
                                    <span className="text-sm font-black text-white tracking-wide">Toplu İşlem Özeti</span>
                                    <span className={`ml-auto text-sm font-black px-3 py-1 rounded-lg ${
                                        hareketTipi === 'giris'
                                            ? 'text-emerald-300 bg-emerald-900/40'
                                            : 'text-red-300 bg-red-900/40'
                                    }`}>
                                        {gecerliPaletler.length} palet — {hareketTipi === 'giris' ? 'Giriş' : 'Çıkış'}
                                    </span>
                                </div>

                                <div className="p-4 space-y-2 max-h-80 overflow-y-auto">
                                    {gecerliPaletler.map(kalem => (
                                        <div key={kalem.palet_no} className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200">
                                            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                                                <Box className="w-4 h-4 text-blue-600" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-black text-slate-800 truncate">{kalem.palet_no}</p>
                                                {kalem.bilgi && (
                                                    <p className="text-xs font-semibold text-slate-400 truncate">
                                                        {kalem.bilgi.urun_adi}
                                                        {kalem.bilgi.raf_bilgi && ` · ${kalem.bilgi.raf_bilgi}`}
                                                    </p>
                                                )}
                                            </div>
                                            <span className="text-base font-black text-slate-700 flex-shrink-0">
                                                {kalem.miktar || kalem.bilgi?.miktar || '?'} <span className="text-xs font-bold text-slate-400">koli</span>
                                                {kalem.miktar && kalem.bilgi && kalem.miktar !== kalem.bilgi.miktar && (
                                                    <span className="block text-[10px] font-black text-amber-600">kısmi</span>
                                                )}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Toplam */}
                                <div className="px-4 py-3 border-t border-slate-200 bg-slate-100/50 flex items-center justify-between">
                                    <span className="text-xs font-black text-slate-500 uppercase">Toplam Koli</span>
                                    <span className="text-lg font-black text-slate-800">
                                        {gecerliPaletler.reduce((acc, t) => acc + (t.miktar || t.bilgi?.miktar || 0), 0)}
                                    </span>
                                </div>
                            </div>

                            {/* Çıkış Ortak Alanları */}
                            {hareketTipi === 'cikis' && (
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
                            )}

                            {/* Hatalı paletler uyarısı */}
                            {hataliPaletler.length > 0 && (
                                <div className="p-4 rounded-2xl bg-amber-50 border-2 border-amber-200/60 flex items-start gap-3">
                                    <div className="w-10 h-10 rounded-2xl bg-white shadow-sm border border-amber-100 flex items-center justify-center text-amber-500 flex-shrink-0">
                                        <AlertTriangle className="w-5 h-5" />
                                    </div>
                                    <div className="pt-0.5">
                                        <h4 className="text-sm font-black text-amber-900">{hataliPaletler.length} palet hatalı</h4>
                                        <p className="text-xs font-semibold text-amber-700/80 mt-0.5">
                                            Hatalı paletler işleme dahil edilmeyecek. Listeye dönüp kaldırabilirsiniz.
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
                                    disabled={submitting || gecerliPaletler.length === 0}
                                    className={`h-16 rounded-2xl text-lg font-black text-white
                                        active:scale-[0.97] transition-all shadow-xl
                                        flex items-center justify-center gap-3
                                        ${submitting || gecerliPaletler.length === 0
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
                                    {submitting ? 'Kaydediliyor...' : `Onayla (${gecerliPaletler.length})`}
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
                            {sonIslemler.slice(0, visibleCount).map(h => {
                                const isGiris = h.hareket_tipi === 'giris';
                                const tarih = new Date(h.tarih);
                                return (
                                    <div key={h.id} className="flex items-center gap-3 px-4 py-3.5
                                        bg-white rounded-2xl border border-slate-100
                                        hover:border-slate-200 transition-colors shadow-sm">
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
                                        <span className={`text-xl font-black tabular-nums flex-shrink-0
                                            ${isGiris ? 'text-emerald-600' : 'text-red-500'}`}>
                                            {isGiris ? '+' : '−'}{h.miktar}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

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
                    handlePaletEkle(code);
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
