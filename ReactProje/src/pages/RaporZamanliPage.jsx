import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Loader2, X, Edit2, Trash2, Clock, Mail, CheckCircle2, ArrowLeft, Calendar, FileText
} from 'lucide-react';
import {
  getRaporSchedules, createRaporSchedule, updateRaporSchedule, deleteRaporSchedule, getRaporSablonlari
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const periyodRenkleri = {
  'gunluk': 'bg-blue-50 text-blue-700 border-blue-100',
  'haftalik': 'bg-purple-50 text-purple-700 border-purple-100',
  'aylik': 'bg-emerald-50 text-emerald-700 border-emerald-100',
};

export default function RaporZamanliPage() {
  const navigate = useNavigate();
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

  const handleEmailEkle = (e) => {
    e?.preventDefault();
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
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-4 bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Planlar yükleniyor...</p>
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
                Zamanlı Raporlar
              </h1>
              <p className="text-slate-500 mt-1 text-sm sm:text-base">
                Otomatik rapor gönderim planlarınızı yönetin.
              </p>
            </div>
          </div>
          
          <button
            onClick={() => setYeniModal(true)}
            className="w-full sm:w-auto group flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3.5 sm:py-3 rounded-2xl sm:rounded-xl font-semibold shadow-md shadow-blue-600/20 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/30 active:scale-[0.98] transition-all duration-200"
          >
            <Plus className="h-5 w-5 group-hover:rotate-90 transition-transform duration-300" />
            Yeni Plan Oluştur
          </button>
        </div>

        {/* Plan Listesi */}
        {schedules.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border-2 border-dashed border-slate-200 flex flex-col items-center justify-center">
            <div className="h-20 w-20 bg-slate-50 rounded-full flex items-center justify-center mb-5">
              <Calendar className="h-10 w-10 text-slate-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Henüz Plan Yok</h3>
            <p className="text-slate-500 max-w-sm mx-auto">
              Belirli aralıklarla otomatik olarak oluşturulup e-posta ile gönderilecek bir rapor planı ekleyin.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className="bg-white rounded-3xl p-5 sm:p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-blue-100 hover:shadow-md transition-all duration-300 flex flex-col"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 pr-4">
                    <h3 className="text-lg font-bold text-slate-900 mb-3 leading-snug line-clamp-2">
                      {schedule.sablon_adi}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold uppercase tracking-wide flex items-center gap-1.5 ${periyodRenkleri[schedule.periyod]}`}>
                        <Calendar className="h-3.5 w-3.5" />
                        {schedule.periyod}
                      </span>
                      <span className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-700 rounded-lg text-[11px] font-bold flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" /> 
                        {schedule.saat}
                      </span>
                      <span className="px-2.5 py-1 bg-slate-800 text-white rounded-lg text-[11px] font-bold uppercase flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5" />
                        {schedule.format}
                      </span>
                      {schedule.is_aktif && (
                        <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-lg text-[11px] font-bold flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> 
                          Aktif
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Kart Aksiyonları */}
                  <div className="flex bg-slate-50 p-1 rounded-xl border border-slate-100">
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
                      className="p-2 text-blue-600 hover:bg-white hover:shadow-sm rounded-lg transition-all"
                      title="Düzenle"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleSil(schedule.id)}
                      className="p-2 text-red-600 hover:bg-white hover:shadow-sm rounded-lg transition-all"
                      title="Sil"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Alıcılar Bölümü */}
                {schedule.alici_emailler && schedule.alici_emailler.length > 0 && (
                  <div className="pt-4 mt-auto border-t border-slate-50">
                    <div className="flex items-center gap-2 mb-2.5">
                      <Mail className="h-4 w-4 text-slate-400" />
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                        Alıcılar ({schedule.alici_emailler.length})
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {schedule.alici_emailler.map((email, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 bg-slate-50 border border-slate-100 text-slate-600 rounded-md text-xs font-medium truncate max-w-full"
                          title={email}
                        >
                          {email}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Son Çalıştırılma Bilgisi */}
                {schedule.son_calistirilma && (
                  <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-400">Son Çalıştırılma:</span>
                    <span className="text-xs font-medium text-slate-600">
                      {new Date(schedule.son_calistirilma).toLocaleString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Ekle/Düzenle Modal */}
        {(yeniModal || editModal) && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-end sm:items-center justify-center sm:p-4">
            <div className="bg-white w-full sm:max-w-lg rounded-t-[2rem] sm:rounded-3xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto shadow-2xl transform transition-all animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
              
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                    {editModal ? 'Planı Düzenle' : 'Yeni Zamanlı Rapor'}
                  </h2>
                  <p className="text-sm text-slate-500 mt-1">Raporun ne zaman ve kime gideceğini ayarlayın.</p>
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
                {/* Şablon Seçimi */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Şablon Seçimi</label>
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
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  >
                    <option value="">Şablon Seçiniz...</option>
                    {sablonlar.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.ad}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Plan Adı */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Plan Adı</label>
                  <input
                    type="text"
                    value={formData.sablon_adi}
                    onChange={(e) => setFormData({ ...formData, sablon_adi: e.target.value })}
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                    placeholder="Örn: Haftalık Satış Özet Raporu"
                  />
                </div>

                {/* Periyot ve Saat (Yan yana) */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Periyot</label>
                    <select
                      value={formData.periyod}
                      onChange={(e) => setFormData({ ...formData, periyod: e.target.value })}
                      className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                    >
                      <option value="gunluk">Günlük</option>
                      <option value="haftalik">Haftalık</option>
                      <option value="aylik">Aylık</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Saat</label>
                    <input
                      type="time"
                      value={formData.saat}
                      onChange={(e) => setFormData({ ...formData, saat: e.target.value })}
                      className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                    />
                  </div>
                </div>

                {/* Format */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Çıktı Formatı</label>
                  <select
                    value={formData.format}
                    onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  >
                    <option value="pdf">PDF Dokümanı</option>
                    <option value="excel">Excel Tablosu</option>
                    <option value="csv">CSV Dosyası</option>
                  </select>
                </div>

                {/* E-posta Alıcıları */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">E-posta Alıcıları</label>
                  <div className="flex gap-2 mb-3 relative">
                    <input
                      type="email"
                      value={emailInput}
                      onChange={(e) => setEmailInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleEmailEkle(e)}
                      className="flex-1 h-12 pl-10 pr-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                      placeholder="ornek@sirket.com"
                    />
                    <Mail className="absolute left-3.5 top-3.5 h-5 w-5 text-slate-400 pointer-events-none" />
                    <button
                      onClick={handleEmailEkle}
                      type="button"
                      className="px-5 h-12 rounded-xl bg-slate-800 text-white font-semibold text-sm hover:bg-slate-900 transition-colors shadow-sm"
                    >
                      Ekle
                    </button>
                  </div>
                  
                  {formData.alici_emailler.length > 0 && (
                    <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-xl border border-slate-100">
                      {formData.alici_emailler.map((email, idx) => (
                        <div
                          key={idx}
                          className="pl-3 pr-1.5 py-1.5 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm"
                        >
                          {email}
                          <button
                            onClick={() => {
                              setFormData({
                                ...formData,
                                alici_emailler: formData.alici_emailler.filter((_, i) => i !== idx),
                              });
                            }}
                            className="p-1 bg-slate-100 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
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
                  {editModal ? 'Değişiklikleri Kaydet' : 'Planı Oluştur'}
                </button>
              </div>
              
            </div>
          </div>
        )}
      </div>
    </div>
  );
}