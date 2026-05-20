/**
 * AgvSimService HTTP istemcisi.
 *
 * Vite proxy yapılandırması (`/api/agv` → `http://127.0.0.1:8002`) sayesinde
 * frontend göreceli yol kullanır; üretimde reverse proxy aynı path'i AGV
 * servisine yönlendirir. `api` axios instance'ının baseURL'i `/api` olduğu
 * için buradaki yolların başında `/api` tekrar yazılmaz.
 */

import api from './api';

export const agvApi = {
    grid: () => api.get('/agv/grid').then((r) => r.data),
    robotlar: () => api.get('/agv/robotlar').then((r) => r.data),
    /**
     * @param {{ wms_gorev_id: number, wms_gorev_tipi?: 'Yerlestirme'|'Toplama',
     *           kaynak_raf_id: number, hedef_raf_id: number,
     *           palet_id?: number, oncelik?: number }} payload
     */
    pushGorev: (payload) => api.post('/agv/gorevler', payload).then((r) => r.data),

    // Demo / test paneli — AgvSimService `AGV_TEST_PANEL_ENABLED` ile gated.
    test: {
        gorev: (body = {}) =>
            api.post('/agv/test/gorev', body).then((r) => r.data),
        yogunTrafik: (gorev_sayisi = 8) =>
            api
                .post('/agv/test/yogun-trafik', { gorev_sayisi })
                .then((r) => r.data),
        dusukBatarya: (body = {}) =>
            api.post('/agv/test/dusuk-batarya', body).then((r) => r.data),
        robotAriza: (body = {}) =>
            api.post('/agv/test/robot-ariza', body).then((r) => r.data),
        deadlock: () =>
            api.post('/agv/test/deadlock-senaryosu', {}).then((r) => r.data),
        duraklat: () => api.post('/agv/test/duraklat').then((r) => r.data),
        devam: () => api.post('/agv/test/devam').then((r) => r.data),
        sifirla: () => api.post('/agv/test/sifirla').then((r) => r.data),
    },
};
