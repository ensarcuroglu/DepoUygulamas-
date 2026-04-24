import { useState, useRef, useEffect, useCallback } from 'react';
import { Scan, CheckCircle, AlertTriangle, X, Loader2, Package, MapPin } from 'lucide-react';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import useTerminalScanInput from '../hooks/useTerminalScanInput';
import { sanitizeBarkod } from '../utils/barcode';
import { uretimPaletiKabulEt, uretimPaletiYerlestir, getRaflar, getUretimPaleti } from '../services/api';

// ── Sabitler ──────────────────────────────────────────────────────────────────

const FAZ = {
    PALET_BEKLIYOR: 'palet_bekliyor',
    RAF_BEKLIYOR: 'raf_bekliyor',
};

const SONUC = {
    BASARI: 'basari',
    HATA: 'hata',
};

const idempotencyConfig = (idempotencyKey) => (
    idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : {}
);

// ── Bileşen ───────────────────────────────────────────────────────────────────

export default function UretimPaletiKabulPage() {
    const [faz, setFaz] = useState(FAZ.PALET_BEKLIYOR);
    const [barkodInput, setBarkodInput] = useState('');
    const [yukleniyor, setYukleniyor] = useState(false);
    const [sonuc, setSonuc] = useState(null);
    const [gecmis, setGecmis] = useState([]);
    const [raflar, setRaflar] = useState([]);

    // Kabul edilen palet bilgisi (faz 2 için)
    const [kabulBilgi, setKabulBilgi] = useState(null);

    const inputRef = useRef(null);
    const resetTimerRef = useRef(null);

    // Raf listesini bir kez yükle (client-side raf kodu → raf_id çözümleme)
    useEffect(() => {
        getRaflar()
            .then((res) => setRaflar(res.data || []))
            .catch(() => {/* sessiz hata — raf çözümleme yapılamaz */});
    }, []);

    useEffect(() => {
        inputRef.current?.focus();
    }, [faz]);

    // Sıfırlama: 3 saniye sonra faz 1'e dön
    const otomatikSifirla = useCallback(() => {
        if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
        resetTimerRef.current = setTimeout(() => {
            setFaz(FAZ.PALET_BEKLIYOR);
            setKabulBilgi(null);
            setSonuc(null);
            setBarkodInput('');
            setTimeout(() => inputRef.current?.focus(), 50);
        }, 3000);
    }, []);

    // Temizlik
    useEffect(() => {
        return () => {
            if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
        };
    }, []);

    // ── Raf kodu → raf_id çözümleme ──
    const rafKoduCozumle = (kod) => {
        const normalKod = sanitizeBarkod(kod, 'raf');
        const raf = raflar.find(
            (r) => [r.kod, r.raf_kodu, r.barkod, String(r.id)]
                .filter(Boolean)
                .some((aday) => String(aday).toUpperCase() === normalKod)
        );
        return raf || null;
    };

    // ── Faz 1: Palet barkod okut ──
    const paletOkut = async (barkod, meta = {}) => {
        const paletBarkod = sanitizeBarkod(barkod, 'palet');
        if (!paletBarkod) return false;

        setYukleniyor(true);
        setSonuc(null);

        try {
            // Önce palet durumunu kontrol et
            let palet;
            try {
                const durumRes = await getUretimPaleti(paletBarkod);
                palet = durumRes.data;
            } catch {
                // Palet bulunamadı veya ağ hatası — kabul-et dene
                palet = null;
            }

            // Zaten YERLESTIRME_BEKLIYOR ise doğrudan Faz 2'ye geç
            if (palet && (palet.durum === 'YerlestirmeBekliyor' || palet.durum === 'YERLESTIRME_BEKLIYOR')) {
                setKabulBilgi(palet);
                setFaz(FAZ.RAF_BEKLIYOR);
                setSonuc({
                    tip: SONUC.BASARI,
                    mesaj: `Palet zaten kabul edilmiş — ${palet.koli_adedi} koli — Raf barkodunu okutun`,
                    palet,
                });
                toast.success(`${paletBarkod} zaten kabul edilmiş — raf barkodunu okutun`);
                return true;
            }

            // Normal akış: kabul-et çağrısı
            const res = await uretimPaletiKabulEt(paletBarkod, idempotencyConfig(meta.idempotencyKey));
            palet = res.data;
            const yeniSonuc = {
                tip: SONUC.BASARI,
                mesaj: `Kabul edildi — ${palet.koli_adedi} koli — Şimdi raf barkodunu okutun`,
                palet,
            };
            setSonuc(yeniSonuc);
            setKabulBilgi(palet);
            setFaz(FAZ.RAF_BEKLIYOR);
            toast.success(`${paletBarkod} kabul edildi — raf barkodunu okutun`);
            return true;
        } catch (err) {
            const mesaj = hataMetni(err, 'Kabul işlemi başarısız');
            const yeniSonuc = { tip: SONUC.HATA, mesaj };
            setSonuc(yeniSonuc);
            setGecmis((prev) => [
                { ...yeniSonuc, paletNo: paletBarkod, rafKod: null, zaman: new Date().toLocaleTimeString('tr-TR') },
                ...prev.slice(0, 19),
            ]);
            toast.error(mesaj);
            return false;
        } finally {
            setYukleniyor(false);
            setBarkodInput('');
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    };

    // ── Faz 2: Raf barkod okut ──
    const rafOkut = async (barkod, meta = {}) => {
        const rafBarkod = sanitizeBarkod(barkod, 'raf');
        if (!kabulBilgi || !rafBarkod) return false;

        setYukleniyor(true);
        setSonuc(null);

        // Raf kodu → raf_id çözümle
        const raf = rafKoduCozumle(rafBarkod);
        if (!raf) {
            const mesaj = `Raf bulunamadı: "${rafBarkod}" — geçerli bir raf kodu okutun`;
            setSonuc({ tip: SONUC.HATA, mesaj });
            toast.error(mesaj);
            setYukleniyor(false);
            setBarkodInput('');
            setTimeout(() => inputRef.current?.focus(), 50);
            return false;
        }

        try {
            await uretimPaletiYerlestir(kabulBilgi.palet_no, {
                palet_no: kabulBilgi.palet_no,
                raf_id: raf.id,
            }, idempotencyConfig(meta.idempotencyKey));

            const rafKod = raf.kod || raf.raf_kodu || rafBarkod;
            const yeniSonuc = {
                tip: SONUC.BASARI,
                mesaj: `Yerleştirildi — Raf ${rafKod}`,
                palet: kabulBilgi,
                rafKod,
            };
            setSonuc(yeniSonuc);
            setGecmis((prev) => [
                {
                    ...yeniSonuc,
                    paletNo: kabulBilgi.palet_no,
                    rafKod,
                    zaman: new Date().toLocaleTimeString('tr-TR'),
                },
                ...prev.slice(0, 19),
            ]);
            toast.success(`${kabulBilgi.palet_no} → ${rafKod} yerleştirildi`);

            // 3 saniye sonra otomatik sıfırla
            otomatikSifirla();
            return true;
        } catch (err) {
            const mesaj = hataMetni(err, 'Yerleştirme başarısız');
            const yeniSonuc = { tip: SONUC.HATA, mesaj };
            setSonuc(yeniSonuc);
            setGecmis((prev) => [
                {
                    ...yeniSonuc,
                    paletNo: kabulBilgi.palet_no,
                    rafKod: raf.kod || raf.raf_kodu || rafBarkod,
                    zaman: new Date().toLocaleTimeString('tr-TR'),
                },
                ...prev.slice(0, 19),
            ]);
            toast.error(mesaj);
            return false;
        } finally {
            setYukleniyor(false);
            setBarkodInput('');
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    };

    // ── Form gönder ──
    const scanMode = faz === FAZ.PALET_BEKLIYOR ? 'palet' : 'raf';
    const scanInput = useTerminalScanInput({
        mode: scanMode,
        value: barkodInput,
        setValue: setBarkodInput,
        inputRef,
        contextKey: scanMode === 'palet'
            ? 'uretim-paleti-kabul:palet'
            : `uretim-paleti-kabul:${kabulBilgi?.palet_no || 'yok'}:raf`,
        disabled: yukleniyor,
        isEnabled: !yukleniyor,
        onSubmit: async (code, meta) => (scanMode === 'palet'
            ? paletOkut(code, meta)
            : rafOkut(code, meta)),
    });

    const okut = async (e) => {
        e.preventDefault();
        await scanInput.submitScan();
    };

    // ── Faz bazlı UI değerleri ──
    const fazConfig = {
        [FAZ.PALET_BEKLIYOR]: {
            placeholder: 'Palet barkodunu okutun — PRD-YYYYMMDD-NNNN',
            butonLabel: 'Kabul Et',
            butonIcon: <CheckCircle className="w-5 h-5" />,
            renkBg: 'bg-blue-600 hover:bg-blue-700',
            borderRenk: 'border-blue-200 focus:border-blue-500 focus:ring-blue-500/20',
            ikonRenk: 'text-blue-700',
            bgRenk: 'bg-blue-100',
        },
        [FAZ.RAF_BEKLIYOR]: {
            placeholder: 'Raf barkodunu okutun — ZON-KORIDOR-RAF-KAT-GOZ',
            butonLabel: 'Yerleştir',
            butonIcon: <MapPin className="w-5 h-5" />,
            renkBg: 'bg-emerald-600 hover:bg-emerald-700',
            borderRenk: 'border-emerald-300 focus:border-emerald-500 focus:ring-emerald-500/20',
            ikonRenk: 'text-emerald-700',
            bgRenk: 'bg-emerald-100',
        },
    };

    const config = fazConfig[faz];

    return (
        <div className="p-6 max-w-2xl mx-auto space-y-6">
            {/* Başlık */}
            <div className="flex items-center gap-3">
                <div className={`p-2 ${config.bgRenk} rounded-xl transition-colors`}>
                    {faz === FAZ.PALET_BEKLIYOR
                        ? <Scan className={`w-6 h-6 ${config.ikonRenk}`} />
                        : <MapPin className={`w-6 h-6 ${config.ikonRenk}`} />
                    }
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-900">Üretimden Kabul</h1>
                    <p className="text-sm text-gray-500">
                        {faz === FAZ.PALET_BEKLIYOR
                            ? 'Palet barkodunu okutun — otomatik kabul + yerleştirme'
                            : '✓ Palet kabul edildi — şimdi raf barkodunu okutun'
                        }
                    </p>
                </div>
            </div>

            {/* Faz Göstergesi */}
            <div className="flex items-center gap-2">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                    faz === FAZ.PALET_BEKLIYOR
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-emerald-100 text-emerald-800 line-through opacity-60'
                }`}>
                    <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">1</span>
                    Palet Okut
                </div>
                <div className="w-4 h-px bg-gray-300" />
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                    faz === FAZ.RAF_BEKLIYOR
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-gray-100 text-gray-400'
                }`}>
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                        faz === FAZ.RAF_BEKLIYOR ? 'bg-emerald-600 text-white' : 'bg-gray-300 text-gray-500'
                    }`}>2</span>
                    Raf Okut
                </div>
            </div>

            {/* Okutma Formu */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                <form onSubmit={okut} className="space-y-4">
                    <div className="relative">
                        {faz === FAZ.PALET_BEKLIYOR
                            ? <Scan className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            : <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-emerald-500" />
                        }
                        <input
                            ref={scanInput.inputRef}
                            type="text"
                            value={barkodInput}
                            onChange={(e) => setBarkodInput(e.target.value)}
                            onKeyDown={scanInput.handleKeyDown}
                            placeholder={config.placeholder}
                            disabled={yukleniyor}
                            className={`w-full pl-12 pr-4 py-4 text-xl font-mono border-2 ${config.borderRenk} rounded-xl focus:outline-none focus:ring-2 transition-all disabled:opacity-50`}
                        />
                        {barkodInput && (
                            <button
                                type="button"
                                onClick={() => setBarkodInput('')}
                                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100"
                            >
                                <X className="w-4 h-4 text-gray-400" />
                            </button>
                        )}
                    </div>
                    <button
                        type="submit"
                        disabled={!barkodInput.trim() || yukleniyor}
                        className={`w-full py-3 ${config.renkBg} text-white font-semibold rounded-xl disabled:opacity-50 transition-colors flex items-center justify-center gap-2`}
                    >
                        {yukleniyor ? (
                            <><Loader2 className="w-5 h-5 animate-spin" /> İşleniyor...</>
                        ) : (
                            <>{config.butonIcon} {config.butonLabel}</>
                        )}
                    </button>
                </form>

                {/* Kabul Bilgi Kartı (faz 2) */}
                {faz === FAZ.RAF_BEKLIYOR && kabulBilgi && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                        <div className="flex items-center gap-2 mb-2">
                            <CheckCircle className="w-4 h-4 text-blue-600" />
                            <span className="text-sm font-semibold text-blue-800">Palet Kabul Edildi</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                                <span className="text-blue-600">Palet No:</span>
                                <span className="ml-1 font-mono font-semibold text-blue-900">{kabulBilgi.palet_no}</span>
                            </div>
                            <div>
                                <span className="text-blue-600">Koli:</span>
                                <span className="ml-1 font-semibold text-blue-900">{kabulBilgi.koli_adedi} adet</span>
                            </div>
                            {kabulBilgi.urun_isim && (
                                <div className="col-span-2">
                                    <span className="text-blue-600">Ürün:</span>
                                    <span className="ml-1 text-blue-900">{kabulBilgi.urun_isim}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Sonuç */}
                {sonuc && faz === FAZ.PALET_BEKLIYOR && (
                    <div className={`mt-4 flex items-start gap-3 p-4 rounded-xl border ${
                        sonuc.tip === SONUC.BASARI
                            ? 'bg-emerald-50 border-emerald-200'
                            : 'bg-red-50 border-red-200'
                    }`}>
                        {sonuc.tip === SONUC.BASARI ? (
                            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        ) : (
                            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                            <p className={`font-semibold text-sm ${sonuc.tip === SONUC.BASARI ? 'text-emerald-800' : 'text-red-800'}`}>
                                {sonuc.tip === SONUC.BASARI ? 'Tamamlandı' : 'Hata'}
                            </p>
                            <p className={`text-sm mt-0.5 ${sonuc.tip === SONUC.BASARI ? 'text-emerald-700' : 'text-red-700'}`}>
                                {sonuc.mesaj}
                            </p>
                            {sonuc.palet && sonuc.rafKod && (
                                <p className="text-xs text-emerald-600 mt-1 font-mono">
                                    {sonuc.palet.palet_no} → {sonuc.rafKod} · {sonuc.palet.koli_adedi} koli
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* Hata sonucu (faz 2) */}
                {sonuc && sonuc.tip === SONUC.HATA && faz === FAZ.RAF_BEKLIYOR && (
                    <div className="mt-4 flex items-start gap-3 p-4 rounded-xl border bg-red-50 border-red-200">
                        <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="font-semibold text-sm text-red-800">Hata</p>
                            <p className="text-sm mt-0.5 text-red-700">{sonuc.mesaj}</p>
                        </div>
                    </div>
                )}

                {/* Başarılı yerleştirme sonucu */}
                {sonuc && sonuc.tip === SONUC.BASARI && sonuc.rafKod && (
                    <div className="mt-4 flex items-start gap-3 p-4 rounded-xl border bg-emerald-50 border-emerald-200">
                        <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="font-semibold text-sm text-emerald-800">Tamamlandı</p>
                            <p className="text-sm mt-0.5 text-emerald-700">{sonuc.mesaj}</p>
                            {sonuc.palet && (
                                <p className="text-xs text-emerald-600 mt-1 font-mono">
                                    {sonuc.palet.palet_no} → {sonuc.rafKod} · {sonuc.palet.koli_adedi} koli
                                </p>
                            )}
                            <p className="text-xs text-emerald-500 mt-2">3 saniye sonra sıradaki palet için sıfırlanacak...</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Oturum Geçmişi */}
            {gecmis.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                    <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-700">Son İşlemler</span>
                        <span className="text-xs text-gray-400">{gecmis.length} kayıt</span>
                    </div>
                    <ul className="divide-y divide-gray-50">
                        {gecmis.map((g, i) => (
                            <li key={i} className="flex items-center gap-3 px-5 py-3">
                                {g.tip === SONUC.BASARI ? (
                                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                ) : (
                                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                                )}
                                <span className="font-mono text-sm text-gray-800 flex-1">{g.paletNo}</span>
                                {g.rafKod && (
                                    <span className="text-xs font-mono px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md">
                                        → {g.rafKod}
                                    </span>
                                )}
                                <span className="text-xs text-gray-400">{g.zaman}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {gecmis.length === 0 && (
                <div className="text-center py-10 text-gray-300">
                    <Package className="w-10 h-10 mx-auto mb-2" />
                    <p className="text-sm">Henüz işlem yapılmadı</p>
                    <p className="text-xs mt-1">Palet barkodunu okutarak başlayın</p>
                </div>
            )}
        </div>
    );
}
