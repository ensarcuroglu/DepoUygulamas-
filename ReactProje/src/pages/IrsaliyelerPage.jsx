import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Plus, Search, FileText, Loader2, X, Printer, AlertCircle, 
  ChevronRight, Truck, Package, Calendar
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getIrsaliyeler, createIrsaliye, updateIrsaliye, getSiparisler, getSevkiyatPlanlari
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRozetleri = {
  'Taslak': 'bg-slate-100 text-slate-700 ring-1 ring-slate-600/20',
  'Kesildi': 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20',
  'Gonderildi': 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20',
};

const belgeRozetleri = {
  'SevkIrsaliyesi': 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-600/20',
  'IadeIrsaliyesi': 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
};

const bugunTarihi = () => new Date().toISOString().split('T')[0];

const bosFormData = () => ({
  sevkiyat_id: '',
  siparis_id: '',
  irsaliye_tarihi: bugunTarihi(),
  belge_turu: 'SevkIrsaliyesi',
  tir_plaka: '',
  sofor_adi: '',
});

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 }
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { type: 'spring', duration: 0.5, bounce: 0.3 } },
  exit: { opacity: 0, scale: 0.95, y: 20, transition: { duration: 0.2 } }
};

export default function IrsaliyelerPage() {
  const { loading, run } = useAsync(true);
  const [irsaliyeler, setIrsaliyeler] = useState([]);
  const [siparisler, setSiparisler] = useState([]);
  const [sevkiyatPlanlari, setSevkiyatPlanlari] = useState([]);
  const [aramaMetni, setAramaMetni] = useState('');
  const [durumFiltre, setDurumFiltre] = useState('');
  
  const [yeniIrsaliyeModal, setYeniIrsaliyeModal] = useState(false);
  const [detayModal, setDetayModal] = useState(null);
  const [formData, setFormData] = useState(bosFormData);

  const siparisSozlugu = useMemo(() => {
    const map = new Map();
    siparisler.forEach(s => map.set(s.id, s));
    return map;
  }, [siparisler]);

  const planSozlugu = useMemo(() => {
    const map = new Map();
    sevkiyatPlanlari.forEach(p => map.set(p.id, p));
    return map;
  }, [sevkiyatPlanlari]);

  const verileriGetir = useCallback(async () => {
    return await run(() =>
      Promise.all([
        getIrsaliyeler({ limit: 100, durum: durumFiltre || undefined, arama: aramaMetni }),
        getSiparisler({ limit: 500 }),
        getSevkiyatPlanlari({ limit: 500 }),
      ])
    );
  }, [run, durumFiltre, aramaMetni]);

  const yukle = useCallback(async () => {
    const [irsRes, sipRes, planRes] = await verileriGetir();
    setIrsaliyeler(irsRes?.data || []);
    setSiparisler(sipRes?.data || []);
    setSevkiyatPlanlari(planRes?.data || []);
  }, [verileriGetir]);

  useEffect(() => {
    let isMounted = true;
    const baslangicYuklemesi = async () => {
      const [irsRes, sipRes, planRes] = await verileriGetir();
      if (isMounted) {
        setIrsaliyeler(irsRes?.data || []);
        setSiparisler(sipRes?.data || []);
        setSevkiyatPlanlari(planRes?.data || []);
      }
    };
    void baslangicYuklemesi();
    return () => { isMounted = false; };
  }, [verileriGetir]);

  const handlePlanSecimi = (planIdDegeri) => {
    const planId = parseInt(planIdDegeri, 10);
    if (!planId) {
      setFormData(bosFormData());
      return;
    }
    const plan = planSozlugu.get(planId);
    setFormData(onceki => ({
      ...onceki,
      sevkiyat_id: planId,
      siparis_id: plan?.siparis_id || '',
      tir_plaka: plan?.tir_plaka || '',
      sofor_adi: plan?.sofor_adi || '',
    }));
  };

  const handleYeniIrsaliye = async () => {
    if (!formData.sevkiyat_id || !formData.siparis_id) {
      toast.error('Lütfen geçerli bir sevkiyat planı seçin');
      return;
    }

    try {
      await createIrsaliye({
        siparis_id: Number(formData.siparis_id),
        sevkiyat_id: Number(formData.sevkiyat_id),
        irsaliye_tarihi: formData.irsaliye_tarihi,
        belge_turu: formData.belge_turu,
        tir_plaka: formData.tir_plaka || null,
        sofor_adi: formData.sofor_adi || null,
      });
      toast.success('İrsaliye başarıyla oluşturuldu');
      setYeniIrsaliyeModal(false);
      setFormData(bosFormData());
      void yukle();
    } catch (err) {
      toast.error(hataMetni(err, 'İrsaliye oluşturma başarısız'));
    }
  };

  const handleDurumDegis = async (irsaliyeId, yeniDurum) => {
    try {
      await updateIrsaliye(irsaliyeId, { durum: yeniDurum });
      toast.success('İrsaliye durumu güncellendi');
      void yukle();
      setDetayModal(null);
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  // EKSİK OLAN YAZDIRMA FONKSİYONU TAMAMEN GERİ EKLENDİ VE OPTİMİZE EDİLDİ
  const handleYazdir = (irsaliye) => {
    const siparis = siparisSozlugu.get(irsaliye.siparis_id);
    const isSevk = irsaliye.belge_turu === 'SevkIrsaliyesi';
    const belgeBaslik = isSevk ? 'SEVK İRSALİYESİ' : 'İADE İRSALİYESİ';
    const accentColor = isSevk ? '#1e40af' : '#b45309';

    const tarih = new Date(irsaliye.irsaliye_tarihi).toLocaleDateString('tr-TR', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
    const saat = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

    const htmlContent = `
      <!DOCTYPE html>
      <html lang="tr">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${belgeBaslik} - ${irsaliye.irsaliye_no}</title>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
          @page { size: A4; margin: 12mm 15mm; }
          * { box-sizing: border-box; }
          body { font-family: 'Inter', sans-serif; color: #0f172a; font-size: 11pt; line-height: 1.4; margin: 0; background: #fff; }
          .page-container { width: 100%; max-width: 800px; margin: 0 auto; }
          .header-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; border-bottom: 3px solid ${accentColor}; padding-bottom: 20px; margin-bottom: 30px; }
          .company-info h1 { margin: 0 0 5px 0; font-size: 18pt; font-weight: 800; letter-spacing: -0.5px; color: #0f172a; }
          .company-info p { margin: 2px 0; color: #475569; font-size: 9pt; }
          .document-meta { text-align: right; display: flex; flex-direction: column; align-items: flex-end; }
          .doc-type { font-size: 16pt; font-weight: 800; color: ${accentColor}; margin: 0 0 10px 0; letter-spacing: 1px; }
          .qr-placeholder { width: 70px; height: 70px; border: 1px dashed #94a3b8; display: flex; align-items: center; justify-content: center; font-size: 7pt; color: #94a3b8; text-align: center; }
          .info-blocks { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 30px; }
          .info-box { border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; background: #f8fafc; }
          .box-title { font-size: 8.5pt; font-weight: 700; text-transform: uppercase; color: ${accentColor}; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
          .data-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
          .data-label { font-size: 8.5pt; font-weight: 600; color: #64748b; }
          .data-value { font-size: 9pt; font-weight: 600; color: #0f172a; text-align: right; max-width: 65%; }
          .items-table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
          .items-table th { background-color: #f1f5f9; color: #334155; font-size: 8.5pt; font-weight: 700; text-transform: uppercase; padding: 10px 12px; text-align: left; border-top: 2px solid #cbd5e1; border-bottom: 2px solid #cbd5e1; }
          .items-table td { padding: 12px; font-size: 9.5pt; border-bottom: 1px solid #e2e8f0; color: #1e293b; }
          .items-table td.numeric { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
          .items-table tr:last-child td { border-bottom: 2px solid #cbd5e1; }
          .signatures-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 50px; page-break-inside: avoid; }
          .sign-box { border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; min-height: 120px; position: relative; }
          .sign-title { font-size: 8pt; font-weight: 700; color: #64748b; text-transform: uppercase; }
          .sign-name { font-size: 9pt; font-weight: 600; margin-top: 8px; color: #0f172a; }
          .sign-area { position: absolute; bottom: 12px; left: 12px; right: 12px; border-top: 1px dotted #94a3b8; padding-top: 4px; font-size: 7.5pt; color: #94a3b8; text-align: center; }
          .print-footer { margin-top: 40px; text-align: center; font-size: 7.5pt; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 12px; }
          @media print { body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } .info-box { background: #f8fafc !important; } .items-table th { background-color: #f1f5f9 !important; } }
        </style>
      </head>
      <body>
        <div class="page-container">
          <div class="header-grid">
            <div class="company-info">
              <h1>OPTİMAK ENDÜSTRİ VE TEKNOLOJİ A.Ş.</h1>
              <p>Otomotiv İhtisas OSB, 1. Cadde No: 5, Merkez / Türkiye</p>
              <p>Vergi Dairesi: Kurumlar VD. | VKN: 123 456 7890</p>
              <p>Mersis No: 0123456789000001 | Ticaret Sicil No: 12345</p>
            </div>
            <div class="document-meta">
              <h2 class="doc-type">${belgeBaslik}</h2>
              <div class="qr-placeholder">Karekod<br>Alanı</div>
            </div>
          </div>
          <div class="info-blocks">
            <div class="info-box">
              <div class="box-title">Alıcı Bilgileri</div>
              <div class="data-row"><span class="data-label">Müşteri/Unvan:</span><span class="data-value">${siparis?.musteri_adi || '-'}</span></div>
              <div class="data-row"><span class="data-label">Teslimat Adresi:</span><span class="data-value">${siparis?.teslimat_adresi || '-'}</span></div>
            </div>
            <div class="info-box">
              <div class="box-title">Belge Detayları</div>
              <div class="data-row"><span class="data-label">İrsaliye No:</span><span class="data-value">${irsaliye.irsaliye_no}</span></div>
              <div class="data-row"><span class="data-label">Fiili Sevk Tarihi:</span><span class="data-value">${tarih}</span></div>
              <div class="data-row"><span class="data-label">Sipariş No:</span><span class="data-value">${siparis?.siparis_no || '-'}</span></div>
            </div>
          </div>
          <div class="info-blocks" style="margin-bottom: 20px;">
            <div class="info-box" style="grid-column: 1 / -1; display: flex; justify-content: space-between;">
              <div><span class="data-label">Taşıyıcı / Şoför:</span><span class="data-value" style="margin-left: 10px;">${irsaliye.sofor_adi || '-'}</span></div>
              <div><span class="data-label">Araç Plakası:</span><span class="data-value" style="margin-left: 10px;">${irsaliye.tir_plaka || '-'}</span></div>
              <div><span class="data-label">Durum:</span><span class="data-value" style="margin-left: 10px;">${irsaliye.durum}</span></div>
            </div>
          </div>
          <table class="items-table">
            <thead>
              <tr>
                <th style="width: 5%;">#</th>
                <th style="width: 20%;">KOD</th>
                <th style="width: 45%;">ÜRÜN CİNSİ / AÇIKLAMA</th>
                <th style="width: 15%; text-align: right;">MİKTAR</th>
                <th style="width: 15%; text-align: right;">BİRİM</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>1</td>
                <td style="color: #64748b; font-size: 8.5pt;">GEN-001</td>
                <td><strong>Sipariş Kapsamındaki Ürünler</strong><br><span style="font-size: 8pt; color: #64748b;">(Detaylı malzeme dökümü faturada belirtilecektir)</span></td>
                <td class="numeric">1,00</td>
                <td class="numeric">Adet/Set</td>
              </tr>
            </tbody>
          </table>
          <div class="signatures-grid">
            <div class="sign-box">
              <div class="sign-title">Düzenleyen</div>
              <div class="sign-name">Sistem Kullanıcısı</div>
              <div class="sign-area">Kaşe / İmza</div>
            </div>
            <div class="sign-box">
              <div class="sign-title">Taşıyıcı / Teslim Eden</div>
              <div class="sign-name">${irsaliye.sofor_adi || 'Şoför Adı'}</div>
              <div class="sign-area">İmza</div>
            </div>
            <div class="sign-box">
              <div class="sign-title">Teslim Alan</div>
              <div class="sign-name">${siparis?.musteri_adi || 'Müşteri'}</div>
              <div class="sign-area">Kaşe / İmza / Tarih</div>
            </div>
          </div>
          <div class="print-footer">
            İşbu belge 213 sayılı V.U.K. hükümlerine göre düzenlenmiştir. Elektronik ortamda üretilmiş olup, irsaliye yerine geçer.<br>
            Sistem Yazdırma Zamanı: ${tarih} - ${saat}
          </div>
        </div>
      </body>
      </html>
    `;

    const newWindow = window.open('', '_blank');
    if (!newWindow) {
      toast.error('Yazdırma penceresi açılamadı. Lütfen pop-up engelleyiciyi kontrol edin.');
      return;
    }
    newWindow.document.write(htmlContent);
    newWindow.document.close();

    setTimeout(() => {
      newWindow.focus();
      newWindow.print();
    }, 400);
  };

  const filtrelenmisVeri = useMemo(() => {
    const filtre = aramaMetni.trim().toLowerCase();
    
    return irsaliyeler
      .map(irs => ({
        ...irs,
        siparis: siparisSozlugu.get(irs.siparis_id),
        sevkiyat: planSozlugu.get(irs.sevkiyat_id)
      }))
      .filter(irsaliye => {
        if (!filtre) return true;
        const aranacak = [
          irsaliye.irsaliye_no,
          irsaliye.siparis?.siparis_no,
          irsaliye.siparis?.musteri_adi,
          irsaliye.tir_plaka
        ].join(' ').toLowerCase();
        return aranacak.includes(filtre);
      });
  }, [irsaliyeler, siparisSozlugu, planSozlugu, aramaMetni]);

  const kullanilabilirPlanlar = useMemo(() => {
    const irsaliyesiKesilenPlanIdler = new Set(irsaliyeler.map(i => i.sevkiyat_id));
    return sevkiyatPlanlari.filter(plan => !irsaliyesiKesilenPlanIdler.has(plan.id));
  }, [sevkiyatPlanlari, irsaliyeler]);

  const seciliPlan = planSozlugu.get(Number(formData.sevkiyat_id));
  const seciliSiparis = siparisSozlugu.get(Number(formData.siparis_id));

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">İrsaliyeler</h1>
          <p className="mt-1 text-sm text-slate-500">Tüm sevk ve iade irsaliyelerini buradan yönetin.</p>
        </div>
        <button
          onClick={() => setYeniIrsaliyeModal(true)}
          className="group flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-700 hover:shadow-md active:scale-[0.98]"
        >
          <Plus className="h-4 w-4 transition-transform group-hover:rotate-90" />
          Yeni İrsaliye
        </button>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-12">
        <div className="relative md:col-span-8 lg:col-span-9">
          <Search className="absolute left-3.5 top-3 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="İrsaliye no, sipariş, müşteri veya plaka ara..."
            value={aramaMetni}
            onChange={(e) => setAramaMetni(e.target.value)}
            className="w-full rounded-xl border-0 bg-white py-2.5 pl-10 pr-4 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-inset ring-slate-200 transition-all placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-blue-600"
          />
        </div>
        <div className="md:col-span-4 lg:col-span-3">
          <select
            value={durumFiltre}
            onChange={(e) => setDurumFiltre(e.target.value)}
            className="w-full rounded-xl border-0 bg-white py-2.5 pl-4 pr-10 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-inset ring-slate-200 transition-all focus:ring-2 focus:ring-inset focus:ring-blue-600"
          >
            <option value="">Tüm Durumlar</option>
            <option value="Taslak">Taslak</option>
            <option value="Kesildi">Kesildi</option>
            <option value="Gonderildi">Gönderildi</option>
          </select>
        </div>
      </div>

      {filtrelenmisVeri.length === 0 ? (
        <motion.div 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm"
        >
          <div className="mb-4 rounded-full bg-slate-50 p-4 ring-1 ring-slate-100">
            <FileText className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Kayıt Bulunamadı</h3>
          <p className="mt-1 text-sm text-slate-500">Arama kriterlerinize uygun irsaliye belgesi yok.</p>
        </motion.div>
      ) : (
        <>
          <div className="hidden overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm md:block">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">İrsaliye Detayı</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Sipariş / Müşteri</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Lojistik</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Durum</th>
                  <th scope="col" className="relative px-6 py-3"><span className="sr-only">Aksiyonlar</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filtrelenmisVeri.map((irsaliye) => (
                  <motion.tr 
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    key={irsaliye.id} className="transition-colors hover:bg-slate-50/50"
                  >
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <div className="font-semibold text-slate-900">{irsaliye.irsaliye_no}</div>
                      </div>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-xs text-slate-500">{irsaliye.irsaliye_tarihi}</span>
                        <span className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-medium ${belgeRozetleri[irsaliye.belge_turu]}`}>
                          {irsaliye.belge_turu === 'SevkIrsaliyesi' ? 'Sevkiyat' : 'İade'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-900">{irsaliye.siparis?.musteri_adi || 'Bilinmeyen Müşteri'}</div>
                      <div className="text-xs text-slate-500">{irsaliye.siparis?.siparis_no || `#${irsaliye.siparis_id}`}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <div className="flex items-center gap-1.5 text-slate-700">
                        <Truck className="h-3.5 w-3.5 text-slate-400" />
                        {irsaliye.tir_plaka || 'Plaka Yok'}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">{irsaliye.sofor_adi || 'Şoför Belirtilmedi'}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${durumRozetleri[irsaliye.durum]}`}>
                        {irsaliye.durum}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => setDetayModal(irsaliye)} className="text-slate-400 hover:text-blue-600 transition-colors" title="Detaylar">
                          <ChevronRight className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 gap-4 md:hidden">
            {filtrelenmisVeri.map((irsaliye) => (
              <motion.div 
                initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
                key={irsaliye.id} 
                className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="mb-3 flex items-center justify-between">
                  <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${durumRozetleri[irsaliye.durum]}`}>
                    {irsaliye.durum}
                  </span>
                  <span className="text-xs font-medium text-slate-500">{irsaliye.irsaliye_tarihi}</span>
                </div>
                <div className="mb-1 text-lg font-bold text-slate-900">{irsaliye.irsaliye_no}</div>
                <div className="mb-4 text-sm text-slate-600 line-clamp-1">{irsaliye.siparis?.musteri_adi}</div>
                
                <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Package className="h-3.5 w-3.5" /> {irsaliye.siparis?.siparis_no}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Truck className="h-3.5 w-3.5" /> {irsaliye.tir_plaka || '-'}
                    </div>
                  </div>
                  <button 
                    onClick={() => setDetayModal(irsaliye)}
                    className="flex h-8 items-center justify-center rounded-lg bg-slate-50 px-3 text-xs font-semibold text-slate-700 ring-1 ring-inset ring-slate-200 hover:bg-slate-100"
                  >
                    Yönet
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </>
      )}

      <AnimatePresence>
        {yeniIrsaliyeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
            <motion.div 
              variants={overlayVariants} initial="hidden" animate="visible" exit="hidden"
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" 
              onClick={() => setYeniIrsaliyeModal(false)} 
            />
            
            <motion.div 
              variants={modalVariants} initial="hidden" animate="visible" exit="exit"
              className="relative w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-200"
            >
              <div className="border-b border-slate-100 bg-slate-50/50 px-6 py-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Yeni İrsaliye Düzenle</h2>
                <button onClick={() => setYeniIrsaliyeModal(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="px-6 py-5 max-h-[70vh] overflow-y-auto">
                <div className="mb-5 flex gap-3 rounded-xl bg-blue-50 p-4 text-sm text-blue-800 ring-1 ring-blue-600/20">
                  <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
                  <p>İrsaliyeler artık siparişten bağımsız, onaylanmış sevkiyat planları üzerinden kesilmektedir.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700 uppercase tracking-wide">Sevkiyat Planı *</label>
                    <select
                      value={formData.sevkiyat_id}
                      onChange={(e) => handlePlanSecimi(e.target.value)}
                      className="block w-full rounded-xl border-0 bg-slate-50 py-3 px-4 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-inset focus:ring-blue-600"
                    >
                      <option value="">Seçiniz...</option>
                      {kullanilabilirPlanlar.map((plan) => {
                        const siparis = siparisSozlugu.get(plan.siparis_id);
                        return (
                          <option key={plan.id} value={plan.id}>
                            PLN-{plan.id} | {siparis?.musteri_adi}
                          </option>
                        );
                      })}
                    </select>
                  </div>

                  {seciliPlan && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-xs text-slate-500">Sipariş No</p>
                          <p className="font-medium text-slate-900">{seciliSiparis?.siparis_no}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500">Yükleme</p>
                          <p className="font-medium text-slate-900">{seciliPlan.yukleme_tarihi}</p>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1.5 block text-xs font-semibold text-slate-700 uppercase tracking-wide">Belge Türü</label>
                      <select
                        value={formData.belge_turu}
                        onChange={(e) => setFormData({ ...formData, belge_turu: e.target.value })}
                        className="block w-full rounded-xl border-0 bg-slate-50 py-3 px-4 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-blue-600"
                      >
                        <option value="SevkIrsaliyesi">Sevk İrsaliyesi</option>
                        <option value="IadeIrsaliyesi">İade İrsaliyesi</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-1.5 block text-xs font-semibold text-slate-700 uppercase tracking-wide">Tarih</label>
                      <input
                        type="date"
                        value={formData.irsaliye_tarihi}
                        onChange={(e) => setFormData({ ...formData, irsaliye_tarihi: e.target.value })}
                        className="block w-full rounded-xl border-0 bg-slate-50 py-3 px-4 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-blue-600"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-1.5 block text-xs font-semibold text-slate-700 uppercase tracking-wide">Araç Plaka</label>
                      <input
                        type="text" placeholder="Örn: 34 ABC 123"
                        value={formData.tir_plaka}
                        onChange={(e) => setFormData({ ...formData, tir_plaka: e.target.value })}
                        className="block w-full rounded-xl border-0 bg-slate-50 py-3 px-4 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-blue-600"
                      />
                    </div>
                    <div>
                      <label className="mb-1.5 block text-xs font-semibold text-slate-700 uppercase tracking-wide">Şoför Adı</label>
                      <input
                        type="text" placeholder="Ad Soyad"
                        value={formData.sofor_adi}
                        onChange={(e) => setFormData({ ...formData, sofor_adi: e.target.value })}
                        className="block w-full rounded-xl border-0 bg-slate-50 py-3 px-4 text-sm text-slate-900 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-blue-600"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 px-6 py-4 flex items-center justify-end gap-3 border-t border-slate-100">
                <button
                  onClick={() => setYeniIrsaliyeModal(false)}
                  className="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-200 transition"
                >
                  İptal
                </button>
                <button
                  onClick={handleYeniIrsaliye}
                  className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition"
                >
                  Belgeyi Oluştur
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {detayModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
            <motion.div 
              variants={overlayVariants} initial="hidden" animate="visible" exit="hidden"
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" 
              onClick={() => setDetayModal(null)} 
            />
            
            <motion.div 
              variants={modalVariants} initial="hidden" animate="visible" exit="exit"
              className="relative w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-200"
            >
              <div className="border-b border-slate-100 bg-slate-50/50 px-6 py-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">{detayModal.irsaliye_no}</h2>
                  <p className="text-xs text-slate-500">İrsaliye Detayları ve Yönetimi</p>
                </div>
                <button onClick={() => setDetayModal(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="px-6 py-5">
                <div className="mb-6 grid grid-cols-2 gap-y-4 gap-x-6">
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Durum</p>
                    <div className="mt-1">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${durumRozetleri[detayModal.durum]}`}>
                        {detayModal.durum}
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Tarih</p>
                    <p className="mt-1 text-sm font-medium text-slate-900 flex items-center gap-1.5">
                      <Calendar className="h-4 w-4 text-slate-400" /> {detayModal.irsaliye_tarihi}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Müşteri / Alıcı</p>
                    <p className="mt-1 text-sm font-medium text-slate-900">{detayModal.siparis?.musteri_adi || '-'}</p>
                    <p className="text-xs text-slate-500">{detayModal.siparis?.teslimat_adresi || '-'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Araç & Şoför</p>
                    <p className="mt-1 text-sm font-medium text-slate-900">{detayModal.tir_plaka || '-'}</p>
                    <p className="text-xs text-slate-500">{detayModal.sofor_adi || '-'}</p>
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-100 flex flex-col gap-3">
                  <p className="text-xs font-semibold text-slate-700 uppercase">Hızlı İşlemler</p>
                  <div className="flex gap-2">
                    {detayModal.durum === 'Taslak' && (
                      <button
                        onClick={() => handleDurumDegis(detayModal.id, 'Kesildi')}
                        className="flex-1 rounded-lg bg-blue-100 px-3 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-200 transition"
                      >
                        İrsaliyeyi Kes
                      </button>
                    )}
                    {detayModal.durum === 'Kesildi' && (
                      <button
                        onClick={() => handleDurumDegis(detayModal.id, 'Gonderildi')}
                        className="flex-1 rounded-lg bg-emerald-100 px-3 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-200 transition"
                      >
                        Yola Çıktı İşaretle
                      </button>
                    )}
                    <button
                      onClick={() => handleYazdir(detayModal)}
                      className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700 transition shadow-sm"
                    >
                      <Printer className="h-4 w-4" /> Yazdır
                    </button>
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