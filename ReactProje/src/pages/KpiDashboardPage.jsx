import { useState, useEffect, useCallback } from 'react';
import {
  BarChart3, Clock, TrendingUp, AlertTriangle,
  ShieldAlert, RefreshCw, Loader2, Download,
  Users, PackageX, Timer, Activity,
} from 'lucide-react';
import { getInboundKpi } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { exportToExcel, exportToPDF } from '../utils/exportUtils';

const bugunIso = () => new Date().toISOString().split('T')[0];

export default function KpiDashboardPage() {
  const { loading, run } = useAsync(true);
  const [data, setData] = useState(null);
  const [tarihBas, setTarihBas] = useState(bugunIso());
  const [tarihBitis, setTarihBitis] = useState(bugunIso());
  const [esikSaat, setEsikSaat] = useState(24);

  const yukle = useCallback(async () => {
    await run(async () => {
      const res = await getInboundKpi(tarihBas, tarihBitis, esikSaat);
      setData(res.data);
    });
  }, [run, tarihBas, tarihBitis, esikSaat]);

  useEffect(() => { void yukle(); }, [yukle]);

  const handleExportExcel = () => {
    if (!data) return;
    const satirlar = [
      { Metrik: 'Araç Kabul → İlk Palet (dk)', Değer: data.arac_kabul_ilk_palet_sure_dk ?? '—' },
      { Metrik: 'İlk Palet → Son Yerleştirme (dk)', Değer: data.ilk_palet_son_yerlestirme_sure_dk ?? '—' },
      { Metrik: 'Yanlış Palet Okutma Sayısı', Değer: data.yanlis_palet_okutma_sayisi },
      { Metrik: 'Override Sayısı', Değer: data.override_sayisi },
      { Metrik: `Override Oranı (%)`, Değer: data.override_orani ?? '—' },
      { Metrik: 'Karantina Sayısı', Değer: data.karantina_sayisi },
      { Metrik: 'Karantina Oranı (%)', Değer: data.karantina_orani ?? '—' },
      { Metrik: `Staging ${esikSaat}h+ Palet Sayısı`, Değer: data.staging_esik_palet_sayisi },
      ...data.operator_verimliligi.map(op => ({
        Metrik: `Operatör: ${op.kullanici_adi || op.kullanici_id}`,
        Değer: `${op.toplam_yerlestirme} adet / ${op.saatlik_yerlestirme} adet/saat`,
      })),
    ];
    exportToExcel(satirlar, `KPI_${tarihBas}_${tarihBitis}`);
  };

  const handleExportPDF = () => {
    if (!data) return;
    const satirlar = [
      { metrik: 'Araç Kabul → İlk Palet', deger: data.arac_kabul_ilk_palet_sure_dk != null ? `${data.arac_kabul_ilk_palet_sure_dk} dk` : '—' },
      { metrik: 'İlk Palet → Son Yerleştirme', deger: data.ilk_palet_son_yerlestirme_sure_dk != null ? `${data.ilk_palet_son_yerlestirme_sure_dk} dk` : '—' },
      { metrik: 'Yanlış Palet Okutma', deger: String(data.yanlis_palet_okutma_sayisi) },
      { metrik: 'Override', deger: `${data.override_sayisi} (${data.override_orani ?? '—'}%)` },
      { metrik: 'Karantina', deger: `${data.karantina_sayisi} (${data.karantina_orani ?? '—'}%)` },
      { metrik: `Staging ${esikSaat}h+`, deger: String(data.staging_esik_palet_sayisi) },
    ];
    exportToPDF(
      satirlar,
      ['metrik', 'deger'],
      `KPI_${tarihBas}_${tarihBitis}`,
      `Inbound KPI — ${tarihBas} / ${tarihBitis}`,
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-10">

      {/* Başlık + Filtreler */}
      <div className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            KPI Paneli
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Inbound operasyon performans göstergeleri
          </p>
        </div>

        {/* Filtre Satırı */}
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Başlangıç</label>
            <input
              type="date"
              value={tarihBas}
              max={tarihBitis}
              onChange={e => setTarihBas(e.target.value)}
              className="border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Bitiş</label>
            <input
              type="date"
              value={tarihBitis}
              min={tarihBas}
              max={bugunIso()}
              onChange={e => setTarihBitis(e.target.value)}
              className="border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Staging Eşiği (saat)</label>
            <input
              type="number"
              value={esikSaat}
              min={1}
              max={720}
              onChange={e => setEsikSaat(Number(e.target.value))}
              className="border border-slate-200 rounded-xl px-3 py-2 w-28 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <button
            onClick={yukle}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow hover:bg-blue-700 active:scale-95 disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Hesapla
          </button>
          {data && (
            <>
              <button
                onClick={handleExportExcel}
                className="inline-flex items-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow hover:bg-emerald-700 active:scale-95 transition-all"
              >
                <Download className="w-4 h-4" />
                Excel
              </button>
              <button
                onClick={handleExportPDF}
                className="inline-flex items-center gap-2 bg-rose-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow hover:bg-rose-700 active:scale-95 transition-all"
              >
                <Download className="w-4 h-4" />
                PDF
              </button>
            </>
          )}
        </div>
      </div>

      {/* Loading */}
      {loading && !data && (
        <div className="min-h-[40vh] flex flex-col items-center justify-center text-slate-400 space-y-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-sm font-medium animate-pulse">KPI hesaplanıyor...</p>
        </div>
      )}

      {data && (
        <>
          {/* Staging Uyarı Bandı */}
          {data.staging_esik_palet_sayisi > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 flex items-center gap-4">
              <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-amber-900">
                  Staging Uyarısı — {data.staging_esik_palet_sayisi} palet {esikSaat}+ saat bekliyor
                </p>
                <p className="text-xs text-amber-700 mt-0.5">
                  Bu paletler için yerleştirme görevi oluşturulup tamamlanması gerekiyor.
                </p>
              </div>
            </div>
          )}

          {/* KPI Kartları */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              icon={Timer}
              label="Araç → İlk Palet"
              value={data.arac_kabul_ilk_palet_sure_dk != null ? `${data.arac_kabul_ilk_palet_sure_dk} dk` : '—'}
              detail="Ortalama ilk palet giriş süresi"
              color="blue"
            />
            <KpiCard
              icon={Clock}
              label="İlk Palet → Son Yerleştirme"
              value={data.ilk_palet_son_yerlestirme_sure_dk != null ? `${data.ilk_palet_son_yerlestirme_sure_dk} dk` : '—'}
              detail="Ortalama toplam süre"
              color="indigo"
            />
            <KpiCard
              icon={PackageX}
              label="Yanlış Palet Okutma"
              value={data.yanlis_palet_okutma_sayisi}
              detail="Terminal barkod eşleşme hatası"
              color={data.yanlis_palet_okutma_sayisi > 0 ? 'rose' : 'emerald'}
            />
            <KpiCard
              icon={ShieldAlert}
              label="Override"
              value={`${data.override_sayisi} kez`}
              detail={data.override_orani != null ? `%${data.override_orani} oran` : 'Veri yok'}
              color={data.override_sayisi > 0 ? 'amber' : 'emerald'}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <KpiCard
              icon={Activity}
              label="Karantina"
              value={`${data.karantina_sayisi} adet`}
              detail={data.karantina_orani != null ? `%${data.karantina_orani} oran` : 'Veri yok'}
              color={data.karantina_sayisi > 0 ? 'rose' : 'emerald'}
            />
            <KpiCard
              icon={AlertTriangle}
              label={`Staging ${esikSaat}h+ Bekleyen`}
              value={data.staging_esik_palet_sayisi}
              detail="Yerleştirilmemiş palet"
              color={data.staging_esik_palet_sayisi > 0 ? 'amber' : 'emerald'}
            />
          </div>

          {/* Operatör Verimliliği Tablosu */}
          <div className="bg-white border border-slate-200/60 rounded-3xl overflow-hidden shadow-sm">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center gap-3">
              <div className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                <Users className="w-4 h-4" />
              </div>
              <h2 className="text-base font-bold text-slate-800">Operatör Verimliliği</h2>
              <span className="ml-auto bg-slate-100 px-3 py-1 rounded-full text-xs font-bold text-slate-600">
                {data.operator_verimliligi.length} Operatör
              </span>
            </div>

            {data.operator_verimliligi.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm font-medium">Bu dönemde tamamlanan görev bulunamadı.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/60">
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Operatör</th>
                      <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Toplam</th>
                      <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Saatlik Ort.</th>
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Performans</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {[...data.operator_verimliligi]
                      .sort((a, b) => b.toplam_yerlestirme - a.toplam_yerlestirme)
                      .map((op, idx) => {
                        const maxSaat = Math.max(...data.operator_verimliligi.map(o => o.saatlik_yerlestirme), 1);
                        const yuzde = Math.round((op.saatlik_yerlestirme / maxSaat) * 100);
                        return (
                          <tr key={op.kullanici_id} className="hover:bg-slate-50/60 transition-colors">
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                  {idx + 1}
                                </div>
                                <span className="font-semibold text-slate-800">
                                  {op.kullanici_adi || `Kullanıcı #${op.kullanici_id}`}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right font-bold text-slate-800">
                              {op.toplam_yerlestirme}
                            </td>
                            <td className="px-6 py-4 text-right font-semibold text-blue-700">
                              {op.saatlik_yerlestirme} <span className="text-slate-400 font-normal text-xs">adet/saat</span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
                                  <div
                                    className="h-full bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full transition-all duration-700"
                                    style={{ width: `${yuzde}%` }}
                                  />
                                </div>
                                <span className="text-xs font-bold text-slate-500 w-8 text-right">%{yuzde}</span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function KpiCard({ icon, label, value, detail, color }) {
  const IconComp = icon;
  const colors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
  };
  return (
    <div className="bg-white border border-slate-200/60 rounded-3xl p-5 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center border ${colors[color]}`}>
          <IconComp className="w-5 h-5" strokeWidth={2.5} />
        </div>
      </div>
      <div>
        <h3 className="text-xs font-bold text-slate-500 mb-1">{label}</h3>
        <p className="text-2xl font-extrabold text-slate-800 tracking-tight">{value}</p>
        <p className="text-xs font-medium text-slate-400 mt-1.5">{detail}</p>
      </div>
    </div>
  );
}
