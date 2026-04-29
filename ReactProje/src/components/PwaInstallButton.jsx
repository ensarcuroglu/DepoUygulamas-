import { useEffect, useState, useCallback } from 'react';
import { Download } from 'lucide-react';
import toast from 'react-hot-toast';

function getInitialStandalone() {
    if (typeof window === 'undefined') return false;
    return (
        window.matchMedia?.('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
    );
}

export default function PwaInstallButton() {
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [installed, setInstalled] = useState(getInitialStandalone);

    useEffect(() => {
        if (installed) return;

        const onBeforeInstall = (e) => {
            e.preventDefault();
            setDeferredPrompt(e);
        };
        const onInstalled = () => {
            setInstalled(true);
            setDeferredPrompt(null);
            toast.success('Uygulama ana ekrana eklendi.');
        };

        window.addEventListener('beforeinstallprompt', onBeforeInstall);
        window.addEventListener('appinstalled', onInstalled);
        return () => {
            window.removeEventListener('beforeinstallprompt', onBeforeInstall);
            window.removeEventListener('appinstalled', onInstalled);
        };
    }, [installed]);

    const handleInstall = useCallback(async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome !== 'accepted') {
            toast('Yükleme iptal edildi.', { icon: 'i' });
        }
        setDeferredPrompt(null);
    }, [deferredPrompt]);

    if (installed || !deferredPrompt) return null;

    return (
        <button
            onClick={handleInstall}
            title="Uygulamayı yükle"
            className="hidden sm:flex items-center gap-2 h-10 px-3 rounded-2xl
                bg-blue-50 dark:bg-blue-500/10 border border-blue-200/60 dark:border-blue-500/20
                text-blue-700 dark:text-blue-300 text-[13px] font-semibold
                hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-all active:scale-95"
        >
            <Download className="w-4 h-4 stroke-[2.5px]" />
            <span>Yükle</span>
        </button>
    );
}
