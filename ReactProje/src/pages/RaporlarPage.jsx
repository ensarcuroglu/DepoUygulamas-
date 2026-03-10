import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, TrendingUp, FileText, Clock, Loader2, Plus, Eye, Trash2, ArrowRight
} from 'lucide-react';
import { getRaporSablonlari, getRaporLoglari } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const turRenkleri = {
  'stok': 'bg-blue-50 text-blue-700 border border-blue-200',
  'siparis': 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  'finansal': 'bg-amber-50 text-amber-700 border border-amber-200',
  'performans': 'bg-purple-50 text-purple-700 border border-purple-200',
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

  const yükle = async () => {
    const [sabRes, logRes] = await run(() =>
      Promise.all([
        getRaporSablonlari({ limit: 100 }),
        getRaporLoglari({ limit: 10 }),
      ])
    );
    setSablonlar(sabRes?.data || []);
    setLoglar(logRes?.data || []);
  };

  useEffect(() => {
    yükle();
  }, []);

  const filtrelenmis = seciliTur
    ? sablonlar.filter((s) => s.tur === seciliTur)
    : sablonlar;

  if (loading) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium">Raporlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 pb-12">
      <div className="max-w-[1400px] mx-auto px-4 py-8 sm:px-6 lg:px-8">

        {/* Başlık */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-10">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Raporlama Merkezi
            </h1>
            <p className="text-slate-500 mt-2">Kapsamlı iş raporları oluştur, zamanla ve dışa aktar</p>
          </div>
          <button
            onClick={() => navigate('/raporlar/olustur')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:bg-blue-700 active:scale-[0.98] transition-all"
          >
            <Plus className="h-5 w-5" /> Yeni Rapor
          </button>
        </div>

        {/* Hızlı İstatistikler */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-sm font-semibold uppercase">Toplam Şablon</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{sablonlar.length}</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-sm font-semibold uppercase">Son Raporlar</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{loglar.length}</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate('/raporlar/zamanli')}
            className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all text-left group"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-sm font-semibold uppercase">Zamanlı Raporlar</p>
                <p className="text-3xl font-bold text-slate-900 mt-2 group-hover:text-blue-600 transition">
                  Yönet →
                </p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-amber-100 flex items-center justify-center">
                <Clock className="h-6 w-6 text-amber-600" />
              </div>
            </div>
          </button>
        </div>

        {/* Rapor Türü Filtreleri */}
        <div className="mb-8 flex flex-wrap gap-3">
          <button
            onClick={() => setSeciliTur('')}
            className={`px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-sm ${
              !seciliTur
                ? 'bg-blue-600 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
            }`}
          >
            Tüm Raporlar
          </button>
          {['stok', 'siparis', 'finansal', 'performans'].map((tur) => (
            <button
              key={tur}
              onClick={() => setSeciliTur(tur)}
              className={`px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-sm border ${
                seciliTur === tur
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              {tur.charAt(0).toUpperCase() + tur.slice(1)}
            </button>
          ))}
        </div>

        {/* Şablonlar Listesi */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {filtrelenmis.length === 0 ? (
            <div className="lg:col-span-2 bg-white rounded-2xl p-12 text-center border-2 border-dashed border-slate-200">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 font-medium">Rapor şablonu bulunamadı</p>
            </div>
          ) : (
            filtrelenmis.map((sablon) => {
              const Icon = turIkonlari[sablon.tur] || FileText;
              return (
                <div
                  key={sablon.id}
                  className="bg-white rounded-2xl shadow-sm hover:shadow-md border border-slate-200 hover:border-blue-200 transition-all duration-200 overflow-hidden group"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4">
                        <div className={`h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0 ${turRenkleri[sablon.tur]}`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-bold text-slate-900 mb-1">{sablon.ad}</h3>
                          <span className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${turRenkleri[sablon.tur]}`}>
                            {sablon.tur}
                          </span>
                        </div>
                      </div>
                    </div>

                    {sablon.aciklama && (
                      <p className="text-slate-600 text-sm mb-4 line-clamp-2">{sablon.aciklama}</p>
                    )}

                    <div className="flex gap-3 pt-4 border-t border-slate-100">
                      <button
                        onClick={() =>
                          navigate('/raporlar/olustur', {
                            state: { sablon_id: sablon.id },
                          })
                        }
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg font-semibold text-sm transition-colors"
                      >
                        <Eye className="h-4 w-4" /> Oluştur
                      </button>
                      <button
                        onClick={() => navigate('/raporlar/sablonlar')}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg font-semibold text-sm transition-colors"
                      >
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Son Oluşturulan Raporlar */}
        {loglar.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Son Raporlar</h2>
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Şablon</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Durum</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Tarih</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase text-slate-600">Süre</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loglar.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50 transition">
                        <td className="px-6 py-4 font-medium text-slate-900">{log.sablon_id || 'Ad Hoc'}</td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              log.durum === 'Basarili'
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {log.durum}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-600 text-sm">
                          {new Date(log.olusturma_tarihi).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="px-6 py-4 text-slate-600 text-sm">
                          {log.tamamlanma_tarihi
                            ? new Date(
                                new Date(log.tamamlanma_tarihi) -
                                  new Date(log.olusturma_tarihi)
                              ).getSeconds() + 's'
                            : '-'}
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
