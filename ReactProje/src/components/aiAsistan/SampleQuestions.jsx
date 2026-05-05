import { motion as Motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

const FALLBACK_SAMPLES = [
  'Aktif palet sayısı kaç?',
  'Stoğu en az olan 5 ürün',
  'Son 7 günde gelen mal kabul sayısı',
  'SKT\'si 30 günden az kalan lotlar',
  'Hangi depoda en çok aktif palet var?',
  'Bekleyen sipariş sayısı',
];

export default function SampleQuestions({ samples, onPick, disabled }) {
  const items = (samples && samples.length > 0 ? samples : FALLBACK_SAMPLES).slice(0, 6);
  return (
    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
      {items.map((q, i) => (
        <Motion.button
          key={q}
          type="button"
          disabled={disabled}
          onClick={() => onPick?.(q)}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.04, duration: 0.25, ease: 'easeOut' }}
          whileHover={{ y: -1 }}
          className="group relative overflow-hidden rounded-2xl border border-slate-200/70 bg-white/60 px-4 py-3 text-left text-[13.5px] leading-snug text-slate-700 shadow-[0_1px_0_rgba(255,255,255,0.6)_inset,0_4px_16px_-12px_rgba(15,23,42,0.25)] backdrop-blur-md transition-all hover:border-indigo-300/70 hover:bg-white/80 hover:shadow-[0_8px_24px_-12px_rgba(99,102,241,0.35)] disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:border-indigo-400/40 dark:hover:bg-white/10"
        >
          <span className="flex items-start gap-2.5">
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400 transition group-hover:text-indigo-500 dark:text-indigo-300" />
            <span className="line-clamp-2">{q}</span>
          </span>
        </Motion.button>
      ))}
    </div>
  );
}
