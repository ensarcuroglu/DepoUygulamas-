# Üretim Paleti Konum İyileştirme — Uygulama Planı

**İlgili Rapor:** `URETIM-PALET-KONUM-ANALIZ-RAPORU.md`
**Plan Tarihi:** 22 Nisan 2026
**Yaklaşım:** Unified Inbound — "Mal Kabul" ve "Üretimden Kabul" tek kavram altında; depocu sahada context-switch yapmadan her iki akışa ulaşır.

---

## Karar Defteri (Rapor Üzerinde Revizyon)

| # | Konu | Rapor Önerisi | Nihai Karar | Gerekçe |
|---|------|---------------|-------------|---------|
| 1 | `/uretim-paletleri` kalite departman kısıtı | Kaldır | **Kaldırılacak** | Gerçek "kalite" rolü ileride eklenince ayrıca ele alınacak. |
| 2 | URL değişiklikleri | 301 redirect | **SPA doğru çözümü**: rotalar yeni isme taşınır; eski path'ler `<Navigate replace>` ile yenisine yönlenir. HTTP 301 SPA'da geçerli değil. | Bookmark/eski eğitim kaybı yok, yeni URL semantik doğru. |
| 3 | DepocuLayout entegrasyonu | Kutucuk/yeni sekme | **Kabul sekmesi bir "Kabul Seçim" ekranına dönüşür** + DepocuAnaSayfasi grid'ine `Üretimden Kabul` kutucuğu eklenir | Alt menü 5 sekme korunur, thumb-zone ve terminal merkez butonu bozulmaz; operatör hem nav'dan hem ana sayfadan ulaşır. |
| 4 | Sidebar grup yapısı | Yeni "Inbound Operations" accordion | **Mevcut "Lojistik & Sevkiyat" grubu iki parçaya ayrılır**: "Gelen Mal" + "Sevkiyat & Dağıtım". Üretim grubu kaldırılır. | Aynı kavramsal bütün, ekstra nesting yok. |
| 5 | Emoji kullanımı | Etiketlerde emoji | **lucide-react ikonları**; emoji kullanılmayacak | Mevcut sidebar tutarlılığı, CLAUDE.md yönergesi. |
| 6 | `/uretim-paletleri` konumu | Raporlama altına taşı | **"Gelen Mal" grubu içinde kalır** ("Üretim Palet Yönetimi" adıyla) | Kullanıcı zihninde aynı süreç; arama yükü düşer. |

---

## Kapsam

**Dahil:**
- Sidebar.jsx menü yapısı, grup adları, route güncellemeleri
- DepocuLayout.jsx: `Kabul` sekmesi seçim ekranına dönüşür
- DepocuAnaSayfasi.jsx: `Üretimden Kabul` hızlı erişim kutucuğu
- App.jsx: rota yeniden adlandırma + eski path redirect + depocu rotaları
- Yeni sayfa: `KabulSecimPage.jsx` (İrsaliyeli vs Üretimden seçimi)
- `/uretim-paletleri` sayfasındaki `departments: ['kalite']` kısıtının kaldırılması
- Sayfa başlıkları ve breadcrumb'ların yeni isimlendirmeye hizalanması

**Dahil Değil:**
- Backend API/rota isimleri (endpoint'ler URL'lerden bağımsız; isim değişmez)
- `InboundDashboard`'a üretim paleti metrik entegrasyonu (orta vade — ayrı iş)
- Yeni "Kalite" rolü tanımı (ileride ayrıca ele alınacak)
- Görsel redesign (mevcut komponent stilleri korunur)

---

## Yeni URL Haritası

| Eski URL | Yeni URL | Not |
|----------|----------|-----|
| `/mal-kabul-irsaliyeleri` | `/gelen-mal/irsaliyeli` | Tutarlı namespace. Eski path `<Navigate>` ile yönlenir. |
| `/uretim-paletleri/kabul` | `/gelen-mal/uretimden` | Aynı namespace altında. Eski path redirect edilir. |
| `/uretim-paletleri` | `/gelen-mal/uretim-palet-yonetimi` | Liste/yönetim sayfası. Eski path redirect edilir. |
| `/depocu/mal-kabul` | `/depocu/kabul` | Yeni "Kabul Seçim" ekranı |
| *(yeni)* | `/depocu/kabul/irsaliyeli` | MalKabulIrsaliyeleriPage |
| *(yeni)* | `/depocu/kabul/uretimden` | UretimPaletiKabulPage (depocu layout içinde) |

