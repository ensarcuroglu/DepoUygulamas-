/**
 * TerminalLayout — Mobil saha operatörü arayüzü ana sarmalayıcısı (PWA V3)
 * Scroll kilidi çözüldü, Native App hissi ve Zinc/Emerald uyumu eklendi.
 */
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { ClipboardList, BarChart2, LogOut, ChevronLeft, ScanLine } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const NAV_ITEMS = [
  { to: '/terminal/gorevler', icon: ClipboardList, label: 'Görevler' },
  { to: '/terminal/yerlestirme', icon: ScanLine, label: 'Yerleştir' },
  { to: '/terminal/ozet', icon: BarChart2, label: 'Özet' },
];

export default function TerminalLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout?.();
    navigate('/login', { replace: true });
  };

  return (
    // ÇÖZÜM: min-h-[100dvh] yerine fixed inset-0 kullanılarak cihazın kendi scroll'u kilitlendi.
    // Artık sadece içerideki main alanı kendi içinde özgürce kayabilecek.
    <div className="fixed inset-0 bg-zinc-950 text-zinc-100 flex flex-col select-none overflow-hidden overscroll-none">
      
      {/* Performanslı Ambient Glow (Yalnızca üst kısımda hafif bir derinlik) */}
      <div 
        className="absolute top-0 left-0 right-0 h-[35vh] bg-gradient-to-b from-emerald-500/10 to-transparent pointer-events-none"
        style={{ willChange: 'opacity' }}
      />
      
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: '16px',
            background: 'rgba(24, 24, 27, 0.95)', // zinc-900
            backdropFilter: 'blur(16px)',
            color: '#f4f4f5', // zinc-50
            border: '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: '0 10px 30px -5px rgba(0,0,0,0.5)',
            fontSize: '14px',
            fontWeight: 600,
            padding: '12px 16px',
          },
          success: { iconTheme: { primary: '#34d399', secondary: '#18181b' } }, // emerald-400
          error: { iconTheme: { primary: '#f43f5e', secondary: '#18181b' } }, // rose-500
        }}
      />

      {/* Header: Mobil Odaklı, Sabit Yükseklikli (flex-none) */}
      <header className="flex-none relative z-40 bg-zinc-950/80 backdrop-blur-xl border-b border-white/[0.03] pt-[env(safe-area-inset-top)] shadow-sm shadow-black/20">
        <div className="flex items-center justify-between px-4 py-3 h-16">
          <div className="flex items-center gap-3">
            
            {user?.rol === 'depocu' && (
              <button
                onClick={() => navigate('/depocu')}
                className="flex items-center justify-center w-10 h-10 text-zinc-400 bg-zinc-900/80 hover:bg-zinc-800 hover:text-emerald-400 active:scale-90 transition-all rounded-[14px] border border-white/[0.02]"
                aria-label="Panele Dön"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}

            <div className="flex flex-col justify-center">
              <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest mb-0.5 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Terminal
              </span>
              <span className="text-sm font-bold text-zinc-100 truncate max-w-[150px] sm:max-w-[200px]">
                {user?.ad_soyad || user?.kullanici_adi || 'Operatör'}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center justify-center w-10 h-10 text-zinc-500 hover:text-rose-400 bg-transparent hover:bg-rose-500/10 active:scale-90 transition-all rounded-[14px]"
            aria-label="Çıkış Yap"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content Area: Sadece bu alan kaydırılabilir (overflow-y-auto) */}
      <main className="flex-1 w-full overflow-y-auto overflow-x-hidden relative z-10 custom-scrollbar scroll-smooth">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 15 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            // ÇÖZÜM: h-full kaldırıldı, min-h-full eklendi.
            // Alt navigasyon barı kadar boşluk (pb-28) buraya tanımlandı ki scroll en dibe inebilsin.
            className="min-h-full pb-[calc(100px+env(safe-area-inset-bottom))]"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Bottom Navigation: Absolute konumlandırma ile her zaman en altta sabit */}
      <nav className="absolute bottom-0 left-0 right-0 z-50 pb-[env(safe-area-inset-bottom)] px-4 mb-4 pointer-events-none">
        <div className="max-w-md mx-auto bg-zinc-900/95 backdrop-blur-2xl border border-white/[0.06] shadow-2xl shadow-black/80 rounded-[24px] p-1.5 flex pointer-events-auto relative">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className="flex-1 relative flex flex-col items-center justify-center h-14 tap-highlight-transparent rounded-[18px]"
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-emerald-500/10 rounded-[18px]"
                      transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                    />
                  )}
                  
                  <motion.div 
                    className={`relative z-10 flex flex-col items-center gap-1.5 ${
                      isActive ? 'text-emerald-400' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                    animate={{ scale: isActive ? 1 : 0.95 }}
                    transition={{ duration: 0.2 }}
                  >
                    <item.icon 
                      className="w-[22px] h-[22px]" 
                      strokeWidth={isActive ? 2.5 : 2} 
                    />
                    <span className="text-[10px] font-bold tracking-wide">
                      {item.label}
                    </span>
                  </motion.div>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

    </div>
  );
}