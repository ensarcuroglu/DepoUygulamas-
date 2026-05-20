/**
 * AgvSimService HTTP istemcisi.
 *
 * Vite proxy yapılandırması (`/api/agv` → `http://127.0.0.1:8002`) sayesinde
 * frontend göreceli yol kullanır; üretimde reverse proxy aynı path'i AGV
 * servisine yönlendirir.
 */

import api from './api';

export const agvApi = {
    grid: () => api.get('/api/agv/grid').then((r) => r.data),
    robotlar: () => api.get('/api/agv/robotlar').then((r) => r.data),
    /**
     * @param {{ wms_gorev_id: number, wms_gorev_tipi?: 'Yerlestirme'|'Toplama',
     *           kaynak_raf_id: number, hedef_raf_id: number,
     *           palet_id?: number, oncelik?: number }} payload
     */
    pushGorev: (payload) => api.post('/api/agv/gorevler', payload).then((r) => r.data),

    // Demo / test paneli — AgvSimService `AGV_TEST_PANEL_ENABLED` ile gated.
    test: {
        gorev: (body = {}) =>
            api.post('/api/agv/test/gorev', body).then((r) => r.data),
        yogunTrafik: (gorev_sayisi = 8) =>
            api
                .post('/api/agv/test/yogun-trafik', { gorev_sayisi })
                .then((r) => r.data),
        dusukBatarya: (body = {}) =>
            api.post('/api/agv/test/dusuk-batarya', body).then((r) => r.data),
        robotAriza: (body = {}) =>
            api.post('/api/agv/test/robot-ariza', body).then((r) => r.data),
        deadlock: () =>
            api.post('/api/agv/test/deadlock-senaryosu', {}).then((r) => r.data),
        duraklat: () => api.post('/api/agv/test/duraklat').then((r) => r.data),
        devam: () => api.post('/api/agv/test/devam').then((r) => r.data),
        sifirla: () => api.post('/api/agv/test/sifirla').then((r) => r.data),
    },
};
