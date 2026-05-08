/**
 * AGV simülasyon canlı state'i — zustand store.
 *
 * Tasarım kuralı: yüksek frekanslı robot konumları React state'e yazılmaz.
 * Bileşenler şu pattern'le tüketir:
 *   - Statik/seyrek değişen alanlar (isConnected, robotIds, tickNo, sonOlaylar)
 *     için `useAgvStore(s => s.X)` selector'u — re-render sadece o slice değişince.
 *   - Yüksek frekanslı `robots[id]` için `useAgvStore.getState()` ile
 *     `useFrame` içinde okunur (subscribe yok → re-render yok).
 *
 * Store'a sadece WS hook (`useAgvWebSocket`) yazar.
 */

import { create } from 'zustand';

const MAX_OLAY = 30;

const initialState = {
    isConnected: false,
    isConnecting: false,
    lastError: null,

    grid: null,            // { genislik, yukseklik, raflar, sarj_konumlari }
    tickNo: 0,

    robots: {},            // { [id]: { id, x, y, durum, yon, gorev_id, rota_kalan } }
    robotIds: [],          // Stable referans — sadece snapshot'ta güncellenir

    rotalar: {},           // { [robot_id]: [[x, y], ...] } — rota_hesaplandi event'inden
    sonOlaylar: [],        // { olay, robot_id?, gorev_id?, ts } — son N

    kuyrukUzunlugu: 0,
    aktifGorevSayisi: 0,
    aktifGorevler: [],     // Faz 5: aktif görev listesi (delta'dan, gorev_id, robot_id, ...)

    selectedRobotId: null, // Faz 4: kullanıcı 3D'de bir robotu tıkladığında
};

export const useAgvStore = create((set) => ({
    ...initialState,

    setConnectionState: (patch) => set(patch),

    setSelectedRobotId: (id) => set((state) => (
        state.selectedRobotId === id ? state : { selectedRobotId: id }
    )),

    applySnapshot: (msg) => {
        const robots = {};
        const robotIds = [];
        for (const r of msg.robotlar ?? []) {
            robots[r.id] = r;
            robotIds.push(r.id);
        }
        set({
            grid: msg.grid ?? null,
            tickNo: msg.tick_no ?? 0,
            robots,
            robotIds,
            rotalar: {},
            sonOlaylar: [],
        });
    },

    applyDelta: (msg) => set((state) => {
        const robots = { ...state.robots };
        for (const r of msg.robotlar ?? []) {
            robots[r.id] = r;
        }
        return {
            tickNo: msg.tick_no ?? state.tickNo,
            robots,
            kuyrukUzunlugu: msg.kuyruk_uzunlugu ?? state.kuyrukUzunlugu,
            aktifGorevSayisi: msg.aktif_gorev_sayisi ?? state.aktifGorevSayisi,
            aktifGorevler: msg.aktif_gorevler ?? state.aktifGorevler,
        };
    }),

    applyEvent: (msg) => set((state) => {
        const olaylar = [{ ...msg, ts: Date.now() }, ...state.sonOlaylar].slice(0, MAX_OLAY);
        let rotalar = state.rotalar;
        if (msg.olay === 'rota_hesaplandi' && msg.robot_id && Array.isArray(msg.rota)) {
            rotalar = { ...rotalar, [msg.robot_id]: msg.rota };
        } else if (
            (msg.olay === 'gorev_tamamlandi' || msg.olay === 'rota_bulunamadi')
            && msg.robot_id
        ) {
            const { [msg.robot_id]: _silinen, ...kalan } = rotalar;
            void _silinen;
            rotalar = kalan;
        }
        return { sonOlaylar: olaylar, rotalar };
    }),

    reset: () => set(initialState),
}));
