/**
 * ZonlarPage — Zon (Bölge) yönetimi. Admin + Lojistik erişimi.
 */
import { useState, useEffect, useCallback } from 'react';
import { MapPin, Plus, X, RefreshCw, Edit2, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import { getZonlar, createZon, updateZon, deleteZon, getDepolar } from '../services/api';

const ZON_TİPLERİ = [
  { value: 'MalKabul', label: 'Mal Kabul' },
  { value: 'Genel', label: 'Genel Stok' },
  { value: 'Soguk', label: 'Soğuk Depo' },
  { value: 'Karantina', label: 'Karantina' },
  { value: 'Sevkiyat', label: 'Sevkiyat' },
  { value: 'Tehlikeli', label: 'Tehlikeli Madde' },
];

const TIP_RENK = {
  MalKabul: 'bg-blue-100 text-blue-700',
  Genel: 'bg-green-100 text-green-700',
  Soguk: 'bg-cyan-100 text-cyan-700',
  Karantina: 'bg-red-100 text-red-700',
  Sevkiyat: 'bg-purple-100 text-purple-700',
  Tehlikeli: 'bg-orange-100 text-orange-700',
};

const BOSH_FORM = { depo_id: '', isim: '', tip: 'Genel', kod: '', aciklama: '', sira: 0 };

export default function ZonlarPage() {
  const { loading, run } = useAsync(true);
  const [zonlar, setZonlar] = useState([]);
  const [depolar, setDepolar] = useState([]);
  const [seciliDepoId, setSeciliDepoId] = useState('');
  const [modalAcik, setModalAcik] = useState(false);
  const [duzenleZon, setDuzenleZon] = useState(null);
  const [form, setForm] = useState(BOSH_FORM);
  const [silOnayId, setSilOnayId] = useState(null);

  const yukle = useCallback(async () => {
    try {
      const [zonRes, depoRes] = await run(() =>
        Promise.all([
          getZonlar(seciliDepoId ? { depo_id: seciliDepoId } : {}),
          getDepolar(),
        ])
      );
      setZonlar(zonRes.data);
      setDepolar(depoRes.data);
      if (!seciliDepoId && depoRes.data.length > 0) {
        setSeciliDepoId(depoRes.data[0].id);
      }
    } catch (err) {
      toast.error(hataMetni(err, 'Veriler yüklenemedi'));
    }
  }, [run, seciliDepoId]);

  useEffect(() => { void yukle(); }, [yukle]);

  const modalAc = (zon = null) => {
    setDuzenleZon(zon);
    setForm(zon
      ? { depo_id: zon.depo_id, isim: zon.isim, tip: zon.tip, kod: zon.kod, aciklama: zon.aciklama || '', sira: zon.sira || 0 }
      : { ...BOSH_FORM, depo_id: seciliDepoId || '' }
    );
    setModalAcik(true);
  };

  const kaydet = async (e) => {
    e.preventDefault();
    await run(async () => {
      if (duzenleZon) {
        await updateZon(duzenleZon.id, form);
        toast.success('Zon güncellendi');
      } else {
        await createZon(form);
        toast.success('Zon oluşturuldu');
      }
      setModalAcik(false);
      void yukle();
    }).catch((err) => toast.error(hataMetni(err, 'İşlem başarısız')));
  };

  const sil = async (id) => {
    await run(async () => {
      await deleteZon(id);
      toast.success('Zon pasife alındı');
      setSilOnayId(null);
      void yukle();
    }).catch((err) => toast.error(hataMetni(err, 'Silinemedi')));
  };

  const seciliDepolar = depolar.find((d) => d.id === Number(seciliDepoId));

  return (
    <div className="space-y-6">
      {/* Başlık */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-50 rounded-xl">
            <MapPin className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">Zon Yönetimi</h1>
            <p className="text-sm text-slate-500">Depo bölgelerini yönetin</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={seciliDepoId}
            onChange={(e) => setSeciliDepoId(e.target.value)}
            className="text-sm border border-slate-200 rounded-xl px-3 py-2 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Tüm Depolar</option>
            {depolar.map((d) => (
              <option key={d.id} value={d.id}>{d.isim}</option>
            ))}
          </select>
          <button
            onClick={yukle}
            disabled={loading}
            className="p-2 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-40"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => modalAc()}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl px-4 py-2 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            Yeni Zon
          </button>
        </div>
      </div>

      {/* Zon Listesi */}
      {loading && zonlar.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-5 animate-pulse h-36 border border-slate-100" />
          ))}
        </div>
      ) : zonlar.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center text-slate-500">
          <MapPin className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <p className="font-semibold">Zon bulunamadı</p>
          <p className="text-sm mt-1">Yeni zon ekleyerek başlayın.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {zonlar.map((zon) => (
            <div key={zon.id} className="bg-white rounded-2xl border border-slate-100 p-5 hover:border-indigo-200 hover:shadow-sm transition-all group">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${TIP_RENK[zon.tip] || 'bg-slate-100 text-slate-600'}`}>
                      {ZON_TİPLERİ.find((t) => t.value === zon.tip)?.label || zon.tip}
                    </span>
                    {!zon.aktif && (
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-400">Pasif</span>
                    )}
                  </div>
                  <h3 className="font-bold text-slate-800 truncate">{zon.isim}</h3>
                  <p className="text-sm font-mono text-slate-500 mt-0.5">{zon.kod}</p>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => modalAc(zon)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setSilOnayId(zon.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              {zon.aciklama && (
                <p className="text-xs text-slate-500 line-clamp-2">{zon.aciklama}</p>
              )}
              <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-100">
                <span className="text-xs text-slate-400">Sıra: {zon.sira}</span>
                <span className="text-xs text-slate-400">Depo ID: {zon.depo_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Oluştur / Güncelle Modal */}
      {modalAcik && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-slate-100">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="font-bold text-slate-800 text-lg">
                {duzenleZon ? 'Zon Düzenle' : 'Yeni Zon Ekle'}
              </h2>
              <button onClick={() => setModalAcik(false)} className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={kaydet} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Depo</label>
                <select
                  required
                  value={form.depo_id}
                  onChange={(e) => setForm({ ...form, depo_id: e.target.value })}
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Seçin...</option>
                  {depolar.map((d) => <option key={d.id} value={d.id}>{d.isim}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Zon Adı</label>
                  <input
                    required
                    value={form.isim}
                    onChange={(e) => setForm({ ...form, isim: e.target.value })}
                    className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Genel Stok"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Kod (benzersiz)</label>
                  <input
                    required
                    value={form.kod}
                    onChange={(e) => setForm({ ...form, kod: e.target.value.toUpperCase() })}
                    className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="GNL"
                    maxLength={10}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Zon Tipi</label>
                  <select
                    value={form.tip}
                    onChange={(e) => setForm({ ...form, tip: e.target.value })}
                    className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {ZON_TİPLERİ.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Görüntüleme Sırası</label>
                  <input
                    type="number"
                    value={form.sira}
                    onChange={(e) => setForm({ ...form, sira: parseInt(e.target.value) || 0 })}
                    className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    min={0}
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Açıklama</label>
                <textarea
                  value={form.aciklama}
                  onChange={(e) => setForm({ ...form, aciklama: e.target.value })}
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  rows={2}
                  placeholder="Opsiyonel açıklama..."
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setModalAcik(false)} className="flex-1 border border-slate-200 text-slate-600 font-semibold rounded-xl py-2.5 hover:bg-slate-50 transition-colors text-sm">
                  İptal
                </button>
                <button type="submit" disabled={loading} className="flex-[2] bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl py-2.5 transition-colors text-sm disabled:opacity-60">
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin mx-auto" /> : (duzenleZon ? 'Güncelle' : 'Oluştur')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sil Onay Modal */}
      {silOnayId && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 border border-slate-100">
            <h3 className="font-bold text-slate-800 mb-2">Zonu Pasife Al</h3>
            <p className="text-sm text-slate-500 mb-6">Bu zon pasife alınacak. Bağlı raflar etkilenmez.</p>
            <div className="flex gap-3">
              <button onClick={() => setSilOnayId(null)} className="flex-1 border border-slate-200 text-slate-600 rounded-xl py-2.5 font-semibold text-sm">İptal</button>
              <button onClick={() => sil(silOnayId)} disabled={loading} className="flex-[2] bg-red-500 hover:bg-red-600 text-white rounded-xl py-2.5 font-bold text-sm transition-colors">
                {loading ? 'İşleniyor...' : 'Pasife Al'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
