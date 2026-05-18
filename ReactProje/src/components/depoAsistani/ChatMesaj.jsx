import { motion as Motion } from 'framer-motion';
import { Sparkles, User, AlertTriangle } from 'lucide-react';
import TaslakKart from './TaslakKart';

/**
 * Tek bir sohbet satiri. Avatar + soft bubble formati; asistan
 * mesajinda taslak gelirse balon altina TaslakKart gomulur.
 */
export default function ChatMesaj({ message, onTaslakUndo }) {
  const { role, content, pending, taslak, debug, error } = message;
  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  return (
    <Motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className={`flex w-full gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className="shrink-0 pt-0.5">
        {isAssistant ? (
          <div className="relative">
            <div
              aria-hidden
              className="absolute inset-0 -m-0.5 rounded-2xl bg-gradient-to-br from-primary-400/40 to-accent-500/30 blur-sm"
            />
            <div className="relative inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-md shadow-primary-500/25 ring-1 ring-white/40">
              <Sparkles className="h-4 w-4" strokeWidth={2.25} aria-hidden />
            </div>
          </div>
        ) : (
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-text-tertiary/20 to-text-tertiary/5 text-text-secondary ring-1 ring-white/60">
            <User className="h-4 w-4" strokeWidth={2.25} aria-hidden />
          </div>
        )}
      </div>

      {/* Govde */}
      <div
        className={`flex min-w-0 max-w-[85%] flex-col gap-1.5 ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-text-tertiary">
          {isUser ? 'siz' : 'asistan'}
          {isAssistant && !pending && (
            <span className="ml-1.5 text-accent-600">·ai</span>
          )}
        </span>

        <div
          className={
            isUser
              ? 'rounded-3xl rounded-tr-md bg-gradient-to-br from-primary-500 to-primary-700 px-4 py-2.5 text-sm leading-relaxed text-white shadow-md shadow-primary-500/20 ring-1 ring-inset ring-white/15'
              : `rounded-3xl rounded-tl-md border bg-white/85 px-4 py-2.5 text-sm leading-relaxed text-text-primary shadow-sm backdrop-blur-sm ${
                  error
                    ? 'border-danger-500/30 bg-danger-50/60'
                    : 'border-white/70'
                }`
          }
        >
          {pending ? (
            <span className="inline-flex items-center gap-1.5 py-0.5 text-text-secondary">
              <span className="flex items-center gap-1" aria-hidden>
                <Motion.span
                  className="h-1.5 w-1.5 rounded-full bg-primary-500"
                  animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                />
                <Motion.span
                  className="h-1.5 w-1.5 rounded-full bg-primary-500"
                  animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.15 }}
                />
                <Motion.span
                  className="h-1.5 w-1.5 rounded-full bg-primary-500"
                  animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
                />
              </span>
              <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-text-tertiary">
                düşünüyor
              </span>
            </span>
          ) : (
            <div className="flex items-start gap-2">
              {error && (
                <AlertTriangle
                  className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger-500"
                  aria-hidden
                  strokeWidth={2.25}
                />
              )}
              <p className="whitespace-pre-wrap break-words">{content || '—'}</p>
            </div>
          )}
        </div>

        {/* HITL anchor — sadece asistan mesajinda taslak gelirse */}
        {!pending && taslak && (
          <div className="mt-1 w-full">
            <TaslakKart taslak={taslak} onUndo={onTaslakUndo} />
          </div>
        )}

        {/* Debug rozeti */}
        {!pending && isAssistant && debug && Object.keys(debug).length > 0 && (
          <details className="mt-0.5 w-full text-[10.5px]">
            <summary className="cursor-pointer font-mono uppercase tracking-[0.18em] text-text-tertiary transition-colors hover:text-text-secondary">
              debug
            </summary>
            <pre className="mt-1.5 overflow-x-auto rounded-xl border border-border-light bg-surface-tertiary/60 p-2.5 font-mono text-[10.5px] leading-snug text-text-secondary">
              {JSON.stringify(debug, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </Motion.div>
  );
}
