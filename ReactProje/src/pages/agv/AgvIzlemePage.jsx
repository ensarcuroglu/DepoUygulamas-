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

            <div className="flex flex-1 overflow-hidden">
                <main className="relative flex-1 bg-slate-900">
                    <DepoSahnesi />
                    <DuraklatildiBindiri />
                    {/* Sol overlay: yalnız bir robot seçildiğinde göster */}
                    {selectedRobotId && (
                        <div className="pointer-events-auto absolute left-3 top-3 w-72 max-h-[calc(100%-1.5rem)] overflow-y-auto rounded-lg bg-white/95 shadow-xl ring-1 ring-gray-200 backdrop-blur">
                            <SeciliRobotPaneli />
                        </div>
                    )}
                </main>

                <YanSekmePaneli />
            </div>
        </div>
    );
}
