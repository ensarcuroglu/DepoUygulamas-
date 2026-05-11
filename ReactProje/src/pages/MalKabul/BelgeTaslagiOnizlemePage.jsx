import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
    ArrowLeft,
    CalendarDays,
    CheckCircle2,
    ClipboardCheck,
    FileSearch,
    FileText,
    Loader2,
    Truck,
    Warehouse,
    XCircle,
} from 'lucide-react';
import KalemTablosu from '../../components/belge/KalemTablosu';
import AlanGuvenRozeti from '../../components/belge/AlanGuvenRozeti';
import { useDepolarQuery } from '../../queries/locationQueries';
import { useTedarikcilerQuery } from '../../queries/malKabulQueries';
import { useUrunlerQuery } from '../../queries/productQueries';
import {
    useBelgeTaslagiOnaylaMutation,
    useBelgeTaslagiQuery,
    useBelgeTaslagiReddetMutation,
} from '../../queries/belgeTaslagiQueries';
import { hataMetni } from '../../utils/hata';

const asArray = (data) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data?.data)) return data.data;
    return [];
};

const normalize = (value) =>
    String(value ?? '').trim().toLocaleLowerCase('tr-TR').replace(/\s+/g, ' ');

const fieldValue = (field) => {
    if (field && typeof field === 'object' && 'value' in field) return field.value ?? '';
    return field ?? '';
};

const fieldConfidence = (field) => {
    if (field && typeof field === 'object' && Number.isFinite(Number(field.confidence))) {
        return Number(field.confidence);
    }
    return undefined;
};