---

## Yeni Sidebar Menü Yapısı

```
Genel
└── İş Zekası & Özet (admin)

Ürün & Stok (admin, lojistik)
  (değişiklik yok)

Gelen Mal (admin, lojistik, depocu)               ← YENİ GRUP
├── İrsaliyeli Kabul          (mal-kabul-irsaliyeleri → /gelen-mal/irsaliyeli)
├── Üretimden Kabul           (/gelen-mal/uretimden)
├── Üretim Palet Yönetimi     (/gelen-mal/uretim-palet-yonetimi)
├── Inbound Panel             (/inbound-dashboard)
└── KPI Paneli                (/kpi-dashboard)

Sevkiyat & Dağıtım (admin, lojistik)
├── Sevkiyatlar (Çıkış)
├── Siparişler
├── Sevkiyat Planlama
└── İrsaliyeler (Çıkış)

Yerleştirme / Toplama / Saha Terminali / Yönetim & Rapor
  (değişiklik yok)
```

---

## DepocuLayout Yeni Davranışı

**Alt menü sekmeleri (5 sabit):** `Ana Sayfa | Kabul | Terminal | Stok | Profil`

`Kabul` tıklandığında `/depocu/kabul` açılır — bu iki büyük kart sunar:

```
┌──────────────────────────────────────────┐
│    KABUL TİPİ SEÇ                        │
├──────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐ │
│  │  [FileText]    │  │  [Factory]     │ │
│  │  İRSALİYELİ    │  │  ÜRETİMDEN     │ │
│  │  Tedarikçi /   │  │  Üretim hattı  │ │
│  │  irsaliye ile  │  │  barkodu ile   │ │
│  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────┘
```

Ek olarak DepocuAnaSayfasi `ANA_ISLEMLER` grid'ine `Üretimden Kabul` kutucuğu eklenir (doğrudan `/depocu/kabul/uretimden`).

---

## Action Items

[x] **1. Discovery:** `UretimPaletiKabulPage.jsx`'in depocu layout içinde çalıştığını doğrula — `useAuth`, `useNavigate`, toast kullanımı mevcut layout ile uyumlu mu teyit et
[x] **2. Routes (App.jsx):** Yeni path'leri ekle (`/gelen-mal/irsaliyeli`, `/gelen-mal/uretimden`, `/gelen-mal/uretim-palet-yonetimi`, `/depocu/kabul`, `/depocu/kabul/irsaliyeli`, `/depocu/kabul/uretimden`); eski path'ler için `<Route element={<Navigate to="..." replace />} />` redirect'leri ekle. `KabulSecimPage.jsx` stub oluşturuldu (adım 5'te tam tasarlanacak).
[x] **3. Kalite kısıtını kaldır:** App.jsx'te `/uretim-paletleri` üzerindeki `allowedDepartments={['kalite']}` kaldır; Sidebar.jsx'teki `departments: ['kalite']` sil
[x] **4. Sidebar refactor (Sidebar.jsx):** `uretim` grubunu kaldır, `lojistik` grubunu `gelen-mal` + `sevkiyat-dagitim` olarak ikiye ayır, yeni path'leri ve etiketleri (`İrsaliyeli Kabul`, `Üretimden Kabul`, `Üretim Palet Yönetimi`) yerleştir; ikonlar: `ClipboardCheck`, `Factory`, `Package`. Kullanılmayan `Smartphone` import'u temizlendi.
[ ] **5. Yeni sayfa (KabulSecimPage.jsx):** `ReactProje/src/pages/depocu/` altında iki-kartlı seçim ekranı (İrsaliyeli → `/depocu/kabul/irsaliyeli`, Üretimden → `/depocu/kabul/uretimden`); saha-UX prensipleri (min 96px dokunma alanı, active:scale, yüksek kontrast) — mevcut DepocuAnaSayfasi stil dili ile hizalı
[ ] **6. DepocuLayout güncelle:** `TAB_ITEMS` içinde `/depocu/mal-kabul` → `/depocu/kabul`; `isTabActive` mantığını `/depocu/kabul/*` prefix'ini kapsayacak şekilde genişlet; sekme etiketi `Kabul` kalır
[ ] **7. DepocuAnaSayfasi güncelle:** `ANA_ISLEMLER` dizisindeki `Mal Kabul` → `İrsaliyeli` (`to: '/depocu/kabul/irsaliyeli'`); yanına yeni kutucuk `Üretimden` (`icon: Factory`, `to: '/depocu/kabul/uretimden'`, `bg: 'bg-amber-50'`, `color: 'text-amber-700'`)
[ ] **8. Sayfa başlıkları:** `UretimPaletiKabulPage`, `MalKabulIrsaliyeleriPage`, `UretimPaletleriPage` başlıklarını yeni isimlendirmeye hizala (`Üretimden Kabul`, `İrsaliyeli Kabul`, `Üretim Palet Yönetimi`)
[ ] **9. Validation:** Her rol (admin, lojistik, depocu) ile login olup şu akışları dene: (a) sidebar'dan her yeni link çalışıyor, (b) eski URL doğrudan girildiğinde redirect oluyor, (c) depocu `/depocu/kabul` → her iki alt sayfa, (d) depocu `Üretimden` kutucuğu ana sayfadan doğrudan açıyor, (e) `npm run lint` temiz
[ ] **10. Commit:** Tek commit — `refactor(ui): unify inbound flows under /gelen-mal and add depocu kabul chooser`; mesajda eski→yeni URL tablosunu not et

