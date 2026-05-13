import { useEffect, useRef } from 'react';
import { ArrowUp, BookOpenText, Database, Loader2 } from 'lucide-react';
import { motion as Motion } from 'framer-motion';

const COMMANDS = [
  { command: '/sql', label: 'SQL', hint: 'Veri ve metrik', icon: Database },
  { command: '/docs', label: 'Docs', hint: 'Kilavuz ve surec', icon: BookOpenText },
];

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
  const trimmed = value.trimStart();
  const showCommands = trimmed.startsWith('/') && !trimmed.includes(' ');

  const pickCommand = (command) => {
    onChange?.(`${command} `);
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (canSend) onSubmit?.();
      }}
      className="relative w-full"
    >
      <div className="relative">
        {showCommands && (
          <div className="absolute bottom-full left-3 z-20 mb-2 flex w-[min(360px,calc(100vw-3rem))] flex-col gap-1 rounded-2xl border border-slate-200/80 bg-white/95 p-1.5 shadow-lg backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/95">
            {COMMANDS.map((item) => {
              const IconComponent = item.icon;
              return (
                <button
                  key={item.command}
                  type="button"
                  onClick={() => pickCommand(item.command)}
                  className="flex items-center gap-3 rounded-xl px-3 py-2 text-left transition hover:bg-slate-100 dark:hover:bg-white/10"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300">
                    <IconComponent className="h-4 w-4" />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-[13px] font-semibold text-slate-800 dark:text-slate-100">
                      {item.command}{' '}
                      <span className="text-slate-500 dark:text-slate-400">{item.label}</span>
                    </span>
                    <span className="block text-[11.5px] text-slate-500 dark:text-slate-400">
                      {item.hint}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        )}

        <div
          className={[
            'group relative flex w-full items-end gap-2 rounded-[1.75rem] border bg-white/70 p-2 pl-4 pr-2 backdrop-blur-xl transition-all duration-300 ease-out sm:gap-3 sm:pl-6',
            'border-slate-200/80 shadow-[0_2px_12px_-4px_rgba(15,23,42,0.08),0_1px_0_rgba(255,255,255,0.8)_inset]',
            'focus-within:border-indigo-400/50 focus-within:bg-white/95 focus-within:shadow-[0_8px_30px_-8px_rgba(99,102,241,0.25),0_1px_0_rgba(255,255,255,1)_inset]',
            'dark:border-white/10 dark:bg-slate-900/60 dark:shadow-[0_1px_0_rgba(255,255,255,0.05)_inset]',
            'dark:focus-within:border-indigo-400/40 dark:focus-within:bg-slate-900/80 dark:focus-within:shadow-[0_8px_30px_-8px_rgba(99,102,241,0.15)]',
            disabled ? 'pointer-events-none opacity-70' : '',
          ].join(' ')}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={disabled}
            placeholder={placeholder ?? 'Bir soru yazin...'}
            className="min-h-[44px] flex-1 resize-none bg-transparent py-3 text-[15px] leading-relaxed text-slate-800 placeholder-slate-400 outline-none disabled:opacity-60 [scrollbar-width:none] dark:text-slate-100 dark:placeholder-slate-500 sm:text-base"
          />

          <div className="flex h-[44px] shrink-0 items-center">
            <Motion.button
              whileHover={canSend ? { scale: 1.05 } : {}}
              whileTap={canSend ? { scale: 0.95 } : {}}
              type="submit"
              disabled={!canSend}
              aria-label="Gonder"
              className={[
                'flex h-10 w-10 items-center justify-center rounded-full transition-colors duration-300 sm:h-11 sm:w-11',
                canSend
                  ? 'bg-slate-900 text-white shadow-md dark:bg-white dark:text-slate-900'
                  : 'bg-slate-100 text-slate-400 dark:bg-white/5 dark:text-slate-500',
              ].join(' ')}
            >
              {disabled ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <ArrowUp className="h-5 w-5" strokeWidth={2.5} />
              )}
            </Motion.button>
          </div>
        </div>
      </div>

      <div className="mt-2.5 flex justify-center px-4 text-center">
        <p className="text-[11px] font-medium tracking-wide text-slate-400 dark:text-slate-500 sm:text-[12px]">
          AI Asistan SQL ve dokuman yanitlarini tek sohbet akisi icinde yonlendirir.
        </p>
      </div>
    </form>
  );
}
