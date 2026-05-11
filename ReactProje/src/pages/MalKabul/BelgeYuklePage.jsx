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
                    <section className="space-y-4 rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
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
                                className="h-11 w-full rounded-xl border border-slate-200/60 bg-slate-50/50 px-4 text-sm text-slate-800 outline-none transition-all duration-300 focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-500/10 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800/60 dark:bg-slate-950/50 dark:text-slate-100 dark:focus:border-sky-500 dark:focus:bg-slate-900"
                            >
                                <option value="">Depo seçin</option>
                                {depolar.map((depo) => (
                                    <option key={depo.id} value={depo.id}>{depoLabel(depo)}</option>
                                ))}
                            </select>
                        </div>

                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
                            <div className="flex gap-3">
                                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                                <p>AI çıktısı onaydan önce mutlaka kontrol edilmelidir. Eksik ürün eşleşmeleri önizlemede düzeltilebilir.</p>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isUploading || !file || !effectiveDepoId}
                            className="inline-flex h-12 w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-sky-600 px-4 text-sm font-semibold text-white transition-all duration-300 hover:bg-sky-500 hover:shadow-lg hover:shadow-sky-500/25 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:hover:scale-100 disabled:hover:shadow-none dark:disabled:bg-slate-800"
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
                                <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                                    <div
                                        className="h-full rounded-full bg-sky-500 transition-all duration-500 ease-out"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </section>

                    <section className="rounded-xl border border-slate-200/60 bg-white/90 p-5 shadow-sm backdrop-blur-md dark:border-slate-800/60 dark:bg-slate-900/90">
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
                                className={`group flex min-h-[420px] w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 text-center transition-all duration-300 ${
                                    dragActive
                                        ? 'border-sky-500 bg-sky-50/80 dark:bg-sky-500/10'
                                        : 'border-slate-300/80 bg-slate-50/50 hover:border-sky-400 hover:bg-sky-50/30 dark:border-slate-700/80 dark:bg-slate-950/30 dark:hover:border-sky-500/80 dark:hover:bg-sky-900/20'
                                }`}
                            >
                                <div className={`rounded-full p-4 transition-colors duration-300 ${dragActive ? 'bg-sky-100 dark:bg-sky-500/20' : 'bg-slate-100 group-hover:bg-sky-50 dark:bg-slate-800 dark:group-hover:bg-sky-900/30'}`}>
                                    <UploadCloud className={`h-8 w-8 ${dragActive ? 'text-sky-600 dark:text-sky-400' : 'text-slate-500 group-hover:text-sky-500 dark:text-slate-400 dark:group-hover:text-sky-400'}`} />
                                </div>
                                <span className="mt-4 text-base font-semibold text-slate-800 dark:text-slate-200">
                                    Belgeyi buraya bırakın
                                </span>
                                <span className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                                    veya dosya seçmek için tıklayın
                                </span>
                                <span className="mt-6 inline-flex rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-500 shadow-sm ring-1 ring-slate-200/60 backdrop-blur-sm dark:bg-slate-900/80 dark:text-slate-400 dark:ring-slate-700/60">
                                    PDF, PNG, JPG
                                </span>
                            </button>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200/60 bg-slate-50/80 p-3 backdrop-blur-sm dark:border-slate-800/60 dark:bg-slate-950/50">
                                    <div className="flex min-w-0 items-center gap-3">
                                        <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-white shadow-sm ring-1 ring-slate-200/60 dark:bg-slate-900 dark:ring-slate-800">
                                            {isImage ? <Image className="h-5 w-5 text-sky-600 dark:text-sky-400" /> : <FileText className="h-5 w-5 text-sky-600 dark:text-sky-400" />}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{file.name}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">{formatFileSize(file.size)}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="inline-flex h-8 items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 text-xs font-semibold text-emerald-600 ring-1 ring-emerald-500/20 dark:text-emerald-400">
                                            <CheckCircle2 className="h-3.5 w-3.5" />
                                            Hazır
                                        </span>
                                        <button
                                            type="button"
                                            onClick={clearFile}
                                            disabled={isUploading}
                                            title="Dosyayı kaldır"
                                            className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="h-[420px] overflow-hidden rounded-xl border border-slate-200/60 bg-slate-100/50 dark:border-slate-800/60 dark:bg-slate-950/50">
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