---

## Validation Matrisi

| Senaryo | Beklenen |
|---------|----------|
| Admin sidebar'da "Gelen Mal" grubunu görür | 5 alt madde |
| Lojistik sidebar'da "Gelen Mal" grubunu görür | `Üretim Palet Yönetimi` dahil 5 alt madde |
| Depocu sidebar kullanamaz (layout'u yok) | `/depocu/*` içinde yaşar |
| `/mal-kabul-irsaliyeleri` elle yazılır | `/gelen-mal/irsaliyeli`'ye redirect |
| `/uretim-paletleri/kabul` elle yazılır | `/gelen-mal/uretimden`'e redirect |
| Depocu alt menüde Kabul'a basar | `/depocu/kabul` seçim ekranı |
| Depocu ana sayfada `Üretimden` kutucuğuna basar | `/depocu/kabul/uretimden` (1 tap) |
| `npm run lint` | Hata yok |

---

## Risk ve Önlemler

| Risk | Önlem |
|------|-------|
| Feature flag `VITE_FEATURE_URETIM_PALET_ENABLED` kapalıyken yeni rotalar kırılır | Plan içindeki yeni üretim-kabul rotaları aynı flag arkasında kalacak; sadece isimlendirme değişir |
| Depocu layout'unda `/uretim-paletleri/kabul` sayfasının stilinin uyumsuz olması | Sayfa zaten mobile-friendly barkod akışı; layout içinde test et, gerekirse `<main>` padding ayarla |
| Eski bookmark'lar | Redirect rotaları ilk 2 sprint korunacak, sonra temizlenebilir |
| Kalite kısıtının kaldırılmasıyla tüm depocuların yönetim listesi görmesi | Kabul edildi (not defterine alındı); gerçek kalite rolü eklendiğinde rota-bazlı kısıtla geri getirilecek |

---

## Başarı Metrikleri

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| Depocunun üretim paleti kabulüne ulaşmak için tıklama sayısı | DepocuLayout'tan imkânsız (admin layout'a geçmek zorunda) | 2 tıklama (alt menü → Üretimden) veya 1 tıklama (ana sayfa kutucuğu) |
| "Kabul" kelimesinin ayrı iki konumda ve anlamda görünmesi | Var (sidebar "Palet Kabul" + "Mal Kabul") | Aynı grup altında, net alt isimlerle ayrışmış |
| Yeni operatörün eğitime ihtiyacı | Orta | Düşük (seçim ekranı self-explanatory) |
