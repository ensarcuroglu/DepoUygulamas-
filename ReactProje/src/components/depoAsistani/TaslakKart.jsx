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
  Wrench,
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
    accentBar:
      'bg-gradient-to-b from-accent-400 via-accent-500 to-accent-600',
    glow: 'shadow-accent-500/10',
    chipClass:
      'bg-gradient-to-r from-amber-50 to-amber-100/80 text-amber-900 ring-1 ring-inset ring-amber-200/70',
    dotClass: 'bg-accent-500',
  },
  ONAYLANDI: {
    label: 'ONAYLANDI',
    icon: CheckCircle2,
    accentBar:
      'bg-gradient-to-b from-emerald-400 via-success-500 to-success-600',
    glow: 'shadow-success-500/10',
    chipClass:
      'bg-gradient-to-r from-success-50 to-emerald-100/60 text-success-600 ring-1 ring-inset ring-success-500/20',
    dotClass: 'bg-success-500',
  },
  REDDEDILDI: {
    label: 'REDDEDİLDİ',
    icon: XCircle,
    accentBar:
      'bg-gradient-to-b from-danger-400 via-danger-500 to-danger-600',
    glow: 'shadow-danger-500/10',
    chipClass:
      'bg-gradient-to-r from-danger-50 to-rose-100/50 text-danger-600 ring-1 ring-inset ring-danger-500/20',
    dotClass: 'bg-danger-500',
  },
  SURESI_DOLDU: {
    label: 'SÜRESİ DOLDU',
    icon: XCircle,
    accentBar: 'bg-gradient-to-b from-zinc-300 to-zinc-400',
    glow: 'shadow-zinc-400/10',
    chipClass:
      'bg-gradient-to-r from-zinc-100 to-zinc-200/60 text-zinc-600 ring-1 ring-inset ring-zinc-300/60',
    dotClass: 'bg-zinc-400',
  },
};

