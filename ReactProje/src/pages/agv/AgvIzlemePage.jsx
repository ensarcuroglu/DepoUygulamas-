/**
 * AGV İzleme Sayfası — Faz 0 placeholder.
 *
 * Faz 2'de Three.js sahnesi (DepoSahnesi), zustand store'lu WS bağlantısı ve
 * görev paneli eklenecek. Detaylı plan: /AGV_SIMULATION_PLAN.md
 */
export default function AgvIzlemePage() {
  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div className="max-w-md text-center">
        <h1 className="mb-2 text-2xl font-semibold text-gray-800">AGV İzleme</h1>
        <p className="text-sm text-gray-500">
          Otonom mobil robot simülasyon modülü yakında. Faz 0 iskeleti hazır;
          3D sahne ve canlı telemetri Faz 2 ile gelecek.
        </p>
      </div>
    </div>
  );
}
