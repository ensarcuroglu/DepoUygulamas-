import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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
    ClipboardCheck,
    ChevronDown,
    TrendingUp,
    Smartphone,
    Scan,
    Factory,
} from 'lucide-react';

/* ───────────────────────────────────────────
   MENU STRUCTURE — grouped with accordion
   ─────────────────────────────────────────── */
const menuGroups = [
    {
        id: 'genel',
        label: 'Genel',
        items: [
            { path: '/dashboard', label: 'İş Zekası & Özet', icon: LayoutDashboard, roles: ['admin'], badge: null },
        ],
    },
    {
        id: 'urun-stok',
        label: 'Ürün & Stok',
        items: [
            { path: '/urunler', label: 'Ürün Yönetimi', icon: Package, roles: ['admin'], badge: null },
            { path: '/kategoriler', label: 'Kategori Ağacı', icon: FolderOpen, roles: ['admin'], badge: null },
            { path: '/lotlar', label: 'LOT Takibi', icon: Layers, roles: ['admin'], badge: null },
            { path: '/paletler', label: 'Palet Yönetimi', icon: Container, roles: ['admin'], badge: null },
            { path: '/stok-hareketleri', label: 'Stok İşlemleri', icon: ArrowLeftRight, roles: ['admin', 'lojistik'], badge: null },
            { path: '/stok-sayim', label: 'Stok Sayımı', icon: ClipboardCheck, roles: ['admin'], badge: null },
        ],
    },
    {
        id: 'uretim',
        label: 'Üretim',
        items: [
            { path: '/uretim-paletleri', label: 'Üretim Paletleri', icon: Factory, roles: ['admin', 'depocu'], departments: ['kalite'], badge: null },
            { path: '/uretim-paletleri/kabul', label: 'Palet Kabul', icon: Scan, roles: ['admin', 'depocu'], badge: null },
        ],
    },
    {
        id: 'lojistik',
        label: 'Lojistik & Sevkiyat',
        items: [
            { path: '/sevkiyatlar', label: 'Sevkiyatlar (Çıkış)', icon: ArrowUpFromLine, roles: ['admin', 'lojistik'], badge: null },
            { path: '/siparisler', label: 'Siparişler', icon: ClipboardList, roles: ['admin', 'lojistik'], badge: null },
            { path: '/sevkiyat-planlama', label: 'Sevkiyat Planlama', icon: Route, roles: ['admin', 'lojistik'], badge: null },
            { path: '/irsaliyeler', label: 'İrsaliyeler', icon: FileText, roles: ['admin', 'lojistik'], badge: null },
            { path: '/mal-kabul-irsaliyeleri', label: 'Mal Kabul', icon: ClipboardCheck, roles: ['admin', 'lojistik'], badge: null },
            { path: '/inbound-dashboard', label: 'Inbound Panel', icon: BarChart3, roles: ['admin', 'lojistik'], badge: null },
            { path: '/kpi-dashboard', label: 'KPI Paneli', icon: TrendingUp, roles: ['admin', 'lojistik'], badge: null },
        ],
    },
    {
        id: 'putaway',
        label: 'Yerleştirme',
        items: [
            { path: '/zonlar', label: 'Zon Yönetimi', icon: Warehouse, roles: ['admin', 'lojistik'], badge: null },
            { path: '/yerlestirme-gorevleri', label: 'Görev Takibi', icon: ClipboardList, roles: ['admin', 'lojistik'], badge: null },
        ],
    },
    {
        id: 'toplama',
        label: 'Toplama (Pick)',
        items: [
            { path: '/toplama-gorevleri', label: 'Toplama Görevleri', icon: ClipboardCheck, roles: ['admin', 'depocu', 'lojistik'], badge: null },
        ],
    },
    {
        id: 'terminal',
        label: 'Saha Terminali',
        items: [
            { path: '/terminal/gorevler', label: 'Görev Listesi', icon: ClipboardCheck, roles: ['admin', 'lojistik'], badge: null },
            { path: '/terminal/yerlestirme', label: 'Yerleştirme', icon: Scan, roles: ['admin', 'lojistik'], badge: null },
            { path: '/terminal/ozet', label: 'Performans Özeti', icon: TrendingUp, roles: ['admin', 'lojistik'], badge: null },
        ],
    },
    {
        id: 'yonetim',
        label: 'Yönetim & Rapor',
        items: [
            { path: '/raporlar', label: 'Raporlama Merkezi', icon: BarChart3, roles: ['admin', 'lojistik'], badge: null },
            { path: '/kullanicilar', label: 'Kullanıcı Yönetimi', icon: Users, roles: ['admin'], badge: null },
            { path: '/tedarikciler', label: 'Tedarikçi Yönetimi', icon: Truck, roles: ['admin'], badge: null },
            { path: '/depolar', label: 'Depo & Raf', icon: Warehouse, roles: ['admin', 'lojistik'], badge: null },
            { path: '/depo-kroki', label: 'Depo Kroki', icon: LayoutDashboard, roles: ['admin', 'lojistik'], badge: null },
        ],
    },
];

