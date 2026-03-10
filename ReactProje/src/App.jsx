import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import RoleRoute from './components/RoleRoute';
import DashboardLayout from './components/layout/DashboardLayout';
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

/**
 * Varsayılan yönlendirme: Depocu → stok-hareketleri, Admin → dashboard
 */
function DefaultRedirect() {
  const { user } = useAuth();
  const target = (user?.rol === 'depocu' || user?.rol === 'lojistik') ? '/stok-hareketleri' : '/dashboard';
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
              </Route>

              {/* Herkesin erişebildiği korumalı alanlar */}
              <Route path="/stok-hareketleri" element={<StokHareketleriPage />} />
              <Route path="/sevkiyatlar" element={<SevkiyatlarPage />} />
              <Route path="/profil-ayarlari" element={<ProfilAyarlariPage />} />
              <Route path="/destek-masasi" element={<DestekMasasiPage />} />

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