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
    ChevronLeft,
    ChevronRight,
    MapPin,
    Package,
    ArrowUpRight,
    Loader2,
    Filter,
    RotateCcw
} from 'lucide-react';
import { getStokHareketleri, getUrunler, getKullanicilar, getRaflar } from '../services/api';
import toast from 'react-hot-toast';
import { useMemo } from 'react';

// Güvenlik (XSS) için basit bir temizleme fonksiyonu
const escapeHtml = (unsafeText) => {
    if (!unsafeText) return '';
    const textStr = String(unsafeText);
    return textStr
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
};

// Tarih yardımcı fonksiyonları
function gunBaslangici(tarih) {
    const d = new Date(tarih);
    d.setHours(0, 0, 0, 0);
    return d;
}

function ayBaslangici() {
    const d = new Date();
    d.setDate(1);
    d.setHours(0, 0, 0, 0);
    return d;
}

function haftaBaslangici() {
    const d = new Date();
    const gun = d.getDay();
    const fark = gun === 0 ? 6 : gun - 1; // Pazartesi başlangıç
    d.setDate(d.getDate() - fark);
    d.setHours(0, 0, 0, 0);
    return d;
}

function gunOnce(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    d.setHours(0, 0, 0, 0);
    return d;
}

function tarihToInput(tarih) {
    if (!tarih) return '';
    const d = new Date(tarih);
    const yil = d.getFullYear();
    const ay = String(d.getMonth() + 1).padStart(2, '0');
    const gun = String(d.getDate()).padStart(2, '0');
    return `${yil}-${ay}-${gun}`;
}

const HIZLI_FILTRELER = [
    { etiket: 'Bugün', key: 'bugun', hesapla: () => ({ bas: gunBaslangici(new Date()), bit: null }) },
    { etiket: 'Bu Hafta', key: 'bu_hafta', hesapla: () => ({ bas: haftaBaslangici(), bit: null }) },
    { etiket: 'Bu Ay', key: 'bu_ay', hesapla: () => ({ bas: ayBaslangici(), bit: null }) },
    { etiket: 'Son 7 Gün', key: 'son_7', hesapla: () => ({ bas: gunOnce(7), bit: null }) },
    { etiket: 'Son 30 Gün', key: 'son_30', hesapla: () => ({ bas: gunOnce(30), bit: null }) },
    { etiket: 'Tümü', key: 'tumu', hesapla: () => ({ bas: null, bit: null }) },
];

