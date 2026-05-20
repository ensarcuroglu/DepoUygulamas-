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
            className={`group flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-all duration-300 ${
                isPending
                    ? 'border-slate-850 bg-slate-900/10 opacity-50 cursor-not-allowed'
                    : 'border-slate-800 bg-slate-950/40 hover:border-slate-700/60 hover:bg-slate-900/30 hover:shadow-[0_0_10px_rgba(59,130,246,0.05)]'
            }`}
        >
            <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-300 ${renk}`}
            >
                {isPending ? (
                    <Loader2 size={15} className="animate-spin text-slate-400" />
                ) : (
                    <IkonComp size={15} className="transition-transform duration-300 group-hover:scale-110" />
                )}
            </div>
            <div className="flex-1">
                <div className="text-xs font-bold text-slate-200 group-hover:text-white transition-colors">{baslik}</div>
                <div className="mt-0.5 text-[10px] leading-relaxed text-slate-400">{aciklama}</div>
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
        <div className="flex flex-col gap-4 p-4">
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-[10px] leading-relaxed text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.05)]">
                <strong>Demo / Test Modu.</strong> Bu senaryolar AGV simülasyonunu
                doğrudan etkiler. Görev callback'leri WMS'te orphan kalabilir.
            </div>

            <div className="grid grid-cols-1 gap-2.5">
                <Senaryo
                    baslik="Test Görevi Oluştur"
                    aciklama="Rastgele kaynak/hedef raf çifti ile bir görev ekler."
                    ikon={PackagePlus}
                    renk="bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    onClick={() => gorevMut.mutate()}
                    isPending={gorevMut.isPending}
                />

                <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 hover:border-slate-800/80 transition-all duration-200">
                    <div className="mb-1.5 flex items-center gap-2 text-xs font-bold text-slate-200">
                        <Truck size={14} className="text-violet-400 border-none bg-transparent" />
                        Yoğun Trafik Senaryosu
                    </div>
                    <p className="text-[10px] leading-relaxed text-slate-400">
                        Birden fazla görev kuyruğa ekler — paralel rota planlama testi.
                    </p>
                    <div className="mt-2.5 flex items-center gap-2">
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
                            className="w-16 rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-200 font-mono font-bold focus:outline-none focus:border-blue-500/50"
                        />
                        <button
                            type="button"
                            onClick={() => trafikMut.mutate(trafikSayisi)}
                            disabled={trafikMut.isPending}
                            className="flex-1 rounded-md bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 px-3 py-1.5 text-xs font-bold text-white transition-all shadow-[0_0_12px_rgba(109,40,217,0.15)] hover:shadow-[0_0_16px_rgba(109,40,217,0.25)] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {trafikMut.isPending ? 'Başlatılıyor…' : 'Senaryoyu Başlat'}
                        </button>
                    </div>
                </div>

                <Senaryo
                    baslik="Düşük Batarya"
                    aciklama="İlk robotun bataryasını %18'e çeker — otonom şarja dönüş tetiklenir."
                    ikon={BatteryLow}
                    renk="bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    onClick={() => bataryaMut.mutate()}
                    isPending={bataryaMut.isPending}
                />

                <Senaryo
                    baslik="Robot Arızası"
                    aciklama="Bir robotu HataDuruyor durumuna düşürür."
                    ikon={AlertTriangle}
                    renk="bg-red-500/10 text-red-400 border border-red-500/20"
                    onClick={() => arizaMut.mutate()}
                    isPending={arizaMut.isPending}
                />

                <Senaryo
                    baslik="Deadlock Senaryosu"
                    aciklama="Karşılıklı iki görev — kooperatif rota çözümü testi."
                    ikon={GitBranch}
                    renk="bg-purple-500/10 text-purple-400 border border-purple-500/20"
                    onClick={() => deadlockMut.mutate()}
                    isPending={deadlockMut.isPending}
                />

                <Senaryo
                    baslik={duraklatildi ? 'Devam Ettir' : 'Simülasyonu Duraklat'}
                    aciklama={
                        duraklatildi
                            ? 'Tick loop yeniden başlatılır.'
                            : 'Tick loop durdurulur — bağlantı açık kalır.'
                    }
                    ikon={duraklatildi ? Play : Pause}
                    renk={
                        duraklatildi
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-slate-800 text-slate-300 border border-slate-700/50'
                    }
                    onClick={() => duraklatMut.mutate()}
                    isPending={duraklatMut.isPending}
                />

                <Senaryo
                    baslik="Simülasyonu Sıfırla"
                    aciklama="Görevleri ve paletleri temizler, robotları boşa düşürür."
                    ikon={RotateCcw}
                    renk="bg-slate-800 text-slate-300 border border-slate-750"
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
                <div className="rounded-lg bg-slate-900/50 border border-slate-800 p-3 text-[10px] text-slate-400 text-center font-medium">
                    Henüz robot yok — backend bağlantısı bekleniyor.
                </div>
            )}

            {sonSonuc && (
                <div
                    className={`mt-1.5 rounded-lg p-3 text-[10px] border transition-all duration-300 ${
                        sonSonuc.tip === 'ok'
                            ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.06)]'
                            : 'bg-red-950/20 text-red-400 border-red-500/30 shadow-[0_0_12px_rgba(239,68,68,0.06)] animate-pulse'
                    }`}
                >
                    <div className="font-bold flex items-center gap-1.5">
                        <span className={`h-1.5 w-1.5 rounded-full ${sonSonuc.tip === 'ok' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                        {sonSonuc.label}
                    </div>
                    <pre className="mt-2 max-h-28 overflow-auto whitespace-pre-wrap break-all font-mono text-[9px] bg-black/35 p-2 rounded border border-slate-900 text-slate-300 leading-relaxed scrollbar-thin">
                        {typeof sonSonuc.data === 'string'
                            ? sonSonuc.data
                            : JSON.stringify(sonSonuc.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
