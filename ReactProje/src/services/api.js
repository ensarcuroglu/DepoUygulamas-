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
            // Login sayfasındayken 401 alınırsa yönlendirme yapma
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
// ÜRÜNLER
// ========================
export const getUrunler = (params = {}) => api.get('/urunler/', { params });
export const getUrun = (id) => api.get(`/urunler/${id}`);
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
// STOK HAREKETLERİ
// ========================
export const getStokHareketleri = (params = {}) => api.get('/stok-hareketleri/', { params });
export const createStokHareketi = (data) => api.post('/stok-hareketleri/', data);


// ========================
// TEDARİKÇİLER
// ========================
export const getTedarikciler = async () => {
    const response = await api.get('/tedarikciler/');
    return response.data;
};
export const addTedarikci = async (tedarikciData) => {
    const response = await api.post('/tedarikciler/', tedarikciData);
};

export default api;
