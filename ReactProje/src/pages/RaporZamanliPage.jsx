import { useState, useEffect } from 'react';
import {
  Plus, Loader2, X, Edit2, Trash2, Clock, Mail, CheckCircle2
} from 'lucide-react';
import {
  getRaporSchedules, createRaporSchedule, updateRaporSchedule, deleteRaporSchedule, getRaporSablonlari
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const periyodRenkleri = {
  'gunluk': 'bg-blue-100 text-blue-700',
  'haftalik': 'bg-purple-100 text-purple-700',
  'aylik': 'bg-emerald-100 text-emerald-700',
};

export default function RaporZamanliPage() {
  const { loading, run } = useAsync(true);
  const [schedules, setSchedules] = useState([]);
  const [sablonlar, setSablonlar] = useState([]);
  const [yeniModal, setYeniModal] = useState(false);
  const [editModal, setEditModal] = useState(null);

  const [formData, setFormData] = useState({
    sablon_id: '',
    sablon_adi: '',
    periyod: 'haftalik',
    saat: '09:00',
    alici_emailler: [],
    format: 'pdf',
  });

  const [emailInput, setEmailInput] = useState('');

  const yükle = async () => {
    const [schRes, sabRes] = await run(() =>
      Promise.all([
        getRaporSchedules({ limit: 100 }),
        getRaporSablonlari({ limit: 100 }),
      ])
    );
    setSchedules(schRes?.data || []);
    setSablonlar(sabRes?.data || []);
  };

  useEffect(() => {
    yükle();
  }, []);

  const handleEkle = async () => {
    if (!formData.sablon_id || !formData.sablon_adi) {
      toast.error('Lütfen şablon ve ad giriniz');
      return;
    }

    try {
      await createRaporSchedule(formData);
      toast.success('Zamanlı rapor oluşturuldu');
      setYeniModal(false);
      setFormData({
        sablon_id: '',
        sablon_adi: '',
        periyod: 'haftalik',
        saat: '09:00',
        alici_emailler: [],
        format: 'pdf',
      });
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Oluşturma başarısız'));
    }
  };

  const handleGuncelle = async () => {
    try {
      await updateRaporSchedule(editModal.id, formData);
      toast.success('Zamanlı rapor güncellendi');
      setEditModal(null);
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  const handleSil = async (id) => {
    if (!confirm('Bu zamanlı raporu silmek istediğinizden emin misiniz?')) return;
    try {
      await deleteRaporSchedule(id);
      toast.success('Zamanlı rapor silindi');
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Silme başarısız'));
    }
  };

  const handleEmailEkle = () => {
    if (emailInput.trim() && !formData.alici_emailler.includes(emailInput)) {
      setFormData({
        ...formData,
        alici_emailler: [...formData.alici_emailler, emailInput],
      });
      setEmailInput('');
    }
  };

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
        <h1 className="text-3xl font-bold text-slate-900">Zamanlı Raporlar</h1>
        <button
          onClick={() => setYeniModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          <Plus className="h-5 w-5" /> Yeni Plan
        </button>
      </div>

      {schedules.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed rounded-2xl">
          <Clock className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">Zamanlı rapor planı yok</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-slate-900 mb-2">{schedule.sablon_adi}</h3>
                  <div className="flex flex-wrap gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${periyodRenkleri[schedule.periyod]}`}>
                      {schedule.periyod}
                    </span>
                    <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-semibold flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {schedule.saat}
                    </span>
                    <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-semibold">
                      {schedule.format.toUpperCase()}
                    </span>
                    {schedule.is_aktif && (
                      <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Aktif
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setEditModal(schedule);
                      setFormData({
                        sablon_id: schedule.sablon_id,
                        sablon_adi: schedule.sablon_adi,
                        periyod: schedule.periyod,
                        saat: schedule.saat,
                        alici_emailler: schedule.alici_emailler || [],
                        format: schedule.format,
                      });
                    }}
                    className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleSil(schedule.id)}
                    className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {schedule.alici_emailler && schedule.alici_emailler.length > 0 && (
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                    <Mail className="h-3 w-3" /> Alıcılar
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {schedule.alici_emailler.map((email, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium"
                      >
                        {email}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {schedule.son_calistirilma && (
                <p className="text-xs text-slate-500 mt-3">
                  Son çalıştırıldı: {new Date(schedule.son_calistirilma).toLocaleString('tr-TR')}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {(yeniModal || editModal) && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">
                {editModal ? 'Planı Düzenle' : 'Yeni Zamanlı Rapor'}
              </h2>
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
              <div>
                <label className="block text-sm font-semibold mb-2">Şablon</label>
                <select
                  value={formData.sablon_id}
                  onChange={(e) => {
                    const sablon = sablonlar.find((s) => s.id === parseInt(e.target.value));
                    setFormData({
                      ...formData,
                      sablon_id: parseInt(e.target.value),
                      sablon_adi: sablon?.ad || '',
                    });
                  }}
                  className="w-full h-11 px-4 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Şablon Seçiniz...</option>
                  {sablonlar.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.ad}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Plan Adı</label>
                <input
                  type="text"
                  value={formData.sablon_adi}
                  onChange={(e) => setFormData({ ...formData, sablon_adi: e.target.value })}
                  className="w-full h-11 px-4 rounded-lg border border-slate-200 text-sm"
                  placeholder="Örn: Haftalık Stok Raporu"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Periyot</label>
                <select
                  value={formData.periyod}
                  onChange={(e) => setFormData({ ...formData, periyod: e.target.value })}
                  className="w-full h-11 px-4 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="gunluk">Günlük</option>
                  <option value="haftalik">Haftalık</option>
                  <option value="aylik">Aylık</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Saat</label>
                <input
                  type="time"
                  value={formData.saat}
                  onChange={(e) => setFormData({ ...formData, saat: e.target.value })}
                  className="w-full h-11 px-4 rounded-lg border border-slate-200 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Format</label>
                <select
                  value={formData.format}
                  onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                  className="w-full h-11 px-4 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="pdf">PDF</option>
                  <option value="excel">Excel</option>
                  <option value="csv">CSV</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">E-posta Alıcıları</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="email"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleEmailEkle()}
                    className="flex-1 h-10 px-3 rounded-lg border border-slate-200 text-sm"
                    placeholder="E-posta ekle..."
                  />
                  <button
                    onClick={handleEmailEkle}
                    className="px-3 h-10 rounded-lg bg-blue-100 text-blue-600 font-semibold text-sm hover:bg-blue-200"
                  >
                    Ekle
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.alici_emailler.map((email, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-2"
                    >
                      {email}
                      <button
                        onClick={() => {
                          setFormData({
                            ...formData,
                            alici_emailler: formData.alici_emailler.filter((_, i) => i !== idx),
                          });
                        }}
                        className="text-slate-400 hover:text-slate-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
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
