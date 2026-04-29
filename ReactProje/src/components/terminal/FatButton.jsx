import { createElement } from 'react';
import { ChevronDown } from 'lucide-react';

/**
 * Terminal UI için standart kalın buton.
 * Geniş dokunma alanı ve haptic/aktif efektleri içerir.
 */
export function FatButton({ icon, label, onClick, variant = 'primary', disabled = false }) {
  const baseStyle = "w-full min-h-[60px] px-4 rounded-[20px] flex items-center justify-between gap-3 font-bold text-[13px] sm:text-[14px] leading-tight active:scale-[0.98] transition-all disabled:opacity-50 disabled:active:scale-100 tap-highlight-transparent";
  
  const styles = {
    primary: "bg-blue-600 text-white active:bg-blue-700 shadow-[0_4px_20px_rgba(37,99,235,0.2)]",
    success: "bg-emerald-600 text-white active:bg-emerald-700 shadow-[0_4px_20px_rgba(5,150,105,0.2)]",
    secondary: "bg-white/80 dark:bg-[#121316]/80 border border-slate-200/60 dark:border-slate-800/60 text-slate-800 dark:text-slate-200 active:bg-slate-100 dark:active:bg-slate-800 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]",
    danger: "bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700/60 text-red-800 dark:text-red-300 active:bg-red-100 dark:active:bg-red-800/60",
    warning: "bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-700/60 text-orange-800 dark:text-orange-300 active:bg-orange-100 dark:active:bg-orange-800/60"
  };

  return (
    <button onClick={onClick} disabled={disabled} className={`${baseStyle} ${styles[variant]}`}>
      <span className="min-w-0 flex items-center gap-2.5 text-left">
        {icon && createElement(icon, { className: 'w-5 h-5 shrink-0 opacity-80', strokeWidth: 2.5 })}
        <span className="min-w-0 break-words">{label}</span>
      </span>
      {variant === 'primary' || variant === 'success' || variant === 'secondary' ? <ChevronDown className="w-5 h-5 shrink-0 opacity-50" /> : null}
    </button>
  );
}
