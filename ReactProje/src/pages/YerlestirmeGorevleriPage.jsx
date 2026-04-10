/**
 * YerlestirmeGorevleriPage — Admin / Lojistik görev takip sayfası.
 */
import { useState, useEffect, useCallback, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Package, RefreshCw, X, ChevronDown, AlertTriangle, 
  CheckCircle, Clock, XCircle, Search, MapPin, Inbox,
  MoreVertical, UserPlus, Undo2, ArrowRight, Scan, Smartphone
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';
import {
  getYerlestirmeGorevleri,
  getBekleyenGorevOzet,
  goreviIptal,
  goreviBirak,
  siradakiGorevisiniAl,
  karantinayaAl,
  karantinandanCikar,
  bilinmeyenKonumGorevleriOlustur,
  getDepolar,
} from '../services/api';

const DURUM_RENK = {
  Bekliyor: 'bg-amber-100 text-amber-800 border-amber-200',
  Atandi: 'bg-blue-100 text-blue-800 border-blue-200',
  DevamEdiyor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  Tamamlandi: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  IptalEdildi: 'bg-slate-100 text-slate-600 border-slate-200',
};

const DURUM_IKON = {
  Bekliyor: <Clock className="w-3.5 h-3.5" />,
  Atandi: <Clock className="w-3.5 h-3.5" />,
  DevamEdiyor: <RefreshCw className="w-3.5 h-3.5 animate-spin" />,
  Tamamlandi: <CheckCircle className="w-3.5 h-3.5" />,
  IptalEdildi: <XCircle className="w-3.5 h-3.5" />,
};

const TIP_RENK = {
  Yerlestirme: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  Transfer: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  BelirsizKonum: 'bg-rose-50 text-rose-700 ring-rose-600/20',
};

const FILTRE_SEÇENEKLERI = [
  { id: '', label: 'Tümü' },
  { id: 'Bekliyor', label: 'Bekliyor' },
  { id: 'Atandi', label: 'Atandı' },
  { id: 'DevamEdiyor', label: 'Devam Ediyor' },
  { id: 'Tamamlandi', label: 'Tamamlandı' },
  { id: 'IptalEdildi', label: 'İptal Edildi' }
];

export default function YerlestirmeGorevleriPage() {
  const navigate = useNavigate();
  const { loading, run } = useAsync(true);
  const [gorevler, setGorevler] = useState([]);
  const [ozet, setOzet] = useState(null);
  const [filtre, setFiltre] = useState('');
  const [depolar, setDepolar] = useState([]);
  const [seciliDepo, setSeciliDepo] = useState('');
  const [iptalModal, setIptalModal] = useState(null);
  const [iptalNeden, setIptalNeden] = useState('');
  const [karantinaModal, setKarantinaModal] = useState(null);
  const [karantinaNeden, setKarantinaNeden] = useState('');
  const [bilinmeyenYukleniyor, setBilinmeyenYukleniyor] = useState(false);
  const [acikSatirId, setAcikSatirId] = useState(null);
  const [aksiyonYukleniyor, setAksiyonYukleniyor] = useState(null);

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

  // ── Görev Aksiyon Handler'ları ──

  const gorevUstlen = async (gorevId) => {
    setAksiyonYukleniyor(gorevId);
    try {
      await siradakiGorevisiniAl();
      toast.success('Görev üstlenildi');
      void yukle();
    } catch (err) {
      toast.error(hataMetni(err, 'Görev üstlenilemedi'));
    } finally {
      setAksiyonYukleniyor(null);
    }
  };

  const sahadaBaslat = (gorev) => {
    navigate('/terminal/yerlestirme', { state: { gorev } });
  };

  const gorevBirakAction = async (gorevId) => {
    setAksiyonYukleniyor(gorevId);
    try {
      await goreviBirak(gorevId);
      toast.success('Görev havuza iade edildi');
      void yukle();
    } catch (err) {
      toast.error(hataMetni(err, 'Görev bırakılamadı'));
    } finally {
      setAksiyonYukleniyor(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 pb-12">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        
        {/* Başlık ve Aksiyon */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white shadow-sm rounded-2xl border border-slate-100">
              <Package className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Yerleştirme Görevleri</h1>
              <p className="text-sm text-slate-500 font-medium mt-0.5">Lojistik hareketlerini izleyin ve yönetin</p>
            </div>
          </div>
          <button
            onClick={yukle}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 hover:text-indigo-600 transition-all font-semibold text-sm active:scale-95 disabled:opacity-50 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="sm:hidden lg:inline">Yenile</span>
          </button>
        </div>

        {/* Özet Kartları */}
        {ozet && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <OzetKart label="Toplam Bekleyen" value={ozet.toplam_bekleyen} renk="amber" />
            <OzetKart label="Acil Görevler" value={ozet.acil} renk="red" />
            <OzetKart label="Yüksek Öncelikli" value={ozet.yuksek_oncelikli} renk="orange" />
            <OzetKart label="Normal Öncelikli" value={ozet.normal} renk="indigo" />
          </div>
        )}

        {/* Araç Çubuğu (Filtreler & Konumsuz Görevler) */}
        <div className="bg-white rounded-2xl border border-slate-200 p-2 shadow-sm flex flex-col xl:flex-row gap-4 justify-between items-start xl:items-center">
          
          {/* Mobil Uyumlu Scrollable Filtre */}
          <div className="w-full xl:w-auto overflow-x-auto pb-2 xl:pb-0 hide-scrollbar -mb-2 xl:mb-0">
            <div className="flex gap-2 p-1">
              {FILTRE_SEÇENEKLERI.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setFiltre(opt.id)}
                  className={`relative shrink-0 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    filtre === opt.id
                      ? 'bg-slate-900 text-white shadow-md'
                      : 'bg-transparent text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Konumsuz Görev Aksiyonu */}
          <div className="flex flex-col sm:flex-row gap-3 w-full xl:w-auto p-1 border-t xl:border-t-0 border-slate-100 pt-3 xl:pt-1">
            <div className="relative w-full sm:w-64">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <select
                value={seciliDepo}
                onChange={(e) => setSeciliDepo(e.target.value)}
                className="w-full pl-9 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors appearance-none cursor-pointer"
              >
                <option value="">Depo Seçiniz...</option>
                {depolar.map((d) => <option key={d.id} value={d.id}>{d.isim}</option>)}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
            <button
              onClick={bilinmeyenGörevlerOlustur}
              disabled={bilinmeyenYukleniyor || !seciliDepo}
              className="w-full sm:w-auto flex items-center justify-center px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl transition-all active:scale-95 disabled:opacity-50 shadow-sm text-sm"
            >
              {bilinmeyenYukleniyor ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Konumsuz Görev Aç'}
            </button>
          </div>
        </div>

        {/* Veri Listesi - Responsive Grid Yapısı */}
        <div className="space-y-4">
          {loading && gorevler.length === 0 ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-20 bg-white/60 border border-slate-100 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : gorevler.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-3xl text-center py-24 px-4 shadow-sm">
              <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
                <Inbox className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Görev Bulunamadı</h3>
              <p className="text-slate-500 text-sm max-w-sm mx-auto">Seçili filtrelere uygun herhangi bir yerleştirme görevi şu anda mevcut değil.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-3 lg:bg-white lg:border lg:border-slate-200 lg:rounded-2xl lg:shadow-sm overflow-hidden">
              
              {/* Masaüstü Başlıklar (Mobilde Gizli) */}
              <div className="hidden lg:grid grid-cols-[auto_1fr_1.5fr_1fr_1fr_1fr_1fr_minmax(180px,auto)] gap-4 p-4 bg-slate-50/80 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider items-center">
                <div className="w-8"></div>
                <div>Görev ID</div>
                <div>Durum</div>
                <div>İşlem Tipi</div>
                <div>Palet ID</div>
                <div>Öncelik</div>
                <div>Oluşturma</div>
                <div className="text-center">İşlem</div>
              </div>

              {/* Satırlar / Kartlar */}
              <div className="flex flex-col gap-3 lg:gap-0 lg:divide-y lg:divide-slate-100">
                {gorevler.map((g) => {
                  const isExpanded = acikSatirId === g.id;

                  return (
                    <div 
                      key={g.id} 
                      className={`bg-white border border-slate-200 rounded-2xl lg:rounded-none lg:border-none overflow-hidden transition-all duration-200 ${isExpanded ? 'ring-2 ring-indigo-500/20 shadow-md lg:ring-0 lg:shadow-none lg:bg-indigo-50/30' : 'hover:border-slate-300 lg:hover:bg-slate-50 shadow-sm lg:shadow-none'}`}
                    >
                      {/* Ana Satır İçeriği */}
                      <div 
                        onClick={() => setAcikSatirId(isExpanded ? null : g.id)}
                        className="p-4 lg:p-4 lg:grid lg:grid-cols-[auto_1fr_1.5fr_1fr_1fr_1fr_1fr_minmax(180px,auto)] gap-4 items-center cursor-pointer select-none"
                      >
                        {/* 1. Mobil Header & Toggle */}
                        <div className="flex justify-between items-center lg:block mb-3 lg:mb-0">
                          <div className="flex items-center gap-3 lg:hidden">
                            <span className="font-mono text-sm font-bold text-slate-900 px-2 py-1 bg-slate-100 rounded-lg">#{g.id}</span>
                            <span className={`text-xs font-bold ${g.oncelik === 1 ? 'text-rose-600' : g.oncelik === 2 ? 'text-amber-600' : 'text-slate-500'}`}>
                              {g.oncelik === 1 ? '🔥 ACİL' : g.oncelik === 2 ? '⚡ Yüksek' : 'Normal'}
                            </span>
                          </div>
                          <div className="lg:w-8 flex items-center justify-center shrink-0">
                            <div className={`p-1.5 rounded-full transition-colors ${isExpanded ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-50 text-slate-400 group-hover:bg-slate-100'}`}>
                              <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? '-rotate-180' : ''}`} />
                            </div>
                          </div>
                        </div>

                        {/* 2. Desktop ID (Mobilde gizli) */}
                        <div className="hidden lg:block font-mono text-sm font-bold text-slate-800">
                          #{g.id}
                        </div>

                        {/* 3. Durum & Tip (Mobilde yan yana flex) */}
                        <div className="flex flex-wrap items-center gap-2 mb-3 lg:mb-0 lg:col-span-2 lg:grid lg:grid-cols-[1.5fr_1fr] lg:gap-4">
                          <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border ${DURUM_RENK[g.durum] || 'bg-slate-100 text-slate-600'}`}>
                            {DURUM_IKON[g.durum]}
                            {g.durum}
                          </span>
                          <span className={`inline-flex items-center text-xs font-bold px-3 py-1.5 rounded-xl ring-1 ring-inset ${TIP_RENK[g.tip] || 'bg-slate-50 text-slate-600 ring-slate-200'}`}>
                            {g.tip}
                          </span>
                        </div>

                        {/* 4. Palet ID */}
                        <div className="grid grid-cols-2 lg:block gap-2 mb-2 lg:mb-0 text-sm">
                          <span className="text-slate-500 lg:hidden text-xs font-medium">Palet ID</span>
                          <div className="flex items-center gap-2 text-slate-700 font-semibold truncate">
                            <Package className="w-4 h-4 text-slate-400 shrink-0 hidden lg:block" />
                            {g.palet_id}
                          </div>
                        </div>

                        {/* 5. Öncelik (Desktop) */}
                        <div className="hidden lg:block">
                          <span className={`text-xs font-bold px-2 py-1 rounded-md ${g.oncelik === 1 ? 'bg-rose-50 text-rose-700' : g.oncelik === 2 ? 'bg-amber-50 text-amber-700' : 'text-slate-500'}`}>
                            {g.oncelik === 1 ? 'ACİL' : g.oncelik === 2 ? 'Yüksek' : 'Normal'}
                          </span>
                        </div>

                        {/* 6. Tarih */}
                        <div className="grid grid-cols-2 lg:block gap-2 mb-3 lg:mb-0 text-sm">
                          <span className="text-slate-500 lg:hidden text-xs font-medium">Oluşturma</span>
                          <span className="text-slate-600 font-medium">
                            {new Date(g.olusturma_tarihi).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>

                        {/* 7. Aksiyon Butonları — Durum bazlı */}
                        <div className="mt-4 lg:mt-0 lg:w-auto border-t border-slate-100 pt-3 lg:border-t-0 lg:pt-0" onClick={(e) => e.stopPropagation()}>
                          {g.durum === 'Bekliyor' && (
                            <div className="flex gap-2 w-full lg:w-auto">
                              <button
                                onClick={() => gorevUstlen(g.id)}
                                disabled={aksiyonYukleniyor === g.id}
                                className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 py-2.5 lg:py-2 px-4 rounded-xl font-bold text-xs transition-all shadow-sm shadow-indigo-600/20 disabled:opacity-50"
                              >
                                {aksiyonYukleniyor === g.id ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <UserPlus className="w-3.5 h-3.5" />}
                                Üstlen
                              </button>
                              <button
                                onClick={() => setIptalModal(g.id)}
                                className="flex items-center justify-center gap-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 py-2.5 lg:py-2 px-3 rounded-xl font-bold text-xs transition-colors border border-rose-100"
                              >
                                <X className="w-3.5 h-3.5" />
                                <span className="lg:hidden">İptal</span>
                              </button>
                            </div>
                          )}
                          {g.durum === 'Atandi' && (
                            <div className="flex gap-2 w-full lg:w-auto">
                              <button
                                onClick={() => sahadaBaslat(g)}
                                className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 py-2.5 lg:py-2 px-4 rounded-xl font-bold text-xs transition-all shadow-sm shadow-emerald-600/20"
                              >
                                <Scan className="w-3.5 h-3.5" />
                                Sahaya Git
                              </button>
                              <button
                                onClick={() => gorevBirakAction(g.id)}
                                disabled={aksiyonYukleniyor === g.id}
                                className="flex items-center justify-center gap-1.5 text-amber-700 bg-amber-50 hover:bg-amber-100 py-2.5 lg:py-2 px-3 rounded-xl font-bold text-xs transition-colors border border-amber-200 disabled:opacity-50"
                              >
                                <Undo2 className="w-3.5 h-3.5" />
                                Bırak
                              </button>
                              <button
                                onClick={() => setIptalModal(g.id)}
                                className="flex items-center justify-center gap-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 py-2.5 lg:py-2 px-3 rounded-xl font-bold text-xs transition-colors border border-rose-100"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                          {g.durum === 'DevamEdiyor' && (
                            <div className="flex gap-2 w-full lg:w-auto">
                              <button
                                onClick={() => sahadaBaslat(g)}
                                className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 py-2.5 lg:py-2 px-4 rounded-xl font-bold text-xs transition-all shadow-sm shadow-indigo-600/20"
                              >
                                <Smartphone className="w-3.5 h-3.5" />
                                Terminalde Devam Et
                              </button>
                              <button
                                onClick={() => setIptalModal(g.id)}
                                className="flex items-center justify-center gap-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 py-2.5 lg:py-2 px-3 rounded-xl font-bold text-xs transition-colors border border-rose-100"
                              >
                                <X className="w-3.5 h-3.5" />
                                <span className="lg:hidden">İptal</span>
                              </button>
                            </div>
                          )}
                          {(g.durum === 'Tamamlandi' || g.durum === 'IptalEdildi') && (
                            <div className="flex items-center justify-center gap-1.5 text-slate-400 bg-slate-50 py-2 px-3 rounded-xl font-medium text-xs border border-slate-100">
                              {g.durum === 'Tamamlandi' ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                              {g.durum === 'Tamamlandi' ? 'Tamamlandı' : 'İptal Edildi'}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Genişletilmiş Detay Paneli */}
                      {isExpanded && (
                        <div className="bg-slate-50 border-t border-slate-100 p-4 lg:p-6 animate-in slide-in-from-top-2 duration-200">

                          {/* Palet & Ürün Bilgileri */}
                          {(g.urun_adi || g.palet_barkodu || g.lot_no || g.miktar) && (
                            <div className="mb-6 bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm">
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <Package className="w-3.5 h-3.5" /> Palet & Ürün Bilgisi
                              </h4>
                              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                {g.urun_adi && (
                                  <div className="col-span-2 bg-slate-50 rounded-xl p-3 border border-slate-100">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-0.5">Ürün</span>
                                    <span className="text-sm font-bold text-slate-800">{g.urun_adi}</span>
                                  </div>
                                )}
                                {g.palet_barkodu && (
                                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-0.5">Barkod</span>
                                    <span className="text-sm font-mono font-bold text-blue-700">{g.palet_barkodu}</span>
                                  </div>
                                )}
                                {g.miktar != null && (
                                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-0.5">Miktar</span>
                                    <span className="text-sm font-black text-slate-800">{g.miktar}</span>
                                  </div>
                                )}
                                {g.lot_no && (
                                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-0.5">Lot No</span>
                                    <span className="text-sm font-semibold text-slate-700">{g.lot_no}</span>
                                  </div>
                                )}
                                {g.zone_adi && (
                                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase block mb-0.5">Zon</span>
                                    <span className="text-sm font-semibold text-slate-700">{g.zone_adi}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Görev Detayları */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                            <DetayKarti label="Önerilen Raf" value={g.onerilen_raf_kodu || g.onerilen_raf_id} />
                            <DetayKarti label="Gerçekleşen Raf" value={g.gerceklesen_raf_id} highlight={g.gerceklesen_raf_id != null && g.gerceklesen_raf_id !== g.onerilen_raf_id} />
                            <DetayKarti label="Atanan Kullanıcı" value={g.atanan_kullanici_id} />
                            <DetayKarti label="Override Durumu" value={g.override_kullanici_id ? `Evet (${g.override_kullanici_id})` : 'Hayır'} isWarning={!!g.override_kullanici_id} />
                            
                            {g.override_neden && (
                              <div className="sm:col-span-2 lg:col-span-4 bg-amber-50/50 border border-amber-100 rounded-xl p-3 flex gap-3 items-start">
                                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                <div>
                                  <span className="text-xs font-bold text-amber-800 uppercase tracking-wide">Override Gerekçesi</span>
                                  <p className="text-sm font-medium text-amber-700 mt-1">{g.override_neden}</p>
                                </div>
                              </div>
                            )}

                            {g.iptal_nedeni && (
                              <div className="sm:col-span-2 lg:col-span-4 bg-rose-50/50 border border-rose-100 rounded-xl p-3 flex gap-3 items-start">
                                <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                                <div>
                                  <span className="text-xs font-bold text-rose-800 uppercase tracking-wide">İptal Nedeni</span>
                                  <p className="text-sm font-medium text-rose-700 mt-1">{g.iptal_nedeni}</p>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stilize Edilmiş Modallar */}
      
      {/* İptal Modal */}
      {iptalModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4">
          <div className="bg-white w-full sm:w-[400px] rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
            <div className="p-6">
              <div className="w-12 h-1 bg-slate-200 rounded-full mx-auto mb-6 sm:hidden" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
                  <XCircle className="w-5 h-5 text-rose-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Görevi İptal Et</h3>
              </div>
              <p className="text-sm text-slate-500 mb-4">Bu işlemi geri alamazsınız. Lütfen iptal için geçerli bir neden girin.</p>
              
              <textarea
                className="w-full border border-slate-200 rounded-2xl px-4 py-3 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none bg-slate-50 transition-all"
                rows={4}
                placeholder="Örn: Palet hasarlı, hedef raf dolu..."
                value={iptalNeden}
                onChange={(e) => setIptalNeden(e.target.value)}
              />
              
              <div className="flex flex-col-reverse sm:flex-row gap-3 mt-6">
                <button 
                  onClick={() => setIptalModal(null)} 
                  className="w-full px-4 py-3 border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 rounded-xl font-bold text-sm transition-colors active:scale-95"
                >
                  Vazgeç
                </button>
                <button 
                  onClick={iptalEt} 
                  disabled={loading || !iptalNeden.trim()} 
                  className="w-full px-4 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold text-sm transition-all disabled:opacity-50 active:scale-95 flex justify-center items-center gap-2 shadow-sm shadow-rose-600/20"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'İptali Onayla'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Karantina Modal */}
      {karantinaModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4">
          <div className="bg-white w-full sm:w-[400px] rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
            <div className="p-6">
              <div className="w-12 h-1 bg-slate-200 rounded-full mx-auto mb-6 sm:hidden" />
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${karantinaModal.tip === 'al' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'}`}>
                  {karantinaModal.tip === 'al' ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
                </div>
                <h3 className="text-lg font-bold text-slate-900">
                  {karantinaModal.tip === 'al' ? 'Karantinaya Al' : 'Karantinadan Çıkar'}
                </h3>
              </div>
              
              {karantinaModal.tip === 'al' ? (
                <>
                  <p className="text-sm text-slate-500 mb-4">Paleti karantinaya almak için bir gerekçe belirtmelisiniz.</p>
                  <textarea
                    className="w-full border border-slate-200 rounded-2xl px-4 py-3 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none bg-slate-50 transition-all"
                    rows={4}
                    placeholder="Karantina gerekçesi girin..."
                    value={karantinaNeden}
                    onChange={(e) => setKarantinaNeden(e.target.value)}
                  />
                </>
              ) : (
                <p className="text-sm text-slate-600 mb-4 font-medium">Bu paleti karantinadan çıkarmak istediğinize emin misiniz?</p>
              )}
              
              <div className="flex flex-col-reverse sm:flex-row gap-3 mt-6">
                <button 
                  onClick={() => setKarantinaModal(null)} 
                  className="w-full px-4 py-3 border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 rounded-xl font-bold text-sm transition-colors active:scale-95"
                >
                  Vazgeç
                </button>
                <button 
                  onClick={karantinaIslem} 
                  disabled={loading || (karantinaModal.tip === 'al' && !karantinaNeden.trim())} 
                  className={`w-full px-4 py-3 text-white rounded-xl font-bold text-sm transition-all disabled:opacity-50 active:scale-95 flex justify-center items-center gap-2 shadow-sm ${karantinaModal.tip === 'al' ? 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/20' : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20'}`}
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Onayla'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// Yardımcı Komponentler
function OzetKart({ label, value, renk }) {
  const stiller = {
    amber: 'bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-amber-500/20',
    red: 'bg-gradient-to-br from-rose-500 to-red-600 text-white shadow-rose-500/20',
    orange: 'bg-gradient-to-br from-orange-400 to-amber-500 text-white shadow-orange-500/20',
    indigo: 'bg-gradient-to-br from-indigo-500 to-blue-600 text-white shadow-indigo-500/20',
  };
  
  return (
    <div className={`rounded-2xl p-5 shadow-lg relative overflow-hidden ${stiller[renk]}`}>
      <div className="absolute right-0 top-0 opacity-10 translate-x-4 -translate-y-4">
        <Package className="w-24 h-24" />
      </div>
      <p className="text-sm font-medium opacity-90 mb-1">{label}</p>
      <p className="text-3xl font-black tracking-tight relative z-10">{value ?? '0'}</p>
    </div>
  );
}

function DetayKarti({ label, value, highlight = false, isWarning = false }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">{label}</span>
      <div className={`text-sm font-semibold rounded-lg px-3 py-2 border ${
        isWarning ? 'bg-amber-50 text-amber-700 border-amber-200' 
        : highlight ? 'bg-indigo-50 text-indigo-700 border-indigo-200' 
        : 'bg-white text-slate-800 border-slate-200'
      }`}>
        {value || '—'}
      </div>
    </div>
  );
}