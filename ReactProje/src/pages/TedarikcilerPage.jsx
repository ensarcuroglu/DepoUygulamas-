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
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto min-h-screen bg-slate-50/50">

      {/* Sayfa Başlığı */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 bg-white rounded-2xl shadow-sm border border-slate-200 flex items-center justify-center text-indigo-600">
          <Truck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Tedarikçi Yönetimi</h1>
          <p className="text-sm text-slate-500 mt-1">Sistemdeki tedarikçileri görüntüleyin ve yeni firmalar ekleyin.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* SOL TARAF: Ekleme Formu */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <Plus className="w-5 h-5 text-indigo-500" />
                Yeni Tedarikçi Ekle
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">

              {/* Firma Adı */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-slate-400" />
                  Firma Adı <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="firma_adi"
                  value={formData.firma_adi}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400"
                  placeholder="Örn: ABC Lojistik A.Ş."
                />
              </div>

              {/* İletişim Kişisi */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <User className="w-4 h-4 text-slate-400" />
                  İletişim Kişisi
                </label>
                <input
                  type="text"
                  name="iletisim_kisi"
                  value={formData.iletisim_kisi}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400"
                  placeholder="Örn: Ayşe Yılmaz"
                />
              </div>

              {/* Telefon */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <Phone className="w-4 h-4 text-slate-400" />
                  Telefon
                </label>
                <input
                  type="text"
                  name="telefon"
                  value={formData.telefon}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400"
                  placeholder="Örn: 0555 123 45 67"
                />
              </div>

              {/* E-posta */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-slate-400" />
                  E-posta
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400"
                  placeholder="Örn: info@abclojistik.com"
                />
              </div>

              {/* Vergi Numarası */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <FileSignature className="w-4 h-4 text-slate-400" />
                  Vergi Numarası / TC
                </label>
                <input
                  type="text"
                  name="vergi_no"
                  value={formData.vergi_no}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400"
                  placeholder="Örn: 1234567890"
                />
              </div>

              {/* Adres */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  Açık Adres
                </label>
                <textarea
                  name="adres"
                  value={formData.adres}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition-all bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 placeholder:text-slate-400 resize-none h-20"
                  placeholder="Firma açık adresi..."
                />
              </div>

              {/* Kaydet Butonu */}
              <button
                type="submit"
                className="group relative w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition-all duration-300 hover:bg-indigo-600 hover:shadow-indigo-600/30 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]"
              >
                <Plus className="w-5 h-5 transition-transform duration-300 group-hover:rotate-90" />
                <span>Tedarikçiyi Kaydet</span>
              </button>

            </form>
          </div>
        </div>

        {/* SAĞ TARAF: Tedarikçi Listesi (Tablo) */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-full flex flex-col">

            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-indigo-500" />
                Kayıtlı Tedarikçiler
              </h2>
              <span className="bg-white border border-slate-200 text-slate-600 text-xs font-bold px-3 py-1 rounded-full shadow-sm">
                {tedarikciler.length} Kayıt
              </span>
            </div>

            <div className="p-0 overflow-x-auto flex-1">
              {loading ? (
                // Yükleniyor Durumu
                <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
                  <p className="text-sm font-medium">Veriler yükleniyor...</p>
                </div>
              ) : tedarikciler.length === 0 ? (
                // Boş Durum (Empty State)
                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                  <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 border border-slate-100">
                    <SearchX className="w-8 h-8 text-slate-300" />
                  </div>
                  <p className="text-base font-medium text-slate-600">Henüz kayıtlı tedarikçi yok</p>
                  <p className="text-sm mt-1">Sol taraftaki formu kullanarak ilk tedarikçiyi ekleyebilirsiniz.</p>
                </div>
              ) : (
                // Veri Tablosu
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/50 border-b border-slate-100">
                      <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Firma Bilgileri</th>
                      <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Yetkili Kişi</th>
                      <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">İletişim</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {tedarikciler.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50/80 transition-colors group">

                        {/* Firma Sütunu */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 group-hover:scale-105 transition-transform">
                              <Building2 className="w-5 h-5" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{t.firma_adi}</p>
                              <p className="text-xs text-slate-400 mt-0.5">ID: #{t.id}</p>
                            </div>
                          </div>
                        </td>

                        {/* Yetkili Sütunu */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                              <User className="w-3.5 h-3.5" />
                            </div>
                            <span className="text-sm text-slate-600 font-medium">
                              {t.iletisim_kisi || <span className="text-slate-400 italic">Belirtilmedi</span>}
                            </span>
                          </div>
                        </td>

                        {/* İletişim Sütunu */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-2">
                            {t.telefon && (
                              <div className="flex items-center gap-2 text-sm text-slate-600">
                                <Phone className="w-3.5 h-3.5 text-slate-400" />
                                <span>{t.telefon}</span>
                              </div>
                            )}
                            {t.email && (
                              <div className="flex items-center gap-2 text-sm text-slate-600">
                                <Mail className="w-3.5 h-3.5 text-slate-400" />
                                <span>{t.email}</span>
                              </div>
                            )}
                            {!t.telefon && !t.email && (
                              <span className="text-sm text-slate-400 italic">İletişim bilgisi yok</span>
                            )}
                            {t.adres && (
                              <div className="mt-1 pt-2 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-500">
                                <MapPin className="w-3.5 h-3.5 mt-0.5 text-slate-400 flex-shrink-0" />
                                <span className="line-clamp-2">{t.adres}</span>
                              </div>
                            )}
                            {t.vergi_no && (
                              <div className="flex items-center gap-2 text-xs text-slate-500">
                                <FileSignature className="w-3.5 h-3.5 text-slate-400" />
                                <span>VN: {t.vergi_no}</span>
                              </div>
                            )}
                          </div>
                        </td>

                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
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