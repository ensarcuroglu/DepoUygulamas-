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
        <div className={`group flex flex-col items-start min-w-[80px] rounded-lg bg-slate-900/40 border border-white/5 px-3 py-1.5 transition-all duration-300 hover:border-white/10 hover:bg-slate-800/50 cursor-default ${vurgu ? 'shadow-[0_0_15px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/30' : ''}`}>
            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400 group-hover:text-slate-300 transition-colors duration-300">
                {etiket}
            </span>
            <span
                className={`font-mono text-sm font-bold mt-0.5 tracking-tight ${
                    vurgu ? 'text-amber-400 drop-shadow-[0_0_8px_rgba(245,158,11,0.4)] animate-pulse' : 'text-slate-100'
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
        <div className="flex items-center justify-between gap-4 border-b border-white/5 bg-slate-950/60 px-6 py-3 text-slate-100 shadow-2xl backdrop-blur-xl z-10 relative">
            <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none"></div>
            <div className="flex items-center gap-3 relative z-10">
                <div className="flex items-center gap-3">
                    <span className="rounded-lg bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.15)] backdrop-blur-md">
                        AGV SCADA
                    </span>
                    <span className="text-xs text-slate-400 font-medium hidden md:inline tracking-wide">
                        Command Center
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-3">
                <Metrik etiket="Tick" deger={tickNo} />
                <Metrik
                    etiket="Robot"
                    deger={`${aktifRobot}/${robotIds.length}`}
                    vurgu={hataRobot > 0}
                />
                <Metrik etiket="Aktif Görev" deger={aktif} />
                <Metrik etiket="Kuyruk" deger={kuyruk} vurgu={kuyruk > 0} />
                <Metrik etiket="Palet" deger={paletKeys.length} />

                <button
                    type="button"
                    onClick={togglePause}
                    disabled={!isConnected || isToggling}
                    className={`ml-2 flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all duration-300 relative overflow-hidden group ${
                        duraklatildi
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 hover:border-emerald-400/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.25)]'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 hover:border-amber-400/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.25)]'
                    } disabled:cursor-not-allowed disabled:opacity-40 z-10`}
                    title={duraklatildi ? 'Simülasyonu devam ettir' : 'Simülasyonu duraklat'}
                >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out pointer-events-none"></div>
                    {isToggling ? (
                        <Loader2 size={14} className="animate-spin" />
                    ) : duraklatildi ? (
                        <Play size={14} className="fill-current drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    ) : (
                        <Pause size={14} className="fill-current drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]" />
                    )}
                    <span className="drop-shadow-sm">{duraklatildi ? 'Devam' : 'Duraklat'}</span>
                </button>

                <div className="ml-2 flex items-center gap-2.5 rounded-lg bg-slate-900/40 border border-white/5 px-4 py-2 transition-all duration-300 z-10">
                    <span className="relative flex h-2.5 w-2.5">
                        {isConnected ? (
                            <>
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></span>
                            </>
                        ) : isConnecting ? (
                            <>
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]"></span>
                            </>
                        ) : (
                            <>
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"></span>
                            </>
                        )}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">
                        {isConnected
                            ? 'Sistem Bağlı'
                            : isConnecting
                              ? 'Bağlanıyor…'
                              : 'Bağlantı Kesildi'}
                    </span>
                </div>
            </div>
        </div>
    );
}