export default function SevkiyatlarPage() {
    // State tanımlamaları
    const [cikislar, setCikislar] = useState([]);
    const [urunler, setUrunler] = useState([]);
    const [kullanicilar, setKullanicilar] = useState([]);
    const [raflar, setRaflar] = useState([]);
    const [loading, setLoading] = useState(true);
    const [aramaMetni, setAramaMetni] = useState('');
    const [seciliSevkiyat, setSeciliSevkiyat] = useState(null);
    const [mevcutSayfa, setMevcutSayfa] = useState(1);
    const sayfaBasinaKayit = 10;

    // Tarih filtresi state — varsayılan: Bu Ay
    const [baslangicTarih, setBaslangicTarih] = useState(ayBaslangici());
    const [bitisTarih, setBitisTarih] = useState(null);
    const [aktifHizliFiltre, setAktifHizliFiltre] = useState('bu_ay');

    const hizliFiltreSec = (filtre) => {
        const { bas, bit } = filtre.hesapla();
        setBaslangicTarih(bas);
        setBitisTarih(bit);
        setAktifHizliFiltre(filtre.key);
    };

    const filtreleriSifirla = () => {
        setAramaMetni('');
        setBaslangicTarih(ayBaslangici());
        setBitisTarih(null);
        setAktifHizliFiltre('bu_ay');
    };

    const filtreAktifMi = aramaMetni || aktifHizliFiltre !== 'bu_ay';

    const urunMap = useMemo(
        () => new Map(urunler.map((u) => [u.id, u.isim])),
        [urunler]
    );
    const kullaniciMap = useMemo(
        () => new Map(kullanicilar.map((k) => [k.id, k.ad_soyad])),
        [kullanicilar]
    );
    const rafMap = useMemo(
        () => new Map(raflar.map((r) => [r.id, r.kod])),
        [raflar]
    );

    // API Verilerini Çek
    useEffect(() => {
        const fetchTumCikislar = async () => {
            const limit = 500;
            const maxDongu = 20;
            let skip = 0;
            let dongu = 0;
            let tumKayitlar = [];

            while (dongu < maxDongu) {
                const res = await getStokHareketleri({ limit, skip, hareket_tipi: 'cikis' });
                const parcali = Array.isArray(res.data) ? res.data : [];
                tumKayitlar = tumKayitlar.concat(parcali);
                if (parcali.length < limit) break;
                skip += limit;
                dongu += 1;
            }
            return tumKayitlar;
        };

        const fetchData = async () => {
            try {
                const [hareketler, urunlerRes, raflarRes] = await Promise.all([
                    fetchTumCikislar(),
                    getUrunler({ limit: 2000 }),
                    getRaflar({ limit: 1000 }),
                ]);

                setCikislar(hareketler);
                setUrunler(urunlerRes.data);
                setRaflar(raflarRes.data);

                // Bu endpoint admin yetkisi gerektirdiği için opsiyonel çekiliyor.
                try {
                    const kullanicilarRes = await getKullanicilar();
                    setKullanicilar(kullanicilarRes.data);
                } catch {
                    setKullanicilar([]);
                }
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
        return urunMap.get(urun_id) || `Ürün #${urun_id}`;
    };
    const getKullaniciAdi = (sevkiyat) => {
        if (sevkiyat.kullanici?.ad_soyad) return sevkiyat.kullanici.ad_soyad;
        if (sevkiyat.kullanici_id) return kullaniciMap.get(sevkiyat.kullanici_id) || `Kullanıcı #${sevkiyat.kullanici_id}`;
        return 'Sistem';
    };
    const getRafKodu = (sevkiyat) => {
        if (sevkiyat.raf?.kod) return sevkiyat.raf.kod;
        if (sevkiyat.raf_id) return rafMap.get(sevkiyat.raf_id) || `Raf #${sevkiyat.raf_id}`;
        return '-';
    };

    // Filtreler değiştiğinde sayfayı sıfırla
    useEffect(() => {
        setMevcutSayfa(1);
    }, [aramaMetni, baslangicTarih, bitisTarih]);

    // Arama + Tarih Filitresi
    const filtrelenmisCikislar = cikislar.filter(c => {
        // Metin araması
        const arama = aramaMetni.toLowerCase();
        const metinUygun = !aramaMetni || (
            (c.tir_plaka && c.tir_plaka.toLowerCase().includes(arama)) ||
            (c.siparis_no && c.siparis_no.toLowerCase().includes(arama)) ||
            (getKullaniciAdi(c).toLowerCase().includes(arama)) ||
            (c.irsaliye_no && c.irsaliye_no.toLowerCase().includes(arama)) ||
            (c.sofor_adi && c.sofor_adi.toLowerCase().includes(arama)) ||
            (c.tasiyici_firma && c.tasiyici_firma.toLowerCase().includes(arama)) ||
            (c.palet_no && c.palet_no.toLowerCase().includes(arama)) ||
            (getUrunIsmi(c.urun_id).toLowerCase().includes(arama))
        );

        // Tarih filtresi
        let tarihUygun = true;
        if (baslangicTarih || bitisTarih) {
            const kayitTarih = new Date(c.tarih);
            if (baslangicTarih) {
                tarihUygun = kayitTarih >= baslangicTarih;
            }
            if (tarihUygun && bitisTarih) {
                const bitisGunSonu = new Date(bitisTarih);
                bitisGunSonu.setHours(23, 59, 59, 999);
                tarihUygun = kayitTarih <= bitisGunSonu;
            }
        }

        return metinUygun && tarihUygun;
    });

    // Sayfalama hesaplamaları
    const toplamSayfa = Math.ceil(filtrelenmisCikislar.length / sayfaBasinaKayit);
    const baslangicIndex = (mevcutSayfa - 1) * sayfaBasinaKayit;
    const sayfadakiKayitlar = filtrelenmisCikislar.slice(baslangicIndex, baslangicIndex + sayfaBasinaKayit);

    // İrsaliye Yazdırma Şablonu (Endüstriyel WMS Tasarımı)
    const handleYazdir = (sevkiyat) => {
        const urunAdi = escapeHtml(getUrunIsmi(sevkiyat.urun_id));
        const tarih = escapeHtml(new Date(sevkiyat.tarih).toLocaleString('tr-TR'));
        const tirPlaka = escapeHtml(sevkiyat.tir_plaka || 'Araç Bilgisi Yok');
        const depoKapi = escapeHtml(sevkiyat.depo_kapi || 'Tanımsız');
        const siparisNo = escapeHtml(sevkiyat.siparis_no || 'Yok');
        const aciklama = escapeHtml(sevkiyat.aciklama || '-');
        const kullaniciAdi = escapeHtml(getKullaniciAdi(sevkiyat));
        const soforAdi = escapeHtml(sevkiyat.sofor_adi || '-');
        const tasiyiciFirma = escapeHtml(sevkiyat.tasiyici_firma || '-');
        const irsaliyeNo = escapeHtml(sevkiyat.irsaliye_no || '-');
        const paletNo = escapeHtml(sevkiyat.palet_no || '-');

        let barkodHtml = '';
        if (sevkiyat.barkodlar && Array.isArray(sevkiyat.barkodlar) && sevkiyat.barkodlar.length > 0) {
            barkodHtml = sevkiyat.barkodlar.map(b =>
                `<div class="barcode-tag">${escapeHtml(b)}</div>`
            ).join('');
        } else {
            barkodHtml = '<div style="color:#64748b; font-style:italic;">Barkod verisi bulunamadı / Genel Çıkış</div>';
        }

        const printWindow = window.open('', '_blank', 'width=800,height=900');
        // nosemgrep
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

                        table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
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
                                <div class="info-box-val" style="font-size: 24px;">🚚 ${tirPlaka}</div>
                                <div style="margin-top:10px; font-weight:600;">Çıkış Kapısı: ${depoKapi}</div>
                                <div style="margin-top:5px; font-weight:600;">Sipariş / Referans: ${siparisNo}</div>
                                <div style="margin-top:5px; font-weight:600;">İrsaliye No: ${irsaliyeNo}</div>
                            </div>
                            <div class="info-box">
                                <div class="info-box-title">İŞLEMİ YAPAN (DEPO PERSONELİ)</div>
                                <div class="info-box-val">👤 ${kullaniciAdi}</div>
                                <div style="margin-top:10px; font-weight:600;">Şoför: ${soforAdi}</div>
                                <div style="margin-top:5px; font-weight:600;">Taşıyıcı: ${tasiyiciFirma}</div>
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
                                        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">ID: ${sevkiyat.urun_id} • İşlem Tipi: O-CKS • Palet: ${paletNo}</div>
                                    </td>
                                    <td>${aciklama}</td>
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
                                <div style="margin-top: 5px;">${kullaniciAdi}</div>
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

            {/* Sayfa Başlığı */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
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
            </div>

            {/* Filtre Barı */}
            <div className="bg-white border border-slate-200 rounded-2xl p-3 sm:p-4 mb-5 sm:mb-6 shadow-sm">
                {/* Üst satır: Arama + Tarih aralığı + Sıfırla */}
                <div className="flex flex-col gap-2.5 sm:gap-3 lg:flex-row lg:items-center">
                    {/* Arama */}
                    <div className="relative flex-1 min-w-0">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Plaka, sipariş veya personel ara..."
                            value={aramaMetni}
                            onChange={(e) => setAramaMetni(e.target.value)}
                            className="w-full h-11 pl-11 pr-4 text-sm font-semibold rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-slate-700"
                        />
                    </div>

                    {/* Tarih Aralığı + Sıfırla */}
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                        {/* Tarih input'ları — mobilde alt alta, sm+ yan yana */}
                        <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-0 bg-slate-50/80 border border-slate-200 rounded-xl px-3 py-2.5 sm:py-0 sm:h-11">
                            <div className="flex items-center gap-2 sm:gap-1.5">
                                <Calendar className="w-4 h-4 text-slate-400 flex-shrink-0 sm:mr-0.5" />
                                <input
                                    type="date"
                                    value={tarihToInput(baslangicTarih)}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setBaslangicTarih(val ? gunBaslangici(new Date(val)) : null);
                                        setAktifHizliFiltre(null);
                                    }}
                                    className="bg-transparent text-sm font-semibold text-slate-700 outline-none w-full sm:w-[130px] cursor-pointer"
                                />
                            </div>
                            <span className="hidden sm:flex text-slate-300 font-bold text-xs px-1 items-center justify-center">—</span>
                            <div className="flex items-center gap-2 sm:gap-1.5">
                                <Calendar className="w-4 h-4 text-slate-400 flex-shrink-0 sm:hidden" />
                                <input
                                    type="date"
                                    value={tarihToInput(bitisTarih)}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setBitisTarih(val ? new Date(val) : null);
                                        setAktifHizliFiltre(null);
                                    }}
                                    className="bg-transparent text-sm font-semibold text-slate-700 outline-none w-full sm:w-[130px] cursor-pointer"
                                />
                            </div>
                        </div>

                        {/* Sıfırla Butonu */}
                        {filtreAktifMi && (
                            <button
                                onClick={filtreleriSifirla}
                                className="h-11 px-3.5 rounded-xl border border-red-200 bg-red-50 text-red-500 hover:bg-red-100 hover:border-red-300 transition-all flex items-center justify-center gap-1.5 flex-shrink-0"
                                title="Filtreleri sıfırla"
                            >
                                <RotateCcw className="w-4 h-4" />
                                <span className="text-xs font-bold">Sıfırla</span>
                            </button>
                        )}
                    </div>
                </div>

                {/* Alt satır: Hızlı filtre butonları + Sonuç göstergesi */}
                <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between mt-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <Filter className="w-3.5 h-3.5 text-slate-400 mr-0.5" />
                        {HIZLI_FILTRELER.map((filtre) => (
                            <button
                                key={filtre.key}
                                onClick={() => hizliFiltreSec(filtre)}
                                className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-[11px] sm:text-xs font-bold transition-all
                                    ${aktifHizliFiltre === filtre.key
                                        ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                                        : 'bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700'
                                    }`}
                            >
                                {filtre.etiket}
                            </button>
                        ))}
                    </div>

                    {/* Sonuç Göstergesi */}
                    {!loading && (
                        <div className="text-[11px] sm:text-xs font-semibold text-slate-400 flex items-center gap-1.5 flex-shrink-0">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
                            <span>
                                {filtrelenmisCikislar.length === cikislar.length
                                    ? <>{cikislar.length} kayıt</>
                                    : <><span className="text-blue-600 font-bold">{filtrelenmisCikislar.length}</span> / {cikislar.length} kayıt gösteriliyor</>
                                }
                            </span>
                        </div>
                    )}
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
                    {sayfadakiKayitlar.map((sevkiyat) => {
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
                                                        <span className="font-semibold text-slate-700 text-sm">{getKullaniciAdi(sevkiyat)}</span>
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
                                                        <span className="font-semibold text-slate-700 text-sm">{getRafKodu(sevkiyat)}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                                                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">İrsaliye No</span>
                                                    <span className="font-semibold text-slate-700 text-sm">{sevkiyat.irsaliye_no || '-'}</span>
                                                </div>
                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                                                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Palet No</span>
                                                    <span className="font-semibold text-slate-700 text-sm">{sevkiyat.palet_no || '-'}</span>
                                                </div>
                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                                                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Şoför</span>
                                                    <span className="font-semibold text-slate-700 text-sm">{sevkiyat.sofor_adi || '-'}</span>
                                                </div>
                                                <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                                                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Taşıyıcı Firma</span>
                                                    <span className="font-semibold text-slate-700 text-sm">{sevkiyat.tasiyici_firma || '-'}</span>
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

                    {/* Sayfalama */}
                    {toplamSayfa > 1 && (
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-5 sm:pt-6 pb-2">
                            <p className="text-xs sm:text-sm font-semibold text-slate-500 order-2 sm:order-1">
                                Toplam {filtrelenmisCikislar.length} kayıt, sayfa {mevcutSayfa}/{toplamSayfa}
                            </p>

                            <div className="flex items-center gap-1 sm:gap-1.5 order-1 sm:order-2">
                                <button
                                    onClick={() => setMevcutSayfa(s => Math.max(1, s - 1))}
                                    disabled={mevcutSayfa === 1}
                                    className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl flex items-center justify-center border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
                                >
                                    <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
                                </button>

                                {Array.from({ length: toplamSayfa }, (_, i) => i + 1)
                                    .filter(sayfa => {
                                        if (toplamSayfa <= 5) return true;
                                        if (sayfa === 1 || sayfa === toplamSayfa) return true;
                                        return Math.abs(sayfa - mevcutSayfa) <= 1;
                                    })
                                    .reduce((acc, sayfa, idx, arr) => {
                                        if (idx > 0 && sayfa - arr[idx - 1] > 1) {
                                            acc.push('ellipsis-' + sayfa);
                                        }
                                        acc.push(sayfa);
                                        return acc;
                                    }, [])
                                    .map((item) => {
                                        if (typeof item === 'string') {
                                            return (
                                                <span key={item} className="w-7 sm:w-10 h-9 sm:h-10 flex items-center justify-center text-slate-400 font-bold text-xs sm:text-sm">
                                                    ...
                                                </span>
                                            );
                                        }
                                        return (
                                            <button
                                                key={item}
                                                onClick={() => setMevcutSayfa(item)}
                                                className={`w-9 h-9 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl flex items-center justify-center font-bold text-xs sm:text-sm transition-all shadow-sm
                                                    ${mevcutSayfa === item
                                                        ? 'bg-blue-600 text-white border border-blue-600 shadow-md shadow-blue-500/20'
                                                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-blue-200'
                                                    }`}
                                            >
                                                {item}
                                            </button>
                                        );
                                    })}

                                <button
                                    onClick={() => setMevcutSayfa(s => Math.min(toplamSayfa, s + 1))}
                                    disabled={mevcutSayfa === toplamSayfa}
                                    className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl flex items-center justify-center border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
                                >
                                    <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
