/**
 * Sağ yan panel — sekmeli detay (Görevler / Robotlar / Olaylar / Test).
 *
 * Panel collapsible'dır; küçük ekranlarda yön ikonuyla daraltılabilir.
 */

import {
    ChevronRight,
    ChevronLeft,
    Boxes,
    Bot,
    Activity,
    FlaskConical,
} from 'lucide-react';
import { useState } from 'react';

import { useAgvStore } from '../../../stores/agvStore';
import TestPaneli from './TestPaneli';

const DURUM_ETIKET = {
    Bos: 'Boşta',
    KaynagaGidiyor: 'Kaynağa Gidiyor',
    Yukluyor: 'Yüklüyor',
    Tasiyor: 'Taşıyor',
    Birakiyor: 'Bırakıyor',
    TamamlandiBildirim: 'Tamamlandı',
    BeklemeYerineDonuyor: 'Şarja Dönüyor',
    HataDuruyor: 'Hata',
};

const DURUM_RENK_TXT = {
    Bos: 'text-slate-400',
    KaynagaGidiyor: 'text-amber-400 font-bold',
    Yukluyor: 'text-orange-400 font-bold',
    Tasiyor: 'text-emerald-400 font-bold',
    Birakiyor: 'text-orange-400 font-bold',
    TamamlandiBildirim: 'text-blue-400 font-bold',
    BeklemeYerineDonuyor: 'text-sky-400 font-bold',
    HataDuruyor: 'text-red-400 font-bold animate-pulse',
};

const PALET_DURUM_RENK = {
    KaynaktaBekliyor: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
    RobotUzerinde: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    HedefteBirakildi: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
    Bilinmiyor: 'bg-slate-800 text-slate-400 border border-slate-700/50',
};

const SEKMELER = [
    { id: 'gorevler', etiket: 'Görevler', ikon: Boxes },
    { id: 'robotlar', etiket: 'Robotlar', ikon: Bot },
    { id: 'olaylar', etiket: 'Olaylar', ikon: Activity },
    { id: 'test', etiket: 'Test', ikon: FlaskConical },
];

function GorevlerSekmesi() {
    const aktifGorevler = useAgvStore((s) => s.aktifGorevler);
    const kuyruk = useAgvStore((s) => s.kuyrukUzunlugu);
    const paletKeys = useAgvStore((s) => s.paletKeys);
    const paletler = useAgvStore((s) => s.paletler);

    return (
        <div className="flex flex-col gap-4 p-4">
            <Kart baslik={`Aktif Görevler (${aktifGorevler.length}) · Kuyruk: ${kuyruk}`}>
                {aktifGorevler.length === 0 && (
                    <div className="text-[11px] text-slate-500 py-3 text-center">Aktif görev yok</div>
                )}
                {aktifGorevler.map((g) => (
                    <div
                        key={g.gorev_id}
                        className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 hover:border-slate-700/60 px-3 py-2 text-[11px] transition-all duration-200"
                    >
                        <div className="flex items-center gap-2">
                            <span className="flex h-1.5 w-1.5 rounded-full bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.5)]"></span>
                            <span className="font-mono font-bold text-slate-300">
                                AGV-{g.robot_id ?? '—'}
                            </span>
                            <span className="font-mono text-slate-500 text-[10px]">
                                #{g.wms_gorev_id ?? g.gorev_id}
                            </span>
                        </div>
                        <div className="flex items-center gap-1 text-slate-400 font-medium">
                            <span className="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300">{g.kaynak_raf_id}</span>
                            <span className="text-slate-600">→</span>
                            <span className="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300">{g.hedef_raf_id}</span>
                        </div>
                    </div>
                ))}
            </Kart>

            <Kart baslik={`Palet Durumları (${paletKeys.length})`}>
                {paletKeys.length === 0 && (
                    <div className="text-[11px] text-slate-500 py-3 text-center">Palet yok</div>
                )}
                {paletKeys.map((k) => {
                    const p = paletler[k];
                    if (!p) return null;
                    return (
                        <div
                            key={k}
                            className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 hover:border-slate-700/60 px-3 py-2 text-[11px] transition-all duration-200"
                        >
                            <span className="font-mono font-bold text-slate-300">
                                {p.palet_id ? `#${p.palet_id}` : p.palet_key}
                            </span>
                            <span
                                className={`rounded px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                                    PALET_DURUM_RENK[p.durum] ??
                                    'bg-slate-800 text-slate-400 border border-slate-700/50'
                                }`}
                            >
                                {p.durum === 'KaynaktaBekliyor' ? 'Kaynakta' : p.durum === 'RobotUzerinde' ? 'Taşınıyor' : p.durum === 'HedefteBirakildi' ? 'Hedefte' : p.durum}
                            </span>
                        </div>
                    );
                })}
            </Kart>
        </div>
    );
}

