/**
 * TerminalUretimKabulPage — Üretimden palet kabul + raf yerleştirme (Terminal 2-tarama akışı)
 * SAHA ODAKLI ENDÜSTRİYEL UI: Yüksek kontrast, büyük dokunma hedefleri, animasyon gürültüsü yok.
 */
import { createElement, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Factory, CheckCircle, XCircle, ArrowRight, Wifi,
  ScanLine, Package, MapPin,
  Camera, Keyboard, ChevronDown, AlertOctagon, 
  ArrowLeft, RefreshCcw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { hataMetni } from '../../utils/hata';
import useTerminalScanInput from '../../hooks/useTerminalScanInput';
import { sanitizeBarkod, validateBarkodFormat } from '../../utils/barcode';
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
  const [sonuc, setSonuc] = useState(null);
  const [kabulBilgi, setKabulBilgi] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [, setGecmis] = useState([]);
  const [manuelAcik, setManuelAcik] = useState(false);

  const inputRef = useRef(null);

  // TanStack Query ile Raf Listesi Yönetimi
  const {
    data: rafListesi = [],
    isLoading: raflarYukleniyor,
    isError: rafYuklemeHatasi,
    refetch: fetchRaflar
  } = useQuery({
    queryKey: ['terminal-raflar'],
    queryFn: async () => {
      const res = await getRaflar();
      return res.data || [];
    },
    staleTime: 1000 * 60 * 5, // 5 dakika önbellekleme
    retry: 1
  });

  // ── Faz 1: Palet Okut ──────────────────────────────────────────────────────
  const paletOkut = useCallback(async (barkod, meta = {}) => {
    const no = sanitizeBarkod(barkod ?? barkodInput, 'palet');
    if (!no) return false;

    // Yanlış Barkod Tipi Kontrolü
    if (validateBarkodFormat(no, 'raf').valid) {
      hapticFeedback('error');
      setSonuc({ basarili: false, mesaj: 'HATA: Palet barkodu beklerken RAF barkodu okuttunuz.', okunan: no });
      setAdim(ADIM.SONUC);
      return false;
    }
    if (!validateBarkodFormat(no, 'palet').valid) {
      hapticFeedback('error');
      setSonuc({ basarili: false, mesaj: 'HATA: Geçersiz palet barkodu formatı.', okunan: no });
      setAdim(ADIM.SONUC);
      return false;
    }

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
        setSonuc({ basarili: false, mesaj: 'Bu palet ZATEN YERLEŞTİRİLMİŞ.', palet, okunan: no });
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
      setSonuc({ basarili: false, mesaj, okunan: no });
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

    // Yanlış Barkod Tipi Kontrolü
    if (validateBarkodFormat(kod, 'palet').valid) {
      hapticFeedback('error');
      setSonuc({ basarili: false, mesaj: 'HATA: Raf barkodu beklerken PALET barkodu okuttunuz.', okunan: kod, palet: kabulBilgi });
      setAdim(ADIM.SONUC);
      return false;
    }
    if (!validateBarkodFormat(kod, 'raf').valid) {
      hapticFeedback('error');
      setSonuc({ basarili: false, mesaj: 'HATA: Geçersiz raf barkodu formatı.', okunan: kod, palet: kabulBilgi });
      setAdim(ADIM.SONUC);
      return false;
    }

    const raf = rafListesi.find(
      (r) => [r.kod, r.raf_kodu, r.barkod, String(r.id)]
        .filter(Boolean)
        .some((aday) => String(aday).toUpperCase() === kod)
    );
    
    if (!raf) {
      hapticFeedback('error');
      setSonuc({ basarili: false, mesaj: `Sistemde "${kod}" ile eşleşen raf bulunamadı.`, okunan: kod, palet: kabulBilgi });
      setBarkodInput('');
      setAdim(ADIM.SONUC);
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
        okunan: kod
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
      setSonuc({ basarili: false, mesaj, palet: kabulBilgi, okunan: kod });
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

  const sifirla = () => {
    setSonuc(null);
    setKabulBilgi(null);
    setBarkodInput('');
    setManuelAcik(false);
    setAdim(ADIM.PALET);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const ayniPaletIcinRafOkut = () => {
    setSonuc(null);
    setBarkodInput('');
    setManuelAcik(false);
    setAdim(ADIM.RAF);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const isRaf = adim === ADIM.RAF;
  const scanDisabled = yukleniyor || kameraAcik || (isRaf && raflarYukleniyor) || (isRaf && rafYuklemeHatasi);
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
    validateFormat: false, // UI tabanlı spesifik hata yakalayabilmek için hook'un toast'ını kapattık
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

  return (
    <div className="w-full h-full relative overflow-hidden pb-6">
      <AnimatePresence mode="wait">
        {(adim === ADIM.PALET || adim === ADIM.RAF) && (
          <Motion.div key={`scan-${adim}`} variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-2">
            <AdimBasligi
              adim={isRaf ? 2 : 1}
              baslik={isRaf ? 'Raf Yerleştirme' : 'Üretim Kabul'}
              isRaf={isRaf}
            />

            {isRaf && kabulBilgi && <KabulPaletKarti kabulBilgi={kabulBilgi} />}

            {isRaf && rafYuklemeHatasi ? (
              <div className="border-2 border-red-300 dark:border-red-700/60 rounded-[28px] px-5 py-7 flex flex-col items-center justify-center min-h-[200px] bg-red-50 dark:bg-red-900/20 shadow-sm transition-colors text-center">
                <AlertOctagon className="w-16 h-16 text-red-600 dark:text-red-400 mb-4" strokeWidth={2} />
                <h2 className="text-xl font-black uppercase tracking-tight text-red-800 dark:text-red-300 mb-2">BAĞLANTI HATASI</h2>
                <p className="text-[13px] font-bold text-red-600 dark:text-red-400 mb-5 leading-tight">
                  Raf listesi yüklenemedi.<br/>Lütfen bağlantınızı kontrol edin.
                </p>
                <div className="w-full max-w-[240px]">
                  <FatButton icon={RefreshCcw} label="TEKRAR DENE" onClick={() => fetchRaflar()} variant="danger" />
                </div>
              </div>
            ) : (
              <ScannerHazirKarti 
                isRaf={isRaf} 
                busy={yukleniyor} 
                zebraDetected={zebraDetected} 
                raflarYukleniyor={raflarYukleniyor}
              />
            )}

            <div className="grid gap-3 relative">
              <div className={`overflow-hidden transition-all duration-200 ${manuelAcik ? 'h-auto' : 'absolute h-0 w-0 pointer-events-none'}`} aria-hidden={!manuelAcik}>
                <div className="flex gap-2">
                  <input
                    ref={scanInput.inputRef}
                    className="min-w-0 flex-1 bg-white dark:bg-[#121316] border border-slate-200/60 dark:border-slate-800/60 rounded-[20px] px-5 h-16 text-slate-900 dark:text-white text-[15px] font-mono font-bold tracking-wide uppercase placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all disabled:opacity-50 shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
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
                    className={`h-16 w-16 shrink-0 flex items-center justify-center rounded-[20px] text-white font-bold transition-colors shadow-lg ${isRaf ? 'bg-emerald-600 active:bg-emerald-700 shadow-emerald-600/20' : 'bg-blue-600 active:bg-blue-700 shadow-blue-500/20'} disabled:opacity-50`}
                  >
                    <ArrowRight className="w-7 h-7" strokeWidth={2.5} />
                  </button>
                </div>
              </div>

              <FatButton 
                icon={Keyboard} 
                label={manuelAcik ? "KLAVYEYİ GİZLE" : "MANUEL GİRİŞ YAP"} 
                onClick={toggleManuel} 
                variant="secondary"
                disabled={isRaf && (raflarYukleniyor || rafYuklemeHatasi)}
              />

              {!zebraDetected && (
                <FatButton 
                  icon={Camera} 
                  label="KAMERAYI AÇ" 
                  onClick={() => setKameraAcik(true)} 
                  variant="secondary"
                  disabled={isRaf && (raflarYukleniyor || rafYuklemeHatasi)}
                />
              )}

              {isRaf && (
                <div className="grid grid-cols-2 gap-2.5 border-t border-slate-200 dark:border-slate-800/60 pt-4">
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
          <Motion.div key="sonuc" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-6">
            <div className={`rounded-[32px] flex flex-col items-center justify-center p-8 text-center shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] border relative overflow-hidden ${sonuc.basarili ? 'bg-emerald-50/80 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-500/20' : 'bg-red-50/80 border-red-200 dark:bg-red-900/20 dark:border-red-500/20'}`}>
              {sonuc.basarili ? (
                <CheckCircle className="w-20 h-20 text-emerald-600 dark:text-emerald-400 mb-5" strokeWidth={2.5} />
              ) : (
                <AlertOctagon className="w-20 h-20 text-red-600 dark:text-red-400 mb-5" strokeWidth={2.5} />
              )}
              
              <h2 className={`text-2xl font-black uppercase tracking-tight ${sonuc.basarili ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'}`}>
                {sonuc.basarili ? 'İŞLEM BAŞARILI' : 'HATA OLUŞTU'}
              </h2>
              
              <p className="text-[14px] font-bold text-slate-700 dark:text-slate-300 mt-3 leading-snug max-w-[280px]">
                {sonuc.mesaj}
              </p>

              <div className={`w-full rounded-[20px] p-4 mt-6 border text-left ${sonuc.basarili ? 'bg-white/80 dark:bg-[#121316]/80 border-slate-200/60 dark:border-slate-800/60' : 'bg-red-100/50 dark:bg-red-900/40 border-red-200 dark:border-red-800/50'}`}>
                {sonuc.okunan && <SolidInfoRow label="Okunan Barkod" value={sonuc.okunan} />}
                {sonuc.palet && <SolidInfoRow label="Mevcut Palet" value={sonuc.palet.palet_no} />}
                {sonuc.rafKod && <SolidInfoRow label="Yerleşen Raf" value={sonuc.rafKod} />}
              </div>
            </div>

            <div className="grid gap-3">
              {!sonuc.basarili && sonuc.palet && (
                <button onClick={ayniPaletIcinRafOkut} className="w-full min-h-[60px] px-4 bg-orange-500 text-white font-bold text-[14px] rounded-[20px] active:bg-orange-600 uppercase flex items-center justify-center gap-2 leading-tight">
                  <RefreshCcw className="w-5 h-5 shrink-0" />
                  <span>AYNI PALET İÇİN RAF OKUT</span>
                </button>
              )}

              <button onClick={sifirla} className="w-full min-h-[64px] px-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-[16px] font-black rounded-[20px] uppercase tracking-wide active:scale-[0.98] transition-transform">
                YENİ PALET OKUT
              </button>

              <button onClick={() => navigate('/terminal/ozet')} className="w-full min-h-[60px] px-4 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-[14px] rounded-[20px] active:bg-slate-300 dark:active:bg-slate-700 uppercase">
                ÖZETE GİT
              </button>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>

      <ZXingBarcodeScanner isOpen={kameraAcik} onClose={() => setKameraAcik(false)} onScanSuccess={kameraIslem} />
    </div>
  );
}

// ─── Bileşenler ──────────────────────────────────────────────────────────────

function AdimBasligi({ adim, baslik, isRaf }) {
  const Icon = isRaf ? MapPin : Factory;
  const tema = isRaf
    ? {
        step: 'text-emerald-600/80 dark:text-emerald-400/80',
        iconWrap: 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20',
        icon: 'text-emerald-600 dark:text-emerald-400',
        progress: 'bg-emerald-500 dark:bg-emerald-400',
      }
    : {
        step: 'text-blue-600/80 dark:text-blue-400/80',
        iconWrap: 'bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/20',
        icon: 'text-blue-600 dark:text-blue-400',
        progress: 'bg-blue-500 dark:bg-blue-400',
      };

  return (
    <div className="flex items-center gap-3 bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md p-2 pr-4 rounded-[20px] border border-slate-200/60 dark:border-slate-800/60 shadow-[0_2px_10px_rgba(0,0,0,0.02)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.2)]">
      <div className={`w-10 h-10 rounded-[14px] border flex items-center justify-center shrink-0 ${tema.iconWrap}`}>
        {createElement(Icon, { className: `w-5 h-5 ${tema.icon}`, strokeWidth: 2.5 })}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-[10px] uppercase tracking-widest font-bold mb-0.5 ${tema.step}`}>Adım {adim}/2</p>
        <h1 className="text-[17px] font-bold text-slate-900 dark:text-white tracking-tight leading-none truncate">{baslik}</h1>
      </div>
      <div className="flex gap-1.5 shrink-0">
        {[1, 2].map((sira) => (
          <div key={sira} className={`h-1.5 rounded-full transition-all duration-300 ${sira <= adim ? `${tema.progress} w-5` : 'bg-slate-200 dark:bg-slate-800 w-2'}`} />
        ))}
      </div>
    </div>
  );
}

function KabulPaletKarti({ kabulBilgi }) {
  return (
    <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] p-4 border border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between gap-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
      <div className="min-w-0 flex items-center gap-3">
        <div className="bg-emerald-50 dark:bg-emerald-500/10 p-2.5 rounded-[16px] border border-emerald-200 dark:border-emerald-500/20 shrink-0">
          <Package className="w-5 h-5 text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
        </div>
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 dark:text-slate-400 font-bold">Kabul Edilen Palet</p>
          <p className="font-mono font-black text-[16px] text-slate-900 dark:text-white truncate">{kabulBilgi.palet_no}</p>
        </div>
      </div>
      <span className="shrink-0 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400 rounded-xl px-3 py-1.5 text-[12px] font-black">
        {kabulBilgi.koli_adedi} Koli
      </span>
    </div>
  );
}

function ScannerHazirKarti({ isRaf, busy, zebraDetected, raflarYukleniyor }) {
  const bg = isRaf ? 'bg-emerald-100 dark:bg-emerald-900/40 border-emerald-300 dark:border-emerald-700' : 'bg-blue-100 dark:bg-blue-900/40 border-blue-300 dark:border-blue-700';
  const text = isRaf ? 'text-emerald-800 dark:text-emerald-300' : 'text-blue-800 dark:text-blue-300';
  const isLoading = busy || (isRaf && raflarYukleniyor);
  
  return (
    <div className={`border-2 rounded-[28px] px-5 py-7 flex flex-col items-center justify-center min-h-[200px] ${bg} shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] transition-colors`}>
      {isLoading ? (
        <div className={`w-14 h-14 border-4 border-t-transparent rounded-full animate-spin ${isRaf ? 'border-emerald-600' : 'border-blue-600'}`} />
      ) : (
        <ScanLine className={`w-16 h-16 ${text} mb-4`} strokeWidth={2} />
      )}
      
      <h2 className={`text-xl font-black text-center uppercase tracking-tight leading-tight ${text} mt-2`}>
        {isLoading 
          ? (raflarYukleniyor ? 'RAFLAR YÜKLENİYOR...' : 'İŞLENİYOR...') 
          : isRaf ? 'RAF BARKODUNU OKUT' : 'PALET BARKODUNU OKUT'}
      </h2>
      
      <div className="mt-5 flex items-center gap-2 bg-white/60 dark:bg-black/30 px-4 py-2 rounded-xl">
        <Wifi className={`w-4 h-4 ${zebraDetected ? 'text-green-600' : 'text-slate-500'}`} />
        <span className="font-bold text-[12px] text-slate-700 dark:text-slate-300">
          {zebraDetected ? 'ZEBRA AKTİF' : 'CİHAZ DİNLENİYOR'}
        </span>
      </div>
    </div>
  );
}

function FatButton({ icon, label, onClick, variant = 'primary', disabled = false }) {
  const baseStyle = "w-full min-h-[60px] px-4 rounded-[20px] flex items-center justify-between gap-3 font-bold text-[13px] sm:text-[14px] leading-tight active:scale-[0.98] transition-all disabled:opacity-50 disabled:active:scale-100 tap-highlight-transparent";
  
  const styles = {
    primary: "bg-blue-600 text-white active:bg-blue-700",
    secondary: "bg-white/80 dark:bg-[#121316]/80 border border-slate-200/60 dark:border-slate-800/60 text-slate-800 dark:text-slate-200 active:bg-slate-100 dark:active:bg-slate-800 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]",
    danger: "bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700/60 text-red-800 dark:text-red-300 active:bg-red-100 dark:active:bg-red-800/60",
    warning: "bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-700/60 text-orange-800 dark:text-orange-300 active:bg-orange-100 dark:active:bg-orange-800/60"
  };

  return (
    <button onClick={onClick} disabled={disabled} className={`${baseStyle} ${styles[variant]}`}>
      <span className="min-w-0 flex items-center gap-2.5 text-left">
        {createElement(icon, { className: 'w-5 h-5 shrink-0 opacity-80', strokeWidth: 2.5 })}
        <span className="min-w-0 break-words">{label}</span>
      </span>
      {variant === 'primary' || variant === 'secondary' ? <ChevronDown className="w-5 h-5 shrink-0 opacity-50" /> : null}
    </button>
  );
}

function SolidInfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2 border-b border-slate-500/10 last:border-0">
      <span className="text-slate-500 dark:text-slate-400 font-bold uppercase text-[12px] shrink-0">{label}</span>
      <span className="min-w-0 text-slate-900 dark:text-white font-black font-mono text-[15px] truncate text-right">{value}</span>
    </div>
  );
}

function zamanStr() {
  return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}