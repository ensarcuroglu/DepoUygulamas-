import { motion as Motion } from 'framer-motion';

/**
 * Agent cevap blogu: editorial italik soru + mono govde.
 */
export default function AnswerPanel({ question, answer }) {
  if (!question && !answer) return null;
  return (
    <Motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="relative border-l-2 border-amber-500 pl-5"
    >
      {question && (
        <p className="font-['Instrument_Serif'] text-[20px] italic leading-snug text-zinc-700 dark:text-zinc-200">
          “{question}”
        </p>
      )}
      {answer && (
        <p className="mt-3 whitespace-pre-wrap font-['JetBrains_Mono'] text-[13px] leading-relaxed text-zinc-900 dark:text-zinc-100">
          {answer}
        </p>
      )}
    </Motion.section>
  );
}
