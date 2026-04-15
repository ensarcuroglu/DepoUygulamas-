import axios from 'axios';

const BASE = '/api/v1/toplama-gorevleri';

export const toplamaGorevleriApi = {
  listele: (params = {}) =>
    axios.get(BASE + '/', { params }).then(r => r.data),

  getir: (id) =>
    axios.get(`${BASE}/${id}`).then(r => r.data),

  gorevUret: (sevkiyatId) =>
    axios.post(BASE + '/uret', { sevkiyat_id: sevkiyatId }).then(r => r.data),

  siradanGorevAl: (depoId = null) =>
    axios.post(BASE + '/sira-al', { depo_id: depoId }).then(r => r.data),

  baslat: (id) =>
    axios.post(`${BASE}/${id}/baslat`).then(r => r.data),

  tamamla: (id) =>
    axios.post(`${BASE}/${id}/tamamla`).then(r => r.data),

  iptalEt: (id, neden = null) =>
    axios.post(`${BASE}/${id}/iptal`, { neden }).then(r => r.data),

  fefoOverride: (id, yeniPaletId, overrideNeden) =>
    axios.post(`${BASE}/${id}/fefo-override`, {
      yeni_palet_id: yeniPaletId,
      override_neden: overrideNeden,
    }).then(r => r.data),
};
