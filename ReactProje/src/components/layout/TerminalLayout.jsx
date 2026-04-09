/**
 * TerminalLayout — Mobil saha operatörü arayüzü.
 *
 * Tasarım: Industrial Dark — depo ortamı için yüksek kontrast,
 * büyük dokunmatik hedefler, minimal dikkat dağıtıcı.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { ClipboardList, Package, BarChart2, LogOut, ChevronLeft } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';

const NAV_ITEMS = [
  { to: '/terminal/gorevler', icon: ClipboardList, label: 'Görevler' },
  { to: '/terminal/yerlestirme', icon: Package, label: 'Yerleştir' },
  { to: '/terminal/ozet', icon: BarChart2, label: 'Özet' },
];

export default function TerminalLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout?.();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100 select-none overflow-hidden relative">
      {/* Arka plan vurgusu (Glow efekti) */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[30vh] bg-amber-500/5 blur-[120px] pointer-events-none" />
      
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: '16px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(12px)',
            color: '#f8fafc',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            boxShadow: '0 10px 40px -10px rgba(0,0,0,0.5)',
            fontSize: '14px',
            fontWeight: 600,
            padding: '12px 16px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#0f172a' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#0f172a' } },
        }}
      />

      {/* Minimal üst başlık */}
      <header className="sticky top-0 z-40 bg-slate-950/70 backdrop-blur-2xl border-b border-white/5 px-4 py-3 flex items-center justify-between safe-area-top shadow-xl shadow-black/10">
        <div className="flex items-center gap-2">
          {/* Panele Dön — yalnızca depocu rolünde görünür */}
          {user?.rol === 'depocu' && (
            <button
              onClick={() => navigate('/depocu')}
              className="flex justify-center items-center h-10 w-10 md:w-auto md:px-3 text-slate-400 bg-white/5 hover:bg-white/10 hover:text-amber-400 active:scale-95 transition-all rounded-xl mr-2"
              aria-label="Depocu Paneline Dön"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="text-xs font-bold hidden sm:inline ml-1">Panel</span>
            </button>
          )}
          <div className="flex flex-col">
            <span className="text-[10px] text-amber-500/80 uppercase tracking-[0.2em] font-bold">Terminal</span>
            <span className="text-sm font-black text-white leading-tight mt-0.5">
              {user?.ad_soyad || user?.kullanici_adi || 'Operatör'}
            </span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex justify-center items-center h-10 w-10 md:w-auto md:px-3 text-slate-400 bg-red-500/10 hover:bg-red-500/20 hover:text-red-400 active:scale-95 transition-all rounded-xl"
          aria-label="Çıkış"
        >
          <LogOut className="w-4 h-4 md:w-5 md:h-5" />
        </button>
      </header>

      {/* Sayfa içeriği */}
      <main className="flex-1 overflow-y-auto pb-28 relative z-10 w-full h-full custom-scrollbar">
        <Outlet />
      </main>

      {/* Alt navigasyon — Glassmorphism ve Yüksek Kontrast */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 safe-area-bottom">
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-2xl border-t border-white/10" />
        <div className="relative flex px-2 py-2 max-w-md mx-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex-1 relative flex flex-col items-center justify-center py-2 gap-1 rounded-2xl transition-all duration-300 active:scale-95 ${
                  isActive
                    ? 'text-amber-400 bg-amber-400/10'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 md:w-6 md:h-6 transition-transform duration-300 ${isActive ? 'scale-110' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
                  <span className="text-[10px] font-bold tracking-wide">{label}</span>
                  {isActive && (
                    <span className="absolute -top-1 w-8 h-1 bg-amber-400 rounded-full shadow-[0_0_10px_rgba(245,158,11,0.5)]" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
