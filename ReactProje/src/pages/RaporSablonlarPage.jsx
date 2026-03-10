import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Search, Edit2, Trash2, Loader2, X, FileText, ArrowLeft
} from 'lucide-react';
import { getRaporSablonlari, createRaporSablonu, updateRaporSablonu, deleteRaporSablonu } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const turRenkleri = {
  'stok': 'bg-blue-50 text-blue-700 border-blue-100',
  'siparis': 'bg-emerald-50 text-emerald-700 border-emerald-100',
  'finansal': 'bg-amber-50 text-amber-700 border-amber-100',
  'performans': 'bg-purple-50 text-purple-700 border-purple-100',
};

export default function RaporSablonlarPage() {
  const navigate = useNavigate();
  const { loading, run } = useAsync(true);
  const [sablonlar, setSablonlar] = useState([]);
  const [aramaMetni, setAramaMetni] = useState('');
  const [yeniModal, setYeniModal] = useState(false);
  const [editModal, setEditModal] = useState(null);

  const [formData, setFormData] = useState({
    ad: '',
    tur: 'stok',
    aciklama: '',
  });

  const yükle = async () => {
    const res = await run(() => getRaporSablonlari({ limit: 100 }));
    setSablonlar(res?.data || []);
  };

  useEffect(() => {
    yükle();
  }, []);

  const handleEkle = async () => {
    if (!formData.ad) {
      toast.error('Lütfen şablon adı giriniz');
      return;
    }

    try {
      await createRaporSablonu(formData);
      toast.success('Şablon oluşturuldu');
      setYeniModal(false);
      setFormData({ ad: '', tur: 'stok', aciklama: '' });
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Oluşturma başarısız'));
    }
  };

  const handleGuncelle = async () => {
    try {
      await updateRaporSablonu(editModal.id, formData);
      toast.success('Şablon güncellendi');
      setEditModal(null);
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  const handleSil = async (id) => {
    if (!confirm('Bu şablonu silmek istediğinizden emin misiniz?')) return;
    try {
      await deleteRaporSablonu(id);
      toast.success('Şablon silindi');
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Silme başarısız'));
    }
  };

  const filtrelenmis = sablonlar.filter((s) =>
    s.ad.toLowerCase().includes(aramaMetni.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-4 bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Şablonlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12 sm:pb-20">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-10">
        
        {/* Üst Kısım: Geri Butonu, Başlık ve Aksiyon */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-5 mb-8 sm:mb-10">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="p-3 bg-white border border-slate-200 rounded-2xl shadow-sm hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group"
              title="Geri Dön"
            >
              <ArrowLeft className="h-5 w-5 text-slate-600 group-hover:-translate-x-0.5 transition-transform" />
            </button>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Rapor Şablonları
              </h1>
              <p className="text-slate-500 mt-1 text-sm sm:text-base">
                Raporlarınız için temel şablonları oluşturun ve yönetin.
              </p>
            </div>
          </div>
          <button
            onClick={() => setYeniModal(true)}
            className="w-full sm:w-auto group flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3.5 sm:py-3 rounded-2xl sm:rounded-xl font-semibold shadow-md shadow-blue-600/20 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/30 active:scale-[0.98] transition-all duration-200"
          >
            <Plus className="h-5 w-5 group-hover:rotate-90 transition-transform duration-300" />
            Yeni Şablon
          </button>
        </div>

        {/* Arama Çubuğu */}
        <div className="relative mb-6 sm:mb-8">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            placeholder="Şablonlar içinde ara..."
            value={aramaMetni}
            onChange={(e) => setAramaMetni(e.target.value)}
            className="w-full h-14 pl-12 pr-4 rounded-2xl border border-slate-200 bg-white shadow-sm text-slate-900 text-base focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
          />
        </div>

        {/* Şablonlar Listesi (Mobil uyumlu kart grid yapısı) */}
        {filtrelenmis.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border-2 border-dashed border-slate-200 flex flex-col items-center justify-center">
            <div className="h-20 w-20 bg-slate-50 rounded-full flex items-center justify-center mb-5">
              <FileText className="h-10 w-10 text-slate-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Şablon Bulunamadı</h3>
            <p className="text-slate-500 max-w-sm mx-auto">
              Arama kriterlerinize uygun şablon yok veya henüz bir şablon oluşturmadınız.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {filtrelenmis.map((sablon) => (
              <div
                key={sablon.id}
                className="bg-white rounded-3xl p-5 sm:p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-blue-100 hover:shadow-md transition-all duration-300 flex flex-col group"
              >
                <div className="flex justify-between items-start mb-4 gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-slate-900 mb-2 leading-snug group-hover:text-blue-600 transition-colors">
                      {sablon.ad}
                    </h3>
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg border text-[11px] font-bold uppercase tracking-wide ${turRenkleri[sablon.tur] || 'bg-slate-50 text-slate-700 border-slate-200'}`}>
                      {sablon.tur}
                    </span>
                  </div>
                  
                  {/* Aksiyon Butonları */}
                  <div className="flex bg-slate-50 p-1 rounded-xl border border-slate-100 flex-shrink-0 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity duration-200">
                    <button
                      onClick={() => {
                        setEditModal(sablon);
                        setFormData({
                          ad: sablon.ad,
                          tur: sablon.tur,
                          aciklama: sablon.aciklama,
                        });
                      }}
                      className="p-2 text-blue-600 hover:bg-white hover:shadow-sm rounded-lg transition-all"
                      title="Düzenle"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleSil(sablon.id)}
                      className="p-2 text-red-600 hover:bg-white hover:shadow-sm rounded-lg transition-all"
                      title="Sil"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="mt-auto pt-4 border-t border-slate-50">
                  <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed">
                    {sablon.aciklama ? sablon.aciklama : <span className="italic opacity-60">Açıklama bulunmuyor...</span>}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Ekle/Düzenle Modal */}
        {(yeniModal || editModal) && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-end sm:items-center justify-center sm:p-4">
            <div className="bg-white w-full sm:max-w-md rounded-t-[2rem] sm:rounded-3xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto shadow-2xl transform transition-all animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
              
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                    {editModal ? 'Şablonu Düzenle' : 'Yeni Şablon'}
                  </h2>
                  <p className="text-sm text-slate-500 mt-1">Rapor şablonunuzun detaylarını belirleyin.</p>
                </div>
                <button
                  onClick={() => {
                    setYeniModal(false);
                    setEditModal(null);
                  }}
                  className="p-2 bg-slate-50 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-5">
                {/* Şablon Adı */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Şablon Adı</label>
                  <input
                    type="text"
                    placeholder="Örn: Aylık Satış Özeti"
                    value={formData.ad}
                    onChange={(e) => setFormData({ ...formData, ad: e.target.value })}
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  />
                </div>

                {/* Tür Seçimi */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Rapor Türü</label>
                  <select
                    value={formData.tur}
                    onChange={(e) => setFormData({ ...formData, tur: e.target.value })}
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  >
                    <option value="stok">Stok Raporları</option>
                    <option value="siparis">Sipariş Raporları</option>
                    <option value="finansal">Finansal Raporlar</option>
                    <option value="performans">Performans Raporları</option>
                  </select>
                </div>

                {/* Açıklama */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Açıklama (İsteğe Bağlı)</label>
                  <textarea
                    placeholder="Bu şablonun ne işe yaradığını kısaca açıklayın..."
                    value={formData.aciklama}
                    onChange={(e) => setFormData({ ...formData, aciklama: e.target.value })}
                    className="w-full h-24 p-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm resize-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  />
                </div>
              </div>

              {/* Modal Aksiyon Butonları */}
              <div className="flex gap-3 mt-8 pt-6 border-t border-slate-100">
                <button
                  onClick={() => {
                    setYeniModal(false);
                    setEditModal(null);
                  }}
                  className="flex-1 h-12 rounded-xl bg-white border border-slate-200 text-slate-600 font-bold hover:bg-slate-50 hover:border-slate-300 transition-all"
                >
                  İptal
                </button>
                <button
                  onClick={editModal ? handleGuncelle : handleEkle}
                  className="flex-1 h-12 rounded-xl bg-blue-600 text-white font-bold shadow-md shadow-blue-600/20 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/30 transition-all"
                >
                  {editModal ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
              
            </div>
          </div>
        )}
      </div>
    </div>
  );
}