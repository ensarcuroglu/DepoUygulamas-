import { useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Check, X, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import {
  useDepoAsistaniTaslakOnaylaMutation,
  useDepoAsistaniTaslakReddetMutation,
} from '../../queries/depoAsistaniQueries';
import { hataMetni } from '../../utils/hata';
import toast from 'react-hot-toast';

const STATUS_META = {
  BEKLEMEDE: {
    label: 'ONAY BEKLEMEDE',
    icon: Clock,
    barClass: 'bg-accent-500',
    chipClass: 'bg-amber-100 text-amber-900',
  },
  ONAYLANDI: {
    label: 'ONAYLANDI',
    icon: CheckCircle2,
    barClass: 'bg-success-500',
    chipClass: 'bg-success-50 text-success-600',
  },
  REDDEDILDI: {
    label: 'REDDEDILDI',
    icon: XCircle,
    barClass: 'bg-danger-500',
    chipClass: 'bg-danger-50 text-danger-600',
  },
  SURESI_DOLDU: {
    label: 'SURESI DOLDU',
    icon: XCircle,
    barClass: 'bg-zinc-400',
    chipClass: 'bg-zinc-100 text-zinc-600',
  },
};

/**
 * **DESIGN ANCHOR** — Bu uygulamadaki en akilda kalan oge.
 * Terminal-receipt formunda HITL onay karti: sol kenarda kalin accent serit,
 * mono caps durum rozeti, monospace tool_id ve params key-value listesi.
 * Onayla/Reddet aksiyonlari kart icinde gomulu.
 */
export default function TaslakKart({ taslak }) {
  const meta = STATUS_META[taslak.durum] ?? STATUS_META.BEKLEMEDE;
  const StatusIcon = meta.icon;
  const isPending = taslak.durum === 'BEKLEMEDE';

  const [busy, setBusy] = useState(null); // 'onayla' | 'reddet' | null
  const onaylaMutation = useDepoAsistaniTaslakOnaylaMutation();
  const reddetMutation = useDepoAsistaniTaslakReddetMutation();

  const handleOnayla = async () => {
    if (busy) return;
    setBusy('onayla');
    try {
      await onaylaMutation.mutateAsync({ id: taslak.id });
      toast.success('Aksiyon onaylandi.');
    } catch (err) {
      toast.error(hataMetni(err) || 'Onaylama basarisiz.');
    } finally {
      setBusy(null);
    }
  };

  const handleReddet = async () => {
    if (busy) return;
    setBusy('reddet');
    try {
      await reddetMutation.mutateAsync({ id: taslak.id });
      toast.success('Aksiyon reddedildi.');
    } catch (err) {
      toast.error(hataMetni(err) || 'Reddetme basarisiz.');
    } finally {
      setBusy(null);
    }
  };

  const paramsEntries = Object.entries(taslak.payload_json ?? {});

  return (
    <Motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden rounded-lg border border-border bg-surface shadow-sm"
      role="region"
      aria-label={`Aksiyon taslagi ${taslak.tool_id}`}
    >
      {/* Sol accent serit — anchor */}
      <div
        aria-hidden
        className={`absolute inset-y-0 left-0 w-1 ${meta.barClass}`}
      />

      <div className="px-5 py-4 pl-6">
        {/* Header satiri: durum chip + tarih */}
        <div className="flex items-center justify-between gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.16em] ${meta.chipClass}`}
          >
            <StatusIcon className="h-3 w-3" aria-hidden />
            {meta.label}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
            #{taslak.id}
          </span>
        </div>

        {/* Tool ID */}
        <div className="mt-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            alet
          </div>
          <div className="mt-0.5 font-mono text-sm font-semibold text-text-primary">
            {taslak.tool_id}
          </div>
        </div>

        {/* Ozet */}
        {taslak.ozet && (
          <p className="mt-3 text-sm leading-relaxed text-text-primary">
            {taslak.ozet}
          </p>
        )}

        {/* Params */}
        {paramsEntries.length > 0 && (
          <dl className="mt-3 space-y-1 border-t border-border-light pt-3">
            {paramsEntries.map(([k, v]) => (
              <div
                key={k}
                className="flex items-baseline justify-between gap-3 font-mono text-xs"
              >
                <dt className="text-zinc-500">
                  <span aria-hidden className="mr-1 text-zinc-400">
                    &#9656;
                  </span>
                  {k}
                </dt>
                <dd className="truncate text-right text-text-primary">
                  {formatValue(v)}
                </dd>
              </div>
            ))}
          </dl>
        )}

        {/* Hata mesaji (varsa) */}
        {taslak.hata_mesaji && (
          <p className="mt-3 rounded border border-danger-500/30 bg-danger-50 px-3 py-2 font-mono text-xs text-danger-600">
            {taslak.hata_mesaji}
          </p>
        )}

        {/* Aksiyonlar */}
        {isPending && (
          <div className="mt-4 flex items-center gap-2">
            <button
              type="button"
              onClick={handleOnayla}
              disabled={!!busy}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-md bg-primary-700 px-3 py-1.5 text-xs font-semibold text-white transition-colors duration-200 hover:bg-primary-800 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Aksiyon taslagini onayla"
            >
              {busy === 'onayla' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <Check className="h-3.5 w-3.5" aria-hidden />
              )}
              Onayla
            </button>
            <button
              type="button"
              onClick={handleReddet}
              disabled={!!busy}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-text-primary transition-colors duration-200 hover:bg-surface-tertiary disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
              aria-label="Aksiyon taslagini reddet"
            >
              {busy === 'reddet' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <X className="h-3.5 w-3.5" aria-hidden />
              )}
              Reddet
            </button>
          </div>
        )}
      </div>
    </Motion.div>
  );
}

function formatValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}
