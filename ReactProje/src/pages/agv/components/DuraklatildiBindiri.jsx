/**
 * Sim duraklatıldığında 3D sahne üzerinde sade bir bindirme (overlay).
 * WebSocket koparsa veya canlı tick durursa kullanıcıyı uyarmak için.
 */

import { Pause } from 'lucide-react';

import { useAgvStore } from '../../../stores/agvStore';

export default function DuraklatildiBindiri() {
    const duraklatildi = useAgvStore((s) => s.duraklatildi);
    if (!duraklatildi) return null;
    return (
        <div className="pointer-events-none absolute top-6 left-1/2 -translate-x-1/2 flex items-center gap-3 rounded-full bg-amber-500/10 px-6 py-2.5 text-[11px] font-bold uppercase tracking-widest text-amber-400 border border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.2)] backdrop-blur-md animate-in slide-in-from-top-4 fade-in duration-500 z-50">
            <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]"></span>
            </span>
            <Pause size={14} className="drop-shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
            <span className="drop-shadow-sm">Simülasyon Duraklatıldı</span>
        </div>
    );
}
