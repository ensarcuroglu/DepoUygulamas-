import { useState, useRef, useEffect } from 'react';
import { Bell, Search, Settings, User, Menu, LogOut, ChevronDown, Plus, Package, ArrowLeftRight, AlertTriangle } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { UrunModal } from '../../pages/UrunlerPage';
import { HareketModal } from '../../pages/StokHareketleriPage';
import { getKategoriler, getUrunler, createUrun, createStokHareketi } from '../../services/api';
import toast from 'react-hot-toast';
import { hataMetni } from '../../utils/hata';

const PAGE_TITLES = {
    '/dashboard': { title: 'Dashboard', subtitle: 'Gerçek zamanlı depo istatistikleri' },
    '/urunler': { title: 'Ürün Yönetimi', subtitle: 'Stok kartları ve envanter' },
    '/kategoriler': { title: 'Kategori Yönetimi', subtitle: 'Malzeme sınıflandırmaları' },
    '/stok-hareketleri': { title: 'Stok İşlemleri', subtitle: 'Ürün giriş ve çıkış' },
    '/kullanicilar': { title: 'Kullanıcı Yönetimi', subtitle: 'Sistem kullanıcıları ve yetkilendirme' },
    '/ayarlar': { title: 'Ayarlar', subtitle: 'Sistem tercihleri ve yapılandırma' },
    '/profil-ayarlari': { title: 'Profil Ayarları', subtitle: 'Kişisel bilgiler ve güvenlik' },
};

const ROL_LABELS = {
    admin: 'Sistem Yöneticisi',
    depocu: 'Depo Sorumlusu',
    lojistik: 'Lojistik Personeli',
    goruntuleyen: 'Görüntüleyici',
};

