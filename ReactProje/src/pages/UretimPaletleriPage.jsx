import { useCallback, useMemo, useState } from 'react';
import {
    Package, Plus, Search, X, RefreshCw, CheckCircle, AlertTriangle,
    Ban, Download, ShieldAlert, ShieldCheck, Loader2, ChevronDown, MapPin,
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
    [DURUM.OLUSTURULDU]:          'bg-slate-100 text-slate-700',
    [DURUM.KABUL_BEKLIYOR]:       'bg-amber-100 text-amber-800',
    [DURUM.KABUL_EDILDI]:         'bg-emerald-100 text-emerald-800',
    [DURUM.YERLESTIRME_BEKLIYOR]: 'bg-blue-100 text-blue-800',
    [DURUM.YERLESTIRILDI]:        'bg-indigo-100 text-indigo-800',
    [DURUM.KARANTINA]:            'bg-red-100 text-red-700',
    [DURUM.IPTAL_EDILDI]:         'bg-gray-100 text-gray-500 line-through',
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

    // ── Filtre ────────────────────────────────────────────────────────────────

    const filtrelenmis = paletler.filter((p) => {
        const aramaUyum = !aramaMetni || p.palet_no.toLowerCase().includes(aramaMetni.toLowerCase());
        const durumUyum = !durumFiltre || p.durum === durumFiltre;
        return aramaUyum && durumUyum;
    });

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

    const kabulEt    = (pn) => aksiyon(kabulEtMutation.mutateAsync, pn, 'Palet kabul edildi');

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

    return (
        <div className="p-6 space-y-6">
            {/* Başlık */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-100 rounded-xl">
                        <Package className="w-6 h-6 text-emerald-700" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">Üretim Palet Yönetimi</h1>
                        <p className="text-sm text-gray-500">Üretimden gelen palet girişlerini yönetin</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={veriYukle}
                        className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                        title="Yenile"
                    >
                        <RefreshCw className="w-4 h-4 text-gray-600" />
                    </button>
                    {isDepocuOrAdmin && (
                        <button
                            onClick={modaliAc}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
                        >
                            <Plus className="w-4 h-4" />
                            Yeni Palet
                        </button>
                    )}
                </div>
            </div>

            {/* Filtreler */}
            <div className="flex gap-3">
                <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Palet no ara..."
                        value={aramaMetni}
                        onChange={(e) => setAramaMetni(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                </div>
                <select
                    value={durumFiltre}
                    onChange={(e) => setDurumFiltre(e.target.value)}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                >
                    <option value="">Tüm Durumlar</option>
                    {Object.entries(DURUM_ETIKET).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                    ))}
                </select>
            </div>

            {/* Tablo */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                {loading ? (
                    <div className="flex justify-center items-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                    </div>
                ) : filtrelenmis.length === 0 ? (
                    <div className="text-center py-20 text-gray-400">
                        <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>Üretim paleti bulunamadı</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 border-b border-gray-100">
                                <tr>
                                    {['Palet No', 'Lot / Ürün', 'Koli', 'Vardiya', 'Üretim Tarihi', 'Durum', 'İşlemler'].map((h) => (
                                        <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {filtrelenmis.map((p) => {
                                    const islem = islemPaletNo === p.palet_no;
                                    return (
                                        <tr key={p.palet_no} className="hover:bg-gray-50/50 transition-colors">
                                            <td className="px-4 py-3 font-mono font-semibold text-gray-900">{p.palet_no}</td>
                                            <td className="px-4 py-3">
                                                <div className="text-gray-900">{p.lot_no || `Lot #${p.lot_id}`}</div>
                                                {p.urun_isim && <div className="text-xs text-gray-400">{p.urun_isim}</div>}
                                            </td>
                                            <td className="px-4 py-3 text-gray-700">{p.koli_adedi}</td>
                                            <td className="px-4 py-3 text-gray-600">{p.vardiya || '—'}</td>
                                            <td className="px-4 py-3 text-gray-600">{p.uretim_tarihi || '—'}</td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${DURUM_BADGE[p.durum] || 'bg-gray-100 text-gray-600'}`}>
                                                    {DURUM_ETIKET[p.durum] || p.durum}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-1 flex-wrap">
                                                    {islem && <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />}

                                                    {/* Kabul Et (OLUSTURULDU veya KABUL_BEKLIYOR) */}
                                                    {isDepocuOrAdmin && [DURUM.OLUSTURULDU, DURUM.KABUL_BEKLIYOR].includes(p.durum) && (
                                                        <AksiyonButon
                                                            onClick={() => kabulEt(p.palet_no)}
                                                            icon={<CheckCircle className="w-3.5 h-3.5" />}
                                                            label="Kabul Et"
                                                            renk="emerald"
                                                            disabled={islem}
                                                        />
                                                    )}

                                                    {/* Yerleştirme sayfasına yönlendir (YERLESTIRME_BEKLIYOR) */}
                                                    {isDepocuOrAdmin && p.durum === DURUM.YERLESTIRME_BEKLIYOR && (
                                                        <AksiyonButon
                                                            onClick={() => toast('Yerleştirme için Üretimden Kabul sayfasından raf barkodu okutun', { icon: '📍' })}
                                                            icon={<MapPin className="w-3.5 h-3.5" />}
                                                            label="Yerleştir"
                                                            renk="blue"
                                                            disabled={islem}
                                                        />
                                                    )}

                                                    {/* Karantinaya Al */}
                                                    {isKaliteYetkili && p.durum === DURUM.KABUL_EDILDI && (
                                                        <AksiyonButon
                                                            onClick={() => { setSebepModal({ tip: 'karantina', paletNo: p.palet_no }); setSebepText(''); }}
                                                            icon={<ShieldAlert className="w-3.5 h-3.5" />}
                                                            label="Karantina"
                                                            renk="red"
                                                            disabled={islem}
                                                        />
                                                    )}

                                                    {/* Karantinadan Çıkar */}
                                                    {isKaliteYetkili && p.durum === DURUM.KARANTINA && (
                                                        <AksiyonButon
                                                            onClick={() => { setSebepModal({ tip: 'karantina-cikar', paletNo: p.palet_no }); setSebepText(''); }}
                                                            icon={<ShieldCheck className="w-3.5 h-3.5" />}
                                                            label="Çıkar"
                                                            renk="emerald"
                                                            disabled={islem}
                                                        />
                                                    )}

                                                    {/* İptal */}
                                                    {isAdmin && [DURUM.OLUSTURULDU, DURUM.KABUL_BEKLIYOR].includes(p.durum) && (
                                                        <AksiyonButon
                                                            onClick={() => { setSebepModal({ tip: 'iptal', paletNo: p.palet_no }); setSebepText(''); }}
                                                            icon={<Ban className="w-3.5 h-3.5" />}
                                                            label="İptal"
                                                            renk="gray"
                                                            disabled={islem}
                                                        />
                                                    )}

                                                    {/* Etiket Oluştur (şablon bazlı) */}
                                                    <AksiyonButon
                                                        onClick={() => setEtiketModalPaletNo(p.palet_no)}
                                                        icon={<Download className="w-3.5 h-3.5" />}
                                                        label="Etiket"
                                                        renk="slate"
                                                        disabled={islem}
                                                    />
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Yeni Palet Modalı */}
            {yeniModal && (
                <Modal baslik="Yeni Üretim Paleti" onKapat={() => { setYeniModal(false); formuSifirla(); }} genisMi>
                    <form onSubmit={paletOlustur} className="space-y-4">
                        {/* Zorunlu alanlar */}
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Depo <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={formData.depo_id}
                                    onChange={(e) => setFormData({ ...formData, depo_id: e.target.value })}
                                    required
                                    disabled={!isAdmin && !!user?.depo_id}
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-gray-50 disabled:text-gray-600"
                                >
                                    <option value="">Depo seçin...</option>
                                    {depolar.map((d) => (
                                        <option key={d.id} value={d.id}>{d.isim || `Depo #${d.id}`}</option>
                                    ))}
                                </select>
                                {!isAdmin && user?.depo_id && (
                                    <p className="text-xs text-gray-400 mt-1">Atanmış depo — değiştirilemez</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Lot <span className="text-red-500">*</span>
                                </label>
                                <select
                                    value={formData.lot_id}
                                    onChange={(e) => setFormData({ ...formData, lot_id: e.target.value })}
                                    required
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                >
                                    <option value="">Lot seçin...</option>
                                    {lotlar.map((l) => (
                                        <option key={l.id} value={l.id}>{l.lot_no || `#${l.id}`}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <FormField label="Koli Adedi *" type="number" min="1" required
                                value={formData.koli_adedi}
                                onChange={(v) => setFormData({ ...formData, koli_adedi: v })} />
                            <FormField label="Palet Ağırlığı (kg)" type="number" min="0.1" step="0.1"
                                value={formData.palet_kg}
                                onChange={(v) => setFormData({ ...formData, palet_kg: v })} />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <FormField label="Vardiya" type="text" placeholder="A / B / C"
                                value={formData.vardiya}
                                onChange={(v) => setFormData({ ...formData, vardiya: v })} />
                            <FormField label="Üretim Tarihi" type="date"
                                value={formData.uretim_tarihi}
                                onChange={(v) => setFormData({ ...formData, uretim_tarihi: v })} />
                        </div>

                        {/* Üretim meta — opsiyonel */}
                        <div className="pt-2 border-t border-gray-100">
                            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                                İzlenebilirlik (opsiyonel)
                            </p>
                            <div className="grid grid-cols-2 gap-3">
                                <FormField label="Üretim Hattı" type="text" placeholder="HAT-1"
                                    value={formData.uretim_hatti}
                                    onChange={(v) => setFormData({ ...formData, uretim_hatti: v })} />
                                <FormField label="Makine Kodu" type="text" placeholder="M-07"
                                    value={formData.makine_kodu}
                                    onChange={(v) => setFormData({ ...formData, makine_kodu: v })} />
                            </div>
                            <div className="grid grid-cols-3 gap-3 mt-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Operatör</label>
                                    <select
                                        value={formData.operator_kullanici_id}
                                        onChange={(e) => setFormData({ ...formData, operator_kullanici_id: e.target.value })}
                                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    >
                                        <option value="">—</option>
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

                        <div className="flex justify-end gap-2 pt-2">
                            <button type="button" onClick={() => { setYeniModal(false); formuSifirla(); }}
                                className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                                İptal
                            </button>
                            <button type="submit"
                                className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium">
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

            {/* Sebep Modalı (karantina / iptal) */}
            {sebepModal && (
                <Modal
                    baslik={
                        sebepModal.tip === 'karantina' ? 'Karantinaya Al' :
                        sebepModal.tip === 'karantina-cikar' ? 'Karantinadan Çıkar' : 'Paleti İptal Et'
                    }
                    onKapat={() => setSebepModal(null)}
                >
                    <div className="space-y-4">
                        <p className="text-sm text-gray-600">
                            <span className="font-mono font-semibold">{sebepModal.paletNo}</span> için işlem gerekçesi:
                        </p>
                        <textarea
                            autoFocus
                            value={sebepText}
                            onChange={(e) => setSebepText(e.target.value)}
                            placeholder="Sebep girin..."
                            required={sebepModal.tip === 'iptal'}
                            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none h-24"
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setSebepModal(null)}
                                className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                                Vazgeç
                            </button>
                            <button
                                onClick={sebepliIslem}
                                disabled={sebepModal.tip === 'iptal' && !sebepText.trim()}
                                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50"
                            >
                                Onayla
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
        amber:   'bg-amber-50 text-amber-700 hover:bg-amber-100 border-amber-200',
        emerald: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border-emerald-200',
        blue:    'bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200',
        red:     'bg-red-50 text-red-700 hover:bg-red-100 border-red-200',
        gray:    'bg-gray-50 text-gray-600 hover:bg-gray-100 border-gray-200',
        slate:   'bg-slate-50 text-slate-600 hover:bg-slate-100 border-slate-200',
    };
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            title={label}
            className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border transition-colors disabled:opacity-40 ${renkler[renk] || renkler.gray}`}
        >
            {icon}
            <span className="hidden sm:inline">{label}</span>
        </button>
    );
}

function Modal({ baslik, onKapat, children, genisMi }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
            <div className={`bg-white rounded-2xl shadow-xl w-full ${genisMi ? 'max-w-2xl' : 'max-w-md'} max-h-[90vh] flex flex-col`}>
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 flex-shrink-0">
                    <h2 className="font-semibold text-gray-900">{baslik}</h2>
                    <button onClick={onKapat} className="p-1 rounded-lg hover:bg-gray-100">
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>
                <div className="px-6 py-5 overflow-y-auto">{children}</div>
            </div>
        </div>
    );
}

function FormField({ label, onChange, ...props }) {
    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
            <input
                {...props}
                onChange={(e) => onChange(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
        </div>
    );
}
