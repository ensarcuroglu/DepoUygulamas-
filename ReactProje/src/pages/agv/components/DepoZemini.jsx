/**
 * Depo zemini + raflar + şarj noktaları.
 * Modeller public/models/ dizininden yüklenir.
 */

import { Instance, Instances, useGLTF, Clone } from '@react-three/drei';
import { useMemo } from 'react';

const ZEMIN_RENGI = '#1e293b';

export default function DepoZemini({ grid }) {
    const { genislik, yukseklik } = grid;
    const raflar = grid.raflar ?? [];
    const sarjlar = grid.sarj_konumlari ?? [];

    const merkezX = genislik / 2 - 0.5;
    const merkezZ = yukseklik / 2 - 0.5;
    const buyukKenar = Math.max(genislik, yukseklik);

    const { scene: rafScene } = useGLTF('/models/Raf.glb');
    const { scene: chargerScene } = useGLTF('/models/AMR_Charger.glb');
    const { scene: zeminScene } = useGLTF('/models/Zemin.glb');

    // Raf modelinin içindeki tüm mesh'leri bul (Çoklu material/mesh içeren modeller için)
    const rafMeshes = useMemo(() => {
        const meshes = [];
        rafScene.traverse((c) => {
            if (c.isMesh) meshes.push(c);
        });
        return meshes;
    }, [rafScene]);

    return (
        <group>
            {/* Zemin (Yansıtıcı koyu zemin + İsteğe bağlı Zemin modeli) */}
            <mesh
                position={[merkezX, -0.05, merkezZ]}
                rotation={[-Math.PI / 2, 0, 0]}
                receiveShadow
            >
                <planeGeometry args={[genislik, yukseklik]} />
                <meshStandardMaterial color={ZEMIN_RENGI} roughness={0.2} metalness={0.8} />
            </mesh>

            <Clone object={zeminScene} position={[merkezX, -0.04, merkezZ]} receiveShadow />

            {/* Grid çizgileri */}
            <gridHelper
                args={[buyukKenar, buyukKenar, '#334155', '#0f172a']}
                position={[merkezX, 0.01, merkezZ]}
            />

            {/* Raflar (instanced, performansı korumak için) */}
            {raflar.length > 0 &&
                rafMeshes.map((mesh, idx) => (
                    <Instances
                        key={`raf-mesh-${idx}`}
                        limit={Math.max(raflar.length, 1)}
                        castShadow
                        receiveShadow
                    >
                        <primitive object={mesh.geometry} attach="geometry" />
                        <primitive object={mesh.material} attach="material" />
                        {raflar.map((raf) => (
                            <Instance
                                key={raf.raf_id}
                                position={[raf.x, 0, raf.y]}
                            />
                        ))}
                    </Instances>
                ))}

            {/* Şarj noktaları */}
            {sarjlar.map((s, i) => (
                <Clone
                    key={`sarj-${i}`}
                    object={chargerScene}
                    position={[s.x, 0, s.y]}
                    castShadow
                />
            ))}
        </group>
    );
}

useGLTF.preload('/models/Raf.glb');
useGLTF.preload('/models/AMR_Charger.glb');
useGLTF.preload('/models/Zemin.glb');
