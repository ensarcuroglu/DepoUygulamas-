/**
 * BelgeKameraOverlay — Mobil terminal için tam ekran belge çekim arayüzü.
 *
 * Tasarım notları:
 *  - position:fixed inset-0; TerminalLayout scroll/nav etkisini bypass eder.
 *  - Video feed object-cover ile ekranı kaplar; üstüne rule-of-thirds + A4
 *    çerçeve overlay'i çizilir (operatöre belgeyi nereye hizalayacağını söyler).
 *  - Shutter butonu büyük (saha eldiveni dostu, 88x88).
 *  - Torch ve iptal butonları safe-area-inset boşluğuna saygı duyar.
 *  - Hata/permission denied durumunda yumuşak fallback ekran.
 */
import { useEffect } from 'react';
import { motion as Motion } from 'framer-motion';
import { Camera, Flashlight, FlashlightOff, Loader2, X, ShieldAlert, RefreshCcw } from 'lucide-react';
import useDocumentCapture from '../../hooks/useDocumentCapture';

const errorMessage = (error) => {
    if (!error) return 'Kameraya erişilemedi.';
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        return 'Kamera izni reddedildi. Tarayıcı ayarlarından izin verin.';
    }
    if (error.name === 'NotFoundError' || error.name === 'OverconstrainedError') {
        return 'Bu cihazda arka kamera bulunamadı.';
    }
    if (error.name === 'NotReadableError') {
        return 'Kamera başka bir uygulama tarafından kullanılıyor.';
    }
    return error.message || 'Kameraya erişilemedi.';
};

export default function BelgeKameraOverlay({ open, onCapture, onClose, captureLabel = 'Belgeyi Çek' }) {
    const {
        videoRef,
        isReady,
        isStarting,
        error,
        torchOn,
        torchSupported,
        capture,
        toggleTorch,
        start,
    } = useDocumentCapture({ enabled: open });

    useEffect(() => {
        if (!open) return undefined;
        const previous = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = previous;
        };
    }, [open]);

    const handleShutter = async () => {
        try {
            const result = await capture();
            await onCapture?.(result);
        } catch {
            // capture() yalnızca kamera hazır değilken hata atar; sessizce yoksay.
        }
    };

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black text-white select-none">
            {/* Canlı kamera feed'i */}
            <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="absolute inset-0 h-full w-full object-cover"
            />

            {/* Karartma / vinyet */}
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60" />

            {/* Belge çerçeve overlay'i (4 köşe L şekli) */}
            <DocumentFrame />

            {/* Üst aksiyonlar — safe area */}
            <div className="absolute inset-x-0 top-0 z-10 flex items-center justify-between px-4 pt-[max(env(safe-area-inset-top),1rem)]">
                <button
                    type="button"
                    onClick={onClose}
                    aria-label="Kamerayı kapat"
                    className="flex h-12 w-12 items-center justify-center rounded-full bg-black/55 text-white backdrop-blur-md transition active:scale-90"
                >
                    <X className="h-6 w-6" strokeWidth={2.5} />
                </button>

                {torchSupported ? (
                    <button
                        type="button"
                        onClick={toggleTorch}
                        aria-label={torchOn ? 'Feneri kapat' : 'Feneri aç'}
                        className={`flex h-12 w-12 items-center justify-center rounded-full backdrop-blur-md transition active:scale-90 ${
                            torchOn ? 'bg-amber-400 text-black' : 'bg-black/55 text-white'
                        }`}
                    >
                        {torchOn ? <Flashlight className="h-6 w-6" /> : <FlashlightOff className="h-6 w-6" />}
                    </button>
                ) : <span className="h-12 w-12" aria-hidden="true" />}
            </div>

            {/* Yardım metni */}
            <div className="absolute inset-x-0 top-[max(env(safe-area-inset-top),1rem)] z-0 mt-20 flex justify-center px-6 text-center">
                <p className="rounded-full bg-black/55 px-4 py-1.5 text-[12px] font-semibold tracking-wide text-white/95 backdrop-blur-md">
                    Belgeyi çerçevenin içine hizalayın
                </p>
            </div>

            {/* Alt aksiyonlar */}
            <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col items-center gap-3 px-6 pb-[max(env(safe-area-inset-bottom),1.25rem)]">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/70">
                    {captureLabel}
                </p>
                <Motion.button
                    type="button"
                    onClick={handleShutter}
                    disabled={!isReady}
                    whileTap={{ scale: 0.92 }}
                    aria-label="Fotoğraf çek"
                    className="relative flex h-[88px] w-[88px] items-center justify-center rounded-full border-[5px] border-white/95 bg-white/15 backdrop-blur-md transition disabled:opacity-50"
                >
                    <span className={`h-[64px] w-[64px] rounded-full transition ${
                        isReady ? 'bg-white' : 'bg-white/40'
                    }`} />
                    {!isReady && (
                        <Loader2 className="absolute h-7 w-7 animate-spin text-white" />
                    )}
                </Motion.button>
            </div>

            {/* Yüklenme / hata katmanları */}
            {(isStarting && !isReady && !error) && (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-black/70 text-white">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <p className="text-sm font-semibold">Kamera başlatılıyor…</p>
                </div>
            )}

            {error && (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 bg-black/85 px-6 text-center text-white">
                    <div className="rounded-full bg-rose-500/15 p-4 ring-1 ring-rose-400/40">
                        <ShieldAlert className="h-8 w-8 text-rose-300" />
                    </div>
                    <p className="max-w-xs text-sm font-semibold text-white/90">
                        {errorMessage(error)}
                    </p>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={() => start()}
                            className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-bold text-black transition active:scale-95"
                        >
                            <RefreshCcw className="h-4 w-4" />
                            Tekrar dene
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="inline-flex items-center gap-2 rounded-full border border-white/30 px-4 py-2 text-sm font-bold text-white transition active:scale-95"
                        >
                            <X className="h-4 w-4" />
                            Kapat
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

function DocumentFrame() {
    return (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            {/* A4-vari oran (≈1:1.41), ekranın yaklaşık %80'i */}
            <div className="relative h-[68%] w-[82%] max-w-[480px]">
                <CornerMark className="-left-1 -top-1" />
                <CornerMark className="-right-1 -top-1 rotate-90" />
                <CornerMark className="-left-1 -bottom-1 -rotate-90" />
                <CornerMark className="-right-1 -bottom-1 rotate-180" />

                {/* Hafif iç vurgu — operatör gözünü çerçeveye çeker */}
                <div className="absolute inset-0 rounded-2xl ring-1 ring-white/15 shadow-[0_0_0_9999px_rgba(0,0,0,0.25)]" />

                <div className="absolute inset-0 flex items-center justify-center">
                    <Camera className="h-9 w-9 text-white/40" strokeWidth={1.5} />
                </div>
            </div>
        </div>
    );
}

function CornerMark({ className = '' }) {
    return (
        <span className={`absolute h-9 w-9 ${className}`} aria-hidden="true">
            <span className="absolute left-0 top-0 h-1 w-9 rounded-full bg-emerald-400" />
            <span className="absolute left-0 top-0 h-9 w-1 rounded-full bg-emerald-400" />
        </span>
    );
}
