import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { Toaster } from 'react-hot-toast';
import { useTheme } from '../../contexts/ThemeContext';

export default function DashboardLayout() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const location = useLocation();
    const { resolvedMod } = useTheme();
    const isDark = resolvedMod === 'koyu';

    // Sayfa gecisinde scroll'u sifirla
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location.pathname]);

    // Ekran genişliğine göre sidebar durumu
    useEffect(() => {
        const handleResize = () => {
            const mobile = window.innerWidth < 1024;
            setIsMobile(mobile);
            if (mobile) {
                setSidebarCollapsed(true);
                setMobileOpen(false);
            }
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const contentMargin = isMobile ? '0px' : (sidebarCollapsed ? '80px' : '272px');

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
            <Toaster
                position="top-right"
                toastOptions={{
                    duration: 3000,
                    style: {
                        borderRadius: '12px',
                        fontSize: '13px',
                        fontWeight: 500,
                        padding: '12px 16px',
                        background: isDark ? '#1e293b' : '#ffffff',
                        color: isDark ? '#f1f5f9' : '#0f172a',
                        border: isDark ? '1px solid #334155' : '1px solid #E2E8F0',
                        boxShadow: isDark
                            ? '0 10px 15px -3px rgba(0,0,0,0.4)'
                            : '0 10px 15px -3px rgba(0,0,0,0.05)',
                    },
                    success: {
                        iconTheme: { primary: '#10b981', secondary: '#fff' },
                    },
                    error: {
                        iconTheme: { primary: '#ef4444', secondary: '#fff' },
                    },
                }}
            />

            {/* Mobile Sidebar Backdrop */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden transition-opacity"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            <Sidebar
                collapsed={sidebarCollapsed}
                setCollapsed={setSidebarCollapsed}
                mobileOpen={mobileOpen}
                setMobileOpen={setMobileOpen}
            />

            {/* Main Content Area */}
            <div
                className="flex flex-col min-h-screen transition-all duration-400 ease-[cubic-bezier(0.25,0.8,0.25,1)]"
                style={{ marginLeft: contentMargin }}
            >
                <Header
                    onMobileMenuToggle={() => setMobileOpen(!mobileOpen)}
                />

                {/* Main padding and max-width for large screens */}
                <main className="flex-1 p-3 sm:p-5 lg:p-8 overflow-x-hidden">
                    <div className="max-w-[1600px] mx-auto w-full">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}

