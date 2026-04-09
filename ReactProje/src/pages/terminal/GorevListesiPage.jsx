/**
 * GorevListesiPage — Operatörün bekleyen yerleştirme görevleri listesi.
 * Industrial Dark UI — yüksek kontrast, büyük dokunmatik hedefler.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, RefreshCw, ArrowRight, AlertCircle, Inbox, Package } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../../hooks/useAsync';
import { hataMetni } from '../../utils/hata';
import { getYerlestirmeGorevleri, siradakiGorevisiniAl, getBekleyenGorevOzet } from '../../services/api';

const DURUM_RENK = {
  Bekliyor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  Atandi: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  DevamEdiyor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  Tamamlandi: 'bg-green-500/20 text-green-300 border-green-500/30',
  IptalEdildi: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const TIP_RENK = {
  Yerlestirme: 'text-amber-400',
  Transfer: 'text-purple-400',
  BelirsizKonum: 'text-red-400',
};

const ONCELIK_ETİKET = { 1: 'ACİL', 2: 'Yüksek', 3: 'Orta', 4: 'Normal', 5: 'Normal' };
const ONCELIK_RENK = {
  1: 'bg-red-500/30 text-red-300',
  2: 'bg-orange-500/20 text-orange-300',
  3: 'bg-yellow-500/20 text-yellow-300',
  4: 'bg-slate-600 text-slate-400',
  5: 'bg-slate-600 text-slate-400',
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
    <div className="p-4 space-y-6 max-w-lg mx-auto">
      {/* Başlık + Yenile */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-3">
          <div className="bg-amber-400/10 p-2 rounded-xl">
            <ClipboardList className="w-6 h-6 text-amber-400" />
          </div>
          <h1 className="text-xl font-black text-white tracking-tight">Görev Listesi</h1>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="p-2.5 rounded-xl text-slate-400 bg-slate-800/50 hover:text-amber-400 hover:bg-slate-800 active:scale-90 transition-all disabled:opacity-40 border border-white/5"
          aria-label="Yenile"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
        </button>
      </div>

      {/* Bekleyen Özet Kartı — Modern Grid */}
      {ozet && (
        <div className="grid grid-cols-4 gap-3">
          <div className="col-span-2 bg-gradient-to-br from-amber-500/20 to-amber-500/5 border border-amber-500/20 rounded-2xl p-4 flex flex-col justify-center relative overflow-hidden backdrop-blur-sm">
            <div className="absolute -right-4 -top-4 w-16 h-16 bg-amber-500/20 rounded-full blur-xl"></div>
            <p className="text-3xl font-black text-amber-400">{ozet.toplam_bekleyen}</p>
            <p className="text-xs text-amber-200/60 font-semibold mt-1">BEKLEYEN</p>
          </div>
          <div className="col-span-2 grid grid-rows-2 gap-3">
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl flex items-center justify-between px-4 py-2 backdrop-blur-sm shadow-inner">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Acil</span>
              <span className="text-lg font-black text-red-400">{ozet.acil}</span>
            </div>
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl flex items-center justify-between px-4 py-2 backdrop-blur-sm shadow-inner">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Normal</span>
              <span className="text-lg font-black text-slate-300">{(ozet.normal ?? 0) + (ozet.yuksek_oncelikli ?? 0)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Sıradaki Görevi Al Butonu — Glowing & Premium */}
      <div className="relative">
        <div className="absolute -inset-[3px] bg-gradient-to-r from-amber-600 via-amber-400 to-amber-600 rounded-3xl blur-[14px] opacity-20 animate-pulse"></div>
        <button
          onClick={siradakiGoreviAl}
          disabled={aliyor || loading}
          className="relative w-full bg-gradient-to-br from-amber-400 to-amber-500 border border-amber-300/50 hover:from-amber-300 hover:to-amber-400 active:scale-[0.98] disabled:opacity-50 text-slate-950 font-black text-[17px] rounded-2xl py-4 flex items-center justify-center gap-3 transition-all shadow-[0_0_30px_rgba(245,158,11,0.2)] overflow-hidden"
        >
          {/* İç parlama efekti */}
          <div className="absolute top-0 left-0 w-full h-1/2 bg-white/20 rounded-t-2xl pointer-events-none"></div>
          {aliyor ? (
            <RefreshCw className="w-6 h-6 animate-spin text-slate-900" />
          ) : (
            <>
              <span className="tracking-wide relative z-10 drop-shadow-sm">SIRADAKİ GÖREVİ AL</span>
              <ArrowRight className="w-6 h-6 relative z-10 drop-shadow-sm" strokeWidth={2.5} />
            </>
          )}
        </button>
      </div>

      {/* Filtre Tabs — Segmented Control Style */}
      <div className="flex gap-2 p-1.5 bg-slate-900/80 border border-slate-800 rounded-2xl overflow-x-auto custom-scrollbar backdrop-blur-md">
        {[
          { key: '', label: 'Tümü' },
          { key: 'Bekliyor', label: 'Bekleyen' },
          { key: 'Atandi', label: 'Atanan' },
          { key: 'DevamEdiyor', label: 'Devam' }
        ].map((d) => (
          <button
            key={d.key}
            onClick={() => setFiltre(d.key)}
            className={`shrink-0 flex-1 px-4 py-2 rounded-xl text-[13px] font-bold transition-all duration-300 whitespace-nowrap ${
              filtre === d.key
                ? 'bg-slate-700/80 text-white shadow-sm ring-1 ring-white/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      {/* Görev Listesi */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-800/40 rounded-3xl p-4 border border-slate-800/50 flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <div className="h-6 w-20 bg-slate-700/50 rounded-lg animate-pulse" />
                <div className="h-6 w-16 bg-slate-700/50 rounded-lg animate-pulse" />
              </div>
              <div className="h-5 w-48 bg-slate-700/50 rounded-md animate-pulse mt-2" />
              <div className="h-3 w-24 bg-slate-700/50 rounded-md animate-pulse" />
              <div className="flex gap-2 mt-3 pt-3 border-t border-slate-800/50">
                <div className="h-8 w-24 bg-slate-700/50 rounded-lg animate-pulse" />
                <div className="h-8 w-24 bg-slate-700/30 rounded-lg animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      ) : gorevler.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-900/50 rounded-3xl border border-dashed border-slate-800">
          <div className="bg-slate-800 p-4 rounded-full mb-4 shadow-inner">
            <Inbox className="w-10 h-10 text-slate-500" />
          </div>
          <p className="font-bold text-lg text-slate-300">Görev bulunamadı</p>
          <p className="text-sm text-slate-500 mt-1">Bu filtreye uygun görev yok.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {gorevler.map((g) => {
            const atanmis = g.durum === 'Atandi' || g.durum === 'DevamEdiyor';
            return (
              <button
                key={g.id}
                onClick={atanmis ? () => navigate('/terminal/yerlestirme', { state: { gorev: g } }) : undefined}
                disabled={!atanmis}
                className={`group w-full relative overflow-hidden rounded-3xl p-4 text-left transition-all duration-300 border ${
                  atanmis
                    ? 'bg-gradient-to-b from-slate-800 to-slate-900 border-slate-700 hover:border-slate-500 active:scale-[0.98] shadow-lg shadow-black/20'
                    : 'bg-slate-900/60 border-slate-800/50 cursor-not-allowed opacity-[0.85]'
                }`}
              >
                {/* Atanmış Görevler için sol Highlight bar */}
                {atanmis && <div className="absolute left-0 top-0 bottom-0 w-[5px] bg-amber-500 shadow-[2px_0_10px_rgba(245,158,11,0.5)]" />}

                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-1 rounded-lg border ${DURUM_RENK[g.durum] || 'bg-slate-700/50 text-slate-300 border-slate-600/30'}`}>
                      {g.durum}
                    </span>
                    <span className={`flex items-center gap-1 text-[10px] uppercase font-bold px-2.5 py-1 rounded-lg border border-transparent ${ONCELIK_RENK[g.oncelik] || 'bg-slate-800 text-slate-400'}`}>
                      {g.oncelik <= 2 && <AlertCircle className="w-3 h-3" />}
                      {ONCELIK_ETİKET[g.oncelik] || g.oncelik}
                    </span>
                  </div>
                  {atanmis ? (
                    <div className="bg-white/5 p-1.5 rounded-full group-hover:bg-white/10 transition-colors">
                      <ArrowRight className="w-4 h-4 text-slate-300" />
                    </div>
                  ) : (
                    <span className="text-[10px] font-semibold text-slate-500 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
                      Bekliyor
                    </span>
                  )}
                </div>

                <div className="flex flex-col gap-1">
                  <div className="flex items-baseline gap-2">
                    <p className={`text-[15px] font-bold ${atanmis ? 'text-white' : 'text-slate-300'}`}>
                      {g.urun_adi || `Görev #${g.id}`}
                    </p>
                    <span className="text-[11px] font-mono font-medium text-slate-500 bg-slate-950/50 px-1.5 rounded shrink-0">#{g.id}</span>
                  </div>
                  
                  <p className={`text-[11px] font-bold tracking-widest uppercase flex items-center gap-1.5 ${TIP_RENK[g.tip] || 'text-slate-500'}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                    {g.tip}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 flex gap-3 text-xs font-medium text-slate-400 flex-wrap">
                  <div className="flex items-center gap-1.5 bg-slate-950/50 px-2.5 py-1.5 rounded-lg border border-white/5">
                    <Package className="w-3.5 h-3.5 text-slate-500" />
                    <span className="font-mono text-slate-300">{g.palet_barkodu || `P#${g.palet_id}`}</span>
                  </div>
                  {(g.onerilen_raf_kodu || g.onerilen_raf_id) && (
                    <div className="flex items-center gap-1.5 bg-amber-500/5 px-2.5 py-1.5 rounded-lg border border-amber-500/10">
                      <ArrowRight className="w-3.5 h-3.5 text-amber-500/50" />
                      <span className="font-mono text-amber-400/90 font-bold">{g.onerilen_raf_kodu || `#${g.onerilen_raf_id}`}</span>
                    </div>
                  )}
                  {g.zone_adi && (
                    <div className="flex items-center gap-1.5 bg-slate-950/50 px-2.5 py-1.5 rounded-lg border border-white/5">
                       <span className="text-slate-300 font-semibold">{g.zone_adi}</span>
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
