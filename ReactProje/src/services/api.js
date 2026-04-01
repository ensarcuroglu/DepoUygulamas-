import axios from 'axios';

const API_BASE_URL = '/api';

// ========================
// HATA YÖNETİMİ
// ========================

/**
 * Standart API hata sınıfı.
 * Backend'in { success, error, code, details } formatını taşır.
 */
export class ApiError extends Error {
    constructor(message, status, code = null, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
        this.details = details;
    }
}

/**
 * Axios hata nesnesini ApiError'a dönüştürür.
 * - Backend standardize yanıtı (success: false) destekler
 * - Ağ hatası (no response) ayrıca işlenir
 * - Fallback olarak axios hata mesajını kullanır
 */
export const handleApiError = (error) => {
    // Backend'den gelen standardize yanıt
    if (error.response?.data) {
        const { success, error: message, code, details } = error.response.data;
        if (success === false && message) {
            return new ApiError(message, code ?? error.response.status, code, details);
        }
        // FastAPI'nin kendi hata formatı (detail field)
        const detail = error.response.data.detail;
        if (detail) {
            const msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
            return new ApiError(msg, error.response.status);
        }
    }
    // Ağ / bağlantı hatası
    if (!error.response) {
        return new ApiError('Sunucuya bağlanılamadı', 0, 'NETWORK_ERROR');
    }
    // Fallback
    return new ApiError(
        error.message || 'Beklenmeyen hata oluştu',
        error.response?.status ?? 500,
    );
};

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ========================
// REQUEST INTERCEPTOR — Her istekte access token ekle
// ========================
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// ========================
// RESPONSE INTERCEPTOR — 401'de önce refresh dene, başarısızsa logout
// ========================

// Eş zamanlı birden fazla 401 isteğini yönetmek için
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

const forceLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
    }
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // 401 değilse, login sayfasındaysa veya zaten retry yapıldıysa direkt reject
        if (
            error.response?.status !== 401 ||
            originalRequest._retry ||
            window.location.pathname.includes('/login')
        ) {
            return Promise.reject(error);
        }

        // Refresh zaten devam ediyorsa, bu isteği kuyruğa al
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                })
                .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refresh_token');

        if (!refreshToken) {
            isRefreshing = false;
            forceLogout();
            return Promise.reject(error);
        }

        try {
            // Refresh endpoint'ine axios direkt çağrı (interceptor döngüsünü önler)
            const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken,
            });

            const { access_token } = response.data;
            localStorage.setItem('access_token', access_token);
            api.defaults.headers.common.Authorization = `Bearer ${access_token}`;

            processQueue(null, access_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            forceLogout();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

// ========================
// AUTH (KİMLİK DOĞRULAMA)
// ========================
export const loginUser = (credentials) => api.post('/auth/login', credentials);
export const getCurrentUser = () => api.get('/auth/me');
export const registerUser = (data) => api.post('/auth/register', data);
export const refreshAccessToken = (data) => api.post('/auth/refresh', data);
export const logoutUser = (data) => api.post('/auth/logout', data);

// ========================
// KULLANICI YÖNETİMİ
// ========================
export const getKullanicilar = () => api.get('/kullanicilar/');
export const getKullanici = (id) => api.get(`/kullanicilar/${id}`);
export const createKullanici = (data) => api.post('/auth/register', data);
export const updateKullanici = (id, data) => api.put(`/kullanicilar/${id}`, data);
export const deleteKullanici = (id) => api.delete(`/kullanicilar/${id}`);

// ========================
// DASHBOARD
// ========================
export const getDashboardStats = () => api.get('/dashboard');

// ========================
// MARKALAR
// ========================
export const getMarkalar = () => api.get('/markalar/');
export const getMarka = (id) => api.get(`/markalar/${id}`);
export const createMarka = (data) => api.post('/markalar/', data);
export const updateMarka = (id, data) => api.put(`/markalar/${id}`, data);
export const deleteMarka = (id) => api.delete(`/markalar/${id}`);

// ========================
// ÜRÜNLER
// ========================
export const getUrunler = (params = {}) => api.get('/urunler/', { params });
export const getUrun = (id) => api.get(`/urunler/${id}`);
export const getUrunByBarkod = (barkod) => api.get(`/urunler/barkod/${encodeURIComponent(barkod)}`);
export const getKritikUrunler = () => api.get('/urunler/kritik');
export const createUrun = (data) => api.post('/urunler/', data);
export const updateUrun = (id, data) => api.put(`/urunler/${id}`, data);
export const deleteUrun = (id) => api.delete(`/urunler/${id}`);
export const checkBarkodUniqueness = (deger, alan, excludeId = null) => {
    const params = { deger, alan };
    if (excludeId) params.exclude_id = excludeId;
    return api.get('/urunler/barkod-kontrol', { params });
};

// ========================
// KATEGORİLER
// ========================
export const getKategoriler = () => api.get('/kategoriler/');
export const createKategori = (data) => api.post('/kategoriler/', data);
export const updateKategori = (id, data) => api.put(`/kategoriler/${id}`, data);
export const deleteKategori = (id) => api.delete(`/kategoriler/${id}`);

// ========================
// DEPOLAR
// ========================
export const getDepolar = () => api.get('/depolar/');
export const getDepo = (id) => api.get(`/depolar/${id}`);
export const createDepo = (data) => api.post('/depolar/', data);
export const updateDepo = (id, data) => api.put(`/depolar/${id}`, data);
export const deleteDepo = (id) => api.delete(`/depolar/${id}`);
export const getRaflar = (params = {}) => api.get('/raflar/', { params });
export const createRaf = (data) => api.post('/raflar/', data);

// ========================
// LOTLAR
// ========================
export const getLotlar = (params = {}) => api.get('/lotlar/', { params });
export const getLot = (id) => api.get(`/lotlar/${id}`);
export const getSktYaklasanLotlar = (gun = 30) => api.get('/lotlar/skt-yaklasan', { params: { gun } });
export const createLot = (data) => api.post('/lotlar/', data);
export const updateLot = (id, data) => api.put(`/lotlar/${id}`, data);
export const deleteLot = (id) => api.delete(`/lotlar/${id}`);

// ========================
// PALETLER
// ========================
export const getPaletler = (params = {}) => api.get('/paletler/', { params });
export const getPalet = (id) => api.get(`/paletler/${id}`);
export const getPaletByBarkod = (palet_no) => api.get(`/paletler/barkod/${encodeURIComponent(palet_no)}`);
export const getSonrakiPaletNo = () => api.get('/paletler/sonraki-numara');
export const createPalet = (data) => api.post('/paletler/', data);
export const updatePalet = (id, data) => api.put(`/paletler/${id}`, data);
export const deletePalet = (id) => api.delete(`/paletler/${id}`);

// ========================
// STOK HAREKETLERİ
// ========================
export const getStokHareketleri = (params = {}) => api.get('/stok-hareketleri/', { params });
export const createStokHareketi = (data) => api.post('/stok-hareketleri/', data);

// ========================
// STOK İŞLEMLERİ (Palet Bazlı)
// ========================
export const stokIslemleriPaletSorgula = (paletNo) => api.get(`/stok-islemleri/palet/${encodeURIComponent(paletNo)}`);
export const stokIslemleriPaletGiris = (data) => api.post('/stok-islemleri/palet-giris', data);
export const stokIslemleriPaletCikis = (data) => api.post('/stok-islemleri/palet-cikis', data);
export const stokIslemleriTopluGiris = (data) => api.post('/stok-islemleri/toplu-giris', data);
export const stokIslemleriTopluCikis = (data) => api.post('/stok-islemleri/toplu-cikis', data);

// ========================
// TEDARİKÇİLER
// ========================
export const getTedarikciler = () => api.get('/tedarikciler/');
export const getTedarikci = (id) => api.get(`/tedarikciler/${id}`);
export const addTedarikci = (data) => api.post('/tedarikciler/', data);
export const deleteTedarikci = (id) => api.delete(`/tedarikciler/${id}`);

// ========================
// SİSTEM LOGLARI
// ========================
export const getSistemLoglari = (limit = 100) => api.get('/sistem-loglari/', { params: { limit } });
export const createSistemLog = (data) => api.post('/sistem-loglari/', data);

// ========================
// DESTEK MASASI
// ========================
export const getDestekTalepleri = (params = {}) => api.get('/destek/', { params });
export const getDestekTalebi = (id) => api.get(`/destek/${id}`);
export const createDestekTalebi = (data) => api.post('/destek/', data);
export const updateDestekTalebi = (id, data) => api.put(`/destek/${id}`, data);

// ========================
// SİPARİŞLER
// ========================
export const getSiparisler = (params = {}) => api.get('/siparisler/', { params });
export const getSiparis = (id) => api.get(`/siparisler/${id}`);
export const createSiparis = (data) => api.post('/siparisler/', data);
export const updateSiparis = (id, data) => api.put(`/siparisler/${id}`, data);
export const deleteSiparis = (id) => api.delete(`/siparisler/${id}`);

// ========================
// MAL KABUL İRSALİYELERİ
// ========================
export const getMalKabulIrsaliyeleri = (params = {}) => api.get('/mal-kabul-irsaliyeleri/', { params });
export const getMalKabulIrsaliye = (id) => api.get(`/mal-kabul-irsaliyeleri/${id}`);
export const createMalKabulIrsaliye = (data) => api.post('/mal-kabul-irsaliyeleri/', data);
export const updateMalKabulIrsaliye = (id, data) => api.put(`/mal-kabul-irsaliyeleri/${id}`, data);
export const deleteMalKabulIrsaliye = (id) => api.delete(`/mal-kabul-irsaliyeleri/${id}`);

// ========================
// SEVKİYAT PLANLAMA
// ========================
export const getSevkiyatPlanlari = (params = {}) => api.get('/sevkiyat-planlama/', { params });
export const getSevkiyatPlani = (id) => api.get(`/sevkiyat-planlama/${id}`);
export const createSevkiyatPlani = (data) => api.post('/sevkiyat-planlama/', data);
export const updateSevkiyatPlani = (id, data) => api.put(`/sevkiyat-planlama/${id}`, data);
export const deleteSevkiyatPlani = (id) => api.delete(`/sevkiyat-planlama/${id}`);

// ========================
// İRSALİYELER
// ========================
export const getIrsaliyeler = (params = {}) => api.get('/irsaliyeler/', { params });
export const getIrsaliye = (id) => api.get(`/irsaliyeler/${id}`);
export const createIrsaliye = (data) => api.post('/irsaliyeler/', data);
export const updateIrsaliye = (id, data) => api.put(`/irsaliyeler/${id}`, data);

// ========================
// RAPORLAR - ŞABLONLAR
// ========================
export const getRaporSablonlari = (params = {}) => api.get('/raporlar/sablonlar', { params });
export const getRaporSablonu = (id) => api.get(`/raporlar/sablonlar/${id}`);
export const createRaporSablonu = (data) => api.post('/raporlar/sablonlar', data);
export const updateRaporSablonu = (id, data) => api.put(`/raporlar/sablonlar/${id}`, data);
export const deleteRaporSablonu = (id) => api.delete(`/raporlar/sablonlar/${id}`);

// ========================
// RAPORLAR - VERİ
// ========================
export const getStokRaporuVeri = (params = {}) => api.get('/raporlar/stok/veriler', { params });
export const getSiparisRaporuVeri = (params = {}) => api.get('/raporlar/siparis/veriler', { params });
export const getHareketRaporuVeri = (params = {}) => api.get('/raporlar/hareket/veriler', { params });
export const getKritikStokRaporu = () => api.get('/raporlar/kritik-stok');
export const getSktRaporu = (gun = 30) => api.get('/raporlar/skt', { params: { gun } });
export const getAbcAnaliz = () => api.get('/raporlar/abc-analiz');
export const getDepoDoluluk = () => api.get('/raporlar/doluluk');
export const raporExport = (params = {}) => api.post('/raporlar/export', null, { params, responseType: 'blob' });
export const tetikleRaporSchedule = (scheduleId) => api.post(`/raporlar/schedule/tetikle`, null, { params: { schedule_id: scheduleId } });

// ========================
// RAPORLAR - LOG
// ========================
export const getRaporLoglari = (params = {}) => api.get('/raporlar/log', { params });

// ========================
// RAPORLAR - SCHEDULE
// ========================
export const getRaporSchedules = (params = {}) => api.get('/raporlar/schedule', { params });
export const getRaporSchedule = (id) => api.get(`/raporlar/schedule/${id}`);
export const createRaporSchedule = (data) => api.post('/raporlar/schedule', data);
export const updateRaporSchedule = (id, data) => api.put(`/raporlar/schedule/${id}`, data);
export const deleteRaporSchedule = (id) => api.delete(`/raporlar/schedule/${id}`);

// ========================
// İRSALİYE YAZDIR
// ========================
export const getIrsaliyeYazdirVerisi = (id) => api.get(`/irsaliyeler/${id}/yazdir`);

export default api;