const bottomItems = [
    { path: '/sistem-loglari', label: 'Sistem Logları', icon: ShieldAlert, roles: ['admin'], badge: null },
    { path: '/destek-masasi', label: 'Destek Masası', icon: HelpCircle, roles: ['admin', 'lojistik'], badge: null },
    { path: '/ayarlar', label: 'Sistem Tercihleri', icon: Settings, roles: ['admin'], badge: null },
];

const canAccessItem = (item, userRole, userDepartment) => {
    if (!item.roles && !item.departments) return true;
    const roleAllowed = item.roles?.includes(userRole) ?? false;
    const departmentAllowed = item.departments?.includes(userDepartment) ?? false;
    return roleAllowed || departmentAllowed;
};

/* ───────────────────────────────────────────
   TOOLTIP — collapsed desktop only
   ─────────────────────────────────────────── */
function Tooltip({ children, label, show }) {
    const [visible, setVisible] = useState(false);
    const [coords, setCoords] = useState({ top: 0 });
    const ref = useRef(null);

    const handleEnter = useCallback(() => {
        if (!show) return;
        const rect = ref.current?.getBoundingClientRect();
        if (rect) setCoords({ top: rect.top + rect.height / 2 });
        setVisible(true);
    }, [show]);

    const handleLeave = useCallback(() => setVisible(false), []);

    return (
        <div
            ref={ref}
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
            className="relative"
        >
            {children}
            {show && visible && (
                <div
                    className="fixed z-[9999] pointer-events-none"
                    style={{ top: coords.top, left: 96, transform: 'translateY(-50%)' }}
                >
                    <div className="bg-slate-700 text-white text-[11px] font-medium tracking-wide px-3 py-1.5 rounded-md shadow-md border border-slate-600/50 whitespace-nowrap animate-tooltip-in">
                        {label}
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-[4px] w-[8px] h-[8px] bg-slate-700 border-l border-b border-slate-600/50 rotate-45" />
                    </div>
                </div>
            )}
        </div>
    );
}

/* ───────────────────────────────────────────
   BADGE
   ─────────────────────────────────────────── */
function Badge({ count, collapsed }) {
    if (!count) return null;
    const display = count > 99 ? '99+' : count;
    return (
        <span
            className={`inline-flex items-center justify-center font-semibold rounded-full bg-red-500 text-white shadow-sm flex-shrink-0 leading-none
                ${collapsed ? 'absolute -top-1 -right-1 text-[9px] min-w-[18px] h-[18px] px-1' : 'text-[10px] min-w-[20px] h-[20px] px-1.5 ml-auto'}`}
        >
            {display}
        </span>
    );
}

/* ───────────────────────────────────────────
   MENU ITEM
   ─────────────────────────────────────────── */
