/**
 * TerminalUretimKabulPage — Üretimden palet kabul + raf yerleştirme (Terminal 2-tarama akışı)
 * Scanner-first sleek industrial UI — el terminali birincil, kamera/manuel sigorta.
 *
 * Akış: Palet Barkod Okut → Kabul Et → Raf Barkod Okut → Yerleştir → Sonuç
 */
import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Factory, CheckCircle, XCircle, ArrowRight, Wifi,
  RefreshCw, ScanLine, CornerDownRight, Package, Inbox, AlertTriangle, MapPin,
  Camera, Keyboard, ChevronDown, ChevronUp,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { hataMetni } from '../../utils/hata';
import useTerminalScanInput from '../../hooks/useTerminalScanInput';
import { sanitizeBarkod } from '../../utils/barcode';
import { uretimPaletiKabulEt, uretimPaletiYerlestir, getRaflar, getUretimPaleti } from '../../services/api';
import ZXingBarcodeScanner from '../../components/common/ZXingBarcodeScanner';

// ── Sabitler ──────────────────────────────────────────────────────────────────
const ADIM = { PALET: 1, RAF: 2, SONUC: 3 };
const ZATEN_YERLESTIRME = ['YerlestirmeBekliyor'];
const ZATEN_BITMIS = ['Yerlestirildi'];

const idempotencyConfig = (idempotencyKey) => (
  idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : {}
);

const stepVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: 'easeIn' } }
};

const collapseVariants = {
  initial: { opacity: 0, height: 0 },
  animate: { opacity: 1, height: 'auto', transition: { duration: 0.22, ease: 'easeOut' } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.18, ease: 'easeIn' } },
};

