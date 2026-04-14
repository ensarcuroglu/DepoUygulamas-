/**
 * GorevListesiPage — Operatörün bekleyen yerleştirme görevleri listesi.
 * Zümrüt Yeşili & Çinko (Emerald & Zinc) High-Vis Dark Mode UI
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
  Bekliyor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  Atandi: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  DevamEdiyor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  Tamamlandi: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  IptalEdildi: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
};

const TIP_RENK = {
  Yerlestirme: 'text-emerald-400',
  Transfer: 'text-sky-400',
  BelirsizKonum: 'text-rose-400',
};

const ONCELIK_ETİKET = { 1: 'ACİL', 2: 'Yüksek', 3: 'Orta', 4: 'Normal', 5: 'Normal' };
const ONCELIK_RENK = {
  1: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  2: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  3: 'bg-amber-500/10 text-amber-400 border-transparent',
  4: 'bg-zinc-800 text-zinc-400 border-transparent',
  5: 'bg-zinc-800 text-zinc-400 border-transparent',
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
    // Alt barda boşluk bırakmak için pb-6 eklendi ve max-w-md ile mobil görünüm sabitlendi
    <div className="p-4 space-y-6 max-w-md mx-auto pb-6">
      
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-3">
          <div className="bg-emerald-500/10 p-2.5 rounded-2xl border border-emerald-500/20">
            <ClipboardList className="w-6 h-6 text-emerald-400" />
          </div>
          <h1 className="text-xl font-bold text-zinc-100 tracking-tight">Görevler</h1>
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={yukle}
          disabled={loading}
          className="p-3 rounded-2xl text-zinc-400 bg-zinc-900 hover:text-emerald-400 hover:bg-zinc-800 transition-colors disabled:opacity-50 border border-white/[0.02]"
          aria-label="Yenile"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
        </motion.button>
      </div>

      {/* Bekleyen Özet Kartı — Modern Dashboard Hissi */}
      {ozet && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-4 gap-3"
        >
          <div className="col-span-2 bg-gradient-to-br from-emerald-500/20 to-emerald-900/20 border border-emerald-500/20 rounded-3xl p-4 flex flex-col justify-center relative overflow-hidden">
            <div className="absolute -right-6 -top-6 w-24 h-24 bg-emerald-500/20 rounded-full blur-2xl pointer-events-none" />
            <p className="text-4xl font-black text-emerald-400 tracking-tighter">{ozet.toplam_bekleyen}</p>
            <p className="text-[11px] text-emerald-400/70 font-bold uppercase tracking-widest mt-1">Bekleyen</p>
          </div>
          <div className="col-span-2 grid grid-rows-2 gap-3">
            <div className="bg-zinc-900 border border-white/[0.03] rounded-2xl flex items-center justify-between px-4 py-2 shadow-inner">
              <div className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-[11px] text-zinc-400 font-bold uppercase tracking-wider">Acil</span>
              </div>
              <span className="text-lg font-black text-rose-400">{ozet.acil}</span>
            </div>
            <div className="bg-zinc-900 border border-white/[0.03] rounded-2xl flex items-center justify-between px-4 py-2 shadow-inner">
              <span className="text-[11px] text-zinc-400 font-bold uppercase tracking-wider pl-1">Normal</span>
              <span className="text-lg font-black text-zinc-300">{(ozet.normal ?? 0) + (ozet.yuksek_oncelikli ?? 0)}</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Sıradaki Görevi Al Butonu — Cta (Call to Action) */}
      <div className="relative">
        <div className="absolute -inset-[2px] bg-gradient-to-r from-emerald-600 via-emerald-400 to-emerald-600 rounded-3xl blur-[12px] opacity-25 animate-pulse" />
        <motion.button
          whileTap={!aliyor && !loading ? { scale: 0.97 } : {}}
          onClick={siradakiGoreviAl}
          disabled={aliyor || loading}
          className="relative w-full bg-gradient-to-br from-emerald-400 to-emerald-600 border border-emerald-300/30 hover:from-emerald-300 hover:to-emerald-500 disabled:opacity-60 text-zinc-950 font-black text-[16px] rounded-[24px] py-4.5 h-16 flex items-center justify-center gap-3 transition-all shadow-lg shadow-emerald-900/20 overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-[24px] pointer-events-none" />
          {aliyor ? (
            <RefreshCw className="w-6 h-6 animate-spin text-zinc-900" />
          ) : (
            <>
              <span className="tracking-wide relative z-10 drop-shadow-sm mt-0.5">SIRADAKİ GÖREVİ AL</span>
              <ArrowRight className="w-6 h-6 relative z-10 drop-shadow-sm" strokeWidth={2.5} />
            </>
          )}
        </motion.button>
      </div>

      {/* Filtre Tabs — Segmented Control Style w/ Framer Motion */}
      <div className="flex gap-2 p-1.5 bg-zinc-900/80 border border-zinc-800 rounded-[20px] overflow-x-auto custom-scrollbar relative z-10">
        {[
          { key: '', label: 'Tümü' },
          { key: 'Bekliyor', label: 'Bekleyen' },
          { key: 'Atandi', label: 'Atanan' },
          { key: 'DevamEdiyor', label: 'Devam' }
        ].map((d) => (
          <button
            key={d.key}
            onClick={() => setFiltre(d.key)}
            className={`relative shrink-0 flex-1 px-4 py-2.5 rounded-2xl text-[13px] font-bold transition-colors whitespace-nowrap tap-highlight-transparent ${
              filtre === d.key ? 'text-zinc-950' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {filtre === d.key && (
              <motion.div
                layoutId="filterTab"
                className="absolute inset-0 bg-zinc-100 rounded-[14px]"
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
          // Skeleton Loader (Çinko uyumlu)
          [1, 2, 3].map((i) => (
            <div key={i} className="bg-zinc-900/50 rounded-3xl p-5 border border-white/[0.02] flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <div className="h-6 w-20 bg-zinc-800 rounded-lg animate-pulse" />
                <div className="h-6 w-16 bg-zinc-800 rounded-lg animate-pulse" />
              </div>
              <div className="h-5 w-48 bg-zinc-800 rounded-md animate-pulse mt-1" />
              <div className="flex gap-2 mt-2 pt-4 border-t border-white/[0.02]">
                <div className="h-8 w-24 bg-zinc-800 rounded-xl animate-pulse" />
                <div className="h-8 w-24 bg-zinc-800/50 rounded-xl animate-pulse" />
              </div>
            </div>
          ))
        ) : gorevler.length === 0 ? (
          // Boş Durum
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-16 bg-zinc-900/30 rounded-3xl border border-dashed border-zinc-800"
          >
            <div className="bg-zinc-900 p-4 rounded-full mb-4 shadow-inner">
              <Inbox className="w-10 h-10 text-zinc-600" />
            </div>
            <p className="font-bold text-[15px] text-zinc-300">Görev bulunamadı</p>
            <p className="text-[13px] text-zinc-500 mt-1">Bu filtreye uygun görev yok.</p>
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
                    className={`group w-full relative overflow-hidden rounded-3xl p-5 text-left transition-all duration-300 border ${
                      atanmis
                        ? 'bg-zinc-900 border-zinc-700 hover:border-emerald-500/50 shadow-lg shadow-black/20 cursor-pointer'
                        : 'bg-zinc-900/40 border-white/[0.02] cursor-not-allowed opacity-90'
                    }`}
                  >
                    {/* Atanmış Görevler için sol Highlight bar */}
                    {atanmis && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-emerald-500 shadow-[2px_0_12px_rgba(16,185,129,0.5)]" />}

                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-[10px] uppercase font-black tracking-wide px-2.5 py-1 rounded-lg border ${DURUM_RENK[g.durum] || 'bg-zinc-800 text-zinc-300 border-zinc-700'}`}>
                          {g.durum}
                        </span>
                        <span className={`flex items-center gap-1 text-[10px] uppercase font-black tracking-wide px-2.5 py-1 rounded-lg border ${ONCELIK_RENK[g.oncelik] || 'bg-zinc-800 text-zinc-400 border-transparent'}`}>
                          {g.oncelik <= 2 && <AlertCircle className="w-3.5 h-3.5" />}
                          {ONCELIK_ETİKET[g.oncelik] || g.oncelik}
                        </span>
                      </div>
                      {atanmis ? (
                        <div className="bg-emerald-500/10 p-2 rounded-full group-hover:bg-emerald-500/20 transition-colors">
                          <ArrowRight className="w-4 h-4 text-emerald-400" />
                        </div>
                      ) : (
                        <span className="text-[10px] font-bold text-zinc-500 bg-zinc-950 px-2.5 py-1 rounded-lg border border-white/[0.05]">
                          Bekliyor
                        </span>
                      )}
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-baseline gap-2">
                        <p className={`text-[16px] font-bold ${atanmis ? 'text-zinc-50' : 'text-zinc-300'}`}>
                          {g.urun_adi || `Görev #${g.id}`}
                        </p>
                        <span className="text-[11px] font-mono font-medium text-zinc-500 bg-zinc-950 px-1.5 py-0.5 rounded-md shrink-0">#{g.id}</span>
                      </div>
                      
                      <p className={`text-[11px] font-bold tracking-widest uppercase flex items-center gap-1.5 ${TIP_RENK[g.tip] || 'text-zinc-500'}`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {g.tip}
                      </p>
                    </div>

                    <div className="mt-4 pt-4 border-t border-white/[0.04] flex gap-2.5 text-xs font-medium text-zinc-400 flex-wrap">
                      <div className="flex items-center gap-1.5 bg-zinc-950/80 px-3 py-1.5 rounded-xl border border-white/[0.02]">
                        <Package className="w-3.5 h-3.5 text-zinc-500" />
                        <span className="font-mono text-zinc-300">{g.palet_barkodu || `P#${g.palet_id}`}</span>
                      </div>
                      {(g.onerilen_raf_kodu || g.onerilen_raf_id) && (
                        <div className="flex items-center gap-1.5 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20">
                          <ArrowRight className="w-3.5 h-3.5 text-emerald-500/60" />
                          <span className="font-mono text-emerald-400 font-bold">{g.onerilen_raf_kodu || `#${g.onerilen_raf_id}`}</span>
                        </div>
                      )}
                      {g.zone_adi && (
                        <div className="flex items-center gap-1.5 bg-zinc-950/80 px-3 py-1.5 rounded-xl border border-white/[0.02]">
                           <span className="text-zinc-300 font-semibold">{g.zone_adi}</span>
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