function MenuItem({ item, showLabel, collapsed, isMobile }) {
    const location = useLocation();
    const Icon = item.icon;
    const isActive = location.pathname.startsWith(item.path);
    const showTooltip = !isMobile && collapsed;

    const content = (
        <NavLink
            to={item.path}
            className={`group flex items-center gap-3.5 rounded-xl text-[13.5px] font-medium tracking-wide transition-all duration-250 relative overflow-hidden
                ${isActive
                    ? 'bg-sky-50 dark:bg-slate-800/80 text-sky-700 dark:text-sky-400'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }
                ${!showLabel ? 'justify-center p-3 mx-auto w-12 h-12' : 'px-3.5 py-[11px]'}`}
        >
            {/* Active indicator */}
            {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-lg bg-sky-500 opacity-90" />
            )}

            {/* Hover shimmer */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-r from-black/[0.02] dark:from-white/[0.02] via-black/[0.04] dark:via-white/[0.04] to-transparent" />
            </div>

            <div className="relative">
                <Icon
                    className={`flex-shrink-0 transition-all duration-250
                        ${!showLabel ? 'w-[22px] h-[22px]' : 'w-[18px] h-[18px]'}
                    ${isActive ? 'text-sky-500 dark:text-sky-400' : 'text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300'}`}
                    strokeWidth={isActive ? 2.2 : 1.8}
                />
                {!showLabel && <Badge count={item.badge} collapsed />}
            </div>

            {showLabel && (
                <>
                    <span className="whitespace-nowrap transition-transform duration-250 group-hover:translate-x-0.5 leading-none">{item.label}</span>
                    <Badge count={item.badge} />
                </>
            )}
        </NavLink>
    );

    if (showTooltip) {
        return <Tooltip label={item.label} show>{content}</Tooltip>;
    }
    return content;
}

/* ───────────────────────────────────────────
   ACCORDION GROUP
   ─────────────────────────────────────────── */
