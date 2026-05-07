import api from './api';

const BASE = '/operator-performans';

export const operatorPerformansApi = {
  ozet: (params = {}) =>
    api.get(`${BASE}/ozet`, { params }).then((r) => r.data),

  leaderboard: (params = {}) =>
    api.get(`${BASE}/leaderboard`, { params }).then((r) => r.data),

  benimMetriklerim: (params = {}) =>
    api.get(`${BASE}/me`, { params }).then((r) => r.data),

  kullaniciDetay: (kullaniciId, params = {}) =>
    api.get(`${BASE}/kullanici/${kullaniciId}`, { params }).then((r) => r.data),
};
