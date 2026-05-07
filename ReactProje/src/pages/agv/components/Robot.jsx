/**
 * Robot 3D temsilcisi — useFrame ile lerp interpolasyonu ve yönelme.
 *
 * KRİTİK PERFORMANS NOTU:
 * - Robot'un pozisyon `useAgvStore.getState()` ile her frame'de okunur.
 * - Sadece `durum` (renk değişimi vb. için) selector ile abone olunur.
 * - Bu sayede WS tick'i (5-10 Hz) React render tetiklemez; useFrame 60 FPS'de
 *   smooth interpolasyon yapar.
 */

import { useFrame } from '@react-three/fiber';
import { useMemo, useRef, useState } from 'react';
import { Html, useGLTF, Clone } from '@react-three/drei';
import * as THREE from 'three';

import { useAgvStore } from '../../../stores/agvStore';

const LERP_FAKTOR = 0.06;
const ROTATION_LERP_FAKTOR = 0.08;

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
    const groupRef = useRef(null);
    const baslatildiRef = useRef(false);
    const [hovered, setHovered] = useState(false);

    // Sadece durum'a ve bataryaya subscribe ol
    const durum = useAgvStore((s) => s.robots[robotId]?.durum);
    const batarya = useAgvStore((s) => s.robots[robotId]?.batarya) ?? 100;
    const renk = DURUM_RENK[durum] ?? '#9ca3af';

    const { scene: amrScene } = useGLTF('/models/AMR.glb');
    const { scene: paletScene } = useGLTF('/models/Palet.glb');

    useFrame(() => {
        const group = groupRef.current;
        if (!group) return;
        const robot = useAgvStore.getState().robots[robotId];
        if (!robot) return;

        const tx = robot.x;
        const tz = robot.y;

        if (!baslatildiRef.current) {
            group.position.set(tx, 0, tz); // Zemin hizası
            baslatildiRef.current = true;
            return;
        }

        const dx = tx - group.position.x;
        const dz = tz - group.position.z;
        const distance = Math.sqrt(dx * dx + dz * dz);

        // Linear interpolation for position
        group.position.x += dx * LERP_FAKTOR;
        group.position.z += dz * LERP_FAKTOR;

        // Spherical interpolation for rotation if moving
        if (distance > 0.01) {
            const targetAngle = Math.atan2(dx, dz);
            const targetQuaternion = new THREE.Quaternion().setFromAxisAngle(
                new THREE.Vector3(0, 1, 0),
                targetAngle
            );
            group.quaternion.slerp(targetQuaternion, ROTATION_LERP_FAKTOR);
        }
    });

    if (durum === undefined) return null;

    return (
        <group
            ref={groupRef}
            onPointerOver={(e) => {
                e.stopPropagation();
                setHovered(true);
            }}
            onPointerOut={() => setHovered(false)}
        >
            {/* AGV Modeli - Daha gerçekçi boyutlandırma */}
            <Clone object={amrScene} scale={0.6} castShadow />

            {/* Durum Göstergesi (LED Glow) - Boyuta göre hizalandı */}
            <mesh position={[0, 0.8, 0]}>
                <sphereGeometry args={[0.08, 16, 16]} />
                <meshStandardMaterial
                    color={renk}
                    emissive={renk}
                    emissiveIntensity={2}
                    toneMapped={false}
                />
            </mesh>

            {/* Yük Modeli (Sadece taşıyor veya bırakıyor iken) */}
            {(durum === 'Tasiyor' || durum === 'Birakiyor') && (
                // Palet robotun boyutuna ve platform yüksekliğine göre ayarlandı
                <Clone object={paletScene} scale={0.6} position={[0, 0.28, 0]} castShadow />
            )}

            {/* Kullanıcı Etkileşim Balonu (Glassmorphism Tooltip) */}
            {hovered && (
                <Html position={[0, 1.2, 0]} center className="pointer-events-none">
                    <div className="flex w-32 flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-900/80 p-2 text-[11px] text-white shadow-xl backdrop-blur-md transition-all">
                        <span className="font-bold text-blue-400">AGV-{robotId}</span>
                        <span className="mt-1 font-medium">{durum}</span>
                        <div className="mt-1 flex w-full items-center gap-2">
                            <div className="h-1.5 flex-1 rounded-full bg-slate-700 overflow-hidden">
                                <div
                                    className="h-full bg-green-500"
                                    style={{ width: `${batarya}%` }}
                                />
                            </div>
                            <span className="text-[10px] text-gray-300">%{batarya}</span>
                        </div>
                    </div>
                </Html>
            )}
        </group>
    );
}

useGLTF.preload('/models/AMR.glb');
useGLTF.preload('/models/Palet.glb');
