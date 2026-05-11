import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    AlertTriangle,
    ArrowRight,
    ClipboardList,
    FileSearch,
    RefreshCw,
    SlidersHorizontal,
    Warehouse,
} from 'lucide-react';
import AlanGuvenRozeti from '../../components/belge/AlanGuvenRozeti';
import { useBelgeIncelemeKuyruguQuery } from '../../queries/belgeTaslagiQueries';
import { useDepolarQuery } from '../../queries/locationQueries';
import { hataMetni } from '../../utils/hata';

const asArray = (data) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data?.data)) return data.data;
    return [];
};

const depoLabel = (depo) =>
    depo?.ad || depo?.depo_adi || depo?.isim || `Depo #${depo?.id}`;

const payloadFromTaslak = (taslak) => {
    const raw = taslak?.ham_json || {};
    return raw?.taslak && typeof raw.taslak === 'object' ? raw.taslak : raw;
};

const fieldValue = (field) => {
    if (field && typeof field === 'object' && 'value' in field) return field.value ?? '';
    return field ?? '';
};

const formatDate = (value) => {
    if (!value) return '-';
    try {
        return new Intl.DateTimeFormat('tr-TR', {
            dateStyle: 'short',
            timeStyle: 'short',
        }).format(new Date(value));
    } catch {
        return String(value);
    }
};

const queueParams = ({ depoId, maxConfidence }) => ({
    limit: 100,
    max_confidence: Number(maxConfidence),
    ...(depoId ? { depo_id: Number(depoId) } : {}),
});

export default function BelgeIncelemeKuyruguPage() {
    const navigate = useNavigate();
    const [depoId, setDepoId] = useState('');
    const [maxConfidence, setMaxConfidence] = useState('0.6');
    const params = queueParams({ depoId, maxConfidence });
    const queueQuery = useBelgeIncelemeKuyruguQuery(params);
    const depolarQuery = useDepolarQuery();
    const taslaklar = asArray(queueQuery.data);
    const depolar = asArray(depolarQuery.data);

    const avgConfidence = taslaklar.length
        ? taslaklar.reduce((sum, item) => sum + Number(item.confidence_skoru || 0), 0) / taslaklar.length
        : 0;

    return (
        <div className="min-h-full bg-slate-50 px-4 py-5 text-slate-900 dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-7xl space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                            Belge AI kontrol masası
                        </p>
                        <h1 className="mt-1 text-2xl font-bold tracking-tight">İnceleme kuyruğu</h1>
                        <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                            Güven skoru eşiğin altında kalan belge taslaklarını operasyon onayından önce yakalayın.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={() => queueQuery.refetch()}
                        className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                        <RefreshCw className={`h-4 w-4 ${queueQuery.isFetching ? 'animate-spin' : ''}`} />
                        Yenile
                    </button>
                </div>

                <section className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Bekleyen taslak</span>
                            <ClipboardList className="h-5 w-5 text-slate-400" />
                        </div>
                        <p className="mt-2 text-3xl font-bold">{taslaklar.length}</p>
                    </div>
                    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Ortalama güven</span>
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                        </div>
                        <p className="mt-2 text-3xl font-bold">%{Math.round(avgConfidence * 100)}</p>
                    </div>
                    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Eşik</span>
                            <SlidersHorizontal className="h-5 w-5 text-slate-400" />
                        </div>
                        <p className="mt-2 text-3xl font-bold">%{Math.round(Number(maxConfidence) * 100)}</p>
                    </div>
                </section>

                <section className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <div className="grid gap-3 md:grid-cols-[minmax(180px,260px)_180px_auto] md:items-end">
                        <label className="block">
                            <span className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                <Warehouse className="h-3.5 w-3.5" />
                                Depo
                            </span>
                            <select
                                value={depoId}
                                onChange={(event) => setDepoId(event.target.value)}
                                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
                            >
                                <option value="">Tüm depolar</option>
                                {depolar.map((depo) => (
                                    <option key={depo.id} value={depo.id}>{depoLabel(depo)}</option>
                                ))}
                            </select>
                        </label>

                        <label className="block">
                            <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                Maks. güven
                            </span>
                            <select
                                value={maxConfidence}
                                onChange={(event) => setMaxConfidence(event.target.value)}
                                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
                            >
                                <option value="0.5">%50 altı</option>
                                <option value="0.6">%60 altı</option>
                                <option value="0.7">%70 altı</option>
                            </select>
                        </label>
                    </div>
                </section>

                <section className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
                        <div className="flex items-center gap-2">
                            <FileSearch className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                            <h2 className="font-semibold">Kontrol bekleyen belgeler</h2>
                        </div>
                    </div>

                    {queueQuery.isError ? (
                        <div className="p-6 text-sm text-rose-600 dark:text-rose-300">
                            {hataMetni(queueQuery.error, 'İnceleme kuyruğu alınamadı')}
                        </div>
                    ) : queueQuery.isLoading ? (
                        <div className="p-6 text-sm text-slate-500 dark:text-slate-400">Kuyruk yükleniyor...</div>
                    ) : taslaklar.length === 0 ? (
                        <div className="p-8 text-center">
                            <p className="font-semibold text-slate-700 dark:text-slate-200">Kuyruk temiz</p>
                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                Seçili eşik altında bekleyen belge taslağı yok.
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
                                <thead className="bg-slate-50 dark:bg-slate-950/40">
                                    <tr className="text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                        <th className="px-4 py-3">Taslak</th>
                                        <th className="px-4 py-3">Tedarikçi</th>
                                        <th className="px-4 py-3">Eksik alanlar</th>
                                        <th className="px-4 py-3">Güven</th>
                                        <th className="px-4 py-3">Oluşturma</th>
                                        <th className="px-4 py-3 text-right">İşlem</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                                    {taslaklar.map((taslak) => {
                                        const payload = payloadFromTaslak(taslak);
                                        const missingFields = payload.missing_fields || [];
                                        return (
                                            <tr key={taslak.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                                                <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-100">
                                                    #{taslak.id}
                                                </td>
                                                <td className="max-w-[260px] truncate px-4 py-3 text-slate-600 dark:text-slate-300">
                                                    {fieldValue(payload.tedarikci) || '-'}
                                                </td>
                                                <td className="px-4 py-3">
                                                    {missingFields.length > 0 ? (
                                                        <div className="flex max-w-[360px] flex-wrap gap-1.5">
                                                            {missingFields.slice(0, 4).map((field) => (
                                                                <span
                                                                    key={field}
                                                                    className="rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:ring-amber-900"
                                                                >
                                                                    {field}
                                                                </span>
                                                            ))}
                                                            {missingFields.length > 4 && (
                                                                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                                                                    +{missingFields.length - 4}
                                                                </span>
                                                            )}
                                                        </div>
                                                    ) : (
                                                        <span className="text-slate-400">Alan bazlı düşük güven</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <AlanGuvenRozeti confidence={taslak.confidence_skoru} />
                                                </td>
                                                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                                                    {formatDate(taslak.created_at)}
                                                </td>
                                                <td className="px-4 py-3 text-right">
                                                    <button
                                                        type="button"
                                                        onClick={() => navigate(`/mal-kabul/taslak/${taslak.id}`)}
                                                        className="inline-flex h-9 items-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white"
                                                    >
                                                        İncele
                                                        <ArrowRight className="h-4 w-4" />
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}
