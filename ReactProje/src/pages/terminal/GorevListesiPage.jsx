/**
 * GorevListesiPage — Operatörün bekleyen yerleştirme görevleri listesi.
 * Sleek Industrial & Glassmorphism UI (Light & Dark Mode)
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, RefreshCw, ArrowRight, AlertCircle, Inbox, Package, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { useAsync } from '../../hooks/useAsync';
import { hataMetni } from '../../utils/hata';
import { getYerlestirmeGorevleri, siradakiGorevisiniAl, getBekleyenGorevOzet } from '../../services/api';

// --- Modernize Edilmiş Renk Paletleri ---
const DURUM_RENK = {
  Bekliyor: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20',
  Atandi: 'bg-sky-50 dark:bg-sky-500/10 text-sky-700 dark:text-sky-400 border-sky-200 dark:border-sky-500/20',
  DevamEdiyor: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20',
  Tamamlandi: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20',
  IptalEdildi: 'bg-slate-100 dark:bg-slate-500/10 text-slate-700 dark:text-slate-400 border-slate-200 dark:border-slate-500/20',
};

const TIP_RENK = {
  Yerlestirme: 'text-blue-600 dark:text-blue-400',
  Transfer: 'text-sky-600 dark:text-sky-400',
  BelirsizKonum: 'text-rose-600 dark:text-rose-400',
};

const ONCELIK_ETİKET = { 1: 'ACİL', 2: 'Yüksek', 3: 'Orta', 4: 'Normal', 5: 'Normal' };
const ONCELIK_RENK = {
  1: 'bg-rose-50 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-500/30',
  2: 'bg-orange-50 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-500/30',
  3: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-transparent',
  4: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-transparent',
  5: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-transparent',
};

export default function GorevListesiPage() {
  const navigate = useNavigate();
  const { loading, run } = useAsync(true);
  const [aliyor, setAliyor] = useState(false);
  const [gorevler, setGorevler] = useState([]);
  const [ozet, setOzet] = useState(null);
  const [filtre, setFiltre] = useState('Bekliyor');

  const yukle = useCallback(async () => {
    try {
      const [gorevRes, ozetRes] = await run(() =>
        Promise.all([
          getYerlestirmeGorevleri({ durum: filtre || undefined, limit: 100 }),
          getBekleyenGorevOzet(),
        ])
      );
      setGorevler(gorevRes.data);
      setOzet(ozetRes.data);
    } catch (err) {
      toast.error(hataMetni(err, 'Görevler yüklenemedi'));
    }
  }, [run, filtre]);

  useEffect(() => { void yukle(); }, [yukle]);

  const siradakiGoreviAl = async () => {
    setAliyor(true);
    try {
      const res = await siradakiGorevisiniAl();
      if (res.data) {
        toast.success('Görev alındı!');
        navigate('/terminal/yerlestirme', { state: { gorev: res.data } });
      } else {
        toast('Havuzda bekleyen görev yok.', { icon: '📭' });
      }
    } catch (err) {
      toast.error(hataMetni(err, 'Görev alınamadı'));
    } finally {
      setAliyor(false);
    }
  };

  return (
    <div className="p-4 space-y-6 max-w-md mx-auto pb-6">
      
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-3">
          <div className="bg-blue-50 dark:bg-blue-500/10 p-2.5 rounded-2xl border border-blue-200 dark:border-blue-500/20">
            <ClipboardList className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Görevler</h1>
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={yukle}
          disabled={loading}
          className="p-3 rounded-2xl text-slate-500 dark:text-slate-400 bg-white/80 dark:bg-[#121316]/80 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-[#1A1C20] transition-colors disabled:opacity-50 border border-slate-200/60 dark:border-slate-800/60 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]"
          aria-label="Yenile"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-blue-600 dark:text-blue-400' : ''}`} />
        </motion.button>
      </div>

      {/* Bekleyen Özet Kartı — Modern Dashboard Hissi */}
      {ozet && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-4 gap-3"
        >
          <div className="col-span-2 bg-gradient-to-br from-blue-50 dark:from-blue-500/20 to-indigo-50 dark:to-indigo-900/20 border border-blue-200/60 dark:border-blue-500/20 rounded-[28px] p-4 flex flex-col justify-center relative overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-none">
            <div className="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/20 rounded-full blur-2xl pointer-events-none" />
            <p className="text-4xl font-black text-blue-700 dark:text-blue-400 tracking-tighter">{ozet.toplam_bekleyen}</p>
            <p className="text-[11px] text-blue-600/70 dark:text-blue-400/70 font-bold uppercase tracking-widest mt-1">Bekleyen</p>
          </div>
          <div className="col-span-2 grid grid-rows-2 gap-3">
            <div className="bg-white/80 dark:bg-[#121316]/80 border border-slate-200/60 dark:border-slate-800/60 rounded-[20px] flex items-center justify-between px-4 py-2 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] backdrop-blur-md">
              <div className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />
                <span className="text-[11px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Acil</span>
              </div>
              <span className="text-lg font-black text-rose-600 dark:text-rose-400">{ozet.acil}</span>
            </div>
            <div className="bg-white/80 dark:bg-[#121316]/80 border border-slate-200/60 dark:border-slate-800/60 rounded-[20px] flex items-center justify-between px-4 py-2 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] backdrop-blur-md">
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider pl-1">Normal</span>
              <span className="text-lg font-black text-slate-700 dark:text-slate-300">{(ozet.normal ?? 0) + (ozet.yuksek_oncelikli ?? 0)}</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Sıradaki Görevi Al Butonu — Cta (Call to Action) */}
      <div className="relative">
        <div className="absolute -inset-[2px] bg-gradient-to-r from-blue-600 via-blue-400 to-indigo-600 rounded-[28px] blur-[12px] opacity-25 animate-pulse" />
        <motion.button
          whileTap={!aliyor && !loading ? { scale: 0.97 } : {}}
          onClick={siradakiGoreviAl}
          disabled={aliyor || loading}
          className="relative w-full bg-gradient-to-br from-blue-500 to-blue-700 border border-blue-400/30 hover:from-blue-400 hover:to-blue-600 disabled:opacity-60 text-white font-black text-[16px] rounded-[28px] py-4.5 h-16 flex items-center justify-center gap-3 transition-all shadow-lg shadow-blue-600/20 overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-[28px] pointer-events-none" />
          {aliyor ? (
            <RefreshCw className="w-6 h-6 animate-spin text-white" />
          ) : (
            <>
              <span className="tracking-wide relative z-10 drop-shadow-sm mt-0.5">SIRADAKİ GÖREVİ AL</span>
              <ArrowRight className="w-6 h-6 relative z-10 drop-shadow-sm" strokeWidth={2.5} />
            </>
          )}
        </motion.button>
      </div>

      {/* Filtre Tabs — Segmented Control Style w/ Framer Motion */}
      <div className="flex gap-2 p-1.5 bg-white/80 dark:bg-[#121316]/80 border border-slate-200/60 dark:border-slate-800/60 rounded-[24px] overflow-x-auto custom-scrollbar relative z-10 backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
        {[
          { key: '', label: 'Tümü' },
          { key: 'Bekliyor', label: 'Bekleyen' },
          { key: 'Atandi', label: 'Atanan' },
          { key: 'DevamEdiyor', label: 'Devam' }
        ].map((d) => (
          <button
            key={d.key}
            onClick={() => setFiltre(d.key)}
            className={`relative shrink-0 flex-1 px-4 py-2.5 rounded-[18px] text-[13px] font-bold transition-colors whitespace-nowrap tap-highlight-transparent ${
              filtre === d.key ? 'text-blue-700 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {filtre === d.key && (
              <motion.div
                layoutId="filterTab"
                className="absolute inset-0 bg-blue-50 dark:bg-blue-500/10 rounded-[18px] border border-blue-100 dark:border-blue-500/20"
                transition={{ type: "spring", stiffness: 500, damping: 35 }}
              />
            )}
            <span className="relative z-10">{d.label}</span>
          </button>
        ))}
      </div>

      {/* Görev Listesi */}
      <div className="space-y-3 relative z-0">
        {loading ? (
          // Skeleton Loader (Sleek Industrial)
          [1, 2, 3].map((i) => (
            <div key={i} className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[28px] p-5 border border-slate-200/60 dark:border-slate-800/60 flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <div className="h-6 w-20 bg-slate-200 dark:bg-slate-800 rounded-lg animate-pulse" />
                <div className="h-6 w-16 bg-slate-200 dark:bg-slate-800 rounded-lg animate-pulse" />
              </div>
              <div className="h-5 w-48 bg-slate-200 dark:bg-slate-800 rounded-md animate-pulse mt-1" />
              <div className="flex gap-2 mt-2 pt-4 border-t border-slate-100 dark:border-slate-800/50">
                <div className="h-8 w-24 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse" />
                <div className="h-8 w-24 bg-slate-200/50 dark:bg-slate-800/50 rounded-xl animate-pulse" />
              </div>
            </div>
          ))
        ) : gorevler.length === 0 ? (
          // Boş Durum
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-16 bg-white/50 dark:bg-[#121316]/50 backdrop-blur-sm rounded-[32px] border border-dashed border-slate-300 dark:border-slate-700"
          >
            <div className="bg-slate-100 dark:bg-[#1A1C20] p-4 rounded-full mb-4 shadow-inner border border-slate-200 dark:border-slate-800">
              <Inbox className="w-10 h-10 text-slate-400 dark:text-slate-500" />
            </div>
            <p className="font-bold text-[15px] text-slate-700 dark:text-slate-300">Görev bulunamadı</p>
            <p className="text-[13px] text-slate-500 dark:text-slate-400 mt-1">Bu filtreye uygun görev yok.</p>
          </motion.div>
        ) : (
          // Animasyonlu Liste
          <AnimatePresence mode="popLayout">
            {gorevler.map((g) => {
              const atanmis = g.durum === 'Atandi' || g.durum === 'DevamEdiyor';
              return (
                <motion.div
                  layout
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
                  key={g.id}
                  className="w-full"
                >
                  <motion.button
                    whileTap={atanmis ? { scale: 0.98 } : {}}
                    onClick={atanmis ? () => navigate('/terminal/yerlestirme', { state: { gorev: g } }) : undefined}
                    disabled={!atanmis}
                    className={`group w-full relative overflow-hidden rounded-[28px] p-5 text-left transition-all duration-300 border backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] ${
                      atanmis
                        ? 'bg-white dark:bg-[#1A1C20] border-slate-200 dark:border-slate-700 hover:border-blue-500/50 dark:hover:border-blue-500/50 cursor-pointer'
                        : 'bg-white/60 dark:bg-[#121316]/60 border-slate-200/50 dark:border-slate-800/50 cursor-not-allowed opacity-90'
                    }`}
                  >
                    {/* Atanmış Görevler için sol Highlight bar */}
                    {atanmis && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-blue-500 shadow-[2px_0_12px_rgba(59,130,246,0.5)]" />}

                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-[10px] uppercase font-black tracking-wide px-2.5 py-1 rounded-lg border ${DURUM_RENK[g.durum] || 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700'}`}>
                          {g.durum}
                        </span>
                        <span className={`flex items-center gap-1 text-[10px] uppercase font-black tracking-wide px-2.5 py-1 rounded-lg border ${ONCELIK_RENK[g.oncelik] || 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-transparent'}`}>
                          {g.oncelik <= 2 && <AlertCircle className="w-3.5 h-3.5" />}
                          {ONCELIK_ETİKET[g.oncelik] || g.oncelik}
                        </span>
                      </div>
                      {atanmis ? (
                        <div className="bg-blue-50 dark:bg-blue-500/10 p-2 rounded-full group-hover:bg-blue-100 dark:group-hover:bg-blue-500/20 transition-colors">
                          <ArrowRight className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </div>
                      ) : (
                        <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-[#0A0B0D] px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800/50">
                          Bekliyor
                        </span>
                      )}
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-baseline gap-2">
                        <p className={`text-[16px] font-bold ${atanmis ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`}>
                          {g.urun_adi || `Görev #${g.id}`}
                        </p>
                        <span className="text-[11px] font-mono font-medium text-slate-500 dark:text-slate-500 bg-slate-100 dark:bg-[#0A0B0D] px-1.5 py-0.5 rounded-md shrink-0">#{g.id}</span>
                      </div>
                      
                      <p className={`text-[11px] font-bold tracking-widest uppercase flex items-center gap-1.5 ${TIP_RENK[g.tip] || 'text-slate-500 dark:text-slate-500'}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {g.tip}
                      </p>
                    </div>

                    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/50 flex gap-2.5 text-xs font-medium text-slate-500 dark:text-slate-400 flex-wrap">
                      <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-[#0A0B0D]/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800/50">
                        <Package className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                        <span className="font-mono text-slate-700 dark:text-slate-300">{g.palet_barkodu || `P#${g.palet_id}`}</span>
                      </div>
                      {(g.onerilen_raf_kodu || g.onerilen_raf_id) && (
                        <div className="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-500/10 px-3 py-1.5 rounded-xl border border-blue-200 dark:border-blue-500/20">
                          <ArrowRight className="w-3.5 h-3.5 text-blue-500/60 dark:text-blue-500/60" />
                          <span className="font-mono text-blue-700 dark:text-blue-400 font-bold">{g.onerilen_raf_kodu || `#${g.onerilen_raf_id}`}</span>
                        </div>
                      )}
                      {g.zone_adi && (
                        <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-[#0A0B0D]/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800/50">
                           <span className="text-slate-700 dark:text-slate-300 font-semibold">{g.zone_adi}</span>
                        </div>
                      )}
                    </div>
                  </motion.button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}