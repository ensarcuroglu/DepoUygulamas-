import { useState, useEffect } from 'react';
import {
  Plus, Search, Calendar, User, MapPin, Loader2, X, ChevronDown,
  Trash2, Eye, DollarSign, Package, ShoppingBag, Receipt
} from 'lucide-react';
import { getSiparisler, createSiparis, updateSiparis, deleteSiparis, getUrunler } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
  'Bekleme': 'bg-slate-100 text-slate-700 border border-slate-200',
  'Hazirlaniyor': 'bg-amber-50 text-amber-700 border border-amber-200',
  'YolaCikti': 'bg-blue-50 text-blue-700 border border-blue-200',
  'TeslimEdildi': 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  'Iptal': 'bg-red-50 text-red-700 border border-red-200',
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
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Veriler yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
        
        {/* Üst Bilgi ve Aksiyon Alanı */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Sipariş Yönetimi</h1>
            <p className="text-sm text-slate-500 mt-1">Tüm siparişlerinizi görüntüleyin ve yönetin.</p>
          </div>
          <button
            onClick={() => setYeniSiparisModal(true)}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold shadow-sm hover:bg-blue-700 hover:shadow active:scale-[0.98] transition-all"
          >
            <Plus className="h-5 w-5" />
            <span>Yeni Sipariş</span>
          </button>
        </div>

        {/* Arama ve Filtreler */}
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 mb-8 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Sipariş no veya müşteri ara..."
              value={aramaMetni}
              onChange={(e) => setAramaMetni(e.target.value)}
              className="w-full h-12 pl-11 pr-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
            />
          </div>
          <div className="relative sm:w-64">
            <select
              value={durumFiltre}
              onChange={(e) => setDurumFiltre(e.target.value)}
              className="w-full h-12 px-4 pr-10 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors appearance-none"
            >
              <option value="">Tüm Durumlar</option>
              <option value="Bekleme">Bekleme</option>
              <option value="Hazirlaniyor">Hazırlanıyor</option>
              <option value="YolaCikti">Yola Çıktı</option>
              <option value="TeslimEdildi">Teslim Edildi</option>
              <option value="Iptal">İptal</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
          </div>
        </div>

        {/* Siparişler Listesi */}
        {filtrelenmis.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <div className="bg-slate-50 p-4 rounded-full mb-4">
              <Package className="h-10 w-10 text-slate-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">Sipariş Bulunamadı</h3>
            <p className="text-slate-500 max-w-sm">Arama kriterlerinize uygun sipariş kaydı bulunmuyor. Farklı filtreler deneyebilir veya yeni sipariş oluşturabilirsiniz.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filtrelenmis.map((siparis) => (
              <div
                key={siparis.id}
                className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group"
              >
                <div className="p-5 sm:p-6">
                  <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-5">
                    
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-3 mb-1.5">
                        <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                          {siparis.siparis_no}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide ${durumRenkleri[siparis.durum]}`}>
                          {siparis.durum}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-600">
                        <User className="h-4 w-4 text-slate-400" />
                        <span className="font-medium text-sm">{siparis.musteri_adi}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => setDetayModal(siparis)}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 p-2.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-xl transition-colors font-medium text-sm"
                        title="Detayları gör"
                      >
                        <Eye className="h-4 w-4" />
                        <span className="sm:hidden">Detay</span>
                      </button>
                      <button
                        onClick={() => handleSil(siparis.id)}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 p-2.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-xl transition-colors font-medium text-sm"
                        title="Sil"
                      >
                        <Trash2 className="h-4 w-4" />
                        <span className="sm:hidden">Sil</span>
                      </button>
                    </div>

                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-slate-100">
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 text-slate-500">
                        <Calendar className="h-3.5 w-3.5" />
                        <p className="text-xs font-bold uppercase tracking-wider">Teslimat</p>
                      </div>
                      <p className="text-slate-900 font-semibold text-sm">{siparis.teslimat_tarihi}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 text-slate-500">
                        <ShoppingBag className="h-3.5 w-3.5" />
                        <p className="text-xs font-bold uppercase tracking-wider">Miktar</p>
                      </div>
                      <p className="text-slate-900 font-semibold text-sm">{siparis.top_miktar} <span className="text-slate-500 font-normal">adet</span></p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 text-slate-500">
                        <Receipt className="h-3.5 w-3.5" />
                        <p className="text-xs font-bold uppercase tracking-wider">Tutar</p>
                      </div>
                      <p className="text-emerald-600 font-bold text-base">₺{siparis.top_tutar?.toFixed(2)}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 text-slate-500">
                        <User className="h-3.5 w-3.5" />
                        <p className="text-xs font-bold uppercase tracking-wider">Oluşturan</p>
                      </div>
                      <p className="text-slate-900 font-medium text-sm truncate">{siparis.olusturan_kullanici?.ad_soyad || '-'}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Yeni Sipariş Modal */}
        {yeniSiparisModal && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/40 backdrop-blur-sm sm:p-4">
            <div className="bg-white w-full sm:max-w-3xl sm:rounded-2xl rounded-t-2xl max-h-[95vh] flex flex-col shadow-2xl animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
              
              <div className="flex justify-between items-center p-5 sm:p-6 border-b border-slate-100 bg-white sm:rounded-t-2xl rounded-t-2xl z-10 sticky top-0">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900">Yeni Sipariş Oluştur</h2>
                <button
                  onClick={() => setYeniSiparisModal(false)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="p-5 sm:p-6 overflow-y-auto space-y-6 flex-1">
                {/* Genel Bilgiler */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Sipariş Bilgileri</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Müşteri Adı</label>
                      <input
                        type="text"
                        placeholder="Örn: Ahmet Yılmaz"
                        value={formData.musteri_adi}
                        onChange={(e) => setFormData({ ...formData, musteri_adi: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-200 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Teslimat Tarihi</label>
                      <input
                        type="date"
                        value={formData.teslimat_tarihi}
                        onChange={(e) => setFormData({ ...formData, teslimat_tarihi: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-200 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                    <div className="space-y-1.5 sm:col-span-2">
                      <label className="text-sm font-semibold text-slate-700">Teslimat Adresi</label>
                      <div className="relative">
                        <MapPin className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
                        <input
                          type="text"
                          placeholder="Açık adres giriniz..."
                          value={formData.teslimat_adresi}
                          onChange={(e) => setFormData({ ...formData, teslimat_adresi: e.target.value })}
                          className="w-full h-12 pl-11 pr-4 text-sm rounded-xl border border-slate-200 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                        />
                      </div>
                    </div>
                    <div className="space-y-1.5 sm:col-span-2">
                      <label className="text-sm font-semibold text-slate-700">Ek Notlar (Opsiyonel)</label>
                      <textarea
                        placeholder="Sipariş ile ilgili belirtmek istedikleriniz..."
                        value={formData.notlar}
                        onChange={(e) => setFormData({ ...formData, notlar: e.target.value })}
                        className="w-full min-h-[80px] p-4 text-sm rounded-xl border border-slate-200 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors resize-y"
                      />
                    </div>
                  </div>
                </div>

                {/* Kalemler */}
                <div className="space-y-4 pt-2">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Sipariş Kalemleri</h3>
                  </div>
                  
                  <div className="space-y-3">
                    {formData.kalemler.map((kalem, idx) => (
                      <div key={idx} className="bg-slate-50 border border-slate-200 p-4 rounded-xl relative group">
                        
                        {/* Mobilde sağ üstte çarpı, masaüstünde hoverda görünen yapı */}
                        {formData.kalemler.length > 1 && (
                          <button
                            onClick={() => {
                              const yeniKalemler = formData.kalemler.filter((_, i) => i !== idx);
                              setFormData({ ...formData, kalemler: yeniKalemler });
                            }}
                            className="absolute -top-2 -right-2 sm:top-4 sm:right-4 h-8 w-8 flex items-center justify-center bg-white sm:bg-transparent text-red-500 hover:bg-red-50 hover:text-red-600 rounded-full shadow-sm sm:shadow-none border border-slate-200 sm:border-transparent transition-all"
                            title="Kalemi Sil"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        )}

                        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                          <div className="sm:col-span-5 space-y-1">
                            <label className="text-xs font-semibold text-slate-500 sm:hidden">Ürün Seçimi</label>
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
                              className="w-full h-11 px-3 text-sm rounded-lg border border-slate-300 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                            >
                              <option value="">Ürün Seçiniz...</option>
                              {urunler.map((u) => (
                                <option key={u.id} value={u.id}>
                                  {u.isim}
                                </option>
                              ))}
                            </select>
                          </div>
                          
                          <div className="grid grid-cols-3 sm:col-span-7 gap-3">
                            <div className="space-y-1">
                              <label className="text-xs font-semibold text-slate-500">Miktar</label>
                              <input
                                type="number"
                                min="1"
                                placeholder="0"
                                value={kalem.miktar}
                                onChange={(e) => {
                                  const yeniKalemler = [...formData.kalemler];
                                  yeniKalemler[idx].miktar = parseInt(e.target.value) || 0;
                                  setFormData({ ...formData, kalemler: yeniKalemler });
                                }}
                                className="w-full h-11 px-3 text-sm rounded-lg border border-slate-300 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-center"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-xs font-semibold text-slate-500">Birim Fiyat (₺)</label>
                              <input
                                type="number"
                                placeholder="0.00"
                                value={kalem.birim_fiyat}
                                onChange={(e) => {
                                  const yeniKalemler = [...formData.kalemler];
                                  yeniKalemler[idx].birim_fiyat = parseFloat(e.target.value) || 0;
                                  setFormData({ ...formData, kalemler: yeniKalemler });
                                }}
                                className="w-full h-11 px-3 text-sm rounded-lg border border-slate-300 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-center"
                              />
                            </div>
                            <div className="space-y-1">
                              <label className="text-xs font-semibold text-slate-500">KDV (%)</label>
                              <input
                                type="number"
                                placeholder="18"
                                value={kalem.kdv_orani}
                                onChange={(e) => {
                                  const yeniKalemler = [...formData.kalemler];
                                  yeniKalemler[idx].kdv_orani = parseFloat(e.target.value) || 0;
                                  setFormData({ ...formData, kalemler: yeniKalemler });
                                }}
                                className="w-full h-11 px-3 text-sm rounded-lg border border-slate-300 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-center"
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

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
                    className="w-full sm:w-auto mt-2 inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors"
                  >
                    <Plus className="h-4 w-4" /> Yeni Kalem Ekle
                  </button>
                </div>
              </div>

              {/* Alt Bilgi / İşlem Butonları */}
              <div className="border-t border-slate-100 bg-slate-50 p-5 sm:p-6 flex flex-col-reverse sm:flex-row gap-3 rounded-b-2xl z-10 sticky bottom-0">
                <button
                  onClick={() => setYeniSiparisModal(false)}
                  className="w-full sm:w-1/3 h-12 rounded-xl border border-slate-300 bg-white text-slate-700 font-bold hover:bg-slate-50 transition-colors"
                >
                  Vazgeç
                </button>
                <button
                  onClick={handleYeniSiparis}
                  className="w-full sm:w-2/3 h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 active:scale-[0.98] transition-all shadow-sm"
                >
                  Siparişi Kaydet
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Detay Modal */}
        {detayModal && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/40 backdrop-blur-sm sm:p-4">
            <div className="bg-white w-full sm:max-w-2xl sm:rounded-2xl rounded-t-2xl max-h-[90vh] flex flex-col shadow-2xl animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
              
              <div className="flex justify-between items-center p-5 sm:p-6 border-b border-slate-100 bg-white sm:rounded-t-2xl rounded-t-2xl z-10 sticky top-0">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <h2 className="text-xl sm:text-2xl font-bold text-slate-900">{detayModal.siparis_no}</h2>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold w-fit ${durumRenkleri[detayModal.durum]}`}>
                    {detayModal.durum}
                  </span>
                </div>
                <button
                  onClick={() => setDetayModal(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="p-5 sm:p-6 overflow-y-auto space-y-6 flex-1">
                {/* Müşteri ve Adres Bilgisi */}
                <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <div className="flex items-center gap-2 mb-1.5 text-slate-500">
                        <User className="h-4 w-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Müşteri</p>
                      </div>
                      <p className="text-slate-900 font-semibold text-base">{detayModal.musteri_adi}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1.5 text-slate-500">
                        <Calendar className="h-4 w-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Teslimat Tarihi</p>
                      </div>
                      <p className="text-slate-900 font-semibold text-base">{detayModal.teslimat_tarihi}</p>
                    </div>
                    <div className="sm:col-span-2 pt-3 border-t border-slate-200/60">
                      <div className="flex items-center gap-2 mb-1.5 text-slate-500">
                        <MapPin className="h-4 w-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Teslimat Adresi</p>
                      </div>
                      <p className="text-slate-800 font-medium leading-relaxed">{detayModal.teslimat_adresi}</p>
                    </div>
                    {detayModal.notlar && (
                      <div className="sm:col-span-2 pt-3 border-t border-slate-200/60">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Sipariş Notu</p>
                        <p className="text-slate-700 italic text-sm">{detayModal.notlar}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Detay Kalemler */}
                <div>
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Sipariş Kalemleri</h3>
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                    <div className="divide-y divide-slate-100">
                      {detayModal.kalemler?.map((kalem, idx) => (
                        <div key={idx} className="flex flex-col sm:flex-row justify-between sm:items-center p-4 gap-3 hover:bg-slate-50 transition-colors">
                          <div className="flex-1">
                            <p className="font-bold text-slate-900 mb-1">{kalem.urun?.isim || 'Bilinmeyen Ürün'}</p>
                            <p className="text-sm text-slate-500">
                              {kalem.miktar} adet × ₺{kalem.birim_fiyat} <span className="text-xs opacity-75">(% {kalem.kdv_orani} KDV)</span>
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="font-bold text-emerald-600 text-lg">
                              ₺{(kalem.toplam || 0).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Genel Toplam */}
                    <div className="bg-slate-50 p-4 border-t border-slate-200 flex justify-between items-center">
                      <span className="font-bold text-slate-600">Genel Toplam</span>
                      <span className="font-extrabold text-slate-900 text-xl">₺{detayModal.top_tutar?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-100 p-5 sm:p-6 bg-white sm:rounded-b-2xl z-10 sticky bottom-0">
                <button
                  onClick={() => setDetayModal(null)}
                  className="w-full h-12 rounded-xl border border-slate-300 text-slate-700 font-bold hover:bg-slate-50 active:scale-[0.98] transition-all"
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}