export default function TerminalUretimKabulPage() {
  const navigate = useNavigate();

  const [adim, setAdim] = useState(ADIM.PALET);
  const [barkodInput, setBarkodInput] = useState('');
  const [yukleniyor, setYukleniyor] = useState(false);
  const [sonuc, setSonuc] = useState(null);
  const [kabulBilgi, setKabulBilgi] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [gecmis, setGecmis] = useState([]);
  const [rafListesi, setRafListesi] = useState([]);
  const [manuelAcik, setManuelAcik] = useState(false);
  const [gecmisAcik, setGecmisAcik] = useState(false);

  const inputRef = useRef(null);

  useEffect(() => {
    getRaflar().then((r) => setRafListesi(r.data || [])).catch(() => {});
  }, []);

  // ── Faz 1: Palet Okut ──────────────────────────────────────────────────────
  const paletOkut = useCallback(async (barkod, meta = {}) => {
    const no = sanitizeBarkod(barkod ?? barkodInput, 'palet');
    if (!no) return false;

    setYukleniyor(true);
    setSonuc(null);

    try {
      let palet = null;
      try {
        const durumRes = await getUretimPaleti(no);
        palet = durumRes.data;
      } catch { /* palet bulunamadı — kabul-et dene */ }

      if (palet && ZATEN_BITMIS.includes(palet.durum)) {
        setSonuc({ basarili: true, mesaj: 'Bu palet zaten yerleştirilmiş.', palet });
        setAdim(ADIM.SONUC);
        return true;
      }

      if (palet && ZATEN_YERLESTIRME.includes(palet.durum)) {
        setKabulBilgi(palet);
        setManuelAcik(false);
        setAdim(ADIM.RAF);
        toast.success(`${no} zaten kabul edilmiş — raf barkodunu okutun`);
        return true;
      }

      const res = await uretimPaletiKabulEt(no, idempotencyConfig(meta.idempotencyKey));
      palet = res.data;
      setKabulBilgi(palet);
      setManuelAcik(false);
      setAdim(ADIM.RAF);
      toast.success(`${no} kabul edildi — raf barkodunu okutun`);
      return true;
    } catch (err) {
      const mesaj = hataMetni(err, 'Kabul işlemi başarısız');
      setSonuc({ basarili: false, mesaj });
      setGecmis((prev) => [
        { basarili: false, mesaj, no, rafKod: null, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      return false;
    } finally {
      setYukleniyor(false);
      setBarkodInput('');
    }
  }, [barkodInput]);

  // ── Faz 2: Raf Okut + Yerleştir ────────────────────────────────────────────
  const rafOkut = useCallback(async (barkod, meta = {}) => {
    const kod = sanitizeBarkod(barkod ?? barkodInput, 'raf');
    if (!kod || !kabulBilgi) return false;

    const raf = rafListesi.find(
      (r) => [r.kod, r.raf_kodu, r.barkod, String(r.id)]
        .filter(Boolean)
        .some((aday) => String(aday).toUpperCase() === kod)
    );
    if (!raf) {
      toast.error(`"${kod}" ile eşleşen raf bulunamadı`);
      setBarkodInput('');
      setTimeout(() => inputRef.current?.focus(), 50);
      return false;
    }

    setYukleniyor(true);
    try {
      await uretimPaletiYerlestir(kabulBilgi.palet_no, {
        palet_no: kabulBilgi.palet_no,
        raf_id: raf.id,
      }, idempotencyConfig(meta.idempotencyKey));
      const rafKod = raf.kod || raf.raf_kodu || kod;
      const yeniSonuc = {
        basarili: true,
        mesaj: `Palet ${rafKod} rafına yerleştirildi.`,
        palet: kabulBilgi,
        rafKod,
      };
      setSonuc(yeniSonuc);
      setGecmis((prev) => [
        { ...yeniSonuc, no: kabulBilgi.palet_no, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      toast.success(`${kabulBilgi.palet_no} → ${rafKod} yerleştirildi`);
      return true;
    } catch (err) {
      const mesaj = hataMetni(err, 'Yerleştirme başarısız');
      setSonuc({ basarili: false, mesaj, palet: kabulBilgi });
      setGecmis((prev) => [
        { basarili: false, mesaj, no: kabulBilgi.palet_no, rafKod: kod, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      toast.error(mesaj);
      return false;
    } finally {
      setYukleniyor(false);
      setBarkodInput('');
    }
  }, [barkodInput, kabulBilgi, rafListesi]);

  /**
   * Manuel mod toggle — Android Chrome user-gesture kuralı için senkron yapılır.
   *   Açılış: DOM attribute'unu doğrudan "text"e set + el.focus() (gesture chain bozulmaz)
   *           → soft klavye gelir. Sonra React state güncellenir.
   *   Kapanış: blur + DOM attribute "none" → klavye iner. Hook'un sessiz re-focus
   *           akışları artık klavye davet etmez.
   */
  const toggleManuel = useCallback(() => {
    const el = inputRef.current;
    setManuelAcik((onceki) => {
      const yeni = !onceki;
      if (!el) return yeni;
      if (yeni) {
        // Açılış — gesture içinde senkron focus + inputmode değişimi
        el.setAttribute('inputmode', 'text');
        el.focus();
      } else {
        el.blur();
        el.setAttribute('inputmode', 'none');
      }
      return yeni;
    });
  }, []);

  // ── Sıfırla ─────────────────────────────────────────────────────────────────
  const sifirla = () => {
    setSonuc(null);
    setKabulBilgi(null);
    setBarkodInput('');
    setManuelAcik(false);
    setAdim(ADIM.PALET);
  };

  // DataWedge Keyboard Wedge: odaklı input + ENTER tek tarama hattı
  const scanMode = adim === ADIM.RAF ? 'raf' : 'palet';
  const scanDisabled = yukleniyor || kameraAcik;
  const scanInput = useTerminalScanInput({
    mode: scanMode,
    value: barkodInput,
    setValue: setBarkodInput,
    inputRef,
    contextKey: scanMode === 'palet'
      ? 'terminal-uretim:palet'
      : `terminal-uretim:${kabulBilgi?.palet_no || 'yok'}:raf`,
    disabled: scanDisabled,
    isEnabled: (adim === ADIM.PALET || adim === ADIM.RAF) && !scanDisabled,
    onSubmit: async (code, meta) => (scanMode === 'palet'
      ? paletOkut(code, meta)
      : rafOkut(code, meta)),
    flushOnIdleMs: 250,
  });
  const zebraDetected = scanInput.zebraDetected;
  const kameraIslem = (code) => {
    setKameraAcik(false);
    void scanInput.submitScan(code, { force: true });
  };

  // İstatistik özetleri
  const bugunOzeti = useMemo(() => {
    const basarili = gecmis.filter((g) => g.basarili).length;
    const hatali = gecmis.length - basarili;
    return { basarili, hatali, toplam: gecmis.length };
  }, [gecmis]);

  // Adım meta
  const isRaf = adim === ADIM.RAF;
  const tema = isRaf
    ? { dot: 'bg-emerald-500', glow: 'bg-emerald-500/10 dark:bg-emerald-500/5', accent: 'emerald' }
    : { dot: 'bg-amber-500', glow: 'bg-amber-500/10 dark:bg-amber-500/5', accent: 'amber' };

  const headerInfo = isRaf
    ? { baslik: 'Raf Yerleştirme', alt: 'Adım 2/2 — Raf barkodunu okutun', icon: MapPin }
    : { baslik: 'Üretimden Kabul', alt: 'Adım 1/2 — Palet barkodunu okutun', icon: Factory };
  const HeaderIcon = headerInfo.icon;

  return (
    <div className="w-full h-full relative overflow-hidden pb-8">
      {/* Ambient glow */}
      <div className={`absolute -top-10 right-0 w-72 h-72 rounded-full blur-[90px] pointer-events-none transition-colors duration-500 ${tema.glow}`} />

      {/* ─── Sticky Header ──────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 backdrop-blur-xl bg-white/70 dark:bg-[#0b0c0e]/70 border-b border-slate-200/50 dark:border-white/[0.04]">
        <div className="px-4 pt-5 pb-4 max-w-md mx-auto">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 min-w-0 flex-1">
              <div className={`p-2.5 rounded-2xl border transition-colors duration-300 shrink-0 ${isRaf ? 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20' : 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20'}`}>
                <HeaderIcon className={`w-5 h-5 ${isRaf ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`} />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-[17px] font-bold text-slate-900 dark:text-white tracking-tight leading-tight">{headerInfo.baslik}</h1>
                {/* Adım 2'de palet bilgisi subtitle'a entegre */}
                {isRaf && kabulBilgi ? (
                  <div className="mt-1 flex items-center gap-1.5 min-w-0">
                    <Package className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <span className="font-mono text-[12px] font-bold text-emerald-700 dark:text-emerald-300 truncate">{kabulBilgi.palet_no}</span>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 shrink-0">• {kabulBilgi.koli_adedi} koli ✓</span>
                  </div>
                ) : (
                  <p className="text-[12px] text-slate-500 dark:text-slate-400 font-medium mt-0.5">{headerInfo.alt}</p>
                )}
              </div>
            </div>

            {/* Adım göstergesi (sağda) */}
            {(adim === ADIM.PALET || adim === ADIM.RAF) && (
              <div className="flex items-center gap-1 pt-1 shrink-0">
                <div className={`h-1.5 rounded-full transition-all duration-500 ${adim >= ADIM.PALET ? `${tema.dot} w-5` : 'bg-slate-200 dark:bg-slate-800 w-2'}`} />
                <div className={`h-1.5 rounded-full transition-all duration-500 ${adim >= ADIM.RAF ? 'bg-emerald-500 w-5' : 'bg-slate-200 dark:bg-slate-800 w-2'}`} />
              </div>
            )}
          </div>
        </div>
      </header>

      <AnimatePresence mode="wait">
        {/* ─── Adım 1 & 2: Tarama ────────────────────────────────────────── */}
        {(adim === ADIM.PALET || adim === ADIM.RAF) && (
          <Motion.div
            key={`scan-${adim}`}
            variants={stepVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="px-4 pt-5 space-y-4 max-w-md mx-auto relative z-10"
          >
            {/* ━━ Birincil: Tarayıcı Hazır kartı ━━ */}
            <ScannerHazirKarti
              accent={tema.accent}
              isRaf={isRaf}
              busy={yukleniyor}
              zebraDetected={zebraDetected}
            />

            {/* ━━ İkincil: Manuel giriş ━━
                Trigger her zaman görünür; input HER ZAMAN DOM'da mount —
                kapalıyken sr-only (scanner keystroke'larını yine de yakalar),
                açıldığında görünür panel olur. */}
            <SecondaryAction
              icon={Keyboard}
              label={manuelAcik ? 'Manuel girişi kapat' : 'Manuel girmek için dokunun'}
              hint={!manuelAcik ? 'Tarayıcı arka planda dinleniyor — klavye açılmaz' : undefined}
              acik={manuelAcik}
              onToggle={toggleManuel}
            />

            {/* Always-mounted scan input — collapse'dan bağımsız scanner alıcı kanalı */}
            <Motion.div
              initial={false}
              animate={manuelAcik
                ? { height: 'auto', opacity: 1, marginTop: 0 }
                : { height: 0, opacity: 0, marginTop: 0 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="overflow-hidden"
              aria-hidden={!manuelAcik}
            >
              <div className="flex gap-2 pt-2">
                <input
                  ref={scanInput.inputRef}
                  className={`flex-1 bg-white dark:bg-[#121316] border rounded-2xl px-4 py-3.5 text-slate-900 dark:text-white text-[15px] font-mono tracking-wide placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:ring-1 transition-all ${isRaf ? 'border-emerald-200/60 dark:border-emerald-800/60 focus:border-emerald-500/50 focus:ring-emerald-500/30' : 'border-amber-200/60 dark:border-amber-800/60 focus:border-amber-500/50 focus:ring-amber-500/30'}`}
                  placeholder={isRaf ? 'GNL-A-01-01-01' : 'PRD-YYYYMMDD-NNNN'}
                  value={barkodInput}
                  onChange={(e) => setBarkodInput(e.target.value)}
                  onKeyDown={scanInput.handleKeyDown}
                  onBlur={scanInput.handleBlur}
                  disabled={scanDisabled}
                  autoComplete="off"
                  autoCapitalize="characters"
                  spellCheck={false}
                  tabIndex={manuelAcik ? 0 : -1}
                  // inputMode="none": kapalıyken soft klavye açılmaz, fiziksel scanner keystroke'ları gelir.
                  // Manuel açıldığında "text" → klavye davet edilir.
                  inputMode={manuelAcik ? 'text' : 'none'}
                />
                <Motion.button
                  whileTap={{ scale: 0.92 }}
                  onClick={() => void scanInput.submitScan()}
                  disabled={scanDisabled || !barkodInput.trim()}
                  tabIndex={manuelAcik ? 0 : -1}
                  className={`disabled:opacity-40 text-white w-12 rounded-2xl flex items-center justify-center tap-highlight-transparent shadow-md ${isRaf ? 'bg-emerald-600 dark:bg-emerald-500 shadow-emerald-500/20' : 'bg-amber-600 dark:bg-amber-500 shadow-amber-500/20'}`}
                  aria-label="Gönder"
                >
                  {yukleniyor ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CornerDownRight className="w-4 h-4" strokeWidth={2.5} />}
                </Motion.button>
              </div>
            </Motion.div>

            {/* ━━ Üçüncül: Kamera (yalnız Zebra olmayan cihazlarda) ━━ */}
            {!zebraDetected && (
              <SecondaryAction
                icon={Camera}
                label="Kamera ile okut"
                onToggle={() => setKameraAcik(true)}
                hint="Tarayıcı çalışmıyorsa"
                isAction
              />
            )}

            {/* ━━ Bugün özeti (alt collapsible) ━━ */}
            {adim === ADIM.PALET && (
              <BugunOzeti
                ozet={bugunOzeti}
                acik={gecmisAcik}
                onToggle={() => setGecmisAcik((v) => !v)}
                gecmis={gecmis}
              />
            )}
          </Motion.div>
        )}

        {/* ─── Adım 3: Sonuç ─────────────────────────────────────────────── */}
        {adim === ADIM.SONUC && sonuc && (
          <Motion.div key="sonuc" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-6 relative z-10">
            <div className={`rounded-[28px] p-7 text-center border relative overflow-hidden shadow-xl backdrop-blur-md ${sonuc.basarili ? 'bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-500/20' : 'bg-rose-50/80 dark:bg-rose-950/30 border-rose-200 dark:border-rose-500/20'}`}>
              <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-40 h-40 blur-[50px] rounded-full pointer-events-none ${sonuc.basarili ? 'bg-emerald-400/20 dark:bg-emerald-500/20' : 'bg-rose-400/20 dark:bg-rose-500/20'}`} />
              <div className="relative z-10 flex flex-col items-center">
                <Motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                  className={`w-20 h-20 rounded-full flex items-center justify-center mb-4 border ${sonuc.basarili ? 'bg-emerald-100 dark:bg-emerald-500/10 border-emerald-300 dark:border-emerald-500/30' : 'bg-rose-100 dark:bg-rose-500/10 border-rose-300 dark:border-rose-500/30'}`}
                >
                  {sonuc.basarili
                    ? <CheckCircle className="w-10 h-10 text-emerald-600 dark:text-emerald-400" strokeWidth={2} />
                    : <XCircle className="w-10 h-10 text-rose-600 dark:text-rose-400" strokeWidth={2} />}
                </Motion.div>
                <h2 className={`text-xl font-black tracking-tight ${sonuc.basarili ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}`}>
                  {sonuc.basarili ? 'Yerleştirildi' : 'İşlem Hatası'}
                </h2>
                <p className="text-[13px] text-slate-600 dark:text-slate-400 mt-1.5 font-medium leading-relaxed max-w-[280px]">{sonuc.mesaj}</p>
              </div>
            </div>

            {sonuc.basarili && sonuc.palet && (
              <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-2xl p-5 border border-slate-200/60 dark:border-slate-800/60 space-y-3 shadow-sm">
                <InfoRow label="Palet" value={sonuc.palet.palet_no} mono />
                <InfoRow label="Lot No" value={sonuc.palet.lot_no || sonuc.palet.lot_id} mono highlight />
                <InfoRow label="Miktar" value={`${sonuc.palet.koli_adedi} Koli`} strong />
                {sonuc.rafKod && <InfoRow label="Raf" value={sonuc.rafKod} mono highlight />}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <button onClick={() => navigate('/terminal/ozet')} className="flex-1 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-[14px] rounded-2xl py-3.5 transition-colors tap-highlight-transparent">
                Özete Dön
              </button>
              <Motion.button whileTap={{ scale: 0.98 }} onClick={sifirla} className="flex-[2] bg-amber-600 dark:bg-amber-500 text-white font-black rounded-2xl py-3.5 flex items-center justify-center gap-2 tap-highlight-transparent shadow-md shadow-amber-500/20">
                <span className="mt-0.5">YENİ OKUTMA</span> <ArrowRight className="w-5 h-5" strokeWidth={2.5} />
              </Motion.button>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>

      <ZXingBarcodeScanner isOpen={kameraAcik} onClose={() => setKameraAcik(false)} onScanSuccess={kameraIslem} />
    </div>
  );
}

// ─── Bileşenler ──────────────────────────────────────────────────────────────

/**
 * Birincil tarama yüzeyi: el terminalini "hazır" göstergesi.
 * Yumuşak nabız + içeride tarama hattı animasyonu — operatör ekrana bakmadan da
 * cihazın aktif olduğunu hisseder (ses + titreşim de feedback hattında zaten var).
 */
function ScannerHazirKarti({ accent, isRaf, busy, zebraDetected }) {
  const accentMap = {
    amber: {
      ring: 'ring-amber-500/20',
      text: 'text-amber-700 dark:text-amber-300',
      sub: 'text-amber-600/80 dark:text-amber-400/70',
      iconBg: 'bg-amber-100 dark:bg-amber-500/15',
      iconColor: 'text-amber-600 dark:text-amber-400',
      line: 'via-amber-400 dark:via-amber-500',
      pulse: 'shadow-[0_0_0_0_rgba(245,158,11,0.4)]',
      dot: 'bg-amber-500',
    },
    emerald: {
      ring: 'ring-emerald-500/20',
      text: 'text-emerald-700 dark:text-emerald-300',
      sub: 'text-emerald-600/80 dark:text-emerald-400/70',
      iconBg: 'bg-emerald-100 dark:bg-emerald-500/15',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
      line: 'via-emerald-400 dark:via-emerald-500',
      pulse: 'shadow-[0_0_0_0_rgba(16,185,129,0.4)]',
      dot: 'bg-emerald-500',
    },
  };
  const a = accentMap[accent] || accentMap.amber;

  return (
    <div className={`relative bg-white/70 dark:bg-[#121316]/70 backdrop-blur-xl border border-slate-200/60 dark:border-white/[0.05] rounded-[28px] p-6 ring-1 ${a.ring} overflow-hidden shadow-sm`}>
      {/* Tarama hattı animasyonu */}
      <div className="absolute inset-x-0 top-0 h-px overflow-hidden pointer-events-none">
        <Motion.div
          initial={{ x: '-100%' }}
          animate={{ x: '100%' }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'linear' }}
          className={`h-full w-1/2 bg-gradient-to-r from-transparent ${a.line} to-transparent`}
        />
      </div>

      <div className="flex flex-col items-center text-center gap-3">
        {/* Nabızlı ikon */}
        <Motion.div
          animate={busy ? { scale: 1 } : { scale: [1, 1.05, 1] }}
          transition={busy ? {} : { duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className={`relative ${a.iconBg} w-16 h-16 rounded-2xl flex items-center justify-center border border-slate-200/50 dark:border-white/[0.05]`}
        >
          {busy
            ? <RefreshCw className={`w-7 h-7 ${a.iconColor} animate-spin`} strokeWidth={2} />
            : <ScanLine className={`w-8 h-8 ${a.iconColor}`} strokeWidth={1.75} />}
          {!busy && (
            <Motion.span
              animate={{ scale: [1, 1.6], opacity: [0.5, 0] }}
              transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
              className={`absolute inset-0 rounded-2xl ${a.pulse} ring-2 ring-current opacity-30`}
              style={{ color: 'transparent' }}
            />
          )}
        </Motion.div>

        <div className="space-y-1">
          <p className={`text-[15px] font-black tracking-tight ${a.text}`}>
            {busy ? 'İŞLENİYOR…' : isRaf ? 'RAF BARKODUNU OKUTUN' : 'PALET BARKODUNU OKUTUN'}
          </p>
          <p className={`text-[12px] font-medium ${a.sub}`}>
            {busy ? 'Lütfen bekleyin' : 'El terminali tetik tuşuna basın'}
          </p>
        </div>

        {/* Cihaz durumu (alt chip) */}
        <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100/80 dark:bg-white/[0.04] border border-slate-200/60 dark:border-white/[0.04]">
          <span className={`relative flex w-1.5 h-1.5`}>
            <span className={`absolute inline-flex w-full h-full rounded-full ${a.dot} opacity-50 animate-ping`} />
            <span className={`relative inline-flex w-1.5 h-1.5 rounded-full ${a.dot}`} />
          </span>
          <Wifi className="w-3 h-3 text-slate-400 dark:text-slate-500" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
            {zebraDetected ? 'Zebra Tarayıcı Aktif' : 'Tarayıcı Dinleniyor'}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Üçüncül/ikincil aksiyon — collapse'li veya direkt tetikleyici.
 * Görsel olarak bilinçli "minör" — birincil aksiyon dikkatini bölmesin.
 */
function SecondaryAction({ icon, label, hint, acik, onToggle, isAction = false, children }) {
  const IconComp = icon;
  return (
    <div>
      <Motion.button
        whileTap={{ scale: 0.99 }}
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 bg-white/60 dark:bg-[#121316]/60 backdrop-blur-md border border-slate-200/60 dark:border-white/[0.05] rounded-2xl px-4 py-3 hover:border-slate-300 dark:hover:border-white/[0.08] transition-colors tap-highlight-transparent group"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="bg-slate-100 dark:bg-white/[0.05] p-1.5 rounded-lg border border-slate-200/60 dark:border-white/[0.04]">
            <IconComp className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" strokeWidth={2} />
          </div>
          <div className="text-left min-w-0">
            <p className="text-[13px] font-semibold text-slate-700 dark:text-slate-300 truncate">{label}</p>
            {hint && <p className="text-[10px] font-medium text-slate-400 dark:text-slate-500 truncate">{hint}</p>}
          </div>
        </div>
        {!isAction && (
          acik
            ? <ChevronUp className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
            : <ChevronDown className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
        )}
        {isAction && <ArrowRight className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />}
      </Motion.button>

      <AnimatePresence initial={false}>
        {!isAction && acik && children && (
          <Motion.div
            variants={collapseVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="overflow-hidden"
          >
            {children}
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Bugün özeti — alta collapse'li, başlıkta sayım rozetleri.
 */
function BugunOzeti({ ozet, acik, onToggle, gecmis }) {
  return (
    <div className="pt-2">
      <Motion.button
        whileTap={{ scale: 0.99 }}
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 bg-white/60 dark:bg-[#121316]/60 backdrop-blur-md border border-slate-200/60 dark:border-white/[0.05] rounded-2xl px-4 py-3 hover:border-slate-300 dark:hover:border-white/[0.08] transition-colors tap-highlight-transparent"
      >
        <div className="flex items-center gap-2.5">
          <div className="bg-slate-100 dark:bg-white/[0.05] p-1.5 rounded-lg border border-slate-200/60 dark:border-white/[0.04]">
            <Inbox className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
          </div>
          <p className="text-[13px] font-semibold text-slate-700 dark:text-slate-300">Bugünkü işlemler</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200/60 dark:border-emerald-500/20 text-[11px] font-bold text-emerald-700 dark:text-emerald-300">
            <CheckCircle className="w-3 h-3" /> {ozet.basarili}
          </span>
          {ozet.hatali > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-50 dark:bg-rose-500/10 border border-rose-200/60 dark:border-rose-500/20 text-[11px] font-bold text-rose-700 dark:text-rose-300">
              <AlertTriangle className="w-3 h-3" /> {ozet.hatali}
            </span>
          )}
          {acik
            ? <ChevronUp className="w-4 h-4 text-slate-400 dark:text-slate-500" />
            : <ChevronDown className="w-4 h-4 text-slate-400 dark:text-slate-500" />}
        </div>
      </Motion.button>

      <AnimatePresence initial={false}>
        {acik && (
          <Motion.div
            variants={collapseVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="overflow-hidden"
          >
            <div className="pt-2 space-y-1.5">
              {gecmis.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 bg-white/40 dark:bg-[#121316]/40 backdrop-blur-sm rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
                  <Inbox className="w-5 h-5 text-slate-400 dark:text-slate-500 mb-1.5" />
                  <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400">Henüz işlem yapılmadı</p>
                </div>
              ) : (
                gecmis.map((g, i) => (
                  <Motion.div
                    key={i}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="bg-white/70 dark:bg-[#121316]/70 backdrop-blur-md border border-slate-200/60 dark:border-white/[0.04] rounded-xl px-3 py-2 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {g.basarili
                        ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                        : <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />}
                      <span className="font-mono text-[12px] font-bold text-slate-700 dark:text-slate-300 truncate">{g.no}</span>
                      {g.rafKod && <span className="text-[11px] text-emerald-600 dark:text-emerald-400 truncate">→ {g.rafKod}</span>}
                    </div>
                    <span className="text-[10px] font-mono font-medium text-slate-400 dark:text-slate-500 shrink-0">{g.zaman}</span>
                  </Motion.div>
                ))
              )}
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function InfoRow({ label, value, mono, strong, highlight }) {
  return (
    <div className={`flex items-center justify-between gap-4 py-1.5 flex-wrap ${highlight ? 'bg-amber-50 dark:bg-amber-500/10 px-3 py-2 -mx-3 rounded-xl border border-amber-200 dark:border-amber-500/20' : ''}`}>
      <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold shrink-0">{label}</span>
      <span className={`text-[14px] ${strong ? 'font-bold text-slate-900 dark:text-white' : highlight ? 'font-black text-amber-600 dark:text-amber-400' : 'font-medium text-slate-700 dark:text-slate-300'} truncate text-right ${mono ? 'font-mono tracking-wide' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function zamanStr() {
  return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}
