import React, { useState, useEffect } from 'react';
import { Warehouse, Search, Building } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

export default function DepoKrokiPage() {
    const [depolar, setDepolar] = useState([]);
    const [seciliDepo, setSeciliDepo] = useState(null);
    const [raflar, setRaflar] = useState([]);
    const [paletler, setPaletler] = useState([]); // Depoya ait paletler (doluluk için)
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        setLoading(true);
        // Depoları çek
        api.get('/depolar/')
            .then(res => {
                const aktifDepolar = res.data.filter(d => d.aktif);
                setDepolar(aktifDepolar);
                if (aktifDepolar.length > 0) {
                    setSeciliDepo(aktifDepolar[0]);
                }
            })
            .catch(() => toast.error('Depolar yüklenirken hata oluştu'))
            .finally(() => setLoading(false));
    }, []);

    // Seçili depo değiştiğinde raflarını ve paletlerini çek
    useEffect(() => {
        if (!seciliDepo) return;

        setLoading(true);
        // O depoya ait rafları çek
        api.get(`/raflar/`)
            .then(res => {
                const depoRaflari = res.data.filter(r => r.aktif && r.depo_id === seciliDepo.id);
                setRaflar(depoRaflari);
            })
            .catch(() => toast.error('Raflar yüklenemedi'))
            .finally(() => setLoading(false));

        // Doluluk durumu için o depodaki paletleri çek. 
        // /paletler/ endpoint'i aktif olanları getiriyor. raf_id üzerinden bağlayacağız.
        api.get('/paletler/')
            .then(res => {
                const aktifPaletler = res.data.filter(p => p.aktif);
                setPaletler(aktifPaletler);
            })
            .catch(err => console.error("Paletler çekilemedi:", err));

    }, [seciliDepo]);

    // Rafları bölgelere (koridorlara vb.) göre grupla
    const getRafGroups = () => {
        const gruplu = {};
        const filtrelenmisRaflar = raflar.filter(r =>
            r.kod.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (r.bolge && r.bolge.toLowerCase().includes(searchQuery.toLowerCase()))
        );

        filtrelenmisRaflar.forEach(raf => {
            const bolge = raf.bolge || "Bölge Belirtilmemiş";
            if (!gruplu[bolge]) gruplu[bolge] = [];
            gruplu[bolge].push(raf);
        });

        // Bölge ismine göre sırala
        return Object.keys(gruplu).sort().reduce((obj, key) => {
            // Rafları kendi içinde koda göre sırala
            obj[key] = gruplu[key].sort((a, b) => a.kod.localeCompare(b.kod));
            return obj;
        }, {});
    };

    // Rafın doluluk oranını hesaplama (Mevcut palet sayısı / Raf kapasitesi)
    const getRafDurum = (rafId, kapasite) => {
        const rafPaletleri = paletler.filter(p => p.raf_id === rafId);
        const mevcutPaletSayisi = rafPaletleri.length;
        const cap = kapasite || 100; // Default 100 eğer girilmemişse
        const oran = mevcutPaletSayisi / cap;

        let renkClass = "bg-emerald-100 border-emerald-300 text-emerald-800"; // Boş / Çok yer var
        let durumText = "Kapasite Var";

        if (oran >= 1) {
            renkClass = "bg-rose-100 border-rose-300 text-rose-800"; // Tamamen dolu
            durumText = "Dolu";
        } else if (oran >= 0.7) {
            renkClass = "bg-amber-100 border-amber-300 text-amber-800"; // Yarı dolu / kritik
            durumText = "Dolmak Üzere";
        }

        return {
            mevcut: mevcutPaletSayisi,
            kapasite: cap,
            oran,
            renkClass,
            durumText,
            paletler: rafPaletleri
        };
    };

    const groupedRaflar = getRafGroups();

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6">
            {/* Header & Depo Seçimi */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-violet-100 border border-violet-200 flex items-center justify-center">
                        <Warehouse className="w-5 h-5 text-violet-600" />
                    </div>
                    <div>
                        <h2 className="text-[17px] font-extrabold text-slate-800">Depo Krokisi</h2>
                        <p className="text-[12px] font-medium text-slate-500">Rafların doluluk durumunu görsel olarak inceleyin</p>
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    {/* Arama */}
                    <div className="relative">
                        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                        <input
                            type="text"
                            placeholder="Raf Kodu veya Bölge Ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full sm:w-64 h-10 pl-10 pr-4 text-[13px] rounded-xl border border-slate-200 bg-white
                            focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 outline-none transition-all"
                        />
                    </div>
                    {/* Depo Seçici */}
                    <div className="relative">
                        <Building className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <select
                            value={seciliDepo?.id || ''}
                            onChange={(e) => {
                                const depo = depolar.find(d => d.id === parseInt(e.target.value));
                                setSeciliDepo(depo);
                            }}
                            className="w-full sm:w-48 h-10 pl-10 pr-8 text-[13px] font-medium text-slate-700 bg-white border border-slate-200 rounded-xl appearance-none focus:outline-none focus:ring-2 focus:ring-violet-500/20 cursor-pointer"
                        >
                            {depolar.map(d => (
                                <option key={d.id} value={d.id}>{d.isim}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Kroki Gösterimi */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 min-h-[500px]">
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div>
                    </div>
                ) : raflar.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-center">
                        <Warehouse className="w-12 h-12 text-slate-300 mb-3" />
                        <p className="text-[14px] font-bold text-slate-600">Bu depoya ait raf bulunamadı</p>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Lejant (Bilgi Kartnaması) */}
                        <div className="flex flex-wrap items-center gap-4 bg-white p-3 rounded-lg border border-slate-100 shadow-sm w-fit">
                            <span className="text-[12px] font-bold text-slate-500 mr-2">Doluluk Göstergesi:</span>
                            <div className="flex items-center gap-1.5 cursor-help" title="Müsait Yer Var (0% - 69%)">
                                <span className="w-3 h-3 rounded-sm bg-emerald-100 border border-emerald-300"></span>
                                <span className="text-[12px] font-medium text-slate-600">Müsait</span>
                            </div>
                            <div className="flex items-center gap-1.5 cursor-help" title="Kapasite Kritik (70% - 99%)">
                                <span className="w-3 h-3 rounded-sm bg-amber-100 border border-amber-300"></span>
                                <span className="text-[12px] font-medium text-slate-600">Kritik</span>
                            </div>
                            <div className="flex items-center gap-1.5 cursor-help" title="Tamamen Dolu (100%)">
                                <span className="w-3 h-3 rounded-sm bg-rose-100 border border-rose-300"></span>
                                <span className="text-[12px] font-medium text-slate-600">Dolu</span>
                            </div>
                        </div>

                        {/* Bölgeler */}
                        {Object.entries(groupedRaflar).map(([bolge, bolgeRaflari]) => (
                            <div key={bolge} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                                <div className="bg-slate-100/50 px-4 py-2.5 border-b border-slate-200">
                                    <h3 className="text-[14px] font-extrabold text-slate-700">{bolge}</h3>
                                </div>
                                <div className="p-4 sm:p-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3 sm:gap-4">
                                    {bolgeRaflari.map(raf => {
                                        const durum = getRafDurum(raf.id, raf.kapasite);
                                        return (
                                            <div
                                                key={raf.id}
                                                title={`Mevcut: ${durum.mevcut} | Kapasite: ${durum.kapasite}`}
                                                className={`group relative h-20 sm:h-24 rounded-lg flex flex-col items-center justify-center border-2 transition-all hover:-translate-y-1 hover:shadow-md cursor-pointer ${durum.renkClass}`}
                                            >
                                                <span className="text-[15px] sm:text-[16px] font-extrabold tracking-tight">{raf.kod}</span>
                                                <span className="text-[10px] sm:text-[11px] font-semibold opacity-90 mt-1">
                                                    {durum.mevcut} / {durum.kapasite}
                                                </span>

                                                {/* Tooltip (Hover olduğunda palet detayları vb gösterilebilir - Daha sonra modal'a da çevrilebilir) */}
                                                <div className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-2 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[11px] p-2 rounded shadow-xl whitespace-nowrap z-10 transition-opacity pointer-events-none">
                                                    Palet Sayısı: {durum.mevcut} <br />
                                                    Durum: {durum.durumText}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
