/**
 * DepocuLayout — Depo operatörü arayüzü.
 *
 * Tasarım ilkeleri:
 * - Sidebar yok; menü değil görev odaklı navigasyon
 * - Bottom tab bar — büyük dokunmatik hedefler (≥48px), safe-area uyumlu
 * - Açık tema: yüksek okunabilirlik, saha koşullarına uygun, Glassmorphism detaylar
 * - URL namespace: /depocu/* — admin arayüzünden tam izolasyon
 */
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
    Home,
    PackageCheck,
    ArrowLeftRight,
    UserCircle,
    Warehouse,
    LogOut,
    Scan,
} from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';

// Terminal sekmesi /terminal/* namespace'ine gider — DepocuLayout'tan çıkış (bilinçli mod geçişi).
// Saha tabletinde dark TerminalLayout açılır; kullanıcı geri gelince /depocu'ya döner.
const TAB_ITEMS = [
    { to: '/depocu',            label: 'Ana Sayfa', icon: Home,           terminal: false },
    { to: '/depocu/mal-kabul',  label: 'Mal Kabul', icon: PackageCheck,   terminal: false },
    { to: '/terminal/gorevler', label: 'Terminal',  icon: Scan,           terminal: true  },
    { to: '/depocu/stok',       label: 'Stok',      icon: ArrowLeftRight, terminal: false },
    { to: '/depocu/profil',     label: 'Profil',    icon: UserCircle,     terminal: false },
];

function isTabActive(tabPath, currentPath) {
    if (tabPath === '/depocu') return currentPath === '/depocu';
    if (tabPath.startsWith('/terminal')) return false;
    return currentPath.startsWith(tabPath);
}

export default function DepocuLayout() {
    const { logout, user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = async () => {
        await logout?.();
        navigate('/login');
    };

    return (
        <div className="min-h-[100dvh] bg-slate-50/50 flex flex-col font-sans">
            <Toaster
                position="top-center"
                toastOptions={{
                    duration: 3500,
                    style: {
                        borderRadius: '16px',
                        background: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                        color: '#0f172a',
                        border: '1px solid rgba(226, 232, 240, 0.8)',
                        fontSize: '14px',
                        fontWeight: 600,
                        boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)',
                        padding: '12px 16px'
                    },
                    success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
                    error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
                }}
            />

            {/* Üst başlık - Glassmorphism */}
            <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 py-3 flex items-center justify-between transition-all">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <Warehouse className="w-5 h-5 text-white" strokeWidth={2.2} />
                    </div>
                    <div className="flex flex-col justify-center">
                        <p className="text-[10px] text-sky-600 uppercase tracking-[0.2em] font-bold leading-none mb-1">
                            Depo Operatörü
                        </p>
                        <p className="text-sm font-extrabold text-slate-800 leading-none">
                            {user?.ad_soyad || user?.kullanici_adi || 'Operatör'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center w-10 h-10 text-slate-400 hover:text-red-500 hover:bg-red-50 active:bg-red-100 rounded-2xl transition-all active:scale-95"
                    aria-label="Çıkış Yap"
                >
                    <LogOut className="w-5 h-5" strokeWidth={2} />
                </button>
            </header>

            {/* Sayfa içeriği - Alt tab için padding eklendi (safe-area dahil) */}
            <main className="flex-1 overflow-y-auto pb-[calc(5rem+env(safe-area-inset-bottom))]">
                <Outlet />
            </main>

            {/* Alt tab navigasyon - Glassmorphism & Safe Area */}
            <nav className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-slate-200/80 z-40 pb-[env(safe-area-inset-bottom)] shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.05)]">
                <div className="flex px-1 h-[4.5rem]">
                    {TAB_ITEMS.map((tab) => {
                        const TabIcon = tab.icon;
                        const active = isTabActive(tab.to, location.pathname);

                        if (tab.terminal) {
                            return (
                                <NavLink
                                    key={tab.to}
                                    to={tab.to}
                                    className="flex-1 flex flex-col items-center justify-center gap-1 transition-all active:scale-95 group relative"
                                >
                                    {/* Terminal Butonu - Vurgulu Merkez */}
                                    <div className="absolute -top-5 w-14 h-14 rounded-full bg-white flex items-center justify-center p-1.5 shadow-[0_-8px_16px_-6px_rgba(0,0,0,0.1)]">
                                        <div className="w-full h-full rounded-full bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center shadow-inner shadow-amber-700/50">
                                            <TabIcon className="w-6 h-6 text-white" strokeWidth={2.5} />
                                        </div>
                                    </div>
                                    <span className="text-[10px] font-bold text-amber-600 leading-none mt-7">
                                        {tab.label}
                                    </span>
                                </NavLink>
                            );
                        }

                        return (
                            <NavLink
                                key={tab.to}
                                to={tab.to}
                                className={`flex-1 flex flex-col items-center justify-center gap-1.5 transition-all active:scale-95 rounded-2xl mx-0.5 my-1
                                    ${active
                                        ? 'text-sky-600'
                                        : 'text-slate-400 hover:text-slate-600'
                                    }`}
                            >
                                <div className={`relative flex items-center justify-center w-8 h-8 rounded-xl transition-all ${active ? 'bg-sky-50' : 'bg-transparent'}`}>
                                    <TabIcon className="w-5 h-5" strokeWidth={active ? 2.5 : 2} />
                                </div>
                                <span className={`text-[10px] leading-none transition-all ${active ? 'font-bold' : 'font-semibold'}`}>
                                    {tab.label}
                                </span>
                            </NavLink>
                        );
                    })}
                </div>
            </nav>
        </div>
    );
}