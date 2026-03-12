/**
 * API hata yanıtlarından tutarlı biçimde mesaj üretir.
 *
 * Öncelik sırası:
 *   1. Yeni backend formatı: { success: false, error: "..." }
 *   2. FastAPI'nin döndürdüğü `detail` alanı  (en yaygın)
 *   3. Genel `message` alanı
 *   4. Ağ/timeout gibi JS hatalarının mesajı (ekrana "Network Error" gibi teknik ifadeler çıkmaması için filtre var)
 *   5. Çağırırken verilen `varsayilan` değer
 *
 * @param {unknown} err         - Axios veya JS hatası
 * @param {string}  varsayilan  - Hiçbir detay bulunamazsa gösterilecek mesaj
 * @returns {string}
 */
export function hataMetni(err, varsayilan = 'Beklenmeyen bir hata oluştu') {
    const data = err?.response?.data;

    // Yeni backend formatı: { success: false, error: "..." }
    if (data?.success === false && data?.error) {
        return String(data.error);
    }

    const detail = data?.detail;
    if (detail) {
        // FastAPI bazen detail'i dizi olarak döner (validation hataları)
        if (Array.isArray(detail)) {
            return detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
        }
        return String(detail);
    }

    const message = data?.message;
    if (message) return String(message);

    // Axios ağ hataları gibi teknik mesajları kullanıcıya gösterme
    const jsMessage = err?.message;
    if (jsMessage && !/network error|status code|request failed/i.test(jsMessage)) {
        return jsMessage;
    }

    return varsayilan;
}
