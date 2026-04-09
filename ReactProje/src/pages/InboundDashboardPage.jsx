import { useState, useEffect, useCallback } from 'react';
import {
  Package, TrendingUp, Clock, AlertTriangle,
  ShieldAlert, FileText, RefreshCw, CheckCircle,
  Loader2, Truck,
} from 'lucide-react';
import { getInboundDashboard } from '../services/api';
import { useAsync } from '../hooks/useAsync';

const DURUM_RENK = {
  Taslak: 'bg-slate-100 text-slate-700',
  Onaylandi: 'bg-blue-50 text-blue-700',
  Kapandi: 'bg-green-50 text-green-700',
};

export default function InboundDashboardPage() {
  const { loading, run } = useAsync(true);
  const [data, setData] = useState(null);

  const yukle = useCallback(async () => {
    await run(async () => {
      const res = await getInboundDashboard();
      setData(res.data);
    });
  }, [run]);

  useEffect(() => { void yukle(); }, [yukle]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Yükleniyor...
      </div>
    );
  }

  if (!data) return null;

  const gorevIlerleme = data.gorev_toplam > 0
    ? Math.round((data.gorev_tamamlanan / data.gorev_toplam) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Başlık */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Inbound Kontrol Paneli</h1>
          <p className="text-sm text-slate-500 mt-0.5">Bugünkü mal kabul ve yerleştirme operasyonu</p>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 px-4 py-2 rounded-xl text-sm font-medium hover:bg-slate-50 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Yenile
        </button>
      </div>

      {/* Özet Kartları */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={FileText}
          label="Toplam İrsaliye"
          value={data.irsaliye_toplam}
          detail={`${data.irsaliye_taslak} taslak · ${data.irsaliye_onaylandi} onaylı · ${data.irsaliye_kapandi} kapandı`}
          color="blue"
        />
        <StatCard
          icon={Package}
          label="Yerleştirme Görevleri"
          value={data.gorev_toplam}
          detail={`${data.gorev_bekleyen} bekleyen · ${data.gorev_devam_eden} devam · ${data.gorev_tamamlanan} tamamlandı`}
          color="amber"
        />
        <StatCard
          icon={Clock}
          label="Ort. Yerleştirme Süresi"
          value={data.ort_yerlestirme_sure_dk != null ? `${data.ort_yerlestirme_sure_dk} dk` : '—'}
          detail="Bugün tamamlanan görevler"
          color="green"
        />
        <StatCard
          icon={AlertTriangle}
          label="İstisna / Override"
          value={`${data.istisna_sayisi} / ${data.override_sayisi}`}
          detail="Fark bildirimi ve kural ihlali"
          color="red"
        />
      </div>

      {/* Görev İlerleme Çubuğu */}
      {data.gorev_toplam > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              Günlük İlerleme
            </h2>
            <span className="text-lg font-bold text-slate-800">{gorevIlerleme}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                gorevIlerleme === 100 ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${gorevIlerleme}%` }}
            />
          </div>
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
              {data.gorev_bekleyen} bekleyen
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              {data.gorev_devam_eden} devam ediyor
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
              {data.gorev_tamamlanan} tamamlandı
            </span>
            {data.gorev_iptal > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                {data.gorev_iptal} iptal
              </span>
            )}
          </div>
        </div>
      )}

      {/* Bugünün İrsaliyeleri */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-700 flex items-center gap-2">
            <Truck className="w-4 h-4 text-slate-400" />
            Bugünkü İrsaliyeler
          </h2>
          <span className="text-xs text-slate-500">{data.bugunun_irsaliyeleri.length} kayıt</span>
        </div>

        {data.bugunun_irsaliyeleri.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            Bugün henüz irsaliye oluşturulmadı.
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {data.bugunun_irsaliyeleri.map((irs) => (
              <div key={irs.id} className="px-5 py-3.5 flex items-center justify-between hover:bg-slate-50/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-700">{irs.irsaliye_no}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      {irs.tir_plaka && <span>{irs.tir_plaka}</span>}
                      <span>{irs.kalem_sayisi} palet</span>
                    </div>
                  </div>
                </div>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${DURUM_RENK[irs.durum] || 'bg-slate-100 text-slate-600'}`}>
                  {irs.durum === 'Kapandi' && <CheckCircle className="w-3 h-3 inline mr-1" />}
                  {irs.durum === 'Onaylandi' && <Loader2 className="w-3 h-3 inline mr-1" />}
                  {irs.durum}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* İstatistik Alt Kartları */}
      {(data.istisna_sayisi > 0 || data.override_sayisi > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {data.istisna_sayisi > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-amber-800">İstisna Bildirimleri</p>
                <p className="text-xs text-amber-600 mt-0.5">
                  Bugün <strong>{data.istisna_sayisi}</strong> kalemde fark/hasar/istisna kaydedildi.
                </p>
              </div>
            </div>
          )}
          {data.override_sayisi > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-2xl p-5 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-orange-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-orange-800">Admin Override</p>
                <p className="text-xs text-orange-600 mt-0.5">
                  Bugün <strong>{data.override_sayisi}</strong> görev kural ihlaliyle tamamlandı.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, detail, color }) {
  const IconComp = icon;
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors[color]}`}>
          <IconComp className="w-5 h-5" />
        </div>
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-slate-800">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{detail}</p>
    </div>
  );
}
