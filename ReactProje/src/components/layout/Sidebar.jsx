import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
    LayoutDashboard,
    Package,
    FolderOpen,
    ArrowLeftRight,
    ArrowUpFromLine,
    Settings,
    ChevronLeft,
    Warehouse,
    Menu,
    LogOut,
    HelpCircle,
    X,
    Users,
    Truck,
    Layers,
    Container,
    UserCircle,
    ShieldAlert,
    ClipboardList,
    Route,
    FileText,
    BarChart3,
    Clock,
    ClipboardCheck
} from 'lucide-react';

const menuItems = [
    { path: '/dashboard', label: 'İş Zekası & Özet', icon: LayoutDashboard, roles: ['admin'] },
    { path: '/urunler', label: 'Ürün Yönetimi', icon: Package, roles: ['admin'] },
    { path: '/kategoriler', label: 'Kategori Ağacı', icon: FolderOpen, roles: ['admin'] },
    { path: '/lotlar', label: 'LOT Takibi', icon: Layers, roles: ['admin'] },
    { path: '/paletler', label: 'Palet Yönetimi', icon: Container, roles: ['admin'] },
    { path: '/stok-hareketleri', label: 'Stok İşlemleri', icon: ArrowLeftRight, roles: ['admin', 'depocu', 'lojistik'] },
    { path: '/stok-sayim', label: 'Stok Sayımı', icon: ClipboardCheck, roles: ['admin', 'depocu'] },
    { path: '/sevkiyatlar', label: 'Sevkiyatlar (Çıkış)', icon: ArrowUpFromLine, roles: ['admin', 'depocu', 'lojistik'] },
    { path: '/siparisler', label: 'Siparişler', icon: ClipboardList, roles: ['admin', 'lojistik'] },
    { path: '/sevkiyat-planlama', label: 'Sevkiyat Planlama', icon: Route, roles: ['admin', 'lojistik'] },
    { path: '/irsaliyeler', label: 'İrsaliyeler', icon: FileText, roles: ['admin', 'lojistik', 'depocu'] },
    { path: '/raporlar', label: 'Raporlama Merkezi', icon: BarChart3, roles: ['admin', 'lojistik'] },
    { path: '/kullanicilar', label: 'Kullanıcı Yönetimi', icon: Users, roles: ['admin'] },
    { path: '/tedarikciler', label: 'Tedarikçi Yönetimi', icon: Truck, roles: ['admin'] },
    { path: '/depolar', label: 'Depo & Raf', icon: Warehouse, roles: ['admin', 'lojistik'] },
    { path: '/depo-kroki', label: 'Depo Kroki', icon: LayoutDashboard, roles: ['admin', 'lojistik'] },
];

const bottomItems = [
    { path: '/sistem-loglari', label: 'Sistem Logları', icon: ShieldAlert, roles: ['admin'] },
    { path: '/destek-masasi', label: 'Destek Masası', icon: HelpCircle, roles: ['admin', 'depocu', 'lojistik'] },
    { path: '/ayarlar', label: 'Sistem Tercihleri', icon: Settings, roles: ['admin'] },
];

