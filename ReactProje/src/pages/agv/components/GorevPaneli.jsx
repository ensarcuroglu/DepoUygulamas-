/**
 * Sağ panel — sistem metrikleri, robot listesi, son olay akışı.
 *
 * Her satır kendi store slice'ına abone olur (RobotSatir kendi durumuna).
 * Panelin kendisi sadece tickNo + ozet metriklere bağımlı.
 */

import { useAgvStore } from '../../../stores/agvStore';

const DURUM_RENK = {
    Bos: 'text-gray-500',
    KaynagaGidiyor: 'text-amber-600',
    Yukluyor: 'text-orange-600',
    Tasiyor: 'text-emerald-600',
    Birakiyor: 'text-orange-600',
    TamamlandiBildirim: 'text-blue-600',
    HataDuruyor: 'text-red-600',
};

export default function GorevPaneli() {
    const tickNo = useAgvStore((s) => s.tickNo);
    const kuyruk = useAgvStore((s) => s.kuyrukUzunlugu);
    const aktif = useAgvStore((s) => s.aktifGorevSayisi);
    const robotIds = useAgvStore((s) => s.robotIds);
    const olaylar = useAgvStore((s) => s.sonOlaylar);

    return (
        <div className="flex h-full flex-col gap-3 overflow-y-auto p-3 text-sm">
            <Kart baslik="Sistem">
                <Satir etiket="Tick" deger={tickNo} />
                <Satir etiket="Kuyruk" deger={kuyruk} />
                <Satir etiket="Aktif görev" deger={aktif} />
            </Kart>

            <Kart baslik={`Robotlar (${robotIds.length})`}>
                {robotIds.length === 0 && (
                    <div className="text-xs text-gray-400">Henüz robot yok</div>
                )}
                {robotIds.map((id) => (
                    <RobotSatir key={id} robotId={id} />
                ))}
            </Kart>

            <Kart baslik="Son Olaylar">
                {olaylar.length === 0 && (
                    <div className="text-xs text-gray-400">Olay bekleniyor…</div>
                )}
                <ul className="space-y-1">
                    {olaylar.slice(0, 12).map((o, i) => (
                        <li key={`${o.ts}-${i}`} className="text-xs text-gray-600">
                            <span className="mr-1.5 font-mono text-gray-400">
                                {o.robot_id ?? '-'}
                            </span>
                            <span>{o.olay}</span>
                            {o.gorev_id && (
                                <span className="ml-1 text-gray-400">#{o.gorev_id}</span>
                            )}
                        </li>
                    ))}
                </ul>
            </Kart>
        </div>
    );
}

function RobotSatir({ robotId }) {
    const robot = useAgvStore((s) => s.robots[robotId]);
    if (!robot) return null;
    const renk = DURUM_RENK[robot.durum] ?? 'text-gray-500';
    return (
        <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-gray-700">{robot.id}</span>
            <span className={`font-medium ${renk}`}>{robot.durum}</span>
        </div>
    );
}

function Kart({ baslik, children }) {
    return (
        <div className="rounded-lg bg-white p-3 shadow-sm ring-1 ring-gray-200">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                {baslik}
            </h3>
            <div className="flex flex-col gap-1">{children}</div>
        </div>
    );
}

function Satir({ etiket, deger }) {
    return (
        <div className="flex justify-between text-xs">
            <span className="text-gray-500">{etiket}</span>
            <span className="font-mono text-gray-800">{deger}</span>
        </div>
    );
}
