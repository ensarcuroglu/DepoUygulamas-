import { useEffect, useCallback, useRef } from 'react';

/**
 * Klavye vuruşlarını arka planda dinleyerek,
 * çok hızlı yazılan tuşları (fiziksel barkod okuyucu cihazlardan gelen)
 * algılar ve tarama sonucu olarak döner.
 *
 * @param {Function} onScan - Barkod başarıyla okunduğunda tetiklenecek callback
 * @param {boolean} isEnabled - Hook'un aktif olup olmadığını kontrol eder (default: true)
 * @param {number} maxTimeBetweenClicks - Okuyucunun iki tuş arası bekleme toleransı (ms)
 */
function useBarcodeScanner({ onScan, isEnabled = true, maxTimeBetweenClicks = 80 }) {
    const barcodeStrRef = useRef('');
    const lastKeyPressTimeRef = useRef(0);
    const onScanRef = useRef(onScan);

    // onScan callback'ini ref ile güncel tut (stale closure önlemi)
    useEffect(() => {
        onScanRef.current = onScan;
    }, [onScan]);

    const handleKeyPress = useCallback(
        (e) => {
            // Hook devre dışıysa hiçbir şey yapma
            if (!isEnabled) return;

            const currentTime = Date.now();

            // Enter tuşu "Okuma Bitti" sinyalidir
            if (e.key === 'Enter') {
                if (barcodeStrRef.current.length > 3) {
                    // Çok kısa kelimeleri barkod sanmaması için min uzunluk sınırı
                    e.preventDefault(); // Enter'ın form submit etmesini engelle
                    onScanRef.current(barcodeStrRef.current);
                }
                barcodeStrRef.current = '';
                return;
            }

            // Alfasayısal tuşları yakala (Shift vb. tuşları görmezden gelmek için length === 1 kontrolü)
            if (e.key.length === 1) {
                // Eğer önceki tuştan bu yana çok zaman geçmişse (insan yazması), stringi sıfırla
                if (currentTime - lastKeyPressTimeRef.current > maxTimeBetweenClicks) {
                    barcodeStrRef.current = e.key;
                } else {
                    // Hızlı yazılıyorsa (makine) karakterleri birleştir
                    barcodeStrRef.current += e.key;
                }
                lastKeyPressTimeRef.current = currentTime;
            }
        },
        [isEnabled, maxTimeBetweenClicks]
    );

    useEffect(() => {
        if (!isEnabled) return;

        // Window 'keydown' eventini dinliyoruz
        window.addEventListener('keydown', handleKeyPress);

        return () => {
            window.removeEventListener('keydown', handleKeyPress);
            // Cleanup: Buffer'ı temizle
            barcodeStrRef.current = '';
        };
    }, [handleKeyPress, isEnabled]);
}

export default useBarcodeScanner;
