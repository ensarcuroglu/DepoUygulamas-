/**
 * YerlestirmeGorevleriPage — Admin görev takip ve yönetim sayfası.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Package, RefreshCw, X, ChevronDown, AlertTriangle,
  CheckCircle, Clock, XCircle, Search, MapPin, Inbox,
  Filter, Shield, ShieldOff, Activity, BarChart3,
} from 'lucide-react';
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
  Bekliyor:     'bg-amber-100 text-amber-800 border-amber-200',
  Atandi:       'bg-blue-100 text-blue-800 border-blue-200',
  DevamEdiyor:  'bg-indigo-100 text-indigo-800 border-indigo-200',
  Tamamlandi:   'bg-emerald-100 text-emerald-800 border-emerald-200',
  IptalEdildi:  'bg-slate-100 text-slate-600 border-slate-200',
};

const DURUM_IKON = {
  Bekliyor:    <Clock className="w-3.5 h-3.5" />,
  Atandi:      <Clock className="w-3.5 h-3.5" />,
  DevamEdiyor: <RefreshCw className="w-3.5 h-3.5 animate-spin" />,
  Tamamlandi:  <CheckCircle className="w-3.5 h-3.5" />,
  IptalEdildi: <XCircle className="w-3.5 h-3.5" />,
};

const TIP_RENK = {
  Yerlestirme:   'bg-blue-50 text-blue-700 ring-blue-600/20',
  Transfer:      'bg-purple-50 text-purple-700 ring-purple-600/20',
  BelirsizKonum: 'bg-rose-50 text-rose-700 ring-rose-600/20',
};

const DURUM_FILTRELERI = [
  { id: '',             label: 'Tümü' },
  { id: 'Bekliyor',     label: 'Bekliyor' },
  { id: 'Atandi',       label: 'Atandı' },
  { id: 'DevamEdiyor',  label: 'Devam Ediyor' },
  { id: 'Tamamlandi',   label: 'Tamamlandı' },
  { id: 'IptalEdildi',  label: 'İptal Edildi' },
];

const TIP_SECENEKLERI = [
  { id: '',              label: 'Tüm Tipler' },
  { id: 'Yerlestirme',   label: 'Yerleştirme' },
  { id: 'Transfer',      label: 'Transfer' },
  { id: 'BelirsizKonum', label: 'Belirsiz Konum' },
];

const ONCELIK_SECENEKLERI = [
  { id: '',  label: 'Tüm Öncelikler' },
  { id: '1', label: 'Acil' },
  { id: '2', label: 'Yüksek' },
  { id: '3', label: 'Normal' },
];

export default function YerlestirmeGorevleriPage() {
  const { loading, run } = useAsync(true);
  const [gorevler, setGorevler]               = useState([]);
  const [ozet, setOzet]                       = useState(null);
  const [depolar, setDepolar]                 = useState([]);
  const [filtre, setFiltre]                   = useState('');
  const [aramaMetni, setAramaMetni]           = useState('');
  const [filtreTip, setFiltreTip]             = useState('');
  const [filtreOncelik, setFiltreOncelik]     = useState('');
  const [seciliDepo, setSeciliDepo]           = useState('');
  const [adminPaneliAcik, setAdminPaneliAcik] = useState(false);
  const [iptalModal, setIptalModal]           = useState(null);
  const [iptalNeden, setIptalNeden]           = useState('');
  const [karantinaModal, setKarantinaModal]   = useState(null);
  const [karantinaNeden, setKarantinaNeden]   = useState('');
  const [bilinmeyenYukleniyor, setBilinmeyenYukleniyor] = useState(false);
  const [acikSatirId, setAcikSatirId]         = useState(null);

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

  const gorevSayilari = useMemo(() => gorevler.reduce(
    (acc, g) => {
      if (g.durum === 'Atandi')      acc.atandi++;
      else if (g.durum === 'DevamEdiyor') acc.devamEdiyor++;
      else if (g.durum === 'Tamamlandi') acc.tamamlandi++;
      return acc;
    },
    { atandi: 0, devamEdiyor: 0, tamamlandi: 0 }
  ), [gorevler]);

  const filtrelenmisGorevler = useMemo(() => {
    return gorevler.filter(g => {
      const aramaTuttu = !aramaMetni ||
        String(g.id).includes(aramaMetni) ||
        String(g.palet_id).includes(aramaMetni) ||
        (g.urun_adi || '').toLowerCase().includes(aramaMetni.toLowerCase()) ||
        (g.palet_barkodu || '').toLowerCase().includes(aramaMetni.toLowerCase());
      const tipTuttu      = !filtreTip || g.tip === filtreTip;
      const oncelikTuttu  = !filtreOncelik || String(g.oncelik) === filtreOncelik;
      return aramaTuttu && tipTuttu && oncelikTuttu;
    });
  }, [gorevler, aramaMetni, filtreTip, filtreOncelik]);

  const aktifFiltreler = aramaMetni || filtreTip || filtreOncelik;

  const filtreleriTemizle = () => {
    setAramaMetni('');
    setFiltreTip('');
    setFiltreOncelik('');
    setFiltre('');
  };

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

  const bilinmeyenGorevlerOlustur = async () => {
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
    <div className="min-h-screen bg-slate-50/50 pb-12">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-5">

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

        {ozet && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Bekleyen Havuz — Öncelik Dağılımı</span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <OzetKart label="Toplam Bekleyen" value={ozet.toplam_bekleyen} renk="amber"   ikon={<Clock className="w-5 h-5" />} />
              <OzetKart label="Acil Görevler"   value={ozet.acil}            renk="red"     ikon={<AlertTriangle className="w-5 h-5" />} />
              <OzetKart label="Yüksek Öncelikli" value={ozet.yuksek_oncelikli} renk="orange" ikon={<Activity className="w-5 h-5" />} />
              <OzetKart label="Normal Öncelikli" value={ozet.normal}          renk="indigo"  ikon={<Package className="w-5 h-5" />} />
            </div>
          </div>
        )}

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Anlık Durum (Yüklü Liste)</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <DurumKart label="Atandı"       value={gorevSayilari.atandi}      renk="blue" />
            <DurumKart label="Devam Ediyor" value={gorevSayilari.devamEdiyor} renk="indigo" />
            <DurumKart label="Tamamlandı"   value={gorevSayilari.tamamlandi}  renk="emerald" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

          {/* Filtreler Satırı */}
          <div className="p-3 flex flex-col lg:flex-row gap-3 items-start lg:items-center">

            {/* Arama */}
            <div className="relative w-full lg:w-72 shrink-0">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={aramaMetni}
                onChange={(e) => setAramaMetni(e.target.value)}
                placeholder="Görev ID, Palet ID, Ürün adı..."
                className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors placeholder:text-slate-400"
              />
            </div>

            {/* Durum Pill Filtreleri */}
            <div className="flex-1 w-full overflow-x-auto hide-scrollbar">
              <div className="flex gap-1.5 pb-0.5">
                {DURUM_FILTRELERI.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setFiltre(opt.id)}
                    className={`shrink-0 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                      filtre === opt.id
                        ? 'bg-slate-900 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tip & Öncelik Select */}
            <div className="flex gap-2 shrink-0 w-full lg:w-auto">
              <div className="relative flex-1 lg:w-44">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                <select
                  value={filtreTip}
                  onChange={(e) => setFiltreTip(e.target.value)}
                  className="w-full pl-8 pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors appearance-none cursor-pointer"
                >
                  {TIP_SECENEKLERI.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
              </div>
              <div className="relative flex-1 lg:w-44">
                <select
                  value={filtreOncelik}
                  onChange={(e) => setFiltreOncelik(e.target.value)}
                  className="w-full pl-3 pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors appearance-none cursor-pointer"
                >
                  {ONCELIK_SECENEKLERI.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Admin İşlemleri — Collapsible */}
          <div className="border-t border-slate-100">
            <button
              onClick={() => setAdminPaneliAcik(v => !v)}
              className="w-full flex items-center gap-2 px-4 py-2.5 text-xs font-bold text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${adminPaneliAcik ? '-rotate-180' : ''}`} />
              Admin İşlemleri — Konumsuz Görev Oluştur
            </button>
            {adminPaneliAcik && (
              <div className="px-4 pb-4 flex flex-col sm:flex-row gap-3">
                <div className="relative sm:w-64">
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
                  onClick={bilinmeyenGorevlerOlustur}
                  disabled={bilinmeyenYukleniyor || !seciliDepo}
                  className="flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl transition-all active:scale-95 disabled:opacity-50 shadow-sm text-sm"
                >
                  {bilinmeyenYukleniyor
                    ? <RefreshCw className="w-4 h-4 animate-spin" />
                    : 'Konumsuz Görev Aç'}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-3">
          {/* Sonuç Sayısı */}
          {!loading && gorevler.length > 0 && (
            <div className="flex items-center justify-between px-1">
              <span className="text-xs text-slate-500 font-medium">
                {filtrelenmisGorevler.length === gorevler.length
                  ? `${gorevler.length} görev`
                  : `${filtrelenmisGorevler.length} / ${gorevler.length} görev gösteriliyor`}
              </span>
              {aktifFiltreler && (
                <button
                  onClick={filtreleriTemizle}
                  className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> Filtreleri Temizle
                </button>
              )}
            </div>
          )}

          {loading && gorevler.length === 0 ? (
            <div className="space-y-2.5">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-16 bg-white border border-slate-100 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : filtrelenmisGorevler.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-3xl text-center py-20 px-4 shadow-sm">
              <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
                <Inbox className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Görev Bulunamadı</h3>
              <p className="text-slate-500 text-sm max-w-sm mx-auto mb-4">
                Seçili filtrelere uygun herhangi bir yerleştirme görevi şu anda mevcut değil.
              </p>
              {aktifFiltreler && (
                <button
                  onClick={filtreleriTemizle}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white font-bold text-sm rounded-xl hover:bg-indigo-700 transition-colors"
                >
                  <X className="w-3.5 h-3.5" /> Filtreleri Temizle
                </button>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-2.5 lg:bg-white lg:border lg:border-slate-200 lg:rounded-2xl lg:shadow-sm overflow-hidden">

              {/* Masaüstü Tablo Başlığı */}
              <div className="hidden lg:grid grid-cols-[auto_80px_1.6fr_1fr_0.8fr_0.8fr_0.8fr_160px] gap-4 px-4 py-3 bg-slate-50/80 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <div className="w-8" />
                <div>ID</div>
                <div>Durum / Tip</div>
                <div>Palet</div>
                <div>Atanan</div>
                <div>Öncelik</div>
                <div>Tarih</div>
                <div className="text-center">İşlem</div>
              </div>

              <div className="flex flex-col gap-2.5 lg:gap-0 lg:divide-y lg:divide-slate-100 lg:pb-0 pb-0">
                {filtrelenmisGorevler.map((g) => {
                  const isExpanded = acikSatirId === g.id;
                  const aktif = ['Bekliyor', 'Atandi', 'DevamEdiyor'].includes(g.durum);

                  return (
                    <div
                      key={g.id}
                      className={`bg-white border border-slate-200 rounded-2xl lg:rounded-none lg:border-none overflow-hidden transition-all duration-200 ${
                        isExpanded
                          ? 'ring-2 ring-indigo-500/20 shadow-md lg:ring-0 lg:shadow-none lg:bg-indigo-50/20'
                          : 'hover:border-slate-300 lg:hover:bg-slate-50/60 shadow-sm lg:shadow-none'
                      }`}
                    >
                      {/* Ana Satır */}
                      <div
                        onClick={() => setAcikSatirId(isExpanded ? null : g.id)}
                        className="p-4 lg:grid lg:grid-cols-[auto_80px_1.6fr_1fr_0.8fr_0.8fr_0.8fr_160px] gap-4 items-center cursor-pointer select-none"
                      >
                        {/* Toggle / Mobil Header */}
                        <div className="flex justify-between items-center lg:block mb-3 lg:mb-0">
                          <div className="flex items-center gap-3 lg:hidden">
                            <span className="font-mono text-sm font-bold text-slate-900 px-2 py-1 bg-slate-100 rounded-lg">#{g.id}</span>
                            <span className={`text-xs font-bold ${g.oncelik === 1 ? 'text-rose-600' : g.oncelik === 2 ? 'text-amber-600' : 'text-slate-500'}`}>
                              {g.oncelik === 1 ? '🔥 ACİL' : g.oncelik === 2 ? '⚡ Yüksek' : 'Normal'}
                            </span>
                          </div>
                          <div className="lg:w-8 flex items-center justify-center shrink-0">
                            <div className={`p-1.5 rounded-full transition-colors ${isExpanded ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-50 text-slate-400'}`}>
                              <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? '-rotate-180' : ''}`} />
                            </div>
                          </div>
                        </div>

                        {/* ID (Desktop) */}
                        <div className="hidden lg:block font-mono text-sm font-bold text-slate-800">
                          #{g.id}
                        </div>

                        {/* Durum + Tip */}
                        <div className="flex flex-wrap items-center gap-2 mb-3 lg:mb-0">
                          <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1.5 rounded-xl border ${DURUM_RENK[g.durum] || 'bg-slate-100 text-slate-600'}`}>
                            {DURUM_IKON[g.durum]}
                            {g.durum}
                          </span>
                          <span className={`inline-flex items-center text-xs font-bold px-2.5 py-1.5 rounded-xl ring-1 ring-inset ${TIP_RENK[g.tip] || 'bg-slate-50 text-slate-600 ring-slate-200'}`}>
                            {g.tip}
                          </span>
                        </div>

                        {/* Palet ID */}
                        <div className="grid grid-cols-2 lg:block gap-2 mb-2 lg:mb-0 text-sm">
                          <span className="text-slate-500 lg:hidden text-xs font-medium">Palet</span>
                          <div className="flex items-center gap-2 text-slate-700 font-semibold truncate">
                            <Package className="w-4 h-4 text-slate-400 shrink-0 hidden lg:block" />
                            {g.palet_id}
                          </div>
                        </div>

                        {/* Atanan */}
                        <div className="grid grid-cols-2 lg:block gap-2 mb-2 lg:mb-0">
                          <span className="text-slate-500 lg:hidden text-xs font-medium">Atanan</span>
                          <span className="text-xs font-semibold text-slate-600 truncate">
                            {g.atanan_kullanici_id ?? <span className="text-slate-400 italic">Atanmadı</span>}
                          </span>
                        </div>

                        {/* Öncelik (Desktop) */}
                        <div className="hidden lg:block">
                          <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                            g.oncelik === 1 ? 'bg-rose-50 text-rose-700'
                            : g.oncelik === 2 ? 'bg-amber-50 text-amber-700'
                            : 'bg-slate-50 text-slate-500'
                          }`}>
                            {g.oncelik === 1 ? 'ACİL' : g.oncelik === 2 ? 'Yüksek' : 'Normal'}
                          </span>
                        </div>

                        {/* Tarih */}
                        <div className="grid grid-cols-2 lg:block gap-2 mb-3 lg:mb-0 text-sm">
                          <span className="text-slate-500 lg:hidden text-xs font-medium">Tarih</span>
                          <span className="text-slate-600 font-medium text-xs">
                            {new Date(g.olusturma_tarihi).toLocaleDateString('tr-TR', {
                              day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
                            })}
                          </span>
                        </div>

                        {/* Aksiyon — Admin için sadece İptal Et */}
                        <div
                          className="mt-3 lg:mt-0 border-t border-slate-100 pt-3 lg:border-t-0 lg:pt-0 flex justify-center"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {aktif ? (
                            <button
                              onClick={() => setIptalModal(g.id)}
                              className="flex items-center justify-center gap-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 py-2 px-4 rounded-xl font-bold text-xs transition-colors border border-rose-100 w-full lg:w-auto"
                            >
                              <X className="w-3.5 h-3.5" />
                              İptal Et
                            </button>
                          ) : (
                            <div className="flex items-center justify-center gap-1.5 text-slate-400 bg-slate-50 py-2 px-3 rounded-xl font-medium text-xs border border-slate-100 w-full lg:w-auto">
                              {g.durum === 'Tamamlandi'
                                ? <><CheckCircle className="w-3.5 h-3.5" /> Tamamlandı</>
                                : <><XCircle className="w-3.5 h-3.5" /> İptal Edildi</>}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Genişletilmiş Detay Paneli */}
                      {isExpanded && (
                        <div className="bg-slate-50/80 border-t border-slate-100 p-4 lg:p-6 animate-in slide-in-from-top-2 duration-200 space-y-5">

                          {/* Palet & Ürün Bilgileri */}
                          {(g.urun_adi || g.palet_barkodu || g.lot_no || g.miktar) && (
                            <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm">
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
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <DetayKarti label="Önerilen Raf"    value={g.onerilen_raf_kodu || g.onerilen_raf_id} />
                            <DetayKarti label="Gerçekleşen Raf" value={g.gerceklesen_raf_id} highlight={g.gerceklesen_raf_id != null && g.gerceklesen_raf_id !== g.onerilen_raf_id} />
                            <DetayKarti label="Atanan Kullanıcı" value={g.atanan_kullanici_id} />
                            <DetayKarti label="Override"        value={g.override_kullanici_id ? `Evet (${g.override_kullanici_id})` : 'Hayır'} isWarning={!!g.override_kullanici_id} />

                            {g.override_neden && (
                              <div className="col-span-2 sm:col-span-4 bg-amber-50/50 border border-amber-100 rounded-xl p-3 flex gap-3 items-start">
                                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                <div>
                                  <span className="text-xs font-bold text-amber-800 uppercase tracking-wide">Override Gerekçesi</span>
                                  <p className="text-sm font-medium text-amber-700 mt-1">{g.override_neden}</p>
                                </div>
                              </div>
                            )}

                            {g.iptal_nedeni && (
                              <div className="col-span-2 sm:col-span-4 bg-rose-50/50 border border-rose-100 rounded-xl p-3 flex gap-3 items-start">
                                <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                                <div>
                                  <span className="text-xs font-bold text-rose-800 uppercase tracking-wide">İptal Nedeni</span>
                                  <p className="text-sm font-medium text-rose-700 mt-1">{g.iptal_nedeni}</p>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Karantina İşlemleri */}
                          <div className="pt-4 border-t border-slate-200">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                              <Shield className="w-3.5 h-3.5" /> Karantina İşlemleri
                            </h4>
                            <div className="flex flex-col sm:flex-row gap-2" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={() => setKarantinaModal({ tip: 'al', paletId: g.palet_id })}
                                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-50 hover:bg-amber-100 text-amber-700 font-bold text-xs rounded-xl border border-amber-200 transition-colors"
                              >
                                <Shield className="w-3.5 h-3.5" /> Karantinaya Al
                              </button>
                              <button
                                onClick={() => setKarantinaModal({ tip: 'cikar', paletId: g.palet_id })}
                                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-xs rounded-xl border border-emerald-200 transition-colors"
                              >
                                <ShieldOff className="w-3.5 h-3.5" /> Karantinadan Çıkar
                              </button>
                            </div>
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
                  onClick={() => { setIptalModal(null); setIptalNeden(''); }}
                  className="w-full px-4 py-3 border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 rounded-xl font-bold text-sm transition-colors"
                >
                  Vazgeç
                </button>
                <button
                  onClick={iptalEt}
                  disabled={loading || !iptalNeden.trim()}
                  className="w-full px-4 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold text-sm transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-sm shadow-rose-600/20"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'İptali Onayla'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {karantinaModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4">
          <div className="bg-white w-full sm:w-[400px] rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200">
            <div className="p-6">
              <div className="w-12 h-1 bg-slate-200 rounded-full mx-auto mb-6 sm:hidden" />
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${karantinaModal.tip === 'al' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'}`}>
                  {karantinaModal.tip === 'al' ? <Shield className="w-5 h-5" /> : <ShieldOff className="w-5 h-5" />}
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
                  onClick={() => { setKarantinaModal(null); setKarantinaNeden(''); }}
                  className="w-full px-4 py-3 border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 rounded-xl font-bold text-sm transition-colors"
                >
                  Vazgeç
                </button>
                <button
                  onClick={karantinaIslem}
                  disabled={loading || (karantinaModal.tip === 'al' && !karantinaNeden.trim())}
                  className={`w-full px-4 py-3 text-white rounded-xl font-bold text-sm transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-sm ${
                    karantinaModal.tip === 'al'
                      ? 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/20'
                      : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20'
                  }`}
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

function OzetKart({ label, value, renk, ikon }) {
  const stiller = {
    amber:   'from-amber-500 to-orange-500 shadow-amber-500/20',
    red:     'from-rose-500 to-red-600 shadow-rose-500/20',
    orange:  'from-orange-400 to-amber-500 shadow-orange-500/20',
    indigo:  'from-indigo-500 to-blue-600 shadow-indigo-500/20',
  };
  return (
    <div className={`rounded-2xl p-5 shadow-lg relative overflow-hidden bg-gradient-to-br text-white ${stiller[renk]}`}>
      <div className="absolute right-3 top-3 opacity-20">{ikon}</div>
      <p className="text-xs font-semibold opacity-90 mb-1.5 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-black tracking-tight">{value ?? '0'}</p>
    </div>
  );
}

function DurumKart({ label, value, renk }) {
  const stiller = {
    blue:    'bg-blue-50 border-blue-100 text-blue-700',
    indigo:  'bg-indigo-50 border-indigo-100 text-indigo-700',
    emerald: 'bg-emerald-50 border-emerald-100 text-emerald-700',
  };
  return (
    <div className={`rounded-2xl p-4 border ${stiller[renk]} flex items-center justify-between`}>
      <span className="text-sm font-semibold">{label}</span>
      <span className="text-2xl font-black">{value}</span>
    </div>
  );
}

function DetayKarti({ label, value, highlight = false, isWarning = false }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">{label}</span>
      <div className={`text-sm font-semibold rounded-lg px-3 py-2 border ${
        isWarning  ? 'bg-amber-50 text-amber-700 border-amber-200'
        : highlight ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
        : 'bg-white text-slate-800 border-slate-200'
      }`}>
        {value || '—'}
      </div>
    </div>
  );
}
