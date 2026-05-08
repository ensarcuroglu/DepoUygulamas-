/**
 * Depo zemini + raflar + şarj noktaları + duvarlar.
 *
 * Modeller `public/models/` dizininden yüklenir. Sahnenin koordinat sistemi:
 *   - X grid x'i, Z grid y'si, Y dünya yüksekliği (yukarı).
 *   - Her hücre 1×1 birim.
 *
 * Faz 5 (40×24 layout) için ölçek/offset notları:
 *   - Raf modeli `RAF_SCALE = 0.9` ile cell sınırının içine sığdırılır
 *     (back-to-back rack pair'ları görsel olarak ayırt edilebilsin).
 *   - Şarj istasyonu modeli `SARJ_SCALE = 0.55` ile küçültülür ve cell
 *     içinde z ekseninde +0.25 ofsetlenir; böylece robot cell'in kuzey
 *     yarısına dock olduğunda şarj cihazı arkada görünür (overlap yok).
 *   - Duvar (ENGEL) hücreleri instanced kutu olarak çizilir — depo sınırı
 *     kullanıcıya görünür olsun.
 */

import { Instance, Instances, useGLTF, Clone } from '@react-three/drei';
import { useMemo } from 'react';

const ZEMIN_RENGI = '#1e293b';
const DUVAR_RENGI = '#475569';

// 3D ölçek/ofset sabitleri (cell birimi)
const RAF_SCALE = 0.9;
const SARJ_SCALE = 0.25;
const SARJ_Z_OFFSET = 0.25;   // şarj cihazı cell'in arka yarısında
const DUVAR_YUKSEKLIK = 1.4;
const DUVAR_GENISLIK = 1.0;

export default function DepoZemini({ grid }) {
    const { genislik, yukseklik } = grid;
    const raflar = grid.raflar ?? [];
    const sarjlar = grid.sarj_konumlari ?? [];
    const engeller = grid.engeller ?? [];

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

            {/* Çevre duvarı — instanced kutular (ENGEL hücreleri) */}
            {engeller.length > 0 && (
                <Instances
                    limit={Math.max(engeller.length, 1)}
                    castShadow
                    receiveShadow
                >
                    <boxGeometry args={[DUVAR_GENISLIK, DUVAR_YUKSEKLIK, DUVAR_GENISLIK]} />
                    <meshStandardMaterial color={DUVAR_RENGI} roughness={0.85} metalness={0.1} />
                    {engeller.map((e) => (
                        <Instance
                            key={`duvar-${e.x}-${e.y}`}
                            position={[e.x, DUVAR_YUKSEKLIK / 2, e.y]}
                        />
                    ))}
                </Instances>
            )}

            {/* Raflar (instanced, performansı korumak için).
                Pair'lar back-to-back yerleştirildiği için scale hafifçe küçültülür
                (RAF_SCALE) ki bitişik raflar arasında ince bir kontür kalsın. */}
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
                                scale={[RAF_SCALE, 1, RAF_SCALE]}
                            />
                        ))}
                    </Instances>
                ))}

            {/* Şarj noktaları — küçültülüp cell'in arka yarısına ofsetlenir;
                AGV cell'in ön yarısına dock olur, görsel çakışma yaşanmaz. */}
            {sarjlar.map((s, i) => (
                <Clone
                    key={`sarj-${i}`}
                    object={chargerScene}
                    position={[s.x, 0, s.y + SARJ_Z_OFFSET]}
                    scale={SARJ_SCALE}
                    castShadow
                />
            ))}
        </group>
    );
}

useGLTF.preload('/models/Raf.glb');
useGLTF.preload('/models/AMR_Charger.glb');
useGLTF.preload('/models/Zemin.glb');
