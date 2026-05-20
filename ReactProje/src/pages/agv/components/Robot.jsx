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
import { useRef, useState } from 'react';
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
    BeklemeYerineDonuyor: '#60a5fa',
    HataDuruyor: '#ef4444',
};

export default function RobotMesh({ robotId }) {
    const groupRef = useRef(null);
    const baslatildiRef = useRef(false);
    const [hovered, setHovered] = useState(false);

    // Sadece durum'a ve bataryaya subscribe ol
    const durum = useAgvStore((s) => s.robots[robotId]?.durum);
    const batarya = useAgvStore((s) => s.robots[robotId]?.batarya) ?? 100;
    const isSelected = useAgvStore((s) => s.selectedRobotId === robotId);
    const setSelectedRobotId = useAgvStore((s) => s.setSelectedRobotId);
    const renk = DURUM_RENK[durum] ?? '#9ca3af';

    const { scene: amrScene } = useGLTF('/models/AMR.glb');

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
                document.body.style.cursor = 'pointer';
            }}
            onPointerOut={() => {
                setHovered(false);
                document.body.style.cursor = 'auto';
            }}
            onClick={(e) => {
                e.stopPropagation();
                setSelectedRobotId(isSelected ? null : robotId);
            }}
        >
            {/* AGV Modeli - Daha gerçekçi boyutlandırma */}
            <Clone object={amrScene} scale={isSelected ? 0.25 : 0.2} castShadow />

            {/* Seçim halkası — yere yakın yatay daire (sadece seçiliyken) */}
            {isSelected && (
                <mesh position={[-1.75, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                    <ringGeometry args={[0.55, 0.7, 32]} />
                    <meshBasicMaterial color="#60a5fa" transparent opacity={0.85} />
                </mesh>
            )}

            {/* Durum Göstergesi (LED Glow) - Boyuta göre hizalandı */}
            <mesh position={[-1.4, 1, 0]}>
                <sphereGeometry args={[0.08, 16, 16]} />
                <meshStandardMaterial
                    color={renk}
                    emissive={renk}
                    emissiveIntensity={2}
                    toneMapped={false}
                />
            </mesh>

            {/* Palet render Paletler.jsx içinde — tek source of truth. */}

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
