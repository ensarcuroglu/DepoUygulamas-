/**
 * TerminalUretimKabulPage — Üretimden palet kabul + raf yerleştirme (Terminal 2-tarama akışı)
 * SAHA ODAKLI ENDÜSTRİYEL UI: Yüksek kontrast, büyük dokunma hedefleri, animasyon gürültüsü yok.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Factory, CheckCircle, XCircle, ArrowRight, Wifi,
  ScanLine, Package, AlertTriangle, MapPin,
  Camera, Keyboard, ChevronDown, AlertOctagon, 
  ArrowLeft, RefreshCcw
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
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } }
};

const hapticFeedback = (type) => {
  if (!navigator.vibrate) return;
  if (type === 'success') navigator.vibrate([100, 50, 100]);
  if (type === 'error') navigator.vibrate([300, 150, 300]);
};

export default function TerminalUretimKabulPage() {
  const navigate = useNavigate();

  const [adim, setAdim] = useState(ADIM.PALET);
  const [barkodInput, setBarkodInput] = useState('');
  const [yukleniyor, setYukleniyor] = useState(false);
  const [raflarYukleniyor, setRaflarYukleniyor] = useState(true); // YENİ: Raf yüklenme durumu
  const [sonuc, setSonuc] = useState(null);
  const [kabulBilgi, setKabulBilgi] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [gecmis, setGecmis] = useState([]);
  const [rafListesi, setRafListesi] = useState([]);
  const [manuelAcik, setManuelAcik] = useState(false);

  const inputRef = useRef(null);

  useEffect(() => {
    setRaflarYukleniyor(true);
    getRaflar()
      .then((r) => setRafListesi(r.data || []))
      .catch((err) => {
        toast.error('Raf listesi alınamadı!', { style: { background: '#ef4444', color: '#fff' } });
      })
      .finally(() => setRaflarYukleniyor(false));
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
        hapticFeedback('error');
        setSonuc({ basarili: false, mesaj: 'Bu palet ZATEN YERLEŞTİRİLMİŞ.', palet });
        setAdim(ADIM.SONUC);
        return true;
      }

      if (palet && ZATEN_YERLESTIRME.includes(palet.durum)) {
        hapticFeedback('success');
        setKabulBilgi(palet);
        setManuelAcik(false);
        setAdim(ADIM.RAF);
        return true;
      }

      const res = await uretimPaletiKabulEt(no, idempotencyConfig(meta.idempotencyKey));
      palet = res.data;
      hapticFeedback('success');
      setKabulBilgi(palet);
      setManuelAcik(false);
      setAdim(ADIM.RAF);
      return true;
    } catch (err) {
      hapticFeedback('error');
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
      hapticFeedback('error');
      toast.error(`"${kod}" ile eşleşen raf bulunamadı`, { style: { background: '#ef4444', color: '#fff', fontWeight: 'bold' }});
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
      
      hapticFeedback('success');
      const rafKod = raf.kod || raf.raf_kodu || kod;
      const yeniSonuc = {
        basarili: true,
        mesaj: `Palet başarıyla rafa alındı.`,
        palet: kabulBilgi,
        rafKod,
      };
      setSonuc(yeniSonuc);
      setGecmis((prev) => [
        { ...yeniSonuc, no: kabulBilgi.palet_no, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      return true;
    } catch (err) {
      hapticFeedback('error');
      const mesaj = hataMetni(err, 'Yerleştirme başarısız');
      setSonuc({ basarili: false, mesaj, palet: kabulBilgi });
      setGecmis((prev) => [
        { basarili: false, mesaj, no: kabulBilgi.palet_no, rafKod: kod, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      return false;
    } finally {
      setYukleniyor(false);
      setBarkodInput('');
    }
  }, [barkodInput, kabulBilgi, rafListesi]);

  const toggleManuel = useCallback((e) => {
    if (e && e.currentTarget) e.currentTarget.blur();

    const el = inputRef.current;
    setManuelAcik((onceki) => {
      const yeni = !onceki;
      if (!el) return yeni;
      
      if (yeni) {
        el.setAttribute('inputmode', 'text');
        el.focus();
      } else {
        el.setAttribute('inputmode', 'none');
        el.blur();
        setTimeout(() => el.focus({ preventScroll: true }), 50);
      }
      return yeni;
    });
  }, []);

  // YENİ: İptal Et / Yeni Palet Okut fonksiyonu
  const sifirla = () => {
    setSonuc(null);
    setKabulBilgi(null);
    setBarkodInput('');
    setManuelAcik(false);
    setAdim(ADIM.PALET);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  // YENİ: Hata durumunda aynı paleti tutup raf okutma ekranına dönme
  const ayniPaletIcinRafOkut = () => {
    setSonuc(null);
    setBarkodInput('');
    setManuelAcik(false);
    setAdim(ADIM.RAF);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const isRaf = adim === ADIM.RAF;
  // YENİ: Raf adımındaysa ve raflar yükleniyorsa tarama engellenir
  const scanDisabled = yukleniyor || kameraAcik || (isRaf && raflarYukleniyor);
  const scanMode = isRaf ? 'raf' : 'palet';
  
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

  const headerInfo = isRaf
    ? { baslik: 'RAF YERLEŞTİRME', alt: 'ADIM 2/2', icon: MapPin, bg: 'bg-emerald-600', text: 'text-emerald-50' }
    : { baslik: 'ÜRETİM KABUL', alt: 'ADIM 1/2', icon: Factory, bg: 'bg-blue-600', text: 'text-blue-50' };
  const HeaderIcon = headerInfo.icon;

  return (
    <div className="w-full min-h-screen bg-slate-100 dark:bg-slate-950 flex flex-col">
      <header className={`${headerInfo.bg} shadow-md`}>
        <div className="px-4 py-4 max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 p-2.5 rounded-lg">
              <HeaderIcon className="w-7 h-7 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className={`text-[12px] font-bold ${headerInfo.text} uppercase tracking-wider`}>{headerInfo.alt}</p>
              <h1 className="text-xl font-black text-white tracking-tight">{headerInfo.baslik}</h1>
            </div>
          </div>
        </div>
        
        {isRaf && kabulBilgi && (
          <div className="bg-emerald-800 text-white px-4 py-3 border-t border-emerald-500/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 opacity-80" />
              <span className="font-mono font-bold text-lg">{kabulBilgi.palet_no}</span>
            </div>
            <span className="font-bold text-emerald-200">{kabulBilgi.koli_adedi} Koli</span>
          </div>
        )}
      </header>

      <main className="flex-1 px-4 py-6 max-w-md mx-auto w-full flex flex-col gap-4">
        <AnimatePresence mode="wait">
          {(adim === ADIM.PALET || adim === ADIM.RAF) && (
            <Motion.div key={`scan-${adim}`} variants={stepVariants} initial="initial" animate="animate" exit="exit" className="flex flex-col gap-4 flex-1">
              
              <ScannerHazirKarti 
                isRaf={isRaf} 
                busy={yukleniyor} 
                zebraDetected={zebraDetected} 
                raflarYukleniyor={raflarYukleniyor} // YENİ PROP EKLENDİ
              />

              <div className="grid gap-3 mt-auto">
                <div className={`overflow-hidden transition-all duration-200 ${manuelAcik ? 'h-auto' : 'h-0'}`} aria-hidden={!manuelAcik}>
                  <div className="flex gap-2">
                    <input
                      ref={scanInput.inputRef}
                      className="flex-1 bg-white dark:bg-slate-900 border-2 border-slate-300 dark:border-slate-700 rounded-xl px-4 h-16 text-slate-900 dark:text-white text-lg font-mono font-bold tracking-widest uppercase focus:outline-none focus:border-blue-500 disabled:opacity-50"
                      placeholder={isRaf ? 'RAF BARKODU' : 'PALET BARKODU'}
                      value={barkodInput}
                      onChange={(e) => setBarkodInput(e.target.value)}
                      onKeyDown={scanInput.handleKeyDown}
                      onBlur={scanInput.handleBlur}
                      disabled={scanDisabled}
                      autoComplete="off"
                      autoCapitalize="characters"
                      spellCheck={false}
                      tabIndex={manuelAcik ? 0 : -1}
                      inputMode={manuelAcik ? 'text' : 'none'}
                    />
                    <button
                      onClick={() => void scanInput.submitScan()}
                      disabled={scanDisabled || !barkodInput.trim()}
                      tabIndex={manuelAcik ? 0 : -1}
                      className={`h-16 w-16 flex items-center justify-center rounded-xl text-white font-bold transition-colors ${isRaf ? 'bg-emerald-600 active:bg-emerald-700' : 'bg-blue-600 active:bg-blue-700'} disabled:opacity-50`}
                    >
                      <ArrowRight className="w-8 h-8" strokeWidth={3} />
                    </button>
                  </div>
                </div>

                <FatButton 
                  icon={Keyboard} 
                  label={manuelAcik ? "KLAVYEYİ GİZLE" : "MANUEL GİRİŞ YAP"} 
                  onClick={toggleManuel} 
                  variant="secondary"
                  disabled={isRaf && raflarYukleniyor}
                />

                {!zebraDetected && (
                  <FatButton 
                    icon={Camera} 
                    label="KAMERAYI AÇ" 
                    onClick={() => setKameraAcik(true)} 
                    variant="secondary"
                    disabled={isRaf && raflarYukleniyor}
                  />
                )}

                {/* YENİ: Paleti Değiştir ve İşlemi İptal Et Butonları */}
                {isRaf && (
                  <div className="grid grid-cols-2 gap-3 mt-2 border-t border-slate-200 dark:border-slate-800 pt-4">
                    <FatButton 
                      icon={ArrowLeft} 
                      label="PALET DEĞİŞ" 
                      onClick={sifirla} 
                      variant="warning"
                    />
                    <FatButton 
                      icon={XCircle} 
                      label="İPTAL ET" 
                      onClick={sifirla} 
                      variant="danger"
                    />
                  </div>
                )}
              </div>
            </Motion.div>
          )}

          {adim === ADIM.SONUC && sonuc && (
            <Motion.div key="sonuc" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="flex flex-col flex-1">
              <div className={`flex-1 rounded-2xl flex flex-col items-center justify-center p-6 text-center shadow-lg border-2 ${sonuc.basarili ? 'bg-emerald-50 border-emerald-500 dark:bg-emerald-900/20 dark:border-emerald-500' : 'bg-red-50 border-red-500 dark:bg-red-900/20 dark:border-red-500'}`}>
                
                {sonuc.basarili ? (
                  <CheckCircle className="w-24 h-24 text-emerald-600 dark:text-emerald-400 mb-4" strokeWidth={2.5} />
                ) : (
                  <AlertOctagon className="w-24 h-24 text-red-600 dark:text-red-400 mb-4" strokeWidth={2.5} />
                )}
                
                <h2 className={`text-3xl font-black uppercase tracking-tight ${sonuc.basarili ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'}`}>
                  {sonuc.basarili ? 'İŞLEM BAŞARILI' : 'HATA OLUŞTU'}
                </h2>
                
                <p className="text-lg font-bold text-slate-700 dark:text-slate-300 mt-4 leading-snug">
                  {sonuc.mesaj}
                </p>

                {sonuc.basarili && sonuc.palet && (
                  <div className="w-full bg-white dark:bg-slate-900 rounded-xl p-4 mt-6 border border-slate-200 dark:border-slate-700 text-left">
                    <SolidInfoRow label="Palet" value={sonuc.palet.palet_no} />
                    <SolidInfoRow label="Raf" value={sonuc.rafKod} />
                  </div>
                )}
              </div>

              <div className="mt-4 grid gap-3">
                {/* YENİ: Başarısız işlemde aynı palet için rafı tekrar okut */}
                {!sonuc.basarili && sonuc.palet && (
                  <button onClick={ayniPaletIcinRafOkut} className="w-full h-16 bg-orange-500 text-white font-bold text-lg rounded-xl active:bg-orange-600 uppercase flex items-center justify-center gap-2">
                    <RefreshCcw className="w-6 h-6" />
                    AYNI PALET İÇİN RAF OKUT
                  </button>
                )}

                {/* YENİ: Palet Okutma İsmine Özel Vurgu */}
                <button onClick={sifirla} className="w-full h-20 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xl font-black rounded-xl uppercase tracking-widest active:scale-[0.98] transition-transform">
                  YENİ PALET OKUT
                </button>

                <button onClick={() => navigate('/terminal/ozet')} className="w-full h-16 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-lg rounded-xl active:bg-slate-300 dark:active:bg-slate-700 uppercase">
                  ÖZETE GİT
                </button>
              </div>
            </Motion.div>
          )}
        </AnimatePresence>
      </main>

      <ZXingBarcodeScanner isOpen={kameraAcik} onClose={() => setKameraAcik(false)} onScanSuccess={kameraIslem} />
    </div>
  );
}

// ─── Bileşenler ──────────────────────────────────────────────────────────────

function ScannerHazirKarti({ isRaf, busy, zebraDetected, raflarYukleniyor }) {
  const bg = isRaf ? 'bg-emerald-100 dark:bg-emerald-900/40 border-emerald-300 dark:border-emerald-700' : 'bg-blue-100 dark:bg-blue-900/40 border-blue-300 dark:border-blue-700';
  const text = isRaf ? 'text-emerald-800 dark:text-emerald-300' : 'text-blue-800 dark:text-blue-300';
  const isLoading = busy || (isRaf && raflarYukleniyor);
  
  return (
    <div className={`border-2 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[220px] ${bg} shadow-sm transition-colors`}>
      {isLoading ? (
        <div className={`w-16 h-16 border-4 border-t-transparent rounded-full animate-spin ${isRaf ? 'border-emerald-600' : 'border-blue-600'}`} />
      ) : (
        <ScanLine className={`w-20 h-20 ${text} mb-4`} strokeWidth={2} />
      )}
      
      {/* YENİ: Raf Yükleniyor Mesajı Entegrasyonu */}
      <h2 className={`text-2xl font-black text-center uppercase tracking-tight ${text} mt-2`}>
        {isLoading 
          ? (raflarYukleniyor ? 'RAFLAR YÜKLENİYOR...' : 'İŞLENİYOR...') 
          : isRaf ? 'RAF BARKODUNU OKUT' : 'PALET BARKODUNU OKUT'}
      </h2>
      
      <div className="mt-6 flex items-center gap-2 bg-white/60 dark:bg-black/30 px-4 py-2 rounded-lg">
        <Wifi className={`w-5 h-5 ${zebraDetected ? 'text-green-600' : 'text-slate-500'}`} />
        <span className="font-bold text-sm text-slate-700 dark:text-slate-300">
          {zebraDetected ? 'ZEBRA AKTİF' : 'CİHAZ DİNLENİYOR'}
        </span>
      </div>
    </div>
  );
}

