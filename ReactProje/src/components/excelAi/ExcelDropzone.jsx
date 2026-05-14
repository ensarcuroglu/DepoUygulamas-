import { useCallback, useRef, useState } from 'react';
import { FileSpreadsheet, X } from 'lucide-react';

const ACCEPT = '.xlsx,.xlsm,.csv,.tsv';
const MAX_BYTES = 10 * 1024 * 1024;

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

export default function ExcelDropzone({ file, onFile, disabled = false }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState(null);

  const accept = useCallback(
    (selected) => {
      setError(null);
      if (!selected) return;
      if (selected.size > MAX_BYTES) {
        setError('Dosya 10 MB sinirini asiyor.');
        return;
      }
      const lower = selected.name.toLowerCase();
      if (!ACCEPT.split(',').some((ext) => lower.endsWith(ext.trim()))) {
        setError('Yalnizca .xlsx, .xlsm, .csv, .tsv kabul edilir.');
        return;
      }
      onFile(selected);
    },
    [onFile]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    if (disabled) return;
    accept(e.dataTransfer.files?.[0]);
  };

  if (file) {
    return (
      <div className="flex items-center justify-between gap-3 border border-zinc-200 bg-white px-4 py-3 dark:border-white/[0.08] dark:bg-zinc-900">
        <div className="flex min-w-0 items-center gap-3">
          <FileSpreadsheet
            className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400"
            strokeWidth={1.75}
          />
          <div className="min-w-0">
            <p className="truncate font-['JetBrains_Mono'] text-[12.5px] text-zinc-900 dark:text-zinc-100">
              {file.name}
            </p>
            <p className="mt-0.5 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
              {formatBytes(file.size)}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onFile(null)}
          disabled={disabled}
          className="rounded p-1.5 text-zinc-400 transition hover:text-zinc-900 disabled:opacity-40 dark:hover:text-zinc-100"
          aria-label="Dosyayi kaldir"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={`group relative flex w-full flex-col items-center justify-center gap-3 border border-dashed py-10 transition ${
          drag
            ? 'border-amber-500 bg-amber-50/60 dark:bg-amber-500/[0.06]'
            : 'border-zinc-300 hover:border-zinc-400 dark:border-white/10 dark:hover:border-white/20'
        } ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
      >
        <FileSpreadsheet
          className={`h-6 w-6 transition ${
            drag
              ? 'text-amber-600 dark:text-amber-400'
              : 'text-zinc-400 group-hover:text-zinc-600 dark:text-zinc-600 dark:group-hover:text-zinc-400'
          }`}
          strokeWidth={1.5}
        />
        <div className="text-center">
          <p className="font-['JetBrains_Mono'] text-[11.5px] uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
            dosyayi surukle veya tikla
          </p>
          <p className="mt-1 font-['Instrument_Serif'] text-[14.5px] italic text-zinc-400 dark:text-zinc-500">
            xlsx, xlsm, csv, tsv — en fazla 10 MB
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => accept(e.target.files?.[0])}
        />
      </button>
      {error && (
        <p className="mt-2 font-['JetBrains_Mono'] text-[11px] uppercase tracking-wider text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
