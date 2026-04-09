/**
 * ZonlarPage — Zon (Bölge) yönetimi. Admin + Lojistik erişimi.
 */
import { useState, useEffect, useCallback } from 'react';
import { 
  MapPin, Plus, X, RefreshCw, Edit2, Trash2, 
  Box, Snowflake, ShieldAlert, Truck, AlertTriangle, Layers 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import { getZonlar, createZon, updateZon, deleteZon, getDepolar } from '../services/api';

const ZON_TİPLERİ = [
  { value: 'MalKabul', label: 'Mal Kabul', icon: Box, color: 'bg-blue-50 text-blue-700 border-blue-200' },
  { value: 'Genel', label: 'Genel Stok', icon: Layers, color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { value: 'Soguk', label: 'Soğuk Depo', icon: Snowflake, color: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
  { value: 'Karantina', label: 'Karantina', icon: ShieldAlert, color: 'bg-rose-50 text-rose-700 border-rose-200' },
  { value: 'Sevkiyat', label: 'Sevkiyat', icon: Truck, color: 'bg-purple-50 text-purple-700 border-purple-200' },
  { value: 'Tehlikeli', label: 'Tehlikeli Madde', icon: AlertTriangle, color: 'bg-amber-50 text-amber-700 border-amber-200' },
];

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
        toast.success('Zon başarıyla güncellendi');
      } else {
        await createZon(form);
        toast.success('Yeni zon oluşturuldu');
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

  // Helper function to get zone styling details
  const getZonStili = (tip) => {
    return ZON_TİPLERİ.find((t) => t.value === tip) || ZON_TİPLERİ[1]; // Fallback to Genel
  };

  return (
    <div className="space-y-4 md:space-y-6 max-w-[1600px] mx-auto pb-20 md:pb-8">
      {/* Üst Panel - Sticky on mobile for quick actions */}
      <div className="sticky top-0 z-10 md:static bg-white/80 backdrop-blur-md md:bg-white border-b md:border md:rounded-2xl border-slate-200 shadow-sm px-4 py-4 md:p-5 flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center -mx-4 md:mx-0">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl hidden sm:block">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Zon Yönetimi</h1>
            <p className="text-sm text-slate-500 font-medium">Depo bölgelerini ve kapasiteleri yönetin</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-48">
            <select
              value={seciliDepoId}
              onChange={(e) => setSeciliDepoId(e.target.value)}
              className="w-full appearance-none border border-slate-200 rounded-xl pl-4 pr-10 py-2.5 text-sm font-medium text-slate-700 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer"
            >
              <option value="">Tüm Depolar</option>
              {depolar.map((d) => (
                <option key={d.id} value={d.id}>{d.isim}</option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-slate-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>
          
          <button
            onClick={yukle}
            disabled={loading}
            className="p-2.5 rounded-xl border border-slate-200 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 hover:border-indigo-200 transition-all disabled:opacity-50 active:scale-95"
            aria-label="Yenile"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          
          <button
            onClick={() => modalAc()}
            className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl px-4 py-2.5 transition-all active:scale-95 shadow-sm shadow-indigo-200"
          >
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Yeni Zon</span>
          </button>
        </div>
      </div>

      {/* İçerik Alanı */}
      {loading && zonlar.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-5 animate-pulse border border-slate-100 shadow-sm flex flex-col h-44">
              <div className="flex gap-4 mb-4">
                <div className="w-12 h-12 bg-slate-100 rounded-xl" />
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-slate-100 rounded w-3/4" />
                  <div className="h-3 bg-slate-100 rounded w-1/2" />
                </div>
              </div>
              <div className="mt-auto flex justify-between">
                <div className="h-8 bg-slate-100 rounded w-20" />
                <div className="flex gap-2"><div className="w-8 h-8 bg-slate-100 rounded-lg" /><div className="w-8 h-8 bg-slate-100 rounded-lg" /></div>
              </div>
            </div>
          ))}
        </div>
      ) : zonlar.length === 0 ? (
        <div className="bg-slate-50/50 rounded-3xl border-2 border-dashed border-slate-200 p-12 flex flex-col items-center justify-center text-center">
          <div className="w-20 h-20 bg-white rounded-full shadow-sm flex items-center justify-center mb-5">
            <MapPin className="w-10 h-10 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-2">Henüz Zon Bulunmuyor</h3>
          <p className="text-slate-500 max-w-sm mb-6">Seçili depoya ait herhangi bir zon kaydı bulunamadı. Lojistik operasyonlarına başlamak için hemen bir zon ekleyin.</p>
          <button onClick={() => modalAc()} className="flex items-center gap-2 text-indigo-600 bg-white border border-indigo-100 hover:bg-indigo-50 font-semibold rounded-xl px-5 py-2.5 transition-colors shadow-sm">
            <Plus className="w-5 h-5" /> İlk Zonu Oluştur
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
          {zonlar.map((zon) => {
            const ZonStil = getZonStili(zon.tip);
            const Icon = ZonStil.icon;
            
            return (
              <div 
                key={zon.id} 
                className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all flex flex-col"
              >
                <div className="p-5 flex-1">
                  <div className="flex justify-between items-start mb-4 gap-3">
                    <div className={`p-3 rounded-xl border ${ZonStil.color} bg-opacity-50`}>
                      <Icon className="w-6 h-6" strokeWidth={1.5} />
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      <span className={`text-[11px] font-bold px-2.5 py-1 rounded-md border ${ZonStil.color}`}>
                        {ZonStil.label}
                      </span>
                      {!zon.aktif && (
                        <span className="text-[11px] font-bold px-2.5 py-1 rounded-md bg-slate-100 text-slate-500 border border-slate-200">
                          Pasif
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 leading-tight mb-1 line-clamp-1" title={zon.isim}>
                      {zon.isim}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">
                        {zon.kod}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">Depo: {zon.depo_id}</span>
                    </div>
                  </div>
                  
                  {zon.aciklama && (
                    <p className="text-sm text-slate-500 mt-3 line-clamp-2 leading-relaxed">
                      {zon.aciklama}
                    </p>
                  )}
                </div>
                
                {/* Kart Altı İşlem Çubuğu - Mobilde her zaman görünür, masaüstünde temiz durur */}
                <div className="px-5 py-3.5 bg-slate-50/80 border-t border-slate-100 rounded-b-2xl flex items-center justify-between">
                  <div className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                    Sıra: {zon.sira}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => modalAc(zon)}
                      className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-white hover:shadow-sm border border-transparent hover:border-indigo-100 transition-all"
                      aria-label="Düzenle"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setSilOnayId(zon.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-white hover:shadow-sm border border-transparent hover:border-rose-100 transition-all"
                      aria-label="Pasife Al"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Oluştur / Güncelle Modal */}
      {modalAcik && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full max-w-lg border border-slate-100 overflow-hidden animate-in slide-in-from-bottom-4 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 sm:p-6 border-b border-slate-100 bg-white sticky top-0 z-10">
              <div>
                <h2 className="font-bold text-slate-800 text-lg md:text-xl">
                  {duzenleZon ? 'Zon Detaylarını Düzenle' : 'Yeni Zon Oluştur'}
                </h2>
                <p className="text-xs text-slate-500 mt-1">Sistem üzerindeki bölge tanımlamalarını yapın.</p>
              </div>
              <button 
                onClick={() => setModalAcik(false)} 
                className="p-2.5 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors active:scale-95 bg-slate-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="overflow-y-auto flex-1 custom-scrollbar">
              <form id="zon-form" onSubmit={kaydet} className="p-5 sm:p-6 space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Bağlı Depo <span className="text-rose-500">*</span></label>
                  <select
                    required
                    value={form.depo_id}
                    onChange={(e) => setForm({ ...form, depo_id: e.target.value })}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-700 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all appearance-none"
                  >
                    <option value="">Depo Seçiniz...</option>
                    {depolar.map((d) => <option key={d.id} value={d.id}>{d.isim}</option>)}
                  </select>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Zon Adı <span className="text-rose-500">*</span></label>
                    <input
                      required
                      value={form.isim}
                      onChange={(e) => setForm({ ...form, isim: e.target.value })}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all bg-slate-50 focus:bg-white placeholder:text-slate-400"
                      placeholder="Örn: Genel Stok A"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5 flex items-center justify-between">
                      <span>Zon Kodu <span className="text-rose-500">*</span></span>
                      <span className="text-[10px] text-slate-400 font-normal">Benzersiz</span>
                    </label>
                    <input
                      required
                      value={form.kod}
                      onChange={(e) => setForm({ ...form, kod: e.target.value.toUpperCase() })}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all bg-slate-50 focus:bg-white placeholder:text-slate-400 uppercase"
                      placeholder="GNL-A"
                      maxLength={10}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Zon Tipi</label>
                    <select
                      value={form.tip}
                      onChange={(e) => setForm({ ...form, tip: e.target.value })}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-700 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all appearance-none"
                    >
                      {ZON_TİPLERİ.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Sıralama (Opsiyonel)</label>
                    <input
                      type="number"
                      value={form.sira}
                      onChange={(e) => setForm({ ...form, sira: parseInt(e.target.value) || 0 })}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all bg-slate-50 focus:bg-white"
                      min={0}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">Açıklama (Opsiyonel)</label>
                  <textarea
                    value={form.aciklama}
                    onChange={(e) => setForm({ ...form, aciklama: e.target.value })}
                    className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all bg-slate-50 focus:bg-white resize-none"
                    rows={3}
                    placeholder="Bu bölge ile ilgili özel notlar veya kurallar..."
                  />
                </div>
              </form>
            </div>

            <div className="p-5 sm:p-6 border-t border-slate-100 bg-slate-50 flex gap-3">
              <button 
                type="button" 
                onClick={() => setModalAcik(false)} 
                className="flex-1 bg-white border border-slate-200 text-slate-600 font-bold rounded-xl py-3 hover:bg-slate-100 transition-colors text-sm active:scale-95"
              >
                Vazgeç
              </button>
              <button 
                type="submit" 
                form="zon-form"
                disabled={loading} 
                className="flex-[2] bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl py-3 transition-colors text-sm disabled:opacity-70 active:scale-95 flex items-center justify-center gap-2 shadow-sm shadow-indigo-200"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : (duzenleZon ? 'Değişiklikleri Kaydet' : 'Zonu Oluştur')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sil Onay Modal */}
      {silOnayId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 border border-slate-100 animate-in zoom-in-95 duration-200 text-center">
            <div className="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-slate-800 text-lg mb-2">Zonu Pasife Al</h3>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              Bu işlemi onayladığınızda zon pasif duruma geçecek. Bu zona bağlı raflar ve stoklar etkilenmeyecektir. Emin misiniz?
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setSilOnayId(null)} 
                className="flex-1 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl py-3 font-bold text-sm transition-colors active:scale-95"
              >
                İptal
              </button>
              <button 
                onClick={() => sil(silOnayId)} 
                disabled={loading} 
                className="flex-1 bg-rose-500 hover:bg-rose-600 text-white rounded-xl py-3 font-bold text-sm transition-colors disabled:opacity-70 active:scale-95 flex items-center justify-center"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Evet, Pasife Al'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}