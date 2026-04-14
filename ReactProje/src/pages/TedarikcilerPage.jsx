import React, { useState, useEffect, useCallback } from 'react';
import { getTedarikciler, addTedarikci } from '../services/api';
import {
  Building2,
  User,
  Phone,
  Mail,
  Plus,
  Truck,
  SearchX,
  MapPin,
  FileSignature,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X
} from 'lucide-react';

// ---------------------------------------------------------------------------------

const TedarikcilerPage = () => {
  // Durum (State) Yönetimi
  const [tedarikciler, setTedarikciler] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  
  // Bildirim (Toast) Durumu
  const [toast, setToast] = useState({ show: false, type: '', message: '' });

  // Form Durumu
  const [formData, setFormData] = useState({
    firma_adi: '',
    iletisim_kisi: '',
    telefon: '',
    email: '',
    adres: '',
    vergi_no: ''
  });

  const showToast = useCallback((type, message) => {
    setToast({ show: true, type, message });
    setTimeout(() => {
      setToast({ show: false, type: '', message: '' });
    }, 3000);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getTedarikciler();
      setTedarikciler(response.data || []);
    } catch (error) {
      console.error("Veriler çekilirken hata oluştu:", error);
      showToast('error', 'Tedarikçiler yüklenirken bir sorun oluştu.');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Sayfa yüklendiğinde tedarikçileri getir
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Form elemanları değiştiğinde state'i güncelle
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Hata durumunu temizle (Kullanıcı yazmaya başladığında)
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: false }));
    }
  };

  // Form gönderildiğinde (Yeni kayıt)
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Basit Validasyon
    if (!formData.firma_adi.trim()) {
      setErrors({ firma_adi: true });
      showToast('error', 'Lütfen firma adını giriniz.');
      return;
    }

    try {
      setIsSubmitting(true);
      await addTedarikci(formData);
      setFormData({ firma_adi: '', iletisim_kisi: '', telefon: '', email: '', adres: '', vergi_no: '' });
      showToast('success', 'Tedarikçi başarıyla eklendi.');
      fetchData();
    } catch (error) {
      console.error("Eklerken hata:", error);
      showToast('error', 'Tedarikçi eklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Yükleme durumu için Skeleton Kart
  const SkeletonCard = () => (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm animate-pulse flex flex-col h-full">
      <div className="flex items-start gap-3 mb-4 pb-4 border-b border-slate-50">
        <div className="w-10 h-10 rounded-xl bg-slate-100 shrink-0"></div>
        <div className="flex-1 space-y-2 py-1">
          <div className="h-4 bg-slate-200 rounded w-3/4"></div>
          <div className="h-3 bg-slate-100 rounded w-1/3"></div>
        </div>
      </div>
      <div className="space-y-3 flex-1 py-1">
        <div className="h-3 bg-slate-100 rounded w-1/2"></div>
        <div className="h-3 bg-slate-100 rounded w-2/3"></div>
        <div className="h-3 bg-slate-100 rounded w-3/4"></div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12 relative">
      
      {/* Toast Bildirim Sistemi */}
      <div className={`fixed top-6 right-6 z-50 transition-all duration-300 transform ${toast.show ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0 pointer-events-none'}`}>
        <div className={`flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl border ${toast.type === 'success' ? 'bg-emerald-50 border-emerald-100 text-emerald-800' : 'bg-red-50 border-red-100 text-red-800'}`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <AlertCircle className="w-5 h-5 text-red-600" />}
          <p className="text-sm font-semibold">{toast.message}</p>
          <button onClick={() => setToast({show: false})} className="ml-2 text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">

        {/* Sayfa Başlığı */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl shadow-lg shadow-indigo-600/20 flex items-center justify-center text-white shrink-0 ring-4 ring-white">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Tedarikçi Yönetimi</h1>
              <p className="text-sm text-slate-500 mt-1 font-medium">Sistemdeki tedarikçileri görüntüleyin ve yeni kayıt oluşturun.</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">

          {/* SOL TARAF: Ekleme Formu (Mobilde Üstte) */}
          <div className="w-full lg:w-[400px] xl:w-[420px] shrink-0">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-200/60 overflow-hidden lg:sticky lg:top-6 transition-all">
              <div className="px-6 py-5 border-b border-slate-100 bg-white">
                <h2 className="text-base font-bold text-slate-800 flex items-center gap-3">
                  <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
                    <Plus className="w-4 h-4 stroke-[3]" />
                  </div>
                  Yeni Tedarikçi Ekle
                </h2>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-5">

                {/* Firma Adı */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    Firma Adı <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="firma_adi"
                    value={formData.firma_adi}
                    onChange={handleChange}
                    className={`w-full h-12 px-4 text-sm font-medium rounded-xl border bg-slate-50/50 focus:bg-white focus:ring-4 focus:outline-none transition-all placeholder:text-slate-400 ${errors.firma_adi ? 'border-red-300 focus:border-red-500 focus:ring-red-500/10' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-500/10'}`}
                    placeholder="Örn: ABC Lojistik A.Ş."
                  />
                  {errors.firma_adi && <p className="text-xs font-medium text-red-500 mt-1">Firma adı zorunludur.</p>}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-5">
                  {/* İletişim Kişisi */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      İletişim Kişisi
                    </label>
                    <input
                      type="text"
                      name="iletisim_kisi"
                      value={formData.iletisim_kisi}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: Ayşe Yılmaz"
                    />
                  </div>

                  {/* Telefon */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      Telefon
                    </label>
                    <input
                      type="text"
                      name="telefon"
                      value={formData.telefon}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: 0555 123 45 67"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-5">
                  {/* E-posta */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      E-posta
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: info@firma.com"
                    />
                  </div>

                  {/* Vergi Numarası */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                      <FileSignature className="w-3.5 h-3.5 text-slate-400" />
                      Vergi No / TC
                    </label>
                    <input
                      type="text"
                      name="vergi_no"
                      value={formData.vergi_no}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: 1234567890"
                    />
                  </div>
                </div>

                {/* Adres */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    Açık Adres
                  </label>
                  <textarea
                    name="adres"
                    value={formData.adres}
                    onChange={handleChange}
                    className="w-full min-h-[100px] p-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400 resize-y"
                    placeholder="Firma açık adresi..."
                  />
                </div>

                {/* Kaydet Butonu */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-4 h-12 flex items-center justify-center gap-2 rounded-xl bg-slate-900 text-sm font-bold text-white shadow-md shadow-slate-900/10 transition-all hover:bg-indigo-600 hover:shadow-indigo-600/20 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:bg-slate-900"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Kaydediliyor...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5" />
                      <span>Tedarikçiyi Kaydet</span>
                    </>
                  )}
                </button>

              </form>
            </div>
          </div>

          {/* SAĞ TARAF: Tedarikçi Listesi (Kart Grid Yapısı) */}
          <div className="w-full flex-1">
            <div className="bg-transparent h-full flex flex-col">

              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-bold text-slate-800 flex items-center gap-2.5">
                  Kayıtlı Tedarikçiler
                </h2>
                {!loading && (
                  <span className="bg-white border border-slate-200 text-slate-600 text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm">
                    Toplam {tedarikciler.length}
                  </span>
                )}
              </div>

              <div className="flex-1">
                {loading ? (
                  // Şık Skeleton Yükleme Durumu
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2, 3, 4].map(key => <SkeletonCard key={key} />)}
                  </div>
                ) : tedarikciler.length === 0 ? (
                  // Boş Durum
                  <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-slate-200 border-dashed">
                    <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 border border-slate-100 shadow-sm">
                      <SearchX className="w-8 h-8 text-slate-400" />
                    </div>
                    <p className="text-base font-bold text-slate-700">Henüz Kayıt Yok</p>
                    <p className="text-sm mt-2 text-center text-slate-500 max-w-sm">
                      Sisteme henüz bir tedarikçi eklenmemiş. Sol taraftaki formu kullanarak ilk kaydınızı oluşturabilirsiniz.
                    </p>
                  </div>
                ) : (
                  // Kart Grid Listesi
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {tedarikciler.map((t) => (
                      <div 
                        key={t.id} 
                        className="bg-white border border-slate-200/60 rounded-2xl p-5 hover:border-indigo-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group flex flex-col"
                      >
                        <div className="flex items-start gap-3 mb-4 pb-4 border-b border-slate-100">
                          <div className="w-11 h-11 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-500 shrink-0 group-hover:bg-indigo-50 group-hover:text-indigo-600 group-hover:border-indigo-100 transition-colors">
                            <Building2 className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0 mt-0.5">
                            <h3 className="text-base font-bold text-slate-900 truncate group-hover:text-indigo-600 transition-colors" title={t.firma_adi}>
                              {t.firma_adi}
                            </h3>
                            <p className="text-[11px] font-bold text-slate-400 mt-1 uppercase tracking-wider">Kayıt No: #{t.id}</p>
                          </div>
                        </div>

                        <div className="space-y-3.5 flex-1">
                          {t.iletisim_kisi && (
                            <div className="flex items-start gap-3 text-sm text-slate-600">
                              <User className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <span className="font-semibold">{t.iletisim_kisi}</span>
                            </div>
                          )}

                          {(t.telefon || t.email) ? (
                            <div className="flex flex-col gap-2.5">
                              {t.telefon && (
                                <div className="flex items-center gap-3 text-sm text-slate-600">
                                  <Phone className="w-4 h-4 text-slate-400 shrink-0" />
                                  <span className="font-medium">{t.telefon}</span>
                                </div>
                              )}
                              {t.email && (
                                <div className="flex items-center gap-3 text-sm text-slate-600">
                                  <Mail className="w-4 h-4 text-slate-400 shrink-0" />
                                  <span className="font-medium truncate" title={t.email}>{t.email}</span>
                                </div>
                              )}
                            </div>
                          ) : (
                            !t.iletisim_kisi && <span className="text-sm text-slate-400 italic">İletişim detayı girilmemiş.</span>
                          )}

                          {t.vergi_no && (
                            <div className="flex items-center gap-3 text-sm text-slate-600">
                              <FileSignature className="w-4 h-4 text-slate-400 shrink-0" />
                              <span>Vergi No: <span className="font-semibold">{t.vergi_no}</span></span>
                            </div>
                          )}

                          {t.adres && (
                            <div className="flex items-start gap-3 text-sm text-slate-600 mt-2 pt-3 border-t border-slate-50">
                              <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <span className="line-clamp-2 leading-relaxed font-medium text-slate-500" title={t.adres}>{t.adres}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default function App() {
  return <TedarikcilerPage />;
}