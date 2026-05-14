import { ArrowRight, AlertTriangle, Check } from 'lucide-react';

/**
 * Sutun esleme tablosu: kaynak -> hedef + confidence bar.
 * Mono tabular-numerals; amber bar = guven seviyesi.
 */
function ConfidenceBar({ value }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="h-px w-16 bg-zinc-200 dark:bg-white/[0.08]">
        <div
          className="h-px bg-amber-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-['JetBrains_Mono'] text-[10.5px] tabular-nums text-zinc-400 dark:text-zinc-500">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

export default function MappingPanel({ result }) {
  if (!result) return null;
  const { mappings, missing_required_fields: missing, target_schema } = result;

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-[0.22em] text-zinc-400 dark:text-zinc-500">
          esleme — hedef: {target_schema}
        </h3>
        <span className="font-['Instrument_Serif'] text-[14px] italic text-zinc-400 dark:text-zinc-500">
          {mappings.filter((m) => m.target_field).length}/{mappings.length} kaynak sütun eşleşti
        </span>
      </div>

      {missing.length > 0 && (
        <div className="flex items-start gap-2 border-l-2 border-red-500 bg-red-50/50 py-2 pl-3 pr-4 dark:bg-red-500/[0.06]">
          <AlertTriangle
            className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-600 dark:text-red-400"
            strokeWidth={2}
          />
          <p className="font-['JetBrains_Mono'] text-[11.5px] text-red-700 dark:text-red-300">
            eksik zorunlu alan:{' '}
            <span className="font-semibold">{missing.join(', ')}</span>
          </p>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-zinc-300 dark:border-white/10">
              <th className="py-2 pr-4 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                kaynak
              </th>
              <th className="py-2 pr-4 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                hedef
              </th>
              <th className="py-2 pr-4 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                güven
              </th>
              <th className="py-2 font-['JetBrains_Mono'] text-[10.5px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                alternatifler
              </th>
            </tr>
          </thead>
          <tbody>
            {mappings.map((m) => (
              <tr
                key={m.source_column}
                className="border-b border-zinc-100 last:border-b-0 dark:border-white/[0.04]"
              >
                <td className="py-2 pr-4 font-['JetBrains_Mono'] text-[12px] text-zinc-900 dark:text-zinc-100">
                  {m.source_column}
                </td>
                <td className="py-2 pr-4">
                  {m.target_field ? (
                    <span className="inline-flex items-center gap-1.5 font-['JetBrains_Mono'] text-[12px] text-amber-700 dark:text-amber-300">
                      <ArrowRight className="h-3 w-3" strokeWidth={2} />
                      {m.target_field}
                      <Check className="h-3 w-3 opacity-50" strokeWidth={2.5} />
                    </span>
                  ) : (
                    <span className="font-['JetBrains_Mono'] text-[12px] italic text-zinc-400 dark:text-zinc-600">
                      eşleşme yok
                    </span>
                  )}
                </td>
                <td className="py-2 pr-4">
                  <ConfidenceBar value={m.confidence} />
                </td>
                <td className="py-2">
                  {m.candidates.length > 1 ? (
                    <span className="font-['JetBrains_Mono'] text-[11px] text-zinc-500 dark:text-zinc-400">
                      {m.candidates
                        .slice(1)
                        .map((c) => `${c.target_field} (${(c.score * 100).toFixed(0)}%)`)
                        .join(' · ')}
                    </span>
                  ) : (
                    <span className="font-['JetBrains_Mono'] text-[11px] text-zinc-300 dark:text-zinc-700">
                      —
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
