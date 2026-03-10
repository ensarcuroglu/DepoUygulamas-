import { useState, useEffect } from 'react';
import {
  Plus, Search, Calendar, Truck, User, Phone, DoorOpen, Loader2, X, AlertCircle
} from 'lucide-react';
import {
  getSevkiyatPlanlari, createSevkiyatPlani, updateSevkiyatPlani,
  deleteSevkiyatPlani, getSiparisler
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
  'Planlandi': 'bg-slate-100 text-slate-800 border border-slate-300',
  'Yukleniyor': 'bg-amber-100 text-amber-800 border border-amber-300',
  'Yolda': 'bg-blue-100 text-blue-800 border border-blue-300',
  'TeslimEdildi': 'bg-emerald-100 text-emerald-800 border border-emerald-300',
};

const durumButonlari = ['Planlandi', 'Yukleniyor', 'Yolda', 'TeslimEdildi'];

export default function SevkiyatPlanlamaPage() {
  const { loading, run } = useAsync(true);
  const [planlar, setPlanlar] = useState([]);
  const [siparisler, setSiparisler] = useState([]);
  const [durumFiltre, setDurumFiltre] = useState('');
  const [yeniPlanModal, setYeniPlanModal] = useState(false);
  const [seciliPlan, setSeciliPlan] = useState(null);

  const [formData, setFormData] = useState({
    siparis_id: '',
    tir_plaka: '',
    sofor_adi: '',
    sofor_telefon: '',
    depo_kapi: '',
    yukleme_tarihi: '',
    cikis_saati: '',
    varis_saati: '',
    durum: 'Planlandi',
    notlar: '',
  });

  const yükle = async () => {
    const [planRes, sipRes] = await run(() =>
      Promise.all([
        getSevkiyatPlanlari({ limit: 100, durum: durumFiltre || undefined }),
        getSiparisler({ limit: 500 }),
      ])
    );
    setPlanlar(planRes?.data || []);
    setSiparisler(sipRes?.data || []);
  };

  useEffect(() => {
    yükle();
  }, [durumFiltre]);

  const handleYeniPlan = async () => {
    if (!formData.siparis_id || !formData.yukleme_tarihi) {
      toast.error('Lütfen zorunlu alanları doldurun');
      return;
    }

    try {
      await createSevkiyatPlani(formData);
      toast.success('Sevkiyat planı oluşturuldu');
      setYeniPlanModal(false);
      setFormData({
        siparis_id: '',
        tir_plaka: '',
        sofor_adi: '',
        sofor_telefon: '',
        depo_kapi: '',
        yukleme_tarihi: '',
        cikis_saati: '',
        varis_saati: '',
        durum: 'Planlandi',
        notlar: '',
      });
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Plan oluşturma başarısız'));
    }
  };

  const handleDurumDegis = async (planId, yeniDurum) => {
    try {
      await updateSevkiyatPlani(planId, { durum: yeniDurum });
      toast.success('Durum güncellendi');
      yükle();
      setSeciliPlan(null);
    } catch (err) {
      toast.error(hataMetni(err, 'Güncelleme başarısız'));
    }
  };

  const handleSil = async (id) => {
    if (!confirm('Bu planı silmek istediğinizden emin misiniz?')) return;
    try {
      await deleteSevkiyatPlani(id);
      toast.success('Plan silindi');
      yükle();
    } catch (err) {
      toast.error(hataMetni(err, 'Silme başarısız'));
    }
  };

  const filtrelenmis = planlar.filter((p) =>
    !durumFiltre || p.durum === durumFiltre
  );

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Başlık */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-900">Sevkiyat Planlama</h1>
        <button
          onClick={() => setYeniPlanModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-5 py-3 rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          <Plus className="h-5 w-5" /> Yeni Plan
        </button>
      </div>

      {/* Durum Filtreleri */}
      <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setDurumFiltre('')}
          className={`px-4 py-2 rounded-full font-semibold whitespace-nowrap transition ${
            !durumFiltre ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
          }`}
        >
          Hepsi
        </button>
        {durumButonlari.map((durum) => (
          <button
            key={durum}
            onClick={() => setDurumFiltre(durum)}
            className={`px-4 py-2 rounded-full font-semibold whitespace-nowrap transition ${
              durumFiltre === durum ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            {durum}
          </button>
        ))}
      </div>

      {/* Planlar Listesi */}
      {filtrelenmis.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center">
          <Truck className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Sevkiyat planı bulunamadı</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtrelenmis.map((plan) => (
            <div
              key={plan.id}
              className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Truck className="h-6 w-6 text-blue-600" />
                    <h3 className="text-lg font-bold text-slate-900">
                      {plan.tir_plaka || 'Plaka Belirtilmemiş'}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${durumRenkleri[plan.durum]}`}>
                      {plan.durum}
                    </span>
                  </div>
                  <p className="text-slate-600 text-sm">
                    {plan.siparis?.musteri_adi} - {plan.siparis?.siparis_no}
                  </p>
                </div>
              </div>

              {/* Bilgiler Gridi */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Yükleme Tarihi</p>
                  <p className="text-slate-900 font-semibold flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-600" />
                    {plan.yukleme_tarihi}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Şoför</p>
                  <p className="text-slate-900 font-semibold flex items-center gap-2">
                    <User className="h-4 w-4 text-blue-600" />
                    {plan.sofor_adi || '-'}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Telefon</p>
                  <p className="text-slate-900 font-semibold flex items-center gap-2">
                    <Phone className="h-4 w-4 text-blue-600" />
                    {plan.sofor_telefon || '-'}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase">Depo Kapısı</p>
                  <p className="text-slate-900 font-semibold flex items-center gap-2">
                    <DoorOpen className="h-4 w-4 text-blue-600" />
                    {plan.depo_kapi || '-'}
                  </p>
                </div>
              </div>

              {/* Saatler */}
              {(plan.cikis_saati || plan.varis_saati) && (
                <div className="grid grid-cols-2 gap-4 mb-4 py-3 border-y border-slate-200">
                  {plan.cikis_saati && (
                    <div>
                      <p className="text-slate-500 text-xs font-bold uppercase">Çıkış Saati</p>
                      <p className="text-slate-900 font-semibold">{plan.cikis_saati}</p>
                    </div>
                  )}
                  {plan.varis_saati && (
                    <div>
                      <p className="text-slate-500 text-xs font-bold uppercase">Varış Saati</p>
                      <p className="text-slate-900 font-semibold">{plan.varis_saati}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Notlar */}
              {plan.notlar && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900">
                  <p className="font-semibold mb-1">Not:</p>
                  <p>{plan.notlar}</p>
                </div>
              )}

              {/* Durum Butonları */}
              <div className="flex gap-2 flex-wrap">
                {durumButonlari.map((durum) => (
                  <button
                    key={durum}
                    onClick={() => handleDurumDegis(plan.id, durum)}
                    disabled={durum === plan.durum}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition ${
                      durum === plan.durum
                        ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                        : 'bg-slate-100 text-slate-900 hover:bg-slate-200'
                    }`}
                  >
                    {durum}
                  </button>
                ))}
                <button
                  onClick={() => handleSil(plan.id)}
                  className="ml-auto px-4 py-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 font-semibold text-sm transition"
                >
                  Sil
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Yeni Plan Modal */}
      {yeniPlanModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900">Yeni Sevkiyat Planı</h2>
              <button
                onClick={() => setYeniPlanModal(false)}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Sipariş Seçimi */}
              <div>
                <label className="block text-sm font-bold text-slate-600 uppercase mb-2">
                  Sipariş * (Zorunlu)
                </label>
                <select
                  value={formData.siparis_id}
                  onChange={(e) => setFormData({ ...formData, siparis_id: parseInt(e.target.value) || '' })}
                  className="h-12 px-4 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                >
                  <option value="">Sipariş Seçin</option>
                  {siparisler.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.siparis_no} - {s.musteri_adi}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Tır Plakası"
                  value={formData.tir_plaka}
                  onChange={(e) => setFormData({ ...formData, tir_plaka: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <input
                  type="text"
                  placeholder="Şoför Adı"
                  value={formData.sofor_adi}
                  onChange={(e) => setFormData({ ...formData, sofor_adi: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <input
                  type="tel"
                  placeholder="Şoför Telefonu"
                  value={formData.sofor_telefon}
                  onChange={(e) => setFormData({ ...formData, sofor_telefon: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <input
                  type="text"
                  placeholder="Depo Kapısı"
                  value={formData.depo_kapi}
                  onChange={(e) => setFormData({ ...formData, depo_kapi: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <input
                  type="date"
                  value={formData.yukleme_tarihi}
                  onChange={(e) => setFormData({ ...formData, yukleme_tarihi: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <input
                  type="time"
                  placeholder="Çıkış Saati"
                  value={formData.cikis_saati}
                  onChange={(e) => setFormData({ ...formData, cikis_saati: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
                <input
                  type="time"
                  placeholder="Varış Saati"
                  value={formData.varis_saati}
                  onChange={(e) => setFormData({ ...formData, varis_saati: e.target.value })}
                  className="h-12 px-4 text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                />
              </div>

              <textarea
                placeholder="Notlar"
                value={formData.notlar}
                onChange={(e) => setFormData({ ...formData, notlar: e.target.value })}
                className="h-24 px-4 py-3 w-full text-sm font-medium rounded-xl border border-slate-200 bg-slate-50 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              />
            </div>

            <div className="border-t border-slate-200 p-6 flex gap-3">
              <button
                onClick={() => setYeniPlanModal(false)}
                className="flex-1 h-12 rounded-xl border-2 border-slate-200 text-slate-900 font-bold hover:bg-slate-100 transition"
              >
                İptal
              </button>
              <button
                onClick={handleYeniPlan}
                className="flex-1 h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
              >
                Oluştur
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
