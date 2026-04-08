/**
 * YerlestirmePage — 4 adımlı scan-to-verify yerleştirme akışı.
 *
 * Adım 1: Sıradaki Görevi Al / Görev Detayı (operasyonel bilgilerle)
 * Adım 2: Paleti Tara (gerçek barkod doğrulaması)
 * Adım 3: Rafa Yerleştir (raf kodu gösterir, ID değil)
 * Adım 4: Sonuç (başarı veya hata + alternatifler)
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Package, Camera, CheckCircle, XCircle, ArrowRight,
  RefreshCw, ChevronLeft, Scan, CornerDownRight, AlertTriangle,
  AlertCircle, MapPin,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../../hooks/useAsync';
import { useTerminalDepo } from '../../hooks/useTerminalDepo';
import ZXingBarcodeScanner from '../../components/common/ZXingBarcodeScanner';
import {
  siradakiGorevisiniAl,
  goreviBaslat,
  goreviBirak,
  goreviIptal,
  terminalYerlestir,
  getBekleyenGorevOzet,
  getDepolar,
  goreviOverride,
  karantinayaAl,
} from '../../services/api';

const ADIM = { GOREV: 1, PALET: 2, RAF: 3, SONUC: 4 };

export default function YerlestirmePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, run } = useAsync();
  const { depoId, setDepoId } = useTerminalDepo();

  const [adim, setAdim] = useState(ADIM.GOREV);
  const [gorev, setGorev] = useState(location.state?.gorev || null);
  const [bekleyenSayisi, setBekleyenSayisi] = useState(null);
  const [paletBarkod, setPaletBarkod] = useState('');
  const [rafBarkod, setRafBarkod] = useState('');
  const [sonuc, setSonuc] = useState(null);
  const [kameraAcik, setKameraAcik] = useState(false);
  const [kameraMod, setKameraMod] = useState('palet'); // 'palet' | 'raf'
  const [manuelPalet, setManuelPalet] = useState('');
  const [manuelRaf, setManuelRaf] = useState('');
  const [depolar, setDepolar] = useState([]);
  const [overrideModal, setOverrideModal] = useState(false);
  const [overrideNeden, setOverrideNeden] = useState('');
  const [overrideRafId, setOverrideRafId] = useState(null);
  const [sorunSheet, setSorunSheet] = useState(false);
  const [sorunTip, setSorunTip] = useState(null); // 'karantina' | 'iptal'
  const [sorunNeden, setSorunNeden] = useState('');

  // Depo seçimi yoksa depolar listesini yükle
  useEffect(() => {
    if (!depoId) {
      getDepolar().then((r) => setDepolar(r.data)).catch(() => {});
    }
  }, [depoId]);

  // Önceki sayfadan gorev gelmediyse bekleyen sayısını yükle
  const bekleyenYukle = useCallback(async () => {
    try {
      const res = await getBekleyenGorevOzet();
      setBekleyenSayisi(res.data.toplam_bekleyen);
    } catch { /* sessiz */ }
  }, []);

  useEffect(() => {
    if (!gorev) void bekleyenYukle();
  }, [gorev, bekleyenYukle]);

  // Görev al
  const goreviAl = async () => {
    await run(async () => {
      const res = await siradakiGorevisiniAl(depoId);
      if (res.data) {
        setGorev(res.data);
      } else {
        toast('Havuzda bekleyen görev yok.', { icon: '📭' });
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
        depo_id: depoId,
      });
      setSonuc(res.data);
      setAdim(ADIM.SONUC);
    });
  };

  // Override
  const overrideYap = async () => {
    if (!overrideRafId) {
      toast.error('Lütfen önce bir alternatif raf seçin.');
      return;
    }
    if (!overrideNeden.trim()) {
      toast.error('Override gerekçesi zorunludur.');
      return;
    }
    await run(async () => {
      const res = await goreviOverride(gorev.id, {
        gerceklesen_raf_id: overrideRafId,
        neden: overrideNeden,
      });
      setSonuc({ basarili: true, durum: 'TAMAMLANDI', mesaj: 'Override ile yerleştirildi.', ...res.data });
      setAdim(ADIM.SONUC);
      setOverrideModal(false);
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
        toast.success('Palet karantinaya alındı.');
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
    setAdim(ADIM.GOREV);
    void bekleyenYukle();
  };

  // ─── Depo Seçim Ekranı ───────────────────────────────────────
  if (!depoId) {
    return (
      <div className="p-4 space-y-4 max-w-sm mx-auto pt-8">
        <div className="text-center mb-6">
          <Package className="w-12 h-12 text-amber-400 mx-auto mb-3" />
          <h2 className="text-xl font-black text-slate-100">Depo Seç</h2>
          <p className="text-sm text-slate-500 mt-1">Terminal oturumu için çalışacağınız depoyu seçin.</p>
        </div>
        {depolar.length === 0 ? (
          <p className="text-center text-slate-500">Depolar yükleniyor...</p>
        ) : (
          <div className="space-y-3">
            {depolar.map((d) => (
              <button
                key={d.id}
                onClick={() => setDepoId(d.id)}
                className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-2xl p-5 text-left transition-colors"
              >
                <p className="font-bold text-slate-100">{d.isim}</p>
                {d.adres && <p className="text-sm text-slate-500 mt-0.5">{d.adres}</p>}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Adım 1: Görev ───────────────────────────────────────────
  if (adim === ADIM.GOREV) {
    return (
      <div className="p-4 space-y-4 max-w-sm mx-auto pt-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-black text-slate-100">Yerleştirme</h1>
          <button
            onClick={() => setDepoId(null)}
            className="text-xs text-slate-500 hover:text-amber-400 transition-colors"
          >
            Depo Değiştir
          </button>
        </div>

        {bekleyenSayisi !== null && !gorev && (
          <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700 text-center">
            <p className="text-3xl font-black text-amber-400">{bekleyenSayisi}</p>
            <p className="text-sm text-slate-500 mt-0.5">Havuzda Bekleyen Görev</p>
          </div>
        )}

        {!gorev ? (
          <button
            onClick={goreviAl}
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-400 active:bg-amber-600 disabled:opacity-50 text-slate-900 font-black text-xl rounded-2xl py-6 flex items-center justify-center gap-3 transition-colors shadow-lg shadow-amber-500/20"
          >
            {loading ? <RefreshCw className="w-7 h-7 animate-spin" /> : (
              <>
                <span>SIRADAKI GÖREVİ AL</span>
                <ArrowRight className="w-7 h-7" />
              </>
            )}
          </button>
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-amber-400" />
                <span className="text-xs uppercase tracking-widest text-amber-400 font-bold">Görev #{gorev.id}</span>
              </div>
              <OncelikBadge oncelik={gorev.oncelik} />
            </div>

            {/* Operasyonel bilgiler */}
            <div className="space-y-2">
              {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} />}
              {gorev.palet_barkodu && <InfoRow label="Palet" value={gorev.palet_barkodu} mono />}
              {gorev.lot_no && <InfoRow label="Lot No" value={gorev.lot_no} mono />}
              {gorev.miktar != null && <InfoRow label="Miktar (koli)" value={gorev.miktar} />}
              <div className="border-t border-slate-700 my-1" />
              {gorev.onerilen_raf_kodu
                ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono />
                : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} />}
              {gorev.zone_adi && (
                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs text-slate-500 font-semibold shrink-0">Zon</span>
                  <span className="flex items-center gap-1 text-sm font-bold text-slate-200">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {gorev.zone_adi}
                  </span>
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={goreviBirakAction}
                disabled={loading}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 font-bold rounded-xl py-4 transition-colors"
              >
                BIRAK
              </button>
              <button
                onClick={goreviBaslatAction}
                disabled={loading}
                className="flex-[2] bg-amber-500 hover:bg-amber-400 text-slate-900 font-black rounded-xl py-4 flex items-center justify-center gap-2 transition-colors shadow-md shadow-amber-500/20"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (
                  <>{gorev.durum === 'DevamEdiyor' ? 'DEVAM ET' : 'BAŞLAT'} <ArrowRight className="w-5 h-5" /></>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ─── Adım 2: Palet Scan ───────────────────────────────────────
  if (adim === ADIM.PALET) {
    return (
      <div className="p-4 space-y-4 max-w-sm mx-auto pt-4">
        <AdimHeader adim={2} toplam={3} baslik="Paleti Tara" onGeri={() => setAdim(ADIM.GOREV)} />

        <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700 space-y-1.5">
          {gorev.urun_adi && <InfoRow label="Ürün" value={gorev.urun_adi} />}
          <InfoRow label="Beklenen Palet" value={gorev.palet_barkodu || `#${gorev.palet_id}`} mono />
          {gorev.lot_no && <InfoRow label="Lot" value={gorev.lot_no} mono />}
          {gorev.miktar != null && <InfoRow label="Miktar" value={`${gorev.miktar} koli`} />}
        </div>

        {/* Kamera Butonu */}
        <button
          onClick={() => { setKameraMod('palet'); setKameraAcik(true); }}
          className="w-full bg-slate-800 hover:bg-slate-700 border-2 border-dashed border-slate-600 hover:border-amber-500 rounded-2xl py-10 flex flex-col items-center gap-3 transition-colors group"
        >
          <Camera className="w-12 h-12 text-slate-500 group-hover:text-amber-400 transition-colors" />
          <span className="text-slate-400 group-hover:text-amber-400 font-bold transition-colors">KAMERA İLE OKUT</span>
        </button>

        {/* Manuel Giriş */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 text-center">— veya manuel giriş —</p>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-4 py-4 text-slate-100 text-base font-mono placeholder-slate-600 focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="PLT-2026-XXXXX"
              value={manuelPalet}
              onChange={(e) => setManuelPalet(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && paletDogrula(manuelPalet)}
            />
            <button
              onClick={() => paletDogrula(manuelPalet)}
              className="bg-amber-500 hover:bg-amber-400 text-slate-900 font-black px-5 rounded-xl transition-colors"
            >
              <CornerDownRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Sorun Bildir */}
        <button
          onClick={() => setSorunSheet(true)}
          className="w-full flex items-center justify-center gap-2 text-sm text-slate-500 hover:text-red-400 py-2 transition-colors"
        >
          <AlertCircle className="w-4 h-4" />
          Sorun Bildir
        </button>

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

  // ─── Adım 3: Raf Scan ─────────────────────────────────────────
  if (adim === ADIM.RAF) {
    return (
      <div className="p-4 space-y-4 max-w-sm mx-auto pt-4">
        <AdimHeader adim={3} toplam={3} baslik="Rafa Yerleştir" onGeri={() => setAdim(ADIM.PALET)} />

        <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700 space-y-1.5">
          <InfoRow label="Palet" value={paletBarkod} mono />
          {gorev.onerilen_raf_kodu
            ? <InfoRow label="Hedef Raf" value={gorev.onerilen_raf_kodu} mono />
            : <InfoRow label="Hedef Raf #" value={gorev.onerilen_raf_id} />}
          {gorev.zone_adi && <InfoRow label="Zon" value={gorev.zone_adi} />}
        </div>

        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3 flex items-start gap-2">
          <Scan className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-300">Hedef raf barkodunu okutun ya da farklı uygun bir raf seçin.</p>
        </div>

        {/* Kamera Butonu */}
        <button
          onClick={() => { setKameraMod('raf'); setKameraAcik(true); }}
          className="w-full bg-slate-800 hover:bg-slate-700 border-2 border-dashed border-slate-600 hover:border-amber-500 rounded-2xl py-10 flex flex-col items-center gap-3 transition-colors group"
        >
          <Camera className="w-12 h-12 text-slate-500 group-hover:text-amber-400 transition-colors" />
          <span className="text-slate-400 group-hover:text-amber-400 font-bold transition-colors">RAF BARKODUNU OKUT</span>
        </button>

        {/* Manuel Giriş */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 text-center">— veya manuel giriş —</p>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-4 py-4 text-slate-100 text-base font-mono placeholder-slate-600 focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="GNL-A-01-01-01"
              value={manuelRaf}
              onChange={(e) => setManuelRaf(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && yerlestir(manuelRaf)}
            />
            <button
              onClick={() => yerlestir(manuelRaf)}
              disabled={loading}
              className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-900 font-black px-5 rounded-xl transition-colors"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <CornerDownRight className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Sorun Bildir */}
        <button
          onClick={() => setSorunSheet(true)}
          className="w-full flex items-center justify-center gap-2 text-sm text-slate-500 hover:text-red-400 py-2 transition-colors"
        >
          <AlertCircle className="w-4 h-4" />
          Sorun Bildir
        </button>

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
      <div className="p-4 space-y-4 max-w-sm mx-auto pt-4">
        {/* Sonuç Başlığı */}
        <div className={`rounded-2xl p-6 text-center border ${
          basarili
            ? 'bg-green-500/10 border-green-500/30'
            : 'bg-red-500/10 border-red-500/30'
        }`}>
          {basarili ? (
            <CheckCircle className="w-14 h-14 text-green-400 mx-auto mb-3" />
          ) : (
            <XCircle className="w-14 h-14 text-red-400 mx-auto mb-3" />
          )}
          <h2 className={`text-xl font-black ${basarili ? 'text-green-300' : 'text-red-300'}`}>
            {basarili ? 'Tamamlandı!' : 'Doğrulama Hatası'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">{sonuc.mesaj}</p>
        </div>

        {/* Detaylar */}
        {basarili && (
          <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700 space-y-2">
            {sonuc.palet_no && <InfoRow label="Palet" value={sonuc.palet_no} mono />}
            {sonuc.raf_kod && <InfoRow label="Yerleştirildi" value={sonuc.raf_kod} mono />}
            {sonuc.zon && <InfoRow label="Zon" value={sonuc.zon} />}
            {sonuc.onerilen_raf_kod && sonuc.onerilen_raf_kod !== sonuc.raf_kod && (
              <div className="flex items-center gap-2 pt-1">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <p className="text-xs text-amber-400">Önerilen raftan farklı: {sonuc.onerilen_raf_kod}</p>
              </div>
            )}
          </div>
        )}

        {/* Hata Detayları + Alternatifler */}
        {!basarili && (
          <div className="space-y-3">
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              <p className="text-sm font-bold text-red-300 mb-1">{sonuc.hata_tipi}</p>
              <p className="text-xs text-slate-400">{sonuc.mesaj}</p>
            </div>

            {sonuc.alternatifler?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Alternatif Raflar</p>
                {sonuc.alternatifler.map((alt) => (
                  <button
                    key={alt.raf_id}
                    onClick={() => {
                      setOverrideRafId(alt.raf_id);
                      setRafBarkod(alt.raf_kod);
                      setOverrideModal(true);
                    }}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl p-4 text-left hover:border-amber-500/50 transition-colors"
                  >
                    <p className="font-mono text-sm font-bold text-slate-200">{alt.raf_kod}</p>
                    <div className="flex gap-4 text-xs text-slate-500 mt-1">
                      <span>{alt.bos_slot} boş slot</span>
                      <span>Skor: {alt.skor}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {sonuc.override_gerekli && (
              <button
                onClick={() => setOverrideModal(true)}
                className="w-full bg-orange-500/20 border border-orange-500/30 text-orange-300 font-bold rounded-xl py-4 hover:bg-orange-500/30 transition-colors"
              >
                Süpervizör Override
              </button>
            )}
          </div>
        )}

        {/* Sonraki Adım Butonları */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => navigate('/terminal/gorevler')}
            className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 font-bold rounded-xl py-4 transition-colors"
          >
            Görev Listesi
          </button>
          <button
            onClick={sifirla}
            className="flex-[2] bg-amber-500 hover:bg-amber-400 text-slate-900 font-black rounded-xl py-4 flex items-center justify-center gap-2 transition-colors"
          >
            <span>Sonraki Görev</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Override Modal */}
        {overrideModal && (
          <div className="fixed inset-0 bg-black/70 z-50 flex items-end p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full p-6 space-y-4">
              <h3 className="font-black text-slate-100 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                Süpervizör Override
              </h3>

              {overrideRafId ? (
                <div className="bg-slate-800 border border-slate-600 rounded-xl px-4 py-2.5 flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-semibold">Hedef Raf</span>
                  <span className="text-sm font-mono font-bold text-slate-200">{rafBarkod || `#${overrideRafId}`}</span>
                </div>
              ) : (
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl px-4 py-2.5 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-400 shrink-0" />
                  <p className="text-xs text-orange-300">Yukarıdaki listeden alternatif bir raf seçin.</p>
                </div>
              )}

              <p className="text-sm text-slate-400">Kural ihlaliyle yerleştirme — gerekçe zorunlu.</p>
              <textarea
                className="w-full bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-slate-100 text-sm placeholder-slate-600 focus:outline-none focus:border-orange-500 transition-colors resize-none"
                rows={3}
                placeholder="Override gerekçesini yazın..."
                value={overrideNeden}
                onChange={(e) => setOverrideNeden(e.target.value)}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setOverrideModal(false)}
                  className="flex-1 bg-slate-700 text-slate-300 font-bold rounded-xl py-3"
                >
                  İptal
                </button>
                <button
                  onClick={overrideYap}
                  disabled={loading || !overrideRafId}
                  className="flex-[2] bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-xl py-3 transition-colors"
                >
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin mx-auto" /> : 'Onayla'}
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

// ─── Yardımcı Bileşenler ──────────────────────────────────────

function AdimHeader({ adim, toplam, baslik, onGeri }) {
  return (
    <div className="flex items-center gap-3">
      <button onClick={onGeri} className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors">
        <ChevronLeft className="w-6 h-6" />
      </button>
      <div className="flex-1">
        <p className="text-xs text-slate-500 font-semibold">Adım {adim}/{toplam}</p>
        <h1 className="text-lg font-black text-slate-100">{baslik}</h1>
      </div>
      <div className="flex gap-1.5">
        {Array.from({ length: toplam }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all ${
              i < adim ? 'bg-amber-400 w-6' : 'bg-slate-700 w-3'
            }`}
          />
        ))}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs text-slate-500 font-semibold shrink-0">{label}</span>
      <span className={`text-sm font-bold text-slate-200 truncate text-right ${mono ? 'font-mono' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function OncelikBadge({ oncelik }) {
  if (oncelik === 1) return <span className="text-xs font-bold bg-red-500/20 text-red-300 px-2.5 py-1 rounded-full">ACİL</span>;
  if (oncelik === 2) return <span className="text-xs font-bold bg-orange-500/20 text-orange-300 px-2.5 py-1 rounded-full">Yüksek</span>;
  return null;
}

function SorunSheet({ open, onClose, sorunTip, setSorunTip, sorunNeden, setSorunNeden, onGonder, loading }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-end p-4" onClick={onClose}>
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl w-full p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-black text-slate-100 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-400" />
          Sorun Bildir
        </h3>

        {/* Sorun tipi seçimi */}
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setSorunTip('karantina')}
            className={`rounded-xl p-4 border text-left transition-colors ${
              sorunTip === 'karantina'
                ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
            }`}
          >
            <p className="font-bold text-sm">Karantinaya Al</p>
            <p className="text-xs mt-0.5 opacity-75">Hasarlı / şüpheli ürün</p>
          </button>
          <button
            onClick={() => setSorunTip('iptal')}
            className={`rounded-xl p-4 border text-left transition-colors ${
              sorunTip === 'iptal'
                ? 'bg-red-500/20 border-red-500/50 text-red-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
            }`}
          >
            <p className="font-bold text-sm">Görevi İptal Et</p>
            <p className="text-xs mt-0.5 opacity-75">Palet bulunamadı vb.</p>
          </button>
        </div>

        {sorunTip && (
          <>
            <textarea
              className="w-full bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-slate-100 text-sm placeholder-slate-600 focus:outline-none focus:border-red-500 transition-colors resize-none"
              rows={3}
              placeholder="Sorunu kısaca açıklayın..."
              value={sorunNeden}
              onChange={(e) => setSorunNeden(e.target.value)}
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 bg-slate-700 text-slate-300 font-bold rounded-xl py-3"
              >
                Vazgeç
              </button>
              <button
                onClick={onGonder}
                disabled={loading || !sorunNeden.trim()}
                className="flex-[2] bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-xl py-3 transition-colors"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin mx-auto" /> : 'Gönder'}
              </button>
            </div>
          </>
        )}

        {!sorunTip && (
          <button onClick={onClose} className="w-full bg-slate-700 text-slate-300 font-bold rounded-xl py-3">
            Vazgeç
          </button>
        )}
      </div>
    </div>
  );
}
