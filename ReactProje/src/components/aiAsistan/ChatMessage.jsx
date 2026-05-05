import { useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Sparkles, User, Copy, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import MessageDetailPanel from './MessageDetailPanel';
import TypingIndicator from './TypingIndicator';

export default function ChatMessage({ message }) {
  const { role, content, pending, error, uretilenSql, debug } = message;
  const [copied, setCopied] = useState(false);

  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  const handleCopy = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast.success('Mesaj kopyalandı');
      setTimeout(() => setCopied(false), 1600);
    } catch {
      toast.error('Kopyalanamadı');
    }
  };

  return (
    <Motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut' }}
      className={`flex w-full gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {isAssistant && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/40 bg-gradient-to-br from-indigo-500/90 via-violet-500/90 to-fuchsia-500/90 text-white shadow-[0_4px_16px_-6px_rgba(99,102,241,0.6)]">
          <Sparkles className="h-4 w-4" />
        </div>
      )}

      <div className={`flex max-w-[85%] flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={[
            'group relative rounded-2xl px-4 py-2.5 text-[14.5px] leading-relaxed shadow-[0_1px_0_rgba(255,255,255,0.6)_inset,0_8px_28px_-18px_rgba(15,23,42,0.25)] backdrop-blur-md',
            isUser
              ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white'
              : error
                ? 'border border-rose-200/70 bg-rose-50/80 text-rose-900 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200'
                : 'border border-slate-200/70 bg-white/70 text-slate-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-100',
          ].join(' ')}
        >
          {pending ? (
            <TypingIndicator />
          ) : error ? (
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span className="whitespace-pre-wrap">{content}</span>
            </div>
          ) : (
            <span className="whitespace-pre-wrap">{content}</span>
          )}

          {isAssistant && !pending && !error && (
            <button
              type="button"
              onClick={handleCopy}
              aria-label="Kopyala"
              className="absolute -bottom-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200/70 bg-white text-slate-500 opacity-0 shadow-sm transition-all hover:text-slate-800 group-hover:opacity-100 dark:border-white/10 dark:bg-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </button>
          )}
        </div>

        {isAssistant && !pending && !error && (uretilenSql || debug?.rows?.length > 0) && (
          <MessageDetailPanel uretilenSql={uretilenSql} debug={debug} />
        )}
      </div>

      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-slate-200/70 bg-white/70 text-slate-600 backdrop-blur dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
          <User className="h-4 w-4" />
        </div>
      )}
    </Motion.div>
  );
}
