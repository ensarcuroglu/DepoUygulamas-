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

const DURUM_RENK_TXT = {
    Bos: 'text-gray-500',
    KaynagaGidiyor: 'text-amber-600',
    Yukluyor: 'text-orange-600',
    Tasiyor: 'text-emerald-600',
    Birakiyor: 'text-orange-600',
    TamamlandiBildirim: 'text-blue-600',
    BeklemeYerineDonuyor: 'text-sky-600',
    HataDuruyor: 'text-red-600',
};

const PALET_DURUM_RENK = {
    KaynaktaBekliyor: 'bg-blue-100 text-blue-700',
    RobotUzerinde: 'bg-emerald-100 text-emerald-700',
    HedefteBirakildi: 'bg-purple-100 text-purple-700',
    Bilinmiyor: 'bg-gray-100 text-gray-700',
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
        <div className="flex flex-col gap-3 p-3">
            <Kart baslik={`Aktif görevler (${aktifGorevler.length}) · kuyruk: ${kuyruk}`}>
                {aktifGorevler.length === 0 && (
                    <div className="text-[11px] text-gray-400">Aktif görev yok</div>
                )}
                {aktifGorevler.map((g) => (
                    <div
                        key={g.gorev_id}
                        className="flex items-center justify-between rounded-md border border-gray-100 bg-white px-2 py-1.5 text-[11px]"
                    >
                        <div className="font-mono text-gray-700">
                            {g.robot_id ?? '—'}
                            <span className="ml-1 text-gray-400">
                                #{g.wms_gorev_id ?? g.gorev_id}
                            </span>
                        </div>
                        <span className="text-gray-500">
                            {g.kaynak_raf_id} → {g.hedef_raf_id}
                        </span>
                    </div>
                ))}
            </Kart>

            <Kart baslik={`Paletler (${paletKeys.length})`}>
                {paletKeys.length === 0 && (
                    <div className="text-[11px] text-gray-400">Palet yok</div>
                )}
                {paletKeys.map((k) => {
                    const p = paletler[k];
                    if (!p) return null;
                    return (
                        <div
                            key={k}
                            className="flex items-center justify-between rounded-md border border-gray-100 bg-white px-2 py-1.5 text-[11px]"
                        >
                            <span className="font-mono text-gray-700">
                                {p.palet_id ? `#${p.palet_id}` : p.palet_key}
                            </span>
                            <span
                                className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                                    PALET_DURUM_RENK[p.durum] ??
                                    'bg-gray-100 text-gray-700'
                                }`}
                            >
                                {p.durum}
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
    const renk = DURUM_RENK_TXT[robot.durum] ?? 'text-gray-500';
    const batarya = robot.batarya ?? 100;
    const bataryaRenk =
        batarya < 20 ? 'bg-red-500' : batarya < 50 ? 'bg-amber-400' : 'bg-emerald-500';
    return (
        <button
            type="button"
            onClick={() => setSelectedRobotId(selected ? null : robotId)}
            className={`flex w-full items-center justify-between gap-2 rounded-md border px-2 py-1.5 text-left text-[11px] transition ${
                selected
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-100 bg-white hover:border-blue-200'
            }`}
        >
            <span className="font-mono text-gray-700">
                {robot.id}
                {robot.sarja_donuyor && (
                    <span className="ml-1 text-[10px] text-amber-600">⚡</span>
                )}
            </span>
            <div className="flex items-center gap-1.5">
                <div className="h-1 w-10 overflow-hidden rounded-full bg-gray-200">
                    <div
                        className={`h-full ${bataryaRenk}`}
                        style={{ width: `${batarya}%` }}
                    />
                </div>
                <span className={`text-[10px] font-medium ${renk}`}>
                    {robot.durum}
                </span>
            </div>
        </button>
    );
}

function RobotlarSekmesi() {
    const robotIds = useAgvStore((s) => s.robotIds);
    return (
        <div className="flex flex-col gap-3 p-3">
            <Kart baslik={`Robotlar (${robotIds.length})`}>
                {robotIds.length === 0 && (
                    <div className="text-[11px] text-gray-400">Henüz robot yok</div>
                )}
                <div className="flex flex-col gap-1">
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
        <div className="flex flex-col gap-3 p-3">
            <Kart baslik={`Son olaylar (${olaylar.length})`}>
                {olaylar.length === 0 && (
                    <div className="text-[11px] text-gray-400">Olay bekleniyor…</div>
                )}
                <ul className="space-y-1">
                    {olaylar.slice(0, 30).map((o, i) => (
                        <li
                            key={`${o.ts}-${i}`}
                            className="flex items-center gap-1.5 rounded-md border border-gray-100 bg-white px-2 py-1 text-[11px]"
                        >
                            <span className="font-mono text-gray-400">
                                {o.robot_id ?? '-'}
                            </span>
                            <span className="text-gray-700">{o.olay}</span>
                            {o.gorev_id && (
                                <span className="ml-auto text-gray-400">
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
        <div className="rounded-lg bg-white p-2.5 shadow-sm ring-1 ring-gray-200">
            <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                {baslik}
            </h3>
            <div className="flex flex-col gap-1">{children}</div>
        </div>
    );
}

export default function YanSekmePaneli() {
    const [aktifSekme, setAktifSekme] = useState('gorevler');
    const [acik, setAcik] = useState(true);

    if (!acik) {
        return (
            <aside className="flex w-10 shrink-0 flex-col border-l border-gray-200 bg-gray-50">
                <button
                    type="button"
                    onClick={() => setAcik(true)}
                    className="flex h-10 items-center justify-center text-gray-500 hover:bg-gray-100"
                    title="Paneli aç"
                >
                    <ChevronLeft size={16} />
                </button>
                {SEKMELER.map((sekme) => {
                    const IkonComp = sekme.ikon;
                    return (
                        <button
                            key={sekme.id}
                            type="button"
                            onClick={() => {
                                setAktifSekme(sekme.id);
                                setAcik(true);
                            }}
                            className="flex h-10 items-center justify-center text-gray-500 hover:bg-gray-100"
                            title={sekme.etiket}
                        >
                            <IkonComp size={14} />
                        </button>
                    );
                })}
            </aside>
        );
    }

    return (
        <aside className="flex w-80 shrink-0 flex-col border-l border-gray-200 bg-gray-50">
            <div className="flex items-center border-b border-gray-200 bg-white">
                <div className="flex flex-1 overflow-x-auto">
                    {SEKMELER.map((sekme) => {
                        const IkonComp = sekme.ikon;
                        return (
                            <button
                                key={sekme.id}
                                type="button"
                                onClick={() => setAktifSekme(sekme.id)}
                                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition ${
                                    aktifSekme === sekme.id
                                        ? 'border-b-2 border-blue-600 text-blue-700'
                                        : 'text-gray-500 hover:text-gray-800'
                                }`}
                            >
                                <IkonComp size={13} />
                                {sekme.etiket}
                            </button>
                        );
                    })}
                </div>
                <button
                    type="button"
                    onClick={() => setAcik(false)}
                    className="flex h-9 w-9 items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                    title="Paneli daralt"
                >
                    <ChevronRight size={16} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {aktifSekme === 'gorevler' && <GorevlerSekmesi />}
                {aktifSekme === 'robotlar' && <RobotlarSekmesi />}
                {aktifSekme === 'olaylar' && <OlaylarSekmesi />}
                {aktifSekme === 'test' && <TestPaneli />}
            </div>
        </aside>
    );
}
