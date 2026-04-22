/**
 * YerlestirmePage — 4 adımlı scan-to-verify yerleştirme akışı.
 * Sleek Industrial & Glassmorphism UI (Light & Dark Mode)
 */
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Package, Camera, CheckCircle, XCircle, ArrowRight,
  RefreshCw, ChevronLeft, ScanLine, CornerDownRight, AlertTriangle,
  AlertCircle, MapPin, ShieldAlert,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../../contexts/AuthContext';
import ZXingBarcodeScanner from '../../components/common/ZXingBarcodeScanner';
import {
  siradakiGorevisiniAl,
  goreviBaslat,
  goreviBirak,
  goreviIptal,
  terminalYerlestir,
  getBekleyenGorevOzet,
  goreviOverride,
  karantinayaAl,
} from '../../services/api';

const ADIM = { GOREV: 1, PALET: 2, RAF: 3, SONUC: 4 };

// Ortak Animasyon Varyantı (Adımlar arası sağdan sola kayma)
const stepVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: 'easeIn' } }
};

export default function YerlestirmePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, run } = useAsync();
  const { user } = useAuth();
  const overrideYetkisiVar = user?.rol === 'admin' || user?.rol === 'lojistik';
  const sorunIslemYetkisiVar = user?.rol === 'admin' || user?.rol === 'lojistik';

  const [adim, setAdim] = useState(ADIM.GOREV);
  const [gorev, setGorev] = useState(location.state?.gorev || null);
  const [bekleyenSayisi, setBekleyenSayisi] = useState(null);
  const [paletBarkod, setPaletBarkod] = useState('');
  const [rafBarkod, setRafBarkod] = useState(''); // Kullanımı düzeltildi
  const [sonuc, setSonuc] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [kameraMod, setKameraMod] = useState('palet');
  const [manuelPalet, setManuelPalet] = useState('');
  const [manuelRaf, setManuelRaf] = useState('');
  const [overrideModal, setOverrideModal] = useState(false);
  const [overrideNeden, setOverrideNeden] = useState('');
  const [overrideRafSec, setOverrideRafSec] = useState(null);
  const [sorunSheet, setSorunSheet] = useState(false);
  const [sorunTip, setSorunTip] = useState(null);
  const [sorunNeden, setSorunNeden] = useState('');

  useEffect(() => {
    if (gorev) return undefined;
    let iptal = false;
    const bekleyenYukle = async () => {
      try {
        const res = await getBekleyenGorevOzet();
        if (!iptal) setBekleyenSayisi(res.data.toplam_bekleyen);
      } catch { /* sessiz */ }
    };
    void bekleyenYukle();
    return () => { iptal = true; };
  }, [gorev]);

  const bekleyenYukle = async () => {
    try {
      const res = await getBekleyenGorevOzet();
      setBekleyenSayisi(res.data.toplam_bekleyen);
    } catch { /* sessiz */ }
  };

  const goreviAl = async () => {
    try {
      await run(async () => {
        const res = await siradakiGorevisiniAl();
        if (res.data) setGorev(res.data);
        else toast('Havuzda bekleyen görev yok.', { icon: '📦' });
      });
    } catch {
      toast.error('Sıradaki görev alınamadı.');
    }
  };

  const goreviBaslatAction = async () => {
    if (gorev.durum === 'DevamEdiyor') {
      setAdim(ADIM.PALET);
      return;
    }
    try {
      await run(async () => {
        await goreviBaslat(gorev.id);
        setGorev((g) => ({ ...g, durum: 'DevamEdiyor' }));
        setAdim(ADIM.PALET);
      });
    } catch {
      toast.error('Görev başlatılamadı.');
    }
  };

  const goreviBirakAction = async () => {
    if (gorev?.durum === 'DevamEdiyor') {
      toast.error('Başlatılmış görev bırakılamaz. Süreci tamamlayın veya süpervizöre bildirin.');
      return;
    }
    try {
      await run(async () => {
        await goreviBirak(gorev.id);
        toast('Görev havuza iade edildi.');
        setGorev(null);
        setAdim(ADIM.GOREV);
        void bekleyenYukle();
      });
    } catch {
      toast.error('Görev bırakılamadı.');
    }
  };

  const paletDogrula = (barkod) => {
    const b = barkod.trim();
    if (!b) return;
    const beklenen = gorev?.palet_barkodu;
    if (beklenen && b !== beklenen) {
      toast.error(`Yanlış palet! Beklenen: ${beklenen}`);
      return;
    }
    setPaletBarkod(b);
    setAdim(ADIM.RAF);
    toast.success('Palet doğrulandı!');
  };

  const yerlestir = async (rafKod) => {
    const r = rafKod.trim();
    if (!r) return;
    setRafBarkod(r);
    try {
      await run(async () => {
        const res = await terminalYerlestir({
          gorev_id: gorev.id,
          palet_barkod: paletBarkod,
          raf_barkod: r,
        });
        setSonuc(res.data);
        setAdim(ADIM.SONUC);
      });
    } catch {
      toast.error('Yerleştirme doğrulaması başarısız.');
    }
  };

  const overrideYap = async () => {
    if (!overrideRafSec) return toast.error('Lütfen önce bir alternatif raf seçin.');
    if (!overrideNeden.trim()) return toast.error('Override gerekçesi zorunludur.');
    try {
      await run(async () => {
        const res = await goreviOverride(gorev.id, {
          gerceklesen_raf_id: overrideRafSec.raf_id,
          neden: overrideNeden,
        });
        setSonuc({ basarili: true, durum: 'TAMAMLANDI', mesaj: 'Override ile yerleştirildi.', ...res.data });
        setAdim(ADIM.SONUC);
        setOverrideModal(false);
        setOverrideNeden('');
      });
    } catch {
      toast.error('Override işlemi başarısız.');
    }
  };

  const sorunGonder = async () => {
    if (!sorunIslemYetkisiVar) return toast.error('Bu işlem için yetkiniz yok. Lütfen süpervizör veya admin çağırın.');
    if (!sorunNeden.trim()) return toast.error('Açıklama zorunludur.');
    try {
      await run(async () => {
        if (sorunTip === 'karantina') {
          await karantinayaAl({ palet_id: gorev.palet_id, neden: sorunNeden });
          toast.success('Palet karantina zonuna yönlendirildi. Transfer görevi oluşturuldu.');
        } else {
          await goreviIptal(gorev.id, { neden: sorunNeden });
          toast('Görev iptal edildi.');
        }
        setSorunSheet(false);
        setSorunNeden('');
        setSorunTip(null);
        sifirla();
      });
    } catch {
      toast.error('Sorun bildirimi işlenemedi.');
    }
  };

  const sifirla = () => {
    setGorev(null);
    setPaletBarkod('');
    setRafBarkod('');
    setSonuc(null);
    setManuelPalet('');
    setManuelRaf('');
    setOverrideModal(false);
    setOverrideNeden('');
    setOverrideRafSec(null);
    setAdim(ADIM.GOREV);
    void bekleyenYukle();
  };

  // --- Render Area ---
  return (
    <div className="w-full h-full relative overflow-hidden pb-6">
      <AnimatePresence mode="wait">
        {/* ─── Adım 1: Görev ─────────────────────────────────────────── */}
        {adim === ADIM.GOREV && (
          <motion.div key="adim1" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-2">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Yerleştirme</h1>
            </div>

            {bekleyenSayisi !== null && !gorev && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[28px] p-6 border border-slate-200/60 dark:border-slate-800/60 text-center relative overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] mt-4">
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/10 rounded-full blur-[40px]" />
                <p className="text-5xl font-black text-blue-600 dark:text-blue-400 drop-shadow-sm tracking-tighter">{bekleyenSayisi}</p>
                <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mt-2 tracking-widest uppercase">Havuzda Bekleyen</p>
              </motion.div>
            )}

            {!gorev ? (
              <div className="relative mt-8">
                <div className="absolute -inset-[2px] bg-gradient-to-r from-blue-600 via-blue-400 to-indigo-600 rounded-[28px] blur-[12px] opacity-25 animate-pulse" />
                <motion.button
                  whileTap={!loading ? { scale: 0.97 } : {}}
                  onClick={goreviAl}
                  disabled={loading}
                  className="relative w-full bg-gradient-to-br from-blue-500 to-blue-700 border border-blue-400/30 hover:from-blue-400 hover:to-blue-600 active:scale-[0.98] disabled:opacity-50 text-white font-black text-[16px] rounded-[28px] py-5 flex items-center justify-center gap-3 transition-all shadow-lg shadow-blue-600/20 overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-[28px] pointer-events-none" />
                  {loading ? <RefreshCw className="w-7 h-7 animate-spin drop-shadow-sm" /> : (
                    <>
                      <span className="tracking-wide relative z-10 drop-shadow-sm mt-0.5">SIRADAKİ GÖREVİ AL</span>
                      <ArrowRight className="w-7 h-7 relative z-10 drop-shadow-sm" strokeWidth={2.5} />
                    </>
                  )}
                </motion.button>
              </div>
            ) : (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="relative mt-2">
                <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 rounded-[24px] overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                  <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-blue-500 shadow-[2px_0_15px_rgba(59,130,246,0.3)]" />
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="bg-blue-50 dark:bg-blue-500/10 p-2 rounded-xl border border-blue-200 dark:border-blue-500/20">
                          <Package className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        </div>
                        <span className="text-[12px] uppercase tracking-widest text-slate-500 dark:text-slate-400 font-black">Görev #{gorev.id}</span>
                      </div>
                      <OncelikBadge oncelik={gorev.oncelik} />
                    </div>

                    <div className="space-y-3 pt-2">
                      {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} strong />}
                      {gorev.palet_barkodu && <InfoRow label="Palet" value={gorev.palet_barkodu} mono />}
                      {gorev.lot_no && <InfoRow label="Lot No" value={gorev.lot_no} mono />}
                      {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}

                      <div className="w-full h-px bg-slate-200 dark:bg-slate-800/50 my-4" />

                      {gorev.onerilen_raf_kodu
                        ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
                        : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
                      {gorev.zone_adi && (
                        <div className="flex items-center justify-between gap-4 py-1">
                          <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider shrink-0">Zon</span>
                          <span className="flex items-center gap-1.5 text-sm font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {gorev.zone_adi}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 p-3 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-200/60 dark:border-slate-800/60">
                    <button
                      onClick={goreviBirakAction}
                      disabled={loading}
                      className="flex-1 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 active:scale-95 text-slate-700 dark:text-slate-300 font-bold text-[13px] rounded-2xl py-3.5 transition-colors tap-highlight-transparent"
                    >
                      Bırak
                    </button>
                    <motion.button
                      whileTap={!loading ? { scale: 0.95 } : {}}
                      onClick={goreviBaslatAction}
                      disabled={loading}
                      className="flex-[2] relative bg-blue-600 dark:bg-blue-500 text-white font-black rounded-2xl py-3.5 flex items-center justify-center gap-2 transition-colors tap-highlight-transparent"
                    >
                      {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
                        <><span className="mt-0.5">{gorev.durum === 'DevamEdiyor' ? 'DEVAM ET' : 'BAŞLAT'}</span> <ArrowRight className="w-5 h-5" strokeWidth={2.5} /></>
                      )}
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* ─── Adım 2: Palet Scan ─────────────────────────────────────────── */}
        {adim === ADIM.PALET && (
          <motion.div key="adim2" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-2">
            <AdimHeader adim={2} toplam={3} baslik="Paleti Tara" onGeri={() => setAdim(ADIM.GOREV)} />

            <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] p-5 border border-slate-200/60 dark:border-slate-800/60 space-y-2 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
              {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} strong />}
              <InfoRow label="Beklenen Palet" value={gorev.palet_barkodu || `#${gorev.palet_id}`} mono highlight />
              {gorev.lot_no && <InfoRow label="Lot" value={gorev.lot_no} mono />}
              {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}
            </div>

            <ScanButton onClick={() => { setKameraMod('palet'); setKameraAcik(true); }} text="PALET BARKODUNU OKUT" />

            <div className="space-y-3">
              <Divider text="Manuel Gir" />
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-white dark:bg-[#121316] border border-slate-200/60 dark:border-slate-800/60 rounded-[20px] px-5 py-4 text-slate-900 dark:text-white text-[15px] font-mono tracking-wide placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
                  placeholder="PLT-2026-XXXXX"
                  value={manuelPalet}
                  onChange={(e) => setManuelPalet(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && paletDogrula(manuelPalet)}
                />
                <motion.button whileTap={{ scale: 0.9 }} onClick={() => paletDogrula(manuelPalet)} className="bg-blue-600 dark:bg-blue-500 text-white w-14 rounded-[20px] flex items-center justify-center tap-highlight-transparent shadow-lg shadow-blue-500/20">
                  <CornerDownRight className="w-5 h-5" strokeWidth={2.5} />
                </motion.button>
              </div>
            </div>

            <ProblemButton onClick={() => setSorunSheet(true)} />
          </motion.div>
        )}

        {/* ─── Adım 3: Raf Scan ─────────────────────────────────────────── */}
        {adim === ADIM.RAF && (
          <motion.div key="adim3" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-2">
            <AdimHeader adim={3} toplam={3} baslik="Rafa Yerleştir" onGeri={() => setAdim(ADIM.PALET)} />

            <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] p-5 border border-slate-200/60 dark:border-slate-800/60 space-y-2 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
              <InfoRow label="Palet" value={paletBarkod} mono strong />
              {gorev.onerilen_raf_kodu
                ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
                : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
              {gorev.zone_adi && <InfoRow label="Zon" value={gorev.zone_adi} />}
            </div>

            <div className="bg-sky-50 dark:bg-sky-500/10 border border-sky-200 dark:border-sky-500/20 rounded-2xl px-4 py-3.5 flex items-start gap-3">
              <div className="bg-sky-100 dark:bg-sky-500/20 p-1.5 rounded-lg shrink-0 border border-sky-300 dark:border-sky-500/30 mt-0.5">
                <ScanLine className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              </div>
              <p className="text-[13px] text-sky-800 dark:text-sky-200/90 font-medium leading-snug">Hedef raf barkodunu okutun ya da farklı uygun bir raf seçin.</p>
            </div>

            <ScanButton onClick={() => { setKameraMod('raf'); setKameraAcik(true); }} text="RAF BARKODUNU OKUT" />

            <div className="space-y-3">
              <Divider text="Manuel Gir" />
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-white dark:bg-[#121316] border border-slate-200/60 dark:border-slate-800/60 rounded-[20px] px-5 py-4 text-slate-900 dark:text-white text-[15px] font-mono tracking-wide placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
                  placeholder="GNL-A-01-01-01"
                  value={manuelRaf}
                  onChange={(e) => setManuelRaf(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && yerlestir(manuelRaf)}
                />
                <motion.button whileTap={{ scale: 0.9 }} disabled={loading} onClick={() => yerlestir(manuelRaf)} className="bg-blue-600 dark:bg-blue-500 disabled:opacity-50 text-white w-14 rounded-[20px] flex items-center justify-center tap-highlight-transparent shadow-lg shadow-blue-500/20">
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <CornerDownRight className="w-5 h-5" strokeWidth={2.5} />}
                </motion.button>
              </div>
            </div>

            <ProblemButton onClick={() => setSorunSheet(true)} />
          </motion.div>
        )}

        {/* ─── Adım 4: Sonuç ─────────────────────────────────────────── */}
        {adim === ADIM.SONUC && sonuc && (
          <motion.div key="adim4" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-6">
            <div className={`rounded-[32px] p-8 text-center border relative overflow-hidden shadow-2xl backdrop-blur-md ${sonuc.basarili ? 'bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-500/20' : 'bg-rose-50/80 dark:bg-rose-950/30 border-rose-200 dark:border-rose-500/20'}`}>
              <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-40 h-40 blur-[50px] rounded-full pointer-events-none ${sonuc.basarili ? 'bg-emerald-400/20 dark:bg-emerald-500/20' : 'bg-rose-400/20 dark:bg-rose-500/20'}`} />
              
              <div className="relative z-10 flex flex-col items-center">
                {sonuc.basarili ? (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 15 }} className="bg-emerald-100 dark:bg-emerald-500/10 w-24 h-24 rounded-full flex items-center justify-center mb-5 border border-emerald-300 dark:border-emerald-500/30">
                    <CheckCircle className="w-12 h-12 text-emerald-600 dark:text-emerald-400" strokeWidth={2} />
                  </motion.div>
                ) : (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 15 }} className="bg-rose-100 dark:bg-rose-500/10 w-24 h-24 rounded-full flex items-center justify-center mb-5 border border-rose-300 dark:border-rose-500/30">
                    <XCircle className="w-12 h-12 text-rose-600 dark:text-rose-400" strokeWidth={2} />
                  </motion.div>
                )}
                <h2 className={`text-2xl font-black tracking-tight ${sonuc.basarili ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}`}>
                  {sonuc.basarili ? 'İşlem Başarılı!' : 'Doğrulama Hatası'}
                </h2>
                <p className="text-[14px] text-slate-600 dark:text-slate-400 mt-2 font-medium leading-relaxed max-w-[280px]">{sonuc.mesaj}</p>
              </div>
            </div>

            {sonuc.basarili && (
              <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] p-5 border border-slate-200/60 dark:border-slate-800/60 space-y-3 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                {sonuc.palet_no && <InfoRow label="Palet" value={sonuc.palet_no} mono />}
                {sonuc.raf_kod && <InfoRow label="Yerleşti" value={sonuc.raf_kod} mono highlight />}
                {sonuc.zon && <InfoRow label="Zon" value={sonuc.zon} />}
              </div>
            )}

            {!sonuc.basarili && (
              <div className="space-y-4">
                {sonuc.alternatifler?.length > 0 && (
                  <div className="space-y-3">
                    <Divider text="Alternatif Raflar" />
                    <div className="space-y-2">
                      {sonuc.alternatifler.map((alt) => (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          key={alt.raf_id}
                          onClick={() => { setOverrideRafSec(alt); setRafBarkod(alt.raf_kod); setOverrideModal(true); }}
                          className="w-full bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 rounded-2xl p-4 text-left hover:border-orange-400/50 dark:hover:border-orange-500/30 transition-colors relative overflow-hidden group shadow-sm"
                        >
                          <div className="flex justify-between items-center">
                            <p className="font-mono text-[16px] font-bold text-slate-900 dark:text-white group-hover:text-orange-500 dark:group-hover:text-orange-400 transition-colors">{alt.raf_kod}</p>
                            <div className="bg-slate-100 dark:bg-white/5 p-1.5 rounded-full"><ArrowRight className="w-4 h-4 text-slate-400" /></div>
                          </div>
                          <div className="flex gap-3 text-[11px] font-medium text-slate-500 mt-2">
                            <span>{alt.bos_slot} boş slot</span>
                            <div className="w-px bg-slate-200 dark:bg-slate-700" />
                            <span>Skor: {alt.skor}</span>
                          </div>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                )}

                {sonuc.override_gerekli && overrideYetkisiVar && (
                  <motion.button
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setOverrideModal(true)}
                    className="w-full bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/30 text-orange-600 dark:text-orange-400 font-bold rounded-[20px] py-4 flex items-center justify-center gap-2"
                  >
                    <ShieldAlert className="w-5 h-5" /> SÜPERVİZÖR OVERRIDE
                  </motion.button>
                )}
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <button onClick={() => navigate('/terminal/gorevler')} className="flex-1 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-[14px] rounded-[20px] py-4 transition-colors tap-highlight-transparent">
                Listeye Dön
              </button>
              <motion.button whileTap={{ scale: 0.98 }} onClick={sifirla} className="flex-[2] bg-blue-600 dark:bg-blue-500 text-white font-black rounded-[20px] py-4 flex items-center justify-center gap-2 tap-highlight-transparent">
                <span className="mt-0.5">SONRAKİ GÖREV</span> <ArrowRight className="w-5 h-5" strokeWidth={2.5} />
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Global Modallar (Override & Kamera & Sorun) */}
      <ZXingBarcodeScanner isOpen={kameraAcik} onClose={() => setKameraAcik(false)} onScanSuccess={(code) => { setKameraAcik(false); adim === ADIM.PALET ? paletDogrula(code) : yerlestir(code); }} />

      <SorunSheet open={sorunSheet} onClose={() => { setSorunSheet(false); setSorunTip(null); setSorunNeden(''); }} sorunTip={sorunTip} setSorunTip={setSorunTip} sorunNeden={sorunNeden} setSorunNeden={setSorunNeden} onGonder={sorunGonder} loading={loading} sorunIslemYetkisiVar={sorunIslemYetkisiVar} />
      
      <OverrideModal open={overrideModal} onClose={() => setOverrideModal(false)} overrideRafSec={overrideRafSec} overrideNeden={overrideNeden} setOverrideNeden={setOverrideNeden} overrideYap={overrideYap} loading={loading} />
    </div>
  );
}

// ─── Yardımcı Bileşenler ───────────────────────────────────────────

function AdimHeader({ adim, toplam, baslik, onGeri }) {
  return (
    <div className="flex items-center gap-3 bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md p-2 pr-4 rounded-[20px] border border-slate-200/60 dark:border-slate-800/60 shadow-[0_2px_10px_rgba(0,0,0,0.02)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.2)]">
      <button onClick={onGeri} className="p-2.5 rounded-[14px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 hover:text-slate-700 dark:hover:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
        <ChevronLeft className="w-5 h-5" />
      </button>
      <div className="flex-1">
        <p className="text-[10px] uppercase tracking-widest text-blue-600/80 dark:text-blue-400/80 font-bold mb-0.5">Adım {adim}/{toplam}</p>
        <h1 className="text-[17px] font-bold text-slate-900 dark:text-white tracking-tight leading-none">{baslik}</h1>
      </div>
      <div className="flex gap-1.5">
        {Array.from({ length: toplam }).map((_, i) => (
          <div key={i} className={`h-1.5 rounded-full transition-all duration-500 ${i < adim ? 'bg-blue-500 dark:bg-blue-400 w-5' : 'bg-slate-200 dark:bg-slate-800 w-2'}`} />
        ))}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono, strong, highlight }) {
  return (
    <div className={`flex items-center justify-between gap-4 py-1.5 flex-wrap ${highlight ? 'bg-blue-50 dark:bg-blue-500/10 px-3 py-2 -mx-3 rounded-xl border border-blue-200 dark:border-blue-500/20' : ''}`}>
      <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold shrink-0">{label}</span>
      <span className={`text-[14px] ${strong ? 'font-bold text-slate-900 dark:text-white' : highlight ? 'font-black text-blue-600 dark:text-blue-400' : 'font-medium text-slate-700 dark:text-slate-300'} truncate text-right ${mono ? 'font-mono tracking-wide' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function OncelikBadge({ oncelik }) {
  if (oncelik === 1) return <span className="text-[10px] uppercase tracking-wider font-black bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-600 dark:text-rose-400 px-2.5 py-1 rounded-lg flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> ACİL</span>;
  if (oncelik === 2) return <span className="text-[10px] uppercase tracking-wider font-bold bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/20 text-orange-600 dark:text-orange-400 px-2.5 py-1 rounded-lg">Yüksek</span>;
  return null;
}

function ScanButton({ onClick, text }) {
  return (
    <motion.button whileTap={{ scale: 0.98 }} onClick={onClick} className="w-full bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 hover:border-blue-400/50 dark:hover:border-blue-500/50 rounded-[28px] py-10 flex flex-col items-center gap-3 transition-colors group shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
      <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-[20px] group-hover:bg-blue-50 dark:group-hover:bg-blue-500/10 transition-colors">
        <ScanLine className="w-10 h-10 text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" strokeWidth={1.5} />
      </div>
      <span className="text-slate-500 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 font-black text-[13px] tracking-widest">{text}</span>
    </motion.button>
  );
}

function ProblemButton({ onClick }) {
  return (
    <div className="pt-2">
      <button onClick={onClick} className="w-full flex items-center justify-center gap-2 text-[13px] font-bold text-slate-500 hover:text-rose-500 dark:hover:text-rose-400 py-3 rounded-xl transition-colors tap-highlight-transparent">
        <AlertCircle className="w-4 h-4" /> SORUN BİLDİR
      </button>
    </div>
  );
}

function Divider({ text }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-px bg-slate-200 dark:bg-slate-800 flex-1" />
      <p className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-widest">{text}</p>
      <div className="h-px bg-slate-200 dark:bg-slate-800 flex-1" />
    </div>
  );
}

// Framer Motion Destekli Alt Sheet Modal
function SorunSheet({ open, onClose, sorunTip, setSorunTip, sorunNeden, setSorunNeden, onGonder, loading, sorunIslemYetkisiVar }) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="absolute inset-0 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm" />
          <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ type: 'spring', damping: 25, stiffness: 300 }} className="w-full max-w-md bg-white dark:bg-zinc-950 border-t border-slate-200 dark:border-white/[0.05] rounded-t-[32px] p-6 pb-[calc(24px+env(safe-area-inset-bottom))] relative z-10 space-y-5 shadow-2xl">
            <div className="w-12 h-1.5 bg-slate-200 dark:bg-zinc-800 rounded-full mx-auto mb-4" />
            <h3 className="font-bold text-xl text-slate-900 dark:text-zinc-100 flex items-center gap-2"><AlertCircle className="w-6 h-6 text-rose-500" /> Sorun Bildir</h3>
            
            <div className="space-y-3">
              <button onClick={() => setSorunTip('karantina')} className={`w-full text-left p-4 rounded-2xl border transition-colors ${sorunTip === 'karantina' ? 'bg-rose-50 dark:bg-rose-500/10 border-rose-200 dark:border-rose-500/30' : 'bg-slate-50 dark:bg-zinc-900 border-slate-200 dark:border-white/[0.04]'}`}>
                <p className={`font-bold text-[15px] flex items-center gap-2 ${sorunTip === 'karantina' ? 'text-rose-600 dark:text-rose-400' : 'text-slate-700 dark:text-zinc-300'}`}><ShieldAlert className="w-4 h-4" /> Karantinaya Al</p>
                <p className="text-[12px] text-slate-500 dark:text-zinc-500 mt-1">Hasarlı veya uygunsuz ürün. Palet karantinaya çekilir.</p>
              </button>
              <button onClick={() => setSorunTip('iptal')} className={`w-full text-left p-4 rounded-2xl border transition-colors ${sorunTip === 'iptal' ? 'bg-orange-50 dark:bg-orange-500/10 border-orange-200 dark:border-orange-500/30' : 'bg-slate-50 dark:bg-zinc-900 border-slate-200 dark:border-white/[0.04]'}`}>
                <p className={`font-bold text-[15px] flex items-center gap-2 ${sorunTip === 'iptal' ? 'text-orange-600 dark:text-orange-400' : 'text-slate-700 dark:text-zinc-300'}`}><XCircle className="w-4 h-4" /> Görevi İptal Et</p>
                <p className="text-[12px] text-slate-500 dark:text-zinc-500 mt-1">Palet bulunamadı veya sistem hatası. Görev havuza döner.</p>
              </button>
            </div>

            {sorunTip && sorunIslemYetkisiVar && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-4">
                <textarea className="w-full bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-white/[0.05] rounded-2xl p-4 text-[14px] text-slate-900 dark:text-zinc-100 outline-none focus:border-blue-500/50 resize-none h-24" placeholder="Sorunu açıklayın..." value={sorunNeden} onChange={(e) => setSorunNeden(e.target.value)} />
                <button onClick={onGonder} disabled={loading || !sorunNeden.trim()} className="w-full bg-blue-600 dark:bg-blue-500 text-white font-black rounded-[20px] py-4 disabled:opacity-50 flex justify-center shadow-lg shadow-blue-500/20">
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'İşlemi Onayla'}
                </button>
              </motion.div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function OverrideModal({ open, onClose, overrideRafSec, overrideNeden, setOverrideNeden, overrideYap, loading }) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="absolute inset-0 bg-slate-900/60 dark:bg-black/70 backdrop-blur-sm" />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="w-full max-w-sm bg-white dark:bg-zinc-950 border border-slate-200 dark:border-white/[0.05] rounded-[32px] p-6 relative z-10 space-y-5 shadow-2xl">
            <h3 className="font-bold text-xl text-slate-900 dark:text-zinc-100 flex items-center gap-2"><ShieldAlert className="w-6 h-6 text-orange-500" /> Override</h3>
            {overrideRafSec && (
              <div className="bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/20 rounded-2xl p-4">
                <div className="flex justify-between items-center"><span className="text-[11px] text-orange-600/80 dark:text-orange-400/80 font-bold uppercase tracking-widest">Seçilen Raf</span><span className="font-mono font-bold text-orange-600 dark:text-orange-400">{overrideRafSec.kod || overrideRafSec.raf_kod}</span></div>
              </div>
            )}
            <textarea className="w-full bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-white/[0.05] rounded-2xl p-4 text-[14px] text-slate-900 dark:text-zinc-100 outline-none focus:border-orange-400/50 dark:focus:border-orange-500/50 resize-none h-24" placeholder="Override gerekçesini yazın..." value={overrideNeden} onChange={(e) => setOverrideNeden(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={onClose} className="flex-1 bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 dark:hover:bg-zinc-700 text-slate-700 dark:text-zinc-300 font-bold rounded-[20px] py-3.5 transition-colors">İptal</button>
              <button onClick={overrideYap} disabled={loading || !overrideRafSec || !overrideNeden.trim()} className="flex-[2] bg-orange-500 text-white font-black rounded-[20px] py-3.5 flex justify-center disabled:opacity-50 shadow-lg shadow-orange-500/20">
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Onayla'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}