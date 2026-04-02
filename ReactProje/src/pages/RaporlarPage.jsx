import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, TrendingUp, FileText, Clock, Loader2, Plus, Eye, ArrowRight, Settings
} from 'lucide-react';
import { getRaporSablonlari, getRaporLoglari } from '../services/api';
import { useAsync } from '../hooks/useAsync';

const turRenkleri = {
  'stok': 'bg-blue-50 text-blue-700 border-blue-100',
  'siparis': 'bg-emerald-50 text-emerald-700 border-emerald-100',
  'finansal': 'bg-amber-50 text-amber-700 border-amber-100',
  'performans': 'bg-purple-50 text-purple-700 border-purple-100',
};

const turIkonlari = {
  'stok': BarChart3,
  'siparis': TrendingUp,
  'finansal': FileText,
  'performans': BarChart3,
};

export default function RaporlarPage() {
  const navigate = useNavigate();
  const { loading, run } = useAsync(true);
  const [sablonlar, setSablonlar] = useState([]);
  const [loglar, setLoglar] = useState([]);
  const [seciliTur, setSeciliTur] = useState('');

  useEffect(() => {
    let aktif = true;

    run(() =>
      Promise.all([
        getRaporSablonlari({ limit: 100 }),
        getRaporLoglari({ limit: 10 }),
      ])
    )
      .then(([sabRes, logRes]) => {
        if (aktif) {
          setSablonlar(sabRes?.data || []);
          setLoglar(logRes?.data || []);
        }
      })
      .catch(() => {});

    return () => {
      aktif = false;
    };
  }, [run]);

  const filtrelenmis = seciliTur
    ? sablonlar.filter((s) => s.tur === seciliTur)
    : sablonlar;

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-4 bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Raporlar hazırlanıyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12 sm:pb-20">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-10">

        {/* Başlık ve Aksiyon Alanı */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-5 mb-8 sm:mb-10">
          <div className="flex-1">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 tracking-tight">
              Raporlama Merkezi
            </h1>
            <p className="text-slate-500 mt-1.5 sm:mt-2 text-sm sm:text-base">
              Kapsamlı iş raporları oluşturun, zamanlayın ve verilerinizi analiz edin.
            </p>
          </div>
          <button
            onClick={() => navigate('/raporlar/olustur')}
            className="w-full sm:w-auto group flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3.5 sm:py-3 rounded-2xl sm:rounded-xl font-semibold shadow-md shadow-blue-600/20 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/30 active:scale-[0.98] transition-all duration-200"
          >
            <Plus className="h-5 w-5 group-hover:rotate-90 transition-transform duration-300" /> 
            <span>Yeni Rapor</span>
          </button>
        </div>

        {/* Özet Kartları (İstatistikler) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8 sm:mb-12">
          {/* Kart 1 */}
          <div className="bg-white rounded-3xl p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-blue-100 hover:shadow-md transition-all duration-300 group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs sm:text-sm font-bold uppercase tracking-wider mb-1">Toplam Şablon</p>
                <p className="text-3xl sm:text-4xl font-extrabold text-slate-900 group-hover:text-blue-600 transition-colors">{sablonlar.length}</p>
              </div>
              <div className="h-14 w-14 rounded-2xl bg-blue-50/50 border border-blue-50 flex items-center justify-center group-hover:bg-blue-50 transition-colors">
                <FileText className="h-7 w-7 text-blue-500" />
              </div>
            </div>
          </div>

          {/* Kart 2 */}
          <div className="bg-white rounded-3xl p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-emerald-100 hover:shadow-md transition-all duration-300 group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs sm:text-sm font-bold uppercase tracking-wider mb-1">Son Raporlar</p>
                <p className="text-3xl sm:text-4xl font-extrabold text-slate-900 group-hover:text-emerald-600 transition-colors">{loglar.length}</p>
              </div>
              <div className="h-14 w-14 rounded-2xl bg-emerald-50/50 border border-emerald-50 flex items-center justify-center group-hover:bg-emerald-50 transition-colors">
                <TrendingUp className="h-7 w-7 text-emerald-500" />
              </div>
            </div>
          </div>

          {/* Kart 3 (Tıklanabilir) - Zamanlı Raporlar */}
          <button
            onClick={() => navigate('/raporlar/zamanli')}
            className="w-full text-left bg-white rounded-3xl p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-amber-200 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 group"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs sm:text-sm font-bold uppercase tracking-wider mb-1">Zamanlı Raporlar</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-lg font-bold text-slate-900 group-hover:text-amber-600 transition-colors">
                    Yönetimi Aç
                  </span>
                  <ArrowRight className="h-5 w-5 text-amber-500 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
              <div className="h-14 w-14 rounded-2xl bg-amber-50/50 border border-amber-50 flex items-center justify-center group-hover:bg-amber-50 transition-colors">
                <Clock className="h-7 w-7 text-amber-500" />
              </div>
            </div>
          </button>

          {/* Kart 4 (Tıklanabilir) - Şablonları Yönet */}
          <button
            onClick={() => navigate('/raporlar/sablonlar')}
            className="w-full text-left bg-white rounded-3xl p-6 shadow-sm shadow-slate-200/50 border border-slate-100 hover:border-indigo-200 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 group"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs sm:text-sm font-bold uppercase tracking-wider mb-1">Rapor Şablonları</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    Yönetimi Aç
                  </span>
                  <ArrowRight className="h-5 w-5 text-indigo-500 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
              <div className="h-14 w-14 rounded-2xl bg-indigo-50/50 border border-indigo-50 flex items-center justify-center group-hover:bg-indigo-50 transition-colors">
                <Settings className="h-7 w-7 text-indigo-500" />
              </div>
            </div>
          </button>
        </div>

        {/* Rapor Türü Filtreleri (Mobil için yatay kaydırma eklendi) */}
        <div className="mb-6 sm:mb-8 -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="flex overflow-x-auto pb-4 sm:pb-0 gap-2 sm:gap-3 snap-x hide-scrollbar" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            <button
              onClick={() => setSeciliTur('')}
              className={`snap-start whitespace-nowrap px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200 ${
                !seciliTur
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
              }`}
            >
              Tüm Şablonlar
            </button>
            {['stok', 'siparis', 'finansal', 'performans'].map((tur) => (
              <button
                key={tur}
                onClick={() => setSeciliTur(tur)}
                className={`snap-start whitespace-nowrap px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200 border ${
                  seciliTur === tur
                    ? 'bg-slate-800 text-white border-slate-800 shadow-md'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                {tur.charAt(0).toUpperCase() + tur.slice(1)} Raporları
              </button>
            ))}
          </div>
        </div>

        {/* Şablonlar Listesi */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6 mb-12 sm:mb-16">
          {filtrelenmis.length === 0 ? (
            <div className="md:col-span-2 lg:col-span-3 bg-white rounded-3xl p-12 text-center border-2 border-dashed border-slate-200">
              <div className="h-16 w-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Şablon Bulunamadı</h3>
              <p className="text-slate-500 font-medium text-sm">Seçili kritere uygun bir rapor şablonu mevcut değil.</p>
            </div>
          ) : (
            filtrelenmis.map((sablon) => {
              const Icon = turIkonlari[sablon.tur] || FileText;
              return (
                <div
                  key={sablon.id}
                  className="bg-white rounded-3xl shadow-sm shadow-slate-200/40 border border-slate-100 hover:border-slate-300 hover:shadow-lg hover:shadow-slate-200/50 transition-all duration-300 flex flex-col group"
                >
                  <div className="p-5 sm:p-6 flex-1 flex flex-col">
                    <div className="flex items-start gap-4 mb-4">
                      <div className={`h-12 w-12 rounded-2xl flex items-center justify-center flex-shrink-0 border ${turRenkleri[sablon.tur]}`}>
                        <Icon className="h-6 w-6" />
                      </div>
                      <div className="flex-1 pt-1">
                        <h3 className="text-[17px] leading-snug font-bold text-slate-900 mb-1.5 group-hover:text-blue-600 transition-colors line-clamp-2">
                          {sablon.ad}
                        </h3>
                        <span className={`inline-block px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wide border ${turRenkleri[sablon.tur]}`}>
                          {sablon.tur}
                        </span>
                      </div>
                    </div>

                    {sablon.aciklama && (
                      <p className="text-slate-500 text-sm mb-6 line-clamp-2 flex-1 leading-relaxed">
                        {sablon.aciklama}
                      </p>
                    )}

                    <div className="flex gap-2 sm:gap-3 pt-4 border-t border-slate-50 mt-auto">
                      <button
                        onClick={() =>
                          navigate('/raporlar/olustur', {
                            state: { sablon_id: sablon.id },
                          })
                        }
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 sm:py-2 bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white rounded-xl font-bold text-sm transition-all duration-200"
                      >
                        <Eye className="h-4 w-4" /> Oluştur
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Son Oluşturulan Raporlar Tablosu */}
        {loglar.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900">Son Raporlar</h2>
            </div>
            <div className="bg-white rounded-3xl shadow-sm shadow-slate-200/40 border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/80 border-b border-slate-100">
                      <th className="px-5 sm:px-6 py-4 text-xs font-extrabold text-slate-400 uppercase tracking-wider whitespace-nowrap">Şablon ID</th>
                      <th className="px-5 sm:px-6 py-4 text-xs font-extrabold text-slate-400 uppercase tracking-wider whitespace-nowrap">Durum</th>
                      <th className="px-5 sm:px-6 py-4 text-xs font-extrabold text-slate-400 uppercase tracking-wider whitespace-nowrap">Tarih</th>
                      <th className="px-5 sm:px-6 py-4 text-xs font-extrabold text-slate-400 uppercase tracking-wider whitespace-nowrap text-right">Süre</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {loglar.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-5 sm:px-6 py-4 whitespace-nowrap">
                          <span className="font-semibold text-slate-700 text-sm">
                            {log.sablon_id || 'Ad Hoc Rapor'}
                          </span>
                        </td>
                        <td className="px-5 sm:px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold border ${
                              log.durum === 'Basarili'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                                : 'bg-red-50 text-red-700 border-red-100'
                            }`}
                          >
                            {log.durum === 'Basarili' && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2"></div>}
                            {log.durum !== 'Basarili' && <div className="w-1.5 h-1.5 rounded-full bg-red-500 mr-2"></div>}
                            {log.durum}
                          </span>
                        </td>
                        <td className="px-5 sm:px-6 py-4 whitespace-nowrap text-slate-500 text-sm font-medium">
                          {new Date(log.olusturma_tarihi).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </td>
                        <td className="px-5 sm:px-6 py-4 whitespace-nowrap text-slate-500 text-sm font-medium text-right">
                          {log.tamamlanma_tarihi
                            ? (new Date(log.tamamlanma_tarihi) - new Date(log.olusturma_tarihi)) / 1000 + ' sn'
                            : <span className="text-slate-300">-</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
