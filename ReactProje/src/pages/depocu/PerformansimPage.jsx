/**
 * PerformansimPage — Depocu rolü için kendi KPI özeti + leaderboard.
 *
 * Mobil odaklı, "Soft Glassmorphism & Minimal" estetiğiyle tasarlanmış tek sütunlu yerleşim.
 */
import { useMemo } from 'react';
import { motion as Motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Award,
  CalendarDays,
  Clock,
  ListChecks,
  Loader2,
  Trophy,
  ArrowLeft,
  ChevronRight,
  Zap
} from 'lucide-react';
import {
  useKendiPerformansimQuery,
  useLeaderboardQuery,
} from '../../queries/operatorPerformansQueries';
import { useAuth } from '../../contexts/AuthContext';

const intFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 });
const decFormat = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 1 });

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

// Gold, Silver, Bronze for top 3
const RANK_STYLES = [
  { bg: 'bg-gradient-to-br from-amber-300 to-yellow-600', text: 'text-white', shadow: 'shadow-amber-500/30' },
  { bg: 'bg-gradient-to-br from-slate-300 to-slate-500', text: 'text-white', shadow: 'shadow-slate-500/20' },
  { bg: 'bg-gradient-to-br from-orange-300 to-orange-600', text: 'text-white', shadow: 'shadow-orange-500/20' }
];

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.05 }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 400, damping: 30 } }
};

