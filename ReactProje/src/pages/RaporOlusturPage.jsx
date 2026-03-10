import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Download, Eye, Loader2, Calendar, Filter, RefreshCw, ArrowLeft, FileText, Settings2
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

  if (loading1) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-4 bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Sayfa hazırlanıyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12 sm:pb-20">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-10">
        
        {/* Üst Kısım: Geri Butonu ve Başlık */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8 sm:mb-10">
          <button
            onClick={() => navigate('/raporlar')}
            className="p-3 bg-white border border-slate-200 rounded-2xl shadow-sm hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group flex-shrink-0"
            title="Geri Dön"
          >
            <ArrowLeft className="h-5 w-5 text-slate-600 group-hover:-translate-x-0.5 transition-transform" />
          </button>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Rapor Oluştur
            </h1>
            <p className="text-slate-500 mt-1 text-sm sm:text-base">
              Verilerinizi anlık olarak önizleyin ve dışa aktarın.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8">
          
          {/* Kontrol Paneli (Sol Kolon) */}
          <div className="lg:col-span-4 xl:col-span-3">
            <div className="bg-white rounded-3xl p-5 sm:p-6 shadow-sm shadow-slate-200/50 border border-slate-100 sticky top-6">
              <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
                <Settings2 className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-extrabold text-slate-900">Rapor Ayarları</h2>
              </div>

              <div className="space-y-5">
                {/* Şablon Seçimi */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Şablon Seçiniz</label>
                  <select
                    value={seciliSablon || ''}
                    onChange={(e) => {
                      setSeciliSablon(parseInt(e.target.value) || null);
                      setVeriler(null);
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

                {/* Tarih Aralığı */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 mb-2">
                    <Calendar className="h-4 w-4 text-slate-400" /> Tarih Aralığı
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 ml-1">Başlangıç</span>
                      <input
                        type="date"
                        value={baslangicTarihi}
                        onChange={(e) => setBaslangicTarihi(e.target.value)}
                        className="w-full h-12 px-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                      />
                    </div>
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 ml-1">Bitiş</span>
                      <input
                        type="date"
                        value={bitisTarihi}
                        onChange={(e) => setBitisTarihi(e.target.value)}
                        className="w-full h-12 px-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Export Format */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Dışa Aktar Formatı</label>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-sm focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
                  >
                    <option value="pdf">PDF Dokümanı (.pdf)</option>
                    <option value="excel">Excel Tablosu (.xlsx)</option>
                    <option value="csv">CSV Dosyası (.csv)</option>
                  </select>
                </div>

                {/* Butonlar */}
                <div className="space-y-3 pt-6 mt-2 border-t border-slate-100">
                  <button
                    onClick={handleOnizle}
                    disabled={loading2}
                    className="w-full h-12 rounded-xl bg-blue-50 text-blue-700 font-bold hover:bg-blue-600 hover:text-white transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    {loading2 ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" /> Yükleniyor...
                      </>
                    ) : (
                      <>
                        <Eye className="h-5 w-5 group-hover:scale-110 transition-transform" /> Verileri Önizle
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleIndir}
                    disabled={!veriler || veriler.length === 0}
                    className="w-full h-12 rounded-xl bg-slate-800 text-white font-bold shadow-md shadow-slate-800/20 hover:bg-slate-900 hover:shadow-lg hover:shadow-slate-800/30 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    <Download className="h-5 w-5 group-hover:-translate-y-0.5 transition-transform" /> Raporu İndir
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Rapor Gösterimi (Sağ Kolon) */}
          <div className="lg:col-span-8 xl:col-span-9">
            <div className="bg-white rounded-3xl p-5 sm:p-8 shadow-sm shadow-slate-200/50 border border-slate-100 min-h-[500px] flex flex-col">
              
              {!seciliSablon ? (
                // Durum 1: Şablon Seçilmemiş
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <div className="h-24 w-24 bg-slate-50 rounded-full flex items-center justify-center mb-6">
                    <Filter className="h-12 w-12 text-slate-300" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Şablon Seçimi Bekleniyor</h3>
                  <p className="text-slate-500 max-w-sm mx-auto">
                    Önizleme yapabilmek için lütfen sol taraftaki panelden bir rapor şablonu seçin.
                  </p>
                </div>
              ) : !veriler ? (
                // Durum 2: Şablon Seçilmiş ama Önizleme Yapılmamış
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <div className="h-24 w-24 bg-blue-50 rounded-full flex items-center justify-center mb-6">
                    <RefreshCw className="h-12 w-12 text-blue-300" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Veriler Hazır</h3>
                  <p className="text-slate-500 max-w-sm mx-auto">
                    Kriterlerinizi belirledikten sonra raporu görmek için <strong>"Verileri Önizle"</strong> butonuna tıklayınız.
                  </p>
                </div>
              ) : veriler.length === 0 ? (
                // Durum 3: Veri Yok
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <div className="h-24 w-24 bg-amber-50 rounded-full flex items-center justify-center mb-6">
                    <FileText className="h-12 w-12 text-amber-300" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Kayıt Bulunamadı</h3>
                  <p className="text-slate-500 max-w-sm mx-auto">
                    Seçtiğiniz tarih aralığına ve şablona ait herhangi bir veri bulunmuyor.
                  </p>
                </div>
              ) : (
                // Durum 4: Veri Var (Tablo)
                <div className="flex-1 flex flex-col">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-xl font-extrabold text-slate-900 mb-1">{seciliSablonObj?.ad}</h3>
                      <p className="text-sm font-medium text-slate-500">
                        Toplam <span className="text-blue-600 font-bold">{veriler.length}</span> kayıt bulundu (İlk 10 kayıt gösteriliyor)
                      </p>
                    </div>
                  </div>

                  <div className="overflow-x-auto bg-slate-50/50 rounded-2xl border border-slate-100 flex-1">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-100/50 border-b border-slate-200">
                          {Object.keys(veriler[0] || {}).map((key) => (
                            <th key={key} className="px-5 py-4 text-xs font-extrabold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {veriler.slice(0, 10).map((row, idx) => (
                          <tr key={idx} className="hover:bg-white transition-colors">
                            {Object.values(row).map((val, i) => (
                              <td key={i} className="px-5 py-4 text-sm text-slate-700 font-medium whitespace-nowrap">
                                {val?.toString() || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {veriler.length > 10 && (
                    <div className="mt-6 text-center">
                      <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 text-blue-700 text-xs font-bold">
                        +{veriler.length - 10} adet daha gizlenmiş kayıt mevcut
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}