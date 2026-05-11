/**
 * BelgeFotograflaPage — Mobil terminal üzerinde irsaliye/fatura fotoğrafı
 * çekip Doc-AI servisine yükleyen tek-ekran akış.
 *
 * Akış:
 *  1) Operatör "Belgeyi Çek" düğmesine basar → tam ekran kamera açılır.
 *  2) Frame alındıktan sonra otomatik kırpma denenir (imageCropper),
 *     başarısız olursa orijinal frame kullanılır.
 *  3) Önizleme ekranında "Yeniden Çek" veya "Yükle ve İşle" seçenekleri.
 *  4) Yükleme tamamlandığında /mal-kabul/taslak/:id sayfasına state ile yönlenir
 *     (önceki sayfalarda olduğu gibi local preview blob URL devredilir).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { motion as Motion } from 'framer-motion';
import {
    AlertTriangle,
    ArrowLeft,
    Camera,
    CheckCircle2,
    CloudUpload,
    Image as ImageIcon,
    Loader2,
    RotateCcw,
    Warehouse,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useDepolarQuery } from '../../queries/locationQueries';
import { useBelgeYukleMutation } from '../../queries/belgeTaslagiQueries';
import { responseData } from '../../queries/queryUtils';
import { autoCropDocument } from '../../utils/imageCropper';
import { hataMetni } from '../../utils/hata';
import BelgeKameraOverlay from '../../components/terminal/BelgeKameraOverlay';

const asArray = (data) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.items)) return data.items;
    if (Array.isArray(data?.data)) return data.data;
    return [];
};

const depoLabel = (depo) =>
    depo?.ad || depo?.depo_adi || depo?.isim || `Depo #${depo?.id}`;

const formatSize = (bytes) => {
    if (!Number.isFinite(bytes)) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const blobToFile = (blob, suggestedName = 'irsaliye.jpg') => {
    if (blob instanceof File) return blob;
    return new File([blob], suggestedName, { type: blob.type || 'image/jpeg', lastModified: Date.now() });
};

const buildFileName = () => {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    return `irsaliye-${stamp}.jpg`;
};

export default function BelgeFotograflaPage() {
    const navigate = useNavigate();
    const { user } = useAuth();

    const depolarQuery = useDepolarQuery();
    const uploadMutation = useBelgeYukleMutation();
    const depolar = asArray(depolarQuery.data);

    const userDepoId = user?.depo_id || user?.depo?.id;
    const defaultDepo = useMemo(
        () => depolar.find((d) => Number(d.id) === Number(userDepoId)) || depolar[0],
        [depolar, userDepoId],
    );
    const [selectedDepoId, setSelectedDepoId] = useState('');
    const effectiveDepoId = selectedDepoId || (defaultDepo?.id ? String(defaultDepo.id) : '');

    const [cameraOpen, setCameraOpen] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [photo, setPhoto] = useState(null); // { blob, previewUrl, width, height, cropped }
    const [progress, setProgress] = useState(0);
    const previewUrlRef = useRef(null);
    const previewTransferredRef = useRef(false);

    const revokePreview = useCallback(() => {
        if (!previewUrlRef.current) return;
        if (!previewTransferredRef.current) {
            try { URL.revokeObjectURL(previewUrlRef.current); } catch { /* ignore */ }
        }
        previewUrlRef.current = null;
        previewTransferredRef.current = false;
    }, []);

    useEffect(() => () => revokePreview(), [revokePreview]);

    const handleCapture = useCallback(async ({ blob }) => {
        setCameraOpen(false);
        setProcessing(true);
        try {
            const { blob: croppedBlob, cropped } = await autoCropDocument(blob).catch(() => ({
                blob,
                cropped: false,
            }));
            const finalBlob = croppedBlob || blob;
            revokePreview();
            const url = URL.createObjectURL(finalBlob);
            previewUrlRef.current = url;
            previewTransferredRef.current = false;
            setPhoto({
                blob: finalBlob,
                previewUrl: url,
                size: finalBlob.size,
                cropped,
            });
            setProgress(0);
        } catch (err) {
            toast.error(hataMetni(err, 'Fotoğraf işlenemedi'));
        } finally {
            setProcessing(false);
        }
    }, [revokePreview]);

    const retake = () => {
        revokePreview();
        setPhoto(null);
        setProgress(0);
        setCameraOpen(true);
    };

    const handleUpload = async () => {
        if (!effectiveDepoId) {
            toast.error('Depo seçin');
            return;
        }
        if (!photo) return;

        const file = blobToFile(photo.blob, buildFileName());
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
            previewTransferredRef.current = true;
            toast.success('Belge işlendi, taslak açılıyor');
            navigate(`/mal-kabul/taslak/${taslak.id}`, {
                state: {
                    localPreviewUrl: photo.previewUrl,
                    fileName: file.name,
                    fileType: file.type,
                },
            });
        } catch (err) {
            toast.error(hataMetni(err, 'Belge yüklenemedi'));
        }
    };

    const isUploading = uploadMutation.isPending;
    const canShoot = Boolean(effectiveDepoId) && !isUploading && !processing;

    return (
        <div className="mx-auto max-w-md space-y-5 p-4 pb-32">
            {/* Üst başlık */}
            <header className="flex items-start justify-between gap-3 px-1">
                <button
                    type="button"
                    onClick={() => navigate(-1)}
                    aria-label="Geri"
                    className="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200/70 bg-white/80 text-slate-600 backdrop-blur transition active:scale-90 dark:border-slate-800/70 dark:bg-zinc-900/80 dark:text-slate-300"
                >
                    <ArrowLeft className="h-5 w-5" />
                </button>
                <div className="min-w-0 flex-1 text-right">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                        Doc AI · Mobil
                    </p>
                    <h1 className="mt-0.5 text-xl font-black tracking-tight text-slate-900 dark:text-white">
                        Belge Çek
                    </h1>
                </div>
            </header>

            {/* Depo seçimi */}
            <section className="rounded-[24px] border border-slate-200/60 bg-white/85 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.04)] backdrop-blur-md dark:border-slate-800/60 dark:bg-zinc-900/80 dark:shadow-[0_4px_20px_rgba(0,0,0,0.25)]">
                <label
                    htmlFor="terminal-depo"
                    className="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400"
                >
                    <Warehouse className="h-3.5 w-3.5" />
                    Depo
                </label>
                <select
                    id="terminal-depo"
                    value={effectiveDepoId}
                    onChange={(e) => setSelectedDepoId(e.target.value)}
                    disabled={isUploading || depolarQuery.isLoading}
                    className="h-12 w-full rounded-2xl border border-slate-200 bg-white px-3 text-base font-semibold text-slate-800 outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100 disabled:text-slate-500 dark:border-slate-700 dark:bg-zinc-950 dark:text-slate-100 dark:focus:border-emerald-500 dark:focus:ring-emerald-900/40"
                >
                    <option value="">Depo seçin</option>
                    {depolar.map((depo) => (
                        <option key={depo.id} value={depo.id}>{depoLabel(depo)}</option>
                    ))}
                </select>
            </section>

            {/* Bilgilendirme */}
            <div className="rounded-2xl border border-amber-200/70 bg-amber-50/80 px-4 py-3 text-[13px] leading-snug text-amber-900 backdrop-blur dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
                <div className="flex gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <p>AI çıktısı onaydan önce mutlaka kontrol edilmelidir. Düşük güven puanlı alanlar önizlemede vurgulanır.</p>
                </div>
            </div>

            {/* Çekim / önizleme alanı */}
            {!photo ? (
                <CaptureCard
                    onShoot={() => setCameraOpen(true)}
                    disabled={!canShoot}
                    processing={processing}
                    needsDepo={!effectiveDepoId}
                />
            ) : (
                <PreviewCard
                    photo={photo}
                    isUploading={isUploading}
                    progress={progress}
                    onRetake={retake}
                    onUpload={handleUpload}
                    canUpload={canShoot}
                />
            )}

            <BelgeKameraOverlay
                open={cameraOpen}
                onCapture={handleCapture}
                onClose={() => setCameraOpen(false)}
            />
        </div>
    );
}

