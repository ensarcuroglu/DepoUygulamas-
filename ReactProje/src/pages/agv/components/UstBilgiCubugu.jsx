/**
 * Üst bilgi çubuğu — bağlantı, anlık metrikler, duraklat/devam.
 *
 * Tasarım: yatay tek satır; küçük metrik chip'leri + duraklat butonu.
 */

import { useMutation } from '@tanstack/react-query';
import { Pause, Play, Wifi, WifiOff, Loader2 } from 'lucide-react';

import { agvApi } from '../../../services/agvApi';
import { useAgvStore } from '../../../stores/agvStore';

function Metrik({ etiket, deger, vurgu = false }) {
    return (
        <div className="flex items-center gap-1.5 rounded-md bg-slate-800/60 px-2.5 py-1 ring-1 ring-slate-700">
            <span className="text-[10px] uppercase tracking-wider text-slate-400">
                {etiket}
            </span>
            <span
                className={`font-mono text-xs ${
                    vurgu ? 'text-amber-300' : 'text-slate-100'
                }`}
            >
                {deger}
            </span>
        </div>
    );
}

export default function UstBilgiCubugu() {
    const tickNo = useAgvStore((s) => s.tickNo);
    const kuyruk = useAgvStore((s) => s.kuyrukUzunlugu);
    const aktif = useAgvStore((s) => s.aktifGorevSayisi);
    const robotIds = useAgvStore((s) => s.robotIds);
    const robots = useAgvStore((s) => s.robots);
    const paletKeys = useAgvStore((s) => s.paletKeys);
    const duraklatildi = useAgvStore((s) => s.duraklatildi);
    const isConnected = useAgvStore((s) => s.isConnected);
    const isConnecting = useAgvStore((s) => s.isConnecting);

    const aktifRobot = robotIds.filter((id) => robots[id]?.durum !== 'Bos').length;
    const hataRobot = robotIds.filter(
        (id) => robots[id]?.durum === 'HataDuruyor'
    ).length;

    const duraklatMut = useMutation({ mutationFn: () => agvApi.test.duraklat() });
    const devamMut = useMutation({ mutationFn: () => agvApi.test.devam() });
    const isToggling = duraklatMut.isPending || devamMut.isPending;

    function togglePause() {
        if (duraklatildi) devamMut.mutate();
        else duraklatMut.mutate();
    }

    return (
        <div className="flex items-center justify-between gap-3 border-b border-slate-800 bg-slate-950 px-4 py-2 text-slate-100">
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-slate-200">
                    <span className="rounded-md bg-blue-500/10 px-2 py-1 ring-1 ring-blue-500/30">
                        <span className="text-xs font-semibold text-blue-300">
                            AGV İzleme
                        </span>
                    </span>
                    <span className="text-[11px] text-slate-500">
                        Otonom mobil robot — canlı 3D simülasyon
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <Metrik etiket="Tick" deger={tickNo} />
                <Metrik
                    etiket="Robot"
                    deger={`${aktifRobot}/${robotIds.length}`}
                    vurgu={hataRobot > 0}
                />
                <Metrik etiket="Aktif görev" deger={aktif} />
                <Metrik etiket="Kuyruk" deger={kuyruk} vurgu={kuyruk > 0} />
                <Metrik etiket="Palet" deger={paletKeys.length} />

                <button
                    type="button"
                    onClick={togglePause}
                    disabled={!isConnected || isToggling}
                    className={`ml-2 flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium ring-1 transition ${
                        duraklatildi
                            ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40 hover:bg-emerald-500/25'
                            : 'bg-amber-500/15 text-amber-300 ring-amber-500/40 hover:bg-amber-500/25'
                    } disabled:cursor-not-allowed disabled:opacity-40`}
                    title={duraklatildi ? 'Simülasyonu devam ettir' : 'Simülasyonu duraklat'}
                >
                    {isToggling ? (
                        <Loader2 size={12} className="animate-spin" />
                    ) : duraklatildi ? (
                        <Play size={12} />
                    ) : (
                        <Pause size={12} />
                    )}
                    {duraklatildi ? 'Devam' : 'Duraklat'}
                </button>

                <div className="ml-2 flex items-center gap-1.5 rounded-md bg-slate-800/60 px-2.5 py-1 ring-1 ring-slate-700">
                    {isConnected ? (
                        <Wifi size={12} className="text-emerald-400" />
                    ) : isConnecting ? (
                        <Loader2 size={12} className="animate-spin text-amber-300" />
                    ) : (
                        <WifiOff size={12} className="text-red-400" />
                    )}
                    <span className="text-xs text-slate-200">
                        {isConnected
                            ? 'Bağlı'
                            : isConnecting
                              ? 'Bağlanıyor…'
                              : 'Kopuk'}
                    </span>
                </div>
            </div>
        </div>
    );
}
