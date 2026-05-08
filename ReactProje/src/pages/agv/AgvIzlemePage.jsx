/**
 * AGV İzleme Sayfası — Faz 2.
 *
 * Layout: header + (3D sahne | sağ panel).
 * WS bağlantısı sayfada bir kez kurulur (`useAgvWebSocket`); zustand store'a yazılır.
 *
 * Detaylı plan: /AGV_SIMULATION_PLAN.md
 */

import { useAgvWebSocket } from '../../hooks/useAgvWebSocket';
import BaglanitiDurumu from './components/BaglanitiDurumu';
import DepoSahnesi from './components/DepoSahnesi';
import GorevPaneli from './components/GorevPaneli';
import SeciliRobotPaneli from './components/SeciliRobotPaneli';

export default function AgvIzlemePage() {
    useAgvWebSocket();

    return (
        <div className="flex h-full w-full flex-col bg-gray-100">
            <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2.5">
                <div>
                    <h1 className="text-base font-semibold text-gray-800">AGV İzleme</h1>
                    <p className="text-[11px] text-gray-500">
                        Otonom mobil robot simülasyonu — canlı 3D görselleştirme
                    </p>
                </div>
                <BaglanitiDurumu />
            </div>

            <div className="flex flex-1 overflow-hidden">
                <main className="relative flex-1 bg-slate-900">
                    <DepoSahnesi />
                </main>
                <aside className="flex w-72 shrink-0 flex-col overflow-y-auto border-l border-gray-200 bg-gray-50">
                    <SeciliRobotPaneli />
                    <GorevPaneli />
                </aside>
            </div>
        </div>
    );
}