function CaptureCard({ onShoot, disabled, processing, needsDepo }) {
    return (
        <Motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="relative overflow-hidden rounded-[28px] border border-slate-200/70 bg-white/85 p-5 shadow-[0_4px_20px_rgba(0,0,0,0.04)] backdrop-blur-md dark:border-slate-800/70 dark:bg-zinc-900/80 dark:shadow-[0_4px_20px_rgba(0,0,0,0.25)]"
        >
            <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-emerald-400/15 blur-3xl" />
            <div className="relative z-10 flex flex-col items-center gap-4 py-2 text-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-[26px] bg-gradient-to-br from-emerald-400 to-emerald-600 text-white shadow-lg shadow-emerald-500/30">
                    <Camera className="h-9 w-9" strokeWidth={2.4} />
                </div>
                <div>
                    <h2 className="text-lg font-black tracking-tight text-slate-900 dark:text-white">
                        İrsaliyenin fotoğrafını çek
                    </h2>
                    <p className="mt-1 text-[13px] font-medium text-slate-500 dark:text-slate-400">
                        Belgeyi düz bir zemine koy, çerçeveye hizala ve çek.
                    </p>
                </div>

                <Motion.button
                    type="button"
                    onClick={onShoot}
                    disabled={disabled}
                    whileTap={{ scale: 0.96 }}
                    className="mt-2 inline-flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-5 text-base font-bold text-white shadow-lg shadow-emerald-600/30 transition active:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none dark:disabled:bg-slate-700"
                >
                    {processing ? (
                        <>
                            <Loader2 className="h-5 w-5 animate-spin" />
                            İşleniyor…
                        </>
                    ) : (
                        <>
                            <Camera className="h-5 w-5" strokeWidth={2.4} />
                            Kamerayı Aç
                        </>
                    )}
                </Motion.button>

                {needsDepo && (
                    <p className="text-[12px] font-semibold text-amber-600 dark:text-amber-400">
                        Devam etmek için depo seçin.
                    </p>
                )}
            </div>
        </Motion.section>
    );
}

