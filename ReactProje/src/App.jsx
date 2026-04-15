import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Context ve İskelet (Layout) bileşenleri uygulama ilk açıldığında 
// hemen lazım olacağı için statik (normal) import olarak bırakıyoruz.
import { useAuth } from './contexts/AuthContext';
import { AuthProvider } from './contexts/AuthProvider';
import { ThemeProvider } from './contexts/ThemeContext';
import PrivateRoute from './components/PrivateRoute';
import RoleRoute from './components/RoleRoute';
import DashboardLayout from './components/layout/DashboardLayout';
import TerminalLayout from './components/layout/TerminalLayout';
import DepocuLayout from './components/layout/DepocuLayout';

// Sayfaları lazy ile dinamik import'a çeviriyoruz. 
// Vite bu sayede her sayfayı (ve içindeki ağır kütüphaneleri) ayrı bir dosyaya bölecek.
const LoginPage = lazy(() => import('./pages/LoginPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const UrunlerPage = lazy(() => import('./pages/UrunlerPage'));
const KategorilerPage = lazy(() => import('./pages/KategorilerPage'));
const StokHareketleriPage = lazy(() => import('./pages/StokHareketleriPage'));
const KullanicilarPage = lazy(() => import('./pages/KullanicilarPage'));
const AyarlarPage = lazy(() => import('./pages/AyarlarPage'));
const TedarikcilerPage = lazy(() => import('./pages/TedarikcilerPage'));
const ProfilAyarlariPage = lazy(() => import('./pages/ProfilAyarlariPage'));
const LotlarPage = lazy(() => import('./pages/LotlarPage'));
const PaletlerPage = lazy(() => import('./pages/PaletlerPage'));
const DepolarPage = lazy(() => import('./pages/DepolarPage'));
const DepoKrokiPage = lazy(() => import('./pages/DepoKrokiPage'));
const SistemLoglariPage = lazy(() => import('./pages/SistemLoglariPage'));
const DestekMasasiPage = lazy(() => import('./pages/DestekMasasiPage'));
const SevkiyatlarPage = lazy(() => import('./pages/SevkiyatlarPage'));
const SiparislerPage = lazy(() => import('./pages/SiparislerPage'));
const SevkiyatPlanlamaPage = lazy(() => import('./pages/SevkiyatPlanlamaPage'));
const IrsaliyelerPage = lazy(() => import('./pages/IrsaliyelerPage'));
const RaporlarPage = lazy(() => import('./pages/RaporlarPage'));
const RaporOlusturPage = lazy(() => import('./pages/RaporOlusturPage'));
const RaporSablonlarPage = lazy(() => import('./pages/RaporSablonlarPage'));
const RaporZamanliPage = lazy(() => import('./pages/RaporZamanliPage'));
const StokSayimPage = lazy(() => import('./pages/StokSayimPage'));
const MalKabulIrsaliyeleriPage = lazy(() => import('./pages/MalKabulIrsaliyeleriPage'));
const InboundDashboardPage = lazy(() => import('./pages/InboundDashboardPage'));
const KpiDashboardPage = lazy(() => import('./pages/KpiDashboardPage'));
const ZonlarPage = lazy(() => import('./pages/ZonlarPage'));
const YerlestirmeGorevleriPage = lazy(() => import('./pages/YerlestirmeGorevleriPage'));
const ToplamaGorevleriPage = lazy(() => import('./pages/ToplamaGorevleriPage'));
const ToplamaGoreviDetayPage = lazy(() => import('./pages/ToplamaGoreviDetayPage'));
const DepocuAnaSayfasi = lazy(() => import('./pages/depocu/DepocuAnaSayfasi'));

// Terminal Sayfaları
const GorevListesiPage = lazy(() => import('./pages/terminal/GorevListesiPage'));
const YerlestirmePage = lazy(() => import('./pages/terminal/YerlestirmePage'));
const TerminalOzetPage = lazy(() => import('./pages/terminal/TerminalOzetPage'));

/**
 * Varsayılan yönlendirme: Depocu → /depocu, Lojistik → /stok-hareketleri, Admin → /dashboard
 */
function DefaultRedirect() {
  const { user } = useAuth();
  const target = user?.rol === 'depocu'
    ? '/depocu'
    : user?.rol === 'lojistik'
      ? '/stok-hareketleri'
      : user?.rol === 'goruntuleyen'
        ? '/profil-ayarlari'
        : '/dashboard';
  return <Navigate to={target} replace />;
}

// Tüm projeye uygun, standart, sade ve nötr bir yükleme ekranı
const LoadingSpinner = () => (
  <div className="flex h-screen w-full items-center justify-center bg-gray-50/50">
    <div className="flex flex-col items-center gap-3">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
      <p className="font-medium text-gray-500 text-sm tracking-wide">Yükleniyor...</p>
    </div>
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          {/* Suspense: Lazy load edilen sayfalar indirilirken ekranda ne görüneceğini belirler */}
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              {/* Herkese açık: Giriş sayfası */}
              <Route path="/login" element={<LoginPage />} />

              {/* ── Depocu Arayüzü (/depocu/*) ───────────────────────────────── */}
              <Route element={<PrivateRoute />}>
                <Route element={<RoleRoute allowedRoles={['depocu']} />}>
                  <Route element={<DepocuLayout />}>
                    <Route path="/depocu" element={<DepocuAnaSayfasi />} />
                    <Route path="/depocu/mal-kabul" element={<MalKabulIrsaliyeleriPage />} />
                    <Route path="/depocu/stok" element={<StokHareketleriPage />} />
                    <Route path="/depocu/stok-sayim" element={<StokSayimPage />} />
                    <Route path="/depocu/sevkiyat" element={<SevkiyatlarPage />} />
                    <Route path="/depocu/irsaliyeler" element={<IrsaliyelerPage />} />
                    <Route path="/depocu/destek" element={<DestekMasasiPage />} />
                    <Route path="/depocu/profil" element={<ProfilAyarlariPage />} />
                  </Route>
                </Route>
              </Route>

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

                  {/* İrsaliye Yönetimi */}
                  <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                    <Route path="/irsaliyeler" element={<IrsaliyelerPage />} />
                    <Route path="/mal-kabul-irsaliyeleri" element={<MalKabulIrsaliyeleriPage />} />
                  </Route>

                  {/* Inbound Dashboard + KPI */}
                  <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                    <Route path="/inbound-dashboard" element={<InboundDashboardPage />} />
                    <Route path="/kpi-dashboard" element={<KpiDashboardPage />} />
                  </Route>

                  {/* Stok Sayımı (Admin) */}
                  <Route element={<RoleRoute allowedRoles={['admin']} />}>
                    <Route path="/stok-sayim" element={<StokSayimPage />} />
                  </Route>

                  {/* Raporlama */}
                  <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                    <Route path="/raporlar" element={<RaporlarPage />} />
                    <Route path="/raporlar/olustur" element={<RaporOlusturPage />} />
                    <Route path="/raporlar/sablonlar" element={<RaporSablonlarPage />} />
                    <Route path="/raporlar/zamanli" element={<RaporZamanliPage />} />
                  </Route>

                  {/* Yerleştirme Görevleri */}
                  <Route element={<RoleRoute allowedRoles={['admin', 'lojistik']} />}>
                    <Route path="/zonlar" element={<ZonlarPage />} />
                    <Route path="/yerlestirme-gorevleri" element={<YerlestirmeGorevleriPage />} />
                  </Route>

                  {/* Toplama Görevleri — Faz 1 */}
                  <Route element={<RoleRoute allowedRoles={['admin', 'depocu', 'lojistik']} />}>
                    <Route path="/toplama-gorevleri" element={<ToplamaGorevleriPage />} />
                    <Route path="/toplama-gorevleri/:id" element={<ToplamaGoreviDetayPage />} />
                  </Route>

                  {/* Herkesin erişebildiği korumalı alanlar */}
                  <Route path="/stok-hareketleri" element={<StokHareketleriPage />} />
                  <Route path="/sevkiyatlar" element={<SevkiyatlarPage />} />
                  <Route path="/profil-ayarlari" element={<ProfilAyarlariPage />} />
                  <Route path="/destek-masasi" element={<DestekMasasiPage />} />

                </Route>
              </Route>

              {/* Mobil Terminal Routes */}
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
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;