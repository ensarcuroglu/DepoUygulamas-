/**
 * Three.js sahne kökü — Canvas + ışık + kamera kontrolü.
 *
 * Sahne sadece `grid` var olduğunda render edilir. Robot mesh'leri `robotIds`
 * üzerinden iter edilir (stable referans, sadece snapshot'ta değişir).
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stats } from '@react-three/drei';

import { useAgvStore } from '../../../stores/agvStore';
import DepoZemini from './DepoZemini';
import RobotMesh from './Robot';
import RobotYollari from './RobotYollari';

export default function DepoSahnesi() {
    const grid = useAgvStore((s) => s.grid);
    const robotIds = useAgvStore((s) => s.robotIds);

    if (!grid) {
        return (
            <div className="flex h-full w-full items-center justify-center text-gray-400">
                Sahne verisi bekleniyor…
            </div>
        );
    }

    const merkezX = grid.genislik / 2 - 0.5;
    const merkezZ = grid.yukseklik / 2 - 0.5;
    const buyukKenar = Math.max(grid.genislik, grid.yukseklik);
    const kameraY = buyukKenar * 1.1;
    const kameraZOfset = buyukKenar * 0.7;

    return (
        <Canvas
            camera={{
                position: [merkezX, kameraY, merkezZ + kameraZOfset],
                fov: 50,
                near: 0.1,
                far: 200,
            }}
            dpr={[1, 2]}
            style={{ background: '#0f172a' }}
        >
            <ambientLight intensity={0.55} />
            <directionalLight
                position={[buyukKenar, buyukKenar * 1.5, buyukKenar]}
                intensity={0.85}
            />

            <DepoZemini grid={grid} />
            <RobotYollari />

            {robotIds.map((id) => (
                <RobotMesh key={id} robotId={id} />
            ))}

            <OrbitControls
                target={[merkezX, 0, merkezZ]}
                maxPolarAngle={Math.PI / 2.05}
                minDistance={3}
                maxDistance={buyukKenar * 2.5}
                enableDamping
            />

            {import.meta.env.DEV && <Stats />}
        </Canvas>
    );
}
