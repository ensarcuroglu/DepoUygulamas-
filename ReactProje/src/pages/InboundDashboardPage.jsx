import { useState, useEffect, useCallback } from 'react';
import {
  Package, TrendingUp, Clock, AlertTriangle,
  ShieldAlert, FileText, RefreshCw, CheckCircle,
  Loader2, Truck, ChevronRight, PackageX
} from 'lucide-react';
import { getInboundDashboard, getInboundKpi } from '../services/api';
import { useAsync } from '../hooks/useAsync';

const DURUM_RENK = {
  Taslak: 'bg-slate-100 text-slate-700 ring-slate-200/50',
  Onaylandi: 'bg-blue-50 text-blue-700 ring-blue-200/50',
  Kapandi: 'bg-emerald-50 text-emerald-700 ring-emerald-200/50',
};

export default function InboundDashboardPage() {
  const { loading, run } = useAsync(true);
  const [data, setData] = useState(null);
  const [stagingPalet, setStagingPalet] = useState(0);

  const yukle = useCallback(async () => {
    await run(async () => {
      const [dashRes, kpiRes] = await Promise.allSettled([
        getInboundDashboard(),
        getInboundKpi(undefined, undefined, 24),
      ]);

      if (dashRes.status === 'rejected') {
        throw dashRes.reason;
      }
      setData(dashRes.value.data);

      if (kpiRes.status === 'fulfilled') {
        setStagingPalet(kpiRes.value.data?.staging_esik_palet_sayisi ?? 0);
      } else {
        setStagingPalet(0);
      }
    });
  }, [run]);

  useEffect(() => { void yukle(); }, [yukle]);

  if (loading && !data) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-slate-500 space-y-4">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-100 rounded-full blur-xl animate-pulse"></div>
          <Loader2 className="w-10 h-10 animate-spin text-blue-600 relative z-10" />
        </div>
        <p className="text-sm font-medium animate-pulse">Kontrol paneli hazırlanıyor...</p>
      </div>
    );
  }

  if (!data) return null;

  const gorevIlerleme = data.gorev_toplam > 0
    ? Math.round((data.gorev_tamamlanan / data.gorev_toplam) * 100)
    : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8 pb-10">
      
      {/* Üst Bilgi ve Aksiyon Alanı */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Inbound Kontrol Paneli
          </h1>
          <p className="text-sm sm:text-base text-slate-500 mt-1">
            Bugünkü mal kabul ve yerleştirme operasyon özeti
          </p>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="group inline-flex items-center justify-center gap-2 bg-white border border-slate-200 text-slate-700 px-5 py-2.5 rounded-xl text-sm font-semibold shadow-sm hover:shadow hover:bg-slate-50 hover:text-blue-600 active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all duration-200 w-full sm:w-auto"
        >
          <RefreshCw className={`w-4 h-4 transition-transform group-hover:rotate-180 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Yenileniyor...' : 'Verileri Yenile'}
        </button>
      </div>

      {/* Staging Uyarı Bandı */}
      {stagingPalet > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <PackageX className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-amber-900">
              Staging Uyarısı — {stagingPalet} palet 24+ saat bekliyor
            </p>
            <p className="text-xs text-amber-700 mt-0.5">
              Bu paletler için yerleştirme görevi tamamlanmamış. KPI Paneli'nden detay görüntüleyebilirsiniz.
            </p>
          </div>
        </div>
      )}

      {/* Özet Kartları (Grid) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          icon={FileText}
          label="Toplam İrsaliye"
          value={data.irsaliye_toplam}
          detail={`${data.irsaliye_taslak} taslak · ${data.irsaliye_onaylandi} onaylı · ${data.irsaliye_kapandi} kapandı`}
          color="blue"
        />
        <StatCard
          icon={Package}
          label="Yerleştirme"
          value={data.gorev_toplam}
          detail={`${data.gorev_bekleyen} bekleyen · ${data.gorev_devam_eden} devam · ${data.gorev_tamamlanan} bitti`}
          color="amber"
        />
        <StatCard
          icon={Clock}
          label="Ort. Süre"
          value={data.ort_yerlestirme_sure_dk != null ? `${data.ort_yerlestirme_sure_dk} dk` : '—'}
          detail="Bugün tamamlanan görevler"
          color="emerald"
        />
        <StatCard
          icon={AlertTriangle}
          label="İstisna & Override"
          value={`${data.istisna_sayisi} / ${data.override_sayisi}`}
          detail="Fark bildirimi ve kural ihlali"
          color="rose"
        />
      </div>

      {/* Görev İlerleme Çubuğu */}
      {data.gorev_toplam > 0 && (
        <div className="bg-white border border-slate-200/60 rounded-3xl p-5 sm:p-7 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-800 flex items-center gap-2.5">
              <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                <TrendingUp className="w-4 h-4" />
              </div>
              Operasyon İlerlemesi
            </h2>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">{gorevIlerleme}%</span>
              <span className="text-sm font-medium text-slate-500">tamamlandı</span>
            </div>
          </div>
          
          <div className="relative w-full bg-slate-100 rounded-full h-4 overflow-hidden shadow-inner">
            <div
              className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ease-out ${
                gorevIlerleme === 100 
                  ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' 
                  : 'bg-gradient-to-r from-blue-500 to-indigo-500'
              }`}
              style={{ width: `${gorevIlerleme}%` }}
            >
              {/* Parlama efekti */}
              <div className="absolute top-0 right-0 bottom-0 left-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.2)_50%,transparent_75%,transparent_100%)] bg-[length:20px_20px] animate-[shimmer_2s_linear_infinite]" />
            </div>
          </div>
          
          <div className="flex flex-wrap gap-x-6 gap-y-3 mt-5 text-sm font-medium text-slate-600">
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-slate-200 shadow-sm border border-slate-300" />
              {data.gorev_bekleyen} <span className="text-slate-400 font-normal">Bekleyen</span>
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 shadow-sm shadow-blue-200" />
              {data.gorev_devam_eden} <span className="text-slate-400 font-normal">Devam Eden</span>
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-200" />
              {data.gorev_tamamlanan} <span className="text-slate-400 font-normal">Tamamlanan</span>
            </span>
            {data.gorev_iptal > 0 && (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-400 shadow-sm shadow-rose-200" />
                {data.gorev_iptal} <span className="text-slate-400 font-normal">İptal</span>
              </span>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Bugünün İrsaliyeleri Listesi */}
        <div className="xl:col-span-2 bg-white border border-slate-200/60 rounded-3xl overflow-hidden shadow-sm flex flex-col">
          <div className="px-5 sm:px-7 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <h2 className="text-base font-bold text-slate-800 flex items-center gap-2.5">
              <div className="p-1.5 bg-slate-200 text-slate-600 rounded-lg">
                <Truck className="w-4 h-4" />
              </div>
              Bugünkü İrsaliyeler
            </h2>
            <span className="bg-white px-3 py-1 rounded-full text-xs font-bold text-slate-600 border border-slate-200 shadow-sm">
              {data.bugunun_irsaliyeleri.length} Kayıt
            </span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[400px] xl:max-h-[500px]">
            {data.bugunun_irsaliyeleri.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-center h-full">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                  <FileText className="w-8 h-8 text-slate-300" />
                </div>
                <p className="text-slate-500 font-medium">Bugün henüz irsaliye oluşturulmadı.</p>
                <p className="text-sm text-slate-400 mt-1">Yeni bir irsaliye eklendiğinde burada görünecektir.</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {data.bugunun_irsaliyeleri.map((irs) => (
                  <li key={irs.id} className="group px-5 sm:px-7 py-4 flex flex-col sm:flex-row sm:items-center justify-between hover:bg-slate-50/80 transition-colors cursor-default gap-4 sm:gap-0">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-50/50 rounded-2xl flex items-center justify-center shrink-0 border border-blue-100 transition-colors group-hover:bg-blue-100/50">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm sm:text-base font-bold text-slate-800">{irs.irsaliye_no}</p>
                        <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-slate-500 mt-0.5">
                          {irs.tir_plaka && (
                            <span className="flex items-center font-medium bg-slate-100 px-2 py-0.5 rounded text-slate-600">
                              {irs.tir_plaka}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Package className="w-3.5 h-3.5" />
                            {irs.kalem_sayisi} palet
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between sm:justify-end gap-3">
                      <span className={`text-xs font-bold px-3 py-1.5 rounded-full ring-1 ring-inset ${DURUM_RENK[irs.durum] || 'bg-slate-50 text-slate-600 ring-slate-200'}`}>
                        {irs.durum === 'Kapandi' && <CheckCircle className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />}
                        {irs.durum === 'Onaylandi' && <Loader2 className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5 animate-spin" />}
                        {irs.durum}
                      </span>
                      {/* Tıklanabilir hissiyatı vermek için ufak bir ok, tıklandığında detay sayfasına gidilecekse kullanışlı olur */}
                      <ChevronRight className="w-5 h-5 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity hidden sm:block" />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Uyarı ve İstisna Alt Kartları (Sağ Kolon) */}
        <div className="xl:col-span-1 space-y-4 sm:space-y-6">
          {data.istisna_sayisi > 0 ? (
            <div className="bg-amber-50/50 border border-amber-200/60 rounded-3xl p-6 relative overflow-hidden group hover:bg-amber-50 transition-colors">
              <div className="absolute -right-4 -top-4 bg-amber-100 w-24 h-24 rounded-full opacity-50 blur-2xl group-hover:scale-110 transition-transform" />
              <div className="flex flex-col gap-3 relative z-10">
                <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-lg font-extrabold text-amber-900">İstisna Bildirimleri</p>
                  <p className="text-sm font-medium text-amber-700 mt-1 leading-relaxed">
                    Bugün <strong className="text-amber-900 bg-amber-200/50 px-1.5 py-0.5 rounded">{data.istisna_sayisi}</strong> kalemde fark, hasar veya istisna kaydedildi.
                  </p>
                </div>
              </div>
            </div>
          ) : (
             <div className="bg-slate-50 border border-slate-200/60 rounded-3xl p-6 flex flex-col items-center justify-center text-center h-full min-h-[160px]">
                <CheckCircle className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-500">İstisna kaydı bulunmuyor.</p>
             </div>
          )}

          {data.override_sayisi > 0 && (
            <div className="bg-rose-50/50 border border-rose-200/60 rounded-3xl p-6 relative overflow-hidden group hover:bg-rose-50 transition-colors">
              <div className="absolute -right-4 -top-4 bg-rose-100 w-24 h-24 rounded-full opacity-50 blur-2xl group-hover:scale-110 transition-transform" />
              <div className="flex flex-col gap-3 relative z-10">
                <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-lg font-extrabold text-rose-900">Admin Override</p>
                  <p className="text-sm font-medium text-rose-700 mt-1 leading-relaxed">
                    Bugün <strong className="text-rose-900 bg-rose-200/50 px-1.5 py-0.5 rounded">{data.override_sayisi}</strong> görev kural ihlaliyle zorunlu tamamlandı.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// Geliştirilmiş StatCard Component'i
function StatCard({ icon, label, value, detail, color }) {
  const IconComp = icon;
  
  // Modern, yumuşak tonlu renk paleti
  const colors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
  };

  return (
    <div className="group bg-white border border-slate-200/60 rounded-3xl p-5 sm:p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 ${colors[color]}`}>
          <IconComp className="w-6 h-6" strokeWidth={2.5} />
        </div>
      </div>
      
      <div>
        <h3 className="text-sm font-bold text-slate-500 mb-1">{label}</h3>
        <div className="flex items-baseline gap-2">
          <p className="text-3xl sm:text-4xl font-extrabold text-slate-800 tracking-tight">{value}</p>
        </div>
        <p className="text-xs sm:text-sm font-medium text-slate-400 mt-2 line-clamp-2">{detail}</p>
      </div>
    </div>
  );
}
