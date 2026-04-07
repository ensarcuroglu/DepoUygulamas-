/**
 * TerminalOzetPage — Operatörün günlük istatistik özeti.
 */
import { useState, useCallback, useEffect } from 'react';
import { BarChart2, RefreshCw, CheckCircle, Clock, AlertCircle, Inbox } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../../hooks/useAsync';
import { hataMetni } from '../../utils/hata';
import { terminalOzet, getYerlestirmeGorevleri } from '../../services/api';

export default function TerminalOzetPage() {
  const { loading, run } = useAsync(true);
  const [ozet, setOzet] = useState(null);
  const [sonTamamlananlar, setSonTamamlananlar] = useState([]);

  const yukle = useCallback(async () => {
    try {
      const [ozetRes, tamamlananRes] = await run(() =>
        Promise.all([
          terminalOzet(),
          getYerlestirmeGorevleri({ durum: 'Tamamlandi', limit: 10 }),
        ])
      );
      setOzet(ozetRes.data);
      setSonTamamlananlar(tamamlananRes.data);
    } catch (err) {
      toast.error(hataMetni(err, 'Özet yüklenemedi'));
    }
  }, [run]);

  useEffect(() => { void yukle(); }, [yukle]);

  const bugun = new Date().toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="p-4 space-y-4 max-w-lg mx-auto">
      {/* Başlık */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-amber-400" />
          <div>
            <h1 className="text-lg font-bold text-slate-100">Günlük Özet</h1>
            <p className="text-xs text-slate-500">{bugun}</p>
          </div>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* İstatistik Kartları */}
      {loading && !ozet ? (
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => <div key={i} className="bg-slate-800 rounded-2xl p-5 animate-pulse h-24" />)}
        </div>
      ) : ozet && (
        <div className="grid grid-cols-3 gap-3">
          <StatKart
            ikon={<CheckCircle className="w-5 h-5 text-green-400" />}
            deger={ozet.bugun_tamamlanan}
            etiket="Tamamladım"
            renk="green"
          />
          <StatKart
            ikon={<Clock className="w-5 h-5 text-blue-400" />}
            deger={ozet.benim_atanan_gorev}
            etiket="Atandı"
            renk="blue"
          />
          <StatKart
            ikon={<AlertCircle className="w-5 h-5 text-amber-400" />}
            deger={ozet.bekleyen_gorev}
            etiket="Havuzda"
            renk="amber"
          />
        </div>
      )}

      {/* Son Tamamlananlar */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-3">Son Tamamlananlar</p>
        {loading && sonTamamlananlar.length === 0 ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="bg-slate-800 rounded-xl h-14 animate-pulse" />)}
          </div>
        ) : sonTamamlananlar.length === 0 ? (
          <div className="flex flex-col items-center py-10 text-slate-600">
            <Inbox className="w-10 h-10 mb-2" />
            <p className="text-sm">Henüz tamamlanan görev yok</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sonTamamlananlar.map((g) => (
              <div key={g.id} className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-200">Görev #{g.id}</p>
                  <p className="text-xs text-slate-500">{g.tip} — Palet {g.palet_id}</p>
                </div>
                <div className="text-right">
                  <span className="inline-block bg-green-500/20 text-green-300 text-xs font-bold px-2 py-0.5 rounded-full border border-green-500/30">
                    Tamamlandı
                  </span>
                  {g.tamamlanma_tarihi && (
                    <p className="text-xs text-slate-600 mt-0.5">
                      {new Date(g.tamamlanma_tarihi).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatKart({ ikon, deger, etiket, renk }) {
  const renlerMap = {
    green: 'bg-green-500/10 border-green-500/20',
    blue: 'bg-blue-500/10 border-blue-500/20',
    amber: 'bg-amber-500/10 border-amber-500/20',
  };
  return (
    <div className={`rounded-2xl p-4 border text-center ${renlerMap[renk] || 'bg-slate-800 border-slate-700'}`}>
      <div className="flex justify-center mb-1">{ikon}</div>
      <p className="text-2xl font-black text-slate-100">{deger ?? '—'}</p>
      <p className="text-xs text-slate-500 mt-0.5">{etiket}</p>
    </div>
  );
}
