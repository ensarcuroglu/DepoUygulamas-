import { motion as Motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import SampleQuestions from './SampleQuestions';

export default function EmptyState({ samples, onPick, disabled }) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="mx-auto flex w-full max-w-2xl flex-col items-center gap-7 px-2 py-10 text-center"
    >
      <Motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.05 }}
        className="relative"
      >
        <div className="absolute inset-0 -z-10 animate-pulse rounded-full bg-indigo-400/20 blur-2xl dark:bg-indigo-500/30" />
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/40 bg-gradient-to-br from-indigo-500/90 via-violet-500/90 to-fuchsia-500/90 text-white shadow-[0_10px_30px_-10px_rgba(99,102,241,0.6)]">
          <Sparkles className="h-6 w-6" />
        </div>
      </Motion.div>

      <div className="space-y-2">
        <h2 className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-600 bg-clip-text text-2xl font-semibold tracking-tight text-transparent dark:from-white dark:via-slate-100 dark:to-slate-300">
          AI Asistan'a soru sorun
        </h2>
        <p className="max-w-md text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          Stok, palet, irsaliye, sipariş ve sevkiyat verileriniz hakkında doğal dilde
          soru sorun. Anında SQL üretip cevaplar.
        </p>
      </div>

      <div className="w-full">
        <SampleQuestions samples={samples} onPick={onPick} disabled={disabled} />
      </div>
    </Motion.div>
  );
}
