/**
 * YerlestirmeGorevleriPage — Admin görev takip ve yönetim sayfası.
 * UX/UI İyileştirilmiş Versiyon: Gelişmiş kontrast, belirgin satır ayrımları, temiz hiyerarşi.
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

/* ═══════════════════════════════════════════════════
   SABIT TANIMLAMALAR (Değiştirilmedi)
   ═══════════════════════════════════════════════════ */

const DURUM_RENK = {
  Bekliyor:    'bg-amber-50 text-amber-700 border-amber-200/60',
  Atandi:      'bg-sky-50 text-sky-700 border-sky-200/60',
  DevamEdiyor: 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
  Tamamlandi:  'bg-emerald-50 text-emerald-700 border-emerald-200/60',
  IptalEdildi: 'bg-slate-100 text-slate-500 border-slate-200/60',
};

const DURUM_IKON = {
  Bekliyor:    <Clock className="w-3 h-3" />,
  Atandi:      <Clock className="w-3 h-3" />,
  DevamEdiyor: <RefreshCw className="w-3 h-3 animate-spin" />,
  Tamamlandi:  <CheckCircle className="w-3 h-3" />,
  IptalEdildi: <XCircle className="w-3 h-3" />,
};

const TIP_RENK = {
  Yerlestirme:   'bg-blue-50 text-blue-600 ring-blue-500/10',
  Transfer:      'bg-violet-50 text-violet-600 ring-violet-500/10',
  BelirsizKonum: 'bg-rose-50 text-rose-600 ring-rose-500/10',
};

