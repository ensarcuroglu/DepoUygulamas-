/**
 * Barkod yardımcı fonksiyonları — Zebra DataWedge ve genel barkod yönetimi.
 *
 * StokHareketleriPage'teki lokal implementasyonlardan merkezi modüle taşınmıştır.
 * Tüm terminal sayfaları ve barkod kullanan sayfalar bu modülü kullanmalıdır.
 */

// ─── Zebra Cihaz Algılama ─────────────────────────────────────────────────────

let _zebraCache = null;

/**
 * Zebra el terminalini User-Agent üzerinden algılar.
 * Sonuç oturum boyunca önbelleğe alınır.
 *
 * Desteklenen modeller: TC21, TC52, TC52x, TC57, TC72, MC3300, MC33, ET51, L10, etc.
 *
 * @returns {boolean}
 */
export const isZebraDevice = () => {
    if (_zebraCache !== null) return _zebraCache;
    const ua = navigator.userAgent.toLowerCase();
    _zebraCache = ua.includes('zebra')
        || ua.includes('symbol')
        || ua.includes('tc52')
        || ua.includes('tc21')
        || ua.includes('tc57')
        || ua.includes('tc72')
        || ua.includes('mc33')
        || ua.includes('mc3300')
        || ua.includes('et51')
        || ua.includes('l10');
    return _zebraCache;
};

// ─── Barkod Sanitization ────────────────────────────────────────────────────────

/**
 * Kontrol karakterleri, DataWedge prefix/suffix karakterleri temizler.
 * ASCII 0-31 (C0 kontrol) ve DEL (127) kaldırılır.
 *
 * @param {string} value - Ham barkod verisi
 * @returns {string} Temizlenmiş barkod
 */
export const stripControlChars = (value) => {
    if (!value) return '';
    return Array.from(value)
        .filter((char) => {
            const code = char.charCodeAt(0);
            return code > 31 && code !== 127;
        })
        .join('');
};

/**
 * Palet barkodunu sanitize eder.
 * - Kontrol karakterleri temizlenir
 * - Zero-width / BOM kaldırılır
 * - Tüm boşluklar kaldırılır
 * - Büyük harfe çevrilir
 *
 * @param {string} raw - Ham palet barkodu
 * @returns {string} Temizlenmiş palet barkodu
 */
export const sanitizePaletNo = (raw) => {
    if (!raw) return '';
    return stripControlChars(raw)
        .replace(/[\u200B-\u200F\uFEFF]/g, '')  // Zero-width / BOM
        .replace(/\s+/g, '')                     // Tüm boşluklar
        .toUpperCase()
        .trim();
};

/**
 * Raf barkodunu sanitize eder.
 * Palet ile aynı kurallar ama boşluk korunabilir (raf kodları tire içerir).
 *
 * @param {string} raw - Ham raf barkodu
 * @returns {string} Temizlenmiş raf barkodu
 */
export const sanitizeRafKod = (raw) => {
    if (!raw) return '';
    return stripControlChars(raw)
        .replace(/[\u200B-\u200F\uFEFF]/g, '')
        .replace(/\s+/g, '')   // Raf kodlarında boşluk istemiyoruz
        .toUpperCase()
        .trim();
};

/**
 * Genel barkod sanitize — tip belirtilmezse palet varsayılır.
 *
 * @param {string} raw - Ham barkod
 * @param {'palet'|'raf'|'generic'} [type='generic']
 * @returns {string} Temizlenmiş barkod
 */
export const sanitizeBarkod = (raw, type = 'generic') => {
    if (type === 'palet') return sanitizePaletNo(raw);
    if (type === 'raf') return sanitizeRafKod(raw);
    // generic: kontrol karakterleri + zero-width temizle, büyük harf
    if (!raw) return '';
    return stripControlChars(raw)
        .replace(/[\u200B-\u200F\uFEFF]/g, '')
        .trim()
        .toUpperCase();
};

// ─── Barkod Format Doğrulama ────────────────────────────────────────────────────

/**
 * Barkod format doğrulama kuralları.
 * Regex'ler mevcut veri formatına göre güncellenmeli.
 * Şu anki pattern'ler yaygın formatları kapsar ama kısıtlayıcı değildir.
 */
const BARKOD_PATTERNLERI = {
    // Çok kaynaklı palet formatları — prefix registry
    // PRD: Üretim | MKB: Mal Kabul | PLT: Tedarikçi ref | Sayısal: Legacy
    palet: /^(PRD-\d{8}-\d{1,5}|MKB-\d{8}-\d{1,5}|PLT-[\w-]{1,30}|\d{4,10})$/i,
    // GNL-A-01-01-01 veya RAF-XX-XX-XX gibi
    raf: /^[A-Z]{2,4}-[A-Z]-\d{2}-\d{2}-\d{2}$/i,
    // LOT-NNN veya LOT-NNNNN
    lot: /^LOT-\d{1,8}$/i,
};

