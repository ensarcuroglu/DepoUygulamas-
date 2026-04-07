/**
 * GorevListesiPage — Operatörün bekleyen yerleştirme görevleri listesi.
 * Industrial Dark UI — yüksek kontrast, büyük dokunmatik hedefler.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, RefreshCw, ArrowRight, AlertCircle, Inbox } from 'lucide-react';
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
    <div className="p-4 space-y-4 max-w-lg mx-auto">
      {/* Başlık + Yenile */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-amber-400" />
          <h1 className="text-lg font-bold text-slate-100">Görev Listesi</h1>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors disabled:opacity-40"
          aria-label="Yenile"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Bekleyen Özet Kartı */}
      {ozet && (
        <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 font-semibold">Havuz Durumu</p>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-2xl font-black text-amber-400">{ozet.toplam_bekleyen}</p>
              <p className="text-xs text-slate-500 mt-0.5">Bekleyen</p>
            </div>
            <div>
              <p className="text-2xl font-black text-red-400">{ozet.acil}</p>
              <p className="text-xs text-slate-500 mt-0.5">Acil</p>
            </div>
            <div>
              <p className="text-2xl font-black text-slate-400">{ozet.normal}</p>
              <p className="text-xs text-slate-500 mt-0.5">Normal</p>
            </div>
          </div>
        </div>
      )}

      {/* Sıradaki Görevi Al Butonu */}
      <button
        onClick={siradakiGoreviAl}
        disabled={aliyor || loading}
        className="w-full bg-amber-500 hover:bg-amber-400 active:bg-amber-600 disabled:opacity-50 text-slate-900 font-black text-lg rounded-2xl py-5 flex items-center justify-center gap-3 transition-colors shadow-lg shadow-amber-500/20"
      >
        {aliyor ? (
          <RefreshCw className="w-6 h-6 animate-spin" />
        ) : (
          <>
            <span>SIRADAKI GÖREVİ AL</span>
            <ArrowRight className="w-6 h-6" />
          </>
        )}
      </button>

      {/* Filtre Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {['Bekliyor', 'Atandi', 'DevamEdiyor', ''].map((d) => (
          <button
            key={d}
            onClick={() => setFiltre(d)}
            className={`shrink-0 px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
              filtre === d
                ? 'bg-amber-500 text-slate-900'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {d || 'Tümü'}
          </button>
        ))}
      </div>

      {/* Görev Listesi */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-800 rounded-2xl p-4 animate-pulse h-28" />
          ))}
        </div>
      ) : gorevler.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-600">
          <Inbox className="w-12 h-12 mb-3" />
          <p className="font-semibold">Görev bulunamadı</p>
        </div>
      ) : (
        <div className="space-y-3">
          {gorevler.map((g) => {
            // Bekliyor görevler atanmamış — doğrudan açılamaz, FIFO butonu kullanılmalı.
            const atanmis = g.durum === 'Atandi' || g.durum === 'DevamEdiyor';
            return (
              <button
                key={g.id}
                onClick={atanmis ? () => navigate('/terminal/yerlestirme', { state: { gorev: g } }) : undefined}
                disabled={!atanmis}
                title={!atanmis ? 'Bu görevi almak için "Sıradaki Görevi Al" butonunu kullanın' : undefined}
                className={`w-full bg-slate-800 border rounded-2xl p-4 text-left transition-all ${
                  atanmis
                    ? 'hover:bg-slate-750 active:bg-slate-700 border-slate-700 hover:border-slate-600 cursor-pointer'
                    : 'border-slate-700/50 opacity-60 cursor-not-allowed'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${DURUM_RENK[g.durum] || 'bg-slate-600 text-slate-300'}`}>
                      {g.durum}
                    </span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${ONCELIK_RENK[g.oncelik] || 'bg-slate-600 text-slate-400'}`}>
                      {ONCELIK_ETİKET[g.oncelik] || g.oncelik}
                    </span>
                  </div>
                  {atanmis
                    ? <ArrowRight className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                    : <span className="text-xs text-slate-600 shrink-0 mt-0.5">FIFO kuyruğu</span>
                  }
                </div>
                <p className="text-sm font-bold text-slate-200">Görev #{g.id}</p>
                <p className={`text-xs font-semibold mt-0.5 ${TIP_RENK[g.tip] || 'text-slate-400'}`}>{g.tip}</p>
                <div className="flex gap-4 mt-2 text-xs text-slate-500">
                  <span>Palet: {g.palet_id}</span>
                  {g.onerilen_raf_id && <span>Hedef Raf: #{g.onerilen_raf_id}</span>}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
