import { useState, useEffect } from 'react';
import {
  Plus, Search, FileText, Loader2, X, Printer, CheckCircle, AlertCircle
} from 'lucide-react';
import {
  getIrsaliyeler, createIrsaliye, updateIrsaliye, getSiparisler
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

export default function IrsaliyelerPage() {
  const { loading, run } = useAsync(true);
  const [irsaliyeler, setIrsaliyeler] = useState([]);
  const [siparisler, setSiparisler] = useState([]);
  const [aramaMetni, setAramaMetni] = useState('');
  const [durumFiltre, setDurumFiltre] = useState('');
  const [yeniIrsaliyeModal, setYeniIrsaliyeModal] = useState(false);
  const [detayModal, setDetayModal] = useState(null);

  const [formData, setFormData] = useState({
    siparis_id: '',
    sevkiyat_id: null,
    irsaliye_tarihi: new Date().toISOString().split('T')[0],
    belge_turu: 'SevkIrsaliyesi',
    tir_plaka: '',
    sofor_adi: '',
    durum: 'Taslak',
  });

  const yükle = async () => {
    const [irsRes, sipRes] = await run(() =>
      Promise.all([
        getIrsaliyeler({ limit: 100, durum: durumFiltre || undefined, arama: aramaMetni }),
        getSiparisler({ limit: 500 }),
      ])
    );
    setIrsaliyeler(irsRes?.data || []);
    setSiparisler(sipRes?.data || []);
  };

  useEffect(() => {
    yükle();
  }, [durumFiltre, aramaMetni]);

  const handleYeniIrsaliye = async () => {
    if (!formData.siparis_id) {
      toast.error('Lütfen sipariş seçin');
      return;
    }

    try {
      await createIrsaliye(formData);
      toast.success('İrsaliye oluşturuldu');
      setYeniIrsaliyeModal(false);
      setFormData({
        siparis_id: '',
        sevkiyat_id: null,
        irsaliye_tarihi: new Date().toISOString().split('T')[0],
        belge_turu: 'SevkIrsaliyesi',
        tir_plaka: '',
        sofor_adi: '',
        durum: 'Taslak',
      });
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'İrsaliye oluşturma başarısız'));
    }
  };

  const handleDurumDegis = async (irsaliyeId, yeniDurum) => {
    try {
      await updateIrsaliye(irsaliyeId, { durum: yeniDurum });
      toast.success('Durum güncellendi');
      yükle();
      setDetayModal(null);
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  const handleYazdir = (irsaliye) => {
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>İrsaliye: ${irsaliye.irsaliye_no}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }
          .content { margin-bottom: 30px; }
          .field { margin: 10px 0; }
          .label { font-weight: bold; color: #555; font-size: 12px; }
          .value { color: #333; font-size: 14px; }
          table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
          th { background-color: #f5f5f5; font-weight: bold; }
          .footer { margin-top: 30px; text-align: center; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>İRSALİYE</h1>
          <p style="font-size: 12px; color: #666;">${irsaliye.belge_turu === 'SevkIrsaliyesi' ? 'Sevkiyat İrsaliyesi' : 'İade İrsaliyesi'}</p>
        </div>

        <div class="content">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
              <div class="field">
                <div class="label">İRSALİYE NO</div>
                <div class="value">${irsaliye.irsaliye_no}</div>
              </div>
              <div class="field">
                <div class="label">İRSALİYE TARİHİ</div>
                <div class="value">${irsaliye.irsaliye_tarihi}</div>
              </div>
            </div>
            <div>
              <div class="field">
                <div class="label">SİPARİŞ NO</div>
                <div class="value">${irsaliye.siparis?.siparis_no}</div>
              </div>
              <div class="field">
                <div class="label">DURUM</div>
                <div class="value">${irsaliye.durum}</div>
              </div>
            </div>
          </div>

          <div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 20px;">
            <h3>MÜŞTERİ BİLGİLERİ</h3>
            <div class="field">
              <div class="label">MÜŞTERİ ADI</div>
              <div class="value">${irsaliye.siparis?.musteri_adi}</div>
            </div>
            <div class="field">
              <div class="label">TESLİMAT ADRESİ</div>
              <div class="value">${irsaliye.siparis?.teslimat_adresi}</div>
            </div>
          </div>

          <div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 20px;">
            <h3>TAŞIYICI BİLGİLERİ</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
              <div class="field">
                <div class="label">TIR PLAKASI</div>
                <div class="value">${irsaliye.tir_plaka || '-'}</div>
              </div>
              <div class="field">
                <div class="label">ŞOFÖR ADI</div>
                <div class="value">${irsaliye.sofor_adi || '-'}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="footer">
          <p>Yazdırıldı: ${new Date().toLocaleString('tr-TR')}</p>
          <p style="margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
            ________________________<br>
            Alıcı İmzası
          </p>
        </div>
      </body>
      </html>
    `;

    const newWindow = window.open('', '_blank');
    newWindow.document.write(htmlContent);
    newWindow.document.close();
    setTimeout(() => newWindow.print(), 250);
  };

  const filtrelenmis = irsaliyeler.filter((i) =>
    i.irsaliye_no.toLowerCase().includes(aramaMetni.toLowerCase()) ||
    i.siparis?.siparis_no.toLowerCase().includes(aramaMetni.toLowerCase())
  );

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
                    {irsaliye.siparis?.musteri_adi} - {irsaliye.siparis?.siparis_no}
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
                    onClick={() => setDetayModal(irsaliye)}
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
              <div>
                <label className="block text-sm font-bold text-slate-600 uppercase mb-2">
                  Sipariş * (Zorunlu)
                </label>
                <select
                  value={formData.siparis_id}
                  onChange={(e) => setFormData({ ...formData, siparis_id: parseInt(e.target.value) || '' })}
                  className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                >
                  <option value="">Sipariş Seçin</option>
                  {siparisler.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.siparis_no} - {s.musteri_adi}
                    </option>
                  ))}
                </select>
              </div>

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
                  <p className="text-slate-900 font-semibold">{detayModal.siparis?.siparis_no}</p>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm font-bold text-slate-600 uppercase mb-3">Müşteri Bilgileri</p>
                <div className="space-y-2">
                  <p>
                    <span className="text-slate-500 text-xs font-bold">MÜŞTERİ:</span>{' '}
                    <span className="text-slate-900">{detayModal.siparis?.musteri_adi}</span>
                  </p>
                  <p>
                    <span className="text-slate-500 text-xs font-bold">ADRES:</span>{' '}
                    <span className="text-slate-900">{detayModal.siparis?.teslimat_adresi}</span>
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
