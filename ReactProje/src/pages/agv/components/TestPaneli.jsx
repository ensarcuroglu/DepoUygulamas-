/**
 * Simülasyon Test Paneli — AgvSimService `/api/agv/test/*` endpoint'lerine
 * bağlı butonlarla senaryo tetikler. Demo/test modunda çalışır
 * (backend `AGV_TEST_PANEL_ENABLED=true`).
 */

import { useMutation } from '@tanstack/react-query';
import {
    PackagePlus,
    Truck,
    BatteryLow,
    AlertTriangle,
    GitBranch,
    Pause,
    Play,
    RotateCcw,
    Loader2,
} from 'lucide-react';
import { useState } from 'react';

import { agvApi } from '../../../services/agvApi';
import { useAgvStore } from '../../../stores/agvStore';

function Senaryo(props) {
    const { baslik, aciklama, ikon: IkonComp, renk, onClick, isPending } = props;
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={isPending}
            className={`group flex w-full items-start gap-2.5 rounded-lg border bg-white p-2.5 text-left transition hover:shadow-sm ${
                isPending
                    ? 'border-gray-200 opacity-60'
                    : 'border-gray-200 hover:border-blue-300'
            }`}
        >
            <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${renk}`}
            >
                {isPending ? (
                    <Loader2 size={16} className="animate-spin" />
                ) : (
                    <IkonComp size={16} />
                )}
            </div>
            <div className="flex-1">
                <div className="text-xs font-semibold text-gray-800">{baslik}</div>
                <div className="mt-0.5 text-[11px] text-gray-500">{aciklama}</div>
            </div>
        </button>
    );
}

export default function TestPaneli() {
    const duraklatildi = useAgvStore((s) => s.duraklatildi);
    const robotIds = useAgvStore((s) => s.robotIds);
    const [sonSonuc, setSonSonuc] = useState(null);
    const [trafikSayisi, setTrafikSayisi] = useState(8);

    function ileBitince(label) {
        return (data) => setSonSonuc({ tip: 'ok', label, data });
    }
    function ileHata(label) {
        return (err) =>
            setSonSonuc({
                tip: 'hata',
                label,
                data: err?.response?.data?.detail ?? String(err?.message ?? err),
            });
    }

    const gorevMut = useMutation({
        mutationFn: () => agvApi.test.gorev(),
        onSuccess: ileBitince('Görev oluşturuldu'),
        onError: ileHata('Görev oluşturulamadı'),
    });
    const trafikMut = useMutation({
        mutationFn: (n) => agvApi.test.yogunTrafik(n),
        onSuccess: ileBitince('Yoğun trafik başlatıldı'),
        onError: ileHata('Yoğun trafik başlatılamadı'),
    });
    const bataryaMut = useMutation({
        mutationFn: () => agvApi.test.dusukBatarya({ seviye: 18 }),
        onSuccess: ileBitince('Düşük batarya tetiklendi'),
        onError: ileHata('Düşük batarya başarısız'),
    });
    const arizaMut = useMutation({
        mutationFn: () => agvApi.test.robotAriza({}),
        onSuccess: ileBitince('Robot arızası tetiklendi'),
        onError: ileHata('Robot arızası başarısız'),
    });
    const deadlockMut = useMutation({
        mutationFn: () => agvApi.test.deadlock(),
        onSuccess: ileBitince('Deadlock senaryosu başladı'),
        onError: ileHata('Deadlock başlatılamadı'),
    });
    const duraklatMut = useMutation({
        mutationFn: () =>
            duraklatildi ? agvApi.test.devam() : agvApi.test.duraklat(),
        onSuccess: ileBitince(duraklatildi ? 'Devam ettirildi' : 'Duraklatıldı'),
        onError: ileHata('Sim durum değiştirilemedi'),
    });
    const sifirlaMut = useMutation({
        mutationFn: () => agvApi.test.sifirla(),
        onSuccess: ileBitince('Simülasyon sıfırlandı'),
        onError: ileHata('Sıfırlama başarısız'),
    });

    return (
        <div className="flex flex-col gap-3 p-3">
            <div className="rounded-lg bg-amber-50 p-2.5 text-[11px] text-amber-800 ring-1 ring-amber-200">
                <strong>Demo / test modu.</strong> Bu senaryolar AGV simülasyonunu
                doğrudan etkiler. Görev callback'leri WMS'te orphan kalabilir.
            </div>

            <div className="grid grid-cols-1 gap-2">
                <Senaryo
                    baslik="Test görevi oluştur"
                    aciklama="Rastgele kaynak/hedef raf çifti ile bir görev ekler."
                    ikon={PackagePlus}
                    renk="bg-blue-100 text-blue-700"
                    onClick={() => gorevMut.mutate()}
                    isPending={gorevMut.isPending}
                />

                <div className="rounded-lg border border-gray-200 bg-white p-2.5">
                    <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-gray-800">
                        <Truck size={14} className="text-violet-700" />
                        Yoğun trafik
                    </div>
                    <p className="text-[11px] text-gray-500">
                        Birden fazla görev kuyruğa ekler — paralel rota planlama testi.
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                        <input
                            type="number"
                            min={1}
                            max={50}
                            value={trafikSayisi}
                            onChange={(e) =>
                                setTrafikSayisi(
                                    Math.max(1, Math.min(50, Number(e.target.value) || 1))
                                )
                            }
                            className="w-16 rounded-md border border-gray-300 px-2 py-1 text-xs"
                        />
                        <button
                            type="button"
                            onClick={() => trafikMut.mutate(trafikSayisi)}
                            disabled={trafikMut.isPending}
                            className="flex-1 rounded-md bg-violet-600 px-2 py-1 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50"
                        >
                            {trafikMut.isPending ? 'Başlatılıyor…' : 'Başlat'}
                        </button>
                    </div>
                </div>

                <Senaryo
                    baslik="Düşük batarya"
                    aciklama="İlk robotun bataryasını %18'e çeker — otonom şarja dönüş tetiklenir."
                    ikon={BatteryLow}
                    renk="bg-amber-100 text-amber-700"
                    onClick={() => bataryaMut.mutate()}
                    isPending={bataryaMut.isPending}
                />

                <Senaryo
                    baslik="Robot arızası"
                    aciklama="Bir robotu HATA_DURUYOR durumuna düşürür."
                    ikon={AlertTriangle}
                    renk="bg-red-100 text-red-700"
                    onClick={() => arizaMut.mutate()}
                    isPending={arizaMut.isPending}
                />

                <Senaryo
                    baslik="Deadlock senaryosu"
                    aciklama="Karşılıklı iki görev — kooperatif rota çözümü testi."
                    ikon={GitBranch}
                    renk="bg-purple-100 text-purple-700"
                    onClick={() => deadlockMut.mutate()}
                    isPending={deadlockMut.isPending}
                />

                <Senaryo
                    baslik={duraklatildi ? 'Devam ettir' : 'Simülasyonu duraklat'}
                    aciklama={
                        duraklatildi
                            ? 'Tick loop yeniden başlatılır.'
                            : 'Tick loop durdurulur — bağlantı açık kalır.'
                    }
                    ikon={duraklatildi ? Play : Pause}
                    renk={
                        duraklatildi
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-slate-100 text-slate-700'
                    }
                    onClick={() => duraklatMut.mutate()}
                    isPending={duraklatMut.isPending}
                />

                <Senaryo
                    baslik="Simülasyonu sıfırla"
                    aciklama="Görevleri ve paletleri temizler, robotları boşa düşürür."
                    ikon={RotateCcw}
                    renk="bg-slate-100 text-slate-700"
                    onClick={() => {
                        if (
                            window.confirm(
                                'Tüm görev ve paletler temizlenecek. Devam edilsin mi?'
                            )
                        )
                            sifirlaMut.mutate();
                    }}
                    isPending={sifirlaMut.isPending}
                />
            </div>

            {robotIds.length === 0 && (
                <div className="rounded-md bg-slate-50 px-2 py-1.5 text-[11px] text-slate-500 ring-1 ring-slate-200">
                    Henüz robot yok — backend bağlantısı bekleniyor.
                </div>
            )}

            {sonSonuc && (
                <div
                    className={`mt-1 rounded-md p-2 text-[11px] ring-1 ${
                        sonSonuc.tip === 'ok'
                            ? 'bg-emerald-50 text-emerald-800 ring-emerald-200'
                            : 'bg-red-50 text-red-800 ring-red-200'
                    }`}
                >
                    <div className="font-semibold">{sonSonuc.label}</div>
                    <pre className="mt-1 max-h-24 overflow-auto whitespace-pre-wrap break-all font-mono text-[10px]">
                        {typeof sonSonuc.data === 'string'
                            ? sonSonuc.data
                            : JSON.stringify(sonSonuc.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
