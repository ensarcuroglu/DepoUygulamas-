import { useState, useEffect } from 'react';
import {
  Plus, Search, Calendar, User, MapPin, Loader2, X, ChevronDown,
  Trash2, Eye, DollarSign
} from 'lucide-react';
import { getSiparisler, createSiparis, updateSiparis, deleteSiparis, getUrunler } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
  'Bekleme': 'bg-slate-100 text-slate-800 border border-slate-300',
  'Hazirlaniyor': 'bg-amber-100 text-amber-800 border border-amber-300',
  'YolaCikti': 'bg-blue-100 text-blue-800 border border-blue-300',
  'TeslimEdildi': 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  'Iptal': 'bg-red-100 text-red-800 border border-red-300',
};

export default function SiparislerPage() {
  const { loading, run } = useAsync(true);
  const [siparisler, setSiparisler] = useState([]);
  const [urunler, setUrunler] = useState([]);
  const [aramaMetni, setAramaMetni] = useState('');
  const [durumFiltre, setDurumFiltre] = useState('');
  const [yeniSiparisModal, setYeniSiparisModal] = useState(false);
  const [detayModal, setDetayModal] = useState(null);
  const [formData, setFormData] = useState({
    musteri_adi: '',
    teslimat_adresi: '',
    teslimat_tarihi: '',
    notlar: '',
    kalemler: [{ urun_id: '', miktar: 1, birim_fiyat: 0, kdv_orani: 18 }],
  });

  const yükle = async () => {
    const [siparisRes, urunRes] = await run(() =>
      Promise.all([
        getSiparisler({ limit: 100, durum: durumFiltre, arama: aramaMetni }),
        getUrunler({ limit: 500 }),
      ])
    );
    setSiparisler(siparisRes?.data || []);
    setUrunler(urunRes?.data || []);
  };

  useEffect(() => {
    yükle();
  }, [durumFiltre, aramaMetni]);

  const handleYeniSiparis = async () => {
    if (!formData.musteri_adi || !formData.teslimat_adresi || !formData.teslimat_tarihi) {
      toast.error('Lütfen tüm alanları doldurun');
      return;
    }

    const filteredKalemler = formData.kalemler
      .filter((k) => k.urun_id && k.miktar > 0)
      .map((k) => ({
        urun_id: k.urun_id,
        miktar: k.miktar,
        birim_fiyat: k.birim_fiyat,
        kdv_orani: k.kdv_orani,
        toplam: k.miktar * k.birim_fiyat * (1 + k.kdv_orani / 100),
      }));

    if (filteredKalemler.length === 0) {
      toast.error('Lütfen en az bir ürün ekleyin');
      return;
    }

    try {
      await createSiparis({
        ...formData,
        kalemler: filteredKalemler,
        top_miktar: filteredKalemler.reduce((a, k) => a + k.miktar, 0),
        top_tutar: filteredKalemler.reduce((a, k) => a + k.toplam, 0),
      });
      toast.success('Sipariş oluşturuldu');
      setYeniSiparisModal(false);
      setFormData({
        musteri_adi: '',
        teslimat_adresi: '',
        teslimat_tarihi: '',
        notlar: '',
        kalemler: [{ urun_id: '', miktar: 1, birim_fiyat: 0, kdv_orani: 18 }],
      });
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Sipariş oluşturma başarısız'));
    }
  };

  const handleSil = async (id) => {
    if (!confirm('Bu siparişi silmek istediğinizden emin misiniz?')) return;
    try {
      await deleteSiparis(id);
      toast.success('Sipariş silindi');
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Silme başarısız'));
    }
  };

  const filtrelenmis = siparisler.filter((s) =>
    s.siparis_no.toLowerCase().includes(aramaMetni.toLowerCase()) ||
    s.musteri_adi.toLowerCase().includes(aramaMetni.toLowerCase())
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
        <h1 className="text-3xl font-bold text-slate-900">Siparişler</h1>
        <button
          onClick={() => setYeniSiparisModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          <Plus className="h-5 w-5" /> Yeni Sipariş
        </button>
      </div>

      {/* Arama ve Filtreler */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Sipariş no veya müşteri ara..."
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
          <option value="Bekleme">Bekleme</option>
          <option value="Hazirlaniyor">Hazırlanıyor</option>
          <option value="YolaCikti">Yola Çıktı</option>
          <option value="TeslimEdildi">Teslim Edildi</option>
          <option value="Iptal">İptal</option>
        </select>
      </div>

      {/* Siparişler Listesi */}
      {filtrelenmis.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center">
          <DollarSign className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Sipariş bulunamadı</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtrelenmis.map((siparis) => (
            <div
              key={siparis.id}
              className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-slate-900">{siparis.siparis_no}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${durumRenkleri[siparis.durum]}`}>
                      {siparis.durum}
                    </span>
                  </div>
                  <p className="text-slate-600 font-medium">{siparis.musteri_adi}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setDetayModal(siparis)}
                    className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition"
                    title="Detayları gör"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleSil(siparis.id)}
                    className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition"
                    title="Sil"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Teslimat Tarihi</p>
                  <p className="text-slate-900 font-semibold">{siparis.teslimat_tarihi}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Toplam Miktar</p>
                  <p className="text-slate-900 font-semibold">{siparis.top_miktar} adet</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Toplam Tutar</p>
                  <p className="text-emerald-600 font-bold">₺ {siparis.top_tutar?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Oluşturan</p>
                  <p className="text-slate-900 font-semibold">{siparis.olusturan_kullanici?.ad_soyad || '-'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Yeni Sipariş Modal */}
      {yeniSiparisModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900">Yeni Sipariş</h2>
              <button
                onClick={() => setYeniSiparisModal(false)}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <input
                type="text"
                placeholder="Müşteri Adı"
                value={formData.musteri_adi}
                onChange={(e) => setFormData({ ...formData, musteri_adi: e.target.value })}
                className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              />
              <input
                type="text"
                placeholder="Teslimat Adresi"
                value={formData.teslimat_adresi}
                onChange={(e) => setFormData({ ...formData, teslimat_adresi: e.target.value })}
                className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              />
              <input
                type="date"
                value={formData.teslimat_tarihi}
                onChange={(e) => setFormData({ ...formData, teslimat_tarihi: e.target.value })}
                className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              />
              <textarea
                placeholder="Notlar"
                value={formData.notlar}
                onChange={(e) => setFormData({ ...formData, notlar: e.target.value })}
                className="h-24 px-4 py-3 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              />

              {/* Kalemler */}
              <div className="space-y-3">
                <p className="text-sm font-bold text-slate-600 uppercase">Ürün Kalemleri</p>
                {formData.kalemler.map((kalem, idx) => (
                  <div key={idx} className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                    <select
                      value={kalem.urun_id}
                      onChange={(e) => {
                        const yeniUrun = urunler.find((u) => u.id === parseInt(e.target.value));
                        const yeniKalemler = [...formData.kalemler];
                        yeniKalemler[idx] = {
                          ...kalem,
                          urun_id: parseInt(e.target.value),
                          birim_fiyat: yeniUrun?.fiyat || 0,
                        };
                        setFormData({ ...formData, kalemler: yeniKalemler });
                      }}
                      className="h-10 px-2 text-xs rounded-lg border border-slate-200 bg-slate-50"
                    >
                      <option value="">Ürün Seç</option>
                      {urunler.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.isim}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      placeholder="Miktar"
                      value={kalem.miktar}
                      onChange={(e) => {
                        const yeniKalemler = [...formData.kalemler];
                        yeniKalemler[idx].miktar = parseInt(e.target.value) || 0;
                        setFormData({ ...formData, kalemler: yeniKalemler });
                      }}
                      className="h-10 px-2 text-xs rounded-lg border border-slate-200 bg-slate-50"
                    />
                    <input
                      type="number"
                      placeholder="Fiyat"
                      value={kalem.birim_fiyat}
                      onChange={(e) => {
                        const yeniKalemler = [...formData.kalemler];
                        yeniKalemler[idx].birim_fiyat = parseFloat(e.target.value) || 0;
                        setFormData({ ...formData, kalemler: yeniKalemler });
                      }}
                      className="h-10 px-2 text-xs rounded-lg border border-slate-200 bg-slate-50"
                    />
                    <input
                      type="number"
                      placeholder="KDV %"
                      value={kalem.kdv_orani}
                      onChange={(e) => {
                        const yeniKalemler = [...formData.kalemler];
                        yeniKalemler[idx].kdv_orani = parseFloat(e.target.value) || 0;
                        setFormData({ ...formData, kalemler: yeniKalemler });
                      }}
                      className="h-10 px-2 text-xs rounded-lg border border-slate-200 bg-slate-50"
                    />
                    <button
                      onClick={() => {
                        const yeniKalemler = formData.kalemler.filter((_, i) => i !== idx);
                        setFormData({ ...formData, kalemler: yeniKalemler });
                      }}
                      className="text-red-600 hover:bg-red-100 rounded-lg transition"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => {
                    setFormData({
                      ...formData,
                      kalemler: [
                        ...formData.kalemler,
                        { urun_id: '', miktar: 1, birim_fiyat: 0, kdv_orani: 18 },
                      ],
                    });
                  }}
                  className="text-blue-600 hover:text-blue-700 font-semibold text-sm"
                >
                  + Kalem Ekle
                </button>
              </div>
            </div>

            <div className="border-t border-slate-200 p-6 flex gap-3">
              <button
                onClick={() => setYeniSiparisModal(false)}
                className="flex-1 h-12 rounded-xl border-2 border-slate-200 text-slate-900 font-bold hover:bg-slate-100 transition"
              >
                İptal
              </button>
              <button
                onClick={handleYeniSiparis}
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
              <h2 className="text-2xl font-bold text-slate-900">{detayModal.siparis_no}</h2>
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
                  <p className="text-slate-500 text-xs font-bold uppercase">Müşteri</p>
                  <p className="text-slate-900 font-semibold">{detayModal.musteri_adi}</p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Durum</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${durumRenkleri[detayModal.durum]}`}>
                    {detayModal.durum}
                  </span>
                </div>
                <div className="col-span-2">
                  <p className="text-slate-500 text-xs font-bold uppercase">Teslimat Adresi</p>
                  <p className="text-slate-900 font-semibold">{detayModal.teslimat_adresi}</p>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm font-bold text-slate-600 uppercase mb-3">Kalemler</p>
                <div className="space-y-2">
                  {detayModal.kalemler?.map((kalem, idx) => (
                    <div key={idx} className="flex justify-between bg-slate-50 p-3 rounded-lg text-sm">
                      <span>{kalem.urun?.isim || 'Bilinmiyor'}</span>
                      <span className="font-semibold">
                        {kalem.miktar} x ₺{kalem.birim_fiyat} = ₺{(kalem.toplam || 0).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="border-t border-slate-200 p-6">
              <button
                onClick={() => setDetayModal(null)}
                className="w-full h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
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
