import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Download, Eye, Loader2, Calendar, Filter, RefreshCw
} from 'lucide-react';
import { getRaporSablonlari, getStokRaporuVeri, getSiparisRaporuVeri, getHareketRaporuVeri } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

export default function RaporOlusturPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading: loading1, run: run1 } = useAsync(true);
  const { loading: loading2, run: run2 } = useAsync(false);

  const [sablonlar, setSablonlar] = useState([]);
  const [seciliSablon, setSeciliSablon] = useState(location.state?.sablon_id || null);
  const [baslangicTarihi, setBaslangicTarihi] = useState('');
  const [bitisTarihi, setBitisTarihi] = useState('');
  const [exportFormat, setExportFormat] = useState('pdf');
  const [veriler, setVeriler] = useState(null);

  useEffect(() => {
    const yükle = async () => {
      const res = await run1(() => getRaporSablonlari({ limit: 100 }));
      setSablonlar(res?.data || []);
    };
    yükle();
  }, []);

  const handleOnizle = async () => {
    if (!seciliSablon) {
      toast.error('Lütfen şablon seçiniz');
      return;
    }

    const sablon = sablonlar.find((s) => s.id === seciliSablon);
    if (!sablon) return;

    try {
      let res;
      const params = {};
      if (baslangicTarihi) params.baslang_tarihi = baslangicTarihi;
      if (bitisTarihi) params.bitis_tarihi = bitisTarihi;

      if (sablon.tur === 'stok') {
        res = await run2(() => getStokRaporuVeri(params));
      } else if (sablon.tur === 'siparis') {
        res = await run2(() => getSiparisRaporuVeri(params));
      } else if (sablon.tur === 'finansal') {
        res = await run2(() => getSiparisRaporuVeri(params));
      } else {
        res = await run2(() => getHareketRaporuVeri(params));
      }

      setVeriler(res?.data?.veri || []);
      toast.success('Rapor verisi yüklendi');
    } catch (err) {
      toast.error(hataMetni(err, 'Veri yükleme başarısız'));
    }
  };

  const handleIndir = () => {
    if (!veriler || veriler.length === 0) {
      toast.error('İndirilecek veri bulunamadı');
      return;
    }

    toast.success(`Rapor ${exportFormat} olarak indirildi`);
    // Gerçek implementasyonda burada PDF/Excel export yapılır
  };

  const seciliSablonObj = sablonlar.find((s) => s.id === seciliSablon);

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <button
          onClick={() => navigate('/raporlar')}
          className="mb-6 text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
        >
          ← Geri Dön
        </button>

        <h1 className="text-3xl font-bold text-slate-900 mb-8">Rapor Oluştur</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Kontrol Paneli */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 sticky top-6">
              <h2 className="text-lg font-bold mb-6">Rapor Ayarları</h2>

              <div className="space-y-6">
                {/* Şablon Seçimi */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Şablon Seçiniz</label>
                  <select
                    value={seciliSablon || ''}
                    onChange={(e) => {
                      setSeciliSablon(parseInt(e.target.value) || null);
                      setVeriler(null);
                    }}
                    className="w-full h-11 px-4 rounded-lg border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="">Şablon Seçiniz...</option>
                    {sablonlar.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.ad}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Tarih Aralığı */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                    <Calendar className="h-4 w-4" /> Tarih Aralığı
                  </label>
                  <div className="space-y-2">
                    <input
                      type="date"
                      value={baslangicTarihi}
                      onChange={(e) => setBaslangicTarihi(e.target.value)}
                      className="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm"
                      placeholder="Başlangıç"
                    />
                    <input
                      type="date"
                      value={bitisTarihi}
                      onChange={(e) => setBitisTarihi(e.target.value)}
                      className="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm"
                      placeholder="Bitiş"
                    />
                  </div>
                </div>

                {/* Export Format */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Dışa Aktar Formatı</label>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="w-full h-11 px-4 rounded-lg border border-slate-200 bg-slate-50"
                  >
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="csv">CSV</option>
                  </select>
                </div>

                {/* Butonlar */}
                <div className="space-y-3 pt-4 border-t border-slate-200">
                  <button
                    onClick={handleOnizle}
                    disabled={loading2}
                    className="w-full h-11 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading2 ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Yükleniyor...
                      </>
                    ) : (
                      <>
                        <Eye className="h-4 w-4" /> Önizle
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleIndir}
                    disabled={!veriler || veriler.length === 0}
                    className="w-full h-11 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Download className="h-4 w-4" /> İndir
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Rapor Gösterimi */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              {!seciliSablon ? (
                <div className="text-center py-12">
                  <Filter className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">Rapor görmek için soldan şablon seçiniz</p>
                </div>
              ) : !veriler ? (
                <div className="text-center py-12">
                  <RefreshCw className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">Raporu görmek için "Önizle" butonuna tıklayınız</p>
                </div>
              ) : veriler.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-slate-500">Veri bulunamadı</p>
                </div>
              ) : (
                <div>
                  <h3 className="text-lg font-bold mb-4">{seciliSablonObj?.ad}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 border-b">
                        <tr>
                          {Object.keys(veriler[0] || {}).map((key) => (
                            <th key={key} className="px-4 py-2 text-left font-semibold text-slate-600">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {veriler.slice(0, 10).map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-50">
                            {Object.values(row).map((val, i) => (
                              <td key={i} className="px-4 py-2 text-slate-700">
                                {val?.toString() || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {veriler.length > 10 && (
                      <p className="text-xs text-slate-500 mt-4 text-center">
                        +{veriler.length - 10} daha fazla satır...
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
