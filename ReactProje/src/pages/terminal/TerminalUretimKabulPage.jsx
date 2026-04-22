/**
 * TerminalUretimKabulPage — Üretimden palet kabul + raf yerleştirme (Terminal 2-tarama akışı)
 * Sleek Industrial & Glassmorphism UI (Light & Dark Mode)
 * 
 * Akış: Palet Barkod Okut → Kabul Et → Raf Barkod Okut → Yerleştir → Sonuç
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Factory, CheckCircle, XCircle, ArrowRight,
  RefreshCw, ScanLine, CornerDownRight, Package, Inbox, AlertTriangle, MapPin
} from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { hataMetni } from '../../utils/hata';
import { uretimPaletiKabulEt, uretimPaletiYerlestir, getRaflar, getUretimPaleti } from '../../services/api';
import ZXingBarcodeScanner from '../../components/common/ZXingBarcodeScanner';

// ── Sabitler ──────────────────────────────────────────────────────────────────
const ADIM = { PALET: 1, RAF: 2, SONUC: 3 };
const ZATEN_YERLESTIRME = ['YerlestirmeBekliyor'];
const ZATEN_BITMIS = ['Yerlestirildi'];

const stepVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: 'easeIn' } }
};

export default function TerminalUretimKabulPage() {
  const navigate = useNavigate();

  const [adim, setAdim] = useState(ADIM.PALET);
  const [barkodInput, setBarkodInput] = useState('');
  const [yukleniyor, setYukleniyor] = useState(false);
  const [sonuc, setSonuc] = useState(null);
  const [kabulBilgi, setKabulBilgi] = useState(null); // kabul edilen palet
  const [kameraAcik, setKameraAcik] = useState(false);
  const [kameraMod, setKameraMod] = useState('palet'); // 'palet' | 'raf'
  const [gecmis, setGecmis] = useState([]);
  const [rafListesi, setRafListesi] = useState([]);

  const inputRef = useRef(null);

  // Raf listesini başlangıçta yükle (client-side raf kodu → id çözümleme)
  useEffect(() => {
    getRaflar().then((r) => setRafListesi(r.data || [])).catch(() => {});
  }, []);

  // Her adım değişiminde inputa odaklan
  useEffect(() => {
    if (adim === ADIM.PALET || adim === ADIM.RAF) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [adim]);

  // ── Faz 1: Palet Okut ──────────────────────────────────────────────────────
  const paletOkut = useCallback(async (barkod) => {
    const no = barkod?.trim() || barkodInput.trim();
    if (!no) return;

    setYukleniyor(true);
    setSonuc(null);

    try {
      // Önce palet durumunu kontrol et
      let palet = null;
      try {
        const durumRes = await getUretimPaleti(no);
        palet = durumRes.data;
      } catch { /* palet bulunamadı — kabul-et dene */ }

      // Zaten yerleştirilmiş → bilgi göster
      if (palet && ZATEN_BITMIS.includes(palet.durum)) {
        setSonuc({ basarili: true, mesaj: 'Bu palet zaten yerleştirilmiş.', palet });
        setAdim(ADIM.SONUC);
        return;
      }

      // Zaten YERLESTIRME_BEKLIYOR → kabul adımını atla, direkt raf taramaya geç
      if (palet && ZATEN_YERLESTIRME.includes(palet.durum)) {
        setKabulBilgi(palet);
        setAdim(ADIM.RAF);
        toast.success(`${no} zaten kabul edilmiş — raf barkodunu okutun`);
        return;
      }

      // Normal akış: kabul-et
      const res = await uretimPaletiKabulEt(no);
      palet = res.data;
      setKabulBilgi(palet);
      setAdim(ADIM.RAF);
      toast.success(`${no} kabul edildi — şimdi raf barkodunu okutun`);
    } catch (err) {
      const mesaj = hataMetni(err, 'Kabul işlemi başarısız');
      setSonuc({ basarili: false, mesaj });
      setGecmis((prev) => [
        { basarili: false, mesaj, no, rafKod: null, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
    } finally {
      setYukleniyor(false);
      setBarkodInput('');
    }
  }, [barkodInput]);

  // ── Faz 2: Raf Okut + Yerleştir ────────────────────────────────────────────
  const rafOkut = useCallback(async (barkod) => {
    const kod = barkod?.trim() || barkodInput.trim();
    if (!kod || !kabulBilgi) return;

    // Raf kodu → raf_id çözümleme
    const raf = rafListesi.find(
      (r) => r.raf_kodu === kod || r.barkod === kod || String(r.id) === kod
    );
    if (!raf) {
      toast.error(`"${kod}" ile eşleşen raf bulunamadı`);
      setBarkodInput('');
      setTimeout(() => inputRef.current?.focus(), 50);
      return;
    }

    setYukleniyor(true);
    try {
      await uretimPaletiYerlestir(kabulBilgi.palet_no, raf.id);
      const yeniSonuc = {
        basarili: true,
        mesaj: `Palet ${raf.raf_kodu} rafına yerleştirildi.`,
        palet: kabulBilgi,
        rafKod: raf.raf_kodu,
      };
      setSonuc(yeniSonuc);
      setGecmis((prev) => [
        { ...yeniSonuc, no: kabulBilgi.palet_no, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      toast.success(`${kabulBilgi.palet_no} → ${raf.raf_kodu} yerleştirildi`);
    } catch (err) {
      const mesaj = hataMetni(err, 'Yerleştirme başarısız');
      setSonuc({ basarili: false, mesaj, palet: kabulBilgi });
      setGecmis((prev) => [
        { basarili: false, mesaj, no: kabulBilgi.palet_no, rafKod: kod, zaman: zamanStr() },
        ...prev.slice(0, 9),
      ]);
      setAdim(ADIM.SONUC);
      toast.error(mesaj);
    } finally {
      setYukleniyor(false);
      setBarkodInput('');
    }
  }, [barkodInput, kabulBilgi, rafListesi]);

  // ── Sıfırla ─────────────────────────────────────────────────────────────────
  const sifirla = () => {
    setSonuc(null);
    setKabulBilgi(null);
    setBarkodInput('');
    setAdim(ADIM.PALET);
  };

  // Aktif işlem fonksiyonu
  const aktifIslem = adim === ADIM.PALET ? paletOkut : rafOkut;
  const kameraIslem = (code) => { setKameraAcik(false); aktifIslem(code); };

  // Adım bilgileri
  const adimBilgi = {
    [ADIM.PALET]: { baslik: 'Üretimden Kabul & Yerleştir', alt: 'Adım 1/2 — Palet barkodunu okutun', scanText: 'PALET BARKODUNU OKUT', placeholder: 'PRD-YYYYMMDD-NNNN', renk: 'amber' },
    [ADIM.RAF]:   { baslik: 'Raf Yerleştirme', alt: `Adım 2/2 — ${kabulBilgi?.palet_no || ''} için raf okutun`, scanText: 'RAF BARKODUNU OKUT', placeholder: 'RAF-XXX veya raf kodu', renk: 'emerald' },
  };
  const info = adimBilgi[adim] || adimBilgi[ADIM.PALET];
  const isEmerald = adim === ADIM.RAF;

  return (
    <div className="w-full h-full relative overflow-hidden pb-6">
      
      {/* Arka Plan Ambient Glow */}
      <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-[80px] pointer-events-none transition-colors duration-500 ${isEmerald ? 'bg-emerald-500/10 dark:bg-emerald-500/5' : 'bg-amber-500/10 dark:bg-amber-500/5'}`} />

      {/* Başlık + Adım Göstergesi */}
      <div className="flex items-center justify-between p-4 pt-6 relative z-10">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-2xl border transition-colors duration-300 ${isEmerald ? 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20' : 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20'}`}>
            {isEmerald ? <MapPin className="w-6 h-6 text-emerald-600 dark:text-emerald-400" /> : <Factory className="w-6 h-6 text-amber-600 dark:text-amber-400" />}
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight leading-tight">{info.baslik}</h1>
            <p className="text-[12px] text-slate-500 dark:text-slate-400 font-medium">{info.alt}</p>
          </div>
        </div>
        {/* Adım göstergesi */}
        {(adim === ADIM.PALET || adim === ADIM.RAF) && (
          <div className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full ${adim >= ADIM.PALET ? (isEmerald ? 'bg-emerald-500' : 'bg-amber-500') : 'bg-slate-300 dark:bg-slate-600'}`} />
            <div className={`w-2.5 h-2.5 rounded-full ${adim >= ADIM.RAF ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`} />
          </div>
        )}
      </div>

      {/* Kabul edilen palet bilgi bandı (Faz 2'de görünür) */}
      {adim === ADIM.RAF && kabulBilgi && (
        <div className="mx-4 mb-3 bg-emerald-50/80 dark:bg-emerald-950/30 backdrop-blur-md rounded-[16px] p-3 border border-emerald-200 dark:border-emerald-500/20 flex items-center gap-3">
          <Package className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-mono text-[13px] font-bold text-emerald-700 dark:text-emerald-300 truncate block">{kabulBilgi.palet_no}</span>
            <span className="text-[11px] text-emerald-600/70 dark:text-emerald-400/60">{kabulBilgi.koli_adedi} koli — Kabul edildi ✓</span>
          </div>
        </div>
      )}

      <AnimatePresence mode="wait">
        {/* ─── Adım 1 & 2: Barkod Girişi ──────────────────────────────────── */}
        {(adim === ADIM.PALET || adim === ADIM.RAF) && (
          <motion.div key={`input-${adim}`} variants={stepVariants} initial="initial" animate="animate" exit="exit" className="px-4 space-y-5 max-w-md mx-auto relative z-10">
            
            <ScanButton onClick={() => setKameraAcik(true)} text={info.scanText} emerald={isEmerald} />

            <div className="space-y-3">
              <Divider text="Manuel Gir Veya Cihazla Oku" />
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  className={`flex-1 bg-white dark:bg-[#121316] border rounded-[20px] px-5 py-4 text-slate-900 dark:text-white text-[15px] font-mono tracking-wide placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:ring-1 transition-all shadow-[0_2px_10px_rgba(0,0,0,0.02)] ${isEmerald ? 'border-emerald-200/60 dark:border-emerald-800/60 focus:border-emerald-500/50 focus:ring-emerald-500/30' : 'border-slate-200/60 dark:border-slate-800/60 focus:border-amber-500/50 focus:ring-amber-500/30'}`}
                  placeholder={info.placeholder}
                  value={barkodInput}
                  onChange={(e) => setBarkodInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && aktifIslem()}
                  disabled={yukleniyor}
                />
                <motion.button 
                  whileTap={{ scale: 0.9 }} 
                  onClick={() => aktifIslem()} 
                  disabled={yukleniyor || !barkodInput.trim()}
                  className={`disabled:opacity-50 text-white w-14 rounded-[20px] flex items-center justify-center tap-highlight-transparent shadow-lg ${isEmerald ? 'bg-emerald-600 dark:bg-emerald-500 shadow-emerald-500/20' : 'bg-amber-600 dark:bg-amber-500 shadow-amber-500/20'}`}
                >
                  {yukleniyor ? <RefreshCw className="w-5 h-5 animate-spin" /> : <CornerDownRight className="w-5 h-5" strokeWidth={2.5} />}
                </motion.button>
              </div>
            </div>

            {/* Geçmiş — sadece Faz 1'de göster */}
            {adim === ADIM.PALET && (
              <div className="pt-4 space-y-3">
                <Divider text="Son İşlemler" />
                {gecmis.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 bg-white/50 dark:bg-[#121316]/50 backdrop-blur-sm rounded-[24px] border border-dashed border-slate-300 dark:border-slate-700">
                    <div className="bg-slate-100 dark:bg-[#1A1C20] p-3 rounded-full mb-2 shadow-inner border border-slate-200 dark:border-slate-800">
                      <Inbox className="w-6 h-6 text-slate-400 dark:text-slate-500" />
                    </div>
                    <p className="text-[12px] font-bold text-slate-500 dark:text-slate-400">Henüz işlem yapılmadı</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {gecmis.map((g, i) => (
                      <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-800/60 rounded-[16px] p-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {g.basarili ? <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" /> : <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />}
                          <div>
                            <span className="font-mono text-[13px] font-bold text-slate-700 dark:text-slate-300">{g.no}</span>
                            {g.rafKod && <span className="text-[11px] text-emerald-600 dark:text-emerald-400 ml-2">→ {g.rafKod}</span>}
                          </div>
                        </div>
                        <span className="text-[10px] font-mono font-medium text-slate-400 dark:text-slate-500">{g.zaman}</span>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* ─── Adım 3: Sonuç ─────────────────────────────────────────── */}
        {adim === ADIM.SONUC && sonuc && (
          <motion.div key="sonuc" variants={stepVariants} initial="initial" animate="animate" exit="exit" className="p-4 space-y-5 max-w-md mx-auto pt-4 relative z-10">
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
                  {sonuc.basarili ? 'Yerleştirildi!' : 'İşlem Hatası'}
                </h2>
                <p className="text-[14px] text-slate-600 dark:text-slate-400 mt-2 font-medium leading-relaxed max-w-[280px]">{sonuc.mesaj}</p>
              </div>
            </div>

            {sonuc.basarili && sonuc.palet && (
              <div className="bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md rounded-[24px] p-5 border border-slate-200/60 dark:border-slate-800/60 space-y-3 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                <InfoRow label="Palet" value={sonuc.palet.palet_no} mono />
                <InfoRow label="Lot No" value={sonuc.palet.lot_no || sonuc.palet.lot_id} mono highlight />
                <InfoRow label="Miktar" value={`${sonuc.palet.koli_adedi} Koli`} strong />
                {sonuc.rafKod && <InfoRow label="Raf" value={sonuc.rafKod} mono highlight />}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <button onClick={() => navigate('/terminal/ozet')} className="flex-1 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-[14px] rounded-[20px] py-4 transition-colors tap-highlight-transparent">
                Özete Dön
              </button>
              <motion.button whileTap={{ scale: 0.98 }} onClick={sifirla} className="flex-[2] bg-amber-600 dark:bg-amber-500 text-white font-black rounded-[20px] py-4 flex items-center justify-center gap-2 tap-highlight-transparent">
                <span className="mt-0.5">YENİ OKUTMA</span> <ArrowRight className="w-5 h-5" strokeWidth={2.5} />
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <ZXingBarcodeScanner isOpen={kameraAcik} onClose={() => setKameraAcik(false)} onScanSuccess={kameraIslem} />
    </div>
  );
}

// ── Yardımcılar ──────────────────────────────────────────────────────────────

function zamanStr() {
  return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

function ScanButton({ onClick, text, emerald }) {
  const base = 'w-full bg-white/80 dark:bg-[#121316]/80 backdrop-blur-md border rounded-[28px] py-8 flex flex-col items-center gap-3 transition-colors group shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)]';
  const border = emerald ? 'border-emerald-200/60 dark:border-emerald-800/60 hover:border-emerald-400/50 dark:hover:border-emerald-500/50' : 'border-slate-200/60 dark:border-slate-800/60 hover:border-amber-400/50 dark:hover:border-amber-500/50';
  const iconHover = emerald ? 'group-hover:bg-emerald-50 dark:group-hover:bg-emerald-500/10' : 'group-hover:bg-amber-50 dark:group-hover:bg-amber-500/10';
  const textHover = emerald ? 'group-hover:text-emerald-600 dark:group-hover:text-emerald-400' : 'group-hover:text-amber-600 dark:group-hover:text-amber-400';
  return (
    <motion.button whileTap={{ scale: 0.98 }} onClick={onClick} className={`${base} ${border}`}>
      <div className={`bg-slate-50 dark:bg-slate-800 p-4 rounded-[20px] ${iconHover} transition-colors`}>
        <ScanLine className={`w-10 h-10 text-slate-400 ${textHover} transition-colors`} strokeWidth={1.5} />
      </div>
      <span className={`text-slate-500 dark:text-slate-400 ${textHover} font-black text-[13px] tracking-widest`}>{text}</span>
    </motion.button>
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