const dateInputValue = (value) => {
    const raw = String(fieldValue(value) ?? '').trim();
    if (!raw) return '';
    const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`;
    const dotted = raw.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
    if (dotted) {
        const day = dotted[1].padStart(2, '0');
        const month = dotted[2].padStart(2, '0');
        return `${dotted[3]}-${month}-${day}`;
    }
    return '';
};

const depoLabel = (depo) =>
    depo?.ad || depo?.depo_adi || depo?.isim || `Depo #${depo?.id}`;

const supplierName = (tedarikci) =>
    tedarikci?.firma_adi || tedarikci?.ad || tedarikci?.isim || '';

const productCode = (urun) =>
    urun?.barkod || urun?.ean || urun?.urun_kodu || urun?.kod || '';

const productName = (urun) =>
    urun?.isim || urun?.ad || urun?.urun_adi || '';

const findSupplier = (name, suppliers) => {
    const needle = normalize(name);
    if (!needle) return null;

    return suppliers.find((supplier) => normalize(supplierName(supplier)) === needle)
        || suppliers.find((supplier) => {
            const candidate = normalize(supplierName(supplier));
            return candidate && (needle.includes(candidate) || candidate.includes(needle));
        })
        || null;
};

const findProduct = ({ code, name }, products) => {
    const normalizedCode = normalize(code);
    const normalizedName = normalize(name);

    return products.find((product) => {
        const candidates = [
            productCode(product),
            product?.barkod,
            product?.ean,
            product?.kod,
            product?.urun_kodu,
        ].map(normalize);
        return normalizedCode && candidates.includes(normalizedCode);
    })
        || products.find((product) => normalize(productName(product)) === normalizedName)
        || null;
};

const payloadFromTaslak = (taslak) => {
    const raw = taslak?.ham_json || {};
    return raw?.taslak && typeof raw.taslak === 'object' ? raw.taslak : raw;
};

const confidenceFromTaslak = (taslak, payload) =>
    Number.isFinite(Number(taslak?.confidence_skoru))
        ? Number(taslak.confidence_skoru)
        : Number(payload?.confidence_score || 0);

const buildInitialForm = (taslak, payload, suppliers) => {
    const extractedSupplier = fieldValue(payload?.tedarikci || payload?.tedarikci_adi);
    const matchedSupplier = findSupplier(extractedSupplier, suppliers);

    return {
        tedarikci_id: matchedSupplier?.id ? String(matchedSupplier.id) : '',
        tedarikci_adi: supplierName(matchedSupplier) || extractedSupplier || '',
        depo_id: String(taslak?.depo_id || ''),
        tarih: dateInputValue(payload?.tarih),
        tir_plaka: fieldValue(payload?.tir_plaka || payload?.plaka),
        sofor_adi: fieldValue(payload?.sofor_adi || payload?.surucu_adi),
        irsaliye_no: fieldValue(payload?.irsaliye_no || payload?.belge_no),
    };
};

const buildInitialKalemler = (taslak, products) => {
    const payload = payloadFromTaslak(taslak);
    const rawKalemler = Array.isArray(payload?.kalemler) ? payload.kalemler : [];

    return rawKalemler.map((kalem, index) => {
        const code = fieldValue(kalem?.urun_kodu || kalem?.kod);
        const name = fieldValue(kalem?.ad || kalem?.urun_adi || kalem?.isim);
        const product = findProduct({ code, name }, products);

        return {
            local_id: `${taslak?.id || 'taslak'}-${index}`,
            urun_id: product?.id || '',
            urun_kodu: code || productCode(product),
            ad: productName(product) || name,
            miktar: fieldValue(kalem?.miktar),
            birim: fieldValue(kalem?.birim) || 'ADET',
            palet_no: fieldValue(kalem?.palet_no),
            lot_no: fieldValue(kalem?.lot_no),
            uretim_tarihi: dateInputValue(kalem?.uretim_tarihi),
            son_kullanma_tarihi: dateInputValue(kalem?.son_kullanma_tarihi),
            confidence: {
                urun_kodu: fieldConfidence(kalem?.urun_kodu || kalem?.kod),
                ad: fieldConfidence(kalem?.ad || kalem?.urun_adi || kalem?.isim),
                miktar: fieldConfidence(kalem?.miktar),
                birim: fieldConfidence(kalem?.birim),
                lot_no: fieldConfidence(kalem?.lot_no),
                uretim_tarihi: fieldConfidence(kalem?.uretim_tarihi),
                son_kullanma_tarihi: fieldConfidence(kalem?.son_kullanma_tarihi),
            },
        };
    });
};

const emptyToNull = (value) => {
    const text = String(value ?? '').trim();
    return text ? text : null;
};

const numericIdOrNull = (value) => {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : null;
};

const inputClass = 'h-11 w-full rounded-xl border border-slate-200/60 bg-slate-50/50 px-4 text-sm text-slate-800 outline-none transition-all duration-300 focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-500/10 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800/60 dark:bg-slate-950/50 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:bg-slate-900';

const Field = ({ label, icon: Icon, confidence, children }) => (
    <div>
        <div className="mb-1.5 flex min-h-6 items-center justify-between gap-2">
            <label className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {Icon && <Icon className="h-3.5 w-3.5" />}
                {label}
            </label>
            {confidence !== undefined && <AlanGuvenRozeti confidence={confidence} />}
        </div>
        {children}
    </div>
);

const LoadingState = () => (
    <div className="flex min-h-[60vh] items-center justify-center bg-slate-50 text-slate-500 dark:bg-slate-950 dark:text-slate-400">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Taslak yükleniyor...
    </div>
);

const ErrorState = ({ error }) => (
    <div className="min-h-full bg-slate-50 px-4 py-8 dark:bg-slate-950 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl rounded-md border border-rose-200 bg-white p-5 text-rose-700 shadow-sm dark:border-rose-900 dark:bg-slate-900 dark:text-rose-300">
            <div className="flex items-start gap-3">
                <XCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                <div>
                    <h1 className="font-semibold">Taslak açılamadı</h1>
                    <p className="mt-1 text-sm">{hataMetni(error, 'Belge taslağı bulunamadı')}</p>
                </div>
            </div>
        </div>
    </div>
);

function BelgeTaslagiEditor({
    id,
    taslak,
    depolar,
    tedarikciler,
    urunler,
    localPreviewUrl,
    fileName,
    fileType,
}) {
    const navigate = useNavigate();
    const payload = payloadFromTaslak(taslak);
    const raw = taslak?.ham_json || {};
    const confidence = confidenceFromTaslak(taslak, payload);
    const isClosed = Boolean(taslak?.durum && taslak.durum !== 'KABUL_BEKLIYOR');
    const [form, setForm] = useState(() => buildInitialForm(taslak, payload, tedarikciler));
    const [kalemler, setKalemler] = useState(() => buildInitialKalemler(taslak, urunler));
    const approveMutation = useBelgeTaslagiOnaylaMutation();
    const rejectMutation = useBelgeTaslagiReddetMutation();
    const isBusy = approveMutation.isPending || rejectMutation.isPending;
    const previewIsImage = fileType?.startsWith('image/');
    const previewIsPdf = fileType === 'application/pdf' || /\.pdf$/i.test(fileName || '');

    const updateForm = (field, value) => {
        setForm((current) => ({ ...current, [field]: value }));
    };

    const handleSupplierChange = (supplierId) => {
        const supplier = tedarikciler.find((item) => Number(item.id) === Number(supplierId));
        setForm((current) => ({
            ...current,
            tedarikci_id: supplierId,
            tedarikci_adi: supplier ? supplierName(supplier) : current.tedarikci_adi,
        }));
    };

    const buildApprovalPayload = () => {
        const candidateRows = kalemler.filter((kalem) =>
            kalem.urun_id
            || emptyToNull(kalem.urun_kodu)
            || emptyToNull(kalem.ad)
            || emptyToNull(kalem.miktar)
        );
        const cleanKalemler = candidateRows.map((kalem) => ({
            urun_id: numericIdOrNull(kalem.urun_id),
            urun_kodu: emptyToNull(kalem.urun_kodu),
            ad: emptyToNull(kalem.ad),
            miktar: Number(kalem.miktar),
            birim: emptyToNull(kalem.birim),
            palet_no: emptyToNull(kalem.palet_no),
            lot_no: emptyToNull(kalem.lot_no),
            uretim_tarihi: emptyToNull(kalem.uretim_tarihi),
            son_kullanma_tarihi: emptyToNull(kalem.son_kullanma_tarihi),
        }));

        if (!form.tedarikci_id && !emptyToNull(form.tedarikci_adi)) {
            throw new Error('Tedarikçi seçin veya adını girin');
        }
        if (!numericIdOrNull(form.depo_id)) {
            throw new Error('Depo seçin');
        }
        if (cleanKalemler.length === 0) {
            throw new Error('En az bir kalem ekleyin');
        }
        const invalidRow = cleanKalemler.find((kalem) => !Number.isFinite(kalem.miktar) || kalem.miktar <= 0);
        if (invalidRow) {
            throw new Error('Tüm kalemlerde miktar sıfırdan büyük olmalı');
        }

        return {
            tedarikci_id: numericIdOrNull(form.tedarikci_id),
            tedarikci_adi: emptyToNull(form.tedarikci_adi),
            depo_id: numericIdOrNull(form.depo_id),
            tarih: emptyToNull(form.tarih),
            tir_plaka: emptyToNull(form.tir_plaka),
            sofor_adi: emptyToNull(form.sofor_adi),
            kalemler: cleanKalemler,
        };
    };

    const handleApprove = async () => {
        try {
            const data = buildApprovalPayload();
            await approveMutation.mutateAsync({ id, data });
            toast.success('Mal kabul oluşturuldu');
            navigate('/gelen-mal/irsaliyeli');
        } catch (error) {
            toast.error(hataMetni(error, error.message || 'Taslak onaylanamadı'));
        }
    };

    const handleReject = async () => {
        if (!window.confirm('Bu belge taslağı reddedilsin mi?')) return;
        try {
            await rejectMutation.mutateAsync({
                id,
                data: { neden: 'Kullanıcı tarafından reddedildi' },
            });
            toast.success('Belge taslağı reddedildi');
            navigate('/mal-kabul/belge-yukle');
        } catch (error) {
            toast.error(hataMetni(error, 'Taslak reddedilemedi'));
        }
    };

    return (
        <div className="min-h-full bg-slate-50 px-4 py-5 text-slate-900 dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-7xl space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <button
                            type="button"
                            onClick={() => navigate('/mal-kabul/belge-yukle')}
                            className="mb-3 inline-flex h-9 cursor-pointer items-center gap-2 rounded-full border border-slate-200/60 bg-white/80 px-4 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-800/60 dark:bg-slate-900/80 dark:text-slate-300 dark:hover:bg-slate-800"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            Yükleme ekranı
                        </button>
                        <p className="text-xs font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-400">
                            Belge taslağı #{taslak?.id}
                        </p>
                        <h1 className="mt-1 text-2xl font-bold tracking-tight">Önizleme ve onay</h1>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <span className="inline-flex h-9 items-center rounded-full bg-white/80 px-4 text-sm font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200/60 backdrop-blur-sm dark:bg-slate-900/80 dark:text-slate-300 dark:ring-slate-800/60">
                            {taslak?.durum}
                        </span>
                        <AlanGuvenRozeti confidence={confidence} className="h-9 px-3 text-sm" />
                    </div>
                </div>

                {isClosed && (
                    <div className="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                        Bu taslak kapalı durumda. Alanlar yalnızca görüntülenebilir.
                    </div>
                )}

                <div className="grid gap-5 xl:grid-cols-[minmax(340px,440px)_minmax(0,1fr)]">
                    <aside className="space-y-4">
                        <section className="rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
                            <div className="mb-3 flex items-center justify-between gap-3">
                                <div className="flex items-center gap-2">
                                    <FileSearch className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                                    <h2 className="font-semibold">Belge önizleme</h2>
                                </div>
                                {fileName && <span className="max-w-[180px] truncate text-xs text-slate-500">{fileName}</span>}
                            </div>
                            <div className="h-[520px] overflow-hidden rounded-xl border border-slate-200/60 bg-slate-100/50 dark:border-slate-800/60 dark:bg-slate-950/50">
                                {localPreviewUrl && previewIsImage ? (
                                    <img src={localPreviewUrl} alt="Belge önizleme" className="h-full w-full object-contain" />
                                ) : localPreviewUrl && previewIsPdf ? (
                                    <object data={localPreviewUrl} type="application/pdf" className="h-full w-full">
                                        <div className="flex h-full items-center justify-center p-6 text-center text-sm text-slate-500">
                                            PDF önizlemesi tarayıcıda açılamadı.
                                        </div>
                                    </object>
                                ) : (
                                    <div className="flex h-full flex-col items-center justify-center p-6 text-center text-slate-500 dark:text-slate-400">
                                        <FileText className="h-12 w-12" />
                                        <p className="mt-3 text-sm font-semibold">Dosya önizlemesi bu oturumda yok</p>
                                        <p className="mt-1 text-xs">{taslak?.kaynak_dosya_yolu || 'Kaynak dosya yolu bulunamadı'}</p>
                                    </div>
                                )}
                            </div>
                        </section>

                        <section className="rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
                            <h2 className="mb-4 font-semibold">AI çıktısı</h2>
                            <dl className="grid gap-3 text-sm">
                                <div className="flex items-center justify-between gap-4">
                                    <dt className="text-slate-500 dark:text-slate-400">Model</dt>
                                    <dd className="truncate font-medium text-slate-800 dark:text-slate-100">{raw?.model || '-'}</dd>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <dt className="text-slate-500 dark:text-slate-400">Belge tipi</dt>
                                    <dd className="font-medium text-slate-800 dark:text-slate-100">{taslak?.belge_tipi || raw?.belge_tipi || '-'}</dd>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <dt className="text-slate-500 dark:text-slate-400">Durum</dt>
                                    <dd className="font-medium text-slate-800 dark:text-slate-100">{raw?.status || taslak?.durum || '-'}</dd>
                                </div>
                            </dl>
                        </section>
                    </aside>

                    <main className="space-y-5">
                        <section className="rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
                            <div className="mb-5 flex items-center gap-2">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400">
                                    <ClipboardCheck className="h-5 w-5" />
                                </div>
                                <h2 className="text-lg font-semibold">Mal kabul bilgileri</h2>
                            </div>

                            <div className="grid gap-4 lg:grid-cols-2">
                                <Field label="Tedarikçi" icon={Truck} confidence={fieldConfidence(payload?.tedarikci || payload?.tedarikci_adi)}>
                                    <input
                                        value={form.tedarikci_adi}
                                        onChange={(event) => updateForm('tedarikci_adi', event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                        placeholder="Tedarikçi adı"
                                    />
                                </Field>

                                <Field label="Tedarikçi eşleşmesi" icon={Truck}>
                                    <select
                                        value={form.tedarikci_id}
                                        onChange={(event) => handleSupplierChange(event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                    >
                                        <option value="">Eşleşme yok</option>
                                        {tedarikciler.map((tedarikci) => (
                                            <option key={tedarikci.id} value={tedarikci.id}>{supplierName(tedarikci)}</option>
                                        ))}
                                    </select>
                                </Field>

                                <Field label="Depo" icon={Warehouse}>
                                    <select
                                        value={form.depo_id}
                                        onChange={(event) => updateForm('depo_id', event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                    >
                                        <option value="">Depo seçin</option>
                                        {depolar.map((depo) => (
                                            <option key={depo.id} value={depo.id}>{depoLabel(depo)}</option>
                                        ))}
                                    </select>
                                </Field>

                                <Field label="Belge tarihi" icon={CalendarDays} confidence={fieldConfidence(payload?.tarih)}>
                                    <input
                                        type="date"
                                        value={form.tarih}
                                        onChange={(event) => updateForm('tarih', event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                    />
                                </Field>

                                <Field label="İrsaliye no" icon={FileText} confidence={fieldConfidence(payload?.irsaliye_no || payload?.belge_no)}>
                                    <input
                                        value={form.irsaliye_no}
                                        onChange={(event) => updateForm('irsaliye_no', event.target.value)}
                                        disabled
                                        className={inputClass}
                                        placeholder="Backend yeni mal kabul numarası üretir"
                                    />
                                </Field>

                                <Field label="Tır plaka" icon={Truck} confidence={fieldConfidence(payload?.tir_plaka || payload?.plaka)}>
                                    <input
                                        value={form.tir_plaka}
                                        onChange={(event) => updateForm('tir_plaka', event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                    />
                                </Field>

                                <Field label="Şoför" icon={Truck} confidence={fieldConfidence(payload?.sofor_adi || payload?.surucu_adi)}>
                                    <input
                                        value={form.sofor_adi}
                                        onChange={(event) => updateForm('sofor_adi', event.target.value)}
                                        disabled={isClosed || isBusy}
                                        className={inputClass}
                                    />
                                </Field>
                            </div>
                        </section>

                        <section className="rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
                            <KalemTablosu
                                kalemler={kalemler}
                                onChange={setKalemler}
                                urunler={urunler}
                                readonly={isClosed || isBusy}
                            />
                        </section>

                        <div className="sticky bottom-4 z-10 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200/60 bg-white/80 p-4 shadow-lg backdrop-blur-xl dark:border-slate-800/60 dark:bg-slate-900/80">
                            <button
                                type="button"
                                onClick={handleReject}
                                disabled={isClosed || isBusy}
                                className="inline-flex h-12 cursor-pointer items-center gap-2 rounded-xl border border-rose-200 bg-white px-5 text-sm font-semibold text-rose-700 transition-all duration-300 hover:bg-rose-50 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 dark:border-rose-900/60 dark:bg-slate-900 dark:text-rose-400 dark:hover:bg-rose-950/30"
                            >
                                {rejectMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
                                Reddet
                            </button>

                            <button
                                type="button"
                                onClick={handleApprove}
                                disabled={isClosed || isBusy}
                                className="inline-flex h-12 cursor-pointer items-center gap-2 rounded-xl bg-emerald-600 px-6 text-sm font-semibold text-white transition-all duration-300 hover:bg-emerald-500 hover:shadow-lg hover:shadow-emerald-500/25 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-emerald-600 dark:hover:bg-emerald-500"
                            >
                                {approveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                                Mal kabul oluştur
                            </button>
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
}

export default function BelgeTaslagiOnizlemePage() {
    const { id } = useParams();
    const location = useLocation();
    const taslakQuery = useBelgeTaslagiQuery(id);
    const depolarQuery = useDepolarQuery();
    const tedarikcilerQuery = useTedarikcilerQuery({ limit: 500 });
    const urunlerQuery = useUrunlerQuery({ limit: 500 });
    const localPreviewUrl = location.state?.localPreviewUrl;
    const fileName = location.state?.fileName;
    const fileType = location.state?.fileType;

    useEffect(() => () => {
        if (localPreviewUrl) URL.revokeObjectURL(localPreviewUrl);
    }, [localPreviewUrl]);

    if (
        taslakQuery.isLoading
        || depolarQuery.isLoading
        || tedarikcilerQuery.isLoading
        || urunlerQuery.isLoading
    ) {
        return <LoadingState />;
    }

    if (taslakQuery.isError) {
        return <ErrorState error={taslakQuery.error} />;
    }

    return (
        <BelgeTaslagiEditor
            key={taslakQuery.data?.id}
            id={id}
            taslak={taslakQuery.data}
            depolar={asArray(depolarQuery.data)}
            tedarikciler={asArray(tedarikcilerQuery.data)}
            urunler={asArray(urunlerQuery.data)}
            localPreviewUrl={localPreviewUrl}
            fileName={fileName}
            fileType={fileType}
        />
    );
}
