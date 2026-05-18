import { useMemo, useState } from 'react';
import { motion as Motion } from 'framer-motion';
import {
  ArrowRight,
  Check,
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  RotateCcw,
} from 'lucide-react';
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
 * Terminal-receipt formunda HITL onay karti: sol kenarda kalin accent serit,
 * mono caps durum rozeti, sonuc ozeti ve ters islem teklifi.
 */
export default function TaslakKart({ taslak, onUndo }) {
  const [updatedTaslak, setUpdatedTaslak] = useState(null);
  const [busy, setBusy] = useState(null);

  const onaylaMutation = useDepoAsistaniTaslakOnaylaMutation();
  const reddetMutation = useDepoAsistaniTaslakReddetMutation();

  const currentTaslak =
    updatedTaslak && updatedTaslak.id === taslak.id ? updatedTaslak : taslak;

  const meta = STATUS_META[currentTaslak.durum] ?? STATUS_META.BEKLEMEDE;
  const StatusIcon = meta.icon;
  const isPending = currentTaslak.durum === 'BEKLEMEDE';
  const isApproved = currentTaslak.durum === 'ONAYLANDI';
  const paramsEntries = Object.entries(currentTaslak.payload_json ?? {});

  const resultSummary = useMemo(
    () => buildResultSummary(currentTaslak),
    [currentTaslak],
  );
  const undoPrompt = useMemo(
    () => buildUndoPrompt(currentTaslak),
    [currentTaslak],
  );

  const handleOnayla = async () => {
    if (busy) return;
    setBusy('onayla');
    try {
      const updated = await onaylaMutation.mutateAsync({ id: currentTaslak.id });
      setUpdatedTaslak(updated);
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
      const updated = await reddetMutation.mutateAsync({ id: currentTaslak.id });
      setUpdatedTaslak(updated);
      toast.success('Aksiyon reddedildi.');
    } catch (err) {
      toast.error(hataMetni(err) || 'Reddetme basarisiz.');
    } finally {
      setBusy(null);
    }
  };

  const handleGeriAl = async () => {
    if (busy || !undoPrompt || !onUndo) return;
    setBusy('geriAl');
    try {
      const started = await onUndo(undoPrompt);
      if (started === false) {
        toast.error('Asistan su an baska bir yanit hazirliyor.');
      } else {
        toast.success('Geri alma teklifi hazirlandi.');
      }
    } catch (err) {
      toast.error(hataMetni(err) || 'Geri alma teklifi hazirlanamadi.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <Motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden rounded-lg border border-border bg-surface shadow-sm"
      role="region"
      aria-label={`Aksiyon taslagi ${currentTaslak.tool_id}`}
    >
      <div
        aria-hidden
        className={`absolute inset-y-0 left-0 w-1 ${meta.barClass}`}
      />

      <div className="px-5 py-4 pl-6">
        <div className="flex items-center justify-between gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.16em] ${meta.chipClass}`}
          >
            <StatusIcon className="h-3 w-3" aria-hidden />
            {meta.label}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
            #{currentTaslak.id}
          </span>
        </div>

        <div className="mt-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            alet
          </div>
          <div className="mt-0.5 font-mono text-sm font-semibold text-text-primary">
            {currentTaslak.tool_id}
          </div>
        </div>

        {currentTaslak.ozet && (
          <p className="mt-3 text-sm leading-relaxed text-text-primary">
            {currentTaslak.ozet}
          </p>
        )}

        {isApproved && resultSummary && (
          <div className="mt-3 rounded-md border border-success-500/20 bg-success-50/80 px-3 py-2.5">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-success-600">
              islem ozeti
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-1.5 text-sm font-medium text-text-primary">
              {resultSummary.before && (
                <span className="font-mono">{resultSummary.before}</span>
              )}
              {resultSummary.before && resultSummary.after && (
                <ArrowRight
                  className="h-3.5 w-3.5 text-success-600"
                  aria-hidden
                />
              )}
              <span className="font-mono">{resultSummary.after}</span>
              <span className="text-zinc-500">{resultSummary.suffix}</span>
            </div>
          </div>
        )}

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

        {currentTaslak.hata_mesaji && (
          <p className="mt-3 rounded border border-danger-500/30 bg-danger-50 px-3 py-2 font-mono text-xs text-danger-600">
            {currentTaslak.hata_mesaji}
          </p>
        )}

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

        {isApproved && undoPrompt && (
          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border-light pt-3">
            <button
              type="button"
              onClick={handleGeriAl}
              disabled={!!busy || !onUndo}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-success-500/30 bg-surface px-3 py-1.5 text-xs font-semibold text-success-700 transition-colors duration-200 hover:bg-success-50 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-success-500 focus:ring-offset-2"
              aria-label="Onaylanan aksiyon icin geri alma teklifi hazirla"
            >
              {busy === 'geriAl' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <RotateCcw className="h-3.5 w-3.5" aria-hidden />
              )}
              Geri al
            </button>
            <span className="text-xs text-zinc-500">
              Ters islem yeni bir onay teklifi olarak acilir.
            </span>
          </div>
        )}
      </div>
    </Motion.div>
  );
}

function formatValue(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function buildResultSummary(taslak) {
  const result = taslak?.sonuc_json;
  if (!result || typeof result !== 'object') return null;

  const oldRaf = result.eski_raf_kodu || result.eski_raf_id;
  const newRaf = result.yeni_raf_kodu || result.yeni_raf_id;
  if (!newRaf) return null;

  if (result.tip === 'palet_raf_degisti') {
    return {
      before: oldRaf ? `Raf: ${oldRaf}` : null,
      after: `Raf: ${newRaf}`,
      suffix: 'olarak degistirildi.',
    };
  }

  if (result.tip === 'gorev_hedef_raf_degisti') {
    return {
      before: oldRaf ? `Hedef raf: ${oldRaf}` : null,
      after: `Hedef raf: ${newRaf}`,
      suffix: 'olarak guncellendi.',
    };
  }

  return {
    before: null,
    after: 'Aksiyon onaylandi',
    suffix: '',
  };
}

function buildUndoPrompt(taslak) {
  const result = taslak?.sonuc_json;
  if (!result || typeof result !== 'object' || !result.eski_raf_kodu) {
    return null;
  }

  if (result.tip === 'palet_raf_degisti' && result.palet_no) {
    return `${result.palet_no} paletinin raf bilgisini ${result.eski_raf_kodu} yapmak icin onay teklifi hazirla.`;
  }

  if (result.tip === 'gorev_hedef_raf_degisti' && result.gorev_id) {
    return `${result.gorev_id} numarali yerlestirme gorevinin hedef rafini ${result.eski_raf_kodu} yapmak icin onay teklifi hazirla.`;
  }

  return null;
}
