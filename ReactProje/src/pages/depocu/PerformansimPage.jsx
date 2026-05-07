/**
 * PerformansimPage — Depocu rolü için kendi KPI özeti + leaderboard.
 *
 * Mobil odaklı tek sütunlu yerleşim.
 */
import { useMemo } from 'react';
import { motion as Motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Award,
  CalendarDays,
  Clock,
  ListChecks,
  Loader2,
  Trophy,
} from 'lucide-react';
import {
  useKendiPerformansimQuery,
  useLeaderboardQuery,
} from '../../queries/operatorPerformansQueries';
import { useAuth } from '../../contexts/AuthContext';

const intFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const decFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 });

function bugun() {
  return new Date().toISOString().slice(0, 10);
}

function formatSure(saniye) {
  if (!saniye) return '0 dk';
  const dk = Math.round(saniye / 60);
  if (dk < 60) return `${dk} dk`;
  const sa = Math.floor(dk / 60);
  const kalan = dk % 60;
  return kalan === 0 ? `${sa} sa` : `${sa} sa ${kalan} dk`;
}

const RANK_RENKLERI = ['#fbbf24', '#94a3b8', '#fb923c'];

export default function PerformansimPage() {
  const { user } = useAuth();
  const benim = useKendiPerformansimQuery({ gun_sayisi: 7 });
  const leaderboard = useLeaderboardQuery({ vardiya_tarihi: bugun(), limit: 10 });

  const bugunKaydi = benim.data?.bugun;
  const sonGunler = useMemo(
    () => benim.data?.son_gunler ?? [],
    [benim.data],
  );
  const lbItems = useMemo(
    () => leaderboard.data?.items ?? [],
    [leaderboard.data],
  );

  const benimSiram = useMemo(() => {
    const id = user?.id;
    if (!id) return null;
    const yer = lbItems.find((i) => i.kullanici_id === id);
    return yer?.sira ?? null;
  }, [lbItems, user]);

  const haftalikOzet = useMemo(() => {
    const toplamGorev = sonGunler.reduce((acc, g) => acc + (g.toplam_gorev || 0), 0);
    const toplamSn = sonGunler.reduce((acc, g) => acc + (g.toplam_aktif_saniye || 0), 0);
    const toplamIptal = sonGunler.reduce((acc, g) => acc + (g.iptal_sayisi || 0), 0);
    const ortUph = toplamSn > 0 ? toplamGorev / (toplamSn / 3600) : 0;
    return { toplamGorev, toplamSn, toplamIptal, ortUph };
  }, [sonGunler]);

  const yukleniyor = benim.isLoading || leaderboard.isLoading;

  return (
    <div className="px-4 pt-4 pb-6 space-y-5 max-w-2xl mx-auto">
      <header>
        <p className="text-[11px] font-extrabold uppercase tracking-widest text-slate-400">
          Bireysel KPI
        </p>
        <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
          Performansım
        </h1>
      </header>

      {(benim.error || leaderboard.error) && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {benim.error?.message || leaderboard.error?.message || 'Veri alınamadı.'}
        </div>
      )}

      {yukleniyor && (
        <div className="py-10 flex flex-col items-center gap-2 text-slate-400">
          <Loader2 className="w-7 h-7 animate-spin text-blue-500" />
          <p className="text-xs font-bold uppercase tracking-wide">Yükleniyor</p>
        </div>
      )}

      {!yukleniyor && (
        <>
          {/* Bugünün özeti */}
          <Motion.section
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 28 }}
            className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
              <CalendarDays className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <h2 className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                Bugün
              </h2>
              {benimSiram && (
                <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-500/10 px-2.5 py-1 text-[11px] font-extrabold text-amber-700 dark:text-amber-400">
                  <Trophy className="w-3 h-3" />
                  Sıra {benimSiram}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3 p-4">
              <BireyselKart
                baslik="Toplam Görev"
                deger={intFormat.format(bugunKaydi?.toplam_gorev || 0)}
                alt={`${intFormat.format(bugunKaydi?.tamamlanan_yerlestirme || 0)} yerleştir + ${intFormat.format(bugunKaydi?.tamamlanan_toplama || 0)} topla`}
                icon={ListChecks}
                renk="text-blue-600"
              />
              <BireyselKart
                baslik="UPH"
                deger={decFormat.format(bugunKaydi?.uph || 0)}
                alt={formatSure(bugunKaydi?.toplam_aktif_saniye || 0)}
                icon={Activity}
                renk="text-emerald-600"
              />
              <BireyselKart
                baslik="Aktif Süre"
                deger={formatSure(bugunKaydi?.toplam_aktif_saniye || 0)}
                alt={`Ort. ${decFormat.format(bugunKaydi?.ortalama_gorev_suresi_sn || 0)} sn / görev`}
                icon={Clock}
                renk="text-violet-600"
              />
              <BireyselKart
                baslik="İptal"
                deger={intFormat.format(bugunKaydi?.iptal_sayisi || 0)}
                alt={`${decFormat.format((bugunKaydi?.hata_orani || 0) * 100)}% hata`}
                icon={AlertTriangle}
                renk={
                  (bugunKaydi?.hata_orani || 0) > 0.1
                    ? 'text-rose-600'
                    : 'text-amber-600'
                }
              />
            </div>
          </Motion.section>

          {/* Haftalık özet */}
          <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-500" />
              <h2 className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                Son 7 Gün
              </h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4">
              <KucukKart
                etiket="Görev"
                deger={intFormat.format(haftalikOzet.toplamGorev)}
              />
              <KucukKart
                etiket="Aktif Süre"
                deger={formatSure(haftalikOzet.toplamSn)}
              />
              <KucukKart
                etiket="Ort. UPH"
                deger={decFormat.format(haftalikOzet.ortUph)}
              />
              <KucukKart
                etiket="İptal"
                deger={intFormat.format(haftalikOzet.toplamIptal)}
                vurgu={haftalikOzet.toplamIptal > 0 ? 'text-rose-600' : undefined}
              />
            </div>

            {sonGunler.length > 0 && (
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {sonGunler.map((g) => (
                  <li
                    key={g.vardiya_tarihi}
                    className="flex items-center justify-between px-4 py-2.5 text-sm"
                  >
                    <span className="font-bold text-slate-700 dark:text-slate-200">
                      {g.vardiya_tarihi}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400 font-semibold">
                      {g.toplam_gorev} görev
                    </span>
                    <span className="font-extrabold text-blue-700 dark:text-blue-400">
                      {decFormat.format(g.uph)} UPH
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Leaderboard */}
          <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-500" />
              <h2 className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                Bugünün Lider Tablosu
              </h2>
            </div>
            {lbItems.length === 0 ? (
              <div className="py-8 text-center text-sm font-semibold text-slate-400">
                Henüz kayıt yok — ilk sıraya tutun!
              </div>
            ) : (
              <ol className="divide-y divide-slate-100 dark:divide-slate-800">
                {lbItems.map((item) => {
                  const benimMi = item.kullanici_id === user?.id;
                  return (
                    <li
                      key={item.kullanici_id}
                      className={`flex items-center gap-3 px-4 py-2.5 ${
                        benimMi
                          ? 'bg-blue-50 dark:bg-blue-500/10'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                      }`}
                    >
                      <span
                        className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-extrabold ${
                          item.sira <= 3
                            ? 'text-white shadow-sm'
                            : 'text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800'
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
                        <p
                          className={`text-sm font-bold truncate ${
                            benimMi
                              ? 'text-blue-800 dark:text-blue-300'
                              : 'text-slate-800 dark:text-slate-100'
                          }`}
                        >
                          {item.operator_adi || `#${item.kullanici_id}`}
                          {benimMi && (
                            <span className="ml-2 inline-flex rounded-full bg-blue-600 text-white text-[10px] px-2 py-0.5 font-extrabold tracking-wide">
                              SEN
                            </span>
                          )}
                        </p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold">
                          {item.toplam_gorev} görev · {formatSure(item.toplam_aktif_saniye)}
                        </p>
                      </div>
                      <span className="text-sm font-extrabold text-blue-700 dark:text-blue-400">
                        {decFormat.format(item.uph)}
                      </span>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function BireyselKart({ baslik, deger, alt, icon, renk }) {
  const IconCmp = icon;
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 p-3.5">
      <div className="flex items-center justify-between">
        <p className="text-[10.5px] font-extrabold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {baslik}
        </p>
        <IconCmp className={`w-4 h-4 ${renk}`} />
      </div>
      <p className="mt-1.5 text-xl font-black text-slate-900 dark:text-white">
        {deger}
      </p>
      {alt && (
        <p className="mt-0.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {alt}
        </p>
      )}
    </div>
  );
}

function KucukKart({ etiket, deger, vurgu }) {
  return (
    <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 px-3 py-2.5 text-center">
      <p className="text-[10.5px] font-extrabold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {etiket}
      </p>
      <p
        className={`mt-1 text-base font-black ${
          vurgu || 'text-slate-900 dark:text-white'
        }`}
      >
        {deger}
      </p>
    </div>
  );
}
