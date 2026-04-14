/**
 * YerlestirmePage — 4 adımlı scan-to-verify yerleştirme akışı.
 * Native PWA UI - Zümrüt & Çinko Paleti, Akıcı Adım Geçişleri
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
              <h1 className="text-xl font-bold text-zinc-100 tracking-tight">Yerleştirme</h1>
            </div>

            {bekleyenSayisi !== null && !gorev && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-gradient-to-br from-zinc-900 to-zinc-900/80 rounded-[24px] p-6 border border-white/[0.04] text-center relative overflow-hidden shadow-2xl mt-4">
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-[40px]" />
                <p className="text-5xl font-black text-emerald-400 drop-shadow-md tracking-tighter">{bekleyenSayisi}</p>
                <p className="text-[11px] font-bold text-zinc-500 mt-2 tracking-widest uppercase">Havuzda Bekleyen</p>
              </motion.div>
            )}

            {!gorev ? (
              <div className="relative mt-8">
                <div className="absolute -inset-[2px] bg-gradient-to-r from-emerald-600 via-emerald-400 to-emerald-600 rounded-3xl blur-[12px] opacity-25 animate-pulse" />
                <motion.button
                  whileTap={!loading ? { scale: 0.97 } : {}}
                  onClick={goreviAl}
                  disabled={loading}
                  className="relative w-full bg-gradient-to-br from-emerald-400 to-emerald-600 border border-emerald-300/30 hover:from-emerald-300 hover:to-emerald-500 active:scale-[0.98] disabled:opacity-50 text-zinc-950 font-black text-[16px] rounded-[24px] py-5 flex items-center justify-center gap-3 transition-all shadow-lg shadow-emerald-900/20 overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-[24px] pointer-events-none" />
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
                <div className="bg-zinc-900 border border-white/[0.04] rounded-[24px] overflow-hidden shadow-2xl">
                  <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-emerald-500 shadow-[2px_0_15px_rgba(16,185,129,0.3)]" />
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="bg-emerald-500/10 p-2 rounded-xl border border-emerald-500/20">
                          <Package className="w-4 h-4 text-emerald-400" />
                        </div>
                        <span className="text-[12px] uppercase tracking-widest text-zinc-400 font-black">Görev #{gorev.id}</span>
                      </div>
                      <OncelikBadge oncelik={gorev.oncelik} />
                    </div>

                    <div className="space-y-3 pt-2">
                      {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} strong />}
                      {gorev.palet_barkodu && <InfoRow label="Palet" value={gorev.palet_barkodu} mono />}
                      {gorev.lot_no && <InfoRow label="Lot No" value={gorev.lot_no} mono />}
                      {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}

                      <div className="w-full h-px bg-white/[0.04] my-4" />

                      {gorev.onerilen_raf_kodu
                        ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
                        : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
                      {gorev.zone_adi && (
                        <div className="flex items-center justify-between gap-4 py-1">
                          <span className="text-[11px] text-zinc-500 font-bold uppercase tracking-wider shrink-0">Zon</span>
                          <span className="flex items-center gap-1.5 text-sm font-bold text-zinc-200 bg-zinc-950 px-3 py-1.5 rounded-xl border border-white/[0.05]">
                            <MapPin className="w-3.5 h-3.5 text-zinc-400" />
                            {gorev.zone_adi}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 p-3 bg-zinc-950/50 border-t border-white/[0.02]">
                    <button
                      onClick={goreviBirakAction}
                      disabled={loading}
                      className="flex-1 bg-zinc-800 hover:bg-zinc-700 active:scale-95 text-zinc-300 font-bold text-[13px] rounded-2xl py-3.5 transition-colors tap-highlight-transparent"
                    >
                      Bırak
                    </button>
                    <motion.button
                      whileTap={!loading ? { scale: 0.95 } : {}}
                      onClick={goreviBaslatAction}
                      disabled={loading}
                      className="flex-[2] relative bg-emerald-500 text-zinc-950 font-black rounded-2xl py-3.5 flex items-center justify-center gap-2 transition-colors tap-highlight-transparent"
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

            <div className="bg-zinc-900 rounded-[24px] p-5 border border-white/[0.04] space-y-2 shadow-lg">
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
                  className="flex-1 bg-zinc-900 border border-white/[0.05] rounded-2xl px-5 py-4 text-zinc-100 text-[15px] font-mono tracking-wide placeholder-zinc-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
                  placeholder="PLT-2026-XXXXX"
                  value={manuelPalet}
                  onChange={(e) => setManuelPalet(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && paletDogrula(manuelPalet)}
                />
                <motion.button whileTap={{ scale: 0.9 }} onClick={() => paletDogrula(manuelPalet)} className="bg-emerald-500 text-zinc-950 w-14 rounded-2xl flex items-center justify-center tap-highlight-transparent">
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

            <div className="bg-zinc-900 rounded-[24px] p-5 border border-white/[0.04] space-y-2 shadow-lg">
              <InfoRow label="Palet" value={paletBarkod} mono strong />
              {gorev.onerilen_raf_kodu
                ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
                : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
              {gorev.zone_adi && <InfoRow label="Zon" value={gorev.zone_adi} />}
            </div>

            <div className="bg-sky-500/10 border border-sky-500/20 rounded-2xl px-4 py-3.5 flex items-start gap-3">
              <div className="bg-sky-500/20 p-1.5 rounded-lg shrink-0 border border-sky-500/30 mt-0.5">
                <ScanLine className="w-4 h-4 text-sky-400" />
              </div>
              <p className="text-[13px] text-sky-200/90 font-medium leading-snug">Hedef raf barkodunu okutun ya da farklı uygun bir raf seçin.</p>
            </div>

            <ScanButton onClick={() => { setKameraMod('raf'); setKameraAcik(true); }} text="RAF BARKODUNU OKUT" />

            <div className="space-y-3">
              <Divider text="Manuel Gir" />
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-zinc-900 border border-white/[0.05] rounded-2xl px-5 py-4 text-zinc-100 text-[15px] font-mono tracking-wide placeholder-zinc-600 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
                  placeholder="GNL-A-01-01-01"
                  value={manuelRaf}
                  onChange={(e) => setManuelRaf(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && yerlestir(manuelRaf)}
                />
                <motion.button whileTap={{ scale: 0.9 }} disabled={loading} onClick={() => yerlestir(manuelRaf)} className="bg-emerald-500 disabled:opacity-50 text-zinc-950 w-14 rounded-2xl flex items-center justify-center tap-highlight-transparent">
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
            <div className={`rounded-[32px] p-8 text-center border relative overflow-hidden shadow-2xl ${sonuc.basarili ? 'bg-emerald-950/30 border-emerald-500/20' : 'bg-rose-950/30 border-rose-500/20'}`}>
              <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-40 h-40 blur-[50px] rounded-full pointer-events-none ${sonuc.basarili ? 'bg-emerald-500/20' : 'bg-rose-500/20'}`} />
              
              <div className="relative z-10 flex flex-col items-center">
                {sonuc.basarili ? (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 15 }} className="bg-emerald-500/10 w-24 h-24 rounded-full flex items-center justify-center mb-5 border border-emerald-500/30">
                    <CheckCircle className="w-12 h-12 text-emerald-400" strokeWidth={2} />
                  </motion.div>
                ) : (
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 15 }} className="bg-rose-500/10 w-24 h-24 rounded-full flex items-center justify-center mb-5 border border-rose-500/30">
                    <XCircle className="w-12 h-12 text-rose-400" strokeWidth={2} />
                  </motion.div>
                )}
                <h2 className={`text-2xl font-black tracking-tight ${sonuc.basarili ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {sonuc.basarili ? 'İşlem Başarılı!' : 'Doğrulama Hatası'}
                </h2>
                <p className="text-[14px] text-zinc-400 mt-2 font-medium leading-relaxed max-w-[280px]">{sonuc.mesaj}</p>
              </div>
            </div>

            {sonuc.basarili && (
              <div className="bg-zinc-900 rounded-[24px] p-5 border border-white/[0.04] space-y-3">
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
                          className="w-full bg-zinc-900 border border-white/[0.04] rounded-2xl p-4 text-left hover:border-orange-500/30 transition-colors relative overflow-hidden group"
                        >
                          <div className="flex justify-between items-center">
                            <p className="font-mono text-[16px] font-bold text-zinc-100 group-hover:text-orange-400 transition-colors">{alt.raf_kod}</p>
                            <div className="bg-white/5 p-1.5 rounded-full"><ArrowRight className="w-4 h-4 text-zinc-400" /></div>
                          </div>
                          <div className="flex gap-3 text-[11px] font-medium text-zinc-500 mt-2">
                            <span>{alt.bos_slot} boş slot</span>
                            <div className="w-px bg-zinc-700" />
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
                    className="w-full bg-orange-500/10 border border-orange-500/30 text-orange-400 font-bold rounded-2xl py-4 flex items-center justify-center gap-2"
                  >
                    <ShieldAlert className="w-5 h-5" /> SÜPERVİZÖR OVERRIDE
                  </motion.button>
                )}
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <button onClick={() => navigate('/terminal/gorevler')} className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-bold text-[14px] rounded-2xl py-4 transition-colors tap-highlight-transparent">
                Listeye Dön
              </button>
              <motion.button whileTap={{ scale: 0.98 }} onClick={sifirla} className="flex-[2] bg-emerald-500 text-zinc-950 font-black rounded-2xl py-4 flex items-center justify-center gap-2 tap-highlight-transparent">
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
    <div className="flex items-center gap-3 bg-zinc-900 p-2 pr-4 rounded-[20px] border border-white/[0.04] shadow-sm">
      <button onClick={onGeri} className="p-2.5 rounded-[14px] text-zinc-400 bg-zinc-800/80 hover:text-zinc-100 hover:bg-zinc-700 transition-colors">
        <ChevronLeft className="w-5 h-5" />
      </button>
      <div className="flex-1">
        <p className="text-[10px] uppercase tracking-widest text-emerald-400/80 font-bold mb-0.5">Adım {adim}/{toplam}</p>
        <h1 className="text-[17px] font-bold text-zinc-100 tracking-tight leading-none">{baslik}</h1>
      </div>
      <div className="flex gap-1.5">
        {Array.from({ length: toplam }).map((_, i) => (
          <div key={i} className={`h-1.5 rounded-full transition-all duration-500 ${i < adim ? 'bg-emerald-400 w-5' : 'bg-zinc-800 w-2'}`} />
        ))}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono, strong, highlight }) {
  return (
    <div className={`flex items-center justify-between gap-4 py-1.5 flex-wrap ${highlight ? 'bg-emerald-500/10 px-3 py-2 -mx-3 rounded-xl border border-emerald-500/20' : ''}`}>
      <span className="text-[11px] uppercase tracking-wider text-zinc-500 font-bold shrink-0">{label}</span>
      <span className={`text-[14px] ${strong ? 'font-bold text-zinc-100' : highlight ? 'font-black text-emerald-400' : 'font-medium text-zinc-300'} truncate text-right ${mono ? 'font-mono tracking-wide' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function OncelikBadge({ oncelik }) {
  if (oncelik === 1) return <span className="text-[10px] uppercase tracking-wider font-black bg-rose-500/10 border border-rose-500/20 text-rose-400 px-2.5 py-1 rounded-lg flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> ACİL</span>;
  if (oncelik === 2) return <span className="text-[10px] uppercase tracking-wider font-bold bg-orange-500/10 border border-orange-500/20 text-orange-400 px-2.5 py-1 rounded-lg">Yüksek</span>;
  return null;
}

function ScanButton({ onClick, text }) {
  return (
    <motion.button whileTap={{ scale: 0.98 }} onClick={onClick} className="w-full bg-zinc-900 border border-white/[0.04] hover:border-emerald-500/50 rounded-[24px] py-10 flex flex-col items-center gap-3 transition-colors group">
      <div className="bg-zinc-800 p-4 rounded-full group-hover:bg-emerald-500/10 transition-colors">
        <ScanLine className="w-10 h-10 text-zinc-400 group-hover:text-emerald-400 transition-colors" strokeWidth={1.5} />
      </div>
      <span className="text-zinc-400 group-hover:text-emerald-400 font-black text-[13px] tracking-widest">{text}</span>
    </motion.button>
  );
}

function ProblemButton({ onClick }) {
  return (
    <div className="pt-2">
      <button onClick={onClick} className="w-full flex items-center justify-center gap-2 text-[13px] font-bold text-zinc-500 hover:text-rose-400 py-3 rounded-xl transition-colors tap-highlight-transparent">
        <AlertCircle className="w-4 h-4" /> SORUN BİLDİR
      </button>
    </div>
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

// Framer Motion Destekli Alt Sheet Modal
function SorunSheet({ open, onClose, sorunTip, setSorunTip, sorunNeden, setSorunNeden, onGonder, loading, sorunIslemYetkisiVar }) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ type: 'spring', damping: 25, stiffness: 300 }} className="w-full max-w-md bg-zinc-950 border-t border-white/[0.05] rounded-t-[32px] p-6 pb-[calc(24px+env(safe-area-inset-bottom))] relative z-10 space-y-5">
            <div className="w-12 h-1.5 bg-zinc-800 rounded-full mx-auto mb-4" />
            <h3 className="font-bold text-xl text-zinc-100 flex items-center gap-2"><AlertCircle className="w-6 h-6 text-rose-500" /> Sorun Bildir</h3>
            
            <div className="space-y-3">
              <button onClick={() => setSorunTip('karantina')} className={`w-full text-left p-4 rounded-2xl border transition-colors ${sorunTip === 'karantina' ? 'bg-rose-500/10 border-rose-500/30' : 'bg-zinc-900 border-white/[0.04]'}`}>
                <p className={`font-bold text-[15px] flex items-center gap-2 ${sorunTip === 'karantina' ? 'text-rose-400' : 'text-zinc-300'}`}><ShieldAlert className="w-4 h-4" /> Karantinaya Al</p>
                <p className="text-[12px] text-zinc-500 mt-1">Hasarlı veya uygunsuz ürün. Palet karantinaya çekilir.</p>
              </button>
              <button onClick={() => setSorunTip('iptal')} className={`w-full text-left p-4 rounded-2xl border transition-colors ${sorunTip === 'iptal' ? 'bg-orange-500/10 border-orange-500/30' : 'bg-zinc-900 border-white/[0.04]'}`}>
                <p className={`font-bold text-[15px] flex items-center gap-2 ${sorunTip === 'iptal' ? 'text-orange-400' : 'text-zinc-300'}`}><XCircle className="w-4 h-4" /> Görevi İptal Et</p>
                <p className="text-[12px] text-zinc-500 mt-1">Palet bulunamadı veya sistem hatası. Görev havuza döner.</p>
              </button>
            </div>

            {sorunTip && sorunIslemYetkisiVar && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-4">
                <textarea className="w-full bg-zinc-900 border border-white/[0.05] rounded-2xl p-4 text-[14px] text-zinc-100 outline-none focus:border-emerald-500/50 resize-none h-24" placeholder="Sorunu açıklayın..." value={sorunNeden} onChange={(e) => setSorunNeden(e.target.value)} />
                <button onClick={onGonder} disabled={loading || !sorunNeden.trim()} className="w-full bg-emerald-500 text-zinc-950 font-black rounded-2xl py-4 disabled:opacity-50 flex justify-center">
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
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="w-full max-w-sm bg-zinc-950 border border-white/[0.05] rounded-[32px] p-6 relative z-10 space-y-5 shadow-2xl">
            <h3 className="font-bold text-xl text-zinc-100 flex items-center gap-2"><ShieldAlert className="w-6 h-6 text-orange-500" /> Override</h3>
            {overrideRafSec && (
              <div className="bg-orange-500/10 border border-orange-500/20 rounded-2xl p-4">
                <div className="flex justify-between items-center"><span className="text-[11px] text-orange-400/80 font-bold uppercase tracking-widest">Seçilen Raf</span><span className="font-mono font-bold text-orange-400">{overrideRafSec.kod || overrideRafSec.raf_kod}</span></div>
              </div>
            )}
            <textarea className="w-full bg-zinc-900 border border-white/[0.05] rounded-2xl p-4 text-[14px] text-zinc-100 outline-none focus:border-orange-500/50 resize-none h-24" placeholder="Override gerekçesini yazın..." value={overrideNeden} onChange={(e) => setOverrideNeden(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={onClose} className="flex-1 bg-zinc-800 text-zinc-300 font-bold rounded-2xl py-3.5">İptal</button>
              <button onClick={overrideYap} disabled={loading || !overrideRafSec || !overrideNeden.trim()} className="flex-[2] bg-orange-500 text-white font-black rounded-2xl py-3.5 flex justify-center disabled:opacity-50">
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Onayla'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}