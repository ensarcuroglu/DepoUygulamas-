import { ScanLine, Wifi } from 'lucide-react';

/**
 * Terminal UI için standart tarayıcı hazırlık kartı.
 * Scanner'ın dinleme durumunu ve animasyonlarını içerir.
 */
export function ScannerHazirKarti({ isRaf, busy, zebraDetected, loadingText = 'İŞLENİYOR...' }) {
  const bg = isRaf ? 'bg-emerald-100 dark:bg-emerald-900/40 border-emerald-300 dark:border-emerald-700' : 'bg-blue-100 dark:bg-blue-900/40 border-blue-300 dark:border-blue-700';
  const text = isRaf ? 'text-emerald-800 dark:text-emerald-300' : 'text-blue-800 dark:text-blue-300';
  
  return (
    <div className={`border-2 rounded-[28px] px-5 py-7 flex flex-col items-center justify-center min-h-[200px] ${bg} shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] transition-colors`}>
      {busy ? (
        <div className={`w-14 h-14 border-4 border-t-transparent rounded-full animate-spin ${isRaf ? 'border-emerald-600' : 'border-blue-600'}`} />
      ) : (
        <ScanLine className={`w-16 h-16 ${text} mb-4`} strokeWidth={2} />
      )}
      
      <h2 className={`text-xl font-black text-center uppercase tracking-tight leading-tight ${text} mt-2`}>
        {busy ? loadingText : (isRaf ? 'RAF BARKODUNU OKUT' : 'PALET BARKODUNU OKUT')}
      </h2>
      
      <div className="mt-5 flex items-center gap-2 bg-white/60 dark:bg-black/30 px-4 py-2 rounded-xl">
        <Wifi className={`w-4 h-4 ${zebraDetected ? 'text-green-600' : 'text-slate-500'}`} />
        <span className="font-bold text-[12px] text-slate-700 dark:text-slate-300">
          {zebraDetected ? 'ZEBRA AKTİF' : 'CİHAZ DİNLENİYOR'}
        </span>
      </div>
    </div>
  );
}