function RobotSatir({ robotId }) {
    const robot = useAgvStore((s) => s.robots[robotId]);
    const setSelectedRobotId = useAgvStore((s) => s.setSelectedRobotId);
    const selected = useAgvStore((s) => s.selectedRobotId === robotId);
    if (!robot) return null;
    const renk = DURUM_RENK_TXT[robot.durum] ?? 'text-slate-400';
    const batarya = robot.batarya ?? 100;
    const bataryaGradient =
        batarya < 20 ? 'from-red-600 to-red-400 animate-pulse' : batarya < 50 ? 'from-amber-600 to-amber-400' : 'from-emerald-600 to-emerald-400';
    return (
        <button
            type="button"
            onClick={() => setSelectedRobotId(selected ? null : robotId)}
            className={`group flex w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-[11px] transition-all duration-300 relative overflow-hidden ${
                selected
                    ? 'border-blue-500/50 bg-blue-500/10 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                    : 'border-white/5 bg-slate-950/40 hover:border-white/10 hover:bg-slate-900/60'
            }`}
        >
            {selected && <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-transparent pointer-events-none"></div>}
            <div className="flex items-center gap-2 relative z-10">
                <span className="font-mono font-bold text-slate-200 group-hover:text-white transition-colors">
                    AGV-{robot.id}
                </span>
                {robot.sarja_donuyor && (
                    <span className="flex items-center text-[9px] text-amber-400 animate-pulse bg-amber-500/10 border border-amber-500/20 px-1 rounded gap-0.5 shadow-[0_0_8px_rgba(245,158,11,0.2)]">
                        ⚡ <span className="text-[7px] uppercase tracking-wider font-bold">Şarj</span>
                    </span>
                )}
            </div>
            <div className="flex items-center gap-2.5 relative z-10">
                <div className="flex flex-col items-end gap-1">
                    <span className={`text-[10px] font-bold ${renk} drop-shadow-sm`}>
                        {DURUM_ETIKET[robot.durum] ?? robot.durum}
                    </span>
                    <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-900 border border-white/5 relative">
                            <div
                                className={`h-full rounded-full bg-gradient-to-r transition-all duration-500 ${bataryaGradient}`}
                                style={{ width: `${batarya}%` }}
                            />
                        </div>
                        <span className="text-[9px] font-bold text-slate-400 font-mono">%{batarya}</span>
                    </div>
                </div>
            </div>
        </button>
    );
}

function RobotlarSekmesi() {
    const robotIds = useAgvStore((s) => s.robotIds);
    return (
        <div className="flex flex-col gap-4 p-4">
            <Kart baslik={`Robot Listesi (${robotIds.length})`}>
                {robotIds.length === 0 && (
                    <div className="text-[11px] text-slate-500 py-3 text-center">Henüz robot yok</div>
                )}
                <div className="flex flex-col gap-1.5">
                    {robotIds.map((id) => (
                        <RobotSatir key={id} robotId={id} />
                    ))}
                </div>
            </Kart>
        </div>
    );
}

function OlaylarSekmesi() {
    const olaylar = useAgvStore((s) => s.sonOlaylar);
    return (
        <div className="flex flex-col gap-4 p-4">
            <Kart baslik={`Sistem Günlüğü (${olaylar.length})`}>
                {olaylar.length === 0 && (
                    <div className="text-[11px] text-slate-500 py-4 text-center">Olay bekleniyor…</div>
                )}
                <ul className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
                    {olaylar.slice(0, 30).map((o, i) => (
                        <li
                            key={`${o.ts}-${i}`}
                            className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/40 hover:border-slate-800/80 px-2.5 py-1.5 text-[11px] transition-colors"
                        >
                            <span className="font-mono font-bold text-blue-400 text-[10px] bg-blue-500/10 border border-blue-500/20 px-1 rounded">
                                {o.robot_id ? `AGV-${o.robot_id}` : 'SYS'}
                            </span>
                            <span className="text-slate-300 text-[10px] font-medium">{o.olay}</span>
                            {o.gorev_id && (
                                <span className="ml-auto font-mono text-[9px] text-slate-500 bg-slate-900 border border-slate-800 px-1 rounded">
                                    #{o.gorev_id}
                                </span>
                            )}
                        </li>
                    ))}
                </ul>
            </Kart>
        </div>
    );
}

function Kart({ baslik, children }) {
    return (
        <div className="rounded-xl bg-slate-900/40 p-4 border border-white/5 shadow-xl backdrop-blur-md transition-all duration-300 hover:border-white/10 hover:bg-slate-900/60 hover:shadow-2xl group relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
            <h3 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2 group-hover:text-slate-300 transition-colors relative z-10">
                <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]"></span>
                </span>
                {baslik}
            </h3>
            <div className="flex flex-col gap-1.5 relative z-10">{children}</div>
        </div>
    );
}

