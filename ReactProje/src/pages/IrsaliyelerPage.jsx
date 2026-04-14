import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, FileText, Loader2, X, Printer, AlertCircle
} from 'lucide-react';
import {
  getIrsaliyeler, createIrsaliye, updateIrsaliye, getSiparisler, getSevkiyatPlanlari
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
  'Taslak': 'bg-slate-100 text-slate-800 border border-slate-300',
  'Kesildi': 'bg-blue-100 text-blue-800 border border-blue-300',
  'Gonderildi': 'bg-emerald-100 text-emerald-800 border border-emerald-300',
};

const belgeRenkleri = {
  'SevkIrsaliyesi': 'bg-blue-50 text-blue-900',
  'IadeIrsaliyesi': 'bg-orange-50 text-orange-900',
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

  const siparisBul = useCallback(
    (siparisId) => {
      if (!siparisId) {
        return null;
      }
      return siparisler.find((siparis) => siparis.id === siparisId) || null;
    },
    [siparisler]
  );

  const planBul = useCallback(
    (planId) => {
      if (!planId) {
        return null;
      }
      return sevkiyatPlanlari.find((plan) => plan.id === planId) || null;
    },
    [sevkiyatPlanlari]
  );

  const detayliIrsaliyeOlustur = useCallback(
    (irsaliye) => ({
      ...irsaliye,
      siparis: siparisBul(irsaliye.siparis_id),
      sevkiyat: planBul(irsaliye.sevkiyat_id),
    }),
    [planBul, siparisBul]
  );

  // 1. Sadece veri çekme işini yapan (state değiştirmeyen) saf fonksiyon
const verileriGetir = useCallback(async () => {
  return await run(() =>
    Promise.all([
      getIrsaliyeler({ limit: 100, durum: durumFiltre || undefined, arama: aramaMetni }),
      getSiparisler({ limit: 500 }),
      getSevkiyatPlanlari({ limit: 500 }),
    ])
  );
}, [run, durumFiltre, aramaMetni]);

// 2. Buton tıklamaları (Yeni İrsaliye, Durum Değiştirme vb.) için manuel tetikleyici
const yükle = useCallback(async () => {
  const [irsRes, sipRes, planRes] = await verileriGetir();
  setIrsaliyeler(irsRes?.data || []);
  setSiparisler(sipRes?.data || []);
  setSevkiyatPlanlari(planRes?.data || []);
}, [verileriGetir]);

// 3. Effect içindeki doğru ve güvenli veri çekme paterni
useEffect(() => {
  let isMounted = true; // Bileşen unmount olursa state güncellenmesini engellemek için

  const baslangicYuklemesi = async () => {
    const [irsRes, sipRes, planRes] = await verileriGetir();

    // Sadece bileşen hala ekrandaysa state'i güncelle (Memory leak'i önler ve linter'ı susturur)
    if (isMounted) {
      setIrsaliyeler(irsRes?.data || []);
      setSiparisler(sipRes?.data || []);
      setSevkiyatPlanlari(planRes?.data || []);
    }
  };

  void baslangicYuklemesi();

  return () => {
    isMounted = false; // Cleanup: Component DOM'dan silinirse bayrağı indir
  };
}, [verileriGetir]);

  const handlePlanSecimi = (planIdDegeri) => {
    const planId = parseInt(planIdDegeri, 10);

    if (!planId) {
      setFormData((onceki) => ({
        ...onceki,
        sevkiyat_id: '',
        siparis_id: '',
        tir_plaka: '',
        sofor_adi: '',
      }));
      return;
    }

    const plan = planBul(planId);
    setFormData((onceki) => ({
      ...onceki,
      sevkiyat_id: planId,
      siparis_id: plan?.siparis_id || '',
      tir_plaka: plan?.tir_plaka || '',
      sofor_adi: plan?.sofor_adi || '',
    }));
  };

  const handleYeniIrsaliye = async () => {
    if (!formData.sevkiyat_id) {
      toast.error('Lütfen bir sevkiyat planı seçin');
      return;
    }

    if (!formData.siparis_id) {
      toast.error('Seçilen sevkiyat planının sipariş bilgisi bulunamadı');
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
      toast.success('İrsaliye oluşturuldu');
      setYeniIrsaliyeModal(false);
      setFormData(bosFormData());
      void yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'İrsaliye oluşturma başarısız'));
    }
  };

  const handleDurumDegis = async (irsaliyeId, yeniDurum) => {
    try {
      await updateIrsaliye(irsaliyeId, { durum: yeniDurum });
      toast.success('Durum güncellendi');
      void yükle();
      setDetayModal(null);
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  const handleYazdir = (irsaliye) => {
    const detayliIrsaliye = detayliIrsaliyeOlustur(irsaliye);
    const siparis = detayliIrsaliye.siparis;
    const isSevk = irsaliye.belge_turu === 'SevkIrsaliyesi';
    const belgeBaslik = isSevk ? 'SEVK İRSALİYESİ' : 'İADE İRSALİYESİ';
    const accentColor = isSevk ? '#1e40af' : '#b45309'; // Kurumsal lacivert veya kiremit

    // Tarih formatlama
    const tarih = new Date(detayliIrsaliye.irsaliye_tarihi).toLocaleDateString('tr-TR', {
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
          
          /* A4 ve Genel Baskı Ayarları */
          @page { size: A4; margin: 12mm 15mm; }
          * { box-sizing: border-box; }
          body { 
            font-family: 'Inter', sans-serif; 
            color: #0f172a; 
            font-size: 11pt; 
            line-height: 1.4; 
            margin: 0; 
            background: #fff;
          }
          .page-container { width: 100%; max-width: 800px; margin: 0 auto; }
          
          /* Üst Başlık ve Logo Alanı */
          .header-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            border-bottom: 3px solid ${accentColor};
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .company-info h1 { 
            margin: 0 0 5px 0; 
            font-size: 18pt; 
            font-weight: 800; 
            letter-spacing: -0.5px;
            color: #0f172a;
          }
          .company-info p { margin: 2px 0; color: #475569; font-size: 9pt; }
          .document-meta { text-align: right; display: flex; flex-direction: column; align-items: flex-end; }
          .doc-type { 
            font-size: 16pt; 
            font-weight: 800; 
            color: ${accentColor}; 
            margin: 0 0 10px 0; 
            letter-spacing: 1px;
          }
          .qr-placeholder {
            width: 70px; height: 70px;
            border: 1px dashed #94a3b8;
            display: flex; align-items: center; justify-content: center;
            font-size: 7pt; color: #94a3b8; text-align: center;
          }

          /* Adres ve Ana Bilgi Blokları */
          .info-blocks {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 30px;
          }
          .info-box {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 12px 16px;
            background: #f8fafc;
          }
          .box-title {
            font-size: 8.5pt;
            font-weight: 700;
            text-transform: uppercase;
            color: ${accentColor};
            margin-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
          }
          .data-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
          .data-label { font-size: 8.5pt; font-weight: 600; color: #64748b; }
          .data-value { font-size: 9pt; font-weight: 600; color: #0f172a; text-align: right; max-width: 65%; }

          /* Kalemler Tablosu */
          .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 40px;
          }
          .items-table th {
            background-color: #f1f5f9;
            color: #334155;
            font-size: 8.5pt;
            font-weight: 700;
            text-transform: uppercase;
            padding: 10px 12px;
            text-align: left;
            border-top: 2px solid #cbd5e1;
            border-bottom: 2px solid #cbd5e1;
          }
          .items-table td {
            padding: 12px;
            font-size: 9.5pt;
            border-bottom: 1px solid #e2e8f0;
            color: #1e293b;
          }
          .items-table td.numeric { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
          .items-table tr:last-child td { border-bottom: 2px solid #cbd5e1; }

          /* Teslimat ve İmzalar */
          .signatures-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 50px;
            page-break-inside: avoid;
          }
          .sign-box {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 12px;
            min-height: 120px;
            position: relative;
          }
          .sign-title { font-size: 8pt; font-weight: 700; color: #64748b; text-transform: uppercase; }
          .sign-name { font-size: 9pt; font-weight: 600; margin-top: 8px; color: #0f172a; }
          .sign-area { 
            position: absolute; bottom: 12px; left: 12px; right: 12px; 
            border-top: 1px dotted #94a3b8; 
            padding-top: 4px; font-size: 7.5pt; color: #94a3b8; text-align: center; 
          }

          /* Footer Notu */
          .print-footer {
            margin-top: 40px;
            text-align: center;
            font-size: 7.5pt;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            padding-top: 12px;
          }

          /* Yazıcı Optimizasyonu */
          @media print {
            body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
            .info-box { background: #f8fafc !important; }
            .items-table th { background-color: #f1f5f9 !important; }
          }
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
              <div class="data-row">
                <span class="data-label">Müşteri/Unvan:</span>
                <span class="data-value">${siparis?.musteri_adi || '-'}</span>
              </div>
              <div class="data-row">
                <span class="data-label">Teslimat Adresi:</span>
                <span class="data-value">${siparis?.teslimat_adresi || '-'}</span>
              </div>
            </div>

            <div class="info-box">
              <div class="box-title">Belge Detayları</div>
              <div class="data-row">
                <span class="data-label">İrsaliye No:</span>
                <span class="data-value">${irsaliye.irsaliye_no}</span>
              </div>
              <div class="data-row">
                <span class="data-label">Fiili Sevk Tarihi:</span>
                <span class="data-value">${tarih}</span>
              </div>
              <div class="data-row">
                <span class="data-label">Sipariş No:</span>
                <span class="data-value">${siparis?.siparis_no || '-'}</span>
              </div>
            </div>
          </div>

          <div class="info-blocks" style="margin-bottom: 20px;">
            <div class="info-box" style="grid-column: 1 / -1; display: flex; justify-content: space-between;">
              <div>
                <span class="data-label">Taşıyıcı / Şoför:</span>
                <span class="data-value" style="margin-left: 10px;">${detayliIrsaliye.sofor_adi || '-'}</span>
              </div>
              <div>
                <span class="data-label">Araç Plakası:</span>
                <span class="data-value" style="margin-left: 10px;">${detayliIrsaliye.tir_plaka || '-'}</span>
              </div>
              <div>
                <span class="data-label">Durum:</span>
                <span class="data-value" style="margin-left: 10px;">${detayliIrsaliye.durum}</span>
              </div>
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
                <td>
                  <strong>Sipariş Kapsamındaki Ürünler</strong><br>
                  <span style="font-size: 8pt; color: #64748b;">(Detaylı malzeme dökümü faturada belirtilecektir)</span>
                </td>
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
              <div class="sign-name">${detayliIrsaliye.sofor_adi || 'Şoför Adı'}</div>
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
      toast.error('Yazdırma penceresi açılamadı');
      return;
    }
    newWindow.document.write(htmlContent);
    newWindow.document.close();

    // Fontların ve stillerin tarayıcı tarafından işlenmesi için kısa bekleme
    setTimeout(() => {
      newWindow.focus();
      newWindow.print();
    }, 400);
  };

  const filtreMetni = aramaMetni.trim().toLowerCase();
  const kullanilabilirPlanlar = sevkiyatPlanlari.filter(
    (plan) => !irsaliyeler.some((irsaliye) => irsaliye.sevkiyat_id === plan.id)
  );
  const seciliPlan = planBul(formData.sevkiyat_id);
  const seciliSiparis = siparisBul(formData.siparis_id);
  const filtrelenmis = irsaliyeler
    .map(detayliIrsaliyeOlustur)
    .filter((irsaliye) => {
      if (!filtreMetni) {
        return true;
      }

      const alanlar = [
        irsaliye.irsaliye_no,
        irsaliye.siparis?.siparis_no,
        irsaliye.siparis?.musteri_adi,
        irsaliye.tir_plaka,
      ];

      return alanlar.some((alan) => (alan || '').toLowerCase().includes(filtreMetni));
    });

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Başlık */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-900">İrsaliyeler</h1>
        <button
          onClick={() => setYeniIrsaliyeModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          <Plus className="h-5 w-5" /> Yeni İrsaliye
        </button>
      </div>

      {/* Arama ve Filtreler */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="İrsaliye no veya sipariş ara..."
            value={aramaMetni}
            onChange={(e) => setAramaMetni(e.target.value)}
            className="h-12 pl-10 pr-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
          />
        </div>
        <select
          value={durumFiltre}
          onChange={(e) => setDurumFiltre(e.target.value)}
          className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
        >
          <option value="">Tüm Durumlar</option>
          <option value="Taslak">Taslak</option>
          <option value="Kesildi">Kesildi</option>
          <option value="Gonderildi">Gönderildi</option>
        </select>
      </div>

      {/* İrsaliyeler Listesi */}
      {filtrelenmis.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center">
          <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">İrsaliye bulunamadı</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtrelenmis.map((irsaliye) => (
            <div
              key={irsaliye.id}
              className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-slate-900">{irsaliye.irsaliye_no}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${durumRenkleri[irsaliye.durum]}`}>
                      {irsaliye.durum}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${belgeRenkleri[irsaliye.belge_turu]}`}>
                      {irsaliye.belge_turu === 'SevkIrsaliyesi' ? 'Sevkiyat' : 'İade'}
                    </span>
                  </div>
                  <p className="text-slate-600 text-sm">
                    {irsaliye.siparis?.musteri_adi || 'Müşteri bilgisi yok'} - {irsaliye.siparis?.siparis_no || `Sipariş #${irsaliye.siparis_id}`}
                  </p>
                </div>
                <button
                  onClick={() => handleYazdir(irsaliye)}
                  className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition"
                  title="Yazdır"
                >
                  <Printer className="h-5 w-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-4">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">İrsaliye Tarihi</p>
                  <p className="text-slate-900 font-semibold">{irsaliye.irsaliye_tarihi}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Tır Plakası</p>
                  <p className="text-slate-900 font-semibold">{irsaliye.tir_plaka || '-'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Şoför</p>
                  <p className="text-slate-900 font-semibold">{irsaliye.sofor_adi || '-'}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Oluş. Tarihi</p>
                  <p className="text-slate-900 font-semibold">
                    {new Date(irsaliye.olusturma_tarihi).toLocaleDateString('tr-TR')}
                  </p>
                </div>
              </div>

              {/* Durum Butonları */}
              {irsaliye.durum !== 'Gonderildi' && (
                <div className="flex gap-2">
                  {irsaliye.durum === 'Taslak' && (
                    <button
                      onClick={() => handleDurumDegis(irsaliye.id, 'Kesildi')}
                      className="px-4 py-2 rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 font-semibold text-sm transition"
                    >
                      Kes
                    </button>
                  )}
                  {irsaliye.durum === 'Kesildi' && (
                    <button
                      onClick={() => handleDurumDegis(irsaliye.id, 'Gonderildi')}
                      className="px-4 py-2 rounded-lg bg-emerald-100 text-emerald-600 hover:bg-emerald-200 font-semibold text-sm transition"
                    >
                      Gönderildi
                    </button>
                  )}
                  <button
                    onClick={() => setDetayModal(detayliIrsaliyeOlustur(irsaliye))}
                    className="ml-auto px-4 py-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 font-semibold text-sm transition"
                  >
                    Detay
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Yeni İrsaliye Modal */}
      {yeniIrsaliyeModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900">Yeni İrsaliye</h2>
              <button
                onClick={() => setYeniIrsaliyeModal(false)}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="flex items-start gap-3 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
                <p>
                  İrsaliye artık doğrudan siparişten değil, seçilmiş bir sevkiyat planından oluşturuluyor.
                  Aynı sevkiyat planı için ikinci bir irsaliye seçilemez.
                </p>
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-600 uppercase mb-2">
                  Sevkiyat Planı * (Zorunlu)
                </label>
                <select
                  value={formData.sevkiyat_id}
                  onChange={(e) => handlePlanSecimi(e.target.value)}
                  className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                >
                  <option value="">Sevkiyat Planı Seçin</option>
                  {kullanilabilirPlanlar.map((plan) => {
                    const siparis = siparisBul(plan.siparis_id);
                    return (
                      <option key={plan.id} value={plan.id}>
                        #{plan.id} - {siparis?.siparis_no || `Sipariş #${plan.siparis_id}`} - {siparis?.musteri_adi || 'Müşteri bilgisi yok'}
                      </option>
                    );
                  })}
                </select>
                {kullanilabilirPlanlar.length === 0 && (
                  <p className="mt-2 text-sm text-slate-500">
                    Kullanılabilir sevkiyat planı bulunmuyor. Önce yeni bir sevkiyat planı oluşturun veya mevcut irsaliyeleri kontrol edin.
                  </p>
                )}
              </div>

              {seciliPlan && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="mb-3 text-sm font-bold text-slate-700">Seçili Plan Özeti</p>
                  <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Sipariş</p>
                      <p className="font-semibold text-slate-900">
                        {seciliSiparis?.siparis_no || `Sipariş #${seciliPlan.siparis_id}`}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Müşteri</p>
                      <p className="font-semibold text-slate-900">{seciliSiparis?.musteri_adi || 'Müşteri bilgisi yok'}</p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Yükleme Tarihi</p>
                      <p className="font-semibold text-slate-900">{seciliPlan.yukleme_tarihi || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase text-slate-500">Durum</p>
                      <p className="font-semibold text-slate-900">{seciliPlan.durum}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <input
                  type="date"
                  value={formData.irsaliye_tarihi}
                  onChange={(e) => setFormData({ ...formData, irsaliye_tarihi: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <select
                  value={formData.belge_turu}
                  onChange={(e) => setFormData({ ...formData, belge_turu: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                >
                  <option value="SevkIrsaliyesi">Sevkiyat İrsaliyesi</option>
                  <option value="IadeIrsaliyesi">İade İrsaliyesi</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Tır Plakası"
                  value={formData.tir_plaka}
                  onChange={(e) => setFormData({ ...formData, tir_plaka: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <input
                  type="text"
                  placeholder="Şoför Adı"
                  value={formData.sofor_adi}
                  onChange={(e) => setFormData({ ...formData, sofor_adi: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
              </div>
            </div>

            <div className="border-t border-slate-200 p-6 flex gap-3">
              <button
                onClick={() => setYeniIrsaliyeModal(false)}
                className="flex-1 h-12 rounded-xl border-2 border-slate-200 text-slate-900 font-bold hover:bg-slate-100 transition"
              >
                İptal
              </button>
              <button
                onClick={handleYeniIrsaliye}
                className="flex-1 h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
              >
                Oluştur
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detay Modal */}
      {detayModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900">{detayModal.irsaliye_no}</h2>
              <button
                onClick={() => setDetayModal(null)}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Belge Türü</p>
                  <p className="text-slate-900 font-semibold">
                    {detayModal.belge_turu === 'SevkIrsaliyesi' ? 'Sevkiyat İrsaliyesi' : 'İade İrsaliyesi'}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Durum</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${durumRenkleri[detayModal.durum]}`}>
                    {detayModal.durum}
                  </span>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">İrsaliye Tarihi</p>
                  <p className="text-slate-900 font-semibold">{detayModal.irsaliye_tarihi}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Sipariş No</p>
                  <p className="text-slate-900 font-semibold">{detayModal.siparis?.siparis_no || `Sipariş #${detayModal.siparis_id}`}</p>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm font-bold text-slate-600 uppercase mb-3">Müşteri Bilgileri</p>
                <div className="space-y-2">
                  <p>
                    <span className="text-slate-500 text-xs font-bold">MÜŞTERİ:</span>{' '}
                    <span className="text-slate-900">{detayModal.siparis?.musteri_adi || 'Müşteri bilgisi yok'}</span>
                  </p>
                  <p>
                    <span className="text-slate-500 text-xs font-bold">ADRES:</span>{' '}
                    <span className="text-slate-900">{detayModal.siparis?.teslimat_adresi || '-'}</span>
                  </p>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm font-bold text-slate-600 uppercase mb-3">Taşıyıcı Bilgileri</p>
                <div className="space-y-2">
                  <p>
                    <span className="text-slate-500 text-xs font-bold">TIR PLAKASI:</span>{' '}
                    <span className="text-slate-900">{detayModal.tir_plaka || '-'}</span>
                  </p>
                  <p>
                    <span className="text-slate-500 text-xs font-bold">ŞOFÖR:</span>{' '}
                    <span className="text-slate-900">{detayModal.sofor_adi || '-'}</span>
                  </p>
                </div>
              </div>
            </div>

            <div className="border-t border-slate-200 p-6 flex gap-3">
              <button
                onClick={() => setDetayModal(null)}
                className="flex-1 h-12 rounded-xl border-2 border-slate-200 text-slate-900 font-bold hover:bg-slate-100 transition"
              >
                Kapat
              </button>
              <button
                onClick={() => handleYazdir(detayModal)}
                className="flex-1 h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition flex items-center justify-center gap-2"
              >
                <Printer className="h-5 w-5" /> Yazdır
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