export default function Header({ onMobileMenuToggle }) {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [quickActionOpen, setQuickActionOpen] = useState(false);
    const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
    const dropdownRef = useRef(null);
    const quickActionRef = useRef(null);

    // Modal state ve verileri
    const [urunModalOpen, setUrunModalOpen] = useState(false);
    const [stokModalOpen, setStokModalOpen] = useState(false);
    const [kategoriler, setKategoriler] = useState([]);
    const [urunler, setUrunler] = useState([]);

    // Modallar için gerekli listeleri çek (sadece admin rolünde)
    useEffect(() => {
        if (user?.rol === 'admin') {
            getKategoriler().then(res => setKategoriler(res.data)).catch(() => { });
        }
        getUrunler({ limit: 500 }).then(res => setUrunler(res.data)).catch(() => { });
    }, [user?.rol]);

    const currentPage = Object.entries(PAGE_TITLES).find(([path]) =>
        location.pathname.startsWith(path)
    );
    const { title, subtitle } = currentPage?.[1] || { title: 'Depo Yönetim', subtitle: '' };

    // Dropdown dışına tıklayınca kapat
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setDropdownOpen(false);
            }
            if (quickActionRef.current && !quickActionRef.current.contains(e.target)) {
                setQuickActionOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleUrunSave = async (data) => {
        try {
            await createUrun(data);
            toast.success('Yeni ürün hızlıca oluşturuldu.');
            setUrunModalOpen(false);
            getUrunler({ limit: 500 }).then(res => setUrunler(res.data)); // Listeyi yenile
        } catch (err) {
            toast.error(hataMetni(err, 'Hızlı ürün ekleme başarısız oldu'));
        }
    };

    const handleStokSave = async (data) => {
        try {
            await createStokHareketi(data);
            toast.success(data.hareket_tipi === 'giris' ? 'Hızlı tedarik girişi eklendi.' : 'Hızlı sevkiyat çıkışı eklendi.');
            setStokModalOpen(false);
        } catch (err) {
            toast.error(hataMetni(err, 'Stok hareketi eklenemedi'));
        }
    };

    const handleLogout = () => {
        setDropdownOpen(false);
        logout();
        navigate('/login', { replace: true });
    };

    // Kullanıcının baş harfleri
    const initials = user?.ad_soyad
        ? user.ad_soyad.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : 'U';

    return (
        <header className="h-[64px] lg:h-[72px] bg-white/75 border-b border-slate-200/60 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-30 shadow-[0_4px_30px_rgb(0,0,0,0.02)] backdrop-blur-xl">

            {/* Arama Alanı Açıkken (Sadece Mobil) */}
            {mobileSearchOpen && (
                <div className="absolute inset-0 z-40 bg-white/95 backdrop-blur-2xl flex items-center px-4 animate-in fade-in zoom-in-95 duration-200 border-b border-slate-200/50">
                    <div className="w-full relative flex items-center">
                        <Search className="absolute left-3 w-5 h-5 text-blue-500" />
                        <input
                            type="text"
                            autoFocus
                            placeholder="Sistemde hızlı ara..."
                            className="w-full h-12 pl-10 pr-12 text-[15px] font-medium rounded-2xl bg-slate-100/70 border-transparent focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-slate-800 placeholder-slate-400 shadow-sm"
                        />
                        <button
                            onClick={() => setMobileSearchOpen(false)}
                            className="absolute right-2 w-8 h-8 flex items-center justify-center rounded-xl bg-slate-200/50 text-slate-500 hover:bg-slate-300/50 hover:text-slate-800 transition-colors"
                        >
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Left: Hamburger (mobile) + Page Title */}
            <div className={`flex items-center gap-2 sm:gap-4 transition-opacity duration-200 ${mobileSearchOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                {/* Mobile Hamburger Button */}
                <button
                    onClick={onMobileMenuToggle}
                    className="lg:hidden w-11 h-11 flex items-center justify-center rounded-2xl bg-slate-100/60 text-slate-600 hover:bg-slate-200/80 hover:text-blue-600 transition-all active:scale-95 -ml-1 border border-transparent shadow-sm"
                >
                    <Menu className="w-[22px] h-[22px] stroke-[2.5px]" />
                </button>

                <div className="flex flex-col justify-center">
                    <h2 className="text-[17px] sm:text-[19px] font-extrabold tracking-tight text-slate-800 leading-none mb-1 sm:mb-1.5">{title}</h2>
                    <p className="text-[11px] sm:text-[12px] text-slate-500 font-medium leading-none hidden sm:block">{subtitle}</p>
                </div>
            </div>

            {/* Right: Search + Notifications + Profile */}
            <div className={`flex items-center gap-1.5 sm:gap-3 lg:gap-5 transition-opacity duration-200 ${mobileSearchOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>

                {/* Desktop Search Engine */}
                <div className="relative hidden lg:flex items-center group">
                    <Search className="absolute left-3.5 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors pointer-events-none z-10" />
                    <input
                        type="text"
                        placeholder="Sistemde hızlı ara..."
                        className="w-[240px] h-10 pl-10 pr-16 text-[13px] font-medium rounded-2xl border border-slate-200/60
                          bg-slate-50/50 text-slate-800 placeholder-slate-400 shadow-[0_2px_10px_rgb(0,0,0,0.01)]
                          focus:outline-none focus:ring-[4px] focus:ring-blue-500/10 focus:border-blue-400 focus:bg-white focus:w-[320px]
                          transition-all duration-300 ease-out hover:bg-white hover:border-slate-300"
                    />
                    <div className="absolute right-2 flex items-center gap-1 pointer-events-none transition-opacity duration-300 group-focus-within:opacity-0">
                        <kbd className="inline-flex items-center justify-center px-1.5 h-5 text-[10px] font-bold text-slate-400 bg-white border border-slate-200/80 rounded tracking-wider shadow-sm">Ctrl</kbd>
                        <kbd className="inline-flex items-center justify-center px-1.5 h-5 text-[10px] font-bold text-slate-400 bg-white border border-slate-200/80 rounded shadow-sm">K</kbd>
                    </div>
                </div>

                {/* Mobile Search Button */}
                <button 
                  onClick={() => setMobileSearchOpen(true)}
                  className="lg:hidden w-11 h-11 flex items-center justify-center rounded-full
                             text-slate-500 hover:text-blue-600 hover:bg-blue-50/80 active:scale-95 transition-all duration-200">
                    <Search className="w-[20px] h-[20px] stroke-[2.5px]" />
                </button>

                {/* Divider - Tablet ve üstünde görünür */}
                <div className="hidden md:block w-px h-6 bg-slate-200/80"></div>

                {/* HIZLI İŞLEMLER (QUICK ACTIONS) */}
                <div className="relative" ref={quickActionRef}>
                    <button
                        onClick={() => setQuickActionOpen(!quickActionOpen)}
                        className={`group relative h-10 w-10 sm:h-10 sm:w-auto sm:px-4 text-[13.5px] font-semibold rounded-full sm:rounded-xl transition-all duration-300 flex items-center justify-center gap-2 active:scale-95 shadow-[0_2px_10px_rgb(0,0,0,0.04)]
                          ${quickActionOpen 
                            ? 'bg-slate-800 text-white shadow-md' 
                            : 'bg-white border border-slate-200/80 text-slate-700 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 hover:shadow-sm'}`}
                    >
                        <Plus className={`w-4 h-4 stroke-[2.5px] transition-transform duration-300 ${quickActionOpen ? 'rotate-45 text-white' : 'text-slate-500 group-hover:rotate-90 group-hover:text-blue-600'}`} />
                        <span className="hidden sm:inline tracking-wide">Yeni İşlem</span>
                    </button>

                    {/* Quick Actions Dropdown */}
                    {quickActionOpen && (
                        <div className="absolute right-0 sm:right-auto sm:left-1/2 sm:-translate-x-1/2 lg:left-auto lg:-translate-x-0 lg:right-0 top-[calc(100%+12px)] w-[260px] bg-white/95 backdrop-blur-2xl rounded-2xl border border-slate-200/60 shadow-[0_12px_40px_rgb(0,0,0,0.08)] py-2 z-50 animate-in fade-in slide-in-from-top-3 duration-200">
                            <div className="px-4 py-2 mb-1 flex items-center justify-between">
                                <p className="text-[11px] font-extrabold text-slate-400 uppercase tracking-widest">Hızlı İşlemler</p>
                            </div>

                            <div className="px-2">
                                <button onClick={() => { setQuickActionOpen(false); setUrunModalOpen(true); }} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-blue-50/60 rounded-xl transition-all text-left group">
                                    <div className="w-9 h-9 flex items-center justify-center bg-blue-100/50 text-blue-600 rounded-lg group-hover:bg-blue-500 group-hover:text-white transition-colors duration-300 shadow-sm shrink-0">
                                        <Package className="w-4 h-4 stroke-[2.5px]" />
                                    </div>
                                    <div>
                                        <p className="text-[13px] font-bold text-slate-800 group-hover:text-blue-700 transition-colors">Yeni Ürün Ekle</p>
                                        <p className="text-[11px] font-medium text-slate-500 pt-0.5">Stok kartı oluşturun</p>
                                    </div>
                                </button>

                                <button onClick={() => { setQuickActionOpen(false); setStokModalOpen(true); }} className="w-full flex items-center gap-3 px-3 py-2.5 mt-1 hover:bg-emerald-50/60 rounded-xl transition-all text-left group">
                                    <div className="w-9 h-9 flex items-center justify-center bg-emerald-100/50 text-emerald-600 rounded-lg group-hover:bg-emerald-500 group-hover:text-white transition-colors duration-300 shadow-sm shrink-0">
                                        <ArrowLeftRight className="w-4 h-4 stroke-[2.5px]" />
                                    </div>
                                    <div>
                                        <p className="text-[13px] font-bold text-slate-800 group-hover:text-emerald-700 transition-colors">Hızlı Stok Girişi</p>
                                        <p className="text-[11px] font-medium text-slate-500 pt-0.5">Tedarik eklemesi yapın</p>
                                    </div>
                                </button>
                                
                                <div className="h-px w-full bg-slate-100/80 my-1.5"></div>

                                <button onClick={() => { setQuickActionOpen(false); toast('Bu özellik yapım aşamasında.', { icon: '🚧' }); }} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-orange-50/60 rounded-xl transition-all text-left group">
                                    <div className="w-9 h-9 flex items-center justify-center bg-orange-100/50 text-orange-600 rounded-lg group-hover:bg-orange-500 group-hover:text-white transition-colors duration-300 shadow-sm shrink-0">
                                        <AlertTriangle className="w-4 h-4 stroke-[2.5px]" />
                                    </div>
                                    <div>
                                        <p className="text-[13px] font-bold text-slate-800 group-hover:text-orange-700 transition-colors">Hasar Kaydı</p>
                                        <p className="text-[11px] font-medium text-slate-500 pt-0.5">Fire/Hasar bildirim formu</p>
                                    </div>
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Notifications - Gizlenirse padding vs ayarlandı */}
                <button className="relative w-11 h-11 hidden sm:flex items-center justify-center rounded-2xl
                  text-slate-500 hover:text-blue-600 hover:bg-blue-50/80 border border-transparent hover:border-blue-100 transition-all duration-200 active:scale-95">
                    <Bell className="w-[20px] h-[20px] stroke-[2px]" />
                    <span className="absolute top-2.5 right-2.5 w-[9px] h-[9px] bg-red-500 rounded-full border-2 border-white shadow-sm" />
                </button>

                {/* Divider on desktop */}
                <div className="hidden sm:block w-px h-6 bg-slate-200/80 mx-1"></div>

                {/* User Menu */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        className="flex items-center gap-2.5 sm:gap-3 p-1 sm:pr-3 rounded-full sm:rounded-2xl hover:bg-slate-50/80 border border-transparent hover:border-slate-200/60 transition-all active:scale-95"
                    >
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20 text-white shrink-0">
                            <span className="text-[12px] sm:text-[13px] font-extrabold tracking-wider">{initials}</span>
                        </div>
                        <div className="hidden md:block text-left">
                            <p className="text-[13px] font-bold text-slate-800 leading-tight">
                                {user?.ad_soyad || 'Kullanıcı'}
                            </p>
                            <p className="text-[11px] font-medium text-slate-500 leading-tight mt-0.5">
                                {ROL_LABELS[user?.rol] || user?.rol || 'Rol'}
                            </p>
                        </div>
                        <ChevronDown className={`hidden md:block w-4 h-4 text-slate-400 ml-1 transition-transform duration-300 ${dropdownOpen ? 'rotate-180 text-blue-500' : ''}`} />
                    </button>

                    {/* Dropdown Menu */}
                    {dropdownOpen && (
                        <div className="absolute right-0 top-[calc(100%+12px)] w-[240px] bg-white/95 backdrop-blur-2xl rounded-2xl border border-slate-200/60 shadow-[0_12px_40px_rgb(0,0,0,0.08)] py-2 z-50 animate-in fade-in slide-in-from-top-3 duration-200">
                            {/* Kullanıcı Bilgisi (Mobil İçin Ekstra Gerekli) */}
                            <div className="px-5 py-4 border-b border-slate-100/80 md:hidden flex flex-col items-center text-center">
                                <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20 text-white mb-3">
                                    <span className="text-[18px] font-extrabold tracking-wider">{initials}</span>
                                </div>
                                <p className="text-[15px] font-bold text-slate-800">{user?.ad_soyad || 'Kullanıcı'}</p>
                                <p className="text-[12px] text-slate-500 font-medium mt-0.5">@{user?.kullanici_adi}</p>
                                <div className="mt-3 inline-flex px-2.5 py-1 rounded-md text-[11px] font-bold bg-blue-50 text-blue-600 border border-blue-100/50">
                                    {ROL_LABELS[user?.rol] || user?.rol}
                                </div>
                            </div>

                            <div className="p-2">
                                <button
                                    onClick={() => {
                                        setDropdownOpen(false);
                                        navigate('/profil-ayarlari');
                                    }}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-semibold text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition-colors group"
                                >
                                    <div className="p-1.5 rounded-lg text-slate-400 group-hover:text-blue-600 group-hover:bg-blue-100/50 transition-colors">
                                        <Settings className="w-[18px] h-[18px]" />
                                    </div>
                                    Profil Ayarları
                                </button>
                            </div>

                            <div className="h-px w-full bg-slate-100/80 my-0.5"></div>

                            <div className="p-2">
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-semibold text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors group"
                                >
                                    <div className="p-1.5 rounded-lg text-red-400 group-hover:text-red-600 group-hover:bg-red-100/80 transition-colors">
                                        <LogOut className="w-[18px] h-[18px]" />
                                    </div>
                                    Oturumu Kapat
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Global Hızlı İşlem Modalları */}
            <UrunModal isOpen={urunModalOpen} onClose={() => setUrunModalOpen(false)} onSave={handleUrunSave} kategoriler={kategoriler} urun={null} />
            <HareketModal isOpen={stokModalOpen} onClose={() => setStokModalOpen(false)} onSave={handleStokSave} urunler={urunler} />

        </header>
    );
}
