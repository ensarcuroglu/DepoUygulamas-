import { useEffect, useRef } from 'react';

const EMPTY_IGNORED_INPUT_TYPES = Object.freeze([]);

/**
 * Fiziksel barkod okuyucu (Zebra DataWedge vb.) tuş vuruşlarını
 * window seviyesinde dinler ve hızlı yazılan karakter dizilerini
 * barkod taraması olarak algılar.
 *
 * Zebra DataWedge — Keyboard Wedge modu için optimize edilmiştir.
 * DataWedge "Send ENTER key" ayarı açık olmalıdır.
 *
 * @param {Object} options
 * @param {Function} options.onScan - Barkod başarıyla okunduğunda tetiklenir
 * @param {boolean}  options.isEnabled - Hook'un aktif olup olmadığı (default: true)
 * @param {number}   options.maxGap - İki tuş arası maks bekleme toleransı (ms).
 *                   Zebra Android WebView'da GC/rendering gecikmeleri nedeniyle
 *                   80ms yetersiz kalır. 150ms önerilir. (default: 150)
 * @param {number}   options.minLength - Barkod olarak kabul edilecek minimum
 *                   karakter uzunluğu. Kısa yanlış pozitifleri engeller. (default: 4)
 * @param {string[]} options.ignoredInputTypes - Hook'un devre dışı olacağı
 *                   aktif element türleri. Input fokuslu iken çift tetiklemeyi
 *                   engellemek için. (default: [])
 */
function useBarcodeScanner({
    onScan,
    isEnabled = true,
    maxGap = 150,
    minLength = 4,
    ignoredInputTypes = EMPTY_IGNORED_INPUT_TYPES,
}) {
    const bufferRef = useRef('');
    const lastKeyTimeRef = useRef(0);
    const onScanRef = useRef(onScan);
    const ignoredInputTypesRef = useRef(EMPTY_IGNORED_INPUT_TYPES);

    // onScan callback'ini ref ile güncel tut (stale closure önlemi)
    useEffect(() => {
        onScanRef.current = onScan;
    }, [onScan]);

    useEffect(() => {
        if (Array.isArray(ignoredInputTypes) && ignoredInputTypes.length > 0) {
            ignoredInputTypesRef.current = ignoredInputTypes.map((tag) => String(tag).toLowerCase());
            return;
        }
        ignoredInputTypesRef.current = EMPTY_IGNORED_INPUT_TYPES;
    }, [ignoredInputTypes]);

    useEffect(() => {
        if (!isEnabled) return;

        const handleKeyDown = (e) => {
            // ─── Aktif input/textarea kontrolü ───
            // Eğer fokus bu element tiplerinden birindeyse hook'u sustur
            // (Böylece input.onKeyDown ile çakışma önlenir)
            const ignoredTypes = ignoredInputTypesRef.current;
            if (ignoredTypes.length > 0) {
                const tag = document.activeElement?.tagName?.toLowerCase();
                if (tag && ignoredTypes.includes(tag)) {
                    return;
                }
            }

            const now = Date.now();

            // ─── Enter = "Okuma Bitti" sinyali ───
            if (e.key === 'Enter') {
                const code = bufferRef.current;
                if (code.length >= minLength) {
                    e.preventDefault();
                    e.stopPropagation();
                    onScanRef.current(code);
                }
                bufferRef.current = '';
                lastKeyTimeRef.current = 0;
                return;
            }

            // ─── Alfasayısal tuşları yakala ───
            // Shift, Ctrl, Alt vb. modifier tuşları yoksay (length === 1 kontrolü)
            if (e.key.length !== 1) return;

            // Önceki tuştan bu yana çok zaman geçmişse → insan yazması → sıfırla
            if (now - lastKeyTimeRef.current > maxGap) {
                bufferRef.current = e.key;
            } else {
                bufferRef.current += e.key;
            }
            lastKeyTimeRef.current = now;
        };

        window.addEventListener('keydown', handleKeyDown, true);

        return () => {
            window.removeEventListener('keydown', handleKeyDown, true);
            bufferRef.current = '';
            lastKeyTimeRef.current = 0;
        };
    }, [isEnabled, maxGap, minLength]);
}

export default useBarcodeScanner;
