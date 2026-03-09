/**
 * API hata yanıtlarından tutarlı biçimde mesaj üretir.
 *
 * Öncelik sırası:
 *   1. FastAPI'nin döndürdüğü `detail` alanı  (en yaygın)
 *   2. Genel `message` alanı
 *   3. Ağ/timeout gibi JS hatalarının mesajı (ekrana "Network Error" gibi teknik ifadeler çıkmaması için filtre var)
 *   4. Çağırırken verilen `varsayilan` değer
 *
 * @param {unknown} err         - Axios veya JS hatası
 * @param {string}  varsayilan  - Hiçbir detay bulunamazsa gösterilecek mesaj
 * @returns {string}
 */
export function hataMetni(err, varsayilan = 'Beklenmeyen bir hata oluştu') {
    const detail = err?.response?.data?.detail;
    if (detail) {
        // FastAPI bazen detail'i dizi olarak döner (validation hataları)
        if (Array.isArray(detail)) {
            return detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
        }
        return String(detail);
    }

    const message = err?.response?.data?.message;
    if (message) return String(message);

    // Axios ağ hataları gibi teknik mesajları kullanıcıya gösterme
    const jsMessage = err?.message;
    if (jsMessage && !/network error|status code|request failed/i.test(jsMessage)) {
        return jsMessage;
    }

    return varsayilan;
}
