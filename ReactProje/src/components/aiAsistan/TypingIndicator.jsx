import { motion as Motion } from 'framer-motion';

/**
 * Modern AI "Düşünüyor" göstergesi.
 * Pürüzsüz zıplayan + parlayan 3 nokta + arka planda nefes alan aura.
 */
export default function TypingIndicator() {
  return (
    <div
      className="relative flex h-6 items-center justify-center gap-1.5 px-2"
      role="status"
      aria-label="Asistan düşünüyor"
    >
      {[0, 1, 2].map((i) => (
        <Motion.span
          key={i}
          className="block h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)] dark:bg-indigo-400 sm:h-2.5 sm:w-2.5"
          initial={{ y: 0, opacity: 0.3, scale: 0.8 }}
          animate={{ 
            y: [0, -6, 0], 
            opacity: [0.3, 1, 0.3], 
            scale: [0.8, 1.1, 0.8] 
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            ease: [0.45, 0, 0.55, 1], // Daha organik zıplama eğrisi
            delay: i * 0.2, // Gecikme ile dalga efekti
          }}
        />
      ))}

      {/* Nefes alan aura arka plan */}
      <Motion.span
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 rounded-full bg-indigo-400/20 blur-xl dark:bg-indigo-400/20"
        initial={{ opacity: 0.2, scale: 0.8 }}
        animate={{ opacity: [0.2, 0.6, 0.2], scale: [0.8, 1.2, 0.8] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
      />
    </div>
  );
}