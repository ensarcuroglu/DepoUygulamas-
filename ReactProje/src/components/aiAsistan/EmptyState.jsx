import { motion as Motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import SampleQuestions from './SampleQuestions';

export default function EmptyState({ samples, onPick, disabled }) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6 px-4 py-8 text-center sm:gap-8 sm:py-12"
    >
      <Motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1, ease: 'easeOut' }}
        className="group relative"
      >
        {/* Yavaşça dönen AI Aurası */}
        <div className="absolute -inset-4 -z-10 animate-[spin_8s_linear_infinite] rounded-full bg-gradient-to-r from-indigo-500/20 via-fuchsia-500/20 to-cyan-500/20 blur-2xl transition-opacity duration-700 group-hover:opacity-100 dark:from-indigo-500/30 dark:via-fuchsia-500/30 dark:to-cyan-500/30 sm:-inset-6" />
        
        {/* Sabit Pulse Efekti */}
        <div className="absolute inset-0 -z-10 animate-pulse rounded-full bg-indigo-400/20 blur-xl dark:bg-indigo-500/30" />
        
        {/* İkon Konteyneri */}
        <div className="flex h-16 w-16 items-center justify-center rounded-[1.25rem] border border-white/50 bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 text-white shadow-[0_8px_32px_-8px_rgba(99,102,241,0.6)] backdrop-blur-md transition-transform duration-300 hover:scale-105 sm:h-20 sm:w-20 sm:rounded-[1.5rem]">
          <Sparkles className="h-7 w-7 sm:h-9 sm:w-9" strokeWidth={1.5} />
        </div>
      </Motion.div>

      <div className="space-y-3 px-2">
        <h2 className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent dark:from-white dark:via-slate-200 dark:to-slate-400 sm:text-3xl">
          Nasıl yardımcı olabilirim?
        </h2>
        <p className="mx-auto max-w-md text-[14px] leading-relaxed text-slate-500 dark:text-slate-400 sm:text-[15px]">
          Stok, palet, irsaliye, sipariş ve sevkiyat verileriniz hakkında doğal dilde sorular sorun. Anında <span className="font-medium text-indigo-500 dark:text-indigo-400">SQL üretip</span> cevaplayayım.
        </p>
      </div>

      <div className="mt-2 w-full sm:mt-4">
        <SampleQuestions samples={samples} onPick={onPick} disabled={disabled} />
      </div>
    </Motion.div>
  );
}