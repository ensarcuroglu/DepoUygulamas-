import { useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  FileText,
  Gauge,
  History,
  Loader2,
  Package,
  Play,
  RefreshCw,
  Route,
  Server,
  ShieldAlert,
  SlidersHorizontal,
  TimerReset,
  X,
  Zap,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useDataGenHealthQuery,
  useDataGenMetadataQuery,
  useDataGenRunScenarioMutation,
} from '../../queries/dataGenQueries';
import { hataMetni } from '../../utils/hata';

const HISTORY_KEY = 'depo.dataGen.recentRuns.v1';

const FALLBACK_SCENARIOS = [
  {
    name: 'seed_baseline',
    label: 'Temel Seed Verisi',
    description: 'Raf, urun, lot ve palet zinciri',
    default_target: 'rest',
    allowed_targets: ['rest'],
    risk_level: 'high',
    confirmation_required: true,
    count_label: 'Toplam seed olcegi',
  },
  {
    name: 'task_load',
    label: 'Gorev Yuk Testi',
    description: 'Toplama gorevleri ve LMS event hatti',
    default_target: 'rest',
    allowed_targets: ['rest', 'rabbit'],
    risk_level: 'medium',
    confirmation_required: true,
    count_label: 'Gorev/event adedi',
    target_notes: {
      rabbit: 'Rabbit hedefi saf yuk testidir; anlamli LMS akisi icin rest tercih edilir.',
    },
  },
  {
    name: 'timeseries_history',
    label: 'Talep Zaman Serisi',
    description: 'ML egitimi icin dosya ciktisi',
    default_target: 'file',
    allowed_targets: ['file'],
    risk_level: 'low',
    confirmation_required: false,
    count_label: 'Urun adedi',
  },
  {
    name: 'agv_traffic',
    label: 'AGV Trafik Uretimi',
    description: 'Backend yerlestirme gorevi trafigi',
    default_target: 'rest',
    allowed_targets: ['rest'],
    risk_level: 'high',
    confirmation_required: true,
    count_label: 'Yerlestirme gorevi adedi',
  },
];

const SAFE_COUNT_DEFAULTS = {
  seed_baseline: '20',
  task_load: '50',
  timeseries_history: '10',
  agv_traffic: '25',
};

const SCENARIO_ICONS = {
  seed_baseline: Package,
  task_load: Activity,
  timeseries_history: FileText,
  agv_traffic: Route,
};

const TARGET_LABELS = {
  rest: 'REST',
  rabbit: 'RabbitMQ',
  file: 'Dosya',
};

const TARGET_BADGES = {
  rest: 'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:ring-rose-900',
  rabbit: 'bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-950/30 dark:text-violet-300 dark:ring-violet-900',
  file: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:ring-emerald-900',
};

const riskLabel = {
  high: 'Yuksek risk',
  medium: 'Kontrollu',
  low: 'Guvenli',
};

const loadHistory = () => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const saveHistory = (items) => {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, 8)));
};

const numberFormat = new Intl.NumberFormat('tr-TR');

const formatNumber = (value) =>
  value === null || value === undefined ? '-' : numberFormat.format(Number(value));

