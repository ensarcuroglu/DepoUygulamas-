import { registerSW } from 'virtual:pwa-register';
import toast from 'react-hot-toast';

let updateSW;

export function setupPwa() {
    if (typeof window === 'undefined') return;
    if (!('serviceWorker' in navigator)) return;

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
