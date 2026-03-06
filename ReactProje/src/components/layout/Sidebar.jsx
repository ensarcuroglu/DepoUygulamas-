import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
    LayoutDashboard,
    Package,
    FolderOpen,
    ArrowLeftRight,
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
    Container
} from 'lucide-react';

const menuItems = [
    { path: '/dashboard', label: 'İş Zekası & Özet', icon: LayoutDashboard, roles: ['admin'] },
    { path: '/urunler', label: 'Ürün Yönetimi', icon: Package, roles: ['admin'] },
    { path: '/kategoriler', label: 'Kategori Ağacı', icon: FolderOpen, roles: ['admin'] },
    { path: '/lotlar', label: 'LOT Takibi', icon: Layers, roles: ['admin'] },
    { path: '/paletler', label: 'Palet Yönetimi', icon: Container, roles: ['admin'] },
    { path: '/stok-hareketleri', label: 'Stok İşlemleri', icon: ArrowLeftRight, roles: ['admin', 'depocu'] },
    { path: '/kullanicilar', label: 'Kullanıcı Yönetimi', icon: Users, roles: ['admin'] },
    { path: '/tedarikciler', label: 'Tedarikçi Yönetimi', icon: Truck, roles: ['admin'] },
    { path: '/depolar', label: 'Depo & Raf', icon: Warehouse, roles: ['admin'] },
];

const bottomItems = [
    { path: '/yardim', label: 'Destek Masası', icon: HelpCircle, roles: ['admin'] },
    { path: '/ayarlar', label: 'Sistem Tercihleri', icon: Settings, roles: ['admin'] },
];

export default function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }) {
    const location = useLocation();
    const { user } = useAuth();
    const [isMobile, setIsMobile] = useState(false);

    // Rolé göre menü öğelerini filtrele
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

    const showLabel = isMobile || !collapsed;

    return (
        <aside
            className={`fixed top-0 left-0 h-screen z-40 flex flex-col bg-[#050B14] border-r border-slate-800/60 shadow-[4px_0_24px_rgba(0,0,0,0.15)]
            transition-all duration-400 ease-[cubic-bezier(0.25,0.8,0.25,1)]
            ${isMobile
                    ? (mobileOpen ? 'w-[280px] translate-x-0' : 'w-[280px] -translate-x-full')
                    : (collapsed ? 'w-[80px]' : 'w-[290px]') // Genişliği menü ferahlığı için biraz artırdık
                }`}
        >
            {/* Brand Logo Area */}
            <div className={`relative flex items-center h-[80px] px-5 mb-4
        ${collapsed && !isMobile ? 'justify-center px-0' : 'gap-4'}`}>
                <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />

                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(37,99,235,0.25)] border border-blue-400/20 relative group overflow-hidden">
                    <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out skew-x-12" />
                    <Warehouse className="w-6 h-6 text-white drop-shadow-md relative z-10" />
                </div>
                {showLabel && (
                    <div className="animate-fade-in overflow-hidden whitespace-nowrap flex flex-col justify-center flex-1">
                        <h1 className="text-[16px] sm:text-[18px] font-extrabold tracking-tight leading-none mb-1 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-300">Depo Yönetim Sistemi</h1>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                            <p className="text-[11px] text-emerald-400 font-bold tracking-[0.2em] uppercase leading-none">OptimakSTU</p>
                        </div>
                    </div>
                )}

                {/* Mobile close button */}
                {isMobile && mobileOpen && (
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-colors flex-shrink-0"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Navigation */}
            <div className="flex-1 flex flex-col justify-between py-2 px-4 overflow-y-auto custom-scrollbar">

                {/* Main Menu - ANA OPERASYONLAR */}
                <nav className="space-y-2.5"> {/* space-y-2.5 ile aralarındaki boşluğu artırdık */}
                    {showLabel && (
                        <div className="px-2 mb-5 mt-2">
                            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest relative inline-block">
                                Ana Operasyonlar
                                <span className="absolute -bottom-1.5 left-0 w-8 h-[2px] bg-slate-700 rounded-full" />
                            </p>
                        </div>
                    )}
                    {filteredMenuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname.startsWith(item.path);
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                title={!showLabel ? item.label : ''}
                                className={`group flex items-center gap-4 px-4 py-3.5 rounded-2xl text-[15px] font-medium tracking-wide transition-all duration-300 relative overflow-hidden
                  ${isActive
                                        ? 'bg-gradient-to-r from-blue-600/20 to-transparent text-blue-400 border border-blue-500/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]'
                                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
                                    }
                  ${!showLabel ? 'justify-center px-0' : ''}`}
                            >
                                {isActive && (
                                    <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.8)] rounded-r-full" />
                                )}
                                <Icon className={`w-[22px] h-[22px] flex-shrink-0 transition-all duration-300
                  ${isActive ? 'text-blue-500 scale-110 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]' : 'text-slate-500 group-hover:text-slate-300'}`}
                                />
                                {showLabel && <span className="whitespace-nowrap translate-x-0 group-hover:translate-x-1 transition-transform duration-300">{item.label}</span>}
                            </NavLink>
                        );
                    })}
                </nav>

                {/* Bottom Menu */}
                <nav className="space-y-1.5 mt-8 relative pt-6">
                    <div className="absolute top-0 left-2 right-2 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
                    {showLabel && (
                        <div className="px-2 mb-4">
                            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest relative inline-block">
                                Sistem & Araçlar
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
                                className={`group flex items-center gap-4 px-4 py-3 rounded-xl text-[14px] font-medium transition-all duration-300 relative overflow-hidden
                  ${isActive
                                        ? 'bg-gradient-to-r from-slate-800/80 to-transparent text-white'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                                    }
                  ${!showLabel ? 'justify-center px-0' : ''}`}
                            >
                                {isActive && (
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-slate-500 rounded-r-full" />
                                )}
                                <Icon className={`w-[20px] h-[20px] flex-shrink-0 transition-all duration-300
                  ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`}
                                />
                                {showLabel && <span className="whitespace-nowrap translate-x-0 group-hover:translate-x-1 transition-transform duration-300">{item.label}</span>}
                            </NavLink>
                        );
                    })}

                    {/* Logout Button */}
                    <button
                        title={!showLabel ? "Sistemden Çıkış" : ''}
                        className={`w-full group flex items-center gap-4 px-4 py-3 rounded-xl text-[14px] font-medium transition-all duration-300
                        text-slate-400 hover:text-red-400 hover:bg-red-500/10 mt-2
                        ${!showLabel ? 'justify-center px-0' : ''}`}
                    >
                        <LogOut className="w-[20px] h-[20px] flex-shrink-0 text-slate-500 group-hover:text-red-400 transition-colors" />
                        {showLabel && <span className="whitespace-nowrap">Sistemden Çıkış</span>}
                    </button>
                </nav>
            </div>

            {/* Collapse Toggle — only on desktop */}
            {!isMobile && (
                <div className="p-4 relative">
                    <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-[14px] font-bold
            text-slate-400 hover:text-white hover:bg-slate-800/80 transition-all duration-300 border border-transparent hover:border-slate-700/50
            ${collapsed ? 'justify-center px-0' : ''}`}
                        title={collapsed ? 'Menüyü Genişlet' : 'Daralt'}
                    >
                        {collapsed ? (
                            <Menu className="w-[22px] h-[22px]" />
                        ) : (
                            <>
                                <ChevronLeft className="w-[20px] h-[20px]" />
                                <span>Menüyü Daralt</span>
                            </>
                        )}
                    </button>
                </div>
            )}
        </aside>
    );
}