const DURUM_FILTRELERI = [
  { id: '',            label: 'Tümü' },
  { id: 'Bekliyor',    label: 'Bekliyor' },
  { id: 'Atandi',      label: 'Atandı' },
  { id: 'DevamEdiyor', label: 'Devam Ediyor' },
  { id: 'Tamamlandi',  label: 'Tamamlandı' },
  { id: 'IptalEdildi', label: 'İptal Edildi' },
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

const ONCELIK_GORSEL = {
  1: { label: 'ACİL',   dot: 'bg-rose-500',  text: 'text-rose-700', bg: 'bg-rose-50' },
  2: { label: 'Yüksek', dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50' },
  3: { label: 'Normal', dot: 'bg-slate-400', text: 'text-slate-500', bg: 'bg-slate-50' },
};

/* ═══════════════════════════════════════════════════
   ANA SAYFA BİLEŞENİ
   ═══════════════════════════════════════════════════ */

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

  /* ─── Veri Yükleme ─── */
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

  /* ─── Hesaplamalar ─── */
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
    const aramaLower = aramaMetni.toLowerCase();
    return gorevler.filter(g => {
      if (aramaMetni) {
        const idStr = String(g.id);
        const paletStr = String(g.palet_id);
        const urun = (g.urun_adi || '').toLowerCase();
        const barkod = (g.palet_barkodu || '').toLowerCase();
        if (!idStr.includes(aramaMetni) && !paletStr.includes(aramaMetni) && !urun.includes(aramaLower) && !barkod.includes(aramaLower)) return false;
      }
      if (filtreTip && g.tip !== filtreTip) return false;
      if (filtreOncelik && String(g.oncelik) !== filtreOncelik) return false;
      return true;
    });
  }, [gorevler, aramaMetni, filtreTip, filtreOncelik]);

  const aktifFiltreler = aramaMetni || filtreTip || filtreOncelik;

  const filtreleriTemizle = () => {
    setAramaMetni('');
    setFiltreTip('');
    setFiltreOncelik('');
    setFiltre('');
  };

  /* ─── İşlemler (İptal, Karantina, vs.) ─── */
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
    <div className="min-h-screen bg-slate-50/50 pb-16">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">

        {/* ━━━ Başlık Alanı ━━━ */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/20">
              <Package className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                Yerleştirme Görevleri
              </h1>
              <p className="text-sm text-slate-500 font-medium mt-0.5">
                Lojistik hareketlerini izleyin ve detaylı yönetin
              </p>
            </div>
          </div>
          <button
            onClick={yukle}
            disabled={loading}
            className="self-start sm:self-auto px-4 py-2 flex items-center gap-2 bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 active:scale-95 transition-all disabled:opacity-50 shadow-sm font-semibold text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Yenile
          </button>
        </header>

        {/* ━━━ Özet Kartları ━━━ */}
        {ozet && (
          <section className="space-y-3">
            <SectionLabel icon={<BarChart3 className="w-4 h-4" />} text="Bekleyen Havuz Özeti" />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <OzetKart label="Toplam Bekleyen" value={ozet.toplam_bekleyen} variant="amber"  icon={<Clock className="w-6 h-6" />} />
              <OzetKart label="Acil"            value={ozet.acil}            variant="rose"   icon={<AlertTriangle className="w-6 h-6" />} />
              <OzetKart label="Yüksek"          value={ozet.yuksek_oncelikli} variant="orange" icon={<Activity className="w-6 h-6" />} />
              <OzetKart label="Normal"          value={ozet.normal}          variant="indigo" icon={<Package className="w-6 h-6" />} />
            </div>
          </section>
        )}

        {/* ━━━ Anlık Durum ━━━ */}
        <section className="space-y-3">
          <SectionLabel icon={<Activity className="w-4 h-4" />} text="İşlemdeki Görevler" />
          <div className="grid grid-cols-3 gap-3 sm:gap-4">
            <DurumKart label="Atandı"       value={gorevSayilari.atandi}      variant="sky" />
            <DurumKart label="Devam Ediyor" value={gorevSayilari.devamEdiyor} variant="indigo" />
            <DurumKart label="Tamamlandı"   value={gorevSayilari.tamamlandi}  variant="emerald" />
          </div>
        </section>

        {/* ━━━ Filtre ve Arama Alanı ━━━ */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 space-y-4">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={aramaMetni}
                  onChange={(e) => setAramaMetni(e.target.value)}
                  placeholder="ID, Palet, Ürün adı veya barkod ile ara..."
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 focus:bg-white transition-all placeholder:text-slate-400"
                />
              </div>
              <div className="flex gap-3">
                <SelectField icon={<Filter className="w-4 h-4" />} value={filtreTip} onChange={setFiltreTip} options={TIP_SECENEKLERI} />
                <SelectField value={filtreOncelik} onChange={setFiltreOncelik} options={ONCELIK_SECENEKLERI} />
              </div>
            </div>

            <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-1">
              {DURUM_FILTRELERI.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setFiltre(opt.id)}
                  className={`shrink-0 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    filtre === opt.id
                      ? 'bg-slate-800 text-white shadow-md shadow-slate-800/20'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Admin Paneli */}
          <div className="border-t border-slate-100 bg-slate-50/50">
            <button
              onClick={() => setAdminPaneliAcik(v => !v)}
              className="w-full flex items-center gap-2 px-4 py-3 text-sm font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${adminPaneliAcik ? '-rotate-180' : ''}`} />
              Konumsuz Görev Oluştur (Admin)
            </button>
            {adminPaneliAcik && (
              <div className="px-4 pb-4 pt-1 flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1 sm:max-w-[280px]">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <select
                    value={seciliDepo}
                    onChange={(e) => setSeciliDepo(e.target.value)}
                    className="w-full pl-9 pr-8 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 appearance-none cursor-pointer"
                  >
                    <option value="">Depo Seçiniz...</option>
                    {depolar.map((d) => <option key={d.id} value={d.id}>{d.isim}</option>)}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
                <button
                  onClick={bilinmeyenGorevlerOlustur}
                  disabled={bilinmeyenYukleniyor || !seciliDepo}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm transition-all active:scale-[0.98] disabled:opacity-50 shadow-sm"
                >
                  {bilinmeyenYukleniyor ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Görevleri Oluştur'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* ━━━ Görev Listesi ━━━ */}
        <section className="space-y-3">
          {!loading && gorevler.length > 0 && (
            <div className="flex items-center justify-between px-1">
              <span className="text-sm text-slate-500 font-medium">
                {filtrelenmisGorevler.length === gorevler.length
                  ? `Toplam ${gorevler.length} görev listeleniyor`
                  : `${gorevler.length} görevden ${filtrelenmisGorevler.length} tanesi gösteriliyor`}
              </span>
              {aktifFiltreler && (
                <button onClick={filtreleriTemizle} className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 transition-colors">
                  <X className="w-4 h-4" /> Filtreleri Temizle
                </button>
              )}
            </div>
          )}

          {loading && gorevler.length === 0 ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }, (_, i) => (
                <div key={i} className="h-16 bg-white border border-slate-200 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : filtrelenmisGorevler.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-3xl text-center py-20 px-6 shadow-sm">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-5">
                <Inbox className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-2">Görev Bulunamadı</h3>
              <p className="text-slate-500 text-sm max-w-sm mx-auto mb-6">Seçtiğiniz kriterlere uygun görev kaydı bulunmuyor.</p>
              {aktifFiltreler && (
                <button onClick={filtreleriTemizle} className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white font-semibold text-sm rounded-xl hover:bg-slate-800 transition-all shadow-md">
                  <X className="w-4 h-4" /> Filtreleri Temizle
                </button>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              {/* Daha okunaklı Header */}
              <div className="hidden lg:grid grid-cols-[40px_70px_1.4fr_1fr_0.8fr_0.8fr_0.8fr_120px] gap-4 px-5 py-3.5 bg-slate-100/60 border-b border-slate-200 text-xs font-bold text-slate-600 uppercase tracking-wider">
                <div />
                <div>ID</div>
                <div>Durum / Tip</div>
                <div>LPN</div>
                <div>Atanan</div>
                <div>Öncelik</div>
                <div>Tarih</div>
                <div className="text-right pr-4">İşlem</div>
              </div>

              {/* Satırları bölen kapsayıcı (divide-y yerine satır içinde border-b kullanıyoruz) */}
              <div className="flex flex-col">
                {filtrelenmisGorevler.map((g) => (
                  <GorevSatiri
                    key={g.id}
                    g={g}
                    isExpanded={acikSatirId === g.id}
                    onToggle={() => setAcikSatirId(acikSatirId === g.id ? null : g.id)}
                    onIptal={() => setIptalModal(g.id)}
                    onKarantinaAl={() => setKarantinaModal({ tip: 'al', paletId: g.palet_id })}
                    onKarantinaCikar={() => setKarantinaModal({ tip: 'cikar', paletId: g.palet_id })}
                  />
                ))}
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Modallar (Değiştirilmedi) */}
      {iptalModal && (
        <Modal onClose={() => { setIptalModal(null); setIptalNeden(''); }}>
          <ModalHeader icon={<XCircle className="w-6 h-6" />} iconBg="bg-rose-100 text-rose-600" title="Görevi İptal Et" />
          <p className="text-sm text-slate-500 mb-4">Bu işlemi geri alamazsınız. Lütfen iptal nedeni girin.</p>
          <textarea
            className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-400 resize-none bg-slate-50/50 transition-all"
            rows={3}
            placeholder="Örn: Palet hasarlı, hedef raf dolu..."
            value={iptalNeden}
            onChange={(e) => setIptalNeden(e.target.value)}
          />
          <ModalActions
            onCancel={() => { setIptalModal(null); setIptalNeden(''); }}
            onConfirm={iptalEt}
            confirmLabel="İptali Onayla"
            confirmClass="bg-rose-600 hover:bg-rose-700 text-white"
            disabled={loading || !iptalNeden.trim()}
            loading={loading}
          />
        </Modal>
      )}

      {karantinaModal && (
        <Modal onClose={() => { setKarantinaModal(null); setKarantinaNeden(''); }}>
          <ModalHeader
            icon={karantinaModal.tip === 'al' ? <Shield className="w-6 h-6" /> : <ShieldOff className="w-6 h-6" />}
            iconBg={karantinaModal.tip === 'al' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'}
            title={karantinaModal.tip === 'al' ? 'Karantinaya Al' : 'Karantinadan Çıkar'}
          />
          {karantinaModal.tip === 'al' ? (
            <>
              <p className="text-sm text-slate-500 mb-4">Paleti karantinaya almak için gerekçe belirtmelisiniz.</p>
              <textarea
                className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-400 resize-none bg-slate-50/50 transition-all"
                rows={3}
                placeholder="Karantina gerekçesi girin..."
                value={karantinaNeden}
                onChange={(e) => setKarantinaNeden(e.target.value)}
              />
            </>
          ) : (
            <p className="text-sm text-slate-600 mb-4 font-medium">Bu paleti karantinadan çıkarmak istediğinize emin misiniz?</p>
          )}
          <ModalActions
            onCancel={() => { setKarantinaModal(null); setKarantinaNeden(''); }}
            onConfirm={karantinaIslem}
            confirmLabel="Onayla"
            confirmClass={karantinaModal.tip === 'al' ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-emerald-600 hover:bg-emerald-700 text-white'}
            disabled={loading || (karantinaModal.tip === 'al' && !karantinaNeden.trim())}
            loading={loading}
          />
        </Modal>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   GÖREV SATIRI — Geliştirilmiş Görünüm
   ═══════════════════════════════════════════════════ */

function GorevSatiri({ g, isExpanded, onToggle, onIptal, onKarantinaAl, onKarantinaCikar }) {
  const aktif = ['Bekliyor', 'Atandi', 'DevamEdiyor'].includes(g.durum);
  const oncelikGorsel = ONCELIK_GORSEL[g.oncelik] || ONCELIK_GORSEL[3];
  const tarih = useMemo(() => new Date(g.olusturma_tarihi).toLocaleDateString('tr-TR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  }), [g.olusturma_tarihi]);

  return (
    // Satırların ayrışması için border-b ve açıldığında sol kenar (border-l) vurgusu eklendi
    <div className={`group relative border-b border-slate-200 last:border-b-0 transition-colors duration-200 ${isExpanded ? 'bg-indigo-50/20' : 'hover:bg-slate-50'}`}>
      <div className={`absolute left-0 top-0 bottom-0 w-1 transition-colors ${isExpanded ? 'bg-indigo-500' : 'bg-transparent group-hover:bg-slate-300'}`} />

      {/* ── Kompakt Ana Satır ── */}
      <div onClick={onToggle} className="cursor-pointer select-none">
        {/* MASAÜSTÜ */}
        <div className="hidden lg:grid lg:grid-cols-[40px_70px_1.4fr_1fr_0.8fr_0.8fr_0.8fr_120px] gap-4 items-center px-5 py-3.5">
          <div className="flex items-center justify-center">
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isExpanded ? '-rotate-180 text-indigo-600' : ''}`} />
          </div>
          <span className="font-mono text-sm font-bold text-slate-800">#{g.id}</span>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md border ${DURUM_RENK[g.durum] || 'bg-slate-100 text-slate-500'}`}>
              {DURUM_IKON[g.durum]} {g.durum}
            </span>
            <span className={`text-xs font-medium px-2 py-1 rounded-md bg-white border ${TIP_RENK[g.tip] ? TIP_RENK[g.tip].replace('ring-', 'border-').replace('/10','') : 'border-slate-200 text-slate-500'}`}>
              {g.tip}
            </span>
          </div>
          <span className="text-sm text-slate-800 font-semibold font-mono truncate">{g.palet_barkodu ?? g.palet_id}</span>
          <span className="text-sm text-slate-500 font-medium truncate">{g.atanan_kullanici_id ?? <span className="italic text-slate-300">—</span>}</span>
          <div>
            <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-md ${oncelikGorsel.bg} ${oncelikGorsel.text}`}>
              <span className={`w-2 h-2 rounded-full ${oncelikGorsel.dot}`} />
              {oncelikGorsel.label}
            </span>
          </div>
          <span className="text-xs text-slate-500 font-medium tabular-nums">{tarih}</span>
          <div onClick={(e) => e.stopPropagation()} className="flex justify-end pr-2">
            {aktif ? (
              <button onClick={onIptal} className="text-xs font-bold text-rose-600 hover:text-white bg-white hover:bg-rose-600 px-3 py-1.5 rounded-lg border border-rose-200 transition-all flex items-center gap-1.5 shadow-sm">
                <X className="w-3.5 h-3.5" /> İptal
              </button>
            ) : (
              <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 justify-end w-full pr-2">
                {g.durum === 'Tamamlandi' ? <><CheckCircle className="w-3.5 h-3.5" /> Tamamlandı</> : <><XCircle className="w-3.5 h-3.5" /> İptal</>}
              </span>
            )}
          </div>
        </div>

        {/* MOBİL — Kompakt Liste */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="font-mono text-sm font-bold text-slate-800">#{g.id}</span>
              <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded border ${DURUM_RENK[g.durum]}`}>
                {DURUM_IKON[g.durum]} {g.durum}
              </span>
              <span className={`w-2 h-2 rounded-full ${oncelikGorsel.dot}`} />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span className="font-medium truncate">LPN: <span className="text-slate-800 font-semibold font-mono">{g.palet_barkodu ?? g.palet_id}</span></span>
              <span className="text-slate-300">•</span>
              <span className="tabular-nums shrink-0">{tarih}</span>
            </div>
          </div>
          <ChevronDown className={`w-5 h-5 shrink-0 text-slate-400 transition-transform duration-300 ${isExpanded ? '-rotate-180 text-indigo-600' : ''}`} />
        </div>
      </div>

      {/* ── Genişletilmiş Detay ── */}
      {/* İç içe geçmiş kutu görünümü kaldırıldı, daha düz bir zemin kullanıldı */}
      {isExpanded && (
        <div className="bg-white border-t border-slate-100 px-4 py-4 lg:px-14 lg:py-5 space-y-5 cursor-default">
          
          {(g.urun_adi || g.palet_barkodu || g.lot_no || g.miktar) && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
              {g.urun_adi && <InfoCell label="Ürün Adı" value={g.urun_adi} span="col-span-2" bold />}
              {g.palet_barkodu && <InfoCell label="LPN / Barkod" value={g.palet_barkodu} mono />}
              <InfoCell label="Palet DB-ID" value={g.palet_id} mono />
              {g.miktar != null && <InfoCell label="Miktar" value={g.miktar} bold />}
              {g.lot_no && <InfoCell label="Lot No" value={g.lot_no} />}
              {g.zone_adi && <InfoCell label="Zon (Bölge)" value={g.zone_adi} />}
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <DetayKarti label="Önerilen Raf" value={g.onerilen_raf_kodu || g.onerilen_raf_id} />
            <DetayKarti label="Gerçekleşen Raf" value={g.gerceklesen_raf_id} highlight={g.gerceklesen_raf_id != null && g.gerceklesen_raf_id !== g.onerilen_raf_id} />
            <DetayKarti label="Atanan Personel" value={g.atanan_kullanici_id} />
            <DetayKarti label="Override (Manuel İzni)" value={g.override_kullanici_id ? `Evet (${g.override_kullanici_id})` : 'Hayır'} isWarning={!!g.override_kullanici_id} />
          </div>

          {g.override_neden && (
            <AlertBox variant="amber" icon={<AlertTriangle className="w-5 h-5" />} title="Override Gerekçesi" text={g.override_neden} />
          )}

          {g.iptal_nedeni && (
            <AlertBox variant="rose" icon={<XCircle className="w-5 h-5" />} title="İptal Nedeni" text={g.iptal_nedeni} />
          )}

          {/* Butonlar sağa yaslandı, tam genişlik yerine daha kompakt yapıya geçildi */}
          <div className="pt-4 border-t border-slate-100 flex flex-wrap justify-end gap-3" onClick={(e) => e.stopPropagation()}>
            <button onClick={onKarantinaAl} className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-amber-50 text-amber-700 font-bold text-sm rounded-xl border border-amber-200 transition-colors shadow-sm">
              <Shield className="w-4 h-4" /> Karantinaya Al
            </button>
            <button onClick={onKarantinaCikar} className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-emerald-50 text-emerald-700 font-bold text-sm rounded-xl border border-emerald-200 transition-colors shadow-sm">
              <ShieldOff className="w-4 h-4" /> Karantinadan Çıkar
            </button>
            {aktif && (
              <button onClick={onIptal} className="lg:hidden flex items-center gap-2 px-4 py-2 bg-rose-600 text-white font-bold text-sm rounded-xl transition-colors shadow-sm">
                <X className="w-4 h-4" /> İptal Et
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   YARDIMCI BİLEŞENLER
   ═══════════════════════════════════════════════════ */

function SectionLabel({ icon, text }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className="text-indigo-500 bg-indigo-50 p-1.5 rounded-md">{icon}</div>
      <span className="text-xs font-bold text-slate-700 uppercase tracking-widest">{text}</span>
    </div>
  );
}

function SelectField({ icon, value, onChange, options }) {
  return (
    <div className="relative flex-1 sm:w-48">
      {icon && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">{icon}</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full ${icon ? 'pl-9' : 'pl-4'} pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 appearance-none cursor-pointer transition`}
      >
        {options.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
    </div>
  );
}

function OzetKart({ label, value, variant, icon }) {
  const styles = {
    amber:  'from-amber-500 to-orange-500 shadow-amber-500/20',
    rose:   'from-rose-500 to-rose-600 shadow-rose-500/20',
    orange: 'from-orange-400 to-amber-500 shadow-orange-500/20',
    indigo: 'from-indigo-500 to-indigo-600 shadow-indigo-500/20',
  };
  return (
    <div className={`rounded-2xl p-4 sm:p-5 shadow-md relative overflow-hidden bg-gradient-to-br text-white ${styles[variant]}`}>
      <div className="absolute right-3 top-3 opacity-20">{icon}</div>
      <p className="text-xs font-bold opacity-90 mb-1.5 uppercase tracking-wider">{label}</p>
      <p className="text-3xl sm:text-4xl font-black tracking-tight leading-none">{value ?? '0'}</p>
    </div>
  );
}

function DurumKart({ label, value, variant }) {
  const styles = {
    sky:     'bg-white border-slate-200 text-sky-600',
    indigo:  'bg-white border-slate-200 text-indigo-600',
    emerald: 'bg-white border-slate-200 text-emerald-600',
  };
  return (
    <div className={`rounded-2xl p-4 border shadow-sm ${styles[variant]} flex flex-col justify-center`}>
      <span className="text-xs sm:text-sm font-bold text-slate-500 uppercase tracking-wide mb-1">{label}</span>
      <span className="text-2xl sm:text-3xl font-black leading-none">{value}</span>
    </div>
  );
}

function InfoCell({ label, value, span = '', bold = false, mono = false }) {
  return (
    // Hücreler arkaplanda kaybolmasın diye beyaz arka plan, hafif gölge ve border eklendi
    <div className={`bg-white rounded-xl p-3 border border-slate-200 shadow-sm ${span}`}>
      <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1 tracking-wider">{label}</span>
      <span className={`text-sm ${bold ? 'font-black' : 'font-semibold'} ${mono ? 'font-mono text-indigo-600' : 'text-slate-800'}`}>{value}</span>
    </div>
  );
}

function DetayKarti({ label, value, highlight = false, isWarning = false }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</span>
      <div className={`text-sm font-bold rounded-xl px-3 py-2 border ${
        isWarning  ? 'bg-amber-50 text-amber-700 border-amber-200'
        : highlight ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
        : 'bg-slate-50 text-slate-700 border-slate-200'
      }`}>
        {value || '—'}
      </div>
    </div>
  );
}

function AlertBox({ variant, icon, title, text }) {
  const styles = {
    amber: 'bg-amber-50 border-l-amber-500 text-amber-800',
    rose:  'bg-rose-50 border-l-rose-500 text-rose-800',
  };
  return (
    // Kalın kutular yerine daha şık duran sol border konsepti eklendi
    <div className={`border border-slate-100 border-l-4 rounded-r-xl rounded-l-sm p-4 flex gap-3 items-start ${styles[variant]}`}>
      <span className="shrink-0 mt-0.5">{icon}</span>
      <div>
        <span className="text-xs font-bold uppercase tracking-wider block mb-1">{title}</span>
        <p className="text-sm font-medium opacity-90 leading-relaxed">{text}</p>
      </div>
    </div>
  );
}

// Modal, ModalHeader, ModalActions bileşenleri değişmediği için kısaltılabilir veya aynı bırakılabilir. (Aynı bırakıldı)
function Modal({ onClose, children }) {
  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center sm:p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="bg-white w-full sm:w-[440px] rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden">
        <div className="p-6 sm:p-7">
          <div className="w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-6 sm:hidden" />
          {children}
        </div>
      </div>
    </div>
  );
}

function ModalHeader({ icon, iconBg, title }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>{icon}</div>
      <h3 className="text-xl font-bold text-slate-900">{title}</h3>
    </div>
  );
}

function ModalActions({ onCancel, onConfirm, confirmLabel, confirmClass, disabled, loading: isLoading }) {
  return (
    <div className="flex flex-col-reverse sm:flex-row gap-3 mt-6">
      <button onClick={onCancel} className="w-full px-4 py-3 border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 rounded-xl font-bold text-sm transition-colors">
        Vazgeç
      </button>
      <button
        onClick={onConfirm}
        disabled={disabled}
        className={`w-full px-4 py-3 text-white rounded-xl font-bold text-sm transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-sm ${confirmClass}`}
      >
        {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : confirmLabel}
      </button>
    </div>
  );
}