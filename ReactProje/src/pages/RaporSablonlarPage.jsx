import { useState, useEffect } from 'react';
import {
  Plus, Search, Edit2, Trash2, Loader2, X, FileText, Eye
} from 'lucide-react';
import { getRaporSablonlari, createRaporSablonu, updateRaporSablonu, deleteRaporSablonu } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

export default function RaporSablonlarPage() {
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
      <div className="flex min-h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-[1200px] mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Rapor Şablonları</h1>
        <button
          onClick={() => setYeniModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          <Plus className="h-5 w-5" /> Yeni Şablon
        </button>
      </div>

      {/* Arama */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
        <input
          type="text"
          placeholder="Şablon ara..."
          value={aramaMetni}
          onChange={(e) => setAramaMetni(e.target.value)}
          className="w-full h-12 pl-11 pr-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
        />
      </div>

      {/* Şablonlar */}
      {filtrelenmis.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-2xl">
          <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">Şablon bulunamadı</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Ad</th>
                  <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Tür</th>
                  <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Açıklama</th>
                  <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtrelenmis.map((sablon) => (
                  <tr key={sablon.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">{sablon.ad}</td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold">
                        {sablon.tur}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 text-sm line-clamp-1">{sablon.aciklama}</td>
                    <td className="px-6 py-4 flex gap-2">
                      <button
                        onClick={() => {
                          setEditModal(sablon);
                          setFormData({
                            ad: sablon.ad,
                            tur: sablon.tur,
                            aciklama: sablon.aciklama,
                          });
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleSil(sablon.id)}
                        className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal */}
      {(yeniModal || editModal) && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
          <div className="bg-white rounded-2xl max-w-md w-full mx-4 p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">{editModal ? 'Şablonu Düzenle' : 'Yeni Şablon'}</h2>
              <button
                onClick={() => {
                  setYeniModal(false);
                  setEditModal(null);
                }}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              <input
                type="text"
                placeholder="Şablon Adı"
                value={formData.ad}
                onChange={(e) => setFormData({ ...formData, ad: e.target.value })}
                className="w-full h-11 px-4 rounded-lg border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />
              <select
                value={formData.tur}
                onChange={(e) => setFormData({ ...formData, tur: e.target.value })}
                className="w-full h-11 px-4 rounded-lg border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="stok">Stok Raporları</option>
                <option value="siparis">Sipariş Raporları</option>
                <option value="finansal">Finansal Raporlar</option>
                <option value="performans">Performans Raporları</option>
              </select>
              <textarea
                placeholder="Açıklama"
                value={formData.aciklama}
                onChange={(e) => setFormData({ ...formData, aciklama: e.target.value })}
                className="w-full h-20 p-4 rounded-lg border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setYeniModal(false);
                  setEditModal(null);
                }}
                className="flex-1 h-11 rounded-lg border border-slate-200 font-semibold hover:bg-slate-100"
              >
                İptal
              </button>
              <button
                onClick={editModal ? handleGuncelle : handleEkle}
                className="flex-1 h-11 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
              >
                {editModal ? 'Güncelle' : 'Oluştur'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
