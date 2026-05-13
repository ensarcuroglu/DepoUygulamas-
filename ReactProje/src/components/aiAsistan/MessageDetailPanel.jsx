import { useMemo, useState } from 'react';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import {
  BookOpenText,
  Check,
  ChevronDown,
  Code2,
  Copy,
  Database,
  Download,
  FileTerminal,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { exportToExcel } from '../../utils/exportUtils';

function formatValue(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export default function MessageDetailPanel({ uretilenSql, debug, route, sources = [] }) {
  const [open, setOpen] = useState(false);
  const [sqlCopied, setSqlCopied] = useState(false);

  const rows = useMemo(() => debug?.rows ?? [], [debug]);
  const columns = debug?.columns ?? (rows[0] ? Object.keys(rows[0]) : []);
  const rowCount = debug?.row_count ?? rows.length;
  const previewRows = useMemo(() => rows.slice(0, 50), [rows]);
  const isDocs = route === 'docs';

  const handleCopySql = async () => {
    if (!uretilenSql) return;
    try {
      await navigator.clipboard.writeText(uretilenSql);
      setSqlCopied(true);
      toast.success('SQL kopyalandı');
      setTimeout(() => setSqlCopied(false), 2000);
    } catch {
      toast.error('Kopyalanamadı');
    }
  };

  const handleExport = () => {
    if (!rows.length) {
      toast.error('Dışa aktarılacak veri yok');
      return;
    }
    exportToExcel(rows, `ai-asistan-sonuc-${Date.now()}`);
  };

  return (
    <div className="w-full">
      <Motion.button
        type="button"
        whileTap={{ scale: 0.97 }}
        onClick={() => setOpen((v) => !v)}
        className="group inline-flex items-center gap-2 rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 font-['JetBrains_Mono'] text-[11px] font-medium uppercase tracking-wider text-zinc-600 transition hover:border-amber-400 hover:text-amber-700 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-amber-400/40 dark:hover:text-amber-300"
      >
        {isDocs ? (
          <BookOpenText className="h-3.5 w-3.5" strokeWidth={1.75} />
        ) : (
          <FileTerminal className="h-3.5 w-3.5" strokeWidth={1.75} />
        )}
        {isDocs ? 'kaynaklar' : 'sorgu detayları'}
        <Motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ type: 'spring', stiffness: 260, damping: 20 }}
          className="ml-0.5 opacity-60 group-hover:opacity-100"
        >
          <ChevronDown className="h-3.5 w-3.5" strokeWidth={2.25} />
        </Motion.span>
      </Motion.button>

      <AnimatePresence initial={false}>
        {open && (
          <Motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="space-y-5 rounded-xl border border-zinc-200 bg-white p-4 dark:border-white/[0.08] dark:bg-zinc-900/60 sm:p-5">
              {isDocs && sources.length > 0 && (
                <section>
                  <header className="mb-2.5 flex items-center gap-2">
                    <BookOpenText className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" strokeWidth={2} />
                    <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                      doküman kaynakları
                    </span>
                  </header>
                  <div className="divide-y divide-zinc-100 overflow-hidden rounded-md border border-zinc-200 dark:divide-white/[0.06] dark:border-white/[0.08]">
                    {sources.map((source, index) => (
                      <div
                        key={`${source.source_path}-${source.chunk_id ?? index}`}
                        className="bg-white px-3 py-2.5 dark:bg-zinc-900/60"
                      >
                        <div className="font-['JetBrains_Mono'] text-[12px] font-medium text-zinc-800 dark:text-zinc-100">
                          {source.source_path}
                        </div>
                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 font-['JetBrains_Mono'] text-[11px] text-zinc-500 dark:text-zinc-400">
                          {source.section && <span>{source.section}</span>}
                          {source.score !== undefined && (
                            <span>score <span className="text-amber-600 dark:text-amber-400">{source.score}</span></span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {!isDocs && (
                <section>
                  <header className="mb-2.5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Code2 className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" strokeWidth={2} />
                      <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        üretilen sql
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleCopySql}
                      className="inline-flex h-6 items-center gap-1.5 rounded border border-zinc-200 bg-white px-2 font-['JetBrains_Mono'] text-[10.5px] font-medium text-zinc-500 transition hover:border-amber-400 hover:text-amber-700 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-amber-400/40 dark:hover:text-amber-300"
                    >
                      {sqlCopied ? (
                        <Check className="h-3 w-3 text-emerald-500" strokeWidth={2.5} />
                      ) : (
                        <Copy className="h-3 w-3" strokeWidth={2} />
                      )}
                      {sqlCopied ? 'kopyalandı' : 'kopyala'}
                    </button>
                  </header>
                  <div className="relative overflow-hidden rounded-md border border-zinc-900 bg-[#0a0a0a] dark:border-white/[0.06]">
                    <div className="border-b border-white/[0.06] px-3 py-1.5 font-['JetBrains_Mono'] text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                      sql
                    </div>
                    <pre className="overflow-x-auto p-4 font-['JetBrains_Mono'] text-[12.5px] leading-relaxed text-zinc-200 [scrollbar-width:thin] sm:text-[13px]">
                      <code>{uretilenSql || '-'}</code>
                    </pre>
                  </div>
                </section>
              )}

              {!isDocs && rows.length > 0 && (
                <section>
                  <header className="mb-2.5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" strokeWidth={2} />
                      <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        sonuç
                      </span>
                      <span className="font-['JetBrains_Mono'] text-[10.5px] tracking-wider text-zinc-400 dark:text-zinc-500">
                        {rowCount} satır
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleExport}
                      className="inline-flex h-6 items-center gap-1.5 rounded border border-emerald-300/70 bg-emerald-50 px-2 font-['JetBrains_Mono'] text-[10.5px] font-medium text-emerald-700 transition hover:bg-emerald-100 dark:border-emerald-400/30 dark:bg-emerald-400/10 dark:text-emerald-300 dark:hover:bg-emerald-400/20"
                    >
                      <Download className="h-3 w-3" strokeWidth={2} /> excel
                    </button>
                  </header>

                  <div className="overflow-hidden rounded-md border border-zinc-200 bg-white dark:border-white/[0.08] dark:bg-zinc-900/60">
                    <div className="max-h-[300px] overflow-auto [scrollbar-width:thin]">
                      <table className="min-w-full font-['JetBrains_Mono'] text-[12px] tabular-nums">
                        <thead className="sticky top-0 z-10 border-b border-zinc-200 bg-zinc-50 dark:border-white/[0.08] dark:bg-zinc-900">
                          <tr>
                            {columns.map((col) => (
                              <th
                                key={col}
                                className="whitespace-nowrap px-3 py-2 text-left text-[10.5px] font-semibold uppercase tracking-[0.12em] text-zinc-600 dark:text-zinc-300"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-100 dark:divide-white/[0.04]">
                          {previewRows.map((row, rowIndex) => (
                            <tr
                              key={rowIndex}
                              className="transition-colors hover:bg-amber-50/40 dark:hover:bg-amber-400/[0.04]"
                            >
                              {columns.map((col) => (
                                <td
                                  key={col}
                                  className="whitespace-nowrap px-3 py-1.5 text-zinc-700 dark:text-zinc-300"
                                >
                                  {formatValue(row[col])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {rowCount > previewRows.length && (
                      <div className="border-t border-zinc-200 bg-zinc-50 px-3 py-1.5 text-center font-['JetBrains_Mono'] text-[10.5px] tracking-wide text-zinc-500 dark:border-white/[0.08] dark:bg-white/[0.02] dark:text-zinc-400">
                        ilk {previewRows.length} satır · tümü için excel'e aktar
                      </div>
                    )}
                  </div>
                </section>
              )}

              {!isDocs && debug?.duzeltme_logu?.length > 1 && (
                <section>
                  <header className="mb-2 flex items-center gap-2">
                    <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                      düzeltme logu
                    </span>
                  </header>
                  <ul className="space-y-1.5">
                    {debug.duzeltme_logu.map((line, index) => (
                      <li
                        key={index}
                        className="rounded-md border-l-2 border-amber-400 bg-amber-50/70 px-3 py-2 font-['JetBrains_Mono'] text-[11.5px] leading-relaxed text-amber-900 dark:border-amber-400/60 dark:bg-amber-400/[0.06] dark:text-amber-200"
                      >
                        {line}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
