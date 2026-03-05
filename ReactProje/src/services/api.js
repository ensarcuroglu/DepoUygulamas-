import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ========================
// REQUEST INTERCEPTOR — Her istekte token ekle
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
// RESPONSE INTERCEPTOR — 401'de otomatik logout
// ========================
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            if (!window.location.pathname.includes('/login')) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// ========================
// AUTH (KİMLİK DOĞRULAMA)
// ========================
export const loginUser = (credentials) => api.post('/auth/login', credentials);
export const getCurrentUser = () => api.get('/auth/me');
export const registerUser = (data) => api.post('/auth/register', data);

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
// TEDARİKÇİLER
// ========================
export const getTedarikciler = () => api.get('/tedarikciler/');
export const getTedarikci = (id) => api.get(`/tedarikciler/${id}`);
export const addTedarikci = (data) => api.post('/tedarikciler/', data);
export const updateTedarikci = (id, data) => api.put(`/tedarikciler/${id}`, data);
export const deleteTedarikci = (id) => api.delete(`/tedarikciler/${id}`);

export default api;
