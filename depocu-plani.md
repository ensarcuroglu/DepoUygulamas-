# Plan: Depocuya Özel Sade Mod (DepocuLayout)

Depocu rolü için `/depocu/*` URL namespace'i altında, sidebar'sız ve görev odaklı (task-driven)
ayrı bir layout + ana sayfa oluşturulur. Mevcut sayfa bileşenleri değiştirilmez — farklı bir
layout ve URL altında yeniden kullanılır. URL yapısı, kullanıcı rolüne göre açıkça ayrışır;
implicit sıra hilesi veya rol bazlı layout switcher kullanılmaz.

**Sektör standardı referans (Manhattan WMS, SAP EWM, Fishbowl):**
- Operatör menü değil görev kuyruğu görür
- Tek aktif görev akışı, FIFO sıralaması
- Sidebar = 0; bottom tab nav, büyük dokunmatik hedefler (≥48px)
- URL yapısı rol/bağlam bazlı ayrışır

## Scope

**In:**
- `DepocuLayout.jsx` — yeni layout bileşeni (sidebar yok, bottom tab nav)
- `DepocuAnaSayfasi.jsx` — task-driven ana sayfa
- `App.jsx` — `/depocu/*` route grubu ekleme + DefaultRedirect güncelleme

**Out:**
- Mevcut sayfa bileşenlerinin içi — hiçbirine dokunulmaz
- Admin / Lojistik rotaları ve DashboardLayout — tamamen aynı kalır
- Terminal rotaları (`/terminal/*`) — TerminalLayout olduğu gibi kalır
- Backend — sıfır değişiklik

## URL Yapısı (Yeni)

| URL | Layout | Bileşen | Erişim |
|-----|---------|---------|--------|
| `/depocu` | DepocuLayout | DepocuAnaSayfasi (yeni) | depocu |
| `/depocu/mal-kabul` | DepocuLayout | MalKabulIrsaliyeleriPage (mevcut) | depocu |
| `/depocu/stok` | DepocuLayout | StokHareketleriPage (mevcut) | depocu |
| `/depocu/stok-sayim` | DepocuLayout | StokSayimPage (mevcut) | depocu |
| `/depocu/sevkiyat` | DepocuLayout | SevkiyatlarPage (mevcut) | depocu |
| `/depocu/irsaliyeler` | DepocuLayout | IrsaliyelerPage (mevcut) | depocu |
| `/depocu/destek` | DepocuLayout | DestekMasasiPage (mevcut) | depocu |
| `/depocu/profil` | DepocuLayout | ProfilAyarlariPage (mevcut) | depocu |
| `/terminal/*` | TerminalLayout | (değişmez) | depocu + admin + lojistik |
| `/dashboard`, `/urunler`, ... | DashboardLayout | (değişmez) | admin / lojistik |

**Neden `/depocu/*` namespace?**
- URL yapısı hangi bağlamda olduğunu açıkça gösterir
- React Router'da implicit sıra bağımlılığı yok
- Her layout kendi URL alanını sahiplenir — test edilmesi, bakımı, genişletilmesi kolay
- Depocu'ya özel yeni sayfalar eklendiğinde doğal yeri belli
- Admin `/stok-hareketleri`'ne erişmekten etkilenmez

## Action Items

