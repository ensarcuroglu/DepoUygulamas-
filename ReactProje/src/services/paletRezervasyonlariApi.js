import api from './api';

const BASE = '/v1/palet-rezervasyonlari';

export const paletRezervasyonlariApi = {
  listele: (params = {}) =>
    api.get(BASE + '/', { params }).then(r => r.data),

  siparisRezervasyonlari: (siparisId) =>
    api.get(`${BASE}/siparis/${siparisId}`).then(r => r.data),

  iptalEt: (id, neden = null) =>
    api.post(`${BASE}/${id}/iptal`, { neden }).then(r => r.data),

  degistir: (id, yeniPaletId, neden = null) =>
    api.post(`${BASE}/${id}/degistir`, {
      yeni_palet_id: yeniPaletId,
      neden,
    }).then(r => r.data),
};

export const urunStokDetayApi = {
  getir: (urunId) =>
    api.get(`/urunler/${urunId}/stok-detay`).then(r => r.data),
};
