import { useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  Download,
  FlaskConical,
  LineChart,
  Loader2,
  Package,
  PlayCircle,
  RefreshCw,
  Search,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  useBacktestOzetQuery,
  useParquetBacktestMutation,
  useParquetVeriSetleriQuery,
  useTalepTahminUrunleriQuery,
  useTalepTahminiQuery,
} from '../queries/talepTahminiQueries';

const HORIZONS = [7, 14, 30, 90];

const numberFormatter = new Intl.NumberFormat('tr-TR', {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat('tr-TR', {
  maximumFractionDigits: 2,
});

const shortDateFormatter = new Intl.DateTimeFormat('tr-TR', {
  day: '2-digit',
  month: 'short',
});

const riskStyles = {
  kritik: 'bg-rose-50 text-rose-700 border-rose-200',
  dikkat: 'bg-amber-50 text-amber-700 border-amber-200',
  yok: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

const trendStyles = {
  pozitif: 'text-emerald-700 bg-emerald-50 border-emerald-200',
  negatif: 'text-rose-700 bg-rose-50 border-rose-200',
  stabil: 'text-slate-700 bg-slate-50 border-slate-200',
};

function formatNumber(value) {
  return numberFormatter.format(Math.round(Number(value || 0)));
}

function formatDecimal(value) {
  return decimalFormatter.format(Number(value || 0));
}

function formatDate(value) {
  return shortDateFormatter.format(new Date(value));
}

function buildChartData(data) {
  if (!data) return [];

  const history = data.gecmis_gunluk_seri.map((item) => ({
    tarih: item.tarih,
    label: formatDate(item.tarih),
    gecmis: item.miktar,
    tahmin: null,
    band: null,
  }));

  if (history.length > 0) {
    const lastHist = history[history.length - 1];
    history[history.length - 1] = {
      ...lastHist,
      tahmin: lastHist.gecmis,
      band: [lastHist.gecmis, lastHist.gecmis],
    };
  }

  const forecast = data.gelecek_gunluk_tahmin.map((item) => {
    const alt = Number(item.alt_sinir ?? item.tahmin ?? 0);
    const ust = Number(item.ust_sinir ?? item.tahmin ?? 0);
    return {
      tarih: item.tarih,
      label: formatDate(item.tarih),
      gecmis: null,
      tahmin: item.tahmin,
      band: [alt, ust],
    };
  });

  return [...history, ...forecast];
}

function downloadForecastCsv(data) {
  if (!data) return;

  const rows = [
    ['Tarih', 'Model Tahmini'],
    ...data.gelecek_gunluk_tahmin.map((item) => [item.tarih, item.tahmin]),
  ];
  const csv = rows.map((row) => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `talep-tahmini-${data.urun.id}-${data.tahmin_gun}-gun.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

const TABS = [
  { id: 'tahmin', label: 'Tahmin Al', icon: LineChart },
  { id: 'backtest', label: 'Model Testi / Backtest', icon: FlaskConical },
];

export default function TalepTahminiPage() {
  const [activeTab, setActiveTab] = useState('tahmin');

  return (
    <div className="max-w-7xl mx-auto space-y-5 pb-10">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Talep Tahmini
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Urun bazli stok riski, ikmal projeksiyonu ve model dogrulama
        </p>
      </div>

      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex h-10 items-center gap-2 rounded-md px-4 text-sm font-bold transition ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'tahmin' && <TahminAlPanel />}
      {activeTab === 'backtest' && <BacktestPanel />}
    </div>
  );
}

function TahminAlPanel() {
  const [search, setSearch] = useState('');
  const [manualProductId, setManualProductId] = useState('');
  const [horizon, setHorizon] = useState(7);

  const productParams = useMemo(() => ({
    limit: 100,
    ...(search.trim() ? { search: search.trim() } : {}),
  }), [search]);

  const productsQuery = useTalepTahminUrunleriQuery(productParams);
  const backtestQuery = useBacktestOzetQuery(horizon);
  const products = useMemo(() => productsQuery.data ?? [], [productsQuery.data]);
  const selectedProductId = useMemo(() => {
    if (products.length === 0) return '';
    const manualSelectionExists = products.some((product) => String(product.id) === manualProductId);
    return manualSelectionExists ? manualProductId : String(products[0].id);
  }, [manualProductId, products]);

  const selectedId = selectedProductId ? Number(selectedProductId) : null;
  const forecastQuery = useTalepTahminiQuery(selectedId, horizon);
  const forecast = forecastQuery.data;
  const chartData = useMemo(() => buildChartData(forecast), [forecast]);
  const selectedProduct = forecast?.urun ?? products.find((product) => String(product.id) === selectedProductId);
  const riskClass = riskStyles[forecast?.stok_riski] ?? riskStyles.yok;
  const trendClass = trendStyles[forecast?.trend?.yon] ?? trendStyles.stabil;

  const isInitialLoading = productsQuery.isLoading || (selectedId && forecastQuery.isLoading && !forecast);
  const hasNoProducts = !productsQuery.isLoading && products.length === 0;
  const errorMessage = productsQuery.error?.message || forecastQuery.error?.message;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col sm:flex-row gap-3 lg:ml-auto">
          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Urun ara"
              className="w-full h-11 rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm font-medium text-slate-700 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <select
            value={selectedProductId}
            onChange={(event) => setManualProductId(event.target.value)}
            disabled={products.length === 0}
            className="h-11 min-w-[260px] rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100 disabled:opacity-60"
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.isim}{product.barkod ? ` - ${product.barkod}` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>
      {/* TahminAlPanel body */}

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

        <button
          onClick={() => forecastQuery.refetch()}
          disabled={!selectedId || forecastQuery.isFetching}
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-bold text-slate-600 shadow-sm transition hover:border-blue-200 hover:text-blue-700 disabled:opacity-60"
        >
          <RefreshCw className={`w-4 h-4 ${forecastQuery.isFetching ? 'animate-spin' : ''}`} />
          Yenile
        </button>

        {selectedProduct && (
          <div className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 text-sm font-semibold text-slate-600">
            <Package className="w-4 h-4 text-slate-500" />
            Stok: {formatNumber(selectedProduct.stok_miktari)}
          </div>
        )}

        {backtestQuery.data && backtestQuery.data.urun_sayisi > 0 && (
          <div className="inline-flex h-11 items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 text-sm font-semibold text-emerald-700">
            <Activity className="w-4 h-4" />
            MAPE: %{formatDecimal(backtestQuery.data.mape)} ({backtestQuery.data.urun_sayisi} urun)
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {errorMessage}
        </div>
      )}

      {isInitialLoading && (
        <div className="min-h-[44vh] flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-sm font-semibold">Talep verisi yukleniyor...</p>
        </div>
      )}

      {hasNoProducts && (
        <div className="rounded-lg border border-slate-200 bg-white py-14 text-center shadow-sm">
          <Package className="w-10 h-10 mx-auto text-slate-300" />
          <p className="mt-3 text-sm font-semibold text-slate-500">Urun bulunamadi.</p>
        </div>
      )}

      {forecast && !isInitialLoading && (
        <>
          {forecast.uyarilar.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" />
                <div className="space-y-1">
                  {forecast.uyarilar.map((uyari) => (
                    <p key={uyari} className="text-sm font-semibold text-amber-800">
                      {uyari}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              icon={TrendingUp}
              label={`${forecast.tahmin_gun} Gunluk Tahmin`}
              value={`${formatNumber(forecast.tahmini_talep)} Adet`}
              detail={`Gunluk ort. ${formatDecimal(forecast.gunluk_ortalama_talep)}`}
              tone="blue"
            />
            <MetricCard
              icon={ShieldAlert}
              label="Guvenli Stok"
              value={`${formatNumber(forecast.guvenli_stok)} Adet`}
              detail={`Risk: ${forecast.stok_riski}`}
              tone={forecast.stok_riski === 'kritik' ? 'rose' : forecast.stok_riski === 'dikkat' ? 'amber' : 'emerald'}
            />
            <MetricCard
              icon={Activity}
              label="Ikmal Onerisi"
              value={`${formatNumber(forecast.onerilen_ikmal_miktari)} Adet`}
              detail={`Guven skoru %${formatNumber(forecast.veri_guven_skoru * 100)}`}
              tone="indigo"
            />
            <MetricCard
              icon={BarChart3}
              label="Trend"
              value={forecast.trend.etiket}
              detail={`Degisim %${formatDecimal(forecast.trend.degisim_orani * 100)}`}
              tone={forecast.trend.yon === 'pozitif' ? 'emerald' : forecast.trend.yon === 'negatif' ? 'rose' : 'slate'}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-base font-extrabold text-slate-800">{forecast.urun.isim}</h2>
                  <p className="text-xs font-semibold text-slate-400">
                    {forecast.urun.barkod || 'Barkod yok'}
                    {forecast.model_versiyonu && (
                      <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 font-bold text-slate-500">
                        {forecast.model_versiyonu}
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className={`rounded-full border px-3 py-1 text-xs font-extrabold uppercase ${riskClass}`}>
                    {forecast.stok_riski}
                  </span>
                  <span className={`rounded-full border px-3 py-1 text-xs font-extrabold uppercase ${trendClass}`}>
                    {forecast.talep_sinyali}
                  </span>
                </div>
              </div>

              <div className="h-[360px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="label"
                      minTickGap={28}
                      tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }}
                      tickLine={false}
                      axisLine={{ stroke: '#cbd5e1' }}
                    />
                    <YAxis
                      tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }}
                      tickLine={false}
                      axisLine={{ stroke: '#cbd5e1' }}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <Legend verticalAlign="top" height={32} iconType="circle" />
                    <Area
                      type="monotone"
                      dataKey="band"
                      name="Guven Araligi"
                      stroke="none"
                      fill="#fbbf24"
                      fillOpacity={0.18}
                      isAnimationActive={false}
                      connectNulls={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="gecmis"
                      name="Gecmis Cikis"
                      stroke="#2563eb"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                      connectNulls={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="tahmin"
                      name="Tahmin"
                      stroke="#f59e0b"
                      strokeWidth={3}
                      strokeDasharray="8 6"
                      dot={false}
                      activeDot={{ r: 5 }}
                      connectNulls={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                <h2 className="text-sm font-extrabold text-slate-800">Tahmin Tablosu</h2>
                <button
                  onClick={() => downloadForecastCsv(forecast)}
                  className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-xs font-bold text-white transition hover:bg-slate-700"
                >
                  <Download className="h-4 w-4" />
                  CSV
                </button>
              </div>
              <div className="max-h-[390px] overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-50 text-xs font-extrabold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3 text-left">Tarih</th>
                      <th className="px-4 py-3 text-right">Tahmin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {forecast.gelecek_gunluk_tahmin.map((item) => (
                      <tr key={item.tarih} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-semibold text-slate-700">
                          {new Date(item.tarih).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="px-4 py-3 text-right font-extrabold text-slate-900">
                          {formatDecimal(item.tahmin)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

const HORIZON_OPTIONS = HORIZONS;

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function BacktestPanel() {
  const [selectedDataset, setSelectedDataset] = useState('');
  const [horizon, setHorizon] = useState(7);
  const [scope, setScope] = useState('all'); // 'all' | 'single'
  const [singleUrunId, setSingleUrunId] = useState('');
  const [lastRunParams, setLastRunParams] = useState(null);

  const datasetsQuery = useParquetVeriSetleriQuery();
  const datasets = useMemo(() => datasetsQuery.data ?? [], [datasetsQuery.data]);
  const mutation = useParquetBacktestMutation();

  // Auto-select first dataset when list loads
  const effectiveDataset = useMemo(() => {
    if (datasets.length === 0) return '';
    return datasets.some((d) => d.dosya === selectedDataset)
      ? selectedDataset
      : datasets[0].dosya;
  }, [datasets, selectedDataset]);

  const result = mutation.data;
  const errorMessage = datasetsQuery.error?.message || mutation.error?.message;
  const canRun =
    Boolean(effectiveDataset) &&
    !mutation.isPending &&
    (scope === 'all' || (singleUrunId.trim() && /^\d+$/.test(singleUrunId.trim())));

  const handleRun = () => {
    if (!effectiveDataset) return;
    const params = {
      dosya: effectiveDataset,
      tahmin_gun: horizon,
      ...(scope === 'single' ? { urun_id: Number(singleUrunId) } : {}),
    };
    setLastRunParams(params);
    mutation.mutate(params);
  };

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <FlaskConical className="w-5 h-5 text-blue-600" />
          <h2 className="text-base font-extrabold text-slate-800">Backtest Konfigurasyonu</h2>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_auto_auto_auto]">
          <div>
            <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-500 mb-1">
              Parquet Veri Seti
            </label>
            <select
              value={effectiveDataset}
              onChange={(event) => setSelectedDataset(event.target.value)}
              disabled={datasetsQuery.isLoading || datasets.length === 0}
              className="w-full h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100 disabled:opacity-60"
            >
              {datasetsQuery.isLoading && <option>Yukleniyor...</option>}
              {!datasetsQuery.isLoading && datasets.length === 0 && (
                <option value="">Veri seti yok</option>
              )}
              {datasets.map((d) => (
                <option key={d.dosya} value={d.dosya}>
                  {d.dosya} ({d.urun_sayisi} urun, {d.satir_sayisi} satir, {formatBytes(d.boyut_bytes)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-500 mb-1">
              Tahmin Gunu
            </label>
            <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
              {HORIZON_OPTIONS.map((value) => (
                <button
                  key={value}
                  onClick={() => setHorizon(value)}
                  className={`h-9 min-w-14 rounded-md px-3 text-sm font-bold transition ${
                    horizon === value
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-500 mb-1">
              Kapsam
            </label>
            <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
              <button
                onClick={() => setScope('all')}
                className={`h-9 px-3 rounded-md text-sm font-bold transition ${
                  scope === 'all' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                Tum Urunler
              </button>
              <button
                onClick={() => setScope('single')}
                className={`h-9 px-3 rounded-md text-sm font-bold transition ${
                  scope === 'single' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                Tek Urun
              </button>
            </div>
          </div>

          <div className="flex flex-col">
            <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-500 mb-1">
              &nbsp;
            </label>
            <button
              onClick={handleRun}
              disabled={!canRun}
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-blue-600 px-5 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <PlayCircle className="w-4 h-4" />
              )}
              Backtest Calistir
            </button>
          </div>
        </div>

        {scope === 'single' && (
          <div className="mt-3 max-w-xs">
            <label className="block text-xs font-extrabold uppercase tracking-wide text-slate-500 mb-1">
              Urun ID
            </label>
            <input
              type="number"
              min="1"
              value={singleUrunId}
              onChange={(event) => setSingleUrunId(event.target.value)}
              placeholder="orn. 1"
              className="w-full h-11 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        )}
      </section>

      {errorMessage && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {errorMessage}
        </div>
      )}

      {mutation.isPending && (
        <div className="min-h-[28vh] flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-sm font-semibold">Backtest calistiriliyor...</p>
        </div>
      )}

      {!mutation.isPending && !result && !errorMessage && datasets.length > 0 && (
        <div className="rounded-lg border border-dashed border-slate-200 bg-white py-14 text-center">
          <FlaskConical className="w-10 h-10 mx-auto text-slate-300" />
          <p className="mt-3 text-sm font-semibold text-slate-500">
            Veri setini sec ve "Backtest Calistir" butonuna bas.
          </p>
        </div>
      )}

      {!datasetsQuery.isLoading && datasets.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white py-14 text-center shadow-sm">
          <Database className="w-10 h-10 mx-auto text-slate-300" />
          <p className="mt-3 text-sm font-semibold text-slate-500">
            ml_models/talep_tahmin/data/raw altinda parquet dosyasi bulunamadi.
          </p>
          <p className="mt-1 text-xs text-slate-400">
            DataGenService timeseries_history senaryosuyla veri uretebilirsiniz.
          </p>
        </div>
      )}

      {result && !mutation.isPending && (
        <BacktestSonucGorunumu result={result} lastRunParams={lastRunParams} />
      )}
    </div>
  );
}

function BacktestSonucGorunumu({ result, lastRunParams }) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
        <MetricCard
          icon={Activity}
          label="Ortalama MAE"
          value={formatDecimal(result.mae)}
          detail="Mean Absolute Error"
          tone="blue"
        />
        <MetricCard
          icon={TrendingUp}
          label="Ortalama MAPE"
          value={`%${formatDecimal(result.mape)}`}
          detail="Mean Absolute Percentage Error"
          tone="indigo"
        />
        <MetricCard
          icon={Package}
          label="Urun Sayisi"
          value={formatNumber(result.urun_sayisi)}
          detail={lastRunParams?.urun_id ? `Tek urun (#${lastRunParams.urun_id})` : 'Tum urunler'}
          tone="emerald"
        />
        <MetricCard
          icon={BarChart3}
          label="Tahmin Gunu"
          value={`${result.tahmin_gun} gun`}
          detail={result.model_versiyonu}
          tone="amber"
        />
        <MetricCard
          icon={Database}
          label="Veri Kaynagi"
          value={result.veri_kaynagi.replace('.parquet', '')}
          detail="ml_models/.../data/raw"
          tone="slate"
        />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-4 py-3">
          <h2 className="text-sm font-extrabold text-slate-800">
            Per-Urun Sonuclar ({result.sonuclar.length})
          </h2>
        </div>
        {result.sonuclar.length === 0 ? (
          <div className="py-10 text-center text-sm font-semibold text-slate-500">
            Yeterli geçmis serisi olan urun bulunamadi (tahmin_gun {result.tahmin_gun} gunden buyuk seri gerekir).
          </div>
        ) : (
          <div className="max-h-[480px] overflow-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-50 text-xs font-extrabold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 text-left">Urun ID</th>
                  <th className="px-4 py-3 text-right">Gercek Talep</th>
                  <th className="px-4 py-3 text-right">Tahmin</th>
                  <th className="px-4 py-3 text-right">MAE</th>
                  <th className="px-4 py-3 text-right">MAPE</th>
                  <th className="px-4 py-3 text-right">Guven</th>
                  <th className="px-4 py-3 text-left">Stok Riski</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.sonuclar.map((row) => {
                  const riskClass = riskStyles[row.stok_riski] ?? riskStyles.yok;
                  return (
                    <tr key={row.urun_id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-extrabold text-slate-900">#{row.urun_id}</td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-700">
                        {formatDecimal(row.gercek_talep)}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-700">
                        {formatDecimal(row.tahmini_talep)}
                      </td>
                      <td className="px-4 py-3 text-right font-extrabold text-slate-900">
                        {formatDecimal(row.mae)}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-700">
                        %{formatDecimal(row.mape)}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-600">
                        %{formatNumber(row.veri_guven_skoru * 100)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-extrabold uppercase ${riskClass}`}>
                          {row.stok_riski}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function MetricCard({ icon, label, value, detail, tone }) {
  const Icon = icon;
  const tones = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-lg border ${tones[tone]}`}>
        <Icon className="h-5 w-5" strokeWidth={2.4} />
      </div>
      <p className="text-xs font-extrabold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900">{value}</p>
      <p className="mt-1 text-xs font-semibold text-slate-400">{detail}</p>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const rows = payload.filter((item) => item.value != null);
  if (rows.length === 0) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg">
      <p className="mb-1 text-xs font-extrabold uppercase tracking-wide text-slate-400">{label}</p>
      {rows.map((item) => (
        <div key={item.dataKey} className="flex items-center justify-between gap-5 text-sm">
          <span className="font-semibold text-slate-600">{item.name}</span>
          <span className="font-extrabold text-slate-900">{formatDecimal(item.value)}</span>
        </div>
      ))}
    </div>
  );
}
