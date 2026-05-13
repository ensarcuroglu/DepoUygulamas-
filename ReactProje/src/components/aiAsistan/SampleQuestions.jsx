import { motion as Motion } from 'framer-motion';
import { ArrowUpRight } from 'lucide-react';

const FALLBACK_SAMPLES = [
  'Aktif palet sayısı kaç?',
  'Stoğu en az olan 5 ürün',
  'Son 7 günde gelen mal kabul sayısı',
  'SKT\'si 30 günden az kalan lotlar',
  'Hangi depoda en çok aktif palet var?',
  'Bekleyen sipariş sayısı',
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.04 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 6 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] },
  },
};

function splitPrefix(q) {
  const m = q.match(/^(\/[a-z]+)\s+(.*)$/i);
  return m ? { prefix: m[1], rest: m[2] } : { prefix: null, rest: q };
}

export default function SampleQuestions({ samples, onPick, disabled }) {
  const items = (samples && samples.length > 0 ? samples : FALLBACK_SAMPLES).slice(0, 6);

  return (
    <Motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="grid w-full grid-cols-1 gap-px overflow-hidden rounded-xl border border-zinc-200 bg-zinc-200/80 dark:border-white/[0.07] dark:bg-white/[0.06] sm:grid-cols-2"
    >
      {items.map((q) => {
        const { prefix, rest } = splitPrefix(q);
        return (
          <Motion.button
            key={q}
            variants={itemVariants}
            type="button"
            disabled={disabled}
            onClick={() => onPick?.(q)}
            className="group relative flex items-center justify-between gap-3 bg-white px-4 py-3.5 text-left transition-colors duration-200 hover:bg-amber-50/60 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-zinc-900 dark:hover:bg-amber-400/[0.06] sm:px-5 sm:py-4"
          >
            <span className="flex flex-1 items-baseline gap-2 leading-snug">
              {prefix && (
                <span className="shrink-0 rounded bg-amber-100/80 px-1.5 py-0.5 font-['JetBrains_Mono'] text-[11.5px] font-medium text-amber-800 dark:bg-amber-400/15 dark:text-amber-300">
                  {prefix}
                </span>
              )}
              <span className="text-[14px] text-zinc-700 transition-colors group-hover:text-zinc-900 dark:text-zinc-300 dark:group-hover:text-zinc-100 sm:text-[14.5px]">
                {rest}
              </span>
            </span>
            <ArrowUpRight
              className="h-4 w-4 shrink-0 text-zinc-300 transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-amber-600 dark:text-zinc-600 dark:group-hover:text-amber-400"
              strokeWidth={1.75}
            />
          </Motion.button>
        );
      })}
    </Motion.div>
  );
}
