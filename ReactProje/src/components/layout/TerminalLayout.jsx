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
    <div className="min-h-screen bg-slate-900 flex flex-col text-white select-none">
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3500,
          style: {
            borderRadius: '12px',
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            fontSize: '15px',
            fontWeight: 600,
          },
          success: { iconTheme: { primary: '#22c55e', secondary: '#1e293b' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#1e293b' } },
        }}
      />

      {/* Minimal üst başlık */}
      <header className="bg-slate-950 border-b border-slate-800 px-4 py-3 flex items-center justify-between safe-area-top">
        <div className="flex items-center gap-2">
          {/* Panele Dön — yalnızca depocu rolünde görünür */}
          {user?.rol === 'depocu' && (
            <button
              onClick={() => navigate('/depocu')}
              className="flex items-center gap-1 text-slate-400 hover:text-amber-400 active:text-amber-500 transition-colors py-2 px-2 rounded-lg mr-1"
              aria-label="Depocu Paneline Dön"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="text-xs font-semibold hidden sm:inline">Panel</span>
            </button>
          )}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Saha Terminali</p>
            <p className="text-sm font-bold text-slate-200 leading-tight">{user?.ad_soyad || user?.kullanici_adi || 'Operatör'}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-slate-400 hover:text-red-400 active:text-red-500 transition-colors py-2 px-3 rounded-lg"
          aria-label="Çıkış"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-xs font-semibold hidden sm:inline">Çıkış</span>
        </button>
      </header>

      {/* Sayfa içeriği */}
      <main className="flex-1 overflow-y-auto pb-24">
        <Outlet />
      </main>

      {/* Alt navigasyon — büyük dokunmatik hedefler */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-950 border-t border-slate-800 safe-area-bottom z-50">
        <div className="flex">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center justify-center py-3 gap-1 transition-colors active:bg-slate-800 ${
                  isActive
                    ? 'text-amber-400 border-t-2 border-amber-400'
                    : 'text-slate-500 border-t-2 border-transparent hover:text-slate-300'
                }`
              }
            >
              <Icon className="w-6 h-6" />
              <span className="text-xs font-semibold">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
