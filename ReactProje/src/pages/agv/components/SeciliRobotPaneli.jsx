/**
 * Seçili robotun detay panelini gösterir (Faz 4).
 *
 * 3D sahnede bir robota tıklandığında `agvStore.selectedRobotId` set edilir.
 * Bu panel zustand'dan o robotu okur; robot yoksa null döner (panel gizli).
 *
 * Tasarım: paneldeki konum/durum 5-10 Hz WS delta'sı ile re-render olur.
 * Yüksek frekanslı görsel interpolasyon useFrame'de; bu panel Hz seviyesinde
 * yenilemek React render maliyeti açısından kabul edilebilir.
 */

import { X } from 'lucide-react';
import { useEffect } from 'react';

import { useAgvStore } from '../../../stores/agvStore';

const DURUM_ETIKET = {
    Bos: 'Boşta',
    KaynagaGidiyor: 'Kaynağa Gidiyor',
    Yukluyor: 'Yüklüyor',
    Tasiyor: 'Taşıyor',
    Birakiyor: 'Bırakıyor',
    TamamlandiBildirim: 'Tamamlandı (Bildirim)',
    BeklemeYerineDonuyor: 'Bekleme Yerine Dönüyor',
    HataDuruyor: 'Hata - Duruyor',
};

const DURUM_RENK = {
    Bos: 'bg-gray-200 text-gray-700',
    KaynagaGidiyor: 'bg-amber-100 text-amber-700',
    Yukluyor: 'bg-orange-100 text-orange-700',
    Tasiyor: 'bg-emerald-100 text-emerald-700',
    Birakiyor: 'bg-orange-100 text-orange-700',
    TamamlandiBildirim: 'bg-blue-100 text-blue-700',
    BeklemeYerineDonuyor: 'bg-sky-100 text-sky-700',
    HataDuruyor: 'bg-red-100 text-red-700',
};

export default function SeciliRobotPaneli() {
    const selectedRobotId = useAgvStore((s) => s.selectedRobotId);
    const robot = useAgvStore((s) =>
        s.selectedRobotId ? s.robots[s.selectedRobotId] : null
    );
    const rota = useAgvStore((s) =>
        s.selectedRobotId ? s.rotalar[s.selectedRobotId] : null
    );
    const setSelectedRobotId = useAgvStore((s) => s.setSelectedRobotId);

    // ESC ile seçimi kapat
    useEffect(() => {
        if (!selectedRobotId) return;
        const handler = (e) => {
            if (e.key === 'Escape') setSelectedRobotId(null);
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [selectedRobotId, setSelectedRobotId]);

    if (!selectedRobotId || !robot) return null;

    const durumEtiket = DURUM_ETIKET[robot.durum] ?? robot.durum;
    const durumRenk = DURUM_RENK[robot.durum] ?? 'bg-gray-200 text-gray-700';
    const batarya = robot.batarya ?? 100;

    return (
        <div className="border-b border-gray-200 bg-white">
            <div className="flex items-center justify-between border-b border-gray-100 px-3 py-2">
                <h3 className="text-xs font-semibold text-gray-700">
                    Seçili Robot: <span className="text-blue-600">{robot.id}</span>
                </h3>
                <button
                    type="button"
                    onClick={() => setSelectedRobotId(null)}
                    className="rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                    title="Seçimi kaldır (Esc)"
                >
                    <X size={14} />
                </button>
            </div>

            <div className="space-y-2 p-3 text-xs">
                <div className="flex items-center justify-between">
                    <span className="text-gray-500">Durum</span>
                    <span
                        className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${durumRenk}`}
                    >
                        {durumEtiket}
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-gray-500">Konum</span>
                    <span className="font-mono text-gray-800">
                        ({robot.x}, {robot.y})
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-gray-500">Yön</span>
                    <span className="font-mono text-gray-800">{robot.yon ?? '—'}</span>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-gray-500">Aktif görev</span>
                    <span className="font-mono text-gray-800">
                        {robot.gorev_id ?? '—'}
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-gray-500">Rota kalan</span>
                    <span className="font-mono text-gray-800">
                        {robot.rota_kalan ?? 0} hücre
                    </span>
                </div>

                <div>
                    <div className="mb-1 flex items-center justify-between">
                        <span className="text-gray-500">Batarya</span>
                        <span className="text-gray-800">%{batarya}</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-gray-200">
                        <div
                            className={`h-full ${
                                batarya > 30 ? 'bg-emerald-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${batarya}%` }}
                        />
                    </div>
                </div>

                {rota && rota.length > 0 && (
                    <div className="pt-1">
                        <span className="text-gray-500">Planlı rota uzunluğu</span>
                        <div className="mt-0.5 font-mono text-gray-800">
                            {rota.length} adım
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
