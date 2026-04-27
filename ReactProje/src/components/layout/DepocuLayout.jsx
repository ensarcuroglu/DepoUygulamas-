/**
 * DepocuLayout — Depo operatörü arayüzü.
 *
 * Saha Odaklı UX Prensipleri:
 * - Keskin ve yüksek kontrastlı okuma alanları (Açık tema, kurumsal çizgiler)
 * - Minimum görsel gürültü (Gereksiz gölge ve gradientler kaldırıldı)
 * - Safe-area uyumlu, devasa alt navigasyon hedefleri (Thumb-zone optimizasyonu)
 * - Pürüzsüz donanım ivmeli tıklama hissi (active:scale)
 */
import { useLayoutEffect, useRef } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { motion as Motion } from 'framer-motion';
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

const TAB_ITEMS = [
    { to: '/depocu',            label: 'Ana Sayfa', icon: Home,           terminal: false },
    { to: '/depocu/kabul',      label: 'Kabul',     icon: PackageCheck,   terminal: false },
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
    const mainRef = useRef(null);

    const handleLogout = async () => {
        await logout?.();
        navigate('/login');
    };

    useLayoutEffect(() => {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;

        if (mainRef.current) {
            mainRef.current.scrollTop = 0;
            mainRef.current.scrollLeft = 0;
        }
    }, [location.pathname]);

    return (
        <div className="min-h-[100dvh] bg-slate-50 dark:bg-[#0A0B0D] flex flex-col font-sans selection:bg-blue-500/30 transition-colors duration-300">
            {/* WMS Standartlarında Optimize Edilmiş Toaster */}
            <Toaster
                position="top-center"
                toastOptions={{
                    duration: 3000,
                    style: {
                        borderRadius: '12px',
                        background: '#ffffff',
                        color: '#0f172a',
                        border: '1px solid #e2e8f0',
                        fontSize: '14px',
                        fontWeight: 700,
                        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -4px rgba(0,0,0,0.05)',
                        padding: '16px',
                    },
                    success: { iconTheme: { primary: '#059669', secondary: '#fff' } },
                    error: { iconTheme: { primary: '#e11d48', secondary: '#fff' } },
                }}
            />

            {/* ÜST BİLGİ ÇUBUĞU - Floating Glassmorphism */}
            <header className="sticky top-0 z-40 bg-white/70 dark:bg-[#121316]/70 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-800/50 px-4 py-3 flex items-center justify-between transition-colors duration-300">
                <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-blue-600 dark:bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-600/20">
                        <Warehouse className="w-6 h-6 text-white" strokeWidth={2} />
                    </div>
                    <div className="flex flex-col justify-center">
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-widest font-bold mb-0.5">
                            Depo Operatörü
                        </p>
                        <p className="text-base font-black text-slate-900 dark:text-white leading-none">
                            {user?.ad_soyad || user?.kullanici_adi || 'Aktif Kullanıcı'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center w-11 h-11 text-slate-400 dark:text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-xl transition-colors active:scale-95"
                    aria-label="Çıkış Yap"
                >
                    <LogOut className="w-5 h-5" strokeWidth={2.5} />
                </button>
            </header>

            {/* İÇERİK ALANI - Alt menü boşluğu ve safe-area hesaplamalı */}
            <main ref={mainRef} className="flex-1 overflow-y-auto pb-[calc(7rem+env(safe-area-inset-bottom))] relative z-10">
                <Outlet />
            </main>

            {/* ALT NAVİGASYON - Floating Glassmorphism Mobile-first Thumb-zone */}
            <nav className="fixed bottom-4 inset-x-4 z-40 pb-[env(safe-area-inset-bottom)] pointer-events-none">
                <div className="pointer-events-auto bg-white/80 dark:bg-[#1A1C20]/80 backdrop-blur-xl border border-white/20 dark:border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.08)] dark:shadow-[0_8px_32px_rgba(0,0,0,0.3)] rounded-[28px] flex justify-around items-end h-20 px-2 relative transition-colors duration-300">
                    {TAB_ITEMS.map((tab) => {
                        const TabIcon = tab.icon;
                        const active = isTabActive(tab.to, location.pathname);

                        // Terminal Butonu (Merkezdeki Dev Call-to-Action)
                        if (tab.terminal) {
                            return (
                                <NavLink
                                    key={tab.to}
                                    to={tab.to}
                                    className="group flex flex-col items-center justify-center w-[76px] -mt-8 mb-3 transition-transform active:scale-95 z-50"
                                >
                                    <div className="relative w-16 h-16 rounded-[22px] bg-gradient-to-br from-blue-500 to-blue-700 p-[3px] shadow-lg shadow-blue-600/30">
                                        <div className="w-full h-full rounded-[19px] bg-blue-600 dark:bg-blue-600 flex items-center justify-center relative overflow-hidden">
                                            {/* Parlama efekti */}
                                            <div className="absolute inset-0 bg-white/20 dark:bg-white/10 rotate-45 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                                            <TabIcon className="w-7 h-7 text-white" strokeWidth={2.5} />
                                        </div>
                                    </div>
                                    <span className="text-[11px] font-extrabold text-blue-700 dark:text-blue-400 mt-1.5 tracking-wide">
                                        {tab.label}
                                    </span>
                                </NavLink>
                            );
                        }

                        // Standart Sekmeler
                        return (
                            <NavLink
                                key={tab.to}
                                to={tab.to}
                                className={`flex-1 flex flex-col items-center justify-center py-2 mb-1 gap-1 transition-all active:scale-95 relative
                                    ${active ? 'text-blue-700 dark:text-blue-400' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                            >
                                <div className="relative flex items-center justify-center w-12 h-10 rounded-2xl z-10">
                                    {active && (
                                        <Motion.div
                                            layoutId="activeTabIndicator"
                                            className="absolute inset-0 bg-blue-50 dark:bg-blue-500/15 rounded-2xl -z-10"
                                            initial={false}
                                            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                        />
                                    )}
                                    <TabIcon className="w-[22px] h-[22px]" strokeWidth={active ? 2.5 : 2} />
                                </div>
                                <span className={`text-[10px] leading-none tracking-wide ${active ? 'font-bold' : 'font-semibold'}`}>
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
