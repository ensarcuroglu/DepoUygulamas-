import { useState, useMemo } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Code2, Database, Download, Copy, Check, FileTerminal } from 'lucide-react';
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
    <div className="mt-3 w-full">
      <Motion.button
        type="button"
        whileTap={{ scale: 0.97 }}
        onClick={() => setOpen((v) => !v)}
        className="group inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/70 px-3.5 py-1.5 text-[12px] font-medium text-slate-600 shadow-[0_2px_8px_-4px_rgba(15,23,42,0.08)] backdrop-blur-md transition-all duration-300 hover:border-indigo-300/80 hover:bg-white hover:text-indigo-600 dark:border-white/10 dark:bg-slate-800/60 dark:text-slate-300 dark:hover:border-indigo-400/50 dark:hover:bg-slate-800/90 dark:hover:text-indigo-300 sm:px-4 sm:py-2"
      >
        <FileTerminal className="h-3.5 w-3.5 sm:h-4 sm:w-4" strokeWidth={2} />
        Sorgu Detayları
        <Motion.span 
          animate={{ rotate: open ? 180 : 0 }} 
          transition={{ type: "spring", stiffness: 260, damping: 20 }}
          className="ml-0.5 opacity-70 group-hover:opacity-100"
        >
          <ChevronDown className="h-3.5 w-3.5 sm:h-4 sm:w-4" strokeWidth={2.5} />
        </Motion.span>
      </Motion.button>

      <AnimatePresence initial={false}>
        {open && (
          <Motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="space-y-4 rounded-[1.25rem] border border-slate-200/80 bg-white/60 p-3.5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/40 sm:p-5">
              
              {/* SQL Paneli */}
              <div>
                <div className="mb-2 flex items-center justify-between px-1">
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 sm:text-[12px]">
                    <Code2 className="h-3.5 w-3.5" /> Üretilen SQL
                  </span>
                  <button
                    type="button"
                    onClick={handleCopySql}
                    className="inline-flex h-7 items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 text-[11.5px] font-medium text-slate-600 transition-colors hover:bg-indigo-50 hover:text-indigo-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-indigo-500/20 dark:hover:text-indigo-300"
                  >
                    {sqlCopied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                    {sqlCopied ? 'Kopyalandı' : 'Kopyala'}
                  </button>
                </div>
                <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-[#0D1117] shadow-inner dark:border-white/10">
                  <div className="absolute top-0 left-0 flex h-7 w-full items-center gap-1.5 bg-slate-800/50 px-3">
                    <div className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                  </div>
                  <pre className="overflow-x-auto p-4 pt-10 text-[13px] leading-relaxed text-slate-300 [scrollbar-width:thin] sm:text-[13.5px]">
                    <code>{uretilenSql || '—'}</code>
                  </pre>
                </div>
              </div>

              {/* Sonuç Tablosu */}
              {rows.length > 0 && (
                <div>
                  <div className="mb-2 flex items-center justify-between px-1">
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 sm:text-[12px]">
                      <Database className="h-3.5 w-3.5" /> Sonuç ({rowCount} satır)
                    </span>
                    <button
                      type="button"
                      onClick={handleExport}
                      className="inline-flex h-7 items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 text-[11.5px] font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20"
                    >
                      <Download className="h-3.5 w-3.5" /> Excel'e İndir
                    </button>
                  </div>
                  
                  <div className="overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/50">
                    <div className="max-h-[300px] overflow-auto [scrollbar-width:thin]">
                      <table className="min-w-full text-[13px]">
                        <thead className="sticky top-0 z-10 border-b border-slate-200/80 bg-slate-50/95 backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/95">
                          <tr>
                            {columns.map((col) => (
                              <th
                                key={col}
                                className="whitespace-nowrap px-4 py-2.5 text-left font-semibold text-slate-700 dark:text-slate-200"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                          {previewRows.map((row, i) => (
                            <tr
                              key={i}
                              className="transition-colors hover:bg-slate-50/80 dark:hover:bg-white/[0.03]"
                            >
                              {columns.map((col) => (
                                <td
                                  key={col}
                                  className="whitespace-nowrap px-4 py-2 text-slate-600 dark:text-slate-300"
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
                      <div className="border-t border-slate-200/80 bg-slate-50/50 px-4 py-2 text-center text-[11px] font-medium text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 sm:text-[12px]">
                        İlk {previewRows.length} satır gösteriliyor. Tüm {rowCount} satırı görmek için Excel'e indirin.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Düzeltme Logu */}
              {debug?.duzeltme_logu?.length > 1 && (
                <div>
                  <span className="mb-2 block px-1 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 sm:text-[12px]">
                    Düzeltme Logu
                  </span>
                  <ul className="space-y-1.5">
                    {debug.duzeltme_logu.map((line, i) => (
                      <li 
                        key={i} 
                        className="rounded-lg border border-amber-200/50 bg-amber-50/80 px-3 py-2 font-mono text-[11.5px] leading-relaxed text-amber-900 shadow-sm dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"
                      >
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