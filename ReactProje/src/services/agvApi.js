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
};
