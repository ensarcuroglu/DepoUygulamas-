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
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Kopyalanamadı');
    }
  };

  return (
    <Motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={`flex w-full gap-3 sm:gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* Asistan Avatarı */}
      {isAssistant && (
        <div className="relative mt-1 shrink-0">
          {pending && (
            <Motion.span
              aria-hidden
              className="absolute -inset-2 rounded-full bg-gradient-to-br from-indigo-400/40 via-violet-400/40 to-fuchsia-400/40 blur-lg dark:from-indigo-500/30 dark:via-fuchsia-500/30"
              animate={{ opacity: [0.4, 0.8, 0.4], scale: [0.9, 1.15, 0.9] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            />
          )}
          <div className="relative flex h-8 w-8 items-center justify-center rounded-[0.85rem] border border-white/50 bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 text-white shadow-[0_4px_16px_-4px_rgba(99,102,241,0.5)] sm:h-9 sm:w-9 sm:rounded-xl">
            <Sparkles className="h-4 w-4 sm:h-4.5 sm:w-4.5" strokeWidth={1.5} />
          </div>
        </div>
      )}

      {/* Mesaj İçeriği */}
      <div className={`flex max-w-[88%] flex-col sm:max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={[
            'group relative text-[14.5px] leading-relaxed transition-all duration-300 sm:text-[15px]',
            // Asimetrik Köşe Yuvarlamaları (Yön hissiyatı)
            isUser ? 'rounded-[1.5rem] rounded-br-[0.35rem]' : 'rounded-[1.5rem] rounded-bl-[0.35rem]',
            
            pending
              ? 'inline-flex min-h-[44px] min-w-[72px] items-center border border-slate-200/60 bg-white/60 px-4 py-2.5 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-slate-800/50'
              : 'px-4 py-3 sm:px-5 sm:py-3.5',
              
            !pending && (isUser
              ? 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-[0_4px_20px_-8px_rgba(99,102,241,0.6)]'
              : error
                ? 'border border-rose-200/70 bg-rose-50/90 text-rose-800 shadow-sm backdrop-blur-md dark:border-rose-400/20 dark:bg-rose-900/20 dark:text-rose-200'
                : 'border border-slate-200/80 bg-white/80 text-slate-800 shadow-[0_2px_12px_-4px_rgba(15,23,42,0.06),0_1px_0_rgba(255,255,255,0.8)_inset] backdrop-blur-xl dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-100 dark:shadow-[0_1px_0_rgba(255,255,255,0.05)_inset]'),
          ].filter(Boolean).join(' ')}
        >
          {pending ? (
            <TypingIndicator />
          ) : error ? (
            <div className="flex items-start gap-2.5">
              <AlertCircle className="mt-0.5 h-4.5 w-4.5 shrink-0 text-rose-500 dark:text-rose-400" />
              <span className="whitespace-pre-wrap">{content}</span>
            </div>
          ) : (
            <span className="whitespace-pre-wrap">{content}</span>
          )}

          {/* Kopyalama Butonu */}
          {isAssistant && !pending && !error && (
            <button
              type="button"
              onClick={handleCopy}
              aria-label="Kopyala"
              className="absolute -bottom-3 -right-3 flex h-8 w-8 items-center justify-center rounded-full border border-slate-200/80 bg-white text-slate-400 opacity-0 shadow-md transition-all duration-200 hover:scale-105 hover:text-slate-800 focus:opacity-100 group-hover:opacity-100 dark:border-white/10 dark:bg-slate-700 dark:text-slate-300 dark:hover:text-white sm:h-7 sm:w-7 md:opacity-0"
            >
              <Motion.div
                initial={false}
                animate={{ scale: copied ? 1.1 : 1 }}
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" strokeWidth={2.5} /> : <Copy className="h-3.5 w-3.5" />}
              </Motion.div>
            </button>
          )}
        </div>

        {/* Opsiyonel: Üretilen SQL Paneli */}
        {isAssistant && !pending && !error && (uretilenSql || debug?.rows?.length > 0) && (
          <div className="mt-2 w-full pl-1">
            <MessageDetailPanel uretilenSql={uretilenSql} debug={debug} />
          </div>
        )}
      </div>

      {/* Kullanıcı Avatarı */}
      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-[0.85rem] border border-indigo-200/50 bg-indigo-50/50 text-indigo-600 shadow-sm backdrop-blur-md dark:border-indigo-400/20 dark:bg-indigo-400/10 dark:text-indigo-300 sm:h-9 sm:w-9 sm:rounded-xl">
          <User className="h-4 w-4 sm:h-4.5 sm:w-4.5" strokeWidth={1.5} />
        </div>
      )}
    </Motion.div>
  );
}