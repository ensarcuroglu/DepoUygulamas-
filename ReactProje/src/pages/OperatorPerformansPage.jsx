/**
 * OperatorPerformansPage — Admin / Lojistik için operatör KPI özeti.
 *
 * - Tarih aralığı + depo filtreli vardiya tablosu
 * - Tek günlük UPH leaderboard'u
 * - Recharts bar grafiği: ilk 10 operatörün UPH karşılaştırması
 */
import { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertTriangle,
  Award,
  BarChart3,
  Loader2,
  RefreshCw,
  TrendingUp,
  Trophy,
  Users,
} from 'lucide-react';
import {
  useLeaderboardQuery,
  useOperatorOzetQuery,
} from '../queries/operatorPerformansQueries';
import { useDepolarQuery } from '../queries/locationQueries';

const intFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const decFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 });

function bugun() {
  return new Date().toISOString().slice(0, 10);
}
function gunOnce(g) {
  const d = new Date();
  d.setDate(d.getDate() - g);
  return d.toISOString().slice(0, 10);
}

function formatSure(saniye) {
  if (!saniye) return '0 dk';
  const dk = Math.round(saniye / 60);
  if (dk < 60) return `${dk} dk`;
  const sa = Math.floor(dk / 60);
  const kalan = dk % 60;
  return kalan === 0 ? `${sa} sa` : `${sa} sa ${kalan} dk`;
}

function HataKutusu({ mesaj }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700 flex items-center gap-2">
      <AlertTriangle className="w-4 h-4" />
      {mesaj}
    </div>
  );
}

const RANK_RENKLERI = ['#fbbf24', '#94a3b8', '#fb923c'];