export default function PerformansimPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const benim = useKendiPerformansimQuery({ gun_sayisi: 7 });
  const leaderboard = useLeaderboardQuery({ vardiya_tarihi: bugun(), limit: 10 });

  const bugunKaydi = benim.data?.bugun;
  const sonGunler = useMemo(() => benim.data?.son_gunler ?? [], [benim.data]);
  const lbItems = useMemo(() => leaderboard.data?.items ?? [], [leaderboard.data]);

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
    <Motion.div 
      className="mx-auto max-w-md space-y-6 p-4 sm:max-w-2xl sm:p-6 pb-32"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {/* HEADER WITH BACK BUTTON */}
      <Motion.header variants={itemVariants} className="flex items-center gap-4 px-1">
        <button 
          onClick={() => navigate(-1)}
          className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/50 dark:bg-white/5 border border-slate-200/50 dark:border-slate-800/50 text-slate-600 dark:text-slate-300 shadow-sm active:scale-95 transition-transform"
        >
          <ArrowLeft className="h-5 w-5" strokeWidth={2.5} />
        </button>
        <div>
          <p className="text-[11px] font-extrabold uppercase tracking-widest text-slate-400 dark:text-slate-500">
            Bireysel KPI
          </p>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight leading-none mt-0.5">
            Performansım
          </h1>
        </div>
      </Motion.header>

      {(benim.error || leaderboard.error) && (
        <Motion.div variants={itemVariants} className="rounded-2xl border border-rose-200/60 bg-rose-50/80 px-4 py-3 text-sm font-semibold text-rose-700 flex items-center gap-3 backdrop-blur-md">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" strokeWidth={2.5} />
          {benim.error?.message || leaderboard.error?.message || 'Veri alınamadı.'}
        </Motion.div>
      )}

      {yukleniyor && (
        <div className="py-20 flex flex-col items-center gap-3 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" strokeWidth={2.5} />
          <p className="text-[11px] font-extrabold uppercase tracking-widest">Veriler Derleniyor</p>
        </div>
      )}

      {!yukleniyor && (
        <>
          {/* HERO RANK CARD */}
          <Motion.section variants={itemVariants} className="relative overflow-hidden rounded-[32px] p-1 shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.2)]">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-indigo-600 opacity-90" />
            
            <div className="relative bg-white/10 dark:bg-black/20 backdrop-blur-xl w-full rounded-[28px] border border-white/20 p-6 overflow-hidden">
              {/* Dynamic glowing orb inside */}
              <Motion.div 
                  className="absolute -right-10 -bottom-10 w-48 h-48 bg-white/20 rounded-full blur-3xl"
                  animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              />
              
              <div className="relative z-10 flex flex-col items-center justify-center text-center">
                <div className="flex items-center gap-2 mb-2 text-white/90">
                  <CalendarDays className="w-4 h-4" />
                  <span className="text-sm font-bold tracking-wide uppercase">Bugün</span>
                </div>
                
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-6xl font-black text-white drop-shadow-md tracking-tighter">
                    {benimSiram ? `#${benimSiram}` : '-'}
                  </span>
                </div>
                <p className="mt-1 text-sm font-semibold text-white/80">
                  Günlük Lider Tablosu Sıralamanız
                </p>
              </div>
            </div>
          </Motion.section>

          {/* DETAILED STATS GRID */}
          <Motion.section variants={itemVariants} className="grid grid-cols-2 gap-3">
            <BireyselKart
              baslik="UPH (Hız)"
              deger={decFormat.format(bugunKaydi?.uph || 0)}
              alt="Adet / Saat"
              icon={Zap}
              renk="text-amber-500 dark:text-amber-400"
              bgRenk="bg-amber-50 dark:bg-amber-500/10"
              vurgu={true}
            />
            <BireyselKart
              baslik="Toplam Görev"
              deger={intFormat.format(bugunKaydi?.toplam_gorev || 0)}
              alt={`${intFormat.format(bugunKaydi?.tamamlanan_yerlestirme || 0)} Y + ${intFormat.format(bugunKaydi?.tamamlanan_toplama || 0)} T`}
              icon={ListChecks}
              renk="text-blue-500 dark:text-blue-400"
              bgRenk="bg-blue-50 dark:bg-blue-500/10"
            />
            <BireyselKart
              baslik="Aktif Süre"
              deger={formatSure(bugunKaydi?.toplam_aktif_saniye || 0)}
              alt={`Ort. ${decFormat.format(bugunKaydi?.ortalama_gorev_suresi_sn || 0)} sn / görev`}
              icon={Clock}
              renk="text-violet-500 dark:text-violet-400"
              bgRenk="bg-violet-50 dark:bg-violet-500/10"
            />
            <BireyselKart
              baslik="İptal / Hata"
              deger={intFormat.format(bugunKaydi?.iptal_sayisi || 0)}
              alt={`${decFormat.format((bugunKaydi?.hata_orani || 0) * 100)}% Hata`}
              icon={AlertTriangle}
              renk={(bugunKaydi?.hata_orani || 0) > 0.1 ? 'text-rose-500 dark:text-rose-400' : 'text-slate-400'}
              bgRenk={(bugunKaydi?.hata_orani || 0) > 0.1 ? 'bg-rose-50 dark:bg-rose-500/10' : 'bg-slate-50 dark:bg-slate-800/40'}
            />
          </Motion.section>

          {/* LEADERBOARD */}
          <Motion.section variants={itemVariants} className="pt-2">
            <div className="flex items-center justify-between px-2 mb-4">
              <h2 className="text-lg font-black text-slate-900 dark:text-white tracking-tight">
                Günün Liderleri
              </h2>
              <Trophy className="w-5 h-5 text-amber-500" />
            </div>

            <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[28px] border border-slate-200/60 dark:border-slate-800/60 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] overflow-hidden">
              {lbItems.length === 0 ? (
                <div className="py-12 text-center">
                  <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Trophy className="w-6 h-6 text-slate-300 dark:text-slate-600" />
                  </div>
                  <p className="text-sm font-semibold text-slate-500">Henüz kayıt yok.</p>
                  <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mt-1">İlk sıraya tutun!</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-slate-100/80 dark:divide-slate-800/80">
                  {lbItems.map((item) => {
                    const benimMi = item.kullanici_id === user?.id;
                    const isTop3 = item.sira <= 3;
                    const rankStyle = isTop3 ? RANK_STYLES[item.sira - 1] : null;

                    return (
                      <div
                        key={item.kullanici_id}
                        className={`flex items-center gap-4 px-5 py-4 transition-colors ${
                          benimMi ? 'bg-blue-50/50 dark:bg-blue-500/5' : 'hover:bg-slate-50/50 dark:hover:bg-slate-800/20'
                        }`}
                      >
                        <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full text-[13px] font-black ${
                          isTop3 ? `${rankStyle.bg} ${rankStyle.text} shadow-lg ${rankStyle.shadow}` : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                        }`}>
                          {item.sira}
                        </div>
                        
                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                          <p className={`text-sm font-bold truncate ${benimMi ? 'text-blue-700 dark:text-blue-400' : 'text-slate-800 dark:text-slate-200'}`}>
                            {item.operator_adi || `Operatör #${item.kullanici_id}`}
                            {benimMi && (
                              <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-black tracking-widest uppercase bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400">
                                SEN
                              </span>
                            )}
                          </p>
                          <p className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mt-0.5">
                            {item.toplam_gorev} Görev · {formatSure(item.toplam_aktif_saniye)}
                          </p>
                        </div>
                        
                        <div className="flex flex-col items-end justify-center">
                          <span className={`text-lg font-black tracking-tight ${
                            isTop3 ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'
                          }`}>
                            {decFormat.format(item.uph)}
                          </span>
                          <span className="text-[9px] font-extrabold uppercase tracking-widest text-slate-400">UPH</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Motion.section>

          {/* WEEKLY SUMMARY */}
          <Motion.section variants={itemVariants} className="pt-2">
            <p className="mb-3 text-[11px] font-extrabold uppercase tracking-widest text-slate-500 dark:text-slate-400 px-2">
              Son 7 Gün Özeti
            </p>
            <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] border border-slate-200/60 dark:border-slate-800/60 shadow-sm p-5 grid grid-cols-2 gap-4">
               <div>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">Toplam Görev</p>
                  <p className="text-xl font-black text-slate-800 dark:text-slate-200 mt-0.5">{intFormat.format(haftalikOzet.toplamGorev)}</p>
               </div>
               <div>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">Ort. UPH</p>
                  <p className="text-xl font-black text-blue-600 dark:text-blue-400 mt-0.5">{decFormat.format(haftalikOzet.ortUph)}</p>
               </div>
               <div>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">Aktif Süre</p>
                  <p className="text-xl font-black text-slate-800 dark:text-slate-200 mt-0.5">{formatSure(haftalikOzet.toplamSn)}</p>
               </div>
               <div>
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">İptal</p>
                  <p className={`text-xl font-black mt-0.5 ${haftalikOzet.toplamIptal > 0 ? 'text-rose-500' : 'text-slate-800 dark:text-slate-200'}`}>
                    {intFormat.format(haftalikOzet.toplamIptal)}
                  </p>
               </div>
            </div>
          </Motion.section>

        </>
      )}
    </Motion.div>
  );
}

function BireyselKart({ baslik, deger, alt, icon: IconCmp, renk, bgRenk, vurgu }) {
  return (
    <div className={`rounded-[24px] border border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md p-4 shadow-[0_4px_20px_rgba(0,0,0,0.02)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] flex flex-col justify-between ${vurgu ? 'ring-1 ring-amber-400/20 dark:ring-amber-500/20' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`flex items-center justify-center w-9 h-9 rounded-xl ${bgRenk} ${renk}`}>
          <IconCmp className="w-5 h-5" strokeWidth={2.5} />
        </div>
      </div>
      <div>
        <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-1">
          {baslik}
        </p>
        <p className="text-2xl font-black tracking-tight text-slate-900 dark:text-white leading-none">
          {deger}
        </p>
        {alt && (
          <p className="mt-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            {alt}
          </p>
        )}
      </div>
    </div>
  );
}
