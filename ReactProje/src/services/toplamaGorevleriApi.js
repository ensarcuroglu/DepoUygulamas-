import api from './api';

const BASE = '/v1/toplama-gorevleri';

export const toplamaGorevleriApi = {
  listele: (params = {}) =>
    api.get(BASE + '/', { params }).then(r => r.data),

  getir: (id) =>
    api.get(`${BASE}/${id}`).then(r => r.data),

  gorevUret: (sevkiyatId) =>
    api.post(BASE + '/uret', { sevkiyat_id: sevkiyatId }).then(r => r.data),

  siradanGorevAl: (depoId = null) =>
    api.post(BASE + '/sira-al', { depo_id: depoId }).then(r => r.data),

  baslat: (id) =>
    api.post(`${BASE}/${id}/baslat`).then(r => r.data),

  tamamla: (id) =>
    api.post(`${BASE}/${id}/tamamla`).then(r => r.data),

  iptalEt: (id, neden = null) =>
    api.post(`${BASE}/${id}/iptal`, { neden }).then(r => r.data),

  fefoOverride: (id, yeniPaletId, overrideNeden) =>
    api.post(`${BASE}/${id}/fefo-override`, {
      yeni_palet_id: yeniPaletId,
      override_neden: overrideNeden,
    }).then(r => r.data),
};