export default function OperatorPerformansPage() {
  const [baslangic, setBaslangic] = useState(() => gunOnce(6));
  const [bitis, setBitis] = useState(() => bugun());
  const [depoId, setDepoId] = useState('');

  const ozetParams = useMemo(() => {
    const p = { baslangic, bitis, limit: 200 };
    if (depoId) p.depo_id = Number(depoId);
    return p;
  }, [baslangic, bitis, depoId]);

  const leaderboardParams = useMemo(() => {
    const p = { vardiya_tarihi: bitis, limit: 10 };
    if (depoId) p.depo_id = Number(depoId);
    return p;
  }, [bitis, depoId]);

  const { data: depoData } = useDepolarQuery({ limit: 100 });
  const depolar = depoData ?? [];

  const ozetSorgu = useOperatorOzetQuery(ozetParams);
  const leaderboardSorgu = useLeaderboardQuery(leaderboardParams);

  const items = useMemo(
    () => ozetSorgu.data?.items ?? [],
    [ozetSorgu.data],
  );
  const lbItems = useMemo(
    () => leaderboardSorgu.data?.items ?? [],
    [leaderboardSorgu.data],
  );

  const grafikData = useMemo(
    () =>
      lbItems.map((i) => ({
        ad: i.operator_adi || `#${i.kullanici_id}`,
        UPH: Number(i.uph || 0),
      })),
    [lbItems],
  );

  const kpiOzet = useMemo(() => {
    const aktif = items.filter((i) => i.toplam_aktif_saniye > 0);
    const toplamGorev = items.reduce((acc, i) => acc + (i.toplam_gorev || 0), 0);
    const toplamSn = items.reduce((acc, i) => acc + (i.toplam_aktif_saniye || 0), 0);
    const ortUph = toplamSn > 0 ? toplamGorev / (toplamSn / 3600) : 0;
    return {
      operatorSayisi: new Set(items.map((i) => i.kullanici_id)).size,
      aktifVardiya: aktif.length,
      toplamGorev,
      ortUph,
    };
  }, [items]);

  const yenile = () => {
    ozetSorgu.refetch();
    leaderboardSorgu.refetch();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-5 pb-10">
      {/* Başlık */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Operatör Performansı
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Vardiya bazlı KPI'lar, UPH karşılaştırması ve günün lider tablosu
          </p>
        </div>
        <button
          onClick={yenile}
          disabled={ozetSorgu.isFetching || leaderboardSorgu.isFetching}
          className="inline-flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-bold text-slate-600 shadow-sm transition hover:border-blue-200 hover:text-blue-700 disabled:opacity-60"
        >
          <RefreshCw
            className={`w-4 h-4 ${
              ozetSorgu.isFetching || leaderboardSorgu.isFetching ? 'animate-spin' : ''
            }`}
          />
          Yenile
        </button>
      </div>

      {/* Filtre Çubuğu */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Başlangıç
          </label>
          <input
            type="date"
            value={baslangic}
            max={bitis}
            onChange={(e) => setBaslangic(e.target.value)}
            className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Bitiş
          </label>
          <input
            type="date"
            value={bitis}
            min={baslangic}
            max={bugun()}
            onChange={(e) => setBitis(e.target.value)}
            className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
            Depo
          </label>
          <select
            value={depoId}
            onChange={(e) => setDepoId(e.target.value)}
            className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
          >
            <option value="">Tümü</option>
            {depolar.map((d) => (
              <option key={d.id} value={d.id}>
                {d.isim}
              </option>
            ))}
          </select>
        </div>
      </div>

      {(ozetSorgu.error || leaderboardSorgu.error) && (
        <HataKutusu
          mesaj={
            ozetSorgu.error?.message ||
            leaderboardSorgu.error?.message ||
            'Veri alınamadı.'
          }
        />
      )}

      {/* Üst KPI kartları */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KartUst
          baslik="Operatör"
          deger={intFormat.format(kpiOzet.operatorSayisi)}
          icon={Users}
          renk="text-blue-600"
        />
        <KartUst
          baslik="Aktif Vardiya"
          deger={intFormat.format(kpiOzet.aktifVardiya)}
          icon={TrendingUp}
          renk="text-emerald-600"
        />
        <KartUst
          baslik="Toplam Görev"
          deger={intFormat.format(kpiOzet.toplamGorev)}
          icon={BarChart3}
          renk="text-violet-600"
        />
        <KartUst
          baslik="Ort. UPH"
          deger={decFormat.format(kpiOzet.ortUph)}
          icon={Award}
          renk="text-amber-600"
        />
      </div>

      {/* Leaderboard + Grafik */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="lg:col-span-1 rounded-lg border border-slate-200 bg-white shadow-sm">
          <header className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-500" />
              <h2 className="text-sm font-extrabold tracking-wide text-slate-800">
                Lider Tablosu — {bitis}
              </h2>
            </div>
          </header>
          {leaderboardSorgu.isLoading ? (
            <YukleniyorBlok />
          ) : lbItems.length === 0 ? (
            <BosBlok mesaj="Bu gün için kayıt bulunamadı." />
          ) : (
            <ol className="divide-y divide-slate-100">
              {lbItems.map((item) => (
                <li
                  key={item.kullanici_id}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
                >
                  <span
                    className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-extrabold ${
                      item.sira <= 3
                        ? 'text-white shadow-sm'
                        : 'text-slate-600 bg-slate-100'
                    }`}
                    style={
                      item.sira <= 3
                        ? { backgroundColor: RANK_RENKLERI[item.sira - 1] }
                        : undefined
                    }
                  >
                    {item.sira}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-800 truncate">
                      {item.operator_adi || `#${item.kullanici_id}`}
                    </p>
                    <p className="text-xs text-slate-500 font-semibold truncate">
                      {item.toplam_gorev} görev · {formatSure(item.toplam_aktif_saniye)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-extrabold text-blue-700">
                      {decFormat.format(item.uph)}
                    </p>
                    <p className="text-[10px] uppercase tracking-wide text-slate-400 font-bold">
                      UPH
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="lg:col-span-2 rounded-lg border border-slate-200 bg-white shadow-sm">
          <header className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
            <BarChart3 className="w-4 h-4 text-blue-500" />
            <h2 className="text-sm font-extrabold tracking-wide text-slate-800">
              UPH Karşılaştırması
            </h2>
          </header>
          <div className="p-4 h-[340px]">
            {grafikData.length === 0 ? (
              <BosBlok mesaj="Grafiği oluşturacak veri yok." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={grafikData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="ad"
                    tick={{ fontSize: 11, fontWeight: 600, fill: '#475569' }}
                    interval={0}
                    angle={-15}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                  <RechartsTooltip
                    formatter={(value) => [decFormat.format(value), 'UPH']}
                    contentStyle={{
                      borderRadius: 8,
                      border: '1px solid #e2e8f0',
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="UPH" radius={[6, 6, 0, 0]}>
                    {grafikData.map((_, idx) => (
                      <Cell
                        key={idx}
                        fill={
                          idx < 3 ? RANK_RENKLERI[idx] : '#3b82f6'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>
      </div>

      {/* Detay Tablo */}
      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <header className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <h2 className="text-sm font-extrabold tracking-wide text-slate-800">
            Vardiya Detayı
          </h2>
          <span className="text-xs text-slate-500 font-semibold">
            {ozetSorgu.data?.toplam ?? 0} kayıt
          </span>
        </header>
        {ozetSorgu.isLoading ? (
          <YukleniyorBlok />
        ) : items.length === 0 ? (
          <BosBlok mesaj="Bu aralıkta kayıt bulunamadı." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs font-extrabold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 text-left">Operatör</th>
                  <th className="px-4 py-3 text-left">Depo</th>
                  <th className="px-4 py-3 text-left">Vardiya</th>
                  <th className="px-4 py-3 text-right">Yerleştirme</th>
                  <th className="px-4 py-3 text-right">Toplama</th>
                  <th className="px-4 py-3 text-right">İptal</th>
                  <th className="px-4 py-3 text-right">Aktif</th>
                  <th className="px-4 py-3 text-right">UPH</th>
                  <th className="px-4 py-3 text-right">Hata %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((m) => (
                  <tr key={`${m.kullanici_id}-${m.vardiya_tarihi}`} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-bold text-slate-800">
                      {m.operator_adi || `#${m.kullanici_id}`}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{m.depo_adi || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{m.vardiya_tarihi}</td>
                    <td className="px-4 py-3 text-right font-bold text-slate-700">
                      {intFormat.format(m.tamamlanan_yerlestirme)}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-700">
                      {intFormat.format(m.tamamlanan_toplama)}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-bold ${
                        m.iptal_sayisi > 0 ? 'text-rose-600' : 'text-slate-400'
                      }`}
                    >
                      {intFormat.format(m.iptal_sayisi)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {formatSure(m.toplam_aktif_saniye)}
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-blue-700">
                      {decFormat.format(m.uph)}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-bold ${
                        m.hata_orani > 0.1 ? 'text-rose-600' : 'text-emerald-600'
                      }`}
                    >
                      {decFormat.format(m.hata_orani * 100)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function KartUst({ baslik, deger, icon, renk }) {
  const IconCmp = icon;
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs font-extrabold uppercase tracking-wide text-slate-500">
          {baslik}
        </p>
        <IconCmp className={`w-4 h-4 ${renk}`} />
      </div>
      <p className="mt-2 text-2xl font-black text-slate-900">{deger}</p>
    </div>
  );
}

function YukleniyorBlok() {
  return (
    <div className="py-12 flex flex-col items-center gap-2 text-slate-400">
      <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      <p className="text-xs font-bold uppercase tracking-wide">Yükleniyor</p>
    </div>
  );
}

function BosBlok({ mesaj }) {
  return (
    <div className="py-10 text-center text-sm font-semibold text-slate-400">
      {mesaj}
    </div>
  );
}
