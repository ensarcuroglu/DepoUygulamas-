import { useRef } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';

/**
 * Mesaj giris alani. Tek satir gibi gorunse de auto-resize textarea.
 * Enter -> gonder, Shift+Enter -> yeni satir.
 */
export default function MesajInput({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = 'Sorunuzu yazin... ',
}) {
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  };

  const handleChange = (e) => {
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
    }
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!disabled && value.trim()) onSubmit();
      }}
      className="relative flex w-full items-end gap-2 rounded-xl border border-border bg-surface px-3 py-2 shadow-sm focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20"
    >
      <label htmlFor="depo-asistani-input" className="sr-only">
        Asistana mesaj yazin
      </label>
      <textarea
        id="depo-asistani-input"
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 resize-none border-0 bg-transparent py-1.5 text-sm leading-relaxed text-text-primary placeholder:text-zinc-400 focus:outline-none focus:ring-0 disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Mesaji gonder"
        className="inline-flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-lg bg-primary-700 text-white transition-colors duration-200 hover:bg-primary-800 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      >
        {disabled ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        ) : (
          <ArrowUp className="h-4 w-4" aria-hidden strokeWidth={2.25} />
        )}
      </button>
    </form>
  );
}
