import React, { useState, useEffect, useMemo } from 'react';
import { Warehouse, Search, Building, LayoutGrid, AlertCircle, AlertTriangle, CheckCircle2, ChevronRight, QrCode, Package, X, Printer, Info, Calendar, Clock, Tag, AlignLeft, Hash, ChevronDown, ChevronUp, Scale } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { QRCodeSVG } from 'qrcode.react';

export default function DepoKrokiPage() {
    const [depolar, setDepolar] = useState([]);
    const [seciliDepo, setSeciliDepo] = useState(null);
    const [raflar, setRaflar] = useState([]);
    const [paletler, setPaletler] = useState([]); // Depoya ait paletler (doluluk için)
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // YENİ: Modal State
    const [seciliRafDetay, setSeciliRafDetay] = useState(null);
    const [seciliPaletDetay, setSeciliPaletDetay] = useState(null);

    // Modal kapandığında palet detayını da sıfırla
    useEffect(() => {
        if (!seciliRafDetay) {
            setSeciliPaletDetay(null);
        }
    }, [seciliRafDetay]);

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
        const yuzde = Math.min(Math.round(oran * 100), 100);

        let bgKutusu = "bg-emerald-50";
        let textRenk = "text-emerald-700";
        let barClass = "bg-emerald-500";
        let icon = <CheckCircle2 className="w-5 h-5 text-emerald-600" />;
        let durumText = "Müsait";

        if (oran >= 1) {
            bgKutusu = "bg-rose-50";
            textRenk = "text-rose-700";
            barClass = "bg-rose-500";
            icon = <AlertCircle className="w-5 h-5 text-rose-600" />;
            durumText = "Dolu";
        } else if (oran >= 0.7) {
            bgKutusu = "bg-amber-50";
            textRenk = "text-amber-700";
            barClass = "bg-amber-500";
            icon = <AlertTriangle className="w-5 h-5 text-amber-600" />;
            durumText = "Kritik";
        }

        return {
            mevcut: mevcutPaletSayisi,
            kapasite: cap,
            yuzde,
            bgKutusu,
            textRenk,
            barClass,
            icon,
            durumText,
            paletler: rafPaletleri
        };
    };

    // QR Kod Yazdırma Fonksiyonu
    const handlePrintQR = () => {
        if (!seciliRafDetay) return;

        const printWindow = window.open('', '_blank', 'width=600,height=600');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Raf Barkod - ${seciliRafDetay.raf.kod}</title>
                    <style>
                        body { 
                            display: flex; 
                            flex-direction: column; 
                            align-items: center; 
                            justify-content: center; 
                            height: 100vh; 
                            margin: 0; 
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background-color: white;
                        }
                        .print-container { 
                            text-align: center;
                            padding: 40px;
                            border: 3px dashed #cbd5e1;
                            border-radius: 20px;
                        }
                        h1 { 
                            font-size: 48px; 
                            color: #1e293b; 
                            margin-bottom: 30px; 
                            margin-top: 0;
                            letter-spacing: -1px;
                        }
                        .qr-wrapper {
                            padding: 20px;
                            background: white;
                        }
                        p { 
                            font-size: 16px; 
                            color: #64748b; 
                            margin-top: 30px; 
                            font-weight: 500;
                        }
                    </style>
                </head>
                <body>
                    <div class="print-container">
                        <h1>${seciliRafDetay.raf.kod}</h1>
                        <div class="qr-wrapper">
                            ${document.getElementById('qr-svg-container').innerHTML}
                        </div>
                        <p>DYS - Otomatik Depo Sistemi</p>
                    </div>
                </body>
                <script>
                    window.onload = () => {
                        window.print();
                        setTimeout(() => window.close(), 500);
                    }
                </script>
            </html>
        `);
        printWindow.document.close();
    };

    const groupedRaflar = getRafGroups();

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6 pb-24 relative">
            {/* Header & Göstergeler Kombini */}
            <div className="flex flex-col gap-6">

                {/* Üst Başlık ve Filtreler */}
                <div className="flex flex-col sm:flex-row gap-5 items-start sm:items-center justify-between bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-violet-100 border border-violet-200 flex items-center justify-center shrink-0">
                            <Warehouse className="w-6 h-6 text-violet-600" />
                        </div>
                        <div>
                            <h2 className="text-[18px] sm:text-[20px] font-extrabold text-slate-800">Depo Krokisi</h2>
                            <p className="text-[13px] font-medium text-slate-500 mt-0.5">Rafların doluluk durumunu detaylı inceleyin</p>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                        {/* Arama */}
                        <div className="relative w-full sm:w-64">
                            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                placeholder="Raf Kodu veya Bölge Ara..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full h-11 pl-10 pr-4 text-[13px] rounded-xl border border-slate-200 bg-slate-50
                                focus:bg-white focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 outline-none transition-all placeholder:text-slate-400 font-medium"
                            />
                        </div>
                        {/* Depo Seçici */}
                        <div className="relative w-full sm:w-56">
                            <Building className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                            <select
                                value={seciliDepo?.id || ''}
                                onChange={(e) => {
                                    const depo = depolar.find(d => d.id === parseInt(e.target.value));
                                    setSeciliDepo(depo);
                                }}
                                className="w-full h-11 pl-10 pr-8 text-[13px] font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl appearance-none focus:outline-none focus:bg-white focus:ring-2 focus:ring-violet-500/20 cursor-pointer transition-all"
                            >
                                {depolar.map(d => (
                                    <option key={d.id} value={d.id}>{d.isim}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Ayraç ve Lejant */}
                <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm w-full">
                    <div className="flex items-center gap-2 mr-2">
                        <LayoutGrid className="w-5 h-5 text-slate-400" />
                        <span className="text-[14px] font-bold text-slate-700">Durum Göstergeleri:</span>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-100/80 px-3.5 py-1.5 rounded-lg shadow-sm">
                            <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm"></div>
                            <span className="text-[13px] font-bold text-emerald-700">Müsait %0-69</span>
                        </div>
                        <div className="flex items-center gap-2 bg-amber-50 border border-amber-100/80 px-3.5 py-1.5 rounded-lg shadow-sm">
                            <div className="w-3 h-3 rounded-full bg-amber-500 shadow-sm"></div>
                            <span className="text-[13px] font-bold text-amber-700">Kritik %70-99</span>
                        </div>
                        <div className="flex items-center gap-2 bg-rose-50 border border-rose-100/80 px-3.5 py-1.5 rounded-lg shadow-sm">
                            <div className="w-3 h-3 rounded-full bg-rose-500 shadow-sm"></div>
                            <span className="text-[13px] font-bold text-rose-700">Dolu %100</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Kroki Gösterimi */}
            <div className="min-h-[500px]">
                {loading ? (
                    <div className="flex flex-col justify-center items-center h-64 space-y-4">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-violet-600"></div>
                        <span className="text-slate-500 font-medium text-[14px]">Depo yükleniyor...</span>
                    </div>
                ) : raflar.length === 0 ? (
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col items-center justify-center p-12 text-center h-80">
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4 border border-slate-100">
                            <Warehouse className="w-10 h-10 text-slate-300" />
                        </div>
                        <h3 className="text-[18px] font-extrabold text-slate-700 mb-1">Raf Bulunamadı</h3>
                        <p className="text-[14px] font-medium text-slate-500 max-w-sm">Bu depoya ait raf bulunmuyor veya aramanızla eşleşen sonuç yok.</p>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Bölgeler */}
                        {Object.entries(groupedRaflar).map(([bolge, bolgeRaflari]) => (
                            <div key={bolge} className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                                {/* Bölge Başlığı */}
                                <div className="bg-slate-50/80 px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-6 bg-violet-500 rounded-full"></div>
                                        <h3 className="text-[16px] font-extrabold text-slate-800">{bolge}</h3>
                                        <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-[12px] font-bold text-slate-500 shadow-sm">
                                            {bolgeRaflari.length} Raf
                                        </span>
                                    </div>
                                </div>

                                {/* Raf Izgarası */}
                                <div className="p-5 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-4 sm:gap-5">
                                    {bolgeRaflari.map(raf => {
                                        const durum = getRafDurum(raf.id, raf.kapasite);
                                        return (
                                            <div
                                                key={raf.id}
                                                onClick={() => setSeciliRafDetay({ raf, durum })}
                                                className="relative flex flex-col justify-between p-4 rounded-2xl border border-slate-200 bg-white transition-all duration-300 hover:shadow-xl hover:border-violet-300 hover:-translate-y-1.5 group cursor-pointer"
                                            >
                                                {/* Üst Kısım: Kod ve İkon */}
                                                <div className="flex justify-between items-start mb-4">
                                                    <div>
                                                        <span className="text-[10px] sm:text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-1">RAF KODU</span>
                                                        <span className="text-[17px] sm:text-[19px] font-black text-slate-800 leading-none">{raf.kod}</span>
                                                    </div>
                                                    <div className={`p-1.5 rounded-lg border border-white/50 shadow-sm ${durum.bgKutusu} group-hover:hidden`}>
                                                        {durum.icon}
                                                    </div>
                                                    {/* Hoverda QR veya Qr İkonu göster (Kullanıcıya tıklanabilirlik hissi vermek için) */}
                                                    <div className={`hidden group-hover:flex p-1.5 rounded-lg border border-violet-200 bg-violet-50 text-violet-600 shadow-sm`}>
                                                        <QrCode className="w-5 h-5" />
                                                    </div>
                                                </div>

                                                {/* Orta Kısım: Sayılar */}
                                                <div className="flex items-end justify-between mb-3 border-t border-slate-100 pt-3">
                                                    <div className="flex flex-col">
                                                        <span className="text-[12px] font-semibold text-slate-500 mb-0.5">Doluluk</span>
                                                        <div className="flex items-baseline gap-1">
                                                            <span className="text-[18px] font-extrabold text-slate-800 leading-none">{durum.mevcut}</span>
                                                            <span className="text-slate-400 text-[13px] font-bold">/ {durum.kapasite}</span>
                                                        </div>
                                                    </div>
                                                    <span className={`text-[15px] font-black ${durum.textRenk}`}>
                                                        %{durum.yuzde}
                                                    </span>
                                                </div>

                                                {/* Alt Kısım: Progress Bar */}
                                                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden shadow-inner">
                                                    <div
                                                        className={`h-full rounded-full transition-all duration-1000 ease-out ${durum.barClass} relative`}
                                                        style={{ width: `${durum.yuzde}%` }}
                                                    >
                                                        {/* Parlama efekti */}
                                                        {durum.yuzde > 0 && (
                                                            <div className="absolute inset-0 bg-white/20 w-full h-full"></div>
                                                        )}
                                                    </div>
                                                </div>

                                                {/* Hover Glow Efekti */}
                                                <div className="absolute inset-0 rounded-2xl ring-2 ring-violet-500/0 group-hover:ring-violet-500/20 pointer-events-none transition-all duration-300"></div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Raf Detay ve QR Modal */}
            {seciliRafDetay && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
                    <div
                        className="bg-white rounded-3xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-100 shrink-0">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
                                    <Warehouse className="w-5 h-5 text-violet-600" />
                                </div>
                                <div>
                                    <h3 className="text-[16px] font-extrabold text-slate-800">Raf Detayları</h3>
                                    <p className="text-[12px] font-medium text-slate-500">Kapasite ve İçerik</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSeciliRafDetay(null)}
                                className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Modal Body - Scrollable */}
                        <div className="overflow-y-auto p-4 sm:p-6 custom-scrollbar flex-1">
                            <div className="flex flex-col items-center">
                                {/* Hızlı İstatistikler */}
                                <div className="w-full flex items-center gap-3 mb-6">
                                    <div className="flex-1 bg-slate-50 border border-slate-100 rounded-2xl p-3 flex flex-col items-center gap-1.5">
                                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">RAF KODU</span>
                                        <span className="text-[20px] font-black text-slate-800 leading-none">{seciliRafDetay.raf.kod}</span>
                                    </div>
                                    <div className="flex-1 bg-slate-50 border border-slate-100 rounded-2xl p-3 flex flex-col items-center gap-1.5">
                                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">DOLULUK</span>
                                        <span className={`text-[18px] font-black ${seciliRafDetay.durum.textRenk} leading-none`}>
                                            %{seciliRafDetay.durum.yuzde}
                                        </span>
                                    </div>
                                </div>

                                {/* Alt Açılır Kısım / Ekstra Görsel - İsteğe Bağlı */}
                                <div className="bg-white p-3 rounded-2xl border border-slate-100 shadow-sm relative group mb-6 flex justify-between items-center w-full">
                                    <div className="flex items-center gap-3">
                                        <div id="qr-svg-container" className="shrink-0">
                                            <QRCodeSVG
                                                value={`http://dys-app.com/raf/${seciliRafDetay.raf.kod}`}
                                                size={60}
                                                bgColor={"#ffffff"}
                                                fgColor={"#1e293b"}
                                                level={"L"}
                                            />
                                        </div>
                                        <div>
                                            <div className="text-[13px] font-bold text-slate-800">Raf QR Kodu</div>
                                            <div className="text-[11px] text-slate-500">Fiziksel raf tespiti için</div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handlePrintQR}
                                        title="QR Kodu Yazdır"
                                        className="p-2 bg-slate-100 text-slate-600 hover:bg-violet-100 hover:text-violet-600 rounded-xl transition-colors"
                                    >
                                        <Printer className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Kapasite Barı */}
                                <div className="w-full mb-6">
                                    <div className="flex justify-between items-end mb-2">
                                        <div className="flex items-center gap-1.5 text-slate-600">
                                            <Package className="w-4 h-4" />
                                            <span className="text-[13px] font-bold">Mevcut Palet</span>
                                        </div>
                                        <div className="text-[14px] font-black text-slate-800">
                                            {seciliRafDetay.durum.mevcut} <span className="text-slate-400 font-bold text-[12px]">/ {seciliRafDetay.durum.kapasite}</span>
                                        </div>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all duration-1000 ease-out ${seciliRafDetay.durum.barClass}`}
                                            style={{ width: `${seciliRafDetay.durum.yuzde}%` }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Raftaki Paletler Listesi (YENİ) */}
                                <div className="w-full">
                                    <h5 className="text-[14px] font-bold text-slate-800 mb-3 flex items-center gap-2 border-b border-slate-100 pb-2">
                                        <LayoutGrid className="w-4 h-4 text-violet-500" />
                                        Raftaki Paletler ({seciliRafDetay.durum.paletler.length})
                                    </h5>

                                    <div className="space-y-2.5">
                                        {seciliRafDetay.durum.paletler.length > 0 ? (
                                            seciliRafDetay.durum.paletler.map(palet => {
                                                const isExpanded = seciliPaletDetay?.id === palet.id;

                                                return (
                                                    <div
                                                        key={palet.id}
                                                        className={`bg-white border ${isExpanded ? 'border-violet-400 ring-2 ring-violet-400/20' : 'border-slate-200'} rounded-2xl shadow-sm hover:border-violet-300 transition-all overflow-hidden flex flex-col`}
                                                    >
                                                        {/* Palet Üst Kısım (Tıklanabilir) */}
                                                        <div
                                                            onClick={() => setSeciliPaletDetay(isExpanded ? null : palet)}
                                                            className="p-3.5 flex items-start sm:items-center justify-between cursor-pointer w-full flex-col sm:flex-row gap-3"
                                                        >
                                                            <div className="flex flex-col gap-1 w-full sm:w-auto">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[14px] font-black text-slate-800">{palet.palet_no}</span>
                                                                    <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider border border-slate-200">
                                                                        Lot: {palet.lot?.lot_no || 'Yok'}
                                                                    </span>
                                                                </div>
                                                                <div className="text-[12px] font-medium text-slate-500 flex items-center gap-1.5 line-clamp-1 w-full max-w-full">
                                                                    <span className="truncate">
                                                                        {palet.lot?.urun?.isim || palet.lot?.urun_id ? `Ürün: ${palet.lot?.urun?.isim || palet.lot?.urun_id}` : 'Ürün bilgisi yok'}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center justify-between sm:justify-end w-full sm:w-auto gap-3">
                                                                <span className="text-[14px] font-black text-violet-700 bg-violet-50 px-2.5 py-1 rounded-lg">
                                                                    {palet.koli_adedi} Koli
                                                                </span>
                                                                <div className={`p-1 rounded-lg transition-colors ${isExpanded ? 'bg-violet-100 text-violet-600' : 'bg-slate-50 text-slate-400'}`}>
                                                                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Açılır Kısım: Palet Detayları */}
                                                        {isExpanded && (
                                                            <div className="p-4 sm:p-5 bg-slate-50/50 border-t border-slate-100 grid grid-cols-2 gap-y-4 gap-x-2 animate-in slide-in-from-top-2 duration-200">
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Tag className="w-3.5 h-3.5" /> BARKOD / SKU</span>
                                                                    <span className="text-[13px] font-bold text-slate-800">{palet.lot?.urun?.barkod || '-'}</span>
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Scale className="w-3.5 h-3.5" /> NET AĞIRLIK</span>
                                                                    <span className="text-[13px] font-bold text-slate-800">{palet.palet_kg ? `${palet.palet_kg} kg` : '-'}</span>
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> ÜRETİM T.</span>
                                                                    <span className="text-[13px] font-bold text-slate-800">{palet.lot?.uretim_tarihi || '-'}</span>
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5" /> SKT</span>
                                                                    {(() => {
                                                                        const bitisText = palet.lot?.son_kullanma_tarihi;
                                                                        if (!bitisText) return <span className="text-[13px] font-bold text-slate-800">-</span>;

                                                                        let renk = "text-slate-800";
                                                                        const bugun = new Date();
                                                                        const skt = new Date(bitisText);
                                                                        const fark = Math.ceil((skt - bugun) / (1000 * 60 * 60 * 24));
                                                                        if (fark < 0) renk = "text-rose-600";
                                                                        else if (fark < 30) renk = "text-amber-600";

                                                                        return <span className={`text-[13px] font-bold ${renk}`}>{bitisText}</span>;
                                                                    })()}
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> VARDİYA</span>
                                                                    <span className="text-[13px] font-bold text-slate-800">{palet.vardiya || '-'}</span>
                                                                </div>
                                                                <div className="flex flex-col gap-1">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Hash className="w-3.5 h-3.5" /> SİSTEME GİRİŞ</span>
                                                                    <span className="text-[13px] font-bold text-slate-800">{palet.olusturma_tarihi ? new Date(palet.olusturma_tarihi).toLocaleDateString("tr-TR") : '-'}</span>
                                                                </div>
                                                                <div className="col-span-2 flex flex-col gap-1 mt-1 pt-3 border-t border-slate-200/50">
                                                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><AlignLeft className="w-3.5 h-3.5" /> AÇIKLAMA</span>
                                                                    <span className="text-[13px] font-medium text-slate-600 whitespace-pre-wrap">{palet.lot?.aciklama || 'Açıklama bulunmuyor.'}</span>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
                                                <Package className="w-8 h-8 text-slate-300 mb-2" />
                                                <span className="text-[13px] font-bold text-slate-600">Bu rafta palet bulunmuyor.</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="p-4 sm:p-5 border-t border-slate-100 bg-slate-50 shrink-0">
                            <button
                                onClick={() => setSeciliRafDetay(null)}
                                className="w-full py-3 px-4 rounded-xl bg-slate-800 text-white font-bold hover:bg-slate-900 transition-colors text-[14px] shadow-md"
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
