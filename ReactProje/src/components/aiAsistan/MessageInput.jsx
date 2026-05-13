import { useEffect, useRef } from 'react';
import { ArrowUp, BookOpenText, Database, Loader2 } from 'lucide-react';
import { motion as Motion } from 'framer-motion';

const COMMANDS = [
  { command: '/sql', label: 'SQL', hint: 'Veri ve metrik', icon: Database },
  { command: '/docs', label: 'Docs', hint: 'Kılavuz ve süreç', icon: BookOpenText },
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
          <Motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18 }}
            className="absolute bottom-full left-0 z-20 mb-2 flex w-[min(360px,calc(100vw-3rem))] flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-[0_8px_30px_-8px_rgba(0,0,0,0.18)] dark:border-white/10 dark:bg-zinc-900 dark:shadow-[0_8px_30px_-8px_rgba(0,0,0,0.6)]"
          >
            <div className="border-b border-zinc-100 px-3 py-1.5 font-['JetBrains_Mono'] text-[10px] font-medium uppercase tracking-[0.2em] text-zinc-500 dark:border-white/[0.06] dark:text-zinc-500">
              komutlar
            </div>
            {COMMANDS.map((item) => {
              const IconComponent = item.icon;
              return (
                <button
                  key={item.command}
                  type="button"
                  onClick={() => pickCommand(item.command)}
                  className="flex items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-amber-50/70 dark:hover:bg-amber-400/[0.06]"
                >
                  <IconComponent className="h-4 w-4 shrink-0 text-zinc-500 dark:text-zinc-400" strokeWidth={1.75} />
                  <span className="min-w-0 flex-1">
                    <span className="block font-['JetBrains_Mono'] text-[12.5px] font-medium text-zinc-900 dark:text-zinc-100">
                      {item.command}
                    </span>
                    <span className="block text-[11.5px] text-zinc-500 dark:text-zinc-400">
                      {item.hint}
                    </span>
                  </span>
                </button>
              );
            })}
          </Motion.div>
        )}

        <div
          className={[
            'relative flex w-full items-end gap-2 rounded-2xl border bg-white px-3 py-2 transition-all duration-200 ease-out sm:gap-3',
            'border-zinc-200 shadow-[0_1px_2px_rgba(0,0,0,0.04)]',
            'focus-within:border-amber-500 focus-within:shadow-[0_0_0_3px_rgba(245,158,11,0.12),0_2px_8px_-2px_rgba(0,0,0,0.06)]',
            'dark:border-white/10 dark:bg-zinc-900 dark:focus-within:border-amber-400/60 dark:focus-within:shadow-[0_0_0_3px_rgba(245,158,11,0.10)]',
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
            placeholder={placeholder ?? 'Bir soru yaz, ya da / ile komut seç…'}
            className="min-h-[40px] flex-1 resize-none bg-transparent px-1.5 py-2.5 text-[15px] leading-relaxed text-zinc-900 caret-amber-600 placeholder-zinc-400 outline-none disabled:opacity-60 [scrollbar-width:none] dark:text-zinc-100 dark:caret-amber-400 dark:placeholder-zinc-500 sm:text-[15.5px]"
          />

          <div className="flex h-[40px] shrink-0 items-center">
            <Motion.button
              whileHover={canSend ? { scale: 1.04 } : {}}
              whileTap={canSend ? { scale: 0.94 } : {}}
              type="submit"
              disabled={!canSend}
              aria-label="Gönder"
              className={[
                'flex h-9 w-9 items-center justify-center rounded-xl transition-colors duration-200',
                canSend
                  ? 'bg-amber-500 text-white shadow-[0_2px_6px_-1px_rgba(245,158,11,0.45)] hover:bg-amber-600 dark:bg-amber-400 dark:text-zinc-950 dark:hover:bg-amber-300'
                  : 'bg-zinc-100 text-zinc-400 dark:bg-white/[0.06] dark:text-zinc-600',
              ].join(' ')}
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
              )}
            </Motion.button>
          </div>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-center gap-2 px-2">
        <kbd className="rounded border border-zinc-200 bg-white px-1.5 font-['JetBrains_Mono'] text-[10px] font-medium text-zinc-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400">
          ↵
        </kbd>
        <span className="font-['JetBrains_Mono'] text-[10.5px] tracking-wide text-zinc-400 dark:text-zinc-500">
          gönder
        </span>
        <span className="text-zinc-300 dark:text-zinc-700">·</span>
        <kbd className="rounded border border-zinc-200 bg-white px-1.5 font-['JetBrains_Mono'] text-[10px] font-medium text-zinc-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400">
          ⇧↵
        </kbd>
        <span className="font-['JetBrains_Mono'] text-[10.5px] tracking-wide text-zinc-400 dark:text-zinc-500">
          satır
        </span>
        <span className="text-zinc-300 dark:text-zinc-700">·</span>
        <kbd className="rounded border border-zinc-200 bg-white px-1.5 font-['JetBrains_Mono'] text-[10px] font-medium text-zinc-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400">
          /
        </kbd>
        <span className="font-['JetBrains_Mono'] text-[10.5px] tracking-wide text-zinc-400 dark:text-zinc-500">
          komut
        </span>
      </div>
    </form>
  );
}
