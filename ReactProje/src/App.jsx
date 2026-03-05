import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
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
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/urunler" element={<UrunlerPage />} />
              <Route path="/kategoriler" element={<KategorilerPage />} />
              <Route path="/lotlar" element={<LotlarPage />} />
              <Route path="/paletler" element={<PaletlerPage />} />
              <Route path="/depolar" element={<DepolarPage />} />
              <Route path="/stok-hareketleri" element={<StokHareketleriPage />} />
              <Route path="/kullanicilar" element={<KullanicilarPage />} />
              <Route path="/ayarlar" element={<AyarlarPage />} />
              <Route path="/profil-ayarlari" element={<ProfilAyarlariPage />} />
              <Route path="/tedarikciler" element={<TedarikcilerPage />} />
            </Route>
          </Route>

          {/* Bilinmeyen rotalar → Dashboard'a yönlendir */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;