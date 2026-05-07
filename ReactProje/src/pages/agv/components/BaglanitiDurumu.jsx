/**
 * WS bağlantı göstergesi — header'da gösterilir.
 */

import { useAgvStore } from '../../../stores/agvStore';

export default function BaglanitiDurumu() {
    const isConnected = useAgvStore((s) => s.isConnected);
    const isConnecting = useAgvStore((s) => s.isConnecting);
    const lastError = useAgvStore((s) => s.lastError);

    let renk = 'bg-gray-400';
    let metin = 'Bilinmiyor';
    if (isConnected) {
        renk = 'bg-green-500';
        metin = 'Bağlı';
    } else if (isConnecting) {
        renk = 'bg-amber-400 animate-pulse';
        metin = 'Bağlanıyor…';
    } else if (lastError) {
        renk = 'bg-red-500';
        metin = 'Kopuk';
    }

    return (
        <div className="flex items-center gap-2 text-xs">
            <div className={`h-2.5 w-2.5 rounded-full ${renk}`} />
            <span className="font-medium text-gray-700">WS: {metin}</span>
            {lastError && !isConnected && (
                <span className="ml-1 truncate text-gray-400" title={lastError}>
                    ({lastError})
                </span>
            )}
        </div>
    );
}
