import React, { useState, useEffect } from 'react';
import { getTedarikciler, addTedarikci } from '../services/api';
import {
  Building2,
  User,
  Phone,
  Mail,
  Plus,
  Truck,
  Loader2,
  SearchX,
  MapPin,
  FileSignature
} from 'lucide-react';

// ---------------------------------------------------------------------------------

const TedarikcilerPage = () => {
  // Durum (State) Yönetimi
  const [tedarikciler, setTedarikciler] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form Durumu
  const [formData, setFormData] = useState({
    firma_adi: '',
    iletisim_kisi: '',
    telefon: '',
    email: '',
    adres: '',
    vergi_no: ''
  });

  // Sayfa yüklendiğinde tedarikçileri getir
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await getTedarikciler();
      setTedarikciler(response.data);
    } catch (error) {
      console.error("Veriler çekilirken hata oluştu:", error);
      alert("Tedarikçiler yüklenirken bir sorun oluştu.");
    } finally {
      setLoading(false);
    }
  };

  // Form elemanları değiştiğinde state'i güncelle
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Form gönderildiğinde (Yeni kayıt)
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.firma_adi) {
      alert("Firma Adı zorunludur!");
      return;
    }

    try {
      await addTedarikci(formData);
      setFormData({ firma_adi: '', iletisim_kisi: '', telefon: '', email: '', adres: '', vergi_no: '' });
      fetchData();
    } catch (error) {
      console.error("Eklerken hata:", error);
      alert("Tedarikçi eklenemedi. Lütfen tekrar deneyin.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">

        {/* Sayfa Başlığı */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-600 rounded-xl shadow-md shadow-indigo-600/20 flex items-center justify-center text-white shrink-0">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Tedarikçi Yönetimi</h1>
              <p className="text-sm text-slate-500 mt-1">Sistemdeki tedarikçileri görüntüleyin ve yönetin.</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">

          {/* SOL TARAF: Ekleme Formu */}
          <div className="w-full lg:w-[400px] xl:w-[450px] shrink-0">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden lg:sticky lg:top-6">
              <div className="px-5 sm:px-6 py-5 border-b border-slate-100 bg-slate-50/50">
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2.5">
                  <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600">
                    <Plus className="w-4 h-4 stroke-[3]" />
                  </div>
                  Yeni Tedarikçi Ekle
                </h2>
              </div>

              <form onSubmit={handleSubmit} className="p-5 sm:px-6 py-6 space-y-4">

                {/* Firma Adı */}
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-slate-400" />
                    Firma Adı <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="firma_adi"
                    value={formData.firma_adi}
                    onChange={handleChange}
                    className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                    placeholder="Örn: ABC Lojistik A.Ş."
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                  {/* İletişim Kişisi */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400" />
                      İletişim Kişisi
                    </label>
                    <input
                      type="text"
                      name="iletisim_kisi"
                      value={formData.iletisim_kisi}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: Ayşe Yılmaz"
                    />
                  </div>

                  {/* Telefon */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-400" />
                      Telefon
                    </label>
                    <input
                      type="text"
                      name="telefon"
                      value={formData.telefon}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: 0555 123 45 67"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                  {/* E-posta */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      E-posta
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: info@firma.com"
                    />
                  </div>

                  {/* Vergi Numarası */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <FileSignature className="w-4 h-4 text-slate-400" />
                      Vergi No / TC
                    </label>
                    <input
                      type="text"
                      name="vergi_no"
                      value={formData.vergi_no}
                      onChange={handleChange}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400"
                      placeholder="Örn: 1234567890"
                    />
                  </div>
                </div>

                {/* Adres */}
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    Açık Adres
                  </label>
                  <textarea
                    name="adres"
                    value={formData.adres}
                    onChange={handleChange}
                    className="w-full min-h-[90px] p-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-400 resize-y"
                    placeholder="Firma açık adresi..."
                  />
                </div>

                {/* Kaydet Butonu */}
                <button
                  type="submit"
                  className="w-full mt-2 h-12 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-sm transition-all hover:bg-indigo-700 active:scale-[0.98]"
                >
                  <Plus className="w-5 h-5" />
                  <span>Tedarikçiyi Kaydet</span>
                </button>

              </form>
            </div>
          </div>

          {/* SAĞ TARAF: Tedarikçi Listesi (Kart Grid Yapısı) */}
          <div className="w-full flex-1">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-full flex flex-col">

              <div className="px-5 sm:px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2.5">
                  <div className="p-1.5 bg-slate-200 text-slate-600 rounded-lg">
                    <Building2 className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  Kayıtlı Tedarikçiler
                </h2>
                <span className="bg-white border border-slate-200 text-indigo-600 text-xs font-bold px-3 py-1.5 rounded-full shadow-sm">
                  {tedarikciler.length} Kayıt
                </span>
              </div>

              <div className="p-4 sm:p-5 flex-1 bg-slate-50/30">
                {loading ? (
                  // Yükleniyor Durumu
                  <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                    <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mb-4" />
                    <p className="text-sm font-medium animate-pulse">Veriler yükleniyor...</p>
                  </div>
                ) : tedarikciler.length === 0 ? (
                  // Boş Durum
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                    <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4 border border-slate-200 shadow-sm">
                      <SearchX className="w-8 h-8 text-slate-300" />
                    </div>
                    <p className="text-base font-bold text-slate-700">Tedarikçi Bulunamadı</p>
                    <p className="text-sm mt-1 text-center max-w-sm">Sol taraftaki formu kullanarak sisteme ilk tedarikçinizi ekleyebilirsiniz.</p>
                  </div>
                ) : (
                  // Kart Grid Listesi (Tablo yerine mobilde çok daha şık durur)
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {tedarikciler.map((t) => (
                      <div 
                        key={t.id} 
                        className="bg-white border border-slate-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-md transition-all duration-200 group flex flex-col"
                      >
                        <div className="flex items-start gap-3 mb-4 pb-4 border-b border-slate-100">
                          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                            <Building2 className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-slate-900 truncate group-hover:text-indigo-600 transition-colors" title={t.firma_adi}>
                              {t.firma_adi}
                            </h3>
                            <p className="text-xs font-medium text-slate-400 mt-0.5">ID: #{t.id}</p>
                          </div>
                        </div>

                        <div className="space-y-3 flex-1">
                          {t.iletisim_kisi ? (
                            <div className="flex items-start gap-2.5 text-sm text-slate-700">
                              <User className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <span className="font-medium">{t.iletisim_kisi}</span>
                            </div>
                          ) : null}

                          {(t.telefon || t.email) ? (
                            <div className="flex flex-col gap-2">
                              {t.telefon && (
                                <div className="flex items-center gap-2.5 text-sm text-slate-600">
                                  <Phone className="w-4 h-4 text-slate-400 shrink-0" />
                                  <span>{t.telefon}</span>
                                </div>
                              )}
                              {t.email && (
                                <div className="flex items-center gap-2.5 text-sm text-slate-600">
                                  <Mail className="w-4 h-4 text-slate-400 shrink-0" />
                                  <span className="truncate" title={t.email}>{t.email}</span>
                                </div>
                              )}
                            </div>
                          ) : (
                            !t.iletisim_kisi && <span className="text-sm text-slate-400 italic">İletişim bilgisi eklenmemiş</span>
                          )}

                          {t.vergi_no && (
                            <div className="flex items-center gap-2.5 text-sm text-slate-600">
                              <FileSignature className="w-4 h-4 text-slate-400 shrink-0" />
                              <span>VN: <span className="font-medium">{t.vergi_no}</span></span>
                            </div>
                          )}

                          {t.adres && (
                            <div className="flex items-start gap-2.5 text-sm text-slate-600 mt-2 pt-3 border-t border-slate-50">
                              <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                              <span className="line-clamp-2 leading-relaxed" title={t.adres}>{t.adres}</span>
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