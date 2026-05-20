/**
 * AGV İzleme Sayfası — 3D odaklı layout.
 *
 *  ┌───── UstBilgiCubugu (dark) ─────────────────────────────────────────┐
 *  │ Bağlantı · Tick · Robot · Aktif · Kuyruk · Palet · Duraklat        │
 *  ├──────────────────────────────────────────────────┬─────────────────┤
 *  │                                                   │ YanSekmePaneli │
 *  │             3D SAHNE (geniş, odaklı)              │  Görevler      │
 *  │ ┌──────────────┐                                  │  Robotlar      │
 *  │ │SeciliRobot   │ (sol overlay, sadece seçildiğinde)│  Olaylar      │
 *  │ │Paneli        │                                  │  Test          │
 *  │ └──────────────┘                                  │                │
 *  └───────────────────────────────────────────────────┴─────────────────┘
 *
 * Mevcut WebSocket + Zustand + useFrame akışı korunur; sadece kompozisyon
 * değişti. Test paneli backend'in `AGV_TEST_PANEL_ENABLED` ayarını gerektirir.
 */

import { useAgvWebSocket } from '../../hooks/useAgvWebSocket';
import { useAgvStore } from '../../stores/agvStore';
import DepoSahnesi from './components/DepoSahnesi';
import DuraklatildiBindiri from './components/DuraklatildiBindiri';
import SeciliRobotPaneli from './components/SeciliRobotPaneli';
import UstBilgiCubugu from './components/UstBilgiCubugu';
import YanSekmePaneli from './components/YanSekmePaneli';

export default function AgvIzlemePage() {
    useAgvWebSocket();
    const selectedRobotId = useAgvStore((s) => s.selectedRobotId);

    return (
        <div className="flex h-full w-full flex-col bg-slate-950">
            <UstBilgiCubugu />

            <div className="flex flex-1 overflow-hidden relative">
                <main className="relative flex-1 bg-slate-950">
                    <DepoSahnesi />
                    <DuraklatildiBindiri />
                    {/* Sol overlay: yalnız bir robot seçildiğinde göster */}
                    {selectedRobotId && (
                        <div className="pointer-events-auto absolute left-4 top-4 w-80 max-h-[calc(100%-2rem)] overflow-y-auto rounded-xl bg-slate-950/60 border border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] backdrop-blur-xl transition-all duration-500 ease-out animate-in fade-in slide-in-from-left-4">
                            <SeciliRobotPaneli />
                        </div>
                    )}
                </main>

                <YanSekmePaneli />
            </div>
        </div>
    );
}
