import { useCallback, useMemo, useState } from 'react';
import {
    Package, Plus, Search, X, RefreshCw, CheckCircle, AlertTriangle,
    Ban, Download, ShieldAlert, ShieldCheck, Loader2, ChevronDown, MapPin,
    Calendar, Layers, CheckSquare
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { hataMetni } from '../utils/hata';
import EtiketOlusturModal from '../components/palet/EtiketOlusturModal';
import { useDepolarQuery } from '../queries/locationQueries';
import { useLotlarQuery } from '../queries/lotQueries';
import {
    useCreateUretimPaletiMutation,
    useUretimPaletleriQuery,
    useUretimPaletiIptalMutation,
    useUretimPaletiKabulEtMutation,
    useUretimPaletiKarantinaAlMutation,
    useUretimPaletiKarantinaCikarMutation,
} from '../queries/productionPalletQueries';
import { useKullanicilarQuery } from '../queries/userQueries';

// ── Sabitler ──────────────────────────────────────────────────────────────────

const DURUM = {
    OLUSTURULDU: 'Olusturuldu',
    KABUL_BEKLIYOR: 'KabulBekliyor',
    KABUL_EDILDI: 'KabulEdildi',
    YERLESTIRME_BEKLIYOR: 'YerlestirmeBekliyor',
    YERLESTIRILDI: 'Yerlestirildi',
    KARANTINA: 'Karantina',
    IPTAL_EDILDI: 'IptalEdildi',
};

const DURUM_BADGE = {
    [DURUM.OLUSTURULDU]:          'bg-slate-50 text-slate-700 ring-slate-200',
    [DURUM.KABUL_BEKLIYOR]:       'bg-amber-50 text-amber-800 ring-amber-200',
    [DURUM.KABUL_EDILDI]:         'bg-emerald-50 text-emerald-800 ring-emerald-200',
    [DURUM.YERLESTIRME_BEKLIYOR]: 'bg-blue-50 text-blue-800 ring-blue-200',
    [DURUM.YERLESTIRILDI]:        'bg-indigo-50 text-indigo-800 ring-indigo-200',
    [DURUM.KARANTINA]:            'bg-red-50 text-red-700 ring-red-200',
    [DURUM.IPTAL_EDILDI]:         'bg-gray-50 text-gray-500 ring-gray-200 line-through',
};

const DURUM_ETIKET = {
    [DURUM.OLUSTURULDU]:          'Oluşturuldu',
    [DURUM.KABUL_BEKLIYOR]:       'Kabul Bekliyor',
    [DURUM.KABUL_EDILDI]:         'Kabul Edildi',
    [DURUM.YERLESTIRME_BEKLIYOR]: 'Yrl. Bekliyor',
    [DURUM.YERLESTIRILDI]:        'Yerleştirildi',
    [DURUM.KARANTINA]:            'Karantina',
    [DURUM.IPTAL_EDILDI]:         'İptal',
};

// ── Yardımcılar ───────────────────────────────────────────────────────────────

const kaliteyetkisi = (user) =>
    user?.rol === 'admin' || (user?.departman || '').toLowerCase() === 'kalite';

// ── Bileşen ───────────────────────────────────────────────────────────────────

export default function UretimPaletleriPage() {
    const { user } = useAuth();

    const [aramaMetni, setAramaMetni] = useState('');
    const [durumFiltre, setDurumFiltre] = useState('');

    const [yeniModal, setYeniModal] = useState(false);
    const [islemPaletNo, setIslemPaletNo] = useState(null);

    const [formData, setFormData] = useState({
        lot_id: '',
        depo_id: '',
        koli_adedi: '',
        vardiya: '',
        palet_kg: '',
        uretim_tarihi: new Date().toISOString().split('T')[0],
        uretim_hatti: '',
        makine_kodu: '',
        operator_kullanici_id: '',
        brut_kg: '',
        net_kg: '',
    });

    // Sebep modal (karantina / iptal)
    const [sebepModal, setSebepModal] = useState(null); // { tip, paletNo }
    const [sebepText, setSebepText] = useState('');

    // Etiket modalı
    const [etiketModalPaletNo, setEtiketModalPaletNo] = useState(null);

    const {
        data: paletler = [],
        isLoading: loading,
        refetch: refetchPaletler,
    } = useUretimPaletleriQuery({ sadece_aktif: false });
    const {
        data: lotlarResult,
        refetch: refetchLotlar,
    } = useLotlarQuery();
    const {
        data: depolar = [],
        refetch: refetchDepolar,
    } = useDepolarQuery();
    const {
        data: kullanicilar = [],
        refetch: refetchKullanicilar,
    } = useKullanicilarQuery();

    const createUretimPaletiMutation = useCreateUretimPaletiMutation();
    const kabulEtMutation = useUretimPaletiKabulEtMutation();
    const karantinaAlMutation = useUretimPaletiKarantinaAlMutation();
    const karantinaCikarMutation = useUretimPaletiKarantinaCikarMutation();
    const iptalMutation = useUretimPaletiIptalMutation();

    const lotlar = lotlarResult?.data ?? [];
    const operatorler = useMemo(
        () => kullanicilar.filter((k) => k.rol === 'depocu' || k.rol === 'admin'),
        [kullanicilar],
    );

    const veriYukle = useCallback(async () => {
        await Promise.all([refetchPaletler(), refetchLotlar(), refetchDepolar(), refetchKullanicilar()]);
    }, [refetchDepolar, refetchKullanicilar, refetchLotlar, refetchPaletler]);

    // ── Filtre (Performans için useMemo eklendi) ──────────────────────────────

    const filtrelenmis = useMemo(() => {
        return paletler.filter((p) => {
            const aramaUyum = !aramaMetni || p.palet_no.toLowerCase().includes(aramaMetni.toLowerCase());
            const durumUyum = !durumFiltre || p.durum === durumFiltre;
            return aramaUyum && durumUyum;
        });
    }, [paletler, aramaMetni, durumFiltre]);

    // ── Form ──────────────────────────────────────────────────────────────────

    const formuSifirla = () => setFormData({
        lot_id: '',
        depo_id: user?.depo_id ? String(user.depo_id) : '',
        koli_adedi: '',
        vardiya: '',
        palet_kg: '',
        uretim_tarihi: new Date().toISOString().split('T')[0],
        uretim_hatti: '',
        makine_kodu: '',
        operator_kullanici_id: '',
        brut_kg: '',
        net_kg: '',
    });

    const modaliAc = () => {
        setFormData((f) => ({
            ...f,
            depo_id: user?.depo_id ? String(user.depo_id) : f.depo_id,
        }));
        setYeniModal(true);
    };

    const paletOlustur = async (e) => {
        e.preventDefault();
        if (!formData.depo_id) {
            toast.error('Depo seçimi zorunludur');
            return;
        }
        try {
            await createUretimPaletiMutation.mutateAsync({
                lot_id: parseInt(formData.lot_id),
                depo_id: parseInt(formData.depo_id),
                koli_adedi: parseInt(formData.koli_adedi),
                vardiya: formData.vardiya || undefined,
                palet_kg: formData.palet_kg ? parseFloat(formData.palet_kg) : undefined,
                uretim_tarihi: formData.uretim_tarihi || undefined,
                uretim_hatti: formData.uretim_hatti || undefined,
                makine_kodu: formData.makine_kodu || undefined,
                operator_kullanici_id: formData.operator_kullanici_id
                    ? parseInt(formData.operator_kullanici_id) : undefined,
                brut_kg: formData.brut_kg ? parseFloat(formData.brut_kg) : undefined,
                net_kg: formData.net_kg ? parseFloat(formData.net_kg) : undefined,
            });
            toast.success('Üretim paleti oluşturuldu');
            setYeniModal(false);
            formuSifirla();
            void veriYukle();
        } catch (err) {
            toast.error(hataMetni(err, 'Palet oluşturulamadı'));
        }
    };

    // ── Aksiyon yardımcıları ──────────────────────────────────────────────────

    const aksiyon = async (mutateAsync, paletNo, basariMesaji, arg) => {
        setIslemPaletNo(paletNo);
        try {
            await mutateAsync(arg === undefined ? paletNo : { paletNo, data: arg });
            toast.success(basariMesaji);
            void veriYukle();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        } finally {
            setIslemPaletNo(null);
        }
    };

    const kabulEt = (pn) => aksiyon(kabulEtMutation.mutateAsync, pn, 'Palet kabul edildi');

    const sebepliIslem = async () => {
        if (!sebepModal) return;
        const { tip, paletNo } = sebepModal;
        if (tip === 'karantina') {
            await aksiyon(karantinaAlMutation.mutateAsync, paletNo, 'Karantinaya alındı', { palet_no: paletNo, sebep: sebepText });
        } else if (tip === 'karantina-cikar') {
            await aksiyon(karantinaCikarMutation.mutateAsync, paletNo, 'Karantinadan çıkarıldı', { palet_no: paletNo, sebep: sebepText });
        } else if (tip === 'iptal') {
            await aksiyon(iptalMutation.mutateAsync, paletNo, 'Palet iptal edildi', { palet_no: paletNo, sebep: sebepText });
        }
        setSebepModal(null);
        setSebepText('');
    };

    // ── Render ────────────────────────────────────────────────────────────────

    const isAdmin = user?.rol === 'admin';
    const isDepocuOrAdmin = user?.rol === 'admin' || user?.rol === 'depocu';
    const isKaliteYetkili = kaliteyetkisi(user);

    // Tekrarı önlemek için aksiyon butonlarını render eden fonksiyon
    const renderIslemler = (p) => {
        const islem = islemPaletNo === p.palet_no;
        return (
            <div className="flex items-center gap-2 flex-wrap">
                {islem && <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />}

                {isDepocuOrAdmin && [DURUM.OLUSTURULDU, DURUM.KABUL_BEKLIYOR].includes(p.durum) && (
                    <AksiyonButon
                        onClick={() => kabulEt(p.palet_no)}
                        icon={<CheckCircle className="w-4 h-4" />}
                        label="Kabul Et"
                        renk="emerald"
                        disabled={islem}
                    />
                )}

                {isDepocuOrAdmin && p.durum === DURUM.YERLESTIRME_BEKLIYOR && (
                    <AksiyonButon
                        onClick={() => toast('Yerleştirme için Üretimden Kabul sayfasından raf barkodu okutun', { icon: '📍' })}
                        icon={<MapPin className="w-4 h-4" />}
                        label="Yerleştir"
                        renk="blue"
                        disabled={islem}
                    />
                )}

                {isKaliteYetkili && p.durum === DURUM.KABUL_EDILDI && (
                    <AksiyonButon
                        onClick={() => { setSebepModal({ tip: 'karantina', paletNo: p.palet_no }); setSebepText(''); }}
                        icon={<ShieldAlert className="w-4 h-4" />}
                        label="Karantina"
                        renk="red"
                        disabled={islem}
                    />
                )}

                {isKaliteYetkili && p.durum === DURUM.KARANTINA && (
                    <AksiyonButon
                        onClick={() => { setSebepModal({ tip: 'karantina-cikar', paletNo: p.palet_no }); setSebepText(''); }}
                        icon={<ShieldCheck className="w-4 h-4" />}
                        label="Çıkar"
                        renk="emerald"
                        disabled={islem}
                    />
                )}

                {isAdmin && [DURUM.OLUSTURULDU, DURUM.KABUL_BEKLIYOR].includes(p.durum) && (
                    <AksiyonButon
                        onClick={() => { setSebepModal({ tip: 'iptal', paletNo: p.palet_no }); setSebepText(''); }}
                        icon={<Ban className="w-4 h-4" />}
                        label="İptal"
                        renk="gray"
                        disabled={islem}
                    />
                )}

                <AksiyonButon
                    onClick={() => setEtiketModalPaletNo(p.palet_no)}
                    icon={<Download className="w-4 h-4" />}
                    label="Etiket"
                    renk="slate"
                    disabled={islem}
                />
            </div>
        );
    };

    return (
        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 sm:space-y-8 min-h-screen bg-slate-50/50">
            {/* Başlık ve Ana Aksiyonlar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
                        <Package className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Üretim Paletleri</h1>
                        <p className="text-sm text-slate-500 font-medium mt-0.5">Üretimden gelen girişleri yönetin</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <button
                        onClick={veriYukle}
                        className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all text-slate-600 shadow-sm"
                        title="Yenile"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                    {isDepocuOrAdmin && (
                        <button
                            onClick={modaliAc}
                            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-all shadow-sm shadow-emerald-600/20 text-sm font-semibold tracking-wide"
                        >
                            <Plus className="w-4 h-4" />
                            Yeni Palet
                        </button>
                    )}
                </div>
            </div>

            {/* Arama ve Filtreler */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Palet no ile ara..."
                        value={aramaMetni}
                        onChange={(e) => setAramaMetni(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm transition-all focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 placeholder:text-slate-400 shadow-sm"
                    />
                </div>
                <div className="relative w-full sm:w-48">
                    <select
                        value={durumFiltre}
                        onChange={(e) => setDurumFiltre(e.target.value)}
                        className="w-full pl-4 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl text-sm appearance-none transition-all focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 shadow-sm text-slate-700 font-medium"
                    >
                        <option value="">Tüm Durumlar</option>
                        {Object.entries(DURUM_ETIKET).map(([k, v]) => (
                            <option key={k} value={k}>{v}</option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
            </div>

            {/* İçerik Alanı */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-32 bg-white rounded-2xl border border-slate-200 shadow-sm">
                    <Loader2 className="w-10 h-10 animate-spin text-emerald-500 mb-4" />
                    <p className="text-sm font-medium text-slate-500">Paletler yükleniyor...</p>
                </div>
            ) : filtrelenmis.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-32 bg-white rounded-2xl border border-slate-200 shadow-sm">
                    <div className="p-4 bg-slate-50 rounded-full mb-4">
                        <Package className="w-10 h-10 text-slate-300" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-700">Palet Bulunamadı</h3>
                    <p className="text-sm text-slate-500 mt-1">Arama kriterlerinize uygun sonuç yok.</p>
                </div>
            ) : (
                <>
                    {/* MOBİL GÖRÜNÜM (Kart Tasarımı) */}
                    <div className="grid grid-cols-1 gap-4 md:hidden">
                        {filtrelenmis.map((p) => (
                            <div key={p.palet_no} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-base font-bold font-mono text-slate-800">{p.palet_no}</span>
                                        </div>
                                        <p className="text-sm text-slate-600 font-medium line-clamp-1">
                                            {p.urun_isim || p.lot_no || `Lot #${p.lot_id}`}
                                        </p>
                                    </div>
                                    <span className={`shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ring-1 ring-inset ${DURUM_BADGE[p.durum] || 'bg-slate-50 text-slate-600 ring-slate-200'}`}>
                                        {DURUM_ETIKET[p.durum] || p.durum}
                                    </span>
                                </div>
                                
                                <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100">
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                        <Layers className="w-4 h-4 text-slate-400" />
                                        <span>{p.koli_adedi} Koli</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                        <Calendar className="w-4 h-4 text-slate-400" />
                                        <span>{p.uretim_tarihi || 'Tarih Yok'}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-600 col-span-2">
                                        <CheckSquare className="w-4 h-4 text-slate-400" />
                                        <span>Vardiya: {p.vardiya || '—'}</span>
                                    </div>
                                </div>

                                <div className="pt-1">
                                    {renderIslemler(p)}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* MASAÜSTÜ GÖRÜNÜM (Tablo Tasarımı) */}
                    <div className="hidden md:block bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500">
                                    <tr>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Palet No</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Lot / Ürün</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Koli</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Vardiya</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Üretim Tarihi</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Durum</th>
                                        <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px] text-right">İşlemler</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {filtrelenmis.map((p) => (
                                        <tr key={p.palet_no} className="hover:bg-slate-50/50 transition-colors group">
                                            <td className="px-5 py-4 whitespace-nowrap font-mono font-bold text-slate-700">{p.palet_no}</td>
                                            <td className="px-5 py-4">
                                                <div className="font-medium text-slate-800">{p.lot_no || `Lot #${p.lot_id}`}</div>
                                                {p.urun_isim && <div className="text-xs text-slate-500 mt-0.5">{p.urun_isim}</div>}
                                            </td>
                                            <td className="px-5 py-4 whitespace-nowrap text-slate-600 font-medium">{p.koli_adedi}</td>
                                            <td className="px-5 py-4 whitespace-nowrap text-slate-600">{p.vardiya || '—'}</td>
                                            <td className="px-5 py-4 whitespace-nowrap text-slate-600">{p.uretim_tarihi || '—'}</td>
                                            <td className="px-5 py-4 whitespace-nowrap">
                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ring-1 ring-inset ${DURUM_BADGE[p.durum] || 'bg-slate-50 text-slate-600 ring-slate-200'}`}>
                                                    {DURUM_ETIKET[p.durum] || p.durum}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 whitespace-nowrap">
                                                <div className="flex justify-end opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                                                    {renderIslemler(p)}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {/* Yeni Palet Modalı */}
            {yeniModal && (
                <Modal baslik="Yeni Üretim Paleti" onKapat={() => { setYeniModal(false); formuSifirla(); }} genisMi>
                    <form onSubmit={paletOlustur} className="space-y-5">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">
                                    Depo <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={formData.depo_id}
                                    onChange={(e) => setFormData({ ...formData, depo_id: e.target.value })}
                                    required
                                    disabled={!isAdmin && !!user?.depo_id}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm transition-all focus:bg-white focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 disabled:opacity-60 disabled:cursor-not-allowed appearance-none"
                                >
                                    <option value="">Seçiniz...</option>
                                    {depolar.map((d) => (
                                        <option key={d.id} value={d.id}>{d.isim || `Depo #${d.id}`}</option>
                                    ))}
                                </select>
                                {!isAdmin && user?.depo_id && (
                                    <p className="text-[11px] font-medium text-slate-400 mt-1.5">Mevcut deponuz atandı, değiştirilemez.</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">
                                    Lot <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={formData.lot_id}
                                    onChange={(e) => setFormData({ ...formData, lot_id: e.target.value })}
                                    required
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm transition-all focus:bg-white focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 appearance-none"
                                >
                                    <option value="">Seçiniz...</option>
                                    {lotlar.map((l) => (
                                        <option key={l.id} value={l.id}>{l.lot_no || `#${l.id}`}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <FormField label="Koli Adedi *" type="number" min="1" required
                                value={formData.koli_adedi}
                                onChange={(v) => setFormData({ ...formData, koli_adedi: v })} />
                            <FormField label="Palet Ağırlığı (kg)" type="number" min="0.1" step="0.1"
                                value={formData.palet_kg}
                                onChange={(v) => setFormData({ ...formData, palet_kg: v })} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <FormField label="Vardiya" type="text" placeholder="A / B / C"
                                value={formData.vardiya}
                                onChange={(v) => setFormData({ ...formData, vardiya: v })} />
                            <FormField label="Üretim Tarihi" type="date"
                                value={formData.uretim_tarihi}
                                onChange={(v) => setFormData({ ...formData, uretim_tarihi: v })} />
                        </div>

                        <div className="pt-4 mt-2 border-t border-slate-100">
                            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">
                                İzlenebilirlik Bilgileri (Opsiyonel)
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <FormField label="Üretim Hattı" type="text" placeholder="Örn: HAT-1"
                                    value={formData.uretim_hatti}
                                    onChange={(v) => setFormData({ ...formData, uretim_hatti: v })} />
                                <FormField label="Makine Kodu" type="text" placeholder="Örn: M-07"
                                    value={formData.makine_kodu}
                                    onChange={(v) => setFormData({ ...formData, makine_kodu: v })} />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">Operatör</label>
                                    <select
                                        value={formData.operator_kullanici_id}
                                        onChange={(e) => setFormData({ ...formData, operator_kullanici_id: e.target.value })}
                                        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm transition-all focus:bg-white focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 appearance-none"
                                    >
                                        <option value="">Yok</option>
                                        {operatorler.map((o) => (
                                            <option key={o.id} value={o.id}>
                                                {o.ad_soyad || o.kullanici_adi}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <FormField label="Brüt (kg)" type="number" min="0.1" step="0.1"
                                    value={formData.brut_kg}
                                    onChange={(v) => setFormData({ ...formData, brut_kg: v })} />
                                <FormField label="Net (kg)" type="number" min="0.1" step="0.1"
                                    value={formData.net_kg}
                                    onChange={(v) => setFormData({ ...formData, net_kg: v })} />
                            </div>
                        </div>

                        <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 border-t border-slate-100 mt-2">
                            <button type="button" onClick={() => { setYeniModal(false); formuSifirla(); }}
                                className="w-full sm:w-auto px-6 py-2.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors">
                                İptal
                            </button>
                            <button type="submit"
                                className="w-full sm:w-auto px-6 py-2.5 text-sm font-semibold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 shadow-sm shadow-emerald-600/20 transition-all">
                                Oluştur
                            </button>
                        </div>
                    </form>
                </Modal>
            )}

            {/* Etiket Oluşturma Modalı */}
            {etiketModalPaletNo && (
                <EtiketOlusturModal
                    paletNo={etiketModalPaletNo}
                    onKapat={() => setEtiketModalPaletNo(null)}
                />
            )}

            {/* Sebep Modalı */}
            {sebepModal && (
                <Modal
                    baslik={
                        sebepModal.tip === 'karantina' ? 'Karantinaya Al' :
                        sebepModal.tip === 'karantina-cikar' ? 'Karantinadan Çıkar' : 'Paleti İptal Et'
                    }
                    onKapat={() => setSebepModal(null)}
                >
                    <div className="space-y-5">
                        <p className="text-sm text-slate-600 font-medium">
                            <span className="font-mono font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md mr-1">{sebepModal.paletNo}</span> 
                            paleti için işlem gerekçesi belirtin:
                        </p>
                        <textarea
                            autoFocus
                            value={sebepText}
                            onChange={(e) => setSebepText(e.target.value)}
                            placeholder="Açıklama veya sebep giriniz..."
                            required={sebepModal.tip === 'iptal'}
                            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm transition-all focus:bg-white focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 resize-none h-28 placeholder:text-slate-400"
                        />
                        <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-2">
                            <button onClick={() => setSebepModal(null)}
                                className="w-full sm:w-auto px-6 py-2.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors">
                                Vazgeç
                            </button>
                            <button
                                onClick={sebepliIslem}
                                disabled={sebepModal.tip === 'iptal' && !sebepText.trim()}
                                className={`w-full sm:w-auto px-6 py-2.5 text-sm font-semibold text-white rounded-xl shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${sebepModal.tip === 'karantina-cikar' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20' : 'bg-red-600 hover:bg-red-700 shadow-red-600/20'}`}
                            >
                                İşlemi Onayla
                            </button>
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}

// ── Alt bileşenler ────────────────────────────────────────────────────────────

function AksiyonButon({ onClick, icon, label, renk, disabled }) {
    const renkler = {
        amber:   'bg-amber-50 text-amber-700 hover:bg-amber-100 hover:text-amber-800 border-transparent hover:border-amber-200',
        emerald: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 hover:text-emerald-800 border-transparent hover:border-emerald-200',
        blue:    'bg-blue-50 text-blue-700 hover:bg-blue-100 hover:text-blue-800 border-transparent hover:border-blue-200',
        red:     'bg-red-50 text-red-700 hover:bg-red-100 hover:text-red-800 border-transparent hover:border-red-200',
        gray:    'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700 border-transparent hover:border-slate-300',
        slate:   'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-800',
    };
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            title={label}
            className={`flex items-center justify-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg border transition-all disabled:opacity-50 disabled:cursor-not-allowed ${renkler[renk] || renkler.gray}`}
        >
            {icon}
            <span className="hidden sm:inline-block">{label}</span>
        </button>
    );
}

function Modal({ baslik, onKapat, children, genisMi }) {
    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-slate-900/40 backdrop-blur-sm transition-opacity">
            <div className={`bg-white shadow-2xl w-full ${genisMi ? 'sm:max-w-3xl' : 'sm:max-w-md'} max-h-[95vh] sm:max-h-[90vh] flex flex-col rounded-t-3xl sm:rounded-2xl overflow-hidden`}>
                {/* Mobilde modal sürükleme indikatörü */}
                <div className="w-full flex justify-center pt-3 pb-1 sm:hidden">
                    <div className="w-12 h-1.5 bg-slate-200 rounded-full"></div>
                </div>
                
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 flex-shrink-0">
                    <h2 className="text-lg font-bold text-slate-800 tracking-tight">{baslik}</h2>
                    <button onClick={onKapat} className="p-2 -mr-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="px-6 py-5 overflow-y-auto custom-scrollbar">{children}</div>
            </div>
        </div>
    );
}

function FormField({ label, onChange, ...props }) {
    return (
        <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">{label}</label>
            <input
                {...props}
                onChange={(e) => onChange(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm transition-all focus:bg-white focus:outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 placeholder:text-slate-400"
            />
        </div>
    );
}