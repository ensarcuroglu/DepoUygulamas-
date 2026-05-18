import { useRef } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';

/**
 * Mesaj giris alani. Tek satir gibi gorunse de auto-resize textarea.
 * Enter -> gonder, Shift+Enter -> yeni satir.
 *
 * Yumusak glass-pill tasarim: focus icinde gradient halo, send butonu
 * primary gradient ile yuksek temas hissi verir.
 */
export default function MesajInput({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = 'Sorunuzu yazın… (Enter ile gönder, Shift+Enter ile yeni satır)',
}) {
  const textareaRef = useRef(null);
  const hasValue = value.trim().length > 0;

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && hasValue) onSubmit();
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
        if (!disabled && hasValue) onSubmit();
      }}
      className="group relative flex w-full items-end gap-2 rounded-2xl border border-white/70 bg-white/90 px-3 py-2 shadow-md shadow-primary-500/5 backdrop-blur-xl transition-all duration-200 focus-within:border-primary-300 focus-within:shadow-lg focus-within:shadow-primary-500/15 focus-within:ring-4 focus-within:ring-primary-500/10"
    >
      <span
        aria-hidden
        className="pointer-events-none absolute -inset-px -z-10 rounded-2xl bg-gradient-to-r from-primary-400/0 via-primary-400/10 to-accent-400/0 opacity-0 transition-opacity duration-300 group-focus-within:opacity-100"
      />
      <label htmlFor="depo-asistani-input" className="sr-only">
        Asistana mesaj yazın
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
        className="flex-1 resize-none border-0 bg-transparent py-2 text-sm leading-relaxed text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-0 disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !hasValue}
        aria-label="Mesajı gönder"
        className="relative inline-flex h-10 w-10 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-md shadow-primary-500/30 ring-1 ring-inset ring-white/15 transition-all duration-200 hover:from-primary-600 hover:to-primary-800 hover:shadow-lg hover:shadow-primary-500/40 active:scale-95 disabled:cursor-not-allowed disabled:from-text-tertiary/40 disabled:to-text-tertiary/40 disabled:shadow-none disabled:ring-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
      >
        {disabled ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        ) : (
          <ArrowUp className="h-4 w-4" aria-hidden strokeWidth={2.5} />
        )}
      </button>
    </form>
  );
}
