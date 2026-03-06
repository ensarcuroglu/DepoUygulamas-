import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { ArrowDownToLine, ArrowUpFromLine, Barcode, Check, Loader2, Package, Clock, Search, X, TrendingUp, TrendingDown, ArrowLeft, RefreshCw } from 'lucide-react';
import { getStokHareketleri, createStokHareketi, getUrunler, getUrunByBarkod } from '../services/api';
import toast from 'react-hot-toast';
import useBarcodeScanner from '../hooks/useBarcodeScanner';
import ZXingBarcodeScanner from '../components/common/ZXingBarcodeScanner';

export default function StokHareketleriPage() {
    // ===== STATE =====
    const [step, setStep] = useState(1); // 1: Tip seç, 2: Ürün seç, 3: Miktar, 4: Sonuç
    const [hareketTipi, setHareketTipi] = useState('');
    const [secilenUrun, setSecilenUrun] = useState(null);
    const [miktar, setMiktar] = useState(1);
    const [aciklama, setAciklama] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Ürün arama
    const [urunler, setUrunler] = useState([]);
    const [aramaText, setAramaText] = useState('');
    const [aramaFocused, setAramaFocused] = useState(false);

    // Kamera tarayıcı
    const [cameraScannerOpen, setCameraScannerOpen] = useState(false);

    // Son işlemler
    const [sonIslemler, setSonIslemler] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(true);

    const barkodInputRef = useRef(null);
    const miktarInputRef = useRef(null);

    // ===== VERİ YÜKLEME =====
    const fetchData = () => {
        Promise.all([
            getUrunler({ limit: 500 }),
            getStokHareketleri({ limit: 20 })
        ]).then(([uRes, hRes]) => {
            setUrunler(uRes.data);
            setSonIslemler(hRes.data);
        }).catch(() => toast.error('Veriler yüklenemedi.'))
            .finally(() => setLoadingHistory(false));
    };

    useEffect(() => { fetchData(); }, []);

    // ===== BARKOD TARAMA (Fiziksel okuyucu) =====
    useBarcodeScanner({
        isEnabled: step === 2,
        onScan: async (code) => {
            try {
                const res = await getUrunByBarkod(code);
                handleUrunSec(res.data);
                toast.success(`${res.data.isim} okutuldu`, { icon: '📦' });
            } catch {
                toast.error(`Ürün bulunamadı: ${code}`);
            }
        }
    });

    // ===== İŞLEMLER =====
    const handleUrunSec = (urun) => {
        setSecilenUrun(urun);
        setAramaText('');
        setAramaFocused(false);
        setStep(3);
        setTimeout(() => miktarInputRef.current?.focus(), 100);
    };

    const handleBarkodArama = async () => {
        if (!aramaText.trim()) return;
        try {
            const res = await getUrunByBarkod(aramaText.trim());
            handleUrunSec(res.data);
            toast.success(`${res.data.isim} bulundu`, { icon: '📦' });
        } catch {
            // Ürün bulunamadıysa normal arama yap
        }
    };

    const handleSubmit = async () => {
        if (!secilenUrun || !hareketTipi || miktar < 1) return;
        setSubmitting(true);
        try {
            await createStokHareketi({
                urun_id: secilenUrun.id,
                hareket_tipi: hareketTipi,
                miktar: Number(miktar),
                aciklama: aciklama || ''
            });
            const isGiris = hareketTipi === 'giris';
            toast.success(
                isGiris
                    ? `+${miktar} ${secilenUrun.isim} giriş yapıldı`
                    : `-${miktar} ${secilenUrun.isim} çıkış yapıldı`,
                { icon: isGiris ? '📥' : '📤', duration: 3000 }
            );
            // Başarılı — sıfırla
            setStep(1);
            setHareketTipi('');
            setSecilenUrun(null);
            setMiktar(1);
            setAciklama('');
            fetchData(); // Geçmişi güncelle
        } catch (err) {
            toast.error(err.response?.data?.detail || 'İşlem başarısız!');
        } finally {
            setSubmitting(false);
        }
    };

    const resetForm = () => {
        setStep(1);
        setHareketTipi('');
        setSecilenUrun(null);
        setMiktar(1);
        setAciklama('');
        setAramaText('');
    };

    // Filtrelenmiş ürünler
    const filteredUrunler = aramaText.length >= 1
        ? urunler.filter(u =>
            u.isim.toLowerCase().includes(aramaText.toLowerCase()) ||
            (u.barkod && u.barkod.toLowerCase().includes(aramaText.toLowerCase())) ||
            (u.ean && u.ean.includes(aramaText))
        ).slice(0, 8)
        : [];

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
                                        Ürün Kabul
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
                                        Ürün Sevk
                                    </span>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ===== ADIM 2: ÜRÜN SEÇ ===== */}
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

                            {/* Barkod / Arama */}
                            <div className="relative">
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                                        <input
                                            ref={barkodInputRef}
                                            autoFocus
                                            type="text"
                                            placeholder="Barkod okut veya ürün ara..."
                                            value={aramaText}
                                            onChange={e => setAramaText(e.target.value)}
                                            onFocus={() => setAramaFocused(true)}
                                            onKeyDown={e => {
                                                if (e.key === 'Enter') {
                                                    e.preventDefault();
                                                    handleBarkodArama();
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

                                {/* Arama sonuçları dropdown */}
                                {aramaFocused && filteredUrunler.length > 0 && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-slate-200 shadow-xl z-50 overflow-hidden max-h-[45vh] min-h-[300px] overflow-y-auto">
                                        {filteredUrunler.map(u => (
                                            <button
                                                key={u.id}
                                                onClick={() => handleUrunSec(u)}
                                                className="w-full flex items-center justify-between gap-3 px-4 py-4 sm:py-5 hover:bg-blue-50 active:bg-blue-100 transition-colors text-left border-b border-slate-100 last:border-0 group"
                                            >
                                                <div className="flex items-center gap-4 min-w-0">
                                                    <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0 group-hover:bg-white group-hover:shadow-sm transition-all">
                                                        <Package className="w-6 h-6 sm:w-7 sm:h-7 text-slate-500 group-hover:text-blue-600 transition-colors" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-base sm:text-lg font-extrabold text-slate-800 truncate">{u.isim}</p>
                                                        <p className="text-sm font-semibold text-slate-500 mt-1">
                                                            <span className="text-slate-400">{u.barkod || 'Barkod yok'}</span> <span className="mx-1">•</span> Stok: <span className="text-slate-700">{u.stok_miktari}</span> {u.birim}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-all">
                                                    <ArrowDownToLine className="w-4 h-4 sm:w-5 sm:h-5 -rotate-90" />
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Arama sonucu yoksa */}
                                {aramaFocused && aramaText.length >= 2 && filteredUrunler.length === 0 && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-slate-200 shadow-xl z-50 p-6 text-center">
                                        <Package className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                                        <p className="text-sm font-bold text-slate-500">Ürün bulunamadı</p>
                                        <p className="text-xs text-slate-400 mt-1">Farklı bir barkod veya isim deneyin</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ===== ADIM 3: MİKTAR VE ONAYLA ===== */}
                    {step === 3 && secilenUrun && (
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
                                    onClick={() => setStep(2)}
                                    className="flex items-center gap-2 h-10 px-3 sm:px-4 rounded-xl bg-orange-50 text-orange-600 font-bold text-sm sm:text-base hover:bg-orange-100 hover:text-orange-700 active:scale-95 transition-all"
                                >
                                    <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5" />
                                    <span className="hidden sm:inline">Ürünü Değiştir</span>
                                </button>
                            </div>

                            {/* Seçilen ürün kartı */}
                            <div className="flex items-center gap-3 p-3 sm:p-4 rounded-xl bg-slate-50 border border-slate-200">
                                <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                                    <Package className="w-6 h-6 text-blue-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-base font-extrabold text-slate-800 truncate">{secilenUrun.isim}</p>
                                    <p className="text-xs font-semibold text-slate-400 mt-0.5">
                                        {secilenUrun.barkod || '-'} • Mevcut: {secilenUrun.stok_miktari} {secilenUrun.birim}
                                    </p>
                                </div>
                            </div>

                            {/* Miktar girişi — Modern UI */}
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 block">
                                    Miktar Girin
                                </label>

                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 sm:gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setMiktar(Math.max(1, miktar - 1))}
                                            className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white border border-slate-200 text-3xl font-light text-slate-600 hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100 active:scale-95 transition-all flex items-center justify-center shadow-sm select-none flex-shrink-0"
                                        >
                                            −
                                        </button>

                                        <input
                                            ref={miktarInputRef}
                                            type="number"
                                            inputMode="numeric"
                                            min="1"
                                            value={miktar}
                                            onChange={e => setMiktar(Math.max(1, parseInt(e.target.value) || 1))}
                                            className="flex-1 w-full min-w-0 h-14 sm:h-16 text-center text-3xl sm:text-4xl font-black rounded-2xl border-2 border-slate-200 bg-white text-slate-800 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all shadow-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                        />

                                        <button
                                            type="button"
                                            onClick={() => setMiktar(miktar + 1)}
                                            className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white border border-slate-200 text-3xl font-light text-slate-600 hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100 active:scale-95 transition-all flex items-center justify-center shadow-sm select-none flex-shrink-0"
                                        >
                                            +
                                        </button>
                                    </div>

                                    {/* Hızlı Miktar Butonları */}
                                    <div className="flex flex-wrap gap-2">
                                        {[5, 10, 50].map(val => (
                                            <button
                                                key={val}
                                                type="button"
                                                onClick={() => setMiktar(miktar + val)}
                                                className="flex-1 h-10 sm:h-11 rounded-xl bg-blue-50 text-blue-700 font-bold text-sm sm:text-base hover:bg-blue-100 active:scale-95 transition-all select-none"
                                            >
                                                +{val}
                                            </button>
                                        ))}

                                        {/* Sadece çıkış işlemiyse MAX butonu göster */}
                                        {hareketTipi === 'cikis' && secilenUrun?.stok_miktari > 0 && (
                                            <button
                                                type="button"
                                                onClick={() => setMiktar(secilenUrun.stok_miktari)}
                                                className="flex-1 h-10 sm:h-11 rounded-xl bg-slate-800 text-white font-bold text-sm sm:text-base hover:bg-slate-900 active:scale-95 transition-all select-none"
                                            >
                                                MAX
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Açıklama (isteğe bağlı) */}
                            <div>
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 block">
                                    Not <span className="text-slate-300 normal-case">(isteğe bağlı)</span>
                                </label>
                                <input
                                    type="text"
                                    placeholder="İrsaliye no, alıcı/teslim bilgisi..."
                                    value={aciklama}
                                    onChange={e => setAciklama(e.target.value)}
                                    className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all"
                                />
                            </div>

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
                            const urun = urunler.find(u => u.id === h.urun_id);
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
                                            {urun?.isim || `Ürün #${h.urun_id}`}
                                        </p>
                                        <p className="text-xs font-medium text-slate-400 mt-0.5">
                                            {tarih.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })} — {tarih.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
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
                onScanSuccess={async (code) => {
                    try {
                        const res = await getUrunByBarkod(code);
                        handleUrunSec(res.data);
                        toast.success(`${res.data.isim} okutuldu`, { icon: '📷' });
                    } catch {
                        toast.error(`Ürün bulunamadı: ${code}`);
                    }
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
