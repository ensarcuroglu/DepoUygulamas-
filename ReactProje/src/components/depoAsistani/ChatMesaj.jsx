import { motion as Motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import TaslakKart from './TaslakKart';

/**
 * Tek bir sohbet satiri. Sibling AiAsistan ChatMessage'in editorial
 * mono-caps role label dilini takip eder. Asistan mesajinda taslak
 * varsa bunu mesaj govdesinin altina TaslakKart olarak gomer.
 */
export default function ChatMesaj({ message }) {
  const { role, content, pending, taslak, debug } = message;
  const isUser = role === 'user';
  const isAssistant = role === 'assistant';
  const roleLabel = isUser ? 'siz' : 'asistan';

  return (
    <Motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="flex w-full flex-col gap-2"
    >
      <div
        className={`flex items-center gap-2 ${
          isUser ? 'justify-end' : 'justify-start'
        }`}
      >
        {isAssistant && (
          <span
            aria-hidden
            className="font-mono text-[11px] font-medium tracking-tight text-zinc-400"
          >
            [&nbsp;<span className="text-accent-600">ai</span>&nbsp;]
          </span>
        )}
        <span className="font-mono text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500">
          {roleLabel}
        </span>
      </div>

      <div
        className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
      >
        <div
          className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-primary-700 text-white'
              : 'border border-border bg-surface text-text-primary'
          }`}
        >
          {pending ? (
            <span className="inline-flex items-center gap-2 text-zinc-500">
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
              <span className="font-mono text-xs uppercase tracking-wider">
                dusunuyor
              </span>
            </span>
          ) : (
            <p className="whitespace-pre-wrap">{content || '—'}</p>
          )}
        </div>
      </div>

      {/* HITL anchor — sadece asistan mesajinda taslak gelirse */}
      {!pending && taslak && (
        <div className="mt-1 flex w-full justify-start">
          <div className="w-full max-w-[85%]">
            <TaslakKart taslak={taslak} />
          </div>
        </div>
      )}

      {/* Debug rozeti — gelistirici icin minik bilgi */}
      {!pending && isAssistant && debug && Object.keys(debug).length > 0 && (
        <details className="ml-1 max-w-[85%] text-[10.5px]">
          <summary className="cursor-pointer font-mono uppercase tracking-wider text-zinc-400 transition-colors hover:text-zinc-600">
            debug
          </summary>
          <pre className="mt-1 overflow-x-auto rounded bg-surface-tertiary p-2 font-mono text-[10.5px] leading-snug text-zinc-600">
            {JSON.stringify(debug, null, 2)}
          </pre>
        </details>
      )}
    </Motion.div>
  );
}