/**
 * Yumusak modern HITL onay karti: sol kenarda gradient accent serit,
 * glass surface, refined status chip ve onay/red/geri al aksiyonlari.
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
      toast.success('Aksiyon onaylandı.');
    } catch (err) {
      toast.error(hataMetni(err) || 'Onaylama başarısız.');
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
      toast.error(hataMetni(err) || 'Reddetme başarısız.');
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
        toast.error('Asistan şu an başka bir yanıt hazırlıyor.');
      } else {
        toast.success('Geri alma teklifi hazırlandı.');
      }
    } catch (err) {
      toast.error(hataMetni(err) || 'Geri alma teklifi hazırlanamadı.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <Motion.div
      initial={{ opacity: 0, y: 8, scale: 0.985 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className={`relative overflow-hidden rounded-2xl border border-white/70 bg-white/85 shadow-md backdrop-blur-sm ${meta.glow}`}
      role="region"
      aria-label={`Aksiyon taslagi ${currentTaslak.tool_id}`}
    >
      {/* Accent serit */}
      <div
        aria-hidden
        className={`absolute inset-y-0 left-0 w-1.5 ${meta.accentBar}`}
      />
      {/* Hafif tepe glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-12 left-12 h-32 w-32 rounded-full bg-primary-200/30 blur-2xl"
      />

      <div className="relative px-5 py-4 pl-7">
        {/* Tepe satiri: durum chip + id */}
        <div className="flex items-center justify-between gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] ${meta.chipClass}`}
          >
            <span className="relative flex h-2 w-2">
              {isPending && (
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${meta.dotClass}`}
                />
              )}
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${meta.dotClass}`}
              />
            </span>
            <StatusIcon className="h-3 w-3" aria-hidden />
            {meta.label}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-tertiary">
            taslak · #{currentTaslak.id}
          </span>
        </div>

        {/* Alet adi */}
        <div className="mt-3.5 flex items-center gap-2">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-primary-50 to-primary-100 ring-1 ring-inset ring-white">
            <Wrench
              className="h-3 w-3 text-primary-700"
              aria-hidden
              strokeWidth={2.5}
            />
          </span>
          <div className="flex min-w-0 flex-col leading-tight">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-tertiary">
              alet
            </span>
            <span className="truncate font-mono text-sm font-semibold text-text-primary">
              {currentTaslak.tool_id}
            </span>
          </div>
        </div>

        {/* Ozet */}
        {currentTaslak.ozet && (
          <p className="mt-3.5 text-sm leading-relaxed text-text-primary">
            {currentTaslak.ozet}
          </p>
        )}

        {/* Onay sonrasi islem ozeti */}
        {isApproved && resultSummary && (
          <div className="mt-3.5 overflow-hidden rounded-xl border border-success-500/20 bg-gradient-to-r from-success-50 to-emerald-50/60 px-3.5 py-3">
            <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-success-600">
              <CheckCircle2 className="h-3 w-3" aria-hidden />
              işlem özeti
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-sm font-medium text-text-primary">
              {resultSummary.before && (
                <span className="rounded-md bg-white/70 px-2 py-0.5 font-mono text-xs ring-1 ring-inset ring-success-500/15">
                  {resultSummary.before}
                </span>
              )}
              {resultSummary.before && resultSummary.after && (
                <ArrowRight
                  className="h-3.5 w-3.5 text-success-600"
                  aria-hidden
                />
              )}
              <span className="rounded-md bg-white/70 px-2 py-0.5 font-mono text-xs ring-1 ring-inset ring-success-500/15">
                {resultSummary.after}
              </span>
              {resultSummary.suffix && (
                <span className="text-text-secondary">
                  {resultSummary.suffix}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Parametre listesi */}
        {paramsEntries.length > 0 && (
          <dl className="mt-3.5 divide-y divide-border-light rounded-xl bg-surface-secondary/50 ring-1 ring-inset ring-border-light">
            {paramsEntries.map(([k, v]) => (
              <div
                key={k}
                className="flex items-baseline justify-between gap-3 px-3 py-2 font-mono text-xs"
              >
                <dt className="text-text-tertiary">
                  <span aria-hidden className="mr-1 text-text-tertiary/70">
                    ▸
                  </span>
                  {k}
                </dt>
                <dd className="truncate text-right font-medium text-text-primary">
                  {formatValue(v)}
                </dd>
              </div>
            ))}
          </dl>
        )}

        {/* Hata mesaji */}
        {currentTaslak.hata_mesaji && (
          <p className="mt-3.5 rounded-xl border border-danger-500/30 bg-danger-50/80 px-3 py-2 font-mono text-xs leading-relaxed text-danger-600">
            {currentTaslak.hata_mesaji}
          </p>
        )}

        {/* Aksiyonlar — beklemede */}
        {isPending && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleOnayla}
              disabled={!!busy}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 px-3.5 py-2 text-xs font-bold text-white shadow-md shadow-primary-500/25 ring-1 ring-inset ring-white/15 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary-500/35 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
              aria-label="Aksiyon taslagini onayla"
            >
              {busy === 'onayla' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <Check className="h-3.5 w-3.5" aria-hidden strokeWidth={2.5} />
              )}
              Onayla
            </button>
            <button
              type="button"
              onClick={handleReddet}
              disabled={!!busy}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-border bg-white/80 px-3.5 py-2 text-xs font-semibold text-text-primary shadow-sm backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-danger-500/40 hover:bg-danger-50 hover:text-danger-600 hover:shadow-md active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-danger-500/60 focus-visible:ring-offset-2"
              aria-label="Aksiyon taslagini reddet"
            >
              {busy === 'reddet' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <X className="h-3.5 w-3.5" aria-hidden strokeWidth={2.5} />
              )}
              Reddet
            </button>
          </div>
        )}

        {/* Geri al — onaylandi */}
        {isApproved && undoPrompt && (
          <div className="mt-4 flex flex-wrap items-center gap-2.5 border-t border-border-light pt-3.5">
            <button
              type="button"
              onClick={handleGeriAl}
              disabled={!!busy || !onUndo}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-success-500/30 bg-white/80 px-3.5 py-2 text-xs font-bold text-success-700 shadow-sm backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-success-500/60 hover:bg-success-50 hover:shadow-md active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-success-500/60 focus-visible:ring-offset-2"
              aria-label="Onaylanan aksiyon icin geri alma teklifi hazirla"
            >
              {busy === 'geriAl' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              ) : (
                <RotateCcw
                  className="h-3.5 w-3.5"
                  aria-hidden
                  strokeWidth={2.5}
                />
              )}
              Geri al
            </button>
            <span className="text-xs text-text-secondary">
              Ters işlem yeni bir onay teklifi olarak açılır.
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
      suffix: 'olarak değiştirildi.',
    };
  }

  if (result.tip === 'gorev_hedef_raf_degisti') {
    return {
      before: oldRaf ? `Hedef raf: ${oldRaf}` : null,
      after: `Hedef raf: ${newRaf}`,
      suffix: 'olarak güncellendi.',
    };
  }

  return {
    before: null,
    after: 'Aksiyon onaylandı',
    suffix: '',
  };
}

function buildUndoPrompt(taslak) {
  const result = taslak?.sonuc_json;
  if (!result || typeof result !== 'object' || !result.eski_raf_kodu) {
    return null;
  }

  if (result.tip === 'palet_raf_degisti' && result.palet_no) {
    return `${result.palet_no} paletinin raf bilgisini ${result.eski_raf_kodu} yapmak için onay teklifi hazırla.`;
  }

  if (result.tip === 'gorev_hedef_raf_degisti' && result.gorev_id) {
    return `${result.gorev_id} numaralı yerleştirme görevinin hedef rafını ${result.eski_raf_kodu} yapmak için onay teklifi hazırla.`;
  }

  return null;
}
