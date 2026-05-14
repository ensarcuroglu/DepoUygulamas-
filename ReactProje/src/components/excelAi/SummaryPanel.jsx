/**
 * pandas df.describe() + dtypes ozetini editorial mono ile sunar.
 * Tabular numerals + hairline gridlines.
 */
const STAT_LABELS = {
  count: 'sayim',
  unique: 'benzersiz',
  top: 'en sik',
  freq: 'frekans',
  mean: 'ortalama',
  std: 'std sapma',
  min: 'min',
  '25%': 'q1',
  '50%': 'medyan',
  '75%': 'q3',
  max: 'max',
};

function formatCell(v) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'number') {
    if (Number.isInteger(v)) return v.toLocaleString('tr-TR');
    return v.toLocaleString('tr-TR', { maximumFractionDigits: 3 });
  }
  return String(v);
}

export default function SummaryPanel({ summary }) {
  if (!summary) return null;
  const cols = summary.columns;
  const stats = Object.keys(summary.describe[cols[0]] ?? {});

  return (
    <section className="space-y-6">
      {/* Sutun seması */}
      <div>
        <h3 className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
          şema — {cols.length} sütun, {summary.rows.toLocaleString('tr-TR')} satır
        </h3>
        <div className="mt-3 grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2 lg:grid-cols-3">
          {cols.map((c) => (
            <div
              key={c}
              className="flex items-baseline justify-between gap-3 border-b border-dashed border-zinc-200 py-1.5 dark:border-white/[0.06]"
            >
              <span className="truncate font-['JetBrains_Mono'] text-[12px] text-zinc-900 dark:text-zinc-100">
                {c}
              </span>
              <span className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
                {summary.dtypes[c]}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* describe() tablosu */}
      <div>
        <h3 className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
          istatistik
        </h3>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-zinc-300 dark:border-white/10">
                <th className="py-2 pr-4 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                  ölçüm
                </th>
                {cols.map((c) => (
                  <th
                    key={c}
                    className="border-l border-zinc-200/80 px-3 py-2 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:border-white/[0.06] dark:text-zinc-400"
                  >
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {stats.map((stat) => (
                <tr
                  key={stat}
                  className="border-b border-zinc-100 last:border-b-0 dark:border-white/[0.04]"
                >
                  <td className="py-1.5 pr-4 font-['JetBrains_Mono'] text-[11.5px] text-zinc-500 dark:text-zinc-400">
                    {STAT_LABELS[stat] ?? stat}
                  </td>
                  {cols.map((c) => (
                    <td
                      key={c}
                      className="border-l border-zinc-200/80 px-3 py-1.5 font-['JetBrains_Mono'] text-[11.5px] tabular-nums text-zinc-900 dark:border-white/[0.06] dark:text-zinc-100"
                    >
                      {formatCell(summary.describe[c]?.[stat])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* head ornegi */}
      {summary.head?.length > 0 && (
        <div>
          <h3 className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
            ilk {summary.head.length} satır
          </h3>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-zinc-300 dark:border-white/10">
                  {cols.map((c) => (
                    <th
                      key={c}
                      className="border-l border-zinc-200/80 px-3 py-2 first:border-l-0 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:border-white/[0.06] dark:text-zinc-400"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {summary.head.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-zinc-100 last:border-b-0 dark:border-white/[0.04]"
                  >
                    {cols.map((c) => (
                      <td
                        key={c}
                        className="border-l border-zinc-200/80 px-3 py-1.5 first:border-l-0 font-['JetBrains_Mono'] text-[11.5px] tabular-nums text-zinc-900 dark:border-white/[0.06] dark:text-zinc-100"
                      >
                        {formatCell(row[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
