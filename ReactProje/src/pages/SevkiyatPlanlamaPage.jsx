import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, Calendar, Truck, User, Phone, DoorOpen, Loader2, X, AlertCircle, Clock, FileText, Package
} from 'lucide-react';
import {
  getSevkiyatPlanlari, createSevkiyatPlani, updateSevkiyatPlani,
  deleteSevkiyatPlani, getSiparisler
} from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import toast from 'react-hot-toast';

const durumRenkleri = {
  'Planlandi': 'bg-slate-100 text-slate-700 border border-slate-200',
  'Yukleniyor': 'bg-amber-50 text-amber-700 border border-amber-200',
  'Yolda': 'bg-blue-50 text-blue-700 border border-blue-200',
  'TeslimEdildi': 'bg-emerald-50 text-emerald-700 border border-emerald-200',
};

const durumButonlari = ['Planlandi', 'Yukleniyor', 'Yolda', 'TeslimEdildi'];

export default function SevkiyatPlanlamaPage() {
  const { loading, run } = useAsync(true);
  const [planlar, setPlanlar] = useState([]);
  const [siparisler, setSiparisler] = useState([]);
  const [durumFiltre, setDurumFiltre] = useState('');
  const [yeniPlanModal, setYeniPlanModal] = useState(false);

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

  const yükle = useCallback(async () => {
    const [planRes, sipRes] = await run(() =>
      Promise.all([
        getSevkiyatPlanlari({ limit: 100, durum: durumFiltre || undefined }),
        getSiparisler({ limit: 500 }),
      ])
    );
    setPlanlar(planRes?.data || []);
    setSiparisler(sipRes?.data || []);
  }, [durumFiltre, run]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void yükle();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [yükle]);

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
      <div className="flex min-h-[80vh] items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
          <p className="text-slate-500 font-medium animate-pulse">Sevkiyatlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
        
        {/* Başlık ve Aksiyon Alanı */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Sevkiyat Planlama</h1>
            <p className="text-sm text-slate-500 mt-1">Araç ve yükleme organizasyonlarını yönetin.</p>
          </div>
          <button
            onClick={() => setYeniPlanModal(true)}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold shadow-sm hover:bg-blue-700 hover:shadow active:scale-[0.98] transition-all"
          >
            <Plus className="h-5 w-5" />
            <span>Yeni Plan</span>
          </button>
        </div>

        {/* Durum Filtreleri */}
        <div className="mb-6 -mx-4 px-4 sm:mx-0 sm:px-0 overflow-x-auto hide-scrollbar">
          <div className="flex gap-2 w-max pb-2">
            <button
              onClick={() => setDurumFiltre('')}
              className={`px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-sm border ${
                !durumFiltre 
                  ? 'bg-blue-600 text-white border-blue-600' 
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
              }`}
            >
              Tüm Planlar
            </button>
            {durumButonlari.map((durum) => (
              <button
                key={durum}
                onClick={() => setDurumFiltre(durum)}
                className={`px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-sm border ${
                  durumFiltre === durum 
                    ? 'bg-blue-600 text-white border-blue-600' 
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                {durum}
              </button>
            ))}
          </div>
        </div>

        {/* Planlar Listesi */}
        {filtrelenmis.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <div className="bg-slate-50 p-4 rounded-full mb-4">
              <Truck className="h-10 w-10 text-slate-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">Kayıt Bulunamadı</h3>
            <p className="text-slate-500 max-w-sm">Arama veya filtreleme kriterlerinize uygun sevkiyat planı bulunmuyor.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5">
            {filtrelenmis.map((plan) => (
              <div
                key={plan.id}
                className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
              >
                <div className="p-5 sm:p-6">
                  {/* Kart Başlığı */}
                  <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                    <div className="flex items-start gap-4">
                      <div className="hidden sm:flex h-12 w-12 rounded-xl bg-blue-50 text-blue-600 items-center justify-center shrink-0">
                        <Truck className="h-6 w-6" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-1.5">
                          <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                            <Truck className="h-5 w-5 sm:hidden text-blue-600" />
                            {plan.tir_plaka || 'Plaka Belirtilmemiş'}
                          </h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide ${durumRenkleri[plan.durum]}`}>
                            {plan.durum}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                          <Package className="h-4 w-4" />
                          <p className="font-medium text-sm">
                            {plan.siparis?.musteri_adi} <span className="text-slate-300 mx-1">|</span> <span className="text-slate-700">{plan.siparis?.siparis_no}</span>
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Detaylar Gridi */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div>
                      <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Yükleme Tarihi</p>
                      <p className="text-slate-900 font-semibold text-sm flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        {plan.yukleme_tarihi}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Şoför</p>
                      <p className="text-slate-900 font-semibold text-sm flex items-center gap-2">
                        <User className="h-4 w-4 text-slate-400" />
                        <span className="truncate">{plan.sofor_adi || '-'}</span>
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Telefon</p>
                      <p className="text-slate-900 font-semibold text-sm flex items-center gap-2">
                        <Phone className="h-4 w-4 text-slate-400" />
                        {plan.sofor_telefon || '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Depo Kapısı</p>
                      <p className="text-slate-900 font-semibold text-sm flex items-center gap-2">
                        <DoorOpen className="h-4 w-4 text-slate-400" />
                        {plan.depo_kapi || '-'}
                      </p>
                    </div>
                  </div>

                  {/* Saatler & Notlar */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    {(plan.cikis_saati || plan.varis_saati) && (
                      <div className="flex gap-6 p-4 rounded-xl border border-slate-100 items-center">
                        <Clock className="h-5 w-5 text-slate-300 shrink-0 hidden sm:block" />
                        {plan.cikis_saati && (
                          <div>
                            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-0.5">Çıkış Saati</p>
                            <p className="text-slate-900 font-bold">{plan.cikis_saati}</p>
                          </div>
                        )}
                        {plan.cikis_saati && plan.varis_saati && (
                          <div className="h-8 w-px bg-slate-200"></div>
                        )}
                        {plan.varis_saati && (
                          <div>
                            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-0.5">Varış Saati</p>
                            <p className="text-slate-900 font-bold">{plan.varis_saati}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {plan.notlar && (
                      <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl text-sm text-amber-900 md:col-span-1">
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className="h-4 w-4 text-amber-600" />
                          <p className="font-bold text-amber-800">Notlar</p>
                        </div>
                        <p className="leading-relaxed opacity-90">{plan.notlar}</p>
                      </div>
                    )}
                  </div>

                  {/* Aksiyon Butonları (Durum Değiştirme ve Silme) */}
                  <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-4 pt-4 border-t border-slate-100">
                    <div className="flex flex-wrap gap-2">
                      {durumButonlari.map((durum) => {
                        const isCurrent = durum === plan.durum;
                        return (
                          <button
                            key={durum}
                            onClick={() => handleDurumDegis(plan.id, durum)}
                            disabled={isCurrent}
                            className={`flex-1 sm:flex-none px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg font-semibold text-xs sm:text-sm transition-colors text-center ${
                              isCurrent
                                ? 'bg-blue-50 text-blue-600 cursor-not-allowed ring-1 ring-blue-200'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 active:bg-slate-300'
                            }`}
                          >
                            {durum}
                          </button>
                        );
                      })}
                    </div>
                    <button
                      onClick={() => handleSil(plan.id)}
                      className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 hover:text-red-700 font-bold text-sm transition-colors text-center"
                    >
                      Planı Sil
                    </button>
                  </div>

                </div>
              </div>
            ))}
          </div>
        )}

        {/* Yeni Plan Modal */}
        {yeniPlanModal && (
          <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/40 backdrop-blur-sm sm:p-4">
            <div className="bg-white w-full sm:max-w-2xl sm:rounded-2xl rounded-t-3xl max-h-[95vh] flex flex-col shadow-2xl animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
              
              <div className="flex justify-between items-center p-5 sm:p-6 border-b border-slate-100 bg-white sm:rounded-t-2xl rounded-t-3xl z-10 sticky top-0">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900">Yeni Sevkiyat Planı</h2>
                <button
                  onClick={() => setYeniPlanModal(false)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="p-5 sm:p-6 overflow-y-auto space-y-6 flex-1">
                
                {/* Uyarı Kutusu */}
                <div className="flex items-start gap-3 p-4 bg-blue-50 text-blue-800 rounded-xl text-sm border border-blue-100">
                  <AlertCircle className="h-5 w-5 shrink-0 text-blue-600 mt-0.5" />
                  <p>Yeni bir sevkiyat planı oluşturmak için önce bir sipariş seçmeli ve yükleme tarihini belirlemelisiniz.</p>
                </div>

                <div className="space-y-5">
                  {/* Sipariş Seçimi */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-bold text-slate-700 flex items-center gap-1">
                      İlgili Sipariş <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.siparis_id}
                      onChange={(e) => setFormData({ ...formData, siparis_id: parseInt(e.target.value) || '' })}
                      className="w-full h-12 px-4 text-sm font-medium rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                    >
                      <option value="">Sipariş Seçiniz...</option>
                      {siparisler.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.siparis_no} - {s.musteri_adi}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Tır Plakası</label>
                      <input
                        type="text"
                        placeholder="Örn: 34 ABC 123"
                        value={formData.tir_plaka}
                        onChange={(e) => setFormData({ ...formData, tir_plaka: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors uppercase"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Şoför Adı</label>
                      <input
                        type="text"
                        placeholder="Örn: Ahmet Yılmaz"
                        value={formData.sofor_adi}
                        onChange={(e) => setFormData({ ...formData, sofor_adi: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Şoför Telefonu</label>
                      <input
                        type="tel"
                        placeholder="Örn: 0555 123 45 67"
                        value={formData.sofor_telefon}
                        onChange={(e) => setFormData({ ...formData, sofor_telefon: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Depo Kapısı</label>
                      <input
                        type="text"
                        placeholder="Örn: Kapı A-1"
                        value={formData.depo_kapi}
                        onChange={(e) => setFormData({ ...formData, depo_kapi: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-sm font-bold text-slate-700 flex items-center gap-1">
                        Yükleme Tarihi <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="date"
                        value={formData.yukleme_tarihi}
                        onChange={(e) => setFormData({ ...formData, yukleme_tarihi: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Çıkış Saati</label>
                      <input
                        type="time"
                        value={formData.cikis_saati}
                        onChange={(e) => setFormData({ ...formData, cikis_saati: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-sm font-semibold text-slate-700">Varış Saati</label>
                      <input
                        type="time"
                        value={formData.varis_saati}
                        onChange={(e) => setFormData({ ...formData, varis_saati: e.target.value })}
                        className="w-full h-12 px-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-sm font-semibold text-slate-700">Ek Notlar</label>
                    <textarea
                      placeholder="Sevkiyat ile ilgili eklemek istedikleriniz..."
                      value={formData.notlar}
                      onChange={(e) => setFormData({ ...formData, notlar: e.target.value })}
                      className="w-full min-h-[100px] p-4 text-sm rounded-xl border border-slate-300 bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-colors resize-y"
                    />
                  </div>
                </div>
              </div>

              {/* Modal Footer / Butonlar */}
              <div className="border-t border-slate-100 bg-slate-50 p-5 sm:p-6 flex flex-col-reverse sm:flex-row gap-3 rounded-b-3xl sm:rounded-b-2xl z-10 sticky bottom-0">
                <button
                  onClick={() => setYeniPlanModal(false)}
                  className="w-full sm:w-1/3 h-12 rounded-xl border border-slate-300 bg-white text-slate-700 font-bold hover:bg-slate-50 active:scale-[0.98] transition-all"
                >
                  İptal
                </button>
                <button
                  onClick={handleYeniPlan}
                  className="w-full sm:w-2/3 h-12 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 active:scale-[0.98] shadow-sm transition-all"
                >
                  Planı Oluştur
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
