import { Briefcase, Eye, ShieldCheck } from 'lucide-react';

/**
 * Sayfanin tepesinde duran kucuk rozet: kullanicinin rolunu,
 * aktif ekrani ve varsa aktif gorevini gosterir. Yumusak gradient
 * pill tasarimi; mono-caps etiket dilini koruyor.
 */
export default function BaglamRozeti({ rol, aktifEkran, aktifGorevId }) {
  const items = [
    { icon: ShieldCheck, label: 'rol', value: rol || '—' },
    { icon: Eye, label: 'ekran', value: aktifEkran || '—' },
    {
      icon: Briefcase,
      label: 'gorev',
      value: aktifGorevId ? `#${aktifGorevId}` : 'yok',
    },
  ];

  return (
    <div
      className="flex flex-wrap items-center gap-2"
      aria-label="Aktif kullanici baglami"
    >
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.label}
            className="group inline-flex items-center gap-2 rounded-full border border-white/60 bg-white/70 px-3 py-1.5 shadow-sm backdrop-blur transition-all duration-200 hover:-translate-y-px hover:border-primary-200 hover:bg-white hover:shadow-md"
          >
            <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-primary-50 to-primary-100 ring-1 ring-inset ring-white">
              <Icon
                aria-hidden
                className="h-3 w-3 text-primary-700"
                strokeWidth={2.5}
              />
            </span>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-tertiary">
              {item.label}
            </span>
            <span className="text-xs font-semibold text-text-primary">
              {item.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
