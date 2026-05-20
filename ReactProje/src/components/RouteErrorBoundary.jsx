import { Component } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

const chunkLoadErrorPatterns = [
    'ChunkLoadError',
    'Loading chunk',
    'Failed to fetch dynamically imported module',
    'Importing a module script failed',
    'error loading dynamically imported module',
];

const isChunkLoadError = (error) => {
    const text = `${error?.name || ''} ${error?.message || ''}`;
    return chunkLoadErrorPatterns.some((pattern) => text.includes(pattern));
};

export default class RouteErrorBoundary extends Component {
    state = {
        error: null,
    };

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('[RouteErrorBoundary] Route render failed:', error, errorInfo);
    }

    componentDidUpdate(prevProps) {
        if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
            this.setState({ error: null });
        }
    }

    handleRetry = () => {
        this.setState({ error: null });
    };

    handleReload = () => {
        window.location.reload();
    };

    render() {
        const { error } = this.state;

        if (!error) {
            return this.props.children;
        }

        const chunkError = isChunkLoadError(error);
        const message = chunkError
            ? 'Sayfa dosyalari yenilendi veya eski cache devrede. Sayfayi yenileyerek temiz kopyayi yukleyebilirsiniz.'
            : 'Bu sayfa yuklenirken beklenmeyen bir hata olustu.';

        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950">
                <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300">
                        <AlertTriangle className="h-6 w-6" strokeWidth={2.2} />
                    </div>
                    <h1 className="mt-4 text-lg font-bold text-slate-900 dark:text-slate-100">
                        Sayfa yuklenemedi
                    </h1>
                    <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                        {message}
                    </p>
                    <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
                        <button
                            type="button"
                            onClick={this.handleReload}
                            className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-bold text-white transition-colors hover:bg-blue-700"
                        >
                            <RefreshCcw className="h-4 w-4" />
                            Sayfayi yenile
                        </button>
                        <button
                            type="button"
                            onClick={this.handleRetry}
                            className="inline-flex h-11 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-bold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                        >
                            Tekrar dene
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}
