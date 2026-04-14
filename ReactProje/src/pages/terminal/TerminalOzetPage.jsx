/**
 * TerminalOzetPage — Operatörün günlük istatistik özeti.
 * Native PWA UI - Zümrüt & Çinko Paleti, Akıcı Liste Animasyonları
 */
import { useState, useCallback, useEffect } from 'react';
import { BarChart2, RefreshCw, CheckCircle, Clock, AlertCircle, Inbox, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { useAsync } from '../../hooks/useAsync';
import { hataMetni } from '../../utils/hata';
import { terminalOzet, getYerlestirmeGorevleri } from '../../services/api';

// Animasyon Varyantları
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
};

export default function TerminalOzetPage() {
  const { loading, run } = useAsync(true);
  const [ozet, setOzet] = useState(null);
  const [sonTamamlananlar, setSonTamamlananlar] = useState([]);

  const yukle = useCallback(async () => {
    try {
      const [ozetRes, tamamlananRes] = await run(() =>
        Promise.all([
          terminalOzet(),
          getYerlestirmeGorevleri({ durum: 'Tamamlandi', limit: 10 }),
        ])
      );
      setOzet(ozetRes.data);
      setSonTamamlananlar(tamamlananRes.data);
    } catch (err) {
      toast.error(hataMetni(err, 'Özet yüklenemedi'));
    }
  }, [run]);

  useEffect(() => {
    const baslangicYuklemesi = async () => {
      await yukle();
    };
    baslangicYuklemesi();
  }, [yukle]);

  const bugun = new Date().toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="p-4 space-y-6 max-w-md mx-auto pb-6 relative">
      
      {/* Arka Plan Ambient Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-[80px] pointer-events-none" />

      {/* Başlık */}
      <div className="flex items-center justify-between pt-2 relative z-10">
        <div className="flex items-center gap-3">
          <div className="bg-emerald-500/10 p-2.5 rounded-2xl border border-emerald-500/20">
            <BarChart2 className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-zinc-100 tracking-tight leading-tight">Günlük Özet</h1>
            <p className="text-[12px] text-zinc-500 font-medium capitalize">{bugun}</p>
          </div>
        </div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => yukle()}
          disabled={loading}
          className="p-3 rounded-2xl text-zinc-400 bg-zinc-900 hover:text-emerald-400 hover:bg-zinc-800 transition-colors disabled:opacity-50 border border-white/[0.02] tap-highlight-transparent"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
        </motion.button>
      </div>

      {/* İstatistik Kartları */}
      {loading && !ozet ? (
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-zinc-900 border border-white/[0.02] rounded-[24px] p-5 animate-pulse h-[110px]" />
          ))}
        </div>
      ) : ozet && (
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-3 gap-3 relative z-10"
        >
          <StatKart
            ikon={<CheckCircle className="w-5 h-5" />}
            deger={ozet.bugun_tamamlanan}
            etiket="Biten"
            tema="emerald"
          />
          <StatKart
            ikon={<Clock className="w-5 h-5" />}
            deger={ozet.benim_atanan_gorev}
            etiket="Üzerimde"
            tema="sky"
          />
          <StatKart
            ikon={<AlertCircle className="w-5 h-5" />}
            deger={ozet.bekleyen_gorev}
            etiket="Havuzda"
            tema="amber"
          />
        </motion.div>
      )}

      {/* Son Tamamlananlar Listesi */}
      <div className="space-y-4 pt-2 relative z-10">
        <Divider text="Son Tamamlananlar" />
        
        {loading && sonTamamlananlar.length === 0 ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-zinc-900 border border-white/[0.02] rounded-[20px] h-[76px] animate-pulse" />
            ))}
          </div>
        ) : sonTamamlananlar.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-12 bg-zinc-900/50 rounded-[24px] border border-dashed border-zinc-800"
          >
            <div className="bg-zinc-900 p-4 rounded-full mb-3 shadow-inner">
              <Inbox className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-[14px] font-bold text-zinc-400">Henüz tamamlanan görev yok</p>
          </motion.div>
        ) : (
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            <AnimatePresence>
              {sonTamamlananlar.map((g) => (
                <motion.div 
                  variants={itemVariants}
                  key={g.id} 
                  className="bg-zinc-900 border border-white/[0.04] rounded-[20px] p-4 flex items-center justify-between group hover:border-emerald-500/30 transition-colors shadow-sm"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="bg-zinc-950 p-2.5 rounded-xl border border-white/[0.02] group-hover:border-emerald-500/20 transition-colors">
                      <Package className="w-5 h-5 text-zinc-500 group-hover:text-emerald-400 transition-colors" />
                    </div>
                    <div>
                      <div className="flex items-baseline gap-2">
                        <p className="text-[15px] font-bold text-zinc-100">Görev <span className="font-mono text-zinc-400">#{g.id}</span></p>
                      </div>
                      <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mt-0.5">
                        {g.tip} <span className="mx-1">•</span> PLT {g.palet_id}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right flex flex-col items-end">
                    <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg border border-emerald-500/20">
                      Tamamlandı
                    </span>
                    {g.tamamlanma_tarihi && (
                      <p className="text-[11px] font-mono font-medium text-zinc-500 mt-1.5">
                        {new Date(g.tamamlanma_tarihi).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}

// ─── Yardımcı Bileşenler ───────────────────────────────────────────

function StatKart({ ikon, deger, etiket, tema }) {
  const temaAyarlari = {
    emerald: {
      bg: 'from-emerald-500/10 to-emerald-900/5',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400',
      icon: 'text-emerald-400',
      glow: 'bg-emerald-500/20'
    },
    sky: {
      bg: 'from-sky-500/10 to-sky-900/5',
      border: 'border-sky-500/20',
      text: 'text-sky-400',
      icon: 'text-sky-400',
      glow: 'bg-sky-500/20'
    },
    amber: {
      bg: 'from-amber-500/10 to-amber-900/5',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      icon: 'text-amber-400',
      glow: 'bg-amber-500/20'
    },
  };

  const aktifTema = temaAyarlari[tema] || temaAyarlari.emerald;

  return (
    <motion.div 
      variants={itemVariants}
      className={`relative overflow-hidden rounded-[24px] p-4 text-center border bg-gradient-to-br backdrop-blur-md shadow-lg shadow-black/10 ${aktifTema.bg} ${aktifTema.border}`}
    >
      {/* Kart İçi Ambient Glow */}
      <div className={`absolute -top-6 -right-6 w-16 h-16 rounded-full blur-[20px] ${aktifTema.glow}`} />
      
      <div className="relative z-10">
        <div className={`flex justify-center mb-2 ${aktifTema.icon}`}>
          {ikon}
        </div>
        <p className={`text-3xl font-black tracking-tighter ${aktifTema.text}`}>
          {deger ?? '—'}
        </p>
        <p className="text-[11px] font-bold text-zinc-500 uppercase tracking-widest mt-1">
          {etiket}
        </p>
      </div>
    </motion.div>
  );
}

function Divider({ text }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-px bg-zinc-800 flex-1" />
      <p className="text-[10px] uppercase font-bold text-zinc-600 tracking-widest">{text}</p>
      <div className="h-px bg-zinc-800 flex-1" />
    </div>
  );
}