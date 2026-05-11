import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
    AlertTriangle,
    ArrowRight,
    CheckCircle2,
    FileText,
    Image,
    UploadCloud,
    Warehouse,
    X,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useDepolarQuery } from '../../queries/locationQueries';
import { useBelgeYukleMutation } from '../../queries/belgeTaslagiQueries';
import { responseData } from '../../queries/queryUtils';
import { hataMetni } from '../../utils/hata';

const asArray = (data) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data?.data)) return data.data;
    return [];
};

const depoLabel = (depo) =>
    depo?.ad || depo?.depo_adi || depo?.isim || `Depo #${depo?.id}`;

const formatFileSize = (size) => {
    if (!Number.isFinite(size)) return '';
    if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

const acceptedTypes = ['application/pdf', 'image/png', 'image/jpeg'];

export default function BelgeYuklePage() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const inputRef = useRef(null);
    const previewUrlRef = useRef(null);
    const transferredPreviewRef = useRef(false);
    const [selectedDepoId, setSelectedDepoId] = useState('');
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const [progress, setProgress] = useState(0);

    const depolarQuery = useDepolarQuery();
    const uploadMutation = useBelgeYukleMutation();
    const depolar = asArray(depolarQuery.data);
    const userDepoId = user?.depo_id || user?.depo?.id;
    const defaultDepo = depolar.find((depo) => Number(depo.id) === Number(userDepoId)) || depolar[0];
    const effectiveDepoId = selectedDepoId || (defaultDepo?.id ? String(defaultDepo.id) : '');

    useEffect(() => () => {
        if (!transferredPreviewRef.current && previewUrlRef.current) {
            URL.revokeObjectURL(previewUrlRef.current);
        }
    }, []);

    const setSelectedFile = (candidate) => {
        if (!candidate) return;
        const isAccepted = acceptedTypes.includes(candidate.type) || /\.(pdf|png|jpe?g)$/i.test(candidate.name);
        if (!isAccepted) {
            toast.error('PDF, PNG veya JPG belge yükleyin');
            return;
        }

        if (previewUrlRef.current) {
            URL.revokeObjectURL(previewUrlRef.current);
        }

        const nextPreviewUrl = URL.createObjectURL(candidate);
        previewUrlRef.current = nextPreviewUrl;
        transferredPreviewRef.current = false;
        setFile(candidate);
        setPreviewUrl(nextPreviewUrl);
        setProgress(0);
    };

    const handleDrop = (event) => {
        event.preventDefault();
        event.stopPropagation();
        setDragActive(false);
        setSelectedFile(event.dataTransfer.files?.[0]);
    };

    const handleDrag = (event) => {
        event.preventDefault();
        event.stopPropagation();
        setDragActive(event.type === 'dragenter' || event.type === 'dragover');
    };

    const clearFile = () => {
        if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
        transferredPreviewRef.current = false;
        setFile(null);
        setPreviewUrl('');
        setProgress(0);
        if (inputRef.current) inputRef.current.value = '';
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!effectiveDepoId) {
            toast.error('Depo seçin');
            return;
        }
        if (!file) {
            toast.error('Belge seçin');
            return;
        }

        try {
            const response = await uploadMutation.mutateAsync({
                depoId: effectiveDepoId,
                file,
                onUploadProgress: (event) => {
                    if (!event.total) return;
                    setProgress(Math.round((event.loaded * 100) / event.total));
                },
            });
            const taslak = responseData(response);
            transferredPreviewRef.current = true;
            toast.success('Belge işlendi, taslak açılıyor');
            navigate(`/mal-kabul/taslak/${taslak.id}`, {
                state: {
                    localPreviewUrl: previewUrl,
                    fileName: file.name,
                    fileType: file.type,
                },
            });
        } catch (error) {
            toast.error(hataMetni(error, 'Belge işlenemedi'));
        }
    };

    const isUploading = uploadMutation.isPending;
    const isImage = file?.type?.startsWith('image/');
    const isPdf = file?.type === 'application/pdf' || /\.pdf$/i.test(file?.name || '');

    return (
        <div className="min-h-full bg-slate-50 px-4 py-5 text-slate-900 dark:bg-slate-950 dark:text-slate-100 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-6xl space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-400">
                            Gelen Mal
                        </p>
                        <h1 className="mt-1 text-2xl font-bold tracking-tight">Belge AI kabul</h1>
                        <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                            İrsaliye PDF veya görselini yükleyin; sistem taslak mal kabul satırlarını önizleme ekranına taşır.
                        </p>
                    </div>
                    <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                        <span className="font-semibold">Durum:</span> Taslak oluşturma
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
                    <section className="space-y-4 rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <div>
                            <label htmlFor="depo_id" className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                                <Warehouse className="h-4 w-4 text-slate-500" />
                                Depo
                            </label>
                            <select
                                id="depo_id"
                                value={effectiveDepoId}
                                onChange={(event) => setSelectedDepoId(event.target.value)}
                                disabled={isUploading || depolarQuery.isLoading}
                                className="h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100 disabled:bg-slate-100 disabled:text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:ring-sky-900/40"
                            >
                                <option value="">Depo seçin</option>
                                {depolar.map((depo) => (
                                    <option key={depo.id} value={depo.id}>{depoLabel(depo)}</option>
                                ))}
                            </select>
                        </div>

                        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-200">
                            <div className="flex gap-2">
                                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                                <p>AI çıktısı onaydan önce mutlaka kontrol edilmelidir. Eksik ürün eşleşmeleri önizlemede düzeltilebilir.</p>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isUploading || !file || !effectiveDepoId}
                            className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-sky-600 px-4 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
                        >
                            {isUploading ? 'İşleniyor...' : 'Taslak oluştur'}
                            <ArrowRight className="h-4 w-4" />
                        </button>

                        {isUploading && (
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
                                    <span>Yükleme</span>
                                    <span>%{progress}</span>
                                </div>
                                <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                                    <div
                                        className="h-2 rounded-full bg-sky-500 transition-all"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </section>

                    <section className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <input
                            ref={inputRef}
                            type="file"
                            accept="application/pdf,image/png,image/jpeg"
                            onChange={(event) => setSelectedFile(event.target.files?.[0])}
                            className="sr-only"
                        />

                        {!file ? (
                            <button
                                type="button"
                                onClick={() => inputRef.current?.click()}
                                onDrop={handleDrop}
                                onDragEnter={handleDrag}
                                onDragOver={handleDrag}
                                onDragLeave={handleDrag}
                                className={`flex min-h-[420px] w-full flex-col items-center justify-center rounded-md border-2 border-dashed px-6 text-center transition ${
                                    dragActive
                                        ? 'border-sky-400 bg-sky-50 dark:border-sky-500 dark:bg-sky-950/30'
                                        : 'border-slate-300 bg-slate-50 hover:border-sky-300 hover:bg-sky-50/50 dark:border-slate-700 dark:bg-slate-950/40 dark:hover:border-sky-700 dark:hover:bg-sky-950/20'
                                }`}
                            >
                                <UploadCloud className="h-12 w-12 text-sky-500" />
                                <span className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                                    Belgeyi buraya bırakın
                                </span>
                                <span className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                                    veya dosya seçmek için tıklayın
                                </span>
                                <span className="mt-4 rounded-md bg-white px-3 py-1.5 text-xs font-semibold text-slate-500 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:ring-slate-700">
                                    PDF, PNG, JPG
                                </span>
                            </button>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-800 dark:bg-slate-950/40">
                                    <div className="flex min-w-0 items-center gap-3">
                                        <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-md bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300">
                                            {isImage ? <Image className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{file.name}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">{formatFileSize(file.size)}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="inline-flex h-8 items-center gap-1 rounded-md bg-emerald-50 px-2.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:ring-emerald-900">
                                            <CheckCircle2 className="h-3.5 w-3.5" />
                                            Hazır
                                        </span>
                                        <button
                                            type="button"
                                            onClick={clearFile}
                                            disabled={isUploading}
                                            title="Dosyayı kaldır"
                                            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition hover:bg-slate-200 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="h-[420px] overflow-hidden rounded-md border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-950">
                                    {isImage ? (
                                        <img src={previewUrl} alt="Belge önizleme" className="h-full w-full object-contain" />
                                    ) : isPdf ? (
                                        <object data={previewUrl} type="application/pdf" className="h-full w-full">
                                            <div className="flex h-full items-center justify-center p-6 text-center text-sm text-slate-500">
                                                PDF önizlemesi tarayıcıda açılamadı.
                                            </div>
                                        </object>
                                    ) : (
                                        <div className="flex h-full flex-col items-center justify-center text-slate-500">
                                            <FileText className="h-12 w-12" />
                                            <p className="mt-3 text-sm">Önizleme desteklenmiyor</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </section>
                </form>
            </div>
        </div>
    );
}
