/**
 * DepocuLayout — Depo operatörü arayüzü.
 *
 * Saha Odaklı UX Prensipleri:
 * - Keskin ve yüksek kontrastlı okuma alanları (Açık tema, kurumsal çizgiler)
 * - Minimum görsel gürültü (Gereksiz gölge ve gradientler kaldırıldı)
 * - Safe-area uyumlu, devasa alt navigasyon hedefleri (Thumb-zone optimizasyonu)
 * - Pürüzsüz donanım ivmeli tıklama hissi (active:scale)
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

    const handleLogout = async () => {
        await logout?.();
        navigate('/login');
    };

    return (
        <div className="min-h-[100dvh] bg-slate-50 flex flex-col font-sans selection:bg-blue-200">
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

            {/* ÜST BİLGİ ÇUBUĞU - Düz, Net ve Kurumsal */}
            <header className="sticky top-0 z-40 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-blue-600 flex items-center justify-center">
                        <Warehouse className="w-6 h-6 text-white" strokeWidth={2} />
                    </div>
                    <div className="flex flex-col justify-center">
                        <p className="text-[11px] text-slate-500 uppercase tracking-widest font-bold mb-0.5">
                            Depo Operatörü
                        </p>
                        <p className="text-base font-black text-slate-900 leading-none">
                            {user?.ad_soyad || user?.kullanici_adi || 'Aktif Kullanıcı'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center w-11 h-11 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors active:scale-95"
                    aria-label="Çıkış Yap"
                >
                    <LogOut className="w-5 h-5" strokeWidth={2.5} />
                </button>
            </header>

            {/* İÇERİK ALANI - Alt menü boşluğu ve safe-area hesaplamalı */}
            <main className="flex-1 overflow-y-auto pb-[calc(5.5rem+env(safe-area-inset-bottom))]">
                <Outlet />
            </main>

            {/* ALT NAVİGASYON - Mobile-first Thumb-zone */}
            <nav className="fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 z-40 pb-[env(safe-area-inset-bottom)]">
                <div className="flex justify-around items-end h20 px-1 relative">
                    {TAB_ITEMS.map((tab) => {
                        const TabIcon = tab.icon;
                        const active = isTabActive(tab.to, location.pathname);

                        // Terminal Butonu (Merkezdeki Dev Call-to-Action)
                        if (tab.terminal) {
                            return (
                                <NavLink
                                    key={tab.to}
                                    to={tab.to}
                                    className="group flex flex-col items-center justify-center w-[72px] -mt-7 mb-2 transition-transform active:scale-95 z-50"
                                >
                                    <div className="w-16 h-16 rounded-2xl bg-blue-600 border-[6px] border-slate-50 flex items-center justify-center shadow-lg shadow-blue-600/20">
                                        <TabIcon className="w-7 h-7 text-white" strokeWidth={2.5} />
                                    </div>
                                    <span className="text-[11px] font-bold text-blue-700 mt-1">
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
                                className={`flex-1 flex flex-col items-center justify-center py-3 gap-1.5 transition-all active:scale-95
                                    ${active ? 'text-blue-700' : 'text-slate-400 hover:text-slate-600'}`}
                            >
                                <div className={`flex items-center justify-center w-10 h-8 rounded-full transition-colors ${active ? 'bg-blue-50' : 'bg-transparent'}`}>
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