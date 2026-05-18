import { Briefcase, Eye, ShieldCheck } from 'lucide-react';

/**
 * Sayfanin tepesinde duran kucuk rozet: kullanicinin rolunu,
 * aktif ekrani ve varsa aktif gorevini gosterir. Editorial sade
 * mono-caps tipografi ile sibling AI sayfalarinin diline uyumlu.
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
      className="flex flex-wrap items-center gap-x-3 gap-y-2"
      aria-label="Aktif kullanici baglami"
    >
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.label}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-secondary px-3 py-1"
          >
            <Icon
              aria-hidden
              className="h-3.5 w-3.5 text-primary-700"
              strokeWidth={2.25}
            />
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              {item.label}
            </span>
            <span className="text-xs font-medium text-text-primary">
              {item.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
