/**
 * Yuklenmis Excel dosyasinin meta panelini gosterir.
 * - Dosya adi (mono) + boyut (serif italic)
 * - Sayfa secici: amber underline aktif sayfayi isaretler.
 */
export default function WorkbookHeader({ workbook, activeSheet, onSheetChange }) {
  if (!workbook) return null;
  const sizeKb = (workbook.size_bytes / 1024).toFixed(1);

  return (
    <section className="border-b border-zinc-200/80 pb-5 dark:border-white/[0.06]">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="select-none font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
            dosya
          </span>
          <h2 className="truncate font-['JetBrains_Mono'] text-[13px] text-zinc-900 dark:text-zinc-100">
            {workbook.filename}
          </h2>
        </div>
        <span className="font-['Instrument_Serif'] text-[14px] italic text-zinc-400 dark:text-zinc-500">
          {sizeKb} KB — {workbook.sheets.length} sayfa
        </span>
      </div>

      {workbook.sheets.length > 1 && (
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
          {workbook.sheets.map((s) => {
            const active = s.name === activeSheet;
            return (
              <button
                key={s.name}
                type="button"
                onClick={() => onSheetChange(s.name)}
                className={`group inline-flex items-baseline gap-2 border-b py-1.5 transition ${
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
                <span className="font-['JetBrains_Mono'] text-[10.5px] tabular-nums text-zinc-400 dark:text-zinc-500">
                  {s.rows}r × {s.columns.length}s
                </span>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
