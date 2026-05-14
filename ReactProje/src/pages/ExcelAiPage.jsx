import { useMemo, useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Loader2, Send } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useExcelAiHedefSemalarQuery,
  useExcelAiSemaEsleMutation,
  useExcelAiYorumlaMutation,
} from '../queries/excelAiQueries';
import ExcelDropzone from '../components/excelAi/ExcelDropzone';
import WorkbookHeader from '../components/excelAi/WorkbookHeader';
import SummaryPanel from '../components/excelAi/SummaryPanel';
import AnswerPanel from '../components/excelAi/AnswerPanel';
import MappingPanel from '../components/excelAi/MappingPanel';
import { hataMetni } from '../utils/hata';

const SAMPLE_QUESTIONS = [
  'Toplam satır kaç?',
  'Hangi sütunda en çok eksik veri var?',
  'Miktar sütununun ortalaması nedir?',
];

const MODES = [
  { id: 'yorum', label: 'yorum', subtitle: 'tabloyu, anlaşılır dilde' },
  { id: 'sema', label: 'şema', subtitle: 'sütunları wms şemasına eşle' },
];

export default function ExcelAiPage() {
  const [mode, setMode] = useState('yorum');
  const [file, setFile] = useState(null);
  const [soru, setSoru] = useState('');
  const [hedefSema, setHedefSema] = useState('siparis_kalemleri');
  const [activeSheet, setActiveSheet] = useState(null);
  const [yorumResult, setYorumResult] = useState(null);
  const [semaResult, setSemaResult] = useState(null);

  const semasQuery = useExcelAiHedefSemalarQuery();
  const yorumMutation = useExcelAiYorumlaMutation();
  const semaMutation = useExcelAiSemaEsleMutation();

  const busy = yorumMutation.isPending || semaMutation.isPending;

  const handleFile = (f) => {
    setFile(f);
    setActiveSheet(null);
    setYorumResult(null);
    setSemaResult(null);
  };

  const runYorum = async ({ withQuestion }) => {
    if (!file || busy) return;
    try {
      const data = await yorumMutation.mutateAsync({
        file,
        soru: withQuestion ? soru.trim() || undefined : undefined,
        sheet_name: activeSheet || undefined,
      });
      setYorumResult(data);
      if (!activeSheet) setActiveSheet(data.sheet_name);
    } catch (err) {
      toast.error(hataMetni(err, 'Excel yorumlanamadi.'));
    }
  };

  const runSemaEsle = async () => {
    if (!file || busy) return;
    try {
      const data = await semaMutation.mutateAsync({
        file,
        hedef_sema: hedefSema,
        sheet_name: activeSheet || undefined,
      });
      setSemaResult(data);
      if (!activeSheet) setActiveSheet(data.sheet_name);
    } catch (err) {
      toast.error(hataMetni(err, 'Sema esleme basarisiz.'));
    }
  };

  const workbook = yorumResult?.workbook ?? semaResult?.workbook ?? null;
  const summary = yorumResult?.summary ?? null;

  const semaOptions = useMemo(() => {
    const semas = semasQuery.data?.schemas ?? [];
    if (semas.length > 0) return semas;
    return [
      { name: 'siparis_kalemleri', label: 'Siparis Kalemleri' },
      { name: 'stok_sayim_kalemleri', label: 'Stok Sayim Kalemleri' },
      { name: 'urun', label: 'Urun Karti' },
    ];
  }, [semasQuery.data]);

  return (
    <div className="relative min-h-[calc(100vh-72px)] overflow-hidden bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      {/* Üst hairline + amber spotlight (AI Asistan ile birebir aynı dil) */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/60 to-transparent dark:via-amber-400/50"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[260px] w-[680px] -translate-x-1/2 -translate-y-1/3 rounded-full bg-amber-200/30 blur-[120px] dark:bg-amber-500/[0.08]"
      />

      <div className="mx-auto flex max-w-4xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
        {/* HEADER */}
        <Motion.header
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="border-b border-zinc-200/80 pb-5 dark:border-white/[0.06]"
        >
          <div className="flex items-baseline gap-3 sm:gap-4">
            <span className="select-none font-['JetBrains_Mono'] text-[13px] font-medium tracking-tight text-zinc-400 dark:text-zinc-500">
              [&nbsp;<span className="text-amber-600 dark:text-amber-400">xl</span>&nbsp;]
            </span>
            <h1 className="text-[17px] font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-[18px]">
              Excel Analizi
            </h1>
            <span className="font-['Instrument_Serif'] text-[16px] italic leading-none text-zinc-400 dark:text-zinc-500 sm:text-[17px]">
              — {MODES.find((m) => m.id === mode)?.subtitle}
            </span>
          </div>

          {/* Mode toggle: editorial mono pills */}
          <div className="mt-5 flex gap-x-5">
            {MODES.map((m) => {
              const active = mode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setMode(m.id)}
                  className={`group border-b py-1.5 transition ${
                    active
                      ? 'border-amber-500'
                      : 'border-transparent hover:border-zinc-300 dark:hover:border-white/15'
                  }`}
                >
                  <span
                    className={`font-['JetBrains_Mono'] text-[12px] uppercase tracking-[0.16em] ${
                      active
                        ? 'text-zinc-900 dark:text-zinc-100'
                        : 'text-zinc-500 dark:text-zinc-400'
                    }`}
                  >
                    {m.label}
                  </span>
                </button>
              );
            })}
          </div>
        </Motion.header>

        {/* DROPZONE */}
        <section>
          <ExcelDropzone file={file} onFile={handleFile} disabled={busy} />
        </section>

        {/* META — sayfa secici */}
        {workbook && (
          <WorkbookHeader
            workbook={workbook}
            activeSheet={activeSheet || workbook.primary_sheet?.name}
            onSheetChange={(name) => {
              setActiveSheet(name);
              setYorumResult(null);
              setSemaResult(null);
            }}
          />
        )}

        {/* MODE BODY */}
        {mode === 'yorum' ? (
          <YorumMode
            file={file}
            soru={soru}
            setSoru={setSoru}
            busy={yorumMutation.isPending}
            disabled={!file || busy}
            onSummarize={() => runYorum({ withQuestion: false })}
            onAsk={() => runYorum({ withQuestion: true })}
            summary={summary}
            answer={yorumResult?.answer}
            question={yorumResult?.question}
          />
        ) : (
          <SemaMode
            file={file}
            hedefSema={hedefSema}
            setHedefSema={setHedefSema}
            semaOptions={semaOptions}
            busy={semaMutation.isPending}
            disabled={!file || busy}
            onSubmit={runSemaEsle}
            result={semaResult}
          />
        )}
      </div>
    </div>
  );
}

