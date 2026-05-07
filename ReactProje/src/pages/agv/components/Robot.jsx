/**
 * Robot 3D temsilcisi — useFrame ile lerp interpolasyonu.
 *
 * KRİTİK PERFORMANS NOTU:
 * - Robot'un pozisyon `useAgvStore.getState()` ile her frame'de okunur (subscribe yok).
 * - Sadece `durum` (renk değişimi için) selector ile abone olunur.
 * - Bu sayede WS tick'i (5-10 Hz) React render tetiklemez; useFrame 60 FPS'de
 *   smooth interpolasyon yapar.
 */

import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';

import { useAgvStore } from '../../../stores/agvStore';

const LERP_FAKTOR = 0.18;

const DURUM_RENK = {
    Bos: '#9ca3af',
    KaynagaGidiyor: '#fbbf24',
    Yukluyor: '#fb923c',
    Tasiyor: '#10b981',
    Birakiyor: '#fb923c',
    TamamlandiBildirim: '#3b82f6',
    HataDuruyor: '#ef4444',
};

export default function RobotMesh({ robotId }) {
    const meshRef = useRef(null);
    const baslatildiRef = useRef(false);

    // Sadece durum'a subscribe ol — pozisyon değil.
    const durum = useAgvStore((s) => s.robots[robotId]?.durum);
    const renk = DURUM_RENK[durum] ?? '#9ca3af';

    const baslangicKonumu = useMemo(() => {
        const r = useAgvStore.getState().robots[robotId];
        return r ? [r.x, 0.3, r.y] : [0, 0.3, 0];
    }, [robotId]);

    useFrame(() => {
        const mesh = meshRef.current;
        if (!mesh) return;
        const robot = useAgvStore.getState().robots[robotId];
        if (!robot) return;

        const tx = robot.x;
        const tz = robot.y;

        if (!baslatildiRef.current) {
            mesh.position.set(tx, 0.3, tz);
            baslatildiRef.current = true;
            return;
        }

        // Linear interpolation — lerp factor 0.18 → ~5 frame'de hedefe %90
        mesh.position.x += (tx - mesh.position.x) * LERP_FAKTOR;
        mesh.position.z += (tz - mesh.position.z) * LERP_FAKTOR;
    });

    if (durum === undefined) return null;

    return (
        <group>
            <mesh ref={meshRef} position={baslangicKonumu} castShadow>
                <boxGeometry args={[0.6, 0.4, 0.85]} />
                <meshStandardMaterial color={renk} />
            </mesh>
        </group>
    );
}