function AccordionGroup({ group, showLabel, collapsed, isMobile, userRole, userDepartment, openGroups, toggleGroup }) {
    const location = useLocation();
    const contentRef = useRef(null);
    const [contentHeight, setContentHeight] = useState(0);

    const filteredItems = useMemo(
        () => group.items.filter(item => canAccessItem(item, userRole, userDepartment)),
        [group.items, userRole, userDepartment]
    );

    const isOpen = openGroups.has(group.id);
    const hasActiveChild = filteredItems.some(item => location.pathname.startsWith(item.path));

    useEffect(() => {
        if (contentRef.current) {
            setContentHeight(contentRef.current.scrollHeight);
        }
    }, [filteredItems]);

    if (filteredItems.length === 0) return null;

    // Collapsed mode — show items directly without group header
    if (!showLabel) {
        return (
            <div className="space-y-1">
                {filteredItems.map(item => (
                    <MenuItem key={item.path} item={item} showLabel={false} collapsed={collapsed} isMobile={isMobile} />
                ))}
            </div>
        );
    }

    return (
        <div className="mb-1">
            {/* Group header */}
            <button
                onClick={() => toggleGroup(group.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2 rounded-lg text-[11px] font-semibold uppercase tracking-wider transition-colors duration-200 group
                    ${hasActiveChild ? 'text-sky-600/90 dark:text-sky-400/90' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
            >
                <span>{group.label}</span>
                <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-300 ease-out
                        ${isOpen ? 'rotate-0' : '-rotate-90'}
                        ${hasActiveChild ? 'text-sky-400/60' : 'text-slate-600 group-hover:text-slate-500'}`}
                />
            </button>

            {/* Collapsible content */}
            <div
                className="overflow-hidden transition-[max-height,opacity] duration-300 ease-out"
                style={{
                    maxHeight: isOpen ? contentHeight + 16 : 0,
                    opacity: isOpen ? 1 : 0,
                }}
            >
                <div ref={contentRef} className="space-y-0.5 pt-1">
                    {filteredItems.map(item => (
                        <MenuItem key={item.path} item={item} showLabel collapsed={collapsed} isMobile={isMobile} />
                    ))}
                </div>
            </div>
        </div>
    );
}

/* ───────────────────────────────────────────
   SIDEBAR (main export)
   ─────────────────────────────────────────── */
export default function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }) {
    const location = useLocation();
    const { user } = useAuth();
    const [isMobile, setIsMobile] = useState(false);
    const prevPathnameRef = useRef(location.pathname);

    // Accordion state — start with all open
    const [openGroups, setOpenGroups] = useState(() => new Set(menuGroups.map(g => g.id)));

    const toggleGroup = useCallback((id) => {
        setOpenGroups(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    }, []);

    // Ensure the group containing active route is visible without mutating state in an effect.
    const activeGroupId = useMemo(() => {
        const activeGroup = menuGroups.find((group) => group.items.some((item) => location.pathname.startsWith(item.path)));
        return activeGroup?.id ?? null;
    }, [location.pathname]);

    const visibleOpenGroups = useMemo(() => {
        if (!activeGroupId || openGroups.has(activeGroupId)) return openGroups;
        const next = new Set(openGroups);
        next.add(activeGroupId);
        return next;
    }, [openGroups, activeGroupId]);

    const filteredBottomItems = useMemo(
        () => bottomItems.filter(item => canAccessItem(item, user?.rol, (user?.departman || '').trim().toLowerCase())),
        [user?.rol, user?.departman]
    );

    useEffect(() => {
        const check = () => setIsMobile(window.innerWidth < 1024);
        check();
        window.addEventListener('resize', check);
        return () => window.removeEventListener('resize', check);
    }, []);

    // Close mobile menu on route change
    useEffect(() => {
        const pathChanged = prevPathnameRef.current !== location.pathname;
        if (pathChanged && isMobile && mobileOpen) {
            setMobileOpen(false);
        }
        prevPathnameRef.current = location.pathname;
    }, [location.pathname, isMobile, mobileOpen, setMobileOpen]);

    const showLabel = isMobile || !collapsed;

    return (
        <>
            {/* ── Global Styles ── */}
            <style>{`
                @keyframes tooltipIn {
                    from { opacity: 0; transform: translateY(-50%) translateX(-6px); }
                    to   { opacity: 1; transform: translateY(-50%) translateX(0); }
                }
                .animate-tooltip-in {
                    animation: tooltipIn 0.15s ease-out forwards;
                }
                .sidebar-scroll {
                    scrollbar-width: thin;
                    scrollbar-color: rgba(51,65,85,0.4) transparent;
                }
                .sidebar-scroll::-webkit-scrollbar {
                    width: 4px;
                }
                .sidebar-scroll::-webkit-scrollbar-track {
                    background: transparent;
                }
                .sidebar-scroll::-webkit-scrollbar-thumb {
                    background: rgba(51,65,85,0.4);
                    border-radius: 4px;
                }
                .sidebar-scroll::-webkit-scrollbar-thumb:hover {
                    background: rgba(71,85,105,0.6);
                }
            `}</style>

            {/* ── Mobile Overlay ── */}
            {isMobile && (
                <div
                    className={`fixed inset-0 z-40 bg-black/50 backdrop-blur-[6px] transition-opacity duration-300
                        ${mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* ── Sidebar Shell ── */}
            <aside
                className={`fixed top-0 left-0 h-[100dvh] z-50 flex flex-col
                    bg-white dark:bg-slate-900 transition-all duration-300 ease-[cubic-bezier(0.25,0.8,0.25,1)]
                    ${isMobile
                        ? (mobileOpen
                            ? 'w-[300px] translate-x-0 shadow-[8px_0_40px_rgba(0,0,0,0.1)] dark:shadow-[8px_0_40px_rgba(0,0,0,0.4)] rounded-r-3xl'
                            : 'w-[300px] -translate-x-full rounded-r-3xl')
                        : (collapsed
                            ? 'w-[80px] border-r border-slate-200/60 dark:border-slate-800'
                            : 'w-[272px] border-r border-slate-200/60 dark:border-slate-800')
                    }`}
            >
                {/* ── Brand Area ── */}
                <div className={`relative flex items-center h-[72px] flex-shrink-0
                    ${collapsed && !isMobile ? 'justify-center px-4' : 'px-5 gap-3.5'}`}
                >
                    {/* Logo */}
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center flex-shrink-0 shadow-md shadow-sky-500/10 relative overflow-hidden">
                        <Warehouse className="w-[18px] h-[18px] text-white relative z-10" strokeWidth={2.2} />
                    </div>

                    {showLabel && (
                        <div className="flex-1 min-w-0">
                            <h1 className="text-[15px] font-extrabold tracking-tight text-slate-800 dark:text-white leading-tight">Depo Yönetim</h1>
                            <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]" />
                                <p className="text-[10px] text-emerald-400/90 font-semibold tracking-[0.15em] uppercase">Aktif</p>
                            </div>
                        </div>
                    )}

                    {/* Mobile close */}
                    {isMobile && showLabel && (
                        <button
                            onClick={() => setMobileOpen(false)}
                            className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-white/[0.05] flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/[0.1] transition-all duration-200 active:scale-95 flex-shrink-0"
                        >
                            <X className="w-4.5 h-4.5" />
                        </button>
                    )}
                </div>

                {/* Divider */}
                <div className="mx-5 h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-slate-800 to-transparent flex-shrink-0" />

                {/* ── Navigation ── */}
                <div className="flex-1 flex flex-col overflow-y-auto sidebar-scroll py-4 px-3">

                    {/* Main Menu Groups */}
                    <nav className="flex-1 space-y-0.5">
                        {menuGroups.map(group => (
                            <AccordionGroup
                                key={group.id}
                                group={group}
                                showLabel={showLabel}
                                collapsed={collapsed}
                                isMobile={isMobile}
                                userRole={user?.rol}
                                userDepartment={(user?.departman || '').trim().toLowerCase()}
                                openGroups={visibleOpenGroups}
                                toggleGroup={toggleGroup}
                            />
                        ))}
                    </nav>

                    {/* ── Bottom Section ── */}
                    <div className="mt-auto pt-4">
                        <div className="mx-1 h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-slate-800 to-transparent mb-4" />

                        {showLabel && (
                            <div className="px-3.5 mb-2">
                                <p className="text-[10.5px] font-bold text-slate-500 uppercase tracking-[0.12em]">Sistem</p>
                            </div>
                        )}

                        <nav className="space-y-0.5">
                            {filteredBottomItems.map(item => (
                                <MenuItem key={item.path} item={item} showLabel={showLabel} collapsed={collapsed} isMobile={isMobile} />
                            ))}
                        </nav>

                        {/* User Profile */}
                        {showLabel && (
                            <div className="mt-4 mx-0.5 p-3 rounded-xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-200/40 dark:border-slate-700/50 flex items-center justify-between group hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 cursor-pointer">
                                <div className="flex items-center gap-2.5 min-w-0">
                                    <div className="w-9 h-9 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0">
                                        <UserCircle className="w-5 h-5 text-slate-500 dark:text-slate-400" strokeWidth={1.8} />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-[13px] font-medium text-slate-700 dark:text-slate-300 truncate leading-tight">{user?.ad_soyad || 'Kullanıcı'}</p>
                                        <p className="text-[11px] text-slate-500 dark:text-slate-500 truncate capitalize leading-tight mt-0.5">{user?.rol || 'Rol Yok'}</p>
                                    </div>
                                </div>
                                <button
                                    title="Çıkış Yap"
                                    className="w-8 h-8 rounded-lg bg-transparent flex items-center justify-center text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition-all duration-200 flex-shrink-0"
                                >
                                    <LogOut className="w-4 h-4" strokeWidth={2} />
                                </button>
                            </div>
                        )}

                        {/* Collapsed — logout only */}
                        {!showLabel && (
                            <Tooltip label="Çıkış Yap" show={!isMobile && collapsed}>
                                <button
                                    title="Çıkış Yap"
                                    className="w-12 h-12 mx-auto flex items-center justify-center rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-200 mt-2"
                                >
                                    <LogOut className="w-[22px] h-[22px]" strokeWidth={1.8} />
                                </button>
                            </Tooltip>
                        )}
                    </div>
                </div>

                {/* ── Collapse Toggle (desktop only) ── */}
                {!isMobile && (
                    <div className="flex-shrink-0 px-3 pb-4 pt-2">
                        <div className="mx-1 h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-slate-800 to-transparent mb-3" />
                        <button
                            onClick={() => setCollapsed(!collapsed)}
                            className={`w-full flex items-center gap-2.5 py-3 rounded-xl text-[12px] font-bold uppercase tracking-wider
                                text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all duration-250
                                ${collapsed ? 'justify-center' : 'px-3.5'}`}
                            title={collapsed ? 'Menüyü Genişlet' : 'Daralt'}
                        >
                            {collapsed ? (
                                <Menu className="w-5 h-5" strokeWidth={1.8} />
                            ) : (
                                <>
                                    <ChevronLeft className="w-4 h-4" strokeWidth={2} />
                                    <span>Daralt</span>
                                </>
                            )}
                        </button>
                    </div>
                )}
            </aside>
        </>
    );
}