const formatDateTime = (value) => {
  try {
    return new Intl.DateTimeFormat('tr-TR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return '-';
  }
};

const payloadFromForm = ({ count, seed, batchSize, concurrency, target }) => {
  const payload = { target };
  if (count !== '') payload.count = Number(count);
  if (seed !== '') payload.seed = Number(seed);
  if (batchSize !== '') payload.batch_size = Number(batchSize);
  if (concurrency !== '') payload.concurrency = Number(concurrency);
  return payload;
};

export default function SentetikVeriPage() {
  const [scenarioName, setScenarioName] = useState('timeseries_history');
  const [target, setTarget] = useState('file');
  const [count, setCount] = useState(SAFE_COUNT_DEFAULTS.timeseries_history);
  const [seed, setSeed] = useState('42');
  const [batchSize, setBatchSize] = useState('500');
  const [concurrency, setConcurrency] = useState('10');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState(loadHistory);
  const [confirmPayload, setConfirmPayload] = useState(null);

  const metadataQuery = useDataGenMetadataQuery();
  const healthQuery = useDataGenHealthQuery();
  const runMutation = useDataGenRunScenarioMutation();

  const scenarios = useMemo(() => {
    const remote = metadataQuery.data?.scenarios;
    return Array.isArray(remote) && remote.length > 0 ? remote : FALLBACK_SCENARIOS;
  }, [metadataQuery.data]);

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.name === scenarioName) ?? scenarios[0],
    [scenarioName, scenarios],
  );

  const allowedTargets = selectedScenario?.allowed_targets ?? ['file'];
  const selectedIcon = SCENARIO_ICONS[selectedScenario?.name] ?? DatabaseZap;
  const TargetIcon = target === 'rest' ? Zap : target === 'rabbit' ? Activity : FileText;
  const serviceOk = healthQuery.data?.status === 'ok';
  const busy = runMutation.isPending;

  const addHistory = (entry) => {
    setHistory((prev) => {
      const next = [entry, ...prev].slice(0, 8);
      saveHistory(next);
      return next;
    });
  };

  const runWithPayload = async (payload) => {
    try {
      const data = await runMutation.mutateAsync({ name: selectedScenario.name, payload });
      const entry = {
        id: `${Date.now()}-${selectedScenario.name}`,
        createdAt: new Date().toISOString(),
        scenario: selectedScenario.name,
        scenarioLabel: selectedScenario.label,
        target: payload.target,
        payload,
        result: data,
      };
      setResult(data);
      addHistory(entry);
      toast.success('Sentetik veri calistirmasi tamamlandi.');
      setConfirmPayload(null);
      void healthQuery.refetch();
    } catch (err) {
      toast.error(hataMetni(err, 'Sentetik veri calistirmasi basarisiz.'));
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = payloadFromForm({ count, seed, batchSize, concurrency, target });
    if (target === 'rest') {
      setConfirmPayload(payload);
      return;
    }
    void runWithPayload(payload);
  };

  const handleScenarioSelect = (name) => {
    const nextScenario = scenarios.find((scenario) => scenario.name === name) ?? scenarios[0];
    setScenarioName(name);
    if (nextScenario) {
      setTarget(nextScenario.default_target);
      setCount(SAFE_COUNT_DEFAULTS[nextScenario.name] ?? '');
    }
  };

  return (
    <div className="min-h-full bg-slate-50 px-4 py-5 text-slate-900 dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-sm dark:bg-slate-100 dark:text-slate-950">
              <DatabaseZap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-400">
                Admin kontrol masasi
              </p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight">Sentetik Veri</h1>
              <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                DataGenService senaryolarini guvenli proxy uzerinden calistirin.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <StatusPill
              loading={healthQuery.isLoading || healthQuery.isFetching}
              ok={serviceOk}
              error={healthQuery.isError}
            />
            <button
              type="button"
              onClick={() => healthQuery.refetch()}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              disabled={healthQuery.isFetching}
            >
              <RefreshCw className={`h-4 w-4 ${healthQuery.isFetching ? 'animate-spin' : ''}`} />
              Yenile
            </button>
          </div>
        </header>

        {metadataQuery.isError && (
          <InlineAlert
            tone="rose"
            icon={<AlertTriangle className="h-4 w-4" />}
            title="Metadata alinamadi"
            text={hataMetni(metadataQuery.error, 'DataGen metadata alinamadi.')}
          />
        )}

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_380px]">
          <main className="space-y-5">
            <section className="rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                  <h2 className="font-semibold">Senaryo</h2>
                </div>
              </div>

              <div className="grid gap-3 p-4 md:grid-cols-2">
                {scenarios.map((scenario) => {
                  const Icon = SCENARIO_ICONS[scenario.name] ?? DatabaseZap;
                  const active = scenario.name === selectedScenario.name;
                  return (
                    <button
                      key={scenario.name}
                      type="button"
                      onClick={() => handleScenarioSelect(scenario.name)}
                      className={`min-h-[112px] rounded-md border p-4 text-left transition ${
                        active
                          ? 'border-sky-400 bg-sky-50 ring-2 ring-sky-100 dark:border-sky-500 dark:bg-sky-950/30 dark:ring-sky-900/40'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-800/70'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className={`flex h-10 w-10 items-center justify-center rounded-md ${active ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>
                            <Icon className="h-5 w-5" />
                          </span>
                          <div>
                            <h3 className="font-semibold">{scenario.label}</h3>
                            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                              {scenario.description}
                            </p>
                          </div>
                        </div>
                        <span className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-bold uppercase tracking-wide ${
                          scenario.risk_level === 'high'
                            ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300'
                            : scenario.risk_level === 'medium'
                              ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300'
                              : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
                        }`}
                        >
                          {riskLabel[scenario.risk_level] ?? scenario.risk_level}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <form
              onSubmit={handleSubmit}
              className="rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {(() => {
                      const Icon = selectedIcon;
                      return <Icon className="h-5 w-5 text-sky-600 dark:text-sky-400" />;
                    })()}
                    <h2 className="font-semibold">{selectedScenario.label}</h2>
                  </div>
                  <span className={`rounded-md px-2.5 py-1 text-xs font-bold ring-1 ${TARGET_BADGES[target]}`}>
                    {TARGET_LABELS[target]}
                  </span>
                </div>
              </div>

              <div className="space-y-5 p-4">
                <div>
                  <span className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Hedef
                  </span>
                  <div className="inline-grid grid-cols-3 rounded-md border border-slate-200 bg-slate-100 p-1 dark:border-slate-800 dark:bg-slate-950">
                    {['rest', 'rabbit', 'file'].map((item) => {
                      const disabled = !allowedTargets.includes(item);
                      return (
                        <button
                          key={item}
                          type="button"
                          onClick={() => !disabled && setTarget(item)}
                          disabled={disabled}
                          className={`h-9 min-w-[92px] rounded px-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:text-slate-300 dark:disabled:text-slate-700 ${
                            target === item
                              ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-slate-100'
                              : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100'
                          }`}
                        >
                          {TARGET_LABELS[item]}
                        </button>
                      );
                    })}
                  </div>
                  {selectedScenario.target_notes?.[target] && (
                    <p className="mt-2 flex items-start gap-2 text-sm text-amber-700 dark:text-amber-300">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      {selectedScenario.target_notes[target]}
                    </p>
                  )}
                </div>

                <div className="grid gap-3 md:grid-cols-4">
                  <NumberField
                    label={selectedScenario.count_label || 'Adet'}
                    value={count}
                    onChange={setCount}
                    min="1"
                  />
                  <NumberField label="Seed" value={seed} onChange={setSeed} />
                  <NumberField label="Batch" value={batchSize} onChange={setBatchSize} min="1" />
                  <NumberField label="Concurrency" value={concurrency} onChange={setConcurrency} min="1" />
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <MetricHint icon={<TargetIcon className="h-4 w-4" />} label="Hedef" value={TARGET_LABELS[target]} />
                  <MetricHint icon={<TimerReset className="h-4 w-4" />} label="Timeout" value="300 sn" />
                  <MetricHint icon={<ShieldAlert className="h-4 w-4" />} label="Yetki" value="Admin" />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {target === 'rest'
                      ? 'REST hedefi veritabaninda gercek is akisi olusturur.'
                      : target === 'rabbit'
                        ? 'RabbitMQ hedefi event hattini yukler.'
                        : 'Dosya hedefi ML ham veri dizinine cikti yazar.'}
                  </p>
                  <button
                    type="submit"
                    disabled={busy || !serviceOk}
                    className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white"
                  >
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    Calistir
                  </button>
                </div>
              </div>
            </form>

            <ResultPanel result={result} />
          </main>

          <aside className="space-y-5">
            <section className="rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                  <h2 className="font-semibold">Servis durumu</h2>
                </div>
              </div>
              <div className="space-y-3 p-4">
                <HealthRow label="Durum" value={serviceOk ? 'ok' : healthQuery.isError ? 'erisilemiyor' : 'kontrol ediliyor'} />
                <HealthRow label="Servis" value={healthQuery.data?.service || 'data-gen'} />
                <HealthRow label="Feature" value="aktif" />
              </div>
            </section>

            <HistoryPanel history={history} onClear={() => { setHistory([]); saveHistory([]); }} />
          </aside>
        </div>
      </div>

      {confirmPayload && (
        <ConfirmModal
          scenario={selectedScenario}
          payload={confirmPayload}
          busy={busy}
          onClose={() => setConfirmPayload(null)}
          onConfirm={() => runWithPayload(confirmPayload)}
        />
      )}
    </div>
  );
}

function StatusPill({ loading, ok, error }) {
  const tone = ok
    ? 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:ring-emerald-900'
    : error
      ? 'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:ring-rose-900'
      : 'bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-800';
  return (
    <span className={`inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm font-semibold ring-1 ${tone}`}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : ok ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
      {ok ? 'DataGen hazir' : error ? 'DataGen erisilemiyor' : 'Kontrol ediliyor'}
    </span>
  );
}

function InlineAlert({ tone, icon, title, text }) {
  const styles = tone === 'rose'
    ? 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200'
    : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200';
  return (
    <div className={`flex items-start gap-3 rounded-md border px-4 py-3 ${styles}`}>
      <span className="mt-0.5 shrink-0">{icon}</span>
      <div>
        <p className="font-semibold">{title}</p>
        <p className="mt-1 text-sm opacity-90">{text}</p>
      </div>
    </div>
  );
}

function NumberField({ label, value, onChange, min }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </span>
      <input
        type="number"
        min={min}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
      />
    </label>
  );
}

function MetricHint({ icon, label, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/50">
      <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
        {icon}
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
      </div>
      <p className="mt-1 font-semibold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function ResultPanel({ result }) {
  if (!result) {
    return (
      <section className="rounded-md border border-dashed border-slate-300 bg-white p-8 text-center dark:border-slate-700 dark:bg-slate-900">
        <Gauge className="mx-auto h-8 w-8 text-slate-400" />
        <p className="mt-3 font-semibold text-slate-700 dark:text-slate-200">Sonuc bekleniyor</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Ilk calistirma tamamlandiginda metrikler burada gorunur.</p>
      </section>
    );
  }

  const successRate = result.total ? Math.round((Number(result.success) / Number(result.total)) * 100) : 0;

  return (
    <section className="rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Gauge className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          <h2 className="font-semibold">Son calistirma</h2>
        </div>
      </div>
      <div className="space-y-4 p-4">
        <div className="grid gap-3 sm:grid-cols-5">
          <ResultMetric label="Toplam" value={formatNumber(result.total)} />
          <ResultMetric label="Basarili" value={formatNumber(result.success)} tone="emerald" />
          <ResultMetric label="Hatali" value={formatNumber(result.failed)} tone={result.failed ? 'rose' : 'slate'} />
          <ResultMetric label="Sure" value={`${result.duration_sec ?? 0} sn`} />
          <ResultMetric label="p95" value={`${result.p95_latency_ms ?? 0} ms`} />
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${Math.min(successRate, 100)}%` }}
          />
        </div>

        {result.output_path && (
          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/50">
            <span className="font-semibold text-slate-500 dark:text-slate-400">Cikti: </span>
            <span className="break-all font-mono text-slate-800 dark:text-slate-100">{result.output_path}</span>
          </div>
        )}

        {Array.isArray(result.errors) && result.errors.length > 0 && (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            {result.errors.map((error) => (
              <p key={error}>{error}</p>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function ResultMetric({ label, value, tone = 'slate' }) {
  const color = tone === 'emerald'
    ? 'text-emerald-700 dark:text-emerald-300'
    : tone === 'rose'
      ? 'text-rose-700 dark:text-rose-300'
      : 'text-slate-900 dark:text-slate-100';
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1 text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function HealthRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2 last:border-b-0 last:pb-0 dark:border-slate-800">
      <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>
      <span className="max-w-[180px] truncate text-sm font-semibold text-slate-800 dark:text-slate-100">{value}</span>
    </div>
  );
}

function HistoryPanel({ history, onClear }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-sky-600 dark:text-sky-400" />
          <h2 className="font-semibold">Son kosular</h2>
        </div>
        {history.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            className="text-xs font-semibold text-slate-500 transition hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-300"
          >
            Temizle
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="p-6 text-sm text-slate-500 dark:text-slate-400">Kayit yok.</div>
      ) : (
        <div className="divide-y divide-slate-200 dark:divide-slate-800">
          {history.map((item) => (
            <div key={item.id} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-800 dark:text-slate-100">{item.scenarioLabel}</p>
                  <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <Clock3 className="h-3.5 w-3.5" />
                    {formatDateTime(item.createdAt)}
                  </p>
                </div>
                <span className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-bold ring-1 ${TARGET_BADGES[item.target]}`}>
                  {TARGET_LABELS[item.target]}
                </span>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <MiniMetric label="Toplam" value={formatNumber(item.result?.total)} />
                <MiniMetric label="OK" value={formatNumber(item.result?.success)} />
                <MiniMetric label="Hata" value={formatNumber(item.result?.failed)} />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function MiniMetric({ label, value }) {
  return (
    <div className="rounded-md bg-slate-50 px-2 py-1.5 dark:bg-slate-950/60">
      <span className="block text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-500">{label}</span>
      <span className="font-bold text-slate-800 dark:text-slate-100">{value}</span>
    </div>
  );
}

function ConfirmModal({ scenario, payload, busy, onClose, onConfirm }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="w-full rounded-t-xl bg-white p-5 shadow-2xl dark:bg-slate-900 sm:max-w-lg sm:rounded-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">REST calistirma onayi</h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {scenario.label} gercek backend is akislarina veri yazacak.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
          <pre className="whitespace-pre-wrap break-words">{JSON.stringify(payload, null, 2)}</pre>
        </div>

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="h-10 rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Vazgec
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-rose-600 px-4 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-50"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <DatabaseZap className="h-4 w-4" />}
            Onayla ve calistir
          </button>
        </div>
      </div>
    </div>
  );
}
