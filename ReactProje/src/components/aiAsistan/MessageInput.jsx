import { useEffect, useRef } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';

export default function MessageInput({ value, onChange, onSubmit, disabled, placeholder }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit?.();
    }
  };

  const canSend = !disabled && value.trim().length > 0;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (canSend) onSubmit?.();
      }}
      className="relative w-full"
    >
      <div
        className={[
          'group relative flex w-full items-end gap-2 rounded-3xl border border-slate-200/80 bg-white/70 p-2 pl-5 pr-2 shadow-[0_1px_0_rgba(255,255,255,0.6)_inset,0_10px_40px_-20px_rgba(15,23,42,0.25)] backdrop-blur-xl transition-all',
          'focus-within:border-indigo-400/60 focus-within:shadow-[0_1px_0_rgba(255,255,255,0.7)_inset,0_18px_60px_-24px_rgba(99,102,241,0.45)]',
          'dark:border-white/10 dark:bg-white/5 dark:focus-within:border-indigo-400/40',
        ].join(' ')}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={disabled}
          placeholder={placeholder ?? 'Bir soru yazın… (Enter ile gönder, Shift+Enter satır)'}
          className="min-h-[36px] flex-1 resize-none bg-transparent py-2 text-[15px] leading-relaxed text-slate-800 placeholder-slate-400 outline-none disabled:opacity-60 dark:text-slate-100 dark:placeholder-slate-500"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Gönder"
          className={[
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl transition-all',
            canSend
              ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-[0_8px_24px_-10px_rgba(99,102,241,0.7)] hover:scale-[1.03] active:scale-[0.97]'
              : 'bg-slate-100 text-slate-400 dark:bg-white/5 dark:text-slate-500',
          ].join(' ')}
        >
          {disabled ? <Loader2 className="h-4.5 w-4.5 animate-spin" /> : <ArrowUp className="h-4.5 w-4.5" strokeWidth={2.5} />}
        </button>
      </div>
      <p className="mt-2 px-2 text-[11px] leading-snug text-slate-400 dark:text-slate-500">
        AI Asistan üretilen SQL'i yalnızca read-only view'lar üzerinde çalıştırır.
      </p>
    </form>
  );
}