export default function YanSekmePaneli() {
    const [aktifSekme, setAktifSekme] = useState('gorevler');
    const [acik, setAcik] = useState(true);

    if (!acik) {
        return (
            <aside className="flex w-12 shrink-0 flex-col border-l border-white/5 bg-slate-950/60 backdrop-blur-xl transition-all duration-500 ease-out shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
                <button
                    type="button"
                    onClick={() => setAcik(true)}
                    className="flex h-12 items-center justify-center text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors border-b border-white/5 group"
                    title="Paneli aç"
                >
                    <ChevronLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
                </button>
                <div className="flex flex-col gap-2 mt-2">
                    {SEKMELER.map((sekme) => {
                        const IkonComp = sekme.ikon;
                        const active = aktifSekme === sekme.id;
                        return (
                            <button
                                key={sekme.id}
                                type="button"
                                onClick={() => {
                                    setAktifSekme(sekme.id);
                                    setAcik(true);
                                }}
                                className={`flex h-10 w-10 mx-auto items-center justify-center rounded-lg transition-all duration-300 group ${
                                    active
                                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                                        : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200 border border-transparent hover:border-white/5'
                                }`}
                                title={sekme.etiket}
                            >
                                <IkonComp size={14} className={active ? 'drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]' : 'group-hover:scale-110 transition-transform'} />
                            </button>
                        );
                    })}
                </div>
            </aside>
        );
    }

    return (
        <aside className="flex w-80 shrink-0 flex-col border-l border-white/5 bg-slate-950/60 backdrop-blur-xl text-slate-100 shadow-[-10px_0_30px_rgba(0,0,0,0.5)] transition-all duration-500 ease-out z-10">
            <div className="flex items-center border-b border-white/5 bg-slate-950/40 relative">
                <div className="flex flex-1 overflow-x-auto px-2 scrollbar-none">
                    {SEKMELER.map((sekme) => {
                        const IkonComp = sekme.ikon;
                        const active = aktifSekme === sekme.id;
                        return (
                            <button
                                key={sekme.id}
                                type="button"
                                onClick={() => setAktifSekme(sekme.id)}
                                className={`flex items-center gap-1.5 px-3 py-3.5 text-[10px] font-bold uppercase tracking-widest transition-all relative group ${
                                    active
                                        ? 'text-blue-400'
                                        : 'text-slate-500 hover:text-slate-300'
                                }`}
                            >
                                <IkonComp size={13} className={active ? 'drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]' : 'group-hover:scale-110 transition-transform'} />
                                <span>{sekme.etiket}</span>
                                {active && (
                                    <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-blue-500 shadow-[0_-2px_8px_rgba(59,130,246,0.8)] rounded-t-full"></div>
                                )}
                            </button>
                        );
                    })}
                </div>
                <button
                    type="button"
                    onClick={() => setAcik(false)}
                    className="flex h-10 w-10 items-center justify-center text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors group"
                    title="Paneli daralt"
                >
                    <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-950/20">
                {aktifSekme === 'gorevler' && <GorevlerSekmesi />}
                {aktifSekme === 'robotlar' && <RobotlarSekmesi />}
                {aktifSekme === 'olaylar' && <OlaylarSekmesi />}
                {aktifSekme === 'test' && <TestPaneli />}
            </div>
        </aside>
    );
}
