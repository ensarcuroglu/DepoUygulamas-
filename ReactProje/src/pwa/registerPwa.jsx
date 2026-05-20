import { registerSW } from 'virtual:pwa-register';
import toast from 'react-hot-toast';

let updateSW;

const shouldCleanDevPwa =
    import.meta.env.DEV && import.meta.env.VITE_PWA_DEV !== 'true';
const devCleanupReloadKey = 'depo:pwa-dev-cleanup-reloaded';

async function cleanupDevelopmentPwa() {
    try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registrations.map((registration) => registration.unregister()));

        if ('caches' in window) {
            const cacheNames = await window.caches.keys();
            await Promise.all(
                cacheNames
                    .filter((name) => name.startsWith('workbox-') || name.startsWith('depo-'))
                    .map((name) => window.caches.delete(name)),
            );
        }

        if (navigator.serviceWorker.controller && sessionStorage.getItem(devCleanupReloadKey) !== 'true') {
            sessionStorage.setItem(devCleanupReloadKey, 'true');
            window.location.reload();
            return;
        }

        if (!navigator.serviceWorker.controller) {
            sessionStorage.removeItem(devCleanupReloadKey);
        }
    } catch (error) {
        console.warn('[PWA] Development service worker cleanup failed:', error);
    }
}

export function setupPwa() {
    if (typeof window === 'undefined') return;
    if (!('serviceWorker' in navigator)) return;

    if (shouldCleanDevPwa) {
        void cleanupDevelopmentPwa();
        return;
    }

    updateSW = registerSW({
        immediate: true,
        onNeedRefresh() {
            toast(
                (t) => (
                    <div className="flex items-center gap-3">
                        <div className="text-[13px] font-semibold text-slate-800 dark:text-slate-100">
                            Yeni sürüm hazır
                            <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 pt-0.5">
                                Yenilemek için tıkla
                            </p>
                        </div>
                        <button
                            onClick={() => {
                                toast.dismiss(t.id);
                                updateSW?.(true);
                            }}
                            className="px-3 h-8 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-[12px] font-semibold transition-colors"
                        >
                            Yenile
                        </button>
                    </div>
                ),
                { duration: Infinity, id: 'pwa-update' },
            );
        },
        onOfflineReady() {
            toast.success('Uygulama çevrimdışı kullanıma hazır.', { duration: 3000 });
        },
        onRegisterError(error) {
            console.error('[PWA] Service worker kaydı başarısız:', error);
        },
    });
}
