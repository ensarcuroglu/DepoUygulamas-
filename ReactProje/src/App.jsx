import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { AuthProvider } from './contexts/AuthProvider';
import PrivateRoute from './components/PrivateRoute';
import RoleRoute from './components/RoleRoute';
import DashboardLayout from './components/layout/DashboardLayout';
import TerminalLayout from './components/layout/TerminalLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UrunlerPage from './pages/UrunlerPage';
import KategorilerPage from './pages/KategorilerPage';
import StokHareketleriPage from './pages/StokHareketleriPage';
import KullanicilarPage from './pages/KullanicilarPage';
import AyarlarPage from './pages/AyarlarPage';
import TedarikcilerPage from './pages/TedarikcilerPage';
import ProfilAyarlariPage from './pages/ProfilAyarlariPage';
import LotlarPage from './pages/LotlarPage';
import PaletlerPage from './pages/PaletlerPage';
import DepolarPage from './pages/DepolarPage';
import DepoKrokiPage from './pages/DepoKrokiPage';
import SistemLoglariPage from './pages/SistemLoglariPage';
import DestekMasasiPage from './pages/DestekMasasiPage';
import SevkiyatlarPage from './pages/SevkiyatlarPage';
import SiparislerPage from './pages/SiparislerPage';
import SevkiyatPlanlamaPage from './pages/SevkiyatPlanlamaPage';
import IrsaliyelerPage from './pages/IrsaliyelerPage';
import RaporlarPage from './pages/RaporlarPage';
import RaporOlusturPage from './pages/RaporOlusturPage';
import RaporSablonlarPage from './pages/RaporSablonlarPage';
import RaporZamanliPage from './pages/RaporZamanliPage';
import StokSayimPage from './pages/StokSayimPage';
import MalKabulIrsaliyeleriPage from './pages/MalKabulIrsaliyeleriPage';
import ZonlarPage from './pages/ZonlarPage';
import YerlestirmeGorevleriPage from './pages/YerlestirmeGorevleriPage';
import GorevListesiPage from './pages/terminal/GorevListesiPage';
import YerlestirmePage from './pages/terminal/YerlestirmePage';
import TerminalOzetPage from './pages/terminal/TerminalOzetPage';

/**
 * Varsayılan yönlendirme: Depocu → stok-hareketleri, Admin → dashboard
 */
function DefaultRedirect() {
  const { user } = useAuth();
  const target = (user?.rol === 'depocu' || user?.rol === 'lojistik') 
    ? '/stok-hareketleri' 
    : (user?.rol === 'goruntuleyen') 
      ? '/profil-ayarlari' 
      : '/dashboard';
  return <Navigate to={target} replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Herkese açık: Giriş sayfası */}
          <Route path="/login" element={<LoginPage />} />

          {/* Korumalı alanlar: Giriş gerektiren tüm sayfalar */}
          <Route element={<PrivateRoute />}>
            <Route element={<DashboardLayout />}>

              {/* Sadece Admin erişimli sayfalar */}
              <Route element={<RoleRoute allowedRoles={['admin']} />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/urunler" element={<UrunlerPage />} />
                <Route path="/kategoriler" element={<KategorilerPage />} />
                <Route path="/lotlar" element={<LotlarPage />} />
                <Route path="/paletler" element={<PaletlerPage />} />
                <Route path="/kullanicilar" element={<KullanicilarPage />} />
                <Route path="/ayarlar" element={<AyarlarPage />} />
                <Route path="/tedarikciler" element={<TedarikcilerPage />} />
                <Route path="/sistem-loglari" element={<SistemLoglariPage />} />
              </Route>

              {/* Depo Yönetimi (Admin + Lojistik) */}
              <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                <Route path="/depolar" element={<DepolarPage />} />
                <Route path="/depo-kroki" element={<DepoKrokiPage />} />
                <Route path="/siparisler" element={<SiparislerPage />} />
                <Route path="/sevkiyat-planlama" element={<SevkiyatPlanlamaPage />} />
              </Route>

              {/* İrsaliye Yönetimi (Admin + Lojistik + Depocu) */}
              <Route element={<RoleRoute allowedRoles={['admin', 'lojistik', 'depocu']} />}>
                <Route path="/irsaliyeler" element={<IrsaliyelerPage />} />
                <Route path="/mal-kabul-irsaliyeleri" element={<MalKabulIrsaliyeleriPage />} />
              </Route>

              {/* Stok Sayımı (Admin + Depocu) */}
              <Route element={<RoleRoute allowedRoles={['admin', 'depocu']} />}>
                <Route path="/stok-sayim" element={<StokSayimPage />} />
              </Route>

              {/* Raporlama (Admin + Lojistik) */}
              <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                <Route path="/raporlar" element={<RaporlarPage />} />
                <Route path="/raporlar/olustur" element={<RaporOlusturPage />} />
                <Route path="/raporlar/sablonlar" element={<RaporSablonlarPage />} />
                <Route path="/raporlar/zamanli" element={<RaporZamanliPage />} />
              </Route>

              {/* Yerleştirme Görevleri (Admin + Lojistik) */}
              <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                <Route path="/zonlar" element={<ZonlarPage />} />
                <Route path="/yerlestirme-gorevleri" element={<YerlestirmeGorevleriPage />} />
              </Route>

              {/* Herkesin erişebildiği korumalı alanlar */}
              <Route path="/stok-hareketleri" element={<StokHareketleriPage />} />
              <Route path="/sevkiyatlar" element={<SevkiyatlarPage />} />
              <Route path="/profil-ayarlari" element={<ProfilAyarlariPage />} />
              <Route path="/destek-masasi" element={<DestekMasasiPage />} />

            </Route>
          </Route>

          {/* Mobil Terminal Routes (TerminalLayout — dark, saha UI) */}
          <Route element={<PrivateRoute />}>
            <Route element={<TerminalLayout />}>
              <Route element={<RoleRoute allowedRoles={['admin', 'depocu', 'lojistik']} />}>
                <Route path="/terminal/gorevler" element={<GorevListesiPage />} />
                <Route path="/terminal/yerlestirme" element={<YerlestirmePage />} />
                <Route path="/terminal/ozet" element={<TerminalOzetPage />} />
              </Route>
            </Route>
          </Route>

          {/* Bilinmeyen rotalar → Role göre yönlendir */}
          <Route path="*" element={<DefaultRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
