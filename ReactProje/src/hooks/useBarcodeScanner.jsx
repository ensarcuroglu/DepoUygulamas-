import { useEffect, useCallback, useRef } from 'react';

/**
 * Klavye vuruşlarını arka planda dinleyerek,
 * çok hızlı yazılan tuşları (fiziksel barkod okuyucu cihazlardan gelen)
 * algılar ve tarama sonucu olarak döner.
 *
 * @param {Function} onScan - Barkod başarıyla okunduğunda tetiklenecek callback (okunan kodu parametre alır)
 * @param {number} maxTimeBetweenClicks - Okuyucunun iki tuş arası bekleme toleransı (ms). İnsan yazmasını engellemek için düşük tutulur.
 */
function useBarcodeScanner({ onScan, maxTimeBetweenClicks = 50 }) {
    const barcodeStrRef = useRef('');
    const lastKeyPressTimeRef = useRef(0);

    const handleKeyPress = useCallback(
        (e) => {
            // Input veya textarea alanındayken global okumayı ezme
            // (Kullanıcı arama kutusuna kendi eliyle yazıyor olabilir)
            if (
                e.target.tagName.toLowerCase() === 'input' ||
                e.target.tagName.toLowerCase() === 'textarea' ||
                e.target.isContentEditable
            ) {
                return;
            }

            const currentTime = Date.now();

            // Enter tuşu "Okuma Bitti" sinyalidir
            if (e.key === 'Enter') {
                if (barcodeStrRef.current.length > 3) {
                    // Çok kısa kelimeleri barkod sanmaması için min uzunluk sınırı
                    onScan(barcodeStrRef.current);
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
        [onScan, maxTimeBetweenClicks]
    );

    useEffect(() => {
        // Window 'keydown' eventini dinliyoruz
        window.addEventListener('keydown', handleKeyPress);

        return () => {
            window.removeEventListener('keydown', handleKeyPress);
        };
    }, [handleKeyPress]);
}

export default useBarcodeScanner;
