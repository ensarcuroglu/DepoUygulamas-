import React, { useState, useEffect, useMemo, memo } from 'react';
import { Warehouse, Search, Building, LayoutGrid, AlertCircle, AlertTriangle, CheckCircle2, QrCode, Package, X, Printer, Calendar, Clock, Tag, AlignLeft, Hash, ChevronDown, ChevronUp, Scale } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { QRCodeSVG } from 'qrcode.react';
import { useDebounce } from 'use-debounce';
import { motion, AnimatePresence } from 'framer-motion';

// --- ALT COMPONENT: Optimize edilmiş Raf Kartı ---
const RafCard = memo(({ raf, durum, onSelect }) => {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            whileHover={{ y: -4, boxShadow: '0 10px 25px -5px rgba(139, 92, 246, 0.15)' }}
            onClick={() => onSelect({ raf, durum })}
            className="relative flex flex-col justify-between p-4 rounded-2xl border border-slate-200 bg-white transition-all duration-200 cursor-pointer group"
        >
            <div className="flex justify-between items-start mb-4">
                <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">RAF KODU</span>
                    <span className="text-[17px] font-black text-slate-800 leading-none">{raf.kod}</span>
                </div>
                <div className={`p-1.5 rounded-xl border ${durum.bgKutusu} ${durum.borderRenk} group-hover:hidden transition-colors`}>
                    {durum.icon}
                </div>
                <div className="hidden group-hover:flex p-1.5 rounded-xl border border-violet-200 bg-violet-50 text-violet-600 shadow-sm transition-all">
                    <QrCode className="w-5 h-5" />
                </div>
            </div>

            <div className="flex items-end justify-between mb-3 border-t border-slate-100 pt-3 mt-auto">
                <div className="flex flex-col">
                    <span className="text-[11px] font-semibold text-slate-500 mb-0.5">Doluluk</span>
                    <div className="flex items-baseline gap-1">
                        <span className="text-[18px] font-extrabold text-slate-800 leading-none">{durum.mevcut}</span>
                        <span className="text-slate-400 text-[12px] font-bold">/ {durum.kapasite}</span>
                    </div>
                </div>
                <span className={`text-[15px] font-black ${durum.textRenk}`}>
                    %{durum.yuzde}
                </span>
            </div>

            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${durum.yuzde}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full ${durum.barClass} relative`}
                >
                    {durum.yuzde > 0 && <div className="absolute inset-0 bg-white/20 w-full h-full"></div>}
                </motion.div>
            </div>
            
            <div className="absolute inset-0 rounded-2xl ring-2 ring-violet-500/0 group-hover:ring-violet-500/20 pointer-events-none transition-all duration-300"></div>
        </motion.div>
    );
});

export default function DepoKrokiPage() {
    const [depolar, setDepolar] = useState([]);
    const [seciliDepo, setSeciliDepo] = useState(null);
    const [raflar, setRaflar] = useState([]);
    const [paletler, setPaletler] = useState([]);
    const [loading, setLoading] = useState(true);
    
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearch] = useDebounce(searchQuery, 300);

    const [seciliRafDetay, setSeciliRafDetay] = useState(null);
    const [seciliPaletDetay, setSeciliPaletDetay] = useState(null);

    const closeRafDetayModal = () => {
        setSeciliRafDetay(null);
        setSeciliPaletDetay(null);
    };

    useEffect(() => {
        api.get('/depolar/')
            .then(res => {
                const aktifDepolar = res.data.filter(d => d.aktif);
                setDepolar(aktifDepolar);
                if (aktifDepolar.length > 0) {
                    setSeciliDepo(aktifDepolar[0]);
                } else {
                    setLoading(false);
                }
            })
            .catch(() => {
                toast.error('Depolar yüklenirken hata oluştu');
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        if (!seciliDepo) return;
        setLoading(true);

        Promise.all([
            api.get(`/raflar/`),
            api.get('/paletler/')
        ]).then(([rafRes, paletRes]) => {
            const depoRaflari = rafRes.data.filter(r => r.aktif && r.depo_id === seciliDepo.id);
            setRaflar(depoRaflari);
            setPaletler(paletRes.data.filter(p => p.aktif));
        }).catch(() => {
            toast.error('Raf ve Palet verileri yüklenemedi. Lütfen bağlantınızı kontrol edin.');
        }).finally(() => {
            setLoading(false);
        });
    }, [seciliDepo]);

    const paletMap = useMemo(() => {
        const map = {};
        paletler.forEach(p => {
            if (!p.raf_id) return;
            if (!map[p.raf_id]) map[p.raf_id] = [];
            map[p.raf_id].push(p);
        });
        return map;
    }, [paletler]);

    const getRafDurum = (rafId, kapasite) => {
        const rafPaletleri = paletMap[rafId] || [];
        const mevcutPaletSayisi = rafPaletleri.length;
        const cap = kapasite || 100;
        const oran = mevcutPaletSayisi / cap;
        const yuzde = Math.min(Math.round(oran * 100), 100);

        let bgKutusu = "bg-emerald-50";
        let borderRenk = "border-emerald-100";
        let textRenk = "text-emerald-700";
        let barClass = "bg-emerald-500";
        let icon = <CheckCircle2 className="w-5 h-5 text-emerald-600" />;

        if (oran >= 1) {
            bgKutusu = "bg-rose-50";
            borderRenk = "border-rose-100";
            textRenk = "text-rose-700";
            barClass = "bg-rose-500";
            icon = <AlertCircle className="w-5 h-5 text-rose-600" />;
        } else if (oran >= 0.7) {
            bgKutusu = "bg-amber-50";
            borderRenk = "border-amber-100";
            textRenk = "text-amber-700";
            barClass = "bg-amber-500";
            icon = <AlertTriangle className="w-5 h-5 text-amber-600" />;
        }

        return { mevcut: mevcutPaletSayisi, kapasite: cap, yuzde, bgKutusu, borderRenk, textRenk, barClass, icon, paletler: rafPaletleri };
    };

    const groupedRaflar = useMemo(() => {
        const gruplu = {};
        const filtrelenmisRaflar = raflar.filter(r =>
            r.kod.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (r.bolge && r.bolge.toLowerCase().includes(debouncedSearch.toLowerCase()))
        );

        filtrelenmisRaflar.forEach(raf => {
            const bolge = raf.bolge || "Genel Alan";
            if (!gruplu[bolge]) gruplu[bolge] = [];
            gruplu[bolge].push(raf);
        });

        return Object.keys(gruplu).sort().reduce((obj, key) => {
            obj[key] = gruplu[key].sort((a, b) => a.kod.localeCompare(b.kod));
            return obj;
        }, {});
    }, [raflar, debouncedSearch]);

    const handlePrintQR = () => {
        if (!seciliRafDetay) return;

        const printWindow = window.open('', '_blank', 'width=800,height=800');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Raf Etiketi - ${seciliRafDetay.raf.kod}</title>
                    <style>
                        @page { size: auto;  margin: 0mm; }
                        body { 
                            margin: 0; 
                            padding: 20px;
                            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background-color: white;
                            color: #0f172a;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                        }
                        
                        .label-card {
                            width: 100%;
                            max-width: 500px;
                            border: 4px solid #0f172a;
                            border-radius: 16px;
                            padding: 32px;
                            box-sizing: border-box;
                            position: relative;
                            background: #fff;
                            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
                        }

                        .header {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            border-bottom: 3px solid #e2e8f0;
                            padding-bottom: 20px;
                            margin-bottom: 30px;
                        }
                        .system-brand {
                            font-size: 24px;
                            font-weight: 900;
                            letter-spacing: -0.5px;
                            color: #334155;
                        }
                        .shelf-zone {
                            background: #f1f5f9;
                            border: 2px solid #cbd5e1;
                            padding: 6px 12px;
                            border-radius: 8px;
                            font-size: 14px;
                            font-weight: 700;
                            color: #475569;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        }

                        .main-content {
                            display: flex;
                            justify-content: space-between;
                            align-items: stretch;
                            gap: 30px;
                        }

                        .info-section {
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            flex: 1;
                        }

                        .label-title {
                            font-size: 14px;
                            font-weight: 800;
                            color: #64748b;
                            text-transform: uppercase;
                            letter-spacing: 2px;
                            margin-bottom: 8px;
                            display: block;
                        }

                        .shelf-code {
                            font-size: 72px;
                            font-weight: 900;
                            line-height: 1;
                            margin: 0 0 20px 0;
                            color: #0f172a;
                            letter-spacing: -2px;
                        }

                        .capacity-box {
                            display: inline-flex;
                            align-items: center;
                            gap: 8px;
                            background: #f8fafc;
                            border: 2px solid #e2e8f0;
                            padding: 10px 16px;
                            border-radius: 10px;
                        }
                        
                        .capacity-box span {
                            font-size: 16px;
                            font-weight: 700;
                            color: #334155;
                        }

                        .qr-section {
                            background: #fff;
                            border: 3px dashed #cbd5e1;
                            padding: 15px;
                            border-radius: 16px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                        
                        #qr-print-container svg {
                            width: 160px;
                            height: 160px;
                            display: block;
                        }

                        .footer {
                            margin-top: 30px;
                            padding-top: 20px;
                            border-top: 3px solid #e2e8f0;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-size: 12px;
                            color: #94a3b8;
                            font-weight: 600;
                        }
                        
                        .footer span strong {
                            color: #64748b;
                        }

                        @media print {
                            body {
                                -webkit-print-color-adjust: exact !important;
                                print-color-adjust: exact !important;
                            }
                            .label-card {
                                border: 4px solid #000;
                                box-shadow: none;
                            }
                        }
                    </style>
                </head>
                <body>
                    <div class="label-card">
                        <div class="header">
                            <div class="system-brand">DYS<span style="color:#64748b; font-weight: 700; margin-left: 5px; font-size: 20px;">WMS</span></div>
                            <div class="shelf-zone">${seciliRafDetay.raf.bolge || 'GENEL ALAN'}</div>
                        </div>

                        <div class="main-content">
                            <div class="info-section">
                                <div>
                                    <span class="label-title">LOC / RAF KODU</span>
                                    <h1 class="shelf-code">${seciliRafDetay.raf.kod}</h1>
                                </div>
                                <div class="capacity-box">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
                                    <span>MAX: <strong>${seciliRafDetay.raf.kapasite}</strong> PLT</span>
                                </div>
                            </div>
                            
                            <div class="qr-section">
                                <div id="qr-print-container">
                                    ${document.getElementById('qr-svg-container')?.innerHTML || ''}
                                </div>
                            </div>
                        </div>

                        <div class="footer">
                            <span>YAZDIRILMA: <strong>${new Date().toLocaleDateString('tr-TR')} ${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</strong></span>
                            <span>OTOMATİK OLUŞTURULDU</span>
                        </div>
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

    // Tailwind Safelist düzeltmesi için manuel array (Production JIT hatasını engeller)
    const durumGöstergeleri = [
        { id: 'musait', bgClass: 'bg-emerald-50', borderClass: 'border-emerald-100', dotClass: 'bg-emerald-500', textClass: 'text-emerald-700', label: 'Müsait (%0-69)' },
        { id: 'kritik', bgClass: 'bg-amber-50', borderClass: 'border-amber-100', dotClass: 'bg-amber-500', textClass: 'text-amber-700', label: 'Kritik (%70-99)' },
        { id: 'dolu', bgClass: 'bg-rose-50', borderClass: 'border-rose-100', dotClass: 'bg-rose-500', textClass: 'text-rose-700', label: 'Dolu (%100)' }
    ];

    return (
        <div className="space-y-6 max-w-[1600px] mx-auto p-4 sm:p-6 pb-24 min-h-screen bg-slate-50/50">
            {/* --- ÜST BİLGİ VE FİLTRELER --- */}
            <div className="flex flex-col gap-5">
                <div className="flex flex-col xl:flex-row gap-5 items-start xl:items-center justify-between bg-white p-6 rounded-3xl shadow-sm border border-slate-200/60">
                    <div className="flex items-center gap-5">
                        <div className="w-14 h-14 rounded-2xl bg-violet-50 border border-violet-100 flex items-center justify-center shrink-0 shadow-inner">
                            <Warehouse className="w-7 h-7 text-violet-600" />
                        </div>
                        <div>
                            <h2 className="text-[22px] font-extrabold text-slate-800 tracking-tight">Depo Krokisi</h2>
                            <p className="text-[14px] font-medium text-slate-500 mt-0.5">Rafların doluluk durumunu ve operasyonel kapasiteyi izleyin</p>
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-4 w-full xl:w-auto">
                        <div className="relative w-full sm:w-72">
                            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                placeholder="Raf Kodu veya Bölge Ara..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full h-12 pl-11 pr-4 text-[14px] rounded-2xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-violet-500/10 focus:border-violet-500 outline-none transition-all placeholder:text-slate-400 font-medium text-slate-700"
                            />
                        </div>
                        <div className="relative w-full sm:w-64">
                            <Building className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                            <select
                                value={seciliDepo?.id || ''}
                                onChange={(e) => {
                                    const depo = depolar.find(d => d.id === parseInt(e.target.value));
                                    if (depo) setSeciliDepo(depo);
                                }}
                                className="w-full h-12 pl-11 pr-10 text-[14px] font-bold text-slate-700 bg-white border border-slate-200 rounded-2xl appearance-none focus:outline-none focus:ring-4 focus:ring-violet-500/10 focus:border-violet-500 cursor-pointer transition-all shadow-sm"
                            >
                                {depolar.map(d => (
                                    <option key={d.id} value={d.id}>{d.isim}</option>
                                ))}
                            </select>
                            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                    </div>
                </div>

                {/* Lejant (Durum Göstergeleri) - Düzeltilmiş Kısım */}
                <div className="flex flex-wrap items-center gap-4 bg-white px-6 py-4 rounded-2xl border border-slate-200/60 shadow-sm">
                    <div className="flex items-center gap-2 mr-4">
                        <LayoutGrid className="w-5 h-5 text-slate-400" />
                        <span className="text-[14px] font-bold text-slate-700">Kapasite Göstergeleri</span>
                    </div>
                    <div className="flex flex-wrap gap-3">
                        {durumGöstergeleri.map(item => (
                            <div key={item.id} className={`flex items-center gap-2 ${item.bgClass} border ${item.borderClass} px-3 py-1.5 rounded-xl`}>
                                <div className={`w-2.5 h-2.5 rounded-full ${item.dotClass} shadow-sm`}></div>
                                <span className={`text-[13px] font-bold ${item.textClass}`}>{item.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* --- KROKİ ALANI --- */}
            <div className="min-h-[500px] mt-8">
                {loading ? (
                    <div className="flex flex-col justify-center items-center h-64 space-y-4">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-violet-600"></div>
                        <span className="text-slate-500 font-medium text-[14px]">Depo analiz ediliyor...</span>
                    </div>
                ) : Object.keys(groupedRaflar).length === 0 ? (
                    <div className="bg-white rounded-3xl border border-slate-200/60 shadow-sm flex flex-col items-center justify-center p-12 text-center h-[400px]">
                        <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-5 border border-slate-100">
                            <Warehouse className="w-10 h-10 text-slate-300" />
                        </div>
                        <h3 className="text-[20px] font-extrabold text-slate-700 mb-2">Kayıt Bulunamadı</h3>
                        <p className="text-[15px] font-medium text-slate-500 max-w-sm">Bu lokasyonda raf bulunmuyor veya aramanızla eşleşen sonuç yok.</p>
                    </div>
                ) : (
                    <div className="space-y-10">
                        {Object.entries(groupedRaflar).map(([bolge, bolgeRaflari]) => (
                            <div key={bolge} className="flex flex-col gap-4">
                                <div className="flex items-center gap-3 px-2">
                                    <div className="w-1.5 h-6 bg-violet-500 rounded-full"></div>
                                    <h3 className="text-[18px] font-extrabold text-slate-800">{bolge}</h3>
                                    <span className="px-3 py-1 rounded-lg bg-slate-100 text-[12px] font-bold text-slate-500">
                                        {bolgeRaflari.length} Raf
                                    </span>
                                </div>
                                
                                <motion.div layout className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-4">
                                    <AnimatePresence>
                                        {bolgeRaflari.map(raf => (
                                            <RafCard 
                                                key={raf.id} 
                                                raf={raf} 
                                                durum={getRafDurum(raf.id, raf.kapasite)} 
                                                onSelect={setSeciliRafDetay} 
                                            />
                                        ))}
                                    </AnimatePresence>
                                </motion.div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* --- MOBİL ÖNCELİKLİ DETAY MODALI (BOTTOM SHEET) --- */}
            <AnimatePresence>
                {seciliRafDetay && (
                    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={closeRafDetayModal}
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
                        />
                        
                        <motion.div
                            initial={{ y: "100%", opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: "100%", opacity: 0 }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="bg-white w-full sm:w-full max-w-lg rounded-t-3xl sm:rounded-3xl shadow-2xl flex flex-col z-10 max-h-[90vh] sm:max-h-[85vh] relative"
                        >
                            <div className="w-full flex justify-center pt-3 pb-1 sm:hidden">
                                <div className="w-12 h-1.5 bg-slate-200 rounded-full"></div>
                            </div>

                            <div className="flex items-center justify-between p-5 border-b border-slate-100 shrink-0">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-violet-50 flex items-center justify-center border border-violet-100">
                                        <Warehouse className="w-6 h-6 text-violet-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-[18px] font-extrabold text-slate-800">{seciliRafDetay.raf.kod}</h3>
                                        <p className="text-[13px] font-medium text-slate-500">{seciliRafDetay.raf.bolge || 'Genel Alan'}</p>
                                    </div>
                                </div>
                                <button
                                    onClick={closeRafDetayModal}
                                    className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-50 text-slate-500 hover:bg-slate-100 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="overflow-y-auto p-5 custom-scrollbar flex-1">
                                <div className="grid grid-cols-2 gap-3 mb-6">
                                    <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 flex flex-col items-center">
                                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">Mevcut / Max</span>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-[22px] font-black text-slate-800">{seciliRafDetay.durum.mevcut}</span>
                                            <span className="text-slate-400 text-[14px] font-bold">/ {seciliRafDetay.durum.kapasite}</span>
                                        </div>
                                    </div>
                                    <div className={`border rounded-2xl p-4 flex flex-col items-center ${seciliRafDetay.durum.bgKutusu} ${seciliRafDetay.durum.borderRenk}`}>
                                        <span className={`text-[11px] font-bold uppercase tracking-widest mb-1 ${seciliRafDetay.durum.textRenk} opacity-70`}>Doluluk</span>
                                        <span className={`text-[22px] font-black ${seciliRafDetay.durum.textRenk}`}>
                                            %{seciliRafDetay.durum.yuzde}
                                        </span>
                                    </div>
                                </div>

                                <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex justify-between items-center w-full mb-8">
                                    <div className="flex items-center gap-4">
                                        <div id="qr-svg-container" className="p-1.5 bg-white border border-slate-100 rounded-xl shadow-sm">
                                            <QRCodeSVG value={`http://dys-app.com/raf/${seciliRafDetay.raf.kod}`} size={48} />
                                        </div>
                                        <div>
                                            <div className="text-[14px] font-bold text-slate-800">Fiziksel Barkod</div>
                                            <div className="text-[12px] font-medium text-slate-500 mt-0.5">Terminal taraması için</div>
                                        </div>
                                    </div>
                                    <button onClick={handlePrintQR} className="p-2.5 bg-violet-50 text-violet-600 hover:bg-violet-100 rounded-xl transition-colors">
                                        <Printer className="w-5 h-5" />
                                    </button>
                                </div>

                                <div className="w-full">
                                    <div className="flex items-center gap-2 mb-4">
                                        <LayoutGrid className="w-4 h-4 text-violet-500" />
                                        <h5 className="text-[15px] font-extrabold text-slate-800">
                                            Raftaki Paletler <span className="text-slate-400 font-medium">({seciliRafDetay.durum.paletler.length})</span>
                                        </h5>
                                    </div>

                                    <div className="space-y-3">
                                        {seciliRafDetay.durum.paletler.length > 0 ? (
                                            seciliRafDetay.durum.paletler.map(palet => {
                                                const isExpanded = seciliPaletDetay?.id === palet.id;
                                                return (
                                                    <div key={palet.id} className={`bg-white border transition-all rounded-2xl overflow-hidden ${isExpanded ? 'border-violet-300 shadow-md ring-4 ring-violet-50' : 'border-slate-200 hover:border-violet-200'}`}>
                                                        <div 
                                                            onClick={() => setSeciliPaletDetay(isExpanded ? null : palet)}
                                                            className="p-4 flex items-center justify-between cursor-pointer"
                                                        >
                                                            <div className="flex flex-col gap-1.5">
                                                                <div className="flex items-center gap-2.5">
                                                                    <span className="text-[15px] font-black text-slate-800">{palet.palet_no}</span>
                                                                    <span className="px-2 py-0.5 rounded-lg bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-widest border border-slate-200/60">
                                                                        Lot: {palet.lot?.lot_no || 'Yok'}
                                                                    </span>
                                                                </div>
                                                                <span className="text-[13px] font-medium text-slate-500 line-clamp-1">
                                                                    {palet.lot?.urun?.isim || 'Ürün bilgisi yok'}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-3">
                                                                <span className="text-[13px] font-black text-violet-700 bg-violet-50 px-3 py-1.5 rounded-xl border border-violet-100/50">
                                                                    {palet.koli_adedi} Koli
                                                                </span>
                                                                <div className="text-slate-400">
                                                                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <AnimatePresence>
                                                            {isExpanded && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: "auto", opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="bg-slate-50/80 border-t border-slate-100"
                                                                >
                                                                    <div className="p-4 grid grid-cols-2 gap-y-4 gap-x-4">
                                                                        <div className="flex flex-col gap-1">
                                                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Scale className="w-3.5 h-3.5" /> Ağırlık</span>
                                                                            <span className="text-[13px] font-bold text-slate-800">{palet.palet_kg ? `${palet.palet_kg} kg` : '-'}</span>
                                                                        </div>
                                                                        <div className="flex flex-col gap-1">
                                                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> Üretim T.</span>
                                                                            <span className="text-[13px] font-bold text-slate-800">{palet.lot?.uretim_tarihi || '-'}</span>
                                                                        </div>
                                                                        <div className="flex flex-col gap-1">
                                                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5" /> SKT</span>
                                                                            <span className="text-[13px] font-bold text-slate-800">{palet.lot?.son_kullanma_tarihi || '-'}</span>
                                                                        </div>
                                                                        <div className="flex flex-col gap-1">
                                                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5"><Hash className="w-3.5 h-3.5" /> Barkod</span>
                                                                            <span className="text-[13px] font-bold text-slate-800">{palet.lot?.urun?.barkod || '-'}</span>
                                                                        </div>
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-8 flex flex-col items-center justify-center text-center">
                                                <Package className="w-10 h-10 text-slate-300 mb-3" />
                                                <span className="text-[14px] font-bold text-slate-600">Bu rafta palet bulunmuyor</span>
                                                <span className="text-[13px] font-medium text-slate-400 mt-1">Raf şu an sistemde boş olarak işaretlenmiştir.</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}