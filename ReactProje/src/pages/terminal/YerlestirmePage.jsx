/**
 * YerlestirmePage — 4 adımlı scan-to-verify yerleştirme akışı.
 *
 * Adım 1: Sıradaki Görevi Al / Görev Detayı (operasyonel bilgilerle)
 * Adım 2: Paleti Tara (gerçek barkod doğrulaması)
 * Adım 3: Rafa Yerleştir (raf kodu gösterir, ID değil)
 * Adım 4: Sonuç (başarı veya hata + alternatifler)
 */
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Package, Camera, CheckCircle, XCircle, ArrowRight,
  RefreshCw, ChevronLeft, Scan, CornerDownRight, AlertTriangle,
  AlertCircle, MapPin, ShieldAlert,
} from 'lucide-react';
import toast from 'react-hot-toast';
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

export default function YerlestirmePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, run } = useAsync();
  const { user } = useAuth();
  const overrideYetkisiVar = user?.rol === 'admin' || user?.rol === 'lojistik';

  const [adim, setAdim] = useState(ADIM.GOREV);
  const [gorev, setGorev] = useState(location.state?.gorev || null);
  const [bekleyenSayisi, setBekleyenSayisi] = useState(null);
  const [paletBarkod, setPaletBarkod] = useState('');
  const [, setRafBarkod] = useState('');
  const [sonuc, setSonuc] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [kameraMod, setKameraMod] = useState('palet'); // 'palet' | 'raf'
  const [manuelPalet, setManuelPalet] = useState('');
  const [manuelRaf, setManuelRaf] = useState('');
  const [overrideModal, setOverrideModal] = useState(false);
  const [overrideNeden, setOverrideNeden] = useState('');
  // overrideRafSec: null | { id, kod, bos_slot, skor }
  const [overrideRafSec, setOverrideRafSec] = useState(null);
  const [sorunSheet, setSorunSheet] = useState(false);
  const [sorunTip, setSorunTip] = useState(null); // 'karantina' | 'iptal'
  const [sorunNeden, setSorunNeden] = useState('');

  const bekleyenYukle = async () => {
    try {
      const res = await getBekleyenGorevOzet();
      setBekleyenSayisi(res.data.toplam_bekleyen);
    } catch {
      // sessiz
    }
  };

  useEffect(() => {
    if (gorev) return undefined;

    let iptal = false;

    const bekleyenYukle = async () => {
      try {
        const res = await getBekleyenGorevOzet();
        if (!iptal) {
          setBekleyenSayisi(res.data.toplam_bekleyen);
        }
      } catch {
        // sessiz
      }
    };

    void bekleyenYukle();

    return () => {
      iptal = true;
    };
  }, [gorev]);

  // Görev al
  const goreviAl = async () => {
    await run(async () => {
      const res = await siradakiGorevisiniAl();
      if (res.data) {
        setGorev(res.data);
      } else {
        toast('Havuzda bekleyen görev yok.', { icon: '📦' });
      }
    });
  };

  // Görevi başlat (paleti fiziksel olarak al).
  const goreviBaslatAction = async () => {
    if (gorev.durum === 'DevamEdiyor') {
      setAdim(ADIM.PALET);
      return;
    }
    await run(async () => {
      await goreviBaslat(gorev.id);
      setGorev((g) => ({ ...g, durum: 'DevamEdiyor' }));
      setAdim(ADIM.PALET);
    });
  };

  // Görevi bırak
  const goreviBirakAction = async () => {
    await run(async () => {
      await goreviBirak(gorev.id);
      toast('Görev havuza iade edildi.');
      setGorev(null);
      setAdim(ADIM.GOREV);
      void bekleyenYukle();
    });
  };

  // Palet doğrulama — gerçek barkod eşleşmesi
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

  // Yerleştir
  const yerlestir = async (rafKod) => {
    const r = rafKod.trim();
    if (!r) return;
    setRafBarkod(r);
    await run(async () => {
      const res = await terminalYerlestir({
        gorev_id: gorev.id,
        palet_barkod: paletBarkod,
        raf_barkod: r,
      });
      setSonuc(res.data);
      setAdim(ADIM.SONUC);
    });
  };

  // Override
  const overrideYap = async () => {
    if (!overrideRafSec) {
      toast.error('Lütfen önce bir alternatif raf seçin.');
      return;
    }
    if (!overrideNeden.trim()) {
      toast.error('Override gerekçesi zorunludur.');
      return;
    }
    await run(async () => {
      const res = await goreviOverride(gorev.id, {
        gerceklesen_raf_id: overrideRafSec.id,
        neden: overrideNeden,
      });
      setSonuc({ basarili: true, durum: 'TAMAMLANDI', mesaj: 'Override ile yerleştirildi.', ...res.data });
      setAdim(ADIM.SONUC);
      setOverrideModal(false);
      setOverrideNeden('');
    });
  };

  // Sorun bildir — gönder
  const sorunGonder = async () => {
    if (!sorunNeden.trim()) {
      toast.error('Açıklama zorunludur.');
      return;
    }
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

  // ─── Adım 1: Görev ───────────────────────────────────────────
  if (adim === ADIM.GOREV) {
    return (
      <div className="p-4 space-y-5 max-w-sm mx-auto pt-4 relative">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-black text-white tracking-tight">Yerleştirme</h1>
        </div>

        {bekleyenSayisi !== null && !gorev && (
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-3xl p-6 border border-slate-700/50 text-center relative overflow-hidden backdrop-blur-sm shadow-xl shadow-black/10 mt-6">
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-amber-500/10 rounded-full blur-[40px]"></div>
            <p className="text-4xl font-black text-amber-400 drop-shadow-md">{bekleyenSayisi}</p>
            <p className="text-[11px] font-bold text-slate-400 mt-2 tracking-widest uppercase">Havuzda Bekleyen</p>
          </div>
        )}

        {!gorev ? (
          <div className="relative mt-8">
            <div className="absolute -inset-[3px] bg-gradient-to-r from-amber-600 via-amber-400 to-amber-600 rounded-3xl blur-[14px] opacity-25 animate-pulse"></div>
            <button
              onClick={goreviAl}
              disabled={loading}
              className="relative w-full bg-gradient-to-br from-amber-400 to-amber-500 border border-amber-300/50 hover:from-amber-300 hover:to-amber-400 active:scale-[0.98] disabled:opacity-50 text-slate-950 font-black text-[17px] rounded-3xl py-5 flex items-center justify-center gap-3 transition-all shadow-[0_0_30px_rgba(245,158,11,0.2)] overflow-hidden"
            >
              {/* İç parlama efekti */}
              <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-3xl pointer-events-none"></div>
              {loading ? <RefreshCw className="w-7 h-7 animate-spin drop-shadow-sm" /> : (
                <>
                  <span className="tracking-wide relative z-10 drop-shadow-sm">SIRADAKİ GÖREVİ AL</span>
                  <ArrowRight className="w-7 h-7 relative z-10 drop-shadow-sm" strokeWidth={2.5} />
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="relative mt-2">
            <div className="bg-slate-900/80 border border-slate-700/80 rounded-3xl overflow-hidden backdrop-blur-md shadow-2xl shadow-black/20">
              <div className="absolute left-0 top-0 bottom-0 w-[5px] bg-amber-500 shadow-[2px_0_15px_rgba(245,158,11,0.4)]" />

              <div className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="bg-amber-400/10 p-1.5 rounded-lg border border-amber-400/20">
                      <Package className="w-4 h-4 text-amber-400" />
                    </div>
                    <span className="text-[11px] uppercase tracking-widest text-slate-300 font-bold">Görev #{gorev.id}</span>
                  </div>
                  <OncelikBadge oncelik={gorev.oncelik} />
                </div>

                {/* Operasyonel bilgiler */}
                <div className="space-y-3 pt-2">
                  {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} strong />}
                  {gorev.palet_barkodu && <InfoRow label="Palet" value={gorev.palet_barkodu} mono />}
                  {gorev.lot_no && <InfoRow label="Lot No" value={gorev.lot_no} mono />}
                  {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}

                  <div className="w-full h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent my-3" />

                  {gorev.onerilen_raf_kodu
                    ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
                    : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
                  {gorev.zone_adi && (
                    <div className="flex items-center justify-between gap-4 py-1">
                      <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider shrink-0">Zon</span>
                      <span className="flex items-center gap-1.5 text-sm font-bold text-slate-200 bg-slate-800/50 px-2.5 py-1 rounded-lg border border-white/5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        {gorev.zone_adi}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-2 p-3 bg-slate-950/50 border-t border-slate-800/50">
                <button
                  onClick={goreviBirakAction}
                  disabled={loading}
                  className="flex-1 bg-slate-800/80 hover:bg-slate-700 border border-transparent hover:border-slate-600 active:scale-95 text-slate-300 font-bold text-[13px] rounded-2xl py-3.5 transition-all"
                >
                  Bırak
                </button>
                <button
                  onClick={goreviBaslatAction}
                  disabled={loading}
                  className="flex-[2] relative bg-amber-500 hover:bg-amber-400 text-slate-950 font-black rounded-2xl py-3.5 flex items-center justify-center gap-2 transition-all shadow-[0_5px_15px_-3px_rgba(245,158,11,0.3)] active:scale-95"
                >
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
                    <><span className="drop-shadow-sm">{gorev.durum === 'DevamEdiyor' ? 'DEVAM ET' : 'BAŞLAT'}</span> <ArrowRight className="w-5 h-5 drop-shadow-sm" strokeWidth={2.5} /></>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ─── Adım 2: Palet Scan ───────────────────────────────────────────
  if (adim === ADIM.PALET) {
    return (
      <div className="p-4 space-y-5 max-w-sm mx-auto pt-2">
        <AdimHeader adim={2} toplam={3} baslik="Paleti Tara" onGeri={() => setAdim(ADIM.GOREV)} />

        <div className="bg-slate-900/60 rounded-3xl p-5 border border-slate-800/50 space-y-2 backdrop-blur-md shadow-lg shadow-black/10">
          {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} strong />}
          <InfoRow label="Beklenen Palet" value={gorev.palet_barkodu || `#${gorev.palet_id}`} mono highlight />
          {gorev.lot_no && <InfoRow label="Lot" value={gorev.lot_no} mono />}
          {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}
        </div>

        {/* Kamera Butonu */}
        <button
          onClick={() => { setKameraMod('palet'); setKameraAcik(true); }}
          className="relative w-full overflow-hidden bg-slate-900/50 hover:bg-slate-800/80 border-2 border-dashed border-slate-700 hover:border-amber-500/80 rounded-3xl py-12 flex flex-col items-center gap-3 transition-all duration-300 group active:scale-[0.98] backdrop-blur-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="bg-slate-800/80 p-4 rounded-full group-hover:bg-amber-500/10 transition-colors relative z-10 border border-slate-700/50 group-hover:border-amber-500/30">
            <Camera className="w-10 h-10 text-slate-400 group-hover:text-amber-400 transition-colors" strokeWidth={1.5} />
          </div>
          <span className="text-slate-300 group-hover:text-amber-400 font-black text-sm tracking-widest relative z-10 transition-colors drop-shadow-sm">KAMERA İLE OKUT</span>
        </button>

        {/* Manuel Giriş */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <div className="h-px bg-slate-800 flex-1"></div>
            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Manuel Gir</p>
            <div className="h-px bg-slate-800 flex-1"></div>
          </div>
          <div className="flex gap-2 relative">
            <input
              className="flex-1 bg-slate-900/80 border border-slate-700/80 rounded-2xl px-5 py-4 text-slate-100 text-[15px] font-mono tracking-wide placeholder-slate-600 focus:outline-none focus:border-amber-500/80 focus:ring-1 focus:ring-amber-500/50 transition-all shadow-inner"
              placeholder="PLT-2026-XXXXX"
              value={manuelPalet}
              onChange={(e) => setManuelPalet(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && paletDogrula(manuelPalet)}
            />
            <button
              onClick={() => paletDogrula(manuelPalet)}
              className="bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 font-black w-14 rounded-2xl flex items-center justify-center transition-all shadow-[0_4px_15px_rgba(245,158,11,0.2)]"
            >
              <CornerDownRight className="w-5 h-5" strokeWidth={2.5} />
            </button>
          </div>
        </div>

        {/* Sorun Bildir */}
        <div className="pt-2">
          <button
            onClick={() => setSorunSheet(true)}
            className="w-full flex items-center justify-center gap-2 text-[13px] font-bold text-slate-500 hover:text-red-400 py-3 rounded-xl hover:bg-red-500/10 transition-all active:scale-95"
          >
            <AlertCircle className="w-4 h-4" />
            SORUN BİLDİR
          </button>
        </div>

        <ZXingBarcodeScanner
          isOpen={kameraAcik && kameraMod === 'palet'}
          onClose={() => setKameraAcik(false)}
          onScanSuccess={(code) => { setKameraAcik(false); paletDogrula(code); }}
        />

        <SorunSheet
          open={sorunSheet}
          onClose={() => { setSorunSheet(false); setSorunTip(null); setSorunNeden(''); }}
          sorunTip={sorunTip}
          setSorunTip={setSorunTip}
          sorunNeden={sorunNeden}
          setSorunNeden={setSorunNeden}
          onGonder={sorunGonder}
          loading={loading}
        />
      </div>
    );
  }

  // ─── Adım 3: Raf Scan ───────────────────────────────────────────
  if (adim === ADIM.RAF) {
    return (
      <div className="p-4 space-y-5 max-w-sm mx-auto pt-2">
        <AdimHeader adim={3} toplam={3} baslik="Rafa Yerleştir" onGeri={() => setAdim(ADIM.PALET)} />

        <div className="bg-slate-900/60 rounded-3xl p-5 border border-slate-800/50 space-y-2 backdrop-blur-md shadow-lg shadow-black/10">
          <InfoRow label="Palet" value={paletBarkod} mono strong />
          {gorev.onerilen_raf_kodu
            ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono highlight />
            : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} highlight />}
          {gorev.zone_adi && <InfoRow label="Zon" value={gorev.zone_adi} />}
        </div>

        <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl px-4 py-3.5 flex items-start gap-3 backdrop-blur-sm">
          <div className="bg-amber-500/20 p-1.5 rounded-lg shrink-0 mt-0.5 border border-amber-500/30">
            <Scan className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-[13px] text-amber-200/90 font-medium leading-snug">Hedef raf barkodunu okutun ya da farklı uygun bir raf seçin.</p>
        </div>

        {/* Kamera Butonu */}
        <button
          onClick={() => { setKameraMod('raf'); setKameraAcik(true); }}
          className="relative w-full overflow-hidden bg-slate-900/50 hover:bg-slate-800/80 border-2 border-dashed border-slate-700 hover:border-amber-500/80 rounded-3xl py-12 flex flex-col items-center gap-3 transition-all duration-300 group active:scale-[0.98] backdrop-blur-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="bg-slate-800/80 p-4 rounded-full group-hover:bg-amber-500/10 transition-colors relative z-10 border border-slate-700/50 group-hover:border-amber-500/30">
            <Camera className="w-10 h-10 text-slate-400 group-hover:text-amber-400 transition-colors" strokeWidth={1.5} />
          </div>
          <span className="text-slate-300 group-hover:text-amber-400 font-black text-sm tracking-widest relative z-10 transition-colors drop-shadow-sm">RAF BARKODUNU OKUT</span>
        </button>

        {/* Manuel Giriş */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <div className="h-px bg-slate-800 flex-1"></div>
            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Manuel Gir</p>
            <div className="h-px bg-slate-800 flex-1"></div>
          </div>
          <div className="flex gap-2 relative">
            <input
              className="flex-1 bg-slate-900/80 border border-slate-700/80 rounded-2xl px-5 py-4 text-slate-100 text-[15px] font-mono tracking-wide placeholder-slate-600 focus:outline-none focus:border-amber-500/80 focus:ring-1 focus:ring-amber-500/50 transition-all shadow-inner"
              placeholder="GNL-A-01-01-01"
              value={manuelRaf}
              onChange={(e) => setManuelRaf(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && yerlestir(manuelRaf)}
            />
            <button
              onClick={() => yerlestir(manuelRaf)}
              disabled={loading}
              className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 active:scale-95 text-slate-950 font-black w-14 rounded-2xl flex items-center justify-center transition-all shadow-[0_4px_15px_rgba(245,158,11,0.2)]"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <CornerDownRight className="w-5 h-5" strokeWidth={2.5} />}
            </button>
          </div>
        </div>

        {/* Sorun Bildir */}
        <div className="pt-2">
          <button
            onClick={() => setSorunSheet(true)}
            className="w-full flex items-center justify-center gap-2 text-[13px] font-bold text-slate-500 hover:text-red-400 py-3 rounded-xl hover:bg-red-500/10 transition-all active:scale-95"
          >
            <AlertCircle className="w-4 h-4" />
            SORUN BİLDİR
          </button>
        </div>

        <ZXingBarcodeScanner
          isOpen={kameraAcik && kameraMod === 'raf'}
          onClose={() => setKameraAcik(false)}
          onScanSuccess={(code) => { setKameraAcik(false); yerlestir(code); }}
        />

        <SorunSheet
          open={sorunSheet}
          onClose={() => { setSorunSheet(false); setSorunTip(null); setSorunNeden(''); }}
          sorunTip={sorunTip}
          setSorunTip={setSorunTip}
          sorunNeden={sorunNeden}
          setSorunNeden={setSorunNeden}
          onGonder={sorunGonder}
          loading={loading}
        />
      </div>
    );
  }

  // ─── Adım 4: Sonuç ───────────────────────────────────────────
  if (adim === ADIM.SONUC && sonuc) {
    const basarili = sonuc.basarili;

    return (
      <div className="p-4 space-y-5 max-w-sm mx-auto pt-6">
        {/* Sonuç Başlığı */}
        <div className={`rounded-3xl p-8 text-center border relative overflow-hidden backdrop-blur-md shadow-2xl ${basarili
            ? 'bg-gradient-to-b from-green-500/10 to-transparent border-green-500/30 shadow-green-500/5'
            : 'bg-gradient-to-b from-red-500/10 to-transparent border-red-500/30 shadow-red-500/5'
          }`}>
          <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 blur-[40px] rounded-full pointer-events-none ${basarili ? 'bg-green-500/20' : 'bg-red-500/20'
            }`} />

          <div className="relative z-10">
            {basarili ? (
              <div className="bg-green-500/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-500/30">
                <CheckCircle className="w-10 h-10 text-green-400" strokeWidth={2.5} />
              </div>
            ) : (
              <div className="bg-red-500/10 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/30">
                <XCircle className="w-10 h-10 text-red-400" strokeWidth={2.5} />
              </div>
            )}
            <h2 className={`text-2xl font-black tracking-tight ${basarili ? 'text-green-300 drop-shadow-sm' : 'text-red-300 drop-shadow-sm'}`}>
              {basarili ? 'Tamamlandı!' : 'Doğrulama Hatası'}
            </h2>
            <p className="text-[13px] text-slate-400 mt-2 font-medium leading-snug max-w-[250px] mx-auto">{sonuc.mesaj}</p>
          </div>
        </div>

        {/* Detaylar */}
        {basarili && (
          <div className="bg-slate-900/60 rounded-3xl p-5 border border-slate-800/50 space-y-3 backdrop-blur-md shadow-lg shadow-black/10">
            {sonuc.palet_no && <InfoRow label="Palet" value={sonuc.palet_no} mono />}
            {sonuc.raf_kod && <InfoRow label="Yerleştirildi" value={sonuc.raf_kod} mono highlight />}
            {sonuc.zon && <InfoRow label="Zon" value={sonuc.zon} />}
            {sonuc.onerilen_raf_kod && sonuc.onerilen_raf_kod !== sonuc.raf_kod && (
              <div className="flex items-center gap-2 pt-3 mt-3 border-t border-white/5">
                <div className="bg-amber-500/20 p-1.5 rounded-lg border border-amber-500/30">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" strokeWidth={2.5} />
                </div>
                <p className="text-[11px] font-bold text-amber-400">Önerilen raftan farklı: <span className="font-mono">{sonuc.onerilen_raf_kod}</span></p>
              </div>
            )}
          </div>
        )}

        {/* Hata Detayları + Alternatifler */}
        {!basarili && (
          <div className="space-y-4">
            <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 backdrop-blur-sm">
              <p className="text-sm font-black text-red-300 mb-1 tracking-wide">{sonuc.hata_tipi}</p>
              <p className="text-[13px] text-slate-300">{sonuc.mesaj}</p>
            </div>

            {sonuc.alternatifler?.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 pb-1">
                  <div className="h-px bg-slate-800 flex-1"></div>
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest font-black">Alternatif Raflar</p>
                  <div className="h-px bg-slate-800 flex-1"></div>
                </div>

                {sonuc.hata_neden && (
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl px-3.5 py-2.5 flex items-start gap-2.5 shadow-inner">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <p className="text-[12px] font-medium text-amber-300">{sonuc.hata_neden}</p>
                  </div>
                )}
                <div className="space-y-2">
                  {sonuc.alternatifler.map((alt) => (
                    <button
                      key={alt.raf_id}
                      onClick={() => {
                        setOverrideRafSec(alt);
                        setRafBarkod(alt.raf_kod);
                        setOverrideModal(true);
                      }}
                      className="w-full bg-slate-900/80 border border-slate-700/80 rounded-2xl p-4 text-left hover:border-amber-500/50 hover:bg-slate-800 active:scale-[0.98] transition-all relative overflow-hidden group shadow-lg shadow-black/10"
                    >
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-transparent group-hover:bg-amber-500 transition-colors" />
                      <div className="flex justify-between items-center">
                        <p className="font-mono text-[15px] font-bold text-slate-100 group-hover:text-amber-400 transition-colors pl-1">{alt.raf_kod}</p>
                        <div className="bg-white/5 p-1 rounded-full group-hover:bg-white/10 transition-colors">
                          <ArrowRight className="w-4 h-4 text-slate-400" />
                        </div>
                      </div>
                      <div className="flex gap-4 text-[11px] font-medium text-slate-500 mt-2 pl-1 bg-slate-950/30 py-1.5 px-2 rounded-lg inline-flex">
                        <span>{alt.bos_slot} boş slot</span>
                        <div className="w-px bg-slate-700"></div>
                        <span>Skor: {alt.skor}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {sonuc.override_gerekli && overrideYetkisiVar && (
              <div className="pt-2">
                <button
                  onClick={() => setOverrideModal(true)}
                  className="relative w-full overflow-hidden bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 text-orange-400 font-bold rounded-2xl py-4 hover:border-orange-500/50 active:scale-[0.98] transition-all flex items-center justify-center gap-2 backdrop-blur-md"
                >
                  <ShieldAlert className="w-5 h-5 relative z-10" />
                  <span className="relative z-10 tracking-wide text-sm font-black">SÜPERVİZÖR OVERRIDE</span>
                </button>
              </div>
            )}
            {sonuc.override_gerekli && !overrideYetkisiVar && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-center mt-4">
                <div className="bg-slate-800 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 shadow-inner">
                  <ShieldAlert className="w-6 h-6 text-slate-500" />
                </div>
                <p className="text-sm font-bold text-slate-300">Bu işlem için yetkiniz yok.</p>
                <p className="text-[12px] text-slate-500 mt-1 font-medium">Süpervizör veya admin çağırın.</p>
              </div>
            )}
          </div>
        )}

        {/* Sonraki Adım Butonları */}
        <div className="flex gap-2 pt-6">
          <button
            onClick={() => navigate('/terminal/gorevler')}
            className="flex-1 bg-slate-800/80 hover:bg-slate-700 active:scale-95 border border-transparent hover:border-slate-600 text-slate-300 font-bold text-[13px] rounded-2xl py-4 transition-all"
          >
            Listeye Dön
          </button>
          <button
            onClick={sifirla}
            className="flex-[2] relative bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 font-black rounded-2xl py-4 flex items-center justify-center gap-2 transition-all shadow-[0_5px_15px_-3px_rgba(245,158,11,0.3)] overflow-hidden"
          >
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
            <span className="drop-shadow-sm">SONRAKİ GÖREV</span>
            <ArrowRight className="w-5 h-5 drop-shadow-sm" strokeWidth={2.5} />
          </button>
        </div>

        {/* Override Modal */}
        {overrideModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 transition-all">
            <div className="bg-slate-900 border-t sm:border border-slate-800 sm:rounded-3xl rounded-t-3xl w-full max-w-sm p-6 space-y-5 shadow-2xl shadow-black animate-in slide-in-from-bottom-4 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-200 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-orange-500 to-amber-500"></div>

              <h3 className="font-black text-xl text-white flex items-center gap-2 tracking-tight">
                <ShieldAlert className="w-6 h-6 text-orange-500" strokeWidth={2.5} />
                Override
              </h3>

              {overrideRafSec ? (
                <div className="bg-slate-950/50 border border-orange-500/20 rounded-2xl p-4 space-y-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 bottom-0 w-16 bg-gradient-to-l from-orange-500/5 to-transparent"></div>
                  <div className="flex items-center justify-between relative z-10">
                    <span className="text-[11px] uppercase tracking-widest text-slate-500 font-bold">Seçilen Raf</span>
                    <span className="text-[15px] font-mono font-black text-orange-400">{overrideRafSec.kod || overrideRafSec.raf_kod}</span>
                  </div>
                  <div className="flex gap-3 text-[11px] font-medium text-slate-500 bg-slate-900/50 py-1.5 px-2 rounded-lg inline-flex relative z-10">
                    {overrideRafSec.bos_slot != null && <span>{overrideRafSec.bos_slot} boş slot</span>}
                    <div className="w-px bg-slate-700"></div>
                    {overrideRafSec.skor != null && <span>Skor: {overrideRafSec.skor}</span>}
                  </div>
                </div>
              ) : (
                <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl px-4 py-3 flex items-center gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-orange-400 shrink-0" />
                  <p className="text-[13px] text-orange-300 font-medium">Listeden alternatif bir raf seçin.</p>
                </div>
              )}

              <div className="space-y-1.5">
                <p className="text-[12px] text-slate-400 font-medium">Kural ihlaliyle yerleştirme (Gerekçe Zorunlu)</p>
                <textarea
                  className="w-full bg-slate-950/50 border border-slate-700/80 rounded-2xl px-4 py-3 text-slate-100 text-[13px] placeholder-slate-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/50 transition-all resize-none shadow-inner"
                  rows={3}
                  placeholder="Override gerekçesini net bir şekilde yazın..."
                  value={overrideNeden}
                  onChange={(e) => setOverrideNeden(e.target.value)}
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => setOverrideModal(false)}
                  className="flex-1 bg-slate-800 text-slate-300 hover:text-white font-bold rounded-2xl py-3.5 transition-colors"
                >
                  İptal
                </button>
                <button
                  onClick={overrideYap}
                  disabled={loading || !overrideRafSec || !overrideNeden.trim()}
                  className="flex-[2] bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-2xl py-3.5 transition-all active:scale-[0.98] relative overflow-hidden"
                >
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin mx-auto" /> : 'Onayla ve Tamamla'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

// ─── Yardımcı Bileşenler ───────────────────────────────────────────

function AdimHeader({ adim, toplam, baslik, onGeri }) {
  return (
    <div className="flex items-center gap-3 bg-slate-900/60 p-2 pr-4 rounded-3xl border border-white/5 backdrop-blur-md shadow-sm">
      <button onClick={onGeri} className="p-2.5 rounded-full text-slate-400 bg-slate-800/50 hover:text-white hover:bg-slate-700 transition-all active:scale-95 border border-white/5">
        <ChevronLeft className="w-5 h-5" />
      </button>
      <div className="flex-1 pt-0.5">
        <p className="text-[10px] uppercase tracking-widest text-amber-500/80 font-bold mb-0.5">Adım {adim}/{toplam}</p>
        <h1 className="text-lg font-black text-white tracking-tight leading-none">{baslik}</h1>
      </div>
      <div className="flex gap-1">
        {Array.from({ length: toplam }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${i < adim ? 'bg-amber-400 w-5 shadow-[0_0_8px_rgba(245,158,11,0.6)]' : 'bg-slate-700/50 w-2'
              }`}
          />
        ))}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono, strong, highlight }) {
  return (
    <div className={`flex items-center justify-between gap-4 py-1 flex-wrap ${highlight ? 'bg-amber-500/10 px-3 py-2 -mx-3 rounded-xl border border-amber-500/20' : ''}`}>
      <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold shrink-0">{label}</span>
      <span className={`text-[14px] ${strong ? 'font-black text-white' : highlight ? 'font-bold text-amber-400' : 'font-semibold text-slate-300'} truncate text-right ${mono ? 'font-mono tracking-wide' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function OncelikBadge({ oncelik }) {
  if (oncelik === 1) return (
    <span className="text-[10px] uppercase tracking-wider font-black bg-red-500/20 border border-red-500/30 text-red-400 px-3 py-1.5 rounded-lg flex items-center gap-1 shadow-inner">
      <AlertCircle className="w-3 h-3" /> ACİL
    </span>
  );
  if (oncelik === 2) return (
    <span className="text-[10px] uppercase tracking-wider font-bold bg-orange-500/20 border border-orange-500/30 text-orange-400 px-3 py-1.5 rounded-lg flex items-center gap-1">
      Yüksek
    </span>
  );
  return null;
}

function SorunSheet({ open, onClose, sorunTip, setSorunTip, sorunNeden, setSorunNeden, onGonder, loading }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 transition-all">
      <div
        className="bg-slate-900 border-t sm:border border-slate-800 sm:rounded-3xl rounded-t-3xl w-full max-w-sm p-6 space-y-5 shadow-2xl shadow-black animate-in slide-in-from-bottom-4 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-200 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-red-500/50"></div>
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-12 h-1.5 bg-slate-800 rounded-full sm:hidden"></div>

        <h3 className="font-black text-xl text-white flex items-center gap-2 tracking-tight mt-2 sm:mt-0">
          <div className="bg-red-500/20 p-1.5 rounded-lg border border-red-500/30">
            <AlertCircle className="w-5 h-5 text-red-500" />
          </div>
          Sorun Bildir
        </h3>

        {/* Sorun tipi seçimi */}
        <div className="space-y-3">
          <button
            onClick={() => setSorunTip('karantina')}
            className={`w-full relative overflow-hidden rounded-2xl p-4 border text-left transition-all active:scale-[0.98] ${sorunTip === 'karantina'
                ? 'bg-red-500/10 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)] ring-1 ring-red-500/30'
                : 'bg-slate-950/50 border-slate-800 hover:border-red-500/30 hover:bg-slate-900/80 hover:shadow-lg'
              }`}
          >
            {sorunTip === 'karantina' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500" />}
            <p className={`font-black text-sm flex items-center gap-2 ${sorunTip === 'karantina' ? 'text-red-400' : 'text-slate-300'}`}>
              <ShieldAlert className="w-4 h-4" />
              Karantinaya Al
            </p>
            <p className="text-[11px] font-medium text-slate-500 mt-1.5 leading-snug">Hasarlı, şüpheli veya uygunsuz ürün. Palet sistemde karantina zonuna çekilir.</p>
          </button>
          <button
            onClick={() => setSorunTip('iptal')}
            className={`w-full relative overflow-hidden rounded-2xl p-4 border text-left transition-all active:scale-[0.98] ${sorunTip === 'iptal'
                ? 'bg-amber-500/10 border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/30'
                : 'bg-slate-950/50 border-slate-800 hover:border-amber-500/30 hover:bg-slate-900/80 hover:shadow-lg'
              }`}
          >
            {sorunTip === 'iptal' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500" />}
            <p className={`font-black text-sm flex items-center gap-2 ${sorunTip === 'iptal' ? 'text-amber-400' : 'text-slate-300'}`}>
              <XCircle className="w-4 h-4" />
              Görevi İptal Et
            </p>
            <p className="text-[11px] font-medium text-slate-500 mt-1.5 leading-snug">Palet bulunamadı, sistemde hata vb. Görev havuza iade edilir.</p>
          </button>
        </div>

        {sorunTip && (
          <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <textarea
              className="w-full bg-slate-950/50 border border-slate-700/80 rounded-2xl px-4 py-3 text-slate-100 text-[13px] placeholder-slate-600 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/50 transition-all resize-none shadow-inner"
              rows={3}
              placeholder="Süpervizör için sorunu kısaca açıklayın..."
              value={sorunNeden}
              onChange={(e) => setSorunNeden(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="flex-1 bg-slate-800 text-slate-300 hover:text-white font-bold rounded-2xl py-3.5 transition-colors"
              >
                Vazgeç
              </button>
              <button
                onClick={onGonder}
                disabled={loading || !sorunNeden.trim()}
                className={`flex-[2] disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-2xl py-3.5 transition-all active:scale-[0.98] relative overflow-hidden ${sorunTip === 'karantina'
                    ? 'bg-gradient-to-br from-red-500 to-red-600 shadow-[0_5px_15px_-3px_rgba(239,68,68,0.3)]'
                    : 'bg-gradient-to-br from-amber-500 to-amber-600 shadow-[0_5px_15px_-3px_rgba(245,158,11,0.3)]'
                  }`}
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
                {loading ? <RefreshCw className="w-5 h-5 animate-spin mx-auto" />
                  : <span className="drop-shadow-sm">{sorunTip === 'karantina' ? 'Karantinaya Al' : 'İptal İşlemini Onayla'}</span>}
              </button>
            </div>
          </div>
        )}

        {!sorunTip && (
          <div className="pt-2">
            <button onClick={onClose} className="w-full bg-slate-800/80 hover:bg-slate-700 active:scale-[0.98] text-slate-300 font-bold rounded-2xl py-3.5 transition-all">
              İptal Et ve Geri Dön
            </button>
          </div>
        )}
      </div>
    </div>
  );
}