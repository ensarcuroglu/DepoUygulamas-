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
        <header className="h-[64px] lg:h-[72px] bg-white/80 border-b border-slate-200/80 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-30 shadow-sm"
            style={{ backdropFilter: 'blur(16px)' }}>

            {/* Left: Hamburger (mobile) + Page Title */}
            <div className="flex items-center gap-3">
                {/* Mobile Hamburger Button */}
                <button
                    onClick={onMobileMenuToggle}
                    className="lg:hidden w-10 h-10 flex items-center justify-center rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800 transition-all -ml-1"
                >
                    <Menu className="w-5 h-5" />
                </button>

                <div className="flex flex-col justify-center">
                    <h2 className="text-[16px] sm:text-[18px] font-bold tracking-tight text-slate-800 leading-none mb-1 sm:mb-1.5">{title}</h2>
                    <p className="text-[11px] sm:text-[12px] text-slate-500 font-medium leading-none hidden sm:block">{subtitle}</p>
                </div>
            </div>

            {/* Right: Search + Notifications + Profile */}
            <div className="flex items-center gap-2 sm:gap-4 lg:gap-6">

                {/* Premium Search Engine — hidden on mobile */}
                <div className="relative hidden lg:flex items-center group">
                    <Search className="absolute left-3.5 w-4 h-4 text-slate-400 group-focus-within:text-blue-600 transition-colors pointer-events-none z-10" />
                    <input
                        type="text"
                        placeholder="Sistemde hızlı ara..."
                        className="w-[260px] h-10 !pl-10 pr-16 text-[13px] font-medium rounded-xl border border-slate-200/80
              bg-slate-100/50 text-slate-800 placeholder-slate-400 shadow-sm
              focus:outline-none focus:ring-[3px] focus:ring-blue-500/15 focus:border-blue-500 focus:bg-white focus:w-[320px]
              transition-all duration-300 ease-in-out hover:bg-slate-100 hover:border-slate-300"
                    />
                    <div className="absolute right-2 flex items-center gap-1 pointer-events-none transition-opacity group-focus-within:opacity-0">
                        <kbd className="inline-flex items-center justify-center px-1.5 h-5 text-[10px] font-bold text-slate-400 bg-white border border-slate-200/80 rounded shadow-sm tracking-wider">Ctrl</kbd>
                        <kbd className="inline-flex items-center justify-center px-1.5 h-5 text-[10px] font-bold text-slate-400 bg-white border border-slate-200/80 rounded shadow-sm">K</kbd>
                    </div>
                </div>

                {/* Mobile Search Button — visible on smaller screens */}
                <button className="lg:hidden w-10 h-10 flex items-center justify-center rounded-full
          text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-all duration-200">
                    <Search className="w-[18px] h-[18px]" />
                </button>

                {/* Divider */}
                <div className="hidden md:block w-px h-6 bg-slate-200"></div>

                {/* HIZLI İŞLEMLER (QUICK ACTIONS) */}
                <div className="relative" ref={quickActionRef}>
                    <button
                        onClick={() => setQuickActionOpen(!quickActionOpen)}
                        className="group relative h-10 w-10 sm:h-10 sm:w-auto sm:px-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[13px] font-bold rounded-full sm:rounded-xl whitespace-nowrap hover:from-blue-500 hover:to-indigo-500 transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 overflow-hidden active:scale-95"
                    >
                        <Plus className="w-5 h-5 stroke-[2.5px] group-hover:rotate-90 transition-transform duration-300" />
                        <span className="hidden sm:inline">Yeni İşlem</span>
                    </button>

                    {/* Quick Actions Dropdown */}
                    {quickActionOpen && (
                        <div className="absolute right-0 top-[calc(100%+8px)] w-[260px] bg-white rounded-2xl border border-slate-200 shadow-xl py-2 z-50 animate-[fadeIn_0.15s_ease-out]">
                            <div className="px-4 py-2 border-b border-slate-100 mb-1">
                                <p className="text-[12px] font-extrabold text-slate-500 uppercase tracking-widest">Hızlı İşlemler</p>
                            </div>

                            <button onClick={() => { setQuickActionOpen(false); setUrunModalOpen(true); }} className="w-full flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors text-left group">
                                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg group-hover:bg-blue-100 transition-colors"><Package className="w-4 h-4" /></div>
                                <div>
                                    <p className="text-[13px] font-bold text-slate-800">Yeni Ürün Ekle</p>
                                    <p className="text-[11px] font-medium text-slate-500 mt-0.5">Stok kartı oluşturun</p>
                                </div>
                            </button>

                            <button onClick={() => { setQuickActionOpen(false); setStokModalOpen(true); }} className="w-full flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors text-left group mt-1">
                                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg group-hover:bg-emerald-100 transition-colors"><ArrowLeftRight className="w-4 h-4" /></div>
                                <div>
                                    <p className="text-[13px] font-bold text-slate-800">Hızlı Stok Girişi</p>
                                    <p className="text-[11px] font-medium text-slate-500 mt-0.5">Tedarik eklemesi yapın</p>
                                </div>
                            </button>

                            <button onClick={() => { setQuickActionOpen(false); toast('Bu özellik yapım aşamasında.', { icon: '🚧' }); }} className="w-full flex items-start gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors text-left group mt-1">
                                <div className="p-2 bg-orange-50 text-orange-600 rounded-lg group-hover:bg-orange-100 transition-colors"><AlertTriangle className="w-4 h-4" /></div>
                                <div>
                                    <p className="text-[13px] font-bold text-slate-800">Hasar Kaydı</p>
                                    <p className="text-[11px] font-medium text-slate-500 mt-0.5">Fire/Hasar çıkışı bildirin</p>
                                </div>
                            </button>
                        </div>
                    )}
                </div>

                {/* Divider */}
                <div className="hidden md:block w-px h-6 bg-slate-200"></div>

                <div className="flex items-center gap-1 sm:gap-2">


                    {/* Notifications */}
                    <button className="relative w-10 h-10 flex items-center justify-center rounded-full
            text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-all duration-200">
                        <Bell className="w-[18px] h-[18px]" />
                        <span className="absolute top-2.5 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white shadow-sm" />
                    </button>
                </div>

                {/* User Menu with Dropdown */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        className="flex items-center gap-3 pl-2 sm:pl-4 sm:border-l sm:border-slate-200
                                   hover:opacity-80 transition-opacity text-left"
                    >
                        <div className="hidden md:block">
                            <p className="text-[13px] font-bold text-slate-800 leading-none mb-1">
                                {user?.ad_soyad || 'Kullanıcı'}
                            </p>
                            <p className="text-[11px] font-medium text-slate-500 leading-none">
                                {ROL_LABELS[user?.rol] || user?.rol || 'Bilinmiyor'}
                            </p>
                        </div>
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600
                                        flex items-center justify-center shadow-md border-2 border-white">
                            <span className="text-[12px] sm:text-[13px] font-extrabold text-white">{initials}</span>
                        </div>
                        <ChevronDown className={`hidden md:block w-4 h-4 text-slate-400 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {/* Dropdown Menu */}
                    {dropdownOpen && (
                        <div className="absolute right-0 top-[calc(100%+8px)] w-[240px] bg-white rounded-2xl border border-slate-200 shadow-xl
                                        py-2 z-50 animate-[fadeIn_0.15s_ease-out]"
                            style={{ animation: 'fadeIn 0.15s ease-out' }}>

                            {/* Kullanıcı Bilgisi */}
                            <div className="px-4 py-3 border-b border-slate-100">
                                <p className="text-[13px] font-bold text-slate-800">{user?.ad_soyad || 'Kullanıcı'}</p>
                                <p className="text-[12px] text-slate-500 font-medium mt-0.5">@{user?.kullanici_adi}</p>
                            </div>

                            <div className="p-2 border-b border-slate-100">
                                <button
                                    onClick={() => {
                                        setDropdownOpen(false);
                                        navigate('/profil-ayarlari');
                                    }}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium
                                               text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition-colors"
                                >
                                    <Settings className="w-4 h-4" />
                                    Profil Ayarları
                                </button>
                            </div>

                            {/* Çıkış Butonu */}
                            <div className="p-2">
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-semibold
                                               text-red-600 hover:bg-red-50 transition-colors"
                                >
                                    <LogOut className="w-4 h-4" />
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
