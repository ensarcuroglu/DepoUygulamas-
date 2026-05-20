/**
 * Three.js sahne kökü — Canvas + ışık + kamera kontrolü.
 *
 * Sahne sadece `grid` var olduğunda render edilir. Robot mesh'leri `robotIds`
 * üzerinden iter edilir (stable referans, sadece snapshot'ta değişir).
 */

import { Canvas } from '@react-three/fiber';
import React, { Suspense, Component } from 'react';
import { OrbitControls, Stats, Environment, Html } from '@react-three/drei';
import { Loader2 } from 'lucide-react';

import { useAgvStore } from '../../../stores/agvStore';
import DepoZemini from './DepoZemini';
import Paletler from './Paletler';
import RobotMesh from './Robot';
import RobotYollari from './RobotYollari';

function SahneFallback() {
    return (
        <Html center>
            <div className="flex items-center gap-2.5 rounded-xl bg-slate-950/80 border border-blue-500/30 px-4 py-3 text-xs text-blue-400 font-bold shadow-[0_0_15px_rgba(59,130,246,0.15)] backdrop-blur whitespace-nowrap">
                <Loader2 size={14} className="animate-spin text-blue-400" />
                <span>3D Depo Ortamı Yükleniyor…</span>
            </div>
        </Html>
    );
}

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error("3D Sahne Hatası:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="flex h-full w-full flex-col items-center justify-center p-6 text-red-500 text-center">
                    <h2 className="mb-2 text-lg font-bold">3D Görselleştirme Hatası</h2>
                    <p className="text-sm font-mono bg-red-900/20 p-2 rounded">{this.state.error?.message}</p>
                </div>
            );
        }
        return this.props.children;
    }
}

export default function DepoSahnesi() {
    const grid = useAgvStore((s) => s.grid);
    const robotIds = useAgvStore((s) => s.robotIds);
    const setSelectedRobotId = useAgvStore((s) => s.setSelectedRobotId);

    if (!grid) {
        return (
            <div className="flex h-full w-full items-center justify-center text-slate-500 font-semibold">
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
        <ErrorBoundary>
            <Canvas
                camera={{
                    position: [merkezX, kameraY, merkezZ + kameraZOfset],
                    fov: 50,
                    near: 0.1,
                    far: 200,
                }}
                dpr={[1, 1.5]}
                shadows
                onPointerMissed={() => setSelectedRobotId(null)}
            >
                <color attach="background" args={['#020617']} />
                
                <fog attach="fog" args={['#020617', buyukKenar * 0.8, buyukKenar * 2.5]} />
                
                <ambientLight intensity={0.45} />
                <directionalLight
                    position={[buyukKenar, buyukKenar * 1.5, buyukKenar]}
                    intensity={1.1}
                    castShadow
                    shadow-mapSize={[1024, 1024]}
                    shadow-camera-near={1}
                    shadow-camera-far={buyukKenar * 3}
                    shadow-camera-left={-buyukKenar}
                    shadow-camera-right={buyukKenar}
                    shadow-camera-top={buyukKenar}
                    shadow-camera-bottom={-buyukKenar}
                />
                
                <pointLight
                    position={[merkezX, 12, merkezZ]}
                    intensity={0.5}
                    color="#06b6d4"
                    distance={buyukKenar * 2.2}
                />

                <Suspense fallback={<SahneFallback />}>
                    <Environment preset="warehouse" />
                    <DepoZemini grid={grid} />
                    <RobotYollari />
                    <Paletler />

                    {robotIds.map((id) => (
                        <RobotMesh key={id} robotId={id} />
                    ))}
                </Suspense>

                <OrbitControls
                    target={[merkezX, 0, merkezZ]}
                    maxPolarAngle={Math.PI / 2.05}
                    minDistance={3}
                    maxDistance={buyukKenar * 2.5}
                    enableDamping
                />

                {import.meta.env.DEV && <Stats />}
            </Canvas>
        </ErrorBoundary>
    );
}