/**
 * Barkod formatını doğrular.
 *
 * @param {string} code - Sanitize edilmiş barkod
 * @param {'palet'|'raf'|'lot'} type - Beklenen barkod tipi
 * @returns {{ valid: boolean, error?: string }}
 */
export const validateBarkodFormat = (code, type) => {
    if (!code) return { valid: false, error: 'Barkod boş.' };

    const pattern = BARKOD_PATTERNLERI[type];
    if (!pattern) return { valid: true }; // Bilinmeyen tip → geçerli say

    if (!pattern.test(code)) {
        const ornekler = {
            palet: 'PRD-20260424-001 veya MKB-20260429-001',
            raf: 'GNL-A-01-01-01',
            lot: 'LOT-12345',
        };
        return {
            valid: false,
            error: `Beklenen format: ${ornekler[type] || '?'}. Okutulan: ${code}`,
        };
    }

    return { valid: true };
};

// ─── Tarama Geri Bildirim (Ses + Titreşim) ──────────────────────────────────────

let _feedbackAudioContext = null;

const getFeedbackAudioContext = () => {
    if (_feedbackAudioContext && _feedbackAudioContext.state !== 'closed') {
        return _feedbackAudioContext;
    }
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return null;
    _feedbackAudioContext = new AudioContextClass();
    return _feedbackAudioContext;
};

/**
 * Tarama sonrası sesli ve/veya dokunsal geri bildirim verir.
 * Depo ortamında operatör ekrana bakamayabilir — bu geri bildirim kritik önem taşır.
 *
 * @param {'success'|'error'|'warning'} type - Geri bildirim tipi
 * @param {{ vibrate?: boolean, sound?: boolean }} [options] - Geri bildirim kanalları
 */
export const scanFeedback = (type, { vibrate = true, sound = true } = {}) => {
    // Titreşim
    if (vibrate && navigator.vibrate) {
        if (type === 'success') {
            navigator.vibrate([100]);
        } else if (type === 'error') {
            navigator.vibrate([100, 50, 100, 50, 100]);
        } else {
            navigator.vibrate([50, 50, 50]);
        }
    }

    // Ses (Web Audio API ile kısa bip)
    if (!sound) return;
    try {
        const ctx = getFeedbackAudioContext();
        if (!ctx) return;
        if (ctx.state === 'suspended') {
            ctx.resume().catch(() => {});
        }

        const duration = type === 'success' ? 0.12 : type === 'error' ? 0.35 : 0.2;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.frequency.value = type === 'success' ? 880 : type === 'error' ? 300 : 660;
        osc.type = type === 'success' ? 'sine' : type === 'error' ? 'square' : 'triangle';
        gain.gain.setValueAtTime(0.0001, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + duration);
    } catch {
        /* Audio API desteklenmiyorsa sessizce devam et */
    }
};

// ─── Duplicate Scan Koruması ────────────────────────────────────────────────────

/**
 * Belirli bir süre içinde aynı barkodun tekrar okutulmasını engeller.
 * Her scan sayfası kendi instance'ını oluşturmalıdır.
 */
export class DuplicateScanGuard {
    /**
     * @param {number} cooldownMs - Aynı barkodun tekrar kabul edileceği minimum süre (ms)
     */
    constructor(cooldownMs = 3000) {
        this._cooldownMs = cooldownMs;
        this._recent = new Map(); // barkod → timestamp
    }

    /**
     * Barkodu kontrol eder. Geçerliyse kaydeder ve true döner.
     * Cooldown içinde tekrar gelirse false döner.
     *
     * @param {string} code - Sanitize edilmiş barkod
     * @returns {boolean} true = yeni/geçerli, false = duplicate
     */
    check(code) {
        if (!code) return false;
        const now = Date.now();
        const lastTime = this._recent.get(code);

        if (lastTime && now - lastTime < this._cooldownMs) {
            return false; // Duplicate
        }

        this._recent.set(code, now);

        // Temizlik: cooldown'dan eski kayıtları sil (bellek sızıntısı önlemi)
        for (const [key, time] of this._recent) {
            if (now - time > this._cooldownMs * 2) {
                this._recent.delete(key);
            }
        }

        return true;
    }

    /** Tüm kayıtları temizler (sayfa sıfırlama gibi durumlarda). */
    reset() {
        this._recent.clear();
    }
}

// ─── Idempotency Key Üretimi ────────────────────────────────────────────────────

/**
 * Backend idempotency kontrolü için benzersiz key üretir.
 * Format: scan-{timestamp}-{random}
 *
 * @returns {string}
 */
export const generateIdempotencyKey = () => {
    return `scan-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
};
