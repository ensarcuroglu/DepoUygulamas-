import { motion as Motion } from 'framer-motion';
import SampleQuestions from './SampleQuestions';

export default function EmptyState({ samples, onPick, disabled }) {
  return (
    <Motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
      className="mx-auto flex w-full max-w-2xl flex-col gap-10 py-12 sm:py-16"
    >
      <div className="flex flex-col gap-3">
        <span className="font-['JetBrains_Mono'] text-[11px] font-medium uppercase tracking-[0.18em] text-amber-600 dark:text-amber-400">
          {/* Editorial role label — differentiation anchor */}
          asistan / hazır
        </span>
        <h2 className="text-[34px] font-semibold leading-[1.05] tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-[44px]">
          Bir soru sor.{' '}
          <span className="font-['Instrument_Serif'] text-[40px] italic font-normal text-zinc-500 dark:text-zinc-400 sm:text-[50px]">
            yanıt veriyim.
          </span>
        </h2>
        <p className="max-w-xl text-[14.5px] leading-relaxed text-zinc-600 dark:text-zinc-400 sm:text-[15.5px]">
          Stok, palet, irsaliye, sipariş ve sevkiyat hakkında doğal dilde sor;{' '}
          <span className="font-['JetBrains_Mono'] text-[13px] text-zinc-800 dark:text-zinc-200">SQL</span>{' '}
          üretip cevaplayım. Dokümana sormak için{' '}
          <span className="rounded bg-amber-100/70 px-1.5 py-0.5 font-['JetBrains_Mono'] text-[12.5px] font-medium text-amber-800 dark:bg-amber-400/15 dark:text-amber-300">
            /docs
          </span>{' '}
          önekini kullan.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-500">
            örnek sorular
          </span>
          <span className="h-px flex-1 bg-zinc-200 dark:bg-white/[0.08]" />
        </div>
        <SampleQuestions samples={samples} onPick={onPick} disabled={disabled} />
      </div>
    </Motion.div>
  );
}
