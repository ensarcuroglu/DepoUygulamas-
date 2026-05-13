import { useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Copy, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import MarkdownContent from './MarkdownContent';
import MessageDetailPanel from './MessageDetailPanel';
import TypingIndicator from './TypingIndicator';

export default function ChatMessage({ message }) {
  const { role, content, pending, error, uretilenSql, debug, route, sources } = message;
  const [copied, setCopied] = useState(false);

  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  const handleCopy = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast.success('Mesaj kopyalandı');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Kopyalanamadı');
    }
  };

  // ROLE LABEL — micro-typography, mono caps. Differentiation anchor.
  const roleLabel = isUser ? 'siz' : 'asistan';

  return (
    <Motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="group/msg flex w-full flex-col gap-2"
    >
      {/* Role label */}
      <div className={`flex items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {isAssistant && (
          <span aria-hidden className="font-['JetBrains_Mono'] text-[11px] font-medium tracking-tight text-zinc-400 dark:text-zinc-600">
            [&nbsp;<span className="text-amber-600 dark:text-amber-400">ai</span>&nbsp;]
          </span>
        )}
        <span className="font-['JetBrains_Mono'] text-[10.5px] font-medium uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-500">
          {roleLabel}
        </span>
        {isAssistant && route === 'docs' && (
          <span className="rounded bg-amber-100/80 px-1.5 py-0.5 font-['JetBrains_Mono'] text-[10px] font-medium uppercase tracking-wider text-amber-800 dark:bg-amber-400/15 dark:text-amber-300">
            docs
          </span>
        )}
        {isAssistant && route === 'sql' && (
          <span className="rounded bg-zinc-100 px-1.5 py-0.5 font-['JetBrains_Mono'] text-[10px] font-medium uppercase tracking-wider text-zinc-600 dark:bg-white/[0.08] dark:text-zinc-400">
            sql
          </span>
        )}
      </div>

      {/* Body — user: right-aligned compact block; assistant: full-width prose with spine rule */}
      {isUser ? (
        <div className="flex justify-end">
          <div className="relative max-w-[88%] rounded-2xl rounded-tr-md border border-zinc-900/90 bg-zinc-900 px-4 py-3 text-[15px] leading-relaxed text-zinc-50 shadow-sm dark:border-white/[0.08] dark:bg-zinc-100 dark:text-zinc-900 sm:max-w-[78%] sm:px-5 sm:py-3.5">
            <span className="whitespace-pre-wrap">{content}</span>
          </div>
        </div>
      ) : (
        <div className="group/asst relative pl-4 sm:pl-5">
          {/* Spine rule — left vertical hairline marking assistant prose */}
          <span
            aria-hidden
            className={[
              'absolute left-0 top-1 w-px bg-gradient-to-b',
              error
                ? 'bottom-1 from-rose-400/70 via-rose-300/40 to-transparent dark:from-rose-400/60'
                : pending
                ? 'bottom-1 from-amber-500/80 via-amber-400/50 to-transparent dark:from-amber-400/80'
                : 'bottom-1 from-zinc-300 via-zinc-200 to-transparent dark:from-white/20 dark:via-white/10',
            ].join(' ')}
          />

          <div
            className={[
              'text-[15px] leading-relaxed transition-colors',
              error
                ? 'text-rose-700 dark:text-rose-300'
                : 'text-zinc-800 dark:text-zinc-100',
            ].join(' ')}
          >
            {pending ? (
              <TypingIndicator />
            ) : error ? (
              <div className="flex items-start gap-2.5">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
                <span className="whitespace-pre-wrap">{content}</span>
              </div>
            ) : route === 'docs' ? (
              <MarkdownContent content={content} />
            ) : (
              <span className="whitespace-pre-wrap">{content}</span>
            )}
          </div>

          {/* Tools row */}
          {!pending && !error && (
            <div className="mt-3 flex items-center gap-2 opacity-0 transition-opacity duration-200 group-hover/asst:opacity-100 focus-within:opacity-100">
              <button
                type="button"
                onClick={handleCopy}
                aria-label="Kopyala"
                className="inline-flex h-7 items-center gap-1.5 rounded-md border border-zinc-200 bg-white px-2 font-['JetBrains_Mono'] text-[11px] font-medium text-zinc-500 transition hover:border-amber-400 hover:text-amber-700 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-amber-400/40 dark:hover:text-amber-300"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-500" strokeWidth={2.5} />
                    <span>kopyalandı</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" strokeWidth={2} />
                    <span>kopyala</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Optional detail panel */}
          {!pending && !error && (uretilenSql || debug?.rows?.length > 0 || sources?.length > 0) && (
            <div className="mt-3">
              <MessageDetailPanel
                uretilenSql={uretilenSql}
                debug={debug}
                route={route}
                sources={sources}
              />
            </div>
          )}
        </div>
      )}
    </Motion.div>
  );
}
