import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  Loader2,
  Package,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { useRiskliUrunlerQuery } from '../queries/talepTahminiQueries';

const HORIZONS = [7, 14, 30, 90];

const numberFormatter = new Intl.NumberFormat('tr-TR', {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat('tr-TR', {
  maximumFractionDigits: 2,
});

const riskBadge = {
  kritik: 'bg-rose-100 text-rose-700 border-rose-200',
  dikkat: 'bg-amber-100 text-amber-700 border-amber-200',
  yok: 'bg-emerald-100 text-emerald-700 border-emerald-200',
};

function formatNumber(value) {
  return numberFormatter.format(Math.round(Number(value || 0)));
}

function formatDecimal(value) {
  return decimalFormatter.format(Number(value || 0));
}

export default function RiskliUrunlerPage() {
  const [horizon, setHorizon] = useState(7);
  const [siniflandirma, setSiniflandirma] = useState('kritik,dikkat');

  const params = useMemo(
    () => ({ tahmin_gun: horizon, siniflandirma, limit: 100 }),
    [horizon, siniflandirma],
  );
  const { data, isLoading, isFetching, error, refetch } =
    useRiskliUrunlerQuery(params);
  const items = data ?? [];

  return (
    <div className="max-w-7xl mx-auto space-y-5 pb-10">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Riskli Urunler
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Gece hesaplanan tahminlere gore stok riski olan urunler
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-bold text-slate-600 shadow-sm transition hover:border-blue-200 hover:text-blue-700 disabled:opacity-60"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Yenile
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          {HORIZONS.map((value) => (
            <button
              key={value}
              onClick={() => setHorizon(value)}
              className={`h-9 min-w-16 rounded-md px-3 text-sm font-bold transition ${
                horizon === value
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
              }`}
            >
              {value} gun
            </button>
          ))}
        </div>

        <select
          value={siniflandirma}
          onChange={(event) => setSiniflandirma(event.target.value)}
          className="h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
        >
          <option value="kritik,dikkat">Kritik + Dikkat</option>
          <option value="kritik">Sadece Kritik</option>
          <option value="dikkat">Sadece Dikkat</option>
        </select>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error.message}
        </div>
      )}

      {isLoading && (
        <div className="min-h-[44vh] flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-sm font-semibold">Riskli urunler yukleniyor...</p>
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white py-14 text-center shadow-sm">
          <ShieldAlert className="w-10 h-10 mx-auto text-emerald-500" />
          <p className="mt-3 text-sm font-semibold text-slate-700">
            Bu ufukta riskli urun bulunamadi.
          </p>
          <p className="mt-1 text-xs font-semibold text-slate-400">
            Cache henuz dolu degilse gece 02:00 sonrasi tekrar deneyin.
          </p>
        </div>
      )}

      {!isLoading && items.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs font-extrabold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 text-left">Urun</th>
                  <th className="px-4 py-3 text-right">Stok</th>
                  <th className="px-4 py-3 text-right">Tahmini Talep</th>
                  <th className="px-4 py-3 text-right">Onerilen Ikmal</th>
                  <th className="px-4 py-3 text-center">Risk</th>
                  <th className="px-4 py-3 text-center">Guven</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={`${item.urun.id}-${item.tahmin_gun}`} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-slate-400" />
                        <div>
                          <p className="font-bold text-slate-800">
                            {item.urun.isim}
                          </p>
                          <p className="text-xs font-semibold text-slate-400">
                            {item.urun.barkod || '—'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-700">
                      {formatNumber(item.urun.stok_miktari)}
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-slate-900">
                      {formatNumber(item.tahmini_talep)}
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-amber-700">
                      {formatNumber(item.onerilen_ikmal_miktari)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-extrabold uppercase ${
                          riskBadge[item.stok_riski] ?? riskBadge.yok
                        }`}
                      >
                        {item.stok_riski === 'kritik' && (
                          <AlertTriangle className="h-3 w-3" />
                        )}
                        {item.stok_riski}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-xs font-bold text-slate-600">
                      %{formatDecimal(item.veri_guven_skoru * 100)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={`/talep-tahmini?urun=${item.urun.id}&ufuk=${item.tahmin_gun}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800"
                      >
                        Detay
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
