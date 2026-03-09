import { useState, useEffect } from 'react';
import {
    Truck,
    Search,
    Calendar,
    User,
    DoorOpen,
    Barcode,
    Printer,
    X,
    ChevronDown,
    MapPin,
    Package,
    ArrowUpRight,
    Loader2
} from 'lucide-react';
import { getStokHareketleri, getUrunler } from '../services/api';
import toast from 'react-hot-toast';

export default function SevkiyatlarPage() {
    // State tanımlamaları
    const [cikislar, setCikislar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [loading, setLoading] = useState(true);
    const [aramaMetni, setAramaMetni] = useState('');
    const [seciliSevkiyat, setSeciliSevkiyat] = useState(null);

    // API Verilerini Çek
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [hareketlerRes, urunlerRes] = await Promise.all([
                    // Sadece çıkışları getir (yeni backend özelliği eklendi)
                    getStokHareketleri({ limit: 100, hareket_tipi: 'cikis' }),
                    getUrunler({ limit: 500 })
                ]);

                // Bazı eski kayıtlarda siparis_no olmayabilir, 
                // ya da frontend'de sıralama gerekebilir. Backend zaten ID descending getiriyor.
                setCikislar(hareketlerRes.data);
                setUrunler(urunlerRes.data);
            } catch (err) {
                toast.error("Sevkiyat geçmişi yüklenirken hata oluştu.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // Ürün ismini bulmak için yardımcı fonksiyon
    const getUrunIsmi = (urun_id) => {
        const urun = urunler.find(u => u.id === urun_id);
        return urun ? urun.isim : `Ürün #${urun_id}`;
    };

    // Arama Filitresi: Plaka, Sipariş, Depocu adına göre
    const filtrelenmisCikislar = cikislar.filter(c => {
        const arama = aramaMetni.toLowerCase();
        return (
            (c.tir_plaka && c.tir_plaka.toLowerCase().includes(arama)) ||
            (c.siparis_no && c.siparis_no.toLowerCase().includes(arama)) ||
            (c.kullanici && c.kullanici.ad_soyad.toLowerCase().includes(arama)) ||
            (getUrunIsmi(c.urun_id).toLowerCase().includes(arama))
        );
    });

    // İrsaliye Yazdırma Şablonu (Endüstriyel WMS Tasarımı)
    const handleYazdir = (sevkiyat) => {
        const urunAdi = getUrunIsmi(sevkiyat.urun_id);
        const tarih = new Date(sevkiyat.tarih).toLocaleString('tr-TR');

        let barkodHtml = '';
        if (sevkiyat.barkodlar && Array.isArray(sevkiyat.barkodlar) && sevkiyat.barkodlar.length > 0) {
            barkodHtml = sevkiyat.barkodlar.map(b =>
                `<div class="barcode-tag">${b}</div>`
            ).join('');
        } else {
            barkodHtml = '<div style="color:#64748b; font-style:italic;">Barkod verisi bulunamadı / Genel Çıkış</div>';
        }

        const printWindow = window.open('', '_blank', 'width=800,height=900');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Sevk İrsaliyesi - ${sevkiyat.siparis_no || 'Tasnifsiz'}</title>
                    <style>
                        @page { size: auto; margin: 0mm; }
                        body { 
                            margin: 0; padding: 40px; 
                            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            color: #0f172a;
                            background: white;
                        }
                        
                        .waybill-container {
                            border: 3px solid #0f172a;
                            padding: 30px;
                            position: relative;
                            border-radius: 8px;
                        }

                        .header {
                            display: flex;
                            justify-content: space-between;
                            align-items: flex-start;
                            border-bottom: 4px solid #1e293b;
                            padding-bottom: 20px;
                            margin-bottom: 30px;
                        }

                        .brand-area h1 {
                            font-size: 32px;
                            font-weight: 900;
                            margin: 0;
                            letter-spacing: -1px;
                        }
                        
                        .brand-area p { margin: 5px 0 0 0; color: #64748b; font-weight: 600; font-size: 14px; }

                        .doc-info { text-align: right; }
                        .doc-title { font-size: 24px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; color: #334155; }
                        
                        .info-grid {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 30px;
                            margin-bottom: 40px;
                        }
                        
                        .info-box {
                            background: #f8fafc;
                            border: 2px solid #e2e8f0;
                            padding: 20px;
                            border-radius: 8px;
                        }
                        .info-box-title { font-size: 12px; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
                        .info-box-val { font-size: 18px; font-weight: 700; color: #0f172a; }

                        table { w-full; border-collapse: collapse; margin-bottom: 40px; }
                        th { background: #0f172a; color: white; text-align: left; padding: 12px; font-size: 14px; text-transform: uppercase; font-weight: 700;}
                        td { border-bottom: 2px solid #e2e8f0; padding: 16px 12px; font-size: 16px; font-weight: 600;}
                        
                        .barcode-section {
                            background: white;
                            border: 2px dashed #cbd5e1;
                            padding: 20px;
                            border-radius: 8px;
                        }
                        
                        .barcode-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
                        .barcode-tag { 
                            background: #f1f5f9; border: 1px solid #cbd5e1; 
                            padding: 6px 12px; border-radius: 4px; font-family: monospace; 
                            font-weight: bold; font-size: 14px; color: #334155;
                        }

                        .footer {
                            margin-top: 50px;
                            display: grid;
                            grid-template-columns: 1fr 1fr 1fr;
                            text-align: center;
                            gap: 20px;
                            font-size: 14px;
                            font-weight: 700;
                            color: #475569;
                        }
                        .signature-line {
                            margin-top: 40px;
                            border-bottom: 2px solid #cbd5e1;
                            display: inline-block;
                            width: 80%;
                            height: 40px;
                        }
                        
                        @media print {
                            body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
                        }
                    </style>
                </head>
                <body>
                    <div class="waybill-container">
                        <div class="header">
                            <div class="brand-area">
                                <h1>DYS WMS</h1>
                                <p>Otomatik Depo & Sevkiyat Yönetimi</p>
                            </div>
                            <div class="doc-info">
                                <div class="doc-title">ÇIKIŞ / SEVK İRSALİYESİ</div>
                                <div style="font-size:16px; font-weight:700;">TARİH: ${tarih}</div>
                                <div style="font-size:14px; font-weight:600; color:#64748b; margin-top:5px;">Belge No: OUT-${sevkiyat.id}</div>
                            </div>
                        </div>

                        <div class="info-grid">
                            <div class="info-box">
                                <div class="info-box-title">LOJİSTİK / NAKLİYE BİLGİSİ</div>
                                <div class="info-box-val" style="font-size: 24px;">🚚 ${sevkiyat.tir_plaka || 'Araç Bilgisi Yok'}</div>
                                <div style="margin-top:10px; font-weight:600;">Çıkış Kapısı: ${sevkiyat.depo_kapi || 'Tanımsız'}</div>
                                <div style="margin-top:5px; font-weight:600;">Sipariş / Referans: ${sevkiyat.siparis_no || 'Yok'}</div>
                            </div>
                            <div class="info-box">
                                <div class="info-box-title">İŞLEMİ YAPAN (DEPO PERSONELİ)</div>
                                <div class="info-box-val">👤 ${sevkiyat.kullanici ? sevkiyat.kullanici.ad_soyad : 'Sistem Auth'}</div>
                            </div>
                        </div>

                        <table style="width: 100%;">
                            <thead>
                                <tr>
                                    <th>Ürün Kodu / Tanımı</th>
                                    <th>Açıklama</th>
                                    <th style="text-align: right;">Miktar</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>
                                        <div style="font-weight: 800;">${urunAdi}</div>
                                        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">ID: ${sevkiyat.urun_id} • İşlem Tipi: O-CKS</div>
                                    </td>
                                    <td>${sevkiyat.aciklama || '-'}</td>
                                    <td style="text-align: right; font-size: 22px; font-weight: 900;">${sevkiyat.miktar} AD.</td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="barcode-section">
                            <div class="info-box-title" style="margin-bottom:0;">OKUTULAN BARKODLAR / SERİ NUMARALARI</div>
                            <div class="barcode-grid">
                                ${barkodHtml}
                            </div>
                        </div>

                        <div class="footer">
                            <div>
                                Yüklemeyi Yapan
                                <div class="signature-line"></div>
                                <div style="margin-top: 5px;">${sevkiyat.kullanici ? sevkiyat.kullanici.ad_soyad : ''}</div>
                            </div>
                            <div>
                                Kontrol Eden / Güvenlik
                                <div class="signature-line"></div>
                            </div>
                            <div>
                                Teslim Alan Şoför
                                <div class="signature-line"></div>
                            </div>
                        </div>
                    </div>
                </body>
                <script>
                    window.onload = () => { window.print(); setTimeout(() => window.close(), 500); }
                </script>
            </html>
        `);
        printWindow.document.close();
    };


    return (
        <div className="max-w-[1200px] mx-auto px-4 py-6 sm:px-6 lg:px-8">

            {/* Sayfa Başlığı ve Arama (Header) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shadow-inner">
                            <ArrowUpRight strokeWidth={3} className="w-6 h-6" />
                        </div>
                        Sevkiyatlar (Çıkış)
                    </h1>
                    <p className="text-slate-500 font-medium mt-1 ml-15">
                        Depodan sevk edilen ürünler, tır ve kapı bilgileri.
                    </p>
                </div>

                <div className="relative w-full sm:w-[350px]">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Plaka, sipariş veya personel ara..."
                        value={aramaMetni}
                        onChange={(e) => setAramaMetni(e.target.value)}
                        className="w-full h-14 pl-12 pr-4 text-sm font-semibold rounded-2xl border-2 border-slate-200 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-slate-700 shadow-sm"
                    />
                </div>
            </div>

            {/* İçerik Alanı */}
            {loading ? (
                <div className="flex flex-col items-center justify-center p-20">
                    <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
                    <p className="text-slate-500 font-semibold">Sevkiyat verileri yükleniyor...</p>
                </div>
            ) : filtrelenmisCikislar.length === 0 ? (
                <div className="bg-white border-2 border-dashed border-slate-200 rounded-3xl p-16 text-center">
                    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Package className="w-10 h-10 text-slate-300" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-700">Kayıt Bulunamadı</h3>
                    <p className="text-slate-500 font-medium mt-1">Arama kriterlerinize uygun çıkış işlemi bulunmuyor.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {filtrelenmisCikislar.map((sevkiyat) => {
                        const isExpanded = seciliSevkiyat?.id === sevkiyat.id;
                        const urunAdi = getUrunIsmi(sevkiyat.urun_id);
                        const isOk = sevkiyat.tir_plaka && sevkiyat.siparis_no; // Plaka ve Sipariş varsa OK

                        return (
                            <div
                                key={sevkiyat.id}
                                className={`bg-white border transition-all duration-300 overflow-hidden cursor-pointer
                                    ${isExpanded
                                        ? 'border-blue-300 shadow-lg shadow-blue-500/10 rounded-3xl ring-4 ring-blue-50'
                                        : 'border-slate-200 shadow-sm hover:border-blue-200 hover:shadow-md rounded-2xl'
                                    }`}
                                onClick={() => setSeciliSevkiyat(isExpanded ? null : sevkiyat)}
                            >
                                {/* Kart Özeti (Her Zaman Görünür) */}
                                <div className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                    <div className="flex items-center gap-4 w-full sm:w-auto">
                                        {/* İkon / Durum */}
                                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner
                                            ${isOk ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-slate-50 text-slate-600 border border-slate-100'}
                                        `}>
                                            <Truck className="w-6 h-6 mb-0.5" />
                                        </div>

                                        {/* Temel Bilgi */}
                                        <div className="min-w-0 pr-2">
                                            <h3 className="text-base sm:text-lg font-bold text-slate-800 truncate">
                                                {sevkiyat.tir_plaka || 'Plaka Tanımsız'}
                                            </h3>
                                            <p className="text-sm font-semibold text-slate-500 mt-0.5 flex items-center gap-2">
                                                <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md font-bold text-xs">{sevkiyat.siparis_no || 'Sipariş Yok'}</span>
                                                <span className="hidden sm:inline text-slate-300">•</span>
                                                <span className="truncate">{urunAdi}</span>
                                            </p>
                                        </div>
                                    </div>

                                    {/* Miktar ve Ok Info */}
                                    <div className="flex items-center justify-between sm:justify-end gap-5 w-full sm:w-auto border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100">
                                        <div className="text-left sm:text-right">
                                            <span className="block text-2xl font-black text-slate-800 leading-none mb-1">
                                                -{sevkiyat.miktar}
                                            </span>
                                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Miktar</span>
                                        </div>

                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-slate-50 transition-transform duration-300 ${isExpanded ? 'rotate-180 bg-blue-100 text-blue-600' : 'text-slate-400'}`}>
                                            <ChevronDown className="w-5 h-5" />
                                        </div>
                                    </div>
                                </div>

                                {/* Genişleyen Detay Paneli (Sadece isExpanded ise) */}
                                <div className={`grid transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${isExpanded ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                                    <div className="overflow-hidden">
                                        <div className="p-4 sm:p-6 bg-slate-50/50 border-t border-slate-100 m-1 rounded-b-[22px]">

                                            {/* Detay Grid */}
                                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-start gap-3">
                                                    <Calendar className="w-5 h-5 text-slate-400 mt-0.5" />
                                                    <div>
                                                        <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Tarih / Saat</span>
                                                        <span className="font-semibold text-slate-700 text-sm">{new Date(sevkiyat.tarih).toLocaleDateString('tr-TR')}</span>
                                                        <div className="font-semibold text-slate-500 text-xs">{new Date(sevkiyat.tarih).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</div>
                                                    </div>
                                                </div>

                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-start gap-3">
                                                    <User className="w-5 h-5 text-slate-400 mt-0.5" />
                                                    <div>
                                                        <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Yükleyen / Depocu</span>
                                                        <span className="font-semibold text-slate-700 text-sm">{sevkiyat.kullanici ? sevkiyat.kullanici.ad_soyad : 'Sistem'}</span>
                                                    </div>
                                                </div>

                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-start gap-3">
                                                    <DoorOpen className="w-5 h-5 text-slate-400 mt-0.5" />
                                                    <div>
                                                        <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Depo Kapısı</span>
                                                        <span className="font-bold text-blue-600 text-sm">{sevkiyat.depo_kapi || 'Tanımsız Kapı'}</span>
                                                    </div>
                                                </div>

                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-start gap-3">
                                                    <MapPin className="w-5 h-5 text-slate-400 mt-0.5" />
                                                    <div>
                                                        <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Raf (Opsiyonel)</span>
                                                        <span className="font-semibold text-slate-700 text-sm">{sevkiyat.raf ? sevkiyat.raf.kod : '-'}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Barkodlar Bölümü */}
                                            <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <Barcode className="w-5 h-5 text-slate-500" />
                                                    <h4 className="font-bold text-slate-700 text-sm">Okutulan Barkodlar / Seri No Listesi</h4>
                                                    <span className="ml-auto bg-slate-100 text-slate-500 font-bold px-2 py-0.5 rounded-md text-xs">
                                                        {sevkiyat.barkodlar ? sevkiyat.barkodlar.length : 0} Adet
                                                    </span>
                                                </div>

                                                {sevkiyat.barkodlar && sevkiyat.barkodlar.length > 0 ? (
                                                    <div className="flex flex-wrap gap-2 max-h-[150px] overflow-y-auto custom-scrollbar pr-2">
                                                        {sevkiyat.barkodlar.map((barkod, i) => (
                                                            <div key={i} className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-sm font-mono font-semibold text-slate-600">
                                                                {barkod}
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <div className="text-center py-4 text-slate-400 font-medium text-sm">
                                                        Barkod okutulmadan çıkış yapılmış.
                                                    </div>
                                                )}
                                            </div>

                                            {/* Aksiyonlar (Yazdır) */}
                                            <div className="flex justify-end pt-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleYazdir(sevkiyat);
                                                    }}
                                                    className="flex items-center gap-2 bg-slate-900 text-white px-5 py-3 rounded-xl font-bold text-sm shadow-lg shadow-slate-900/20 hover:bg-slate-800 active:scale-[0.98] transition-all"
                                                >
                                                    <Printer className="w-5 h-5" />
                                                    Geçmiş Sevk İrsaliyesi Yazdır
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