- [ ] **Oluştur** `ReactProje/src/components/layout/DepocuLayout.jsx`
  - Açık slate tema (`bg-slate-50`), sidebar YOK
  - Sabit üst header: Depo ikonu + "Depo Operatörü" + kullanıcı `ad_soyad` + çıkış butonu
  - `<Outlet />` (orta alan, `pb-20` — bottom nav için boşluk)
  - `<Toaster />` (TerminalLayout'taki aynı config)
  - Alt tab bar — 5 sekme, min 48px yükseklik, ikon + etiket:
    - **Ana Sayfa** → `/depocu` (Home ikonu)
    - **Mal Kabul** → `/depocu/mal-kabul` (PackageCheck ikonu)
    - **Stok** → `/depocu/stok` (ArrowLeftRight ikonu)
    - **Sevkiyat** → `/depocu/sevkiyat` (Truck ikonu)
    - **Profil** → `/depocu/profil` (UserCircle ikonu)
  - Active tab: `useLocation` + `pathname === tab.path` (exact match, `/depocu` için)
    veya `pathname.startsWith(tab.path)` (diğerleri için — `/depocu/stok-sayim` stok tab'ı vurgusun)

- [ ] **Oluştur** `ReactProje/src/pages/depocu/DepocuAnaSayfasi.jsx`
  - `useAsync` hook kullanır (mevcut convention)
  - `getBekleyenGorevOzet()` API çağrısı (zaten var: `/yerlestirme-gorevleri/bekleyen/ozet`)
  - **Görev Kuyruğu kartı** (üstte, belirgin): `toplam_bekleyen` + `acil` sayısı
    → tıklanınca `/terminal/gorevler` (TerminalLayout'a geçiş — beklenen davranış)
  - **Quick Action grid** (2×2):
    - Mal Kabul → `/depocu/mal-kabul`
    - Stok Sayımı → `/depocu/stok-sayim`
    - Stok Hareketi → `/depocu/stok`
    - Destek Talebi → `/depocu/destek`
  - Loading skeleton + hata durumunda toast
  - Klasör: `pages/depocu/` — ileride depocu'ya özel başka sayfalar buraya gelir

- [ ] **Düzenle** `ReactProje/src/App.jsx`
  - `DepocuLayout` ve `DepocuAnaSayfasi` import ekle
  - `DefaultRedirect`: depocu → `/depocu` (mevcut: `/stok-hareketleri`)
  - Yeni route bloğu ekle (mevcut blokların yanına, `<PrivateRoute>` içinde):
    ```jsx
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
    ```
  - DashboardLayout bloğundaki depocu+admin ortak rotalar **olduğu gibi kalır**
    (admin `/stok-hareketleri`'ne erişmeye devam eder, çakışma yok)
  - Eski `/stok-hareketleri` depocu erişimi `RoleRoute`'tan kaldırılabilir —
    depocu artık `/depocu/stok`'u kullanır (opsiyonel, ileride temizlenebilir)

- [ ] **Doğrula** route izolasyonu
  - Depocu ile giriş → `/depocu` → DepocuLayout + DepocuAnaSayfasi
  - Admin ile giriş → `/dashboard` → DashboardLayout (etkilenmemiş)
  - Admin `/stok-hareketleri`'ne gider → DashboardLayout içinde açılır
  - Depocu `/terminal/gorevler`'e gider → TerminalLayout (etkilenmemiş)
  - Depocu `/dashboard`'a gitmeye çalışır → RoleRoute engeller (mevcut davranış)

- [ ] **Test** depocu akışı
  - Login → DepocuAnaSayfasi: görev kuyruğu kartı ve quick action'lar görünür
  - "Görev Kuyruğu" kartına tıkla → `/terminal/gorevler` açılır (TerminalLayout)
  - "Mal Kabul Yap" → `/depocu/mal-kabul` → MalKabulIrsaliyeleriPage DepocuLayout içinde
  - Bottom tab değiştir → doğru sayfa, aktif tab vurgulu
  - Çıkış butonu → login sayfasına yönlendirir

## Mimari Notlar

- **Sayfa bileşenleri layout-agnostik** — `StokHareketleriPage` hem `/stok-hareketleri`'nde (admin)
  hem `/depocu/stok`'ta (depocu) çalışır; bileşen kendi içinde navigasyon yapmıyor
- **Klasör yapısı** `pages/depocu/` — depocu'ya özel yeni sayfalar için doğal yer oluştu
- **DepocuLayout** terminal/dashboard bağımsız, kendi `useAuth` ile kullanıcı bilgisi alır
- **Gelecek genişleme**: depocu'ya özel sayfa gerekirse `/depocu/yeni-sayfa` + `pages/depocu/YeniSayfa.jsx` — başka hiçbir şey değişmez
