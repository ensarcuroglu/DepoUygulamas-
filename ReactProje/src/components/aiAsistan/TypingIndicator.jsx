import { motion as Motion } from 'framer-motion';

export default function TypingIndicator() {
  return (
    <span
      role="status"
      aria-label="Asistan düşünüyor"
      className="inline-flex items-center gap-2 font-['JetBrains_Mono'] text-[12.5px] tracking-tight text-zinc-500 dark:text-zinc-400"
    >
      <span className="inline-flex items-center gap-0.5">
        {[0, 1, 2].map((i) => (
          <Motion.span
            key={i}
            className="block h-1 w-1 rounded-full bg-amber-500 dark:bg-amber-400"
            initial={{ opacity: 0.25 }}
            animate={{ opacity: [0.25, 1, 0.25] }}
            transition={{
              duration: 1.1,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: i * 0.18,
            }}
          />
        ))}
      </span>
      <span>düşünüyor</span>
    </span>
  );
}
