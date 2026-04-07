/**
 * YerlestirmeGorevleriPage — Admin / Lojistik görev takip sayfası.
 */
import { useState, useEffect, useCallback } from 'react';
import { Package, RefreshCw, X, ChevronDown, AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import {
  getYerlestirmeGorevleri,
  getBekleyenGorevOzet,
  goreviIptal,
  karantinayaAl,
  karantinandanCikar,
  bilinmeyenKonumGorevleriOlustur,
  getDepolar,
} from '../services/api';

const DURUM_RENK = {
  Bekliyor: 'bg-amber-50 text-amber-700 border-amber-200',
  Atandi: 'bg-blue-50 text-blue-700 border-blue-200',
  DevamEdiyor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  Tamamlandi: 'bg-green-50 text-green-700 border-green-200',
  IptalEdildi: 'bg-slate-100 text-slate-500 border-slate-200',
};

const DURUM_IKON = {
  Bekliyor: <Clock className="w-3.5 h-3.5" />,
  Atandi: <Clock className="w-3.5 h-3.5" />,
  DevamEdiyor: <RefreshCw className="w-3.5 h-3.5 animate-spin" />,
  Tamamlandi: <CheckCircle className="w-3.5 h-3.5" />,
  IptalEdildi: <XCircle className="w-3.5 h-3.5" />,
};

const TIP_RENK = {
  Yerlestirme: 'bg-blue-100 text-blue-700',
  Transfer: 'bg-purple-100 text-purple-700',
  BelirsizKonum: 'bg-red-100 text-red-700',
};

const FILTRE_SEÇENEKLERI = ['', 'Bekliyor', 'Atandi', 'DevamEdiyor', 'Tamamlandi', 'IptalEdildi'];

export default function YerlestirmeGorevleriPage() {
  const { loading, run } = useAsync(true);
  const [gorevler, setGorevler] = useState([]);
  const [ozet, setOzet] = useState(null);
  const [filtre, setFiltre] = useState('');
  const [depolar, setDepolar] = useState([]);
  const [seciliDepo, setSeciliDepo] = useState('');
  const [iptalModal, setIptalModal] = useState(null);
  const [iptalNeden, setIptalNeden] = useState('');
  const [karantinaModal, setKarantinaModal] = useState(null); // { tip: 'al'|'cikar', paletId }
  const [karantinaNeden, setKarantinaNeden] = useState('');
  const [bilinmeyenYukleniyor, setBilinmeyenYukleniyor] = useState(false);
  const [acikSatirId, setAcikSatirId] = useState(null);

  const yukle = useCallback(async () => {
    try {
      const params = { limit: 200 };
      if (filtre) params.durum = filtre;

      const [gorevRes, ozetRes, depoRes] = await run(() =>
        Promise.all([
          getYerlestirmeGorevleri(params),
          getBekleyenGorevOzet(),
          getDepolar(),
        ])
      );
      setGorevler(gorevRes.data);
      setOzet(ozetRes.data);
      setDepolar(depoRes.data);
    } catch (err) {
      toast.error(hataMetni(err, 'Veriler yüklenemedi'));
    }
  }, [run, filtre]);

  useEffect(() => { void yukle(); }, [yukle]);

  const iptalEt = async () => {
    if (!iptalNeden.trim()) { toast.error('İptal nedeni zorunludur.'); return; }
    await run(async () => {
      await goreviIptal(iptalModal, { neden: iptalNeden });
      toast.success('Görev iptal edildi');
      setIptalModal(null);
      setIptalNeden('');
      void yukle();
    }).catch((err) => toast.error(hataMetni(err)));
  };

  const karantinaIslem = async () => {
    const { tip, paletId } = karantinaModal;
    await run(async () => {
      if (tip === 'al') {
        if (!karantinaNeden.trim()) { toast.error('Karantina gerekçesi zorunludur.'); return; }
        await karantinayaAl({ palet_id: paletId, neden: karantinaNeden });
        toast.success('Karantina görevi oluşturuldu');
      } else {
        await karantinandanCikar({ palet_id: paletId });
        toast.success('Karantina çıkış görevi oluşturuldu');
      }
      setKarantinaModal(null);
      setKarantinaNeden('');
      void yukle();
    }).catch((err) => toast.error(hataMetni(err)));
  };

  const bilinmeyenGörevlerOlustur = async () => {
    if (!seciliDepo) { toast.error('Lütfen depo seçin'); return; }
    setBilinmeyenYukleniyor(true);
    try {
      const res = await bilinmeyenKonumGorevleriOlustur(seciliDepo);
      toast.success(`${res.data.olusturulan_gorev_sayisi} görev oluşturuldu`);
      void yukle();
    } catch (err) {
      toast.error(hataMetni(err, 'İşlem başarısız'));
    } finally {
      setBilinmeyenYukleniyor(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Başlık */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-50 rounded-xl">
            <Package className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">Yerleştirme Görevleri</h1>
            <p className="text-sm text-slate-500">Tüm görevleri izleyin ve yönetin</p>
          </div>
        </div>
        <button
          onClick={yukle}
          disabled={loading}
          className="p-2 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Özet Kartları */}
      {ozet && (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          <OzetKart label="Toplam Bekleyen" value={ozet.toplam_bekleyen} renk="amber" />
          <OzetKart label="Acil" value={ozet.acil} renk="red" />
          <OzetKart label="Yüksek" value={ozet.yuksek_oncelikli} renk="orange" />
          <OzetKart label="Normal" value={ozet.normal} renk="slate" />
        </div>
      )}

      {/* Araç Çubuğu */}
      <div className="bg-white rounded-2xl border border-slate-100 p-4 flex flex-col sm:flex-row gap-3">
        {/* Filtre */}
        <div className="flex gap-2 overflow-x-auto pb-1 flex-1">
          {FILTRE_SEÇENEKLERI.map((d) => (
            <button
              key={d}
              onClick={() => setFiltre(d)}
              className={`shrink-0 px-3 py-1.5 rounded-xl text-sm font-semibold transition-colors ${
                filtre === d
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {d || 'Tümü'}
            </button>
          ))}
        </div>

        {/* Bilinmeyen Konum Görevleri */}
        <div className="flex gap-2 shrink-0">
          <select
            value={seciliDepo}
            onChange={(e) => setSeciliDepo(e.target.value)}
            className="text-sm border border-slate-200 rounded-xl px-3 py-2 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Depo seç...</option>
            {depolar.map((d) => <option key={d.id} value={d.id}>{d.isim}</option>)}
          </select>
          <button
            onClick={bilinmeyenGörevlerOlustur}
            disabled={bilinmeyenYukleniyor || !seciliDepo}
            className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl px-4 py-2 transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            {bilinmeyenYukleniyor ? '...' : 'Konumsuz Görevler'}
          </button>
        </div>
      </div>

      {/* Tablo */}
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        {loading && gorevler.length === 0 ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-14 bg-slate-100 animate-pulse rounded-xl" />)}
          </div>
        ) : gorevler.length === 0 ? (
          <div className="text-center py-16 text-slate-400">
            <Package className="w-10 h-10 mx-auto mb-3 text-slate-300" />
            <p className="font-semibold">Görev bulunamadı</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-5 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide w-8"></th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">ID</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">Durum</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">Tip</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">Palet</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">Öncelik</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">Oluşturma</th>
                  <th className="text-left px-4 py-3.5 font-semibold text-slate-500 text-xs uppercase tracking-wide">İşlem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {gorevler.map((g) => (
                  <>
                    <tr
                      key={g.id}
                      className="hover:bg-slate-50 transition-colors cursor-pointer"
                      onClick={() => setAcikSatirId(acikSatirId === g.id ? null : g.id)}
                    >
                      <td className="px-5 py-3.5">
                        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${acikSatirId === g.id ? 'rotate-180' : ''}`} />
                      </td>
                      <td className="px-4 py-3.5 font-mono text-slate-700 font-bold">#{g.id}</td>
                      <td className="px-4 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${DURUM_RENK[g.durum] || 'bg-slate-100 text-slate-600'}`}>
                          {DURUM_IKON[g.durum]}
                          {g.durum}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${TIP_RENK[g.tip] || 'bg-slate-100 text-slate-600'}`}>
                          {g.tip}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-600">{g.palet_id}</td>
                      <td className="px-4 py-3.5">
                        <span className={`text-xs font-bold ${g.oncelik === 1 ? 'text-red-600' : g.oncelik === 2 ? 'text-orange-500' : 'text-slate-400'}`}>
                          {g.oncelik === 1 ? 'ACİL' : g.oncelik === 2 ? 'Yüksek' : 'Normal'}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-500">
                        {new Date(g.olusturma_tarihi).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="px-4 py-3.5">
                        {['Bekliyor', 'Atandi', 'DevamEdiyor'].includes(g.durum) && (
                          <button
                            onClick={(e) => { e.stopPropagation(); setIptalModal(g.id); }}
                            className="text-xs text-red-500 hover:text-red-700 font-semibold hover:underline"
                          >
                            İptal
                          </button>
                        )}
                      </td>
                    </tr>
                    {acikSatirId === g.id && (
                      <tr key={`${g.id}-detay`} className="bg-slate-50">
                        <td colSpan={8} className="px-8 py-4">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                            <Detay label="Önerilen Raf" value={g.onerilen_raf_id} />
                            <Detay label="Gerçekleşen Raf" value={g.gerceklesen_raf_id || '—'} />
                            <Detay label="Atanan Kullanıcı" value={g.atanan_kullanici_id || '—'} />
                            <Detay label="Override" value={g.override_kullanici_id ? `Evet (${g.override_kullanici_id})` : 'Hayır'} />
                            {g.override_neden && (
                              <div className="col-span-2 sm:col-span-4">
                                <span className="text-xs text-slate-500 font-semibold">Override Gerekçesi:</span>
                                <p className="text-sm text-orange-700 mt-0.5 flex items-start gap-1.5">
                                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                                  {g.override_neden}
                                </p>
                              </div>
                            )}
                            {g.iptal_nedeni && (
                              <div className="col-span-2 sm:col-span-4">
                                <span className="text-xs text-slate-500 font-semibold">İptal Nedeni:</span>
                                <p className="text-sm text-red-700 mt-0.5">{g.iptal_nedeni}</p>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* İptal Modal */}
      {iptalModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 border border-slate-100">
            <h3 className="font-bold text-slate-800 mb-2">Görevi İptal Et</h3>
            <textarea
              className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none mt-2"
              rows={3}
              placeholder="İptal nedeni (zorunlu)..."
              value={iptalNeden}
              onChange={(e) => setIptalNeden(e.target.value)}
            />
            <div className="flex gap-3 mt-4">
              <button onClick={() => setIptalModal(null)} className="flex-1 border border-slate-200 text-slate-600 rounded-xl py-2.5 font-semibold text-sm">İptal</button>
              <button onClick={iptalEt} disabled={loading} className="flex-[2] bg-red-500 hover:bg-red-600 text-white rounded-xl py-2.5 font-bold text-sm transition-colors">
                {loading ? '...' : 'İptal Et'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Karantina Modal */}
      {karantinaModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 border border-slate-100">
            <h3 className="font-bold text-slate-800 mb-2">
              {karantinaModal.tip === 'al' ? 'Karantinaya Al' : 'Karantinadan Çıkar'}
            </h3>
            {karantinaModal.tip === 'al' && (
              <textarea
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none mt-2"
                rows={3}
                placeholder="Karantina gerekçesi (zorunlu)..."
                value={karantinaNeden}
                onChange={(e) => setKarantinaNeden(e.target.value)}
              />
            )}
            <div className="flex gap-3 mt-4">
              <button onClick={() => setKarantinaModal(null)} className="flex-1 border border-slate-200 text-slate-600 rounded-xl py-2.5 font-semibold text-sm">İptal</button>
              <button onClick={karantinaIslem} disabled={loading} className="flex-[2] bg-orange-500 hover:bg-orange-600 text-white rounded-xl py-2.5 font-bold text-sm transition-colors">
                {loading ? '...' : 'Onayla'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OzetKart({ label, value, renk }) {
  const renkMap = {
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
    orange: 'bg-orange-50 text-orange-700',
    slate: 'bg-slate-100 text-slate-600',
  };
  return (
    <div className={`rounded-2xl p-4 text-center ${renkMap[renk] || 'bg-slate-100 text-slate-600'}`}>
      <p className="text-2xl font-black">{value ?? '—'}</p>
      <p className="text-xs font-semibold mt-0.5 opacity-75">{label}</p>
    </div>
  );
}

function Detay({ label, value }) {
  return (
    <div>
      <p className="text-xs text-slate-500 font-semibold">{label}</p>
      <p className="text-sm font-bold text-slate-700 mt-0.5">{value}</p>
    </div>
  );
}
