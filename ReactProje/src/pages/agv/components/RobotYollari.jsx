/**
 * Aktif robot rotalarını çizgi olarak gösterir.
 *
 * `rotalar` event-tabanlı (rota_hesaplandi); bu yüzden subscribe etmek React render
 * maliyeti açısından kabul edilebilir (sık değişmez).
 */

import { Line } from '@react-three/drei';

import { useAgvStore } from '../../../stores/agvStore';

const ROTA_RENGI = '#fbbf24';
const ROTA_Y = 0.06;

export default function RobotYollari() {
    const rotalar = useAgvStore((s) => s.rotalar);

    return Object.entries(rotalar).map(([robotId, hucreler]) => {
        if (!hucreler || hucreler.length < 2) return null;
        const points = hucreler.map(([x, y]) => [x, ROTA_Y, y]);
        return (
            <Line
                key={robotId}
                points={points}
                color={ROTA_RENGI}
                lineWidth={2.5}
                transparent
                opacity={0.8}
                dashed={true}
                dashScale={2}
                dashSize={1}
            />
        );
    });
}
