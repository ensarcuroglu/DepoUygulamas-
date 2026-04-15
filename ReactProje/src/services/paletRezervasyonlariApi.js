import axios from 'axios';

const BASE = '/api/v1/palet-rezervasyonlari';

export const paletRezervasyonlariApi = {
  listele: (params = {}) =>
    axios.get(BASE + '/', { params }).then(r => r.data),

  siparisRezervasyonlari: (siparisId) =>
    axios.get(`${BASE}/siparis/${siparisId}`).then(r => r.data),

  iptalEt: (id, neden = null) =>
    axios.post(`${BASE}/${id}/iptal`, { neden }).then(r => r.data),

  degistir: (id, yeniPaletId, neden = null) =>
    axios.post(`${BASE}/${id}/degistir`, {
      yeni_palet_id: yeniPaletId,
      neden,
    }).then(r => r.data),
};

export const urunStokDetayApi = {
  getir: (urunId) =>
    axios.get(`/api/urunler/${urunId}/stok-detay`).then(r => r.data),
};
