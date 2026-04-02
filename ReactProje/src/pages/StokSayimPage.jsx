import { useState, useEffect, useRef, useCallback } from 'react';
import { useAsync } from '../hooks/useAsync';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function StokSayimPage() {
    const [sayimlar, setSayimlar] = useState([]);
    const [aktifSayim, setAktifSayim] = useState(null);
    const [varyansData, setVaryansData] = useState(null);
    const [varyansModal, setVaryansModal] = useState(false);
    const [aciklama, setAciklama] = useState('');
    const [aciklamaModal, setAciklamaModal] = useState(false);
    const barkodRef = useRef(null);

    const { loading, run } = useAsync();

    // Sayımları yükle
    const yukle = useCallback(async () => {
        await run(async () => {
            const res = await api.get('/stok-sayimlar');
            setSayimlar(res.data);
            // Aktif sayım varsa seç
            const devam = res.data.find(s => s.durum === 'devam_ediyor');
            if (devam) setAktifSayim(devam);
        });
    }, [run]);

    useEffect(() => { void yukle(); }, [yukle]);

    // Aktif sayım değişince barkod input'una odaklan
    useEffect(() => {
        if (aktifSayim && barkodRef.current) {
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
        if (!aktifSayim) return;
        const urunId = parseInt(barkodDegeri);
        if (!urunId || isNaN(urunId)) {
            toast.error('Geçersiz barkod değeri');
            return;
        }
        await run(async () => {
            const res = await api.post(`/stok-sayimlar/${aktifSayim.id}/kalemler`, {
                urun_id: urunId,
                sayilan_miktar: 1,
                notlar: ''
            });
            // Kalem listesini güncelle (upsert mantığı)
            setAktifSayim(prev => {
                const mevcutKalemler = prev.sayim_kalemleri.filter(k => k.urun_id !== res.data.urun_id);
                return { ...prev, sayim_kalemleri: [res.data, ...mevcutKalemler] };
            });
            toast.success(`Ürün kaydedildi: ${res.data.urun_adi || `#${urunId}`}`);
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

    // Sayımı onayla / kapat
    const sayimiKapat = async () => {
        if (!aktifSayim) return;
        if (!window.confirm(`"${aktifSayim.sayim_no}" sayımını onaylamak istediğinize emin misiniz?`)) return;
        await run(async () => {
            await api.post(`/stok-sayimlar/${aktifSayim.id}/onayla`);
            toast.success('Sayım onaylandı ve kapatıldı');
            setAktifSayim(null);
            yukle();
        });
    };

    const durumRenk = (durum) => {
        if (durum === 'onaylandı') return 'bg-emerald-100 text-emerald-800';
        if (durum === 'devam_ediyor') return 'bg-amber-100 text-amber-800';
        return 'bg-slate-100 text-slate-700';
    };

    return (
        <div className="p-6 max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Stok Sayımı (Inventar)</h1>
                    <p className="text-sm text-gray-500 mt-1">Periyodik stok sayımı ve varyans raporlaması</p>
                </div>
                <button
                    onClick={() => setAciklamaModal(true)}
                    disabled={!!aktifSayim || loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold"
                >
                    + Yeni Sayım Başlat
                </button>
            </div>

            {/* AKTİF SAYIM PANELİ */}
            {aktifSayim && (
                <div className="bg-amber-50 border border-amber-300 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="text-lg font-bold text-amber-900">{aktifSayim.sayim_no}</h2>
                            <p className="text-sm text-amber-700">{aktifSayim.aciklama || 'Açıklama yok'}</p>
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => varyansGor(aktifSayim.id)}
                                disabled={loading}
                                className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700"
                            >
                                Varyans Gör
                            </button>
                            <button
                                onClick={sayimiKapat}
                                disabled={loading}
                                className="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-emerald-700"
                            >
                                Sayımı Onayla
                            </button>
                        </div>
                    </div>

                    {/* BARKOD GİRİŞİ */}
                    <div className="mb-4">
                        <label className="block text-sm font-semibold text-amber-800 mb-1">
                            Barkod Tara / Ürün ID Gir
                        </label>
                        <input
                            ref={barkodRef}
                            type="number"
                            placeholder="Ürün ID veya barkod okutun, Enter'a basın..."
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && e.target.value.trim()) {
                                    urunKaydet(e.target.value.trim());
                                    e.target.value = '';
                                }
                            }}
                            className="border border-amber-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white text-base"
                        />
                    </div>

                    {/* SAYILAN ÜRÜNLER */}
                    <div className="bg-white rounded-lg border border-amber-200 overflow-hidden">
                        <div className="px-4 py-2 bg-amber-100 text-sm font-semibold text-amber-800">
                            Sayılan Ürünler ({aktifSayim.sayim_kalemleri?.length || 0})
                        </div>
                        {aktifSayim.sayim_kalemleri?.length > 0 ? (
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-gray-50 text-left">
                                        <th className="px-4 py-2 font-semibold text-gray-600">Ürün</th>
                                        <th className="px-4 py-2 font-semibold text-gray-600 text-center">Sayılan Miktar</th>
                                        <th className="px-4 py-2 font-semibold text-gray-600">Notlar</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {aktifSayim.sayim_kalemleri.map(k => (
                                        <tr key={k.id} className="border-t hover:bg-gray-50">
                                            <td className="px-4 py-2">
                                                <span className="font-medium">{k.urun_adi || `Ürün #${k.urun_id}`}</span>
                                            </td>
                                            <td className="px-4 py-2 text-center font-bold text-blue-700">{k.sayilan_miktar}</td>
                                            <td className="px-4 py-2 text-gray-500 text-xs">{k.notlar || '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p className="text-center text-gray-400 py-6 text-sm">Henüz ürün taranmadı</p>
                        )}
                    </div>
                </div>
            )}

            {/* SAYIM TARİHÇESİ */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100">
                    <h2 className="font-bold text-gray-800">Sayım Tarihçesi</h2>
                </div>
                {sayimlar.length > 0 ? (
                    <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left font-semibold text-gray-600">Sayım No</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-600">Açıklama</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-600">Durum</th>
                                <th className="px-4 py-3 text-left font-semibold text-gray-600">Başlangıç</th>
                                <th className="px-4 py-3 text-center font-semibold text-gray-600">İşlem</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sayimlar.map(s => (
                                <tr key={s.id} className="border-t hover:bg-gray-50">
                                    <td className="px-4 py-3 font-mono font-semibold text-gray-800">{s.sayim_no}</td>
                                    <td className="px-4 py-3 text-gray-600">{s.aciklama || '—'}</td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${durumRenk(s.durum)}`}>
                                            {s.durum}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-gray-500">
                                        {new Date(s.baslangic_tarihi).toLocaleDateString('tr-TR', {
                                            day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
                                        })}
                                    </td>
                                    <td className="px-4 py-3 text-center space-x-2">
                                        <button
                                            onClick={() => varyansGor(s.id)}
                                            className="text-blue-600 hover:text-blue-800 text-xs font-semibold hover:underline"
                                        >
                                            Varyans
                                        </button>
                                        {s.durum === 'devam_ediyor' && (
                                            <button
                                                onClick={() => setAktifSayim(s)}
                                                className="text-amber-600 hover:text-amber-800 text-xs font-semibold hover:underline"
                                            >
                                                Devam Et
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p className="text-center text-gray-400 py-10">Henüz sayım yapılmadı</p>
                )}
            </div>

            {/* AÇIKLAMA MODAL */}
            {aciklamaModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
                        <h3 className="text-lg font-bold mb-4">Yeni Sayım Başlat</h3>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama (opsiyonel)</label>
                        <input
                            type="text"
                            value={aciklama}
                            onChange={e => setAciklama(e.target.value)}
                            placeholder="Örn: Aylık sayım, Çeyrek sonu..."
                            className="border rounded-lg p-2.5 w-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 mb-4"
                            onKeyDown={e => e.key === 'Enter' && sayimBaslat()}
                        />
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setAciklamaModal(false)}
                                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                            >
                                İptal
                            </button>
                            <button
                                onClick={sayimBaslat}
                                disabled={loading}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
                            >
                                {loading ? 'Başlatılıyor...' : 'Sayımı Başlat'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* VARYANS MODAL */}
            {varyansModal && varyansData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
                        <div className="p-6 border-b flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-bold">Varyans Raporu</h3>
                                <p className="text-sm text-gray-500">{varyansData.sayim_no}</p>
                            </div>
                            <button
                                onClick={() => setVaryansModal(false)}
                                className="text-gray-400 hover:text-gray-700 text-2xl leading-none"
                            >
                                &times;
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto flex-1">
                            {/* Özet */}
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="bg-slate-50 rounded-lg p-4 text-center">
                                    <p className="text-2xl font-bold text-slate-800">{varyansData.varyanslar?.length || 0}</p>
                                    <p className="text-xs text-slate-500 mt-1">Sapmalı Ürün</p>
                                </div>
                                <div className="bg-red-50 rounded-lg p-4 text-center">
                                    <p className="text-2xl font-bold text-red-700">{varyansData.toplam_sapma}</p>
                                    <p className="text-xs text-red-500 mt-1">Toplam Sapma (koli)</p>
                                </div>
                                <div className="bg-blue-50 rounded-lg p-4 text-center">
                                    <p className="text-2xl font-bold text-blue-700">%{varyansData.sapma_orani}</p>
                                    <p className="text-xs text-blue-500 mt-1">Sapma Oranı</p>
                                </div>
                            </div>

                            {varyansData.varyanslar?.length > 0 ? (
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-3 py-2 text-left font-semibold text-gray-600">Ürün</th>
                                            <th className="px-3 py-2 text-center font-semibold text-gray-600">Beklenen</th>
                                            <th className="px-3 py-2 text-center font-semibold text-gray-600">Sayılan</th>
                                            <th className="px-3 py-2 text-center font-semibold text-gray-600">Fark</th>
                                            <th className="px-3 py-2 text-center font-semibold text-gray-600">%</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {varyansData.varyanslar.map((v, i) => (
                                            <tr key={i} className="border-t hover:bg-gray-50">
                                                <td className="px-3 py-2 font-medium">{v.urun_adi}</td>
                                                <td className="px-3 py-2 text-center text-gray-600">{v.beklenen}</td>
                                                <td className="px-3 py-2 text-center text-gray-800 font-semibold">{v.sayilan}</td>
                                                <td className={`px-3 py-2 text-center font-bold ${v.fark > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {v.fark > 0 ? `+${v.fark}` : v.fark}
                                                </td>
                                                <td className={`px-3 py-2 text-center text-xs font-semibold ${v.fark > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {v.yuzde > 0 ? `+${v.yuzde}%` : `${v.yuzde}%`}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="text-center py-8 text-gray-400">
                                    <p className="text-4xl mb-2">✓</p>
                                    <p className="font-semibold">Sapma yok — stok tamamen eşleşti!</p>
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t flex justify-end">
                            <button
                                onClick={() => setVaryansModal(false)}
                                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-semibold"
                            >
                                Kapat
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