function FatButton({ icon: Icon, label, onClick, variant = 'primary', disabled = false }) {
  const baseStyle = "w-full min-h-[64px] px-4 md:px-6 rounded-xl flex items-center justify-between font-bold text-sm md:text-lg active:scale-[0.98] transition-all disabled:opacity-50 disabled:active:scale-100";
  
  // YENİ: Varyantlara Danger ve Warning Renkleri Eklendi
  const styles = {
    primary: "bg-blue-600 text-white active:bg-blue-700",
    secondary: "bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-600 text-slate-800 dark:text-slate-200 active:bg-slate-100 dark:active:bg-slate-700",
    danger: "bg-red-100 dark:bg-red-900/40 border-2 border-red-300 dark:border-red-700 text-red-800 dark:text-red-300 active:bg-red-200 dark:active:bg-red-800",
    warning: "bg-orange-100 dark:bg-orange-900/40 border-2 border-orange-300 dark:border-orange-700 text-orange-800 dark:text-orange-300 active:bg-orange-200 dark:active:bg-orange-800"
  };

  return (
    <button onClick={onClick} disabled={disabled} className={`${baseStyle} ${styles[variant]}`}>
      <span className="flex items-center gap-2 md:gap-3">
        <Icon className="w-5 h-5 md:w-6 md:h-6 opacity-80" strokeWidth={2.5} />
        {label}
      </span>
      {/* Sadece uzun butonlarda Chevron gösteriyoruz, ikili gride sığması için sadeleştirdik */}
      {variant === 'primary' || variant === 'secondary' ? <ChevronDown className="w-6 h-6 opacity-50" /> : null}
    </button>
  );
}

function SolidInfoRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
      <span className="text-slate-500 dark:text-slate-400 font-bold uppercase text-sm">{label}</span>
      <span className="text-slate-900 dark:text-white font-black font-mono text-lg">{value}</span>
    </div>
  );
}

function zamanStr() {
  return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}