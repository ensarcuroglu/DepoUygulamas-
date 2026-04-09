/**
 * DepocuLayout — Depo operatörü arayüzü.
 *
 * Tasarım ilkeleri:
 * - Sidebar yok; menü değil görev odaklı navigasyon
 * - Bottom tab bar — büyük dokunmatik hedefler (≥48px)
 * - Açık tema: yüksek okunabilirlik, saha koşullarına uygun
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
    { to: '/depocu',            label: 'Ana Sayfa', icon: Home,         terminal: false },
    { to: '/depocu/mal-kabul',  label: 'Mal Kabul', icon: PackageCheck, terminal: false },
    { to: '/terminal/gorevler', label: 'Terminal',  icon: Scan,         terminal: true  },
    { to: '/depocu/stok',       label: 'Stok',      icon: ArrowLeftRight, terminal: false },
    { to: '/depocu/profil',     label: 'Profil',    icon: UserCircle,   terminal: false },
];

function isTabActive(tabPath, currentPath) {
    if (tabPath === '/depocu') return currentPath === '/depocu';
    // Terminal sekmesi: DepocuLayout içindeyken hiç aktif gösterilmez
    // (kullanıcı terminaldeyken zaten TerminalLayout'a geçmiş olur)
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
        <div className="min-h-screen bg-slate-50 flex flex-col">
            <Toaster
                position="top-center"
                toastOptions={{
                    duration: 3500,
                    style: {
                        borderRadius: '12px',
                        background: '#ffffff',
                        color: '#1e293b',
                        border: '1px solid #e2e8f0',
                        fontSize: '14px',
                        fontWeight: 600,
                        boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)',
                    },
                    success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
                    error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
                }}
            />

            {/* Üst başlık */}
            <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-sm">
                        <Warehouse className="w-5 h-5 text-white" strokeWidth={2} />
                    </div>
                    <div>
                        <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold leading-none">
                            Depo Operatörü
                        </p>
                        <p className="text-sm font-bold text-slate-800 leading-tight mt-0.5">
                            {user?.ad_soyad || user?.kullanici_adi || 'Operatör'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 text-slate-400 hover:text-red-500 transition-colors py-2 px-3 rounded-xl hover:bg-red-50 active:bg-red-100"
                    aria-label="Çıkış Yap"
                >
                    <LogOut className="w-5 h-5" />
                    <span className="text-xs font-semibold hidden sm:inline">Çıkış</span>
                </button>
            </header>

            {/* Sayfa içeriği */}
            <main className="flex-1 overflow-y-auto pb-20">
                <Outlet />
            </main>

            {/* Alt tab navigasyon */}
            <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 safe-area-bottom">
                <div className="flex">
                    {TAB_ITEMS.map((tab) => {
                        const TabIcon = tab.icon;
                        const active = isTabActive(tab.to, location.pathname);

                        if (tab.terminal) {
                            // Terminal sekmesi — amber renkli, mod geçişi simgesi
                            return (
                                <NavLink
                                    key={tab.to}
                                    to={tab.to}
                                    className="flex-1 flex flex-col items-center justify-center py-3 gap-1 min-h-[56px] transition-colors border-t-2 border-transparent group"
                                >
                                    <div className="w-9 h-9 rounded-xl bg-amber-500 group-active:bg-amber-600 flex items-center justify-center shadow-md shadow-amber-500/30 transition-colors -mt-1">
                                        <TabIcon className="w-5 h-5 text-white" strokeWidth={2} />
                                    </div>
                                    <span className="text-[10px] font-bold text-amber-600 leading-none">
                                        {tab.label}
                                    </span>
                                </NavLink>
                            );
                        }

                        return (
                            <NavLink
                                key={tab.to}
                                to={tab.to}
                                className={`flex-1 flex flex-col items-center justify-center py-3 gap-1 min-h-[56px] transition-colors active:bg-slate-100 border-t-2
                                    ${active
                                        ? 'text-sky-600 border-sky-500 bg-sky-50/60'
                                        : 'text-slate-400 border-transparent hover:text-slate-600 hover:bg-slate-50'
                                    }`}
                            >
                                <TabIcon className="w-5 h-5" strokeWidth={active ? 2.2 : 1.8} />
                                <span className="text-[10px] font-semibold leading-none">{tab.label}</span>
                            </NavLink>
                        );
                    })}
                </div>
            </nav>
        </div>
    );
}
