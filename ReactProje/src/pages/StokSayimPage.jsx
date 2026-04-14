import { useState, useEffect, useRef, useCallback } from 'react';
import { useAsync } from '../hooks/useAsync';
import api from '../services/api';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Barcode, Plus, Minus, Play, CheckCircle2, 
    AlertCircle, FileText, X, History, Package, ShieldCheck
} from 'lucide-react';

const EAN_REGEX = /^\d{8,14}$/;

// İşitsel geri bildirim için yardımcı fonksiyon (Harici dosya gerektirmez)
const playBeep = () => {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioCtx = new AudioContext();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 notası
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.1);
    } catch (e) {
        console.error("Tarayıcı ses çalamadı:", e);
    }
};

export default function StokSayimPage() {
    const [sayimlar, setSayimlar] = useState([]);
    const [aktifSayim, setAktifSayim] = useState(null);
    const [varyansData, setVaryansData] = useState(null);
    const [varyansModal, setVaryansModal] = useState(false);
    const [aciklama, setAciklama] = useState('');
    const [aciklamaModal, setAciklamaModal] = useState(false);
    const [cozumlenenUrun, setCozumlenenUrun] = useState(null);
    const [miktar, setMiktar] = useState(1);
    const barkodRef = useRef(null);

    const { loading, run } = useAsync();

    // Sayımları yükle
    const yukle = useCallback(async () => {
        await run(async () => {
            const res = await api.get('/stok-sayimlar');
            setSayimlar(res.data);
            const aktif = res.data.find(s => s.durum === 'devam_ediyor' || s.durum === 'bitti');
            setAktifSayim(aktif ?? null);
        });
    }, [run]);

    useEffect(() => { void yukle(); }, [yukle]);

    // Aktif sayım değişince barkod input'una odaklan
    useEffect(() => {
        if (aktifSayim?.durum === 'devam_ediyor' && barkodRef.current) {
            barkodRef.current.focus();
        }
    }, [aktifSayim]);

    // Yeni sayım başlat
    const sayimBaslat = async () => {
        await run(async () => {
            const res = await api.post('/stok-sayimlar', { aciklama });
            setAktifSayim(res.data);
            setSayimlar([res.data, ...sayimlar]);
            setAciklamaModal(false);
            setAciklama('');
            toast.success(`Sayım başlatıldı: ${res.data.sayim_no}`);
        });
    };

    // Barkod ile ürün kaydet
    const urunKaydet = async (barkodDegeri) => {
        if (!aktifSayim || aktifSayim.durum !== 'devam_ediyor') {
            toast.error('Bu sayım artık düzenlenemez.');
            return;
        }
        if (!EAN_REGEX.test(barkodDegeri)) {
            toast.error('Geçersiz EAN barkod (8-14 rakam olmalı)');
            return;
        }
        await run(async () => {
            const res = await api.post(`/stok-sayimlar/${aktifSayim.id}/kalemler`, {
                ean: barkodDegeri,
                sayilan_miktar: miktar,
                notlar: ''
            });
            setAktifSayim(prev => {
                const mevcutKalemler = prev.sayim_kalemleri.filter(k => k.urun_id !== res.data.urun_id);
                return { ...prev, sayim_kalemleri: [res.data, ...mevcutKalemler] };
            });
            setCozumlenenUrun({ id: res.data.urun_id, isim: res.data.urun_adi || `#${res.data.urun_id}` });
            setMiktar(1);
            playBeep(); // Başarılı okumada sesli bildirim
            toast.success(`Kaydedildi: ${res.data.urun_adi || `Ürün #${res.data.urun_id}`} × ${miktar}`);
        });
    };

    // Sayımı bitir (devam_ediyor → bitti)
    const sayimiBitir = async () => {
        if (!aktifSayim) return;
        if (!window.confirm(`"${aktifSayim.sayim_no}" sayımını bitirmek istediğinize emin misiniz?`)) return;
        await run(async () => {
            await api.post(`/stok-sayimlar/${aktifSayim.id}/bitir`);
            toast.success('Sayım bitirildi. Admin onayı bekliyor.');
            await yukle();
        });
    };

    // Varyans raporu
    const varyansGor = async (sayimId) => {
        await run(async () => {
            const res = await api.get(`/stok-sayimlar/${sayimId}/varyans`);
            setVaryansData(res.data);
            setVaryansModal(true);
        });
    };

    // Sayımı onayla (bitti → onaylandı)
    const sayimiKapat = async () => {
        if (!aktifSayim) return;
        if (aktifSayim.durum !== 'bitti') {
            toast.error('Önce sayımı bitirmeniz gerekiyor.');
            return;
        }
        if (!window.confirm(`"${aktifSayim.sayim_no}" sayımını onaylamak istediğinize emin misiniz?`)) return;
        await run(async () => {
            await api.post(`/stok-sayimlar/${aktifSayim.id}/onayla`);
            toast.success('Sayım onaylandı ve kapatıldı');
            setAktifSayim(null);
            await yukle();
        });
    };

    const sayimDuzenlenebilir = aktifSayim?.durum === 'devam_ediyor';

    return (
        <div className="min-h-screen bg-slate-50 p-4 sm:p-6 lg:p-8">
            <div className="max-w-5xl mx-auto space-y-6 lg:space-y-8">
                
                {/* HEADER */}
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                            <Barcode className="w-8 h-8 text-blue-600" />
                            Stok Sayımı
                        </h1>
                        <p className="text-sm sm:text-base text-slate-500 mt-1">Periyodik envanter kontrolü ve varyans yönetimi</p>
                    </div>
                    <button
                        onClick={() => setAciklamaModal(true)}
                        disabled={!!aktifSayim || loading}
                        className="w-full sm:w-auto bg-blue-600 text-white px-5 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-bold shadow-sm shadow-blue-200 transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                        <Play className="w-4 h-4 fill-current" /> Yeni Sayım Başlat
                    </button>
                </div>

                {/* AKTİF SAYIM PANELİ */}
                <AnimatePresence mode="popLayout">
                    {aktifSayim && (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }} 
                            animate={{ opacity: 1, y: 0 }} 
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-100 overflow-hidden"
                        >
                            {/* Panel Header */}
                            <div className="bg-slate-900 px-5 py-4 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <div className={`w-2.5 h-2.5 rounded-full ${sayimDuzenlenebilir ? 'bg-emerald-400 animate-pulse' : 'bg-blue-400'}`}></div>
                                        <h2 className="text-lg font-bold font-mono tracking-wider">{aktifSayim.sayim_no}</h2>
                                    </div>
                                    <p className="text-sm text-slate-400 mt-0.5">{aktifSayim.aciklama || 'Açıklama belirtilmedi'}</p>
                                </div>
                                <div className="flex items-center gap-2 w-full md:w-auto">
                                    <button
                                        onClick={() => varyansGor(aktifSayim.id)}
                                        disabled={loading}
                                        className="flex-1 md:flex-none bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <FileText className="w-4 h-4" /> <span className="hidden sm:inline">Varyans</span>
                                    </button>
                                    
                                    {sayimDuzenlenebilir && (
                                        <button
                                            onClick={sayimiBitir}
                                            disabled={loading}
                                            className="flex-1 md:flex-none bg-amber-500 text-slate-900 px-4 py-2 rounded-lg text-sm font-bold hover:bg-amber-400 transition-colors flex items-center justify-center gap-2 shadow-sm"
                                        >
                                            <AlertCircle className="w-4 h-4" /> Bitir
                                        </button>
                                    )}
                                    <button
                                        onClick={sayimiKapat}
                                        disabled={loading || aktifSayim.durum !== 'bitti'}
                                        className="flex-1 md:flex-none bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-emerald-400 disabled:opacity-30 disabled:bg-slate-700 disabled:text-slate-400 transition-colors flex items-center justify-center gap-2 shadow-sm"
                                    >
                                        <ShieldCheck className="w-4 h-4" /> Onayla
                                    </button>
                                </div>
                            </div>

                            <div className="p-5 sm:p-8">
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                    {/* Giriş Alanı */}
                                    <div className="lg:col-span-1 space-y-6">
                                        <div>
                                            <label className="flex items-center justify-between text-sm font-bold text-slate-700 mb-2">
                                                <span>EAN Barkod</span>
                                                {!sayimDuzenlenebilir && <span className="text-xs text-rose-500 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-100">Sayım Kapalı</span>}
                                            </label>
                                            <input
                                                ref={barkodRef}
                                                type="text"
                                                inputMode="numeric"
                                                pattern="[0-9]*"
                                                disabled={!sayimDuzenlenebilir || loading}
                                                placeholder="Barkod okutun..."
                                                onKeyDown={(e) => {
                                                    if (sayimDuzenlenebilir && e.key === 'Enter' && e.target.value.trim()) {
                                                        urunKaydet(e.target.value.trim());
                                                        e.target.value = '';
                                                    }
                                                }}
                                                className="w-full text-xl sm:text-2xl font-mono text-center tracking-widest border-2 border-slate-200 rounded-xl p-4 sm:p-5 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 bg-slate-50 transition-all disabled:bg-slate-100 disabled:text-slate-400"
                                            />
                                        </div>

                                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                            <label className="block text-center text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                                                Eklenecek Miktar
                                            </label>
                                            <div className="flex items-center justify-center gap-4">
                                                <button
                                                    type="button"
                                                    onClick={() => setMiktar(m => Math.max(1, m - 1))}
                                                    disabled={!sayimDuzenlenebilir || loading}
                                                    className="w-14 h-14 rounded-xl border-2 border-slate-200 bg-white text-slate-600 hover:bg-slate-100 hover:border-slate-300 flex items-center justify-center active:scale-95 transition-all disabled:opacity-50"
                                                >
                                                    <Minus className="w-6 h-6" />
                                                </button>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={miktar}
                                                    disabled={!sayimDuzenlenebilir || loading}
                                                    onChange={e => setMiktar(Math.max(1, parseInt(e.target.value) || 1))}
                                                    className="w-24 text-3xl font-bold text-center border-none bg-transparent focus:outline-none text-blue-700 p-0 disabled:text-slate-400"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => setMiktar(m => m + 1)}
                                                    disabled={!sayimDuzenlenebilir || loading}
                                                    className="w-14 h-14 rounded-xl border-2 border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300 flex items-center justify-center active:scale-95 transition-all disabled:opacity-50 disabled:bg-slate-50 disabled:border-slate-200 disabled:text-slate-400"
                                                >
                                                    <Plus className="w-6 h-6" />
                                                </button>
                                            </div>
                                        </div>

                                        <AnimatePresence>
                                            {cozumlenenUrun && (
                                                <motion.div 
                                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.95 }}
                                                    className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start gap-3"
                                                >
                                                    <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                                                    <div>
                                                        <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Son Okutulan</p>
                                                        <p className="font-bold text-emerald-900 mt-0.5 leading-tight">{cozumlenenUrun.isim}</p>
                                                        <p className="text-xs text-emerald-600/80 mt-1 font-mono">#{cozumlenenUrun.id}</p>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>

                                    {/* Sayılan Ürünler Listesi */}
                                    <div className="lg:col-span-2 flex flex-col h-[400px] border border-slate-200 rounded-xl overflow-hidden bg-white">
                                        <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
                                            <h3 className="font-bold text-slate-700 flex items-center gap-2">
                                                <Package className="w-4 h-4" /> Sayım Kalemleri
                                            </h3>
                                            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full">
                                                {aktifSayim.sayim_kalemleri?.length || 0} Ürün
                                            </span>
                                        </div>
                                        
                                        <div className="flex-1 overflow-y-auto p-2 bg-slate-50/50">
                                            <AnimatePresence>
                                                {aktifSayim.sayim_kalemleri?.length > 0 ? (
                                                    <div className="space-y-2">
                                                        {aktifSayim.sayim_kalemleri.map((k, idx) => (
                                                            <motion.div 
                                                                key={k.id}
                                                                initial={{ opacity: 0, x: -20 }}
                                                                animate={{ opacity: 1, x: 0 }}
                                                                transition={{ delay: idx < 10 ? idx * 0.05 : 0 }}
                                                                className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4 flex items-center gap-4 hover:border-blue-300 transition-colors shadow-sm"
                                                            >
                                                                <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-700 font-black text-xl flex items-center justify-center shrink-0">
                                                                    {k.sayilan_miktar}
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-bold text-slate-900 truncate">{k.urun_adi || `Ürün #${k.urun_id}`}</p>
                                                                    {k.notlar && <p className="text-xs text-slate-500 mt-1 truncate">{k.notlar}</p>}
                                                                </div>
                                                                <div className="text-xs font-mono text-slate-400 shrink-0">
                                                                    #{k.urun_id}
                                                                </div>
                                                            </motion.div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
                                                        <Barcode className="w-12 h-12 opacity-20" />
                                                        <p className="text-sm font-medium">Henüz ürün okutulmadı</p>
                                                    </div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* SAYIM TARİHÇESİ */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-6 py-5 border-b border-slate-100 flex items-center gap-2">
                        <History className="w-5 h-5 text-slate-400" />
                        <h2 className="font-bold text-slate-800 text-lg">Sayım Tarihçesi</h2>
                    </div>
                    
                    {sayimlar.length > 0 ? (
                        <div className="overflow-x-auto">
                            {/* Masaüstü Tablo, Mobilde Kart Görünümü */}
                            <div className="min-w-[800px] w-full">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                                        <tr>
                                            <th className="px-6 py-4">Sayım No</th>
                                            <th className="px-6 py-4">Açıklama</th>
                                            <th className="px-6 py-4">Durum</th>
                                            <th className="px-6 py-4">Başlangıç</th>
                                            <th className="px-6 py-4 text-right">İşlemler</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {sayimlar.map(s => (
                                            <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                                                <td className="px-6 py-4 font-mono font-bold text-slate-800">{s.sayim_no}</td>
                                                <td className="px-6 py-4 text-slate-600 max-w-xs truncate">{s.aciklama || '—'}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${
                                                        s.durum === 'onaylandı' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 
                                                        s.durum === 'devam_ediyor' ? 'bg-amber-50 text-amber-700 border-amber-200' : 
                                                        'bg-blue-50 text-blue-700 border-blue-200'
                                                    }`}>
                                                        {s.durum === 'devam_ediyor' && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5 animate-pulse"></span>}
                                                        {s.durum.replace('_', ' ').toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-slate-500">
                                                    {new Date(s.baslangic_tarihi).toLocaleDateString('tr-TR', {
                                                        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
                                                    })}
                                                </td>
                                                <td className="px-6 py-4 text-right space-x-3">
                                                    <button
                                                        onClick={() => varyansGor(s.id)}
                                                        className="text-slate-600 hover:text-blue-600 font-semibold text-sm transition-colors"
                                                    >
                                                        Rapor
                                                    </button>
                                                    {(s.durum === 'devam_ediyor' || s.durum === 'bitti') && (
                                                        <button
                                                            onClick={() => setAktifSayim(s)}
                                                            className="text-blue-600 hover:text-blue-800 font-bold text-sm transition-colors"
                                                        >
                                                            {s.durum === 'bitti' ? 'İncele/Onayla' : 'Devam Et'}
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <History className="w-8 h-8 text-slate-400" />
                            </div>
                            <p className="text-slate-500 font-medium">Sistemde kayıtlı sayım bulunamadı.</p>
                        </div>
                    )}
                </div>

                {/* YENİ SAYIM MODAL */}
                <AnimatePresence>
                    {aciklamaModal && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                            <motion.div 
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                                onClick={() => setAciklamaModal(false)}
                            />
                            <motion.div 
                                initial={{ opacity: 0, scale: 0.95, y: 20 }} 
                                animate={{ opacity: 1, scale: 1, y: 0 }} 
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                className="bg-white rounded-2xl shadow-2xl w-full max-w-md relative z-10 overflow-hidden"
                            >
                                <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                                    <h3 className="text-lg font-extrabold text-slate-800">Yeni Sayım Başlat</h3>
                                    <button onClick={() => setAciklamaModal(false)} className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors">
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="p-6">
                                    <label className="block text-sm font-bold text-slate-700 mb-2">Sayım Açıklaması (Opsiyonel)</label>
                                    <input
                                        type="text"
                                        autoFocus
                                        value={aciklama}
                                        onChange={e => setAciklama(e.target.value)}
                                        placeholder="Örn: 2026 1. Çeyrek Sayımı..."
                                        className="w-full border-2 border-slate-200 rounded-xl p-3 sm:p-4 text-base focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all"
                                        onKeyDown={e => e.key === 'Enter' && sayimBaslat()}
                                    />
                                    <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 mt-8">
                                        <button
                                            onClick={() => setAciklamaModal(false)}
                                            className="w-full sm:w-auto px-5 py-3 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition-colors"
                                        >
                                            İptal
                                        </button>
                                        <button
                                            onClick={sayimBaslat}
                                            disabled={loading}
                                            className="w-full sm:w-auto px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 shadow-sm transition-all active:scale-95 flex items-center justify-center"
                                        >
                                            {loading ? 'Başlatılıyor...' : 'Sayımı Başlat'}
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* VARYANS MODAL */}
                <AnimatePresence>
                    {varyansModal && varyansData && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
                            <motion.div 
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
                                onClick={() => setVaryansModal(false)}
                            />
                            <motion.div 
                                initial={{ opacity: 0, scale: 0.95 }} 
                                animate={{ opacity: 1, scale: 1 }} 
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col relative z-10"
                            >
                                <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80 rounded-t-2xl">
                                    <div>
                                        <h3 className="text-xl font-extrabold text-slate-800 flex items-center gap-2">
                                            <FileText className="w-5 h-5 text-blue-600" /> Varyans Raporu
                                        </h3>
                                        <p className="text-sm text-slate-500 mt-1 font-mono">{varyansData.sayim_no}</p>
                                    </div>
                                    <button onClick={() => setVaryansModal(false)} className="text-slate-400 hover:text-slate-700 bg-white shadow-sm p-2 rounded-full border border-slate-200 transition-all hover:scale-105">
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>

                                <div className="p-4 sm:p-6 overflow-y-auto flex-1 bg-slate-50/30">
                                    {/* Özet Kartları */}
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                                        <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col items-center justify-center shadow-sm">
                                            <p className="text-3xl font-black text-slate-800">{varyansData.varyanslar?.length || 0}</p>
                                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mt-2">Sapmalı Ürün</p>
                                        </div>
                                        <div className="bg-white border border-rose-200 rounded-xl p-5 flex flex-col items-center justify-center shadow-sm">
                                            <p className="text-3xl font-black text-rose-600">{varyansData.toplam_sapma}</p>
                                            <p className="text-xs font-bold text-rose-500/80 uppercase tracking-wider mt-2">Toplam Sapma Adedi</p>
                                        </div>
                                        <div className="bg-white border border-blue-200 rounded-xl p-5 flex flex-col items-center justify-center shadow-sm">
                                            <p className="text-3xl font-black text-blue-600">%{varyansData.sapma_orani}</p>
                                            <p className="text-xs font-bold text-blue-500/80 uppercase tracking-wider mt-2">Genel Sapma Oranı</p>
                                        </div>
                                    </div>

                                    {/* Varyans Tablosu */}
                                    {varyansData.varyanslar?.length > 0 ? (
                                        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm text-left whitespace-nowrap">
                                                    <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                                                        <tr>
                                                            <th className="px-4 py-3">Ürün</th>
                                                            <th className="px-4 py-3 text-center">Sistem (Beklenen)</th>
                                                            <th className="px-4 py-3 text-center">Fiziksel (Sayılan)</th>
                                                            <th className="px-4 py-3 text-center">Fark</th>
                                                            <th className="px-4 py-3 text-right">Oran</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-slate-100">
                                                        {varyansData.varyanslar.map((v, i) => (
                                                            <tr key={i} className="hover:bg-slate-50 transition-colors">
                                                                <td className="px-4 py-3 font-semibold text-slate-800">{v.urun_adi}</td>
                                                                <td className="px-4 py-3 text-center text-slate-500">{v.beklenen}</td>
                                                                <td className="px-4 py-3 text-center font-bold text-slate-900 bg-slate-50/50">{v.sayilan}</td>
                                                                <td className="px-4 py-3 text-center">
                                                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md font-bold text-xs ${v.fark > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                                                                        {v.fark > 0 ? `+${v.fark}` : v.fark}
                                                                    </span>
                                                                </td>
                                                                <td className={`px-4 py-3 text-right font-bold ${v.fark > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                                                    {v.yuzde > 0 ? `+${v.yuzde}%` : `${v.yuzde}%`}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-10 flex flex-col items-center justify-center text-emerald-700">
                                            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                                                <CheckCircle2 className="w-10 h-10 text-emerald-600" />
                                            </div>
                                            <p className="text-xl font-extrabold text-center">Kusursuz Sayım!</p>
                                            <p className="text-emerald-600/80 font-medium mt-2 text-center">Sistem verileri ile fiziksel sayım birebir eşleşti.</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}