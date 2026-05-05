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

// Stagger (Ardışık Yükleme) Varyantları
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.98 },
  show: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { type: 'spring', stiffness: 200, damping: 20 } 
  },
};

export default function SampleQuestions({ samples, onPick, disabled }) {
  const items = (samples && samples.length > 0 ? samples : FALLBACK_SAMPLES).slice(0, 6);
  
  return (
    <Motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4"
    >
      {items.map((q) => (
        <Motion.button
          key={q}
          variants={itemVariants}
          type="button"
          disabled={disabled}
          onClick={() => onPick?.(q)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="group relative overflow-hidden rounded-[1.25rem] border border-slate-200/80 bg-white/70 px-4 py-3.5 text-left text-[14px] leading-snug text-slate-700 shadow-[0_2px_10px_-4px_rgba(15,23,42,0.06),0_1px_0_rgba(255,255,255,0.7)_inset] backdrop-blur-xl transition-all duration-300 hover:border-indigo-300 hover:bg-white hover:shadow-[0_8px_24px_-10px_rgba(99,102,241,0.25)] disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-slate-800/60 dark:text-slate-200 dark:hover:border-indigo-400/40 dark:hover:bg-slate-800/90 sm:px-5 sm:py-4"
        >
          {/* Hover parlaması */}
          <div className="absolute inset-0 -z-10 translate-y-[100%] bg-gradient-to-t from-indigo-50/50 to-transparent transition-transform duration-500 group-hover:translate-y-0 dark:from-indigo-500/10" />
          
          <span className="flex items-start gap-3">
            <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400 transition-colors duration-300 group-hover:text-indigo-600 dark:text-indigo-400 dark:group-hover:text-indigo-300 sm:h-4.5 sm:w-4.5" strokeWidth={1.5} />
            <span className="line-clamp-2">{q}</span>
          </span>
        </Motion.button>
      ))}
    </Motion.div>
  );
}