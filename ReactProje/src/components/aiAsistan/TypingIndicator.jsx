import { motion as Motion } from 'framer-motion';

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-3" aria-label="Yanıt yazılıyor">
      {[0, 1, 2].map((i) => (
        <Motion.span
          key={i}
          className="block h-2 w-2 rounded-full bg-indigo-400/70 dark:bg-indigo-300/70"
          animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
        />
      ))}
    </div>
  );
}