function PreviewCard({ photo, isUploading, progress, onRetake, onUpload, canUpload }) {
    return (
        <Motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-3 rounded-[28px] border border-slate-200/70 bg-white/90 p-4 shadow-[0_4px_20px_rgba(0,0,0,0.04)] backdrop-blur-md dark:border-slate-800/70 dark:bg-zinc-900/85 dark:shadow-[0_4px_20px_rgba(0,0,0,0.25)]"
        >
            <div className="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 px-3 py-2 dark:bg-zinc-950/60">
                <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                        <ImageIcon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                        <p className="truncate text-[13px] font-bold text-slate-900 dark:text-white">
                            Hazır
                        </p>
                        <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                            {formatSize(photo.size)}
                            {photo.cropped ? ' · Otomatik kırpıldı' : ''}
                        </p>
                    </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2.5 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20">
                    <CheckCircle2 className="h-3 w-3" />
                    Önizleme
                </span>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-zinc-950">
                <img
                    src={photo.previewUrl}
                    alt="Çekilen belge"
                    className="block h-auto max-h-[60vh] w-full object-contain"
                />
            </div>

            {isUploading && (
                <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        <span>Yükleniyor</span>
                        <span>%{progress}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-zinc-800">
                        <Motion.div
                            className="h-2 rounded-full bg-emerald-500"
                            animate={{ width: `${progress}%` }}
                            transition={{ ease: 'easeOut', duration: 0.25 }}
                        />
                    </div>
                </div>
            )}

            <div className="grid grid-cols-2 gap-3 pt-1">
                <Motion.button
                    type="button"
                    onClick={onRetake}
                    disabled={isUploading}
                    whileTap={{ scale: 0.96 }}
                    className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white text-sm font-bold text-slate-700 transition active:bg-slate-100 disabled:opacity-60 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-200"
                >
                    <RotateCcw className="h-4 w-4" />
                    Yeniden Çek
                </Motion.button>
                <Motion.button
                    type="button"
                    onClick={onUpload}
                    disabled={!canUpload}
                    whileTap={{ scale: 0.96 }}
                    className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-emerald-600 text-sm font-bold text-white shadow-md shadow-emerald-600/20 transition active:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none dark:disabled:bg-slate-700"
                >
                    {isUploading ? (
                        <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            İşleniyor…
                        </>
                    ) : (
                        <>
                            <CloudUpload className="h-4 w-4" />
                            Yükle ve İşle
                        </>
                    )}
                </Motion.button>
            </div>
        </Motion.section>
    );
}

