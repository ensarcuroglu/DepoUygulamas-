import { motion as Motion } from 'framer-motion';
import {
  Sparkles,
  Clock,
  MoveRight,
  ShieldCheck,
  CalendarDays,
} from 'lucide-react';

const ORNEK_SORULAR = [
  {
    soru: 'Şu an saat kaç?',
    baslik: 'Saat sor',
    icon: Clock,
    aciklama: 'Sistem saati ve depo vardiyası.',
    accent: 'from-primary-50 to-primary-100/60 text-primary-700',
  },
  {
    soru: 'Bekleyen yerleştirme görevimi B-12-3 konumuna taşı.',
    baslik: 'Görev konumu değiştir',
    icon: MoveRight,
    aciklama: 'HITL onayı ile hedef rafı güncelle.',
    accent: 'from-accent-400/15 to-accent-500/10 text-accent-600',
  },
  {
    soru: 'Hangi yetkilere sahibim?',
    baslik: 'Yetkilerimi göster',
    icon: ShieldCheck,
    aciklama: 'Rol bazlı erişim özeti.',
    accent: 'from-success-50 to-success-500/10 text-success-600',
  },
  {
    soru: 'Bugün hangi gün?',
    baslik: 'Tarih sor',
    icon: CalendarDays,
    aciklama: 'Takvim / vardiya günü.',
    accent: 'from-primary-50 to-primary-100/60 text-primary-700',
  },
];

const itemAnim = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0 },
};

/**
 * Bos durum — kompakt hero + 2x2 oneri kart gridi. Yukseklik
 * butcesi: chat sayfasi tek viewport icinde scroll'suz oturmali.
 */
export default function BosDurum({ onOrnekSec }) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-4 px-2 py-4 text-center sm:gap-5 sm:py-6">
      {/* Hero */}
      <div className="relative">
        <Motion.div
          aria-hidden
          className="absolute inset-0 -m-4 rounded-full bg-gradient-to-br from-primary-300/40 via-primary-200/30 to-accent-400/30 blur-2xl"
          animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
        />
        <Motion.div
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="relative inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700 text-white shadow-lg shadow-primary-500/30 ring-1 ring-white/50 sm:h-14 sm:w-14"
        >
          <Sparkles className="h-5 w-5 sm:h-6 sm:w-6" strokeWidth={2} aria-hidden />
        </Motion.div>
      </div>

      <Motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: 0.08 }}
        className="max-w-xl space-y-1.5"
      >
        <h2 className="text-lg font-semibold tracking-tight sm:text-xl">
          <span className="bg-gradient-to-r from-text-primary via-primary-700 to-primary-600 bg-clip-text text-transparent">
            Depo Asistanı'na hoş geldiniz
          </span>
        </h2>
        <p className="text-[13px] leading-relaxed text-text-secondary">
          Sorunuzu doğal dilde yazın ya da örneklerden birini seçin. Önerilen her
          aksiyon{' '}
          <span className="font-semibold text-text-primary">onayınızdan</span>{' '}
          önce uygulanmaz.
        </p>
      </Motion.div>

      {/* Oneri kartlari grid */}
      <Motion.div
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.05, delayChildren: 0.15 }}
        className="grid w-full grid-cols-1 gap-2.5 sm:grid-cols-2"
      >
        {ORNEK_SORULAR.map((item) => {
          const Icon = item.icon;
          return (
            <Motion.button
              key={item.soru}
              type="button"
              variants={itemAnim}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onOrnekSec?.(item.soru)}
              className="group relative flex w-full cursor-pointer items-start gap-2.5 overflow-hidden rounded-xl border border-white/60 bg-white/80 p-3 text-left shadow-sm backdrop-blur-sm transition-all duration-300 hover:border-primary-200 hover:bg-white hover:shadow-md hover:shadow-primary-500/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
            >
              <span
                aria-hidden
                className={`pointer-events-none absolute inset-0 -z-0 bg-gradient-to-br ${item.accent} opacity-0 transition-opacity duration-300 group-hover:opacity-60`}
              />
              <span
                className={`relative z-10 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ring-1 ring-inset ring-white/60 ${item.accent}`}
              >
                <Icon className="h-3.5 w-3.5" strokeWidth={2.25} aria-hidden />
              </span>
              <span className="relative z-10 flex min-w-0 flex-col gap-0.5">
                <span className="text-[13px] font-semibold leading-tight text-text-primary">
                  {item.baslik}
                </span>
                <span className="truncate text-[11px] leading-snug text-text-secondary">
                  {item.aciklama}
                </span>
                <span className="mt-0.5 truncate font-mono text-[10px] uppercase tracking-[0.14em] text-text-tertiary">
                  "{item.soru}"
                </span>
              </span>
            </Motion.button>
          );
        })}
      </Motion.div>
    </div>
  );
}
