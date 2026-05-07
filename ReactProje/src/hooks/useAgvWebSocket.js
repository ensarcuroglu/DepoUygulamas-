/**
 * AGV WebSocket bağlantı yöneticisi.
 *
 * - Bağlanır, snapshot/delta/event mesajlarını zustand store'a yazar.
 * - Bağlantı koparsa exponential backoff (1s → 2s → 4s → 8s → 10s) ile yeniden bağlanır.
 * - Component unmount'ta bağlantı temiz kapatılır; reconnect zinciri durdurulur.
 */

import { useEffect, useRef } from 'react';

import { useAgvStore } from '../stores/agvStore';

const RECONNECT_BACKOFF_MS = [1000, 2000, 4000, 8000, 10000];

function buildWsUrl() {
    const envUrl = import.meta.env.VITE_AGV_WS_URL;
    if (envUrl) return envUrl;
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/ws/agv`;
}

export function useAgvWebSocket() {
    const wsRef = useRef(null);
    const reconnectAttemptRef = useRef(0);
    const closingRef = useRef(false);
    const timerRef = useRef(null);

    useEffect(() => {
        closingRef.current = false;
        const store = useAgvStore;

        function scheduleReconnect() {
            if (closingRef.current) return;
            const idx = Math.min(
                reconnectAttemptRef.current,
                RECONNECT_BACKOFF_MS.length - 1
            );
            const delay = RECONNECT_BACKOFF_MS[idx];
            reconnectAttemptRef.current += 1;
            timerRef.current = setTimeout(connect, delay);
        }

        function connect() {
            if (closingRef.current) return;
            const url = buildWsUrl();
            store.getState().setConnectionState({ isConnecting: true, lastError: null });

            let ws;
            try {
                ws = new WebSocket(url);
            } catch (err) {
                store.getState().setConnectionState({
                    isConnected: false,
                    isConnecting: false,
                    lastError: String(err?.message ?? err),
                });
                scheduleReconnect();
                return;
            }
            wsRef.current = ws;

            ws.onopen = () => {
                reconnectAttemptRef.current = 0;
                store.getState().setConnectionState({
                    isConnected: true,
                    isConnecting: false,
                    lastError: null,
                });
            };

            ws.onmessage = (ev) => {
                let msg;
                try {
                    msg = JSON.parse(ev.data);
                } catch {
                    return;
                }
                const s = store.getState();
                if (msg.tip === 'snapshot') s.applySnapshot(msg);
                else if (msg.tip === 'delta') s.applyDelta(msg);
                else if (msg.tip === 'event') s.applyEvent(msg);
            };

            ws.onerror = () => {
                store.getState().setConnectionState({ lastError: 'WebSocket hata' });
            };

            ws.onclose = () => {
                store.getState().setConnectionState({
                    isConnected: false,
                    isConnecting: false,
                });
                if (!closingRef.current) {
                    scheduleReconnect();
                }
            };
        }

        connect();

        return () => {
            closingRef.current = true;
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
            const ws = wsRef.current;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close(1000, 'unmount');
            }
            wsRef.current = null;
        };
    }, []);
}
