/**
 * Palet 3D render layer'ı.
 *
 * Backend `paletler` listesinde her palet'in durumu + konumu yayınlanır.
 * Render kuralları:
 *   - KAYNAKTA_BEKLIYOR : Görev oluştu, robot kaynağa varmadı.
 *     Palet sabit kaynak raf koordinatında çizilir.
 *   - ROBOT_UZERINDE    : Robot kaynaktan paleti aldı, taşıyor/bırakıyor.
 *     Palet robotun useFrame interpolated pozisyonuyla senkronize çizilir.
 *   - HEDEFTE_BIRAKILDI : Robot paleti hedef rafa bıraktı.
 *     Palet hedef raf koordinatında kalır.
 *
 * Robot.jsx'teki ad-hoc palet render'ı kaldırılmıştır; tek source of truth
 * burası.
 */

import { useFrame } from '@react-three/fiber';
import { useGLTF, Clone } from '@react-three/drei';
import { useMemo, useRef } from 'react';

import { useAgvStore } from '../../../stores/agvStore';

const LERP_FAKTOR = 0.06;

// Palet z-offset'i durumuna göre değişir:
//  - KAYNAKTA / HEDEFTE: raf konumunda zeminde (raf modelinin önünde)
//  - ROBOT_UZERINDE   : robot platformunun üstünde
const Y_ZEMIN = 0.05;
const Y_ROBOT_USTU = 0.28;

function Palet({ paletKey }) {
    const groupRef = useRef(null);
    const baslatildiRef = useRef(false);

    // Sadece durum'a abone ol; konum useFrame içinden okunur (lerp).
    const durum = useAgvStore((s) => s.paletler[paletKey]?.durum);
    const robotId = useAgvStore((s) => s.paletler[paletKey]?.robot_id);

    const { scene: paletScene } = useGLTF('/models/Palet.glb');

    useFrame(() => {
        const grp = groupRef.current;
        if (!grp) return;
        const palet = useAgvStore.getState().paletler[paletKey];
        if (!palet) return;

        let tx = palet.x;
        let tz = palet.y;
        let ty = Y_ZEMIN;

        if (palet.durum === 'RobotUzerinde' && palet.robot_id) {
            const robot = useAgvStore.getState().robots[palet.robot_id];
            if (robot) {
                tx = robot.x;
                tz = robot.y;
                ty = Y_ROBOT_USTU;
            }
        }

        if (!baslatildiRef.current) {
            grp.position.set(tx, ty, tz);
            baslatildiRef.current = true;
            return;
        }
        grp.position.x += (tx - grp.position.x) * LERP_FAKTOR;
        grp.position.z += (tz - grp.position.z) * LERP_FAKTOR;
        // Y için snap (taşıma/bırakma anında yumuşak geçiş yerine net yer
        // değiştirme — palet "düşmüş" izlenimi vermesin diye küçük lerp).
        grp.position.y += (ty - grp.position.y) * 0.15;
    });

    // Durum tanımlı değilse hiç çizme (BILINMIYOR fallback)
    if (!durum || durum === 'Bilinmiyor') return null;
    // robotId değiştiğinde React zaten re-render'ı tetikler; useFrame
    // her tick okuduğu için ek bir effect gerekmez.
    void robotId;

    return (
        <group ref={groupRef}>
            <Clone object={paletScene} scale={0.6} castShadow />
        </group>
    );
}

export default function Paletler() {
    const paletKeys = useAgvStore((s) => s.paletKeys);
    // useGLTF.preload aynı modeli yeniden yüklemez; tek seferlik.
    useMemo(() => {
        useGLTF.preload('/models/Palet.glb');
    }, []);
    return paletKeys.map((k) => <Palet key={k} paletKey={k} />);
}

useGLTF.preload('/models/Palet.glb');
