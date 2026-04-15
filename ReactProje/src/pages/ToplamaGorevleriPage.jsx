/**
 * ToplamaGorevleriPage — Palet bazlı toplama görevleri listesi ve yönetim sayfası.
 * Responsive: desktop tablo, mobil kart görünümü.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package, RefreshCw, CheckCircle, Clock, XCircle,
  PlayCircle, ChevronRight, Inbox, Filter,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import { toplamaGorevleriApi } from '../services/toplamaGorevleriApi';
import { useAuth } from '../contexts/AuthContext';

/* ─── Sabitler ─────────────────────────────────────── */

const DURUM_STIL = {
  Beklemede:   'bg-amber-50 text-amber-700 border-amber-200',
  Atandi:      'bg-sky-50 text-sky-700 border-sky-200',
  DevamEdiyor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  Tamamlandi:  'bg-emerald-50 text-emerald-700 border-emerald-200',
  IptalEdildi: 'bg-slate-100 text-slate-500 border-slate-200',
};

const DURUM_IKON = {
  Beklemede:   <Clock className="w-3 h-3" />,
  Atandi:      <Clock className="w-3 h-3" />,
  DevamEdiyor: <RefreshCw className="w-3 h-3 animate-spin" />,
  Tamamlandi:  <CheckCircle className="w-3 h-3" />,
  IptalEdildi: <XCircle className="w-3 h-3" />,
};

const DURUM_FILTRELERI = ['Tümü', 'Beklemede', 'Atandi', 'DevamEdiyor', 'Tamamlandi', 'IptalEdildi'];

/* ─── Alt Bileşenler ────────────────────────────────── */

function DurumBadge({ durum }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${DURUM_STIL[durum] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {DURUM_IKON[durum]}
      {durum}
    </span>
  );
}

function GorevKarti({ gorev, onDetay }) {
  return (
    <div
      className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm cursor-pointer hover:border-indigo-300 hover:shadow-md transition-all"
      onClick={() => onDetay(gorev.id)}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs text-gray-500 font-mono">#{gorev.sira_no} · Palet: {gorev.palet_no || '-'}</p>
          <p className="font-semibold text-gray-800 text-sm mt-0.5">{gorev.urun_adi || `Ürün #${gorev.urun_id}`}</p>
        </div>
        <DurumBadge durum={gorev.durum} />
      </div>
      <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
        <span>Lot: {gorev.lot_no || '-'}</span>
        <span>{gorev.koli_adedi != null ? `${gorev.koli_adedi} koli` : '-'}</span>
      </div>
      {gorev.atanan_kullanici_adi && (
        <p className="text-xs text-indigo-600 mt-1">Operatör: {gorev.atanan_kullanici_adi}</p>
      )}
    </div>
  );
}

/* ─── Ana Sayfa ─────────────────────────────────────── */

export default function ToplamaGorevleriPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { loading, run } = useAsync();

  const [gorevler, setGorevler] = useState([]);
  const [aktifDurum, setAktifDurum] = useState('Tümü');
  const [siradanAlYukleniyor, setSiradanAlYukleniyor] = useState(false);

  const yukle = useCallback(async () => {
    const params = {};
    if (aktifDurum !== 'Tümü') params.durum = aktifDurum;
    await run(async () => {
      const data = await toplamaGorevleriApi.listele(params);
      setGorevler(data);
    });
  }, [aktifDurum, run]);

  useEffect(() => { yukle(); }, [yukle]);

  const siradanGorevAl = async () => {
    setSiradanAlYukleniyor(true);
    try {
      const gorev = await toplamaGorevleriApi.siradanGorevAl(user?.depo_id || null);
      if (!gorev) {
        toast('Sırada bekleyen görev yok.', { icon: '📭' });
      } else {
        toast.success(`Görev #${gorev.sira_no} alındı.`);
        navigate(`/toplama-gorevleri/${gorev.id}`);
      }
    } catch (err) {
      toast.error(hataMetni(err, 'Görev alınamadı.'));
    } finally {
      setSiradanAlYukleniyor(false);
    }
  };

  const bekleyenSayisi = gorevler.filter(g => g.durum === 'Beklemede').length;
  const aktifSayisi = gorevler.filter(g => g.durum === 'DevamEdiyor' || g.durum === 'Atandi').length;

  return (
    <div className="p-4 md:p-6 space-y-4 max-w-6xl mx-auto">
      {/* Başlık */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Toplama Görevleri</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Bekleyen: <span className="font-medium text-amber-600">{bekleyenSayisi}</span>
            {' · '}
            Aktif: <span className="font-medium text-indigo-600">{aktifSayisi}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={yukle}
            className="flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Yenile
          </button>
          <button
            onClick={siradanGorevAl}
            disabled={siradanAlYukleniyor || bekleyenSayisi === 0}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <PlayCircle className="w-4 h-4" />
            {siradanAlYukleniyor ? 'Alınıyor...' : 'Sıradaki Görevi Al'}
          </button>
        </div>
      </div>

      {/* Durum Filtresi */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {DURUM_FILTRELERI.map(d => (
          <button
            key={d}
            onClick={() => setAktifDurum(d)}
            className={`flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${
              aktifDurum === d
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
            }`}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Mobil: Kart listesi */}
      <div className="grid grid-cols-1 gap-3 sm:hidden">
        {loading && <p className="text-center text-sm text-gray-400 py-8">Yükleniyor...</p>}
        {!loading && gorevler.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Inbox className="w-10 h-10 mx-auto mb-2 opacity-40" />
            <p className="text-sm">Görev bulunamadı.</p>
          </div>
        )}
        {gorevler.map(g => (
          <GorevKarti key={g.id} gorev={g} onDetay={(id) => navigate(`/toplama-gorevleri/${id}`)} />
        ))}
      </div>

      {/* Desktop: Tablo */}
      <div className="hidden sm:block bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Sıra</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Palet No</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Ürün</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Lot</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-gray-500">Koli</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Durum</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Operatör</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading && (
              <tr><td colSpan={8} className="text-center py-8 text-gray-400 text-sm">Yükleniyor...</td></tr>
            )}
            {!loading && gorevler.length === 0 && (
              <tr><td colSpan={8} className="text-center py-12 text-gray-400 text-sm">
                <Inbox className="w-8 h-8 mx-auto mb-2 opacity-40" />
                Görev bulunamadı.
              </td></tr>
            )}
            {gorevler.map(g => (
              <tr
                key={g.id}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/toplama-gorevleri/${g.id}`)}
              >
                <td className="px-4 py-3 font-mono text-xs text-gray-500">#{g.sira_no}</td>
                <td className="px-4 py-3 font-mono text-xs">{g.palet_no || '-'}</td>
                <td className="px-4 py-3 font-medium text-gray-800">{g.urun_adi || `Ürün #${g.urun_id}`}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{g.lot_no || '-'}</td>
                <td className="px-4 py-3 text-right text-xs">{g.koli_adedi ?? '-'}</td>
                <td className="px-4 py-3"><DurumBadge durum={g.durum} /></td>
                <td className="px-4 py-3 text-xs text-gray-500">{g.atanan_kullanici_adi || '-'}</td>
                <td className="px-4 py-3">
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