/* ───────────────────────── YORUM MODE ───────────────────────── */
function YorumMode({
  file,
  soru,
  setSoru,
  busy,
  disabled,
  onSummarize,
  onAsk,
  summary,
  answer,
  question,
}) {
  return (
    <div className="space-y-7">
      {/* Action row */}
      <div className="flex flex-wrap items-center gap-3 border-b border-zinc-200/80 pb-5 dark:border-white/[0.06]">
        <button
          type="button"
          onClick={onSummarize}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 border border-zinc-300 bg-white px-3 py-1.5 font-['JetBrains_Mono'] text-[11.5px] uppercase tracking-wider text-zinc-700 transition hover:border-zinc-500 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/15 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-white/30"
        >
          {busy && !question ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <span className="text-amber-600 dark:text-amber-400">›</span>
          )}
          özet üret
        </button>
        <span className="font-['Instrument_Serif'] text-[14px] italic text-zinc-400 dark:text-zinc-500">
          {file ? 'dosya hazır' : 'önce dosya yükleyin'}
        </span>
      </div>

      {/* Question composer */}
      <div>
        <label className="block font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
          soru
        </label>
        <div className="mt-2 flex items-end gap-2 border-b border-zinc-300 focus-within:border-amber-500 dark:border-white/15">
          <textarea
            value={soru}
            onChange={(e) => setSoru(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onAsk();
              }
            }}
            rows={2}
            placeholder="örn. miktar sütununun ortalaması nedir?"
            className="flex-1 resize-none bg-transparent py-2 font-['JetBrains_Mono'] text-[13px] text-zinc-900 placeholder:italic placeholder:text-zinc-400 focus:outline-none dark:text-zinc-100 dark:placeholder:text-zinc-600"
          />
          <button
            type="button"
            onClick={onAsk}
            disabled={disabled || !soru.trim()}
            className="mb-2 inline-flex items-center gap-1.5 px-2.5 py-1.5 font-['JetBrains_Mono'] text-[11.5px] uppercase tracking-wider text-amber-700 transition hover:text-amber-900 disabled:cursor-not-allowed disabled:opacity-40 dark:text-amber-300 dark:hover:text-amber-200"
          >
            {busy && question ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" strokeWidth={2} />
            )}
            sor
          </button>
        </div>

        {/* Sample chips */}
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
          {SAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => setSoru(q)}
              className="font-['Instrument_Serif'] text-[14px] italic text-zinc-400 underline-offset-4 transition hover:text-zinc-900 hover:underline dark:text-zinc-500 dark:hover:text-zinc-100"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Answer */}
      <AnswerPanel question={question} answer={answer} />

      {/* Summary */}
      <SummaryPanel summary={summary} />
    </div>
  );
}

/* ───────────────────────── SEMA MODE ───────────────────────── */
function SemaMode({
  file,
  hedefSema,
  setHedefSema,
  semaOptions,
  busy,
  disabled,
  onSubmit,
  result,
}) {
  return (
    <div className="space-y-7">
      {/* Şema secici + run button */}
      <div className="flex flex-wrap items-end gap-x-6 gap-y-3 border-b border-zinc-200/80 pb-5 dark:border-white/[0.06]">
        <div className="flex flex-col">
          <label className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
            hedef şema
          </label>
          <div className="mt-1 flex gap-x-5">
            {semaOptions.map((s) => {
              const active = hedefSema === s.name;
              return (
                <button
                  key={s.name}
                  type="button"
                  onClick={() => setHedefSema(s.name)}
                  className={`group border-b py-1.5 transition ${
                    active
                      ? 'border-amber-500'
                      : 'border-transparent hover:border-zinc-300 dark:hover:border-white/15'
                  }`}
                >
                  <span
                    className={`font-['JetBrains_Mono'] text-[12px] ${
                      active
                        ? 'text-zinc-900 dark:text-zinc-100'
                        : 'text-zinc-500 group-hover:text-zinc-700 dark:text-zinc-400 dark:group-hover:text-zinc-200'
                    }`}
                  >
                    {s.name}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 border border-zinc-300 bg-white px-3 py-1.5 font-['JetBrains_Mono'] text-[11.5px] uppercase tracking-wider text-zinc-700 transition hover:border-zinc-500 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/15 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-white/30"
        >
          {busy ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <span className="text-amber-600 dark:text-amber-400">›</span>
          )}
          eşle
        </button>
        {!file && (
          <span className="font-['Instrument_Serif'] text-[14px] italic text-zinc-400 dark:text-zinc-500">
            önce dosya yükleyin
          </span>
        )}
      </div>

      <MappingPanel result={result} />
    </div>
  );
}
