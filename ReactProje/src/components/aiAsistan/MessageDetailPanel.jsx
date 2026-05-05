import { useState, useMemo } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Code2, Database, Download, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { exportToExcel } from '../../utils/exportUtils';

function formatValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export default function MessageDetailPanel({ uretilenSql, debug }) {
  const [open, setOpen] = useState(false);
  const [sqlCopied, setSqlCopied] = useState(false);

  const rows = useMemo(() => debug?.rows ?? [], [debug]);
  const columns = debug?.columns ?? (rows[0] ? Object.keys(rows[0]) : []);
  const rowCount = debug?.row_count ?? rows.length;
  const previewRows = useMemo(() => rows.slice(0, 50), [rows]);

  const handleCopySql = async () => {
    if (!uretilenSql) return;
    try {
      await navigator.clipboard.writeText(uretilenSql);
      setSqlCopied(true);
      toast.success('SQL kopyalandı');
      setTimeout(() => setSqlCopied(false), 1600);
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
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white/60 px-3 py-1.5 text-[11.5px] font-medium text-slate-600 backdrop-blur transition hover:border-slate-300 hover:bg-white/80 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
      >
        <Code2 className="h-3.5 w-3.5" />
        Detayları {open ? 'gizle' : 'göster'}
        <Motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="h-3.5 w-3.5" />
        </Motion.span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <Motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-3 rounded-2xl border border-slate-200/70 bg-white/50 p-3 backdrop-blur-md dark:border-white/10 dark:bg-white/5">
              {/* SQL */}
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    <Code2 className="h-3 w-3" /> Üretilen SQL
                  </span>
                  <button
                    type="button"
                    onClick={handleCopySql}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/10 dark:hover:text-slate-200"
                  >
                    {sqlCopied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    Kopyala
                  </button>
                </div>
                <pre className="overflow-x-auto rounded-xl bg-slate-900/95 p-3 text-[12px] leading-relaxed text-slate-100 shadow-inner">
                  <code>{uretilenSql || '—'}</code>
                </pre>
              </div>

              {/* Sonuç tablosu */}
              {rows.length > 0 && (
                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      <Database className="h-3 w-3" /> Sonuç ({rowCount} satır)
                    </span>
                    <button
                      type="button"
                      onClick={handleExport}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-emerald-600 transition hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-500/10"
                    >
                      <Download className="h-3 w-3" /> Excel'e indir
                    </button>
                  </div>
                  <div className="overflow-x-auto rounded-xl border border-slate-200/70 bg-white/70 dark:border-white/10 dark:bg-slate-900/30">
                    <table className="min-w-full text-[12px]">
                      <thead className="border-b border-slate-200/70 bg-slate-50/70 dark:border-white/10 dark:bg-white/5">
                        <tr>
                          {columns.map((col) => (
                            <th
                              key={col}
                              className="whitespace-nowrap px-3 py-2 text-left font-semibold text-slate-600 dark:text-slate-300"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewRows.map((row, i) => (
                          <tr
                            key={i}
                            className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60 dark:border-white/5 dark:hover:bg-white/5"
                          >
                            {columns.map((col) => (
                              <td
                                key={col}
                                className="whitespace-nowrap px-3 py-1.5 text-slate-700 dark:text-slate-200"
                              >
                                {formatValue(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {rowCount > previewRows.length && (
                      <div className="border-t border-slate-200/70 bg-slate-50/40 px-3 py-1.5 text-[11px] text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                        İlk {previewRows.length} satır gösteriliyor — Excel'e indir tüm {rowCount} satır.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Düzeltme logu */}
              {debug?.duzeltme_logu?.length > 1 && (
                <div>
                  <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Düzeltme Logu
                  </span>
                  <ul className="space-y-1 text-[12px] text-slate-600 dark:text-slate-300">
                    {debug.duzeltme_logu.map((line, i) => (
                      <li key={i} className="rounded-md bg-amber-50/60 px-2 py-1 font-mono text-[11px] text-amber-900 dark:bg-amber-400/10 dark:text-amber-200">
                        {line}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
