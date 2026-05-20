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
    Bos: 'bg-slate-800/50 text-slate-300 border border-white/10 shadow-[0_0_10px_rgba(255,255,255,0.05)]',
    KaynagaGidiyor: 'bg-amber-500/20 text-amber-400 border border-amber-400/50 shadow-[0_0_15px_rgba(245,158,11,0.2)]',
    Yukluyor: 'bg-orange-500/20 text-orange-400 border border-orange-400/50 shadow-[0_0_15px_rgba(249,115,22,0.2)]',
    Tasiyor: 'bg-emerald-500/20 text-emerald-400 border border-emerald-400/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]',
    Birakiyor: 'bg-orange-500/20 text-orange-400 border border-orange-400/50 shadow-[0_0_15px_rgba(249,115,22,0.2)]',
    TamamlandiBildirim: 'bg-blue-500/20 text-blue-400 border border-blue-400/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]',
    BeklemeYerineDonuyor: 'bg-sky-500/20 text-sky-400 border border-sky-400/50 shadow-[0_0_15px_rgba(56,189,248,0.2)]',
    HataDuruyor: 'bg-red-500/30 text-red-400 border border-red-400/60 shadow-[0_0_20px_rgba(239,68,68,0.4)] animate-pulse',
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
    const durumRenk = DURUM_RENK[robot.durum] ?? 'bg-slate-800 text-slate-300';
    const batarya = robot.batarya ?? 100;

    return (
        <div className="bg-transparent relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none"></div>
            <div className="flex items-center justify-between border-b border-white/10 bg-slate-950/40 px-4 py-3 relative z-10">
                <h3 className="text-[10px] font-bold text-slate-400 tracking-widest uppercase flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></span>
                    </span>
                    Seçili Robot: <span className="text-blue-400 font-mono drop-shadow-[0_0_8px_rgba(59,130,246,0.6)] text-xs">AGV-{robot.id}</span>
                </h3>
                <button
                    type="button"
                    onClick={() => setSelectedRobotId(null)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-red-500/20 hover:text-red-400 hover:shadow-[0_0_12px_rgba(239,68,68,0.3)] transition-all duration-300"
                    title="Seçimi kaldır (Esc)"
                >
                    <X size={14} />
                </button>
            </div>

            <div className="space-y-1 p-3 text-xs relative z-10">
                {/* Durum */}
                <div className="flex items-center justify-between border-b border-white/5 pb-2 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <span className="text-slate-400 font-medium">Durum</span>
                    <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${durumRenk}`}
                    >
                        {durumEtiket}
                    </span>
                </div>

                {/* Konum */}
                <div className="flex items-center justify-between border-b border-white/5 pb-2 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <span className="text-slate-400 font-medium">Anlık Konum</span>
                    <span className="font-mono font-bold text-slate-200">
                        X: {robot.x} , Y: {robot.y}
                    </span>
                </div>

                {/* Yön */}
                <div className="flex items-center justify-between border-b border-white/5 pb-2 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <span className="text-slate-400 font-medium">Yönelme Açısı</span>
                    <span className="font-mono font-bold text-slate-200">{robot.yon ?? '—'}</span>
                </div>

                {/* Aktif Görev */}
                <div className="flex items-center justify-between border-b border-white/5 pb-2 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <span className="text-slate-400 font-medium">Aktif WMS Görevi</span>
                    <span className={`font-mono font-bold ${robot.gorev_id ? 'text-blue-400 drop-shadow-[0_0_4px_rgba(59,130,246,0.4)]' : 'text-slate-500'}`}>
                        {robot.gorev_id ? `#${robot.gorev_id}` : 'Boşta'}
                    </span>
                </div>

                {/* Rota Kalan */}
                <div className="flex items-center justify-between border-b border-white/5 pb-2 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <span className="text-slate-400 font-medium">Kalan Mesafe</span>
                    <span className="font-mono font-bold text-slate-200">
                        {robot.rota_kalan ?? 0} hücre
                    </span>
                </div>

                {/* Batarya */}
                <div className="border-b border-white/5 pb-3 pt-2 px-2 hover:bg-white/5 rounded transition-colors">
                    <div className="mb-2 flex items-center justify-between">
                        <span className="text-slate-400 font-medium">Batarya Seviyesi</span>
                        <span className={`font-mono font-bold ${
                            batarya > 50 ? 'text-emerald-400 drop-shadow-[0_0_4px_rgba(16,185,129,0.4)]' : batarya > 20 ? 'text-amber-400 drop-shadow-[0_0_4px_rgba(245,158,11,0.4)]' : 'text-red-400 animate-pulse drop-shadow-[0_0_4px_rgba(239,68,68,0.4)]'
                        }`}>
                            %{batarya}
                        </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-950 border border-white/10 relative">
                        <div
                            className={`h-full rounded-full transition-all duration-500 shadow-[0_0_10px_currentColor] ${
                                batarya > 50
                                    ? 'bg-gradient-to-r from-emerald-600 to-emerald-400'
                                    : batarya > 20
                                      ? 'bg-gradient-to-r from-amber-600 to-amber-400'
                                      : 'bg-gradient-to-r from-red-600 to-red-400 animate-pulse'
                            }`}
                            style={{ width: `${batarya}%` }}
                        />
                    </div>
                </div>

                {rota && rota.length > 0 && (
                    <div className="pt-2 px-2 pb-1 hover:bg-white/5 rounded transition-colors">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400 font-medium">Planlı Rota</span>
                            <span className="font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 shadow-[0_0_8px_rgba(245,158,11,0.2)] rounded px-2 py-0.5 text-[10px]">
                                {rota.length} Adım
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