export default function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }) {
    const location = useLocation();
    const { user } = useAuth();
    const [isMobile, setIsMobile] = useState(false);

    const filteredMenuItems = menuItems.filter(item =>
        !item.roles || item.roles.includes(user?.rol)
    );
    const filteredBottomItems = bottomItems.filter(item =>
        !item.roles || item.roles.includes(user?.rol)
    );

    useEffect(() => {
        const check = () => setIsMobile(window.innerWidth < 1024);
        check();
        window.addEventListener('resize', check);
        return () => window.removeEventListener('resize', check);
    }, []);

    // Close mobile menu on route change
    useEffect(() => {
        if (isMobile && mobileOpen) {
            setMobileOpen(false);
        }
    }, [location.pathname, isMobile]);

    const showLabel = isMobile || !collapsed;

    return (
        <>
            {/* Mobile Overlay with Glassmorphism */}
            {isMobile && (
                <div
                    className={`fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300 ${mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                    onClick={() => setMobileOpen(false)}
                />
            )}

            <aside
                className={`fixed top-0 left-0 h-[100dvh] z-50 flex flex-col bg-[#050B14] shadow-[4px_0_30px_rgba(0,0,0,0.3)]
                transition-all duration-400 ease-[cubic-bezier(0.2,0.8,0.2,1)]
                ${isMobile
                        ? (mobileOpen ? 'w-[300px] translate-x-0 rounded-r-[32px]' : 'w-[300px] -translate-x-[110%] rounded-r-[32px]')
                        : (collapsed ? 'w-[88px] border-r border-slate-800/60' : 'w-[290px] border-r border-slate-800/60')
                    }`}
            >
                {/* Brand Logo Area */}
                <div className={`relative flex items-center h-[90px] px-6 mb-2 mt-2
                    ${collapsed && !isMobile ? 'justify-center px-0' : 'gap-4'}`}>

                    <div className="absolute bottom-0 left-6 right-6 h-px bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800" />

                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/20 relative group overflow-hidden">
                        <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out skew-x-12" />
                        <Warehouse className="w-6 h-6 text-white drop-shadow-md relative z-10" />
                    </div>

                    {showLabel && (
                        <div className="animate-fade-in overflow-hidden whitespace-nowrap flex flex-col justify-center flex-1">
                            <h1 className="text-[17px] font-black tracking-tight leading-none mb-1 text-white">Depo Yönetim</h1>
                            <div className="flex items-center gap-1.5 mt-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                                <p className="text-[11px] text-emerald-400 font-bold tracking-[0.2em] uppercase leading-none">Sistem Aktif</p>
                            </div>
                        </div>
                    )}

                    {/* Mobile close button */}
                    {isMobile && showLabel && (
                        <button
                            onClick={() => setMobileOpen(false)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-slate-800/50 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-all active:scale-95 flex-shrink-0"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                </div>

                {/* Navigation Menu */}
                <div className="flex-1 flex flex-col justify-between py-4 px-4 overflow-y-auto custom-scrollbar">

                    {/* Main Menu */}
                    <nav className="space-y-1.5">
                        {showLabel && (
                            <div className="px-3 mb-4 mt-2">
                                <p className="text-[10px] font-extrabold text-slate-500 uppercase tracking-widest relative inline-block">
                                    Ana Menü
                                </p>
                            </div>
                        )}

                        {filteredMenuItems.map((item) => {
                            const Icon = item.icon;
                            // Exact match combined with startsWith for nested routes
                            const isActive = location.pathname.startsWith(item.path);

                            return (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    title={!showLabel ? item.label : ''}
                                    className={`group flex items-center gap-4 py-3.5 rounded-2xl text-[15px] font-bold tracking-wide transition-all duration-300 relative
                                    ${isActive
                                            ? 'bg-blue-600/10 text-blue-400'
                                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                                        }
                                    ${!showLabel ? 'justify-center px-0 mx-2' : 'px-4'}`}
                                >
                                    {isActive && (
                                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-blue-500 rounded-r-full shadow-[0_0_12px_rgba(59,130,246,0.8)]" />
                                    )}
                                    <Icon className={`flex-shrink-0 transition-transform duration-300
                                        ${!showLabel ? 'w-6 h-6' : 'w-5 h-5'}
                                        ${isActive ? 'text-blue-500 scale-110' : 'text-slate-500 group-hover:text-slate-300'}`}
                                    />
                                    {showLabel && <span className="whitespace-nowrap translate-x-0 group-hover:translate-x-1 transition-transform duration-300">{item.label}</span>}
                                </NavLink>
                            );
                        })}
                    </nav>

                    {/* Bottom Section */}
                    <div className="mt-8">
                        <nav className="space-y-1.5 relative pt-6 mb-6">
                            <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800" />

                            {showLabel && (
                                <div className="px-3 mb-3">
                                    <p className="text-[10px] font-extrabold text-slate-500 uppercase tracking-widest relative inline-block">
                                        Sistem Ayarları
                                    </p>
                                </div>
                            )}

                            {filteredBottomItems.map((item) => {
                                const Icon = item.icon;
                                const isActive = location.pathname.startsWith(item.path);
                                return (
                                    <NavLink
                                        key={item.path}
                                        to={item.path}
                                        title={!showLabel ? item.label : ''}
                                        className={`group flex items-center gap-4 py-3 rounded-2xl text-[14px] font-bold transition-all duration-300 relative
                                        ${isActive
                                                ? 'bg-slate-800 text-white'
                                                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                                            }
                                        ${!showLabel ? 'justify-center px-0 mx-2' : 'px-4'}`}
                                    >
                                        <Icon className={`flex-shrink-0 transition-transform duration-300
                                            ${!showLabel ? 'w-5 h-5' : 'w-5 h-5'}
                                            ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`}
                                        />
                                        {showLabel && <span className="whitespace-nowrap translate-x-0 group-hover:translate-x-1 transition-transform duration-300">{item.label}</span>}
                                    </NavLink>
                                );
                            })}
                        </nav>

                        {/* User Profile Snippet for Mobile/Expanded */}
                        {showLabel && (
                            <div className="mx-2 mb-2 p-3 rounded-2xl bg-slate-800/30 border border-slate-700/50 flex items-center justify-between group cursor-pointer hover:bg-slate-800/80 transition-colors">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                                        <UserCircle className="w-6 h-6 text-slate-300" />
                                    </div>
                                    <div className="overflow-hidden">
                                        <p className="text-[13px] font-bold text-slate-200 truncate">{user?.ad_soyad || 'Kullanıcı'}</p>
                                        <p className="text-[11px] font-semibold text-slate-500 truncate capitalize">{user?.rol || 'Rol Yok'}</p>
                                    </div>
                                </div>
                                <button title="Çıkış Yap" className="w-8 h-8 rounded-full bg-slate-700/50 flex items-center justify-center text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-colors flex-shrink-0">
                                    <LogOut className="w-4 h-4" />
                                </button>
                            </div>
                        )}

                        {/* Just Logout Icon for Collapsed Desktop */}
                        {!showLabel && (
                            <button
                                title="Sistemden Çıkış"
                                className="w-full flex items-center justify-center py-3 rounded-2xl text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors px-0 mx-2"
                            >
                                <LogOut className="w-6 h-6" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Collapse Toggle — only on desktop */}
                {!isMobile && (
                    <div className="p-4 relative">
                        <div className="absolute top-0 left-6 right-6 h-px bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800" />
                        <button
                            onClick={() => setCollapsed(!collapsed)}
                            className={`w-full flex items-center gap-3 py-4 rounded-2xl text-[13px] font-black uppercase tracking-wider
                            text-slate-500 hover:text-white hover:bg-slate-800/80 transition-all duration-300
                            ${collapsed ? 'justify-center px-0 mx-2' : 'px-4'}`}
                            title={collapsed ? 'Menüyü Genişlet' : 'Daralt'}
                        >
                            {collapsed ? (
                                <Menu className="w-6 h-6" />
                            ) : (
                                <>
                                    <ChevronLeft className="w-5 h-5" />
                                    <span>Menüyü Daralt</span>
                                </>
                            )}
                        </button>
                    </div>
                )}
            </aside>
        </>
    );
}