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
        <div className="pointer-events-none absolute right-4 top-4 flex items-center gap-1.5 rounded-full bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-200 ring-1 ring-amber-400/40 backdrop-blur">
            <Pause size={12} />
            Simülasyon duraklatıldı
        </div>
    );
}
