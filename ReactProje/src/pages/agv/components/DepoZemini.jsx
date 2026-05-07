/**
 * Depo zemini + raflar + şarj noktaları.
 *
 * Raflar `<Instances>` ile tek draw call'da render edilir (1000+ raf bile tek mesh).
 * Statik — `grid` referansı sadece snapshot'ta değişir.
 */

import { Instance, Instances } from '@react-three/drei';

const ZEMIN_RENGI = '#1f2937';
const RAF_RENGI = '#3b82f6';
const SARJ_RENGI = '#22c55e';

export default function DepoZemini({ grid }) {
    const { genislik, yukseklik } = grid;
    const raflar = grid.raflar ?? [];
    const sarjlar = grid.sarj_konumlari ?? [];

    const merkezX = genislik / 2 - 0.5;
    const merkezZ = yukseklik / 2 - 0.5;
    const buyukKenar = Math.max(genislik, yukseklik);

    return (
        <group>
            {/* Zemin */}
            <mesh
                position={[merkezX, -0.05, merkezZ]}
                rotation={[-Math.PI / 2, 0, 0]}
                receiveShadow
            >
                <planeGeometry args={[genislik, yukseklik]} />
                <meshStandardMaterial color={ZEMIN_RENGI} />
            </mesh>

            {/* Grid çizgileri */}
            <gridHelper
                args={[buyukKenar, buyukKenar, '#374151', '#111827']}
                position={[merkezX, 0, merkezZ]}
            />

            {/* Raflar (instanced) */}
            {raflar.length > 0 && (
                <Instances limit={Math.max(raflar.length, 1)}>
                    <boxGeometry args={[0.85, 1.2, 0.85]} />
                    <meshStandardMaterial color={RAF_RENGI} />
                    {raflar.map((raf) => (
                        <Instance
                            key={raf.raf_id}
                            position={[raf.x, 0.6, raf.y]}
                        />
                    ))}
                </Instances>
            )}

            {/* Şarj noktaları */}
            {sarjlar.map((s, i) => (
                <mesh key={`sarj-${i}`} position={[s.x, 0.05, s.y]}>
                    <cylinderGeometry args={[0.4, 0.4, 0.1, 16]} />
                    <meshStandardMaterial color={SARJ_RENGI} />
                </mesh>
            ))}
        </group>
    );
}
