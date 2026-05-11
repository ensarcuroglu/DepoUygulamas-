/**
 * useDocumentCapture — Mobil terminalde belge fotoğrafı çekmek için kullanılır.
 *
 * Sorumluluk:
 *  - getUserMedia ile arka kamerayı (environment) açar.
 *  - <video> ref'ine stream'i bağlar, hazır olunca isReady=true yapar.
 *  - capture() çağrısıyla mevcut frame'i offscreen canvas'a çizip Blob döner.
 *  - Mümkünse torch (fener) kontrolünü açar/kapatır.
 *  - Unmount veya stop() çağrısında track'leri serbest bırakır.
 *
 * Not: HTTPS gerektirir (mkcert ile dev server zaten https). PWA içinde
 * iOS Safari için inline video oynatabilmek için playsInline + muted şarttır.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

const CAPTURE_MIME = 'image/jpeg';
const CAPTURE_QUALITY = 0.92;

const stopStream = (stream) => {
    if (!stream) return;
    for (const track of stream.getTracks()) {
        try { track.stop(); } catch { /* ignore */ }
    }
};

export function useDocumentCapture({ enabled = true } = {}) {
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [error, setError] = useState(null);
    const [torchOn, setTorchOn] = useState(false);
    const [torchSupported, setTorchSupported] = useState(false);

    const stop = useCallback(() => {
        stopStream(streamRef.current);
        streamRef.current = null;
        if (videoRef.current) {
            try { videoRef.current.srcObject = null; } catch { /* ignore */ }
        }
        setIsReady(false);
        setTorchOn(false);
        setTorchSupported(false);
    }, []);

    const start = useCallback(async () => {
        if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
            setError(new Error('Kameraya erişilemiyor. Tarayıcı desteklemiyor.'));
            return;
        }

        setIsStarting(true);
        setError(null);
        try {
            stopStream(streamRef.current);
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: false,
                video: {
                    facingMode: { ideal: 'environment' },
                    width: { ideal: 1920 },
                    height: { ideal: 1440 },
                },
            });
            streamRef.current = stream;

            const [track] = stream.getVideoTracks();
            const capabilities = typeof track?.getCapabilities === 'function'
                ? track.getCapabilities()
                : {};
            setTorchSupported(Boolean(capabilities?.torch));

            const video = videoRef.current;
            if (video) {
                video.srcObject = stream;
                video.setAttribute('playsinline', 'true');
                video.muted = true;
                try { await video.play(); } catch { /* autoplay engellenirse kullanıcı dokunduğunda başlayacak */ }
                setIsReady(true);
            }
        } catch (err) {
            setError(err);
            stopStream(streamRef.current);
            streamRef.current = null;
        } finally {
            setIsStarting(false);
        }
    }, []);

    const toggleTorch = useCallback(async () => {
        const stream = streamRef.current;
        if (!stream) return;
        const [track] = stream.getVideoTracks();
        if (!track || typeof track.applyConstraints !== 'function') return;

        const next = !torchOn;
        try {
            await track.applyConstraints({ advanced: [{ torch: next }] });
            setTorchOn(next);
        } catch {
            setTorchSupported(false);
        }
    }, [torchOn]);

    const capture = useCallback(async () => {
        const video = videoRef.current;
        if (!video || !video.videoWidth || !video.videoHeight) {
            throw new Error('Kamera henüz hazır değil.');
        }

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise((resolve, reject) => {
            canvas.toBlob(
                (b) => (b ? resolve(b) : reject(new Error('Fotoğraf oluşturulamadı.'))),
                CAPTURE_MIME,
                CAPTURE_QUALITY,
            );
        });

        return {
            blob,
            width: canvas.width,
            height: canvas.height,
            mimeType: CAPTURE_MIME,
        };
    }, []);

    useEffect(() => {
        if (!enabled) return undefined;
        let cancelled = false;
        // Microtask defer: setIsStarting/setError çağrılarını effect body'nin
        // senkron fazından sonra çalıştırır (react-hooks/set-state-in-effect).
        Promise.resolve().then(() => {
            if (!cancelled) void start();
        });
        return () => {
            cancelled = true;
            stop();
        };
    }, [enabled, start, stop]);

    return {
        videoRef,
        isReady,
        isStarting,
        error,
        torchOn,
        torchSupported,
        start,
        stop,
        capture,
        toggleTorch,
    };
}

export default useDocumentCapture;
