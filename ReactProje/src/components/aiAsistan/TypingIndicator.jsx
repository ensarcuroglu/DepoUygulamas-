import { motion as Motion } from 'framer-motion';

/**
 * Modern AI "Düşünüyor" göstergesi.
 * Yumuşak zıplayan + parlayan 3 nokta + arka planda çok hafif aura.
 *
 * Not: Variants API yerine inline animate prop kullanıldı; build/SSR'siz
 * setuplarda bazen variants resolve edilemiyor ve animasyon hiç tetiklenmiyor.
 */
export default function TypingIndicator() {
  return (
    <div
      className="relative flex h-5 items-center gap-1.5 px-1"
      role="status"
      aria-label="Asistan düşünüyor"
    >
      {[0, 1, 2].map((i) => (
        <Motion.span
          key={i}
          className="block h-2 w-2 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 shadow-[0_0_8px_rgba(99,102,241,0.45)]"
          initial={{ y: 0, opacity: 0.5, scale: 0.9 }}
          animate={{ y: [0, -5, 0], opacity: [0.5, 1, 0.5], scale: [0.9, 1.1, 0.9] }}
          transition={{
            duration: 1.15,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: i * 0.15,
          }}
        />
      ))}

      <Motion.span
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 rounded-full bg-indigo-400/10 blur-xl dark:bg-indigo-300/15"
        initial={{ opacity: 0.3 }}
        animate={{ opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut' }}
      />
    </div>
  );
}
