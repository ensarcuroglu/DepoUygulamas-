# Depocu Rolü Mobile-First Redesign Planı

> **Hedef:** Depo operatörünün (rol: `depocu`) dokunduğu tüm ekranları, Android el terminali (Zebra/Honeywell, 5"–6", eldivenli parmak, değişken saha ışığı) için mobile-first ve OLED-dostu biçimde yeniden kurmak.
> **Yaklaşım:** `pages/depocu/` altına **ayrı sayfa dosyaları** açılır — admin/lojistik tarafı dokunulmaz.
> **Tasarım dili:** "Hangar Minimal" (Fonksiyonel Minimalizm × Material 3 token sistemi × iOS bottom-sheet ergonomisi).
> **Kapsam:** 14 ekran + paylaşılan design system + 2 yeni hook + route güncellemeleri.

---

## 1. Mevcut Durum (Tarama Özeti)

### Depocu'ya özel (korunacak + dark mode uyarlaması)
| Dosya | Satır | Mobil hazırlık |
|---|---|---|
| `components/layout/DepocuLayout.jsx` | ~145 | 90% (dark mod + offline chip eklenecek) |
| `pages/depocu/DepocuAnaSayfasi.jsx` | ~187 | 85% (dark mode + küçük ayarlar) |
| `pages/depocu/KabulSecimPage.jsx` | ~72 | 90% (dark mode) |

### Depocu'nun kullandığı paylaşılan sayfalar (yeni depocu sürümleri açılacak)
| Admin kaynak | Satır | Redesign tipi | Hedef dosya |
|---|---|---|---|
| `StokHareketleriPage.jsx` | 1361 | **Full wizard** | `pages/depocu/DepocuStokHareketleriPage.jsx` |
| `SevkiyatlarPage.jsx` | 805 | **Swipe-list + sheet** | `pages/depocu/DepocuSevkiyatlarPage.jsx` |
| `IrsaliyelerPage.jsx` | 728 | **Segment + fullscreen sheet** | `pages/depocu/DepocuIrsaliyelerPage.jsx` |
| `MalKabulIrsaliyeleriPage.jsx` | 1093 | **4-adım wizard** | `pages/depocu/DepocuMalKabulPage.jsx` |
| `StokSayimPage.jsx` | 557 | **Tek-odak scan** | `pages/depocu/DepocuStokSayimPage.jsx` |
| `UretimPaletiKabulPage.jsx` | 176 | **Scan-monolith only** | `pages/depocu/DepocuUretimKabulPage.jsx` |
| `DestekMasasiPage.jsx` | 619 | **Segment + chat sheet** | `pages/depocu/DepocuDestekPage.jsx` |
| `ProfilAyarlariPage.jsx` | 278 | **Form sheets** | `pages/depocu/DepocuProfilPage.jsx` |

### Terminal sayfaları (`pages/terminal/`)
Zaten mobile-first; dark mode ince ayarı + Scan Monolith bileşenine geçiş.
| Dosya | Satır | Not |
|---|---|---|
| `GorevListesiPage.jsx` | 296 | Dark mod + pagination kaldır |
| `YerlestirmePage.jsx` | 614 | ScanMonolith + StepIndicator entegrasyonu |
| `TerminalOzetPage.jsx` | 246 | Dark mod + KPI display font |

### Mevcut yardımcılar (yeniden kullanılacak)
- `hooks/useAsync.js`, `hooks/useBarcodeScanner.js`, `hooks/useTerminalDepo.js`
- `components/ZXingBarcodeScanner.jsx` (kamera fallback)
- `contexts/ThemeContext` (dark/light — depocu'da zorunlu aktif)
- `services/api.js`, `utils/hata.js`

---

## 2. Tasarım Yönü — "Hangar Minimal"

**Farklılaştırıcı Çapa:** Her ekranın merkezinde **Scan Monolith** — canlı nabız halesi olan, devasa, tek bir tarama yüzeyi.
**DFII:** Impact 4 + Fit 5 + Feasibility 5 + Performance 5 − Risk 1 = **+14 (Excellent)**.

### 2.1 Tasarım Prensipleri
1. **Tek ekran = tek iş.** Her sayfada tek birincil CTA; ikincil eylemler sheet'e kaçar.
2. **Tarama birincildir, klavye ikincildir.** Scan Monolith sayfanın optik merkezinde; klavye sadece fallback.
3. **Parmak eldivenlidir.** Min 56px dokunma hedefi, 8px ayraç, thumb-zone'da birincil aksiyon.
4. **Bilgi > süsleme.** Gradient/shadow sadece elevation token'ı üzerinden.
5. **OLED-first dark.** Saf siyah yüzey; her bileşen önce dark tasarlanır.
6. **Durum = renk + ikon + metin.** Renk körü & güneş altı için üçlü kod.
7. **Geri döndürülebilirlik.** Her tarama sonrası 3sn "geri al" pill.

### 2.2 Renk Token'ları (CSS vars — `src/styles/depocu-tokens.css`)

**Dark (birincil — OLED):**
```css
--bg:#000; --surface:#0A0B0D; --surface-1:#121316; --surface-2:#1A1C20; --surface-3:#24262B;
--outline:#2E3138; --outline-strong:#4A4E57;
--primary:#5AA9FF; --on-primary:#00244D;
--primary-container:#0A3B73; --on-primary-container:#CFE3FF;
--accent:#FFC043; --on-accent:#2A1C00;
--success:#4ADE80; --warning:#FFB020; --error:#FF5C5C; --info:#5AA9FF;
--on-surface:#E6E8EC; --on-surface-dim:#9AA0AA; --on-surface-muted:#5E6470;
```

**Light (ışıklı saha):**
```css
--bg:#F5F6F8; --surface:#FFFFFF; --surface-1:#FAFBFC; --surface-2:#F0F2F5; --surface-3:#E6E9EE;
--outline:#D6DAE0; --outline-strong:#9AA0AA;
--primary:#0A66E0; --on-primary:#FFFFFF;
--primary-container:#DCE9FF; --on-primary-container:#002A66;
--accent:#C27400; --success:#0F9D58; --warning:#B8750A; --error:#C22B2B;
--on-surface:#0E1014; --on-surface-dim:#4A4E57; --on-surface-muted:#7B818C;
```

### 2.3 Tipografi
- **Mono (sayı/barkod):** `JetBrains Mono`
- **Metin:** `Manrope`

| Rol | px / line | weight | not |
|---|---|---|---|
| display | 32 / 38 | 800 | Scan Monolith sayısı (Mono) |
| title-lg | 24 / 30 | 800 | sayfa başlığı |
| title | 20 / 26 | 700 | kart başlığı |
| body-lg | 17 / 24 | 500 | birincil metin |
| body | 15 / 22 | 500 | |
| label | 13 / 16 | 700 | uppercase tracking-.08em |
| caption | 12 / 16 | 500 | timestamp, meta |

### 2.4 Elevation & Spacing
- **Elevation:** elev-0 `bg` → elev-4 `surface-3`. Dark'ta gölge yok, offset. Light'ta `0 1px 2px rgba(0,0,0,.06)` ≥elev-2.
- **Radius:** `xs:6 · sm:10 · md:14 · lg:20 · xl:28`.
- **Spacing:** 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 (8px grid + 12/20 ara).
- **Safe area:** `padding-bottom: env(safe-area-inset-bottom)`.

### 2.5 Motion
| Olay | ms | Easing |
|---|---|---|
| Active tap | 80 | ease-out, `scale .97` |
| Sheet açılış | 280 | `cubic-bezier(.22,1,.36,1)` |
| Sheet kapanış | 220 | `cubic-bezier(.4,0,1,1)` |
| Scan success hale | 400 | ease-out, scale 1→1.06 + fade |
| Toast | 200 | ease-out |
| Step geçiş | 240 | slide-x + fade |
| List swipe | follow-finger | — |

`prefers-reduced-motion: reduce` → tüm süreler 0, sadece opacity crossfade.

### 2.6 Erişilebilirlik
- Kontrast: `on-surface/surface` ≥ 13.8:1 (dark), ≥ 7:1 (light). Hiç <4.5 yok.
- Min touch: 56×56 CSS hedefi (padding ile).
- Focus ring: `ring-2 ring-primary ring-offset-2 ring-offset-bg`.
- IconButton'larda `aria-label` zorunlu.
- ScanField: `role="search" aria-live="polite"`.
- Haptic + audio: `navigator.vibrate(30)` + Web Audio beep; `prefers-reduced-motion` ile titreşim kapatılır.
- Sheet açıkken focus trap; DataWedge klavye odağını kaybetmesin diye `useAutoRefocus`.

---

## 3. Component Library İskeleti

Konum: `ReactProje/src/components/depocu/ui/`

| Bileşen | Boyut / Davranış |
|---|---|
| `Button` | `h-14` min, radius-md; variants: `filled / tonal / outline / ghost / danger`. Active: `scale .97` + opacity. |
| `IconButton` | 48×48 görsel, 56×56 tap (padding). |
| `InputField` | `h-14`, left-icon, right-clear; label üstte (floating değil). |
| `ScanField` | `h-20`, Mono caret-none; autofocus + `useAutoRefocus`; soldaki "SCAN" pulsing dot. |
| `ScanMonolith` | `h-48` hero; idle/ready/success/error; radial hale breathing 2s. |
| `Sheet` | Bottom-sheet; `rounded-t-[20px]`; drag handle 40×4; snap: auto / 50% / 92%. |
| `Card` | radius-md, surface-1, opsiyonel 4px left accent bar (semantik). |
| `ListItem` | min-h-72; swipe-sol = iptal, swipe-sağ = tamamla. |
| `StatusPill` | h-7, label typo; 8 variant: bekliyor/atandı/devam/tamam/hata/iptal/öncelikli/onay. |
| `StepIndicator` | 4 nokta + ilerleyen bar; sticky wizard üstünde. |
| `EmptyState` | 64px outline ikon + başlık + 1 CTA. |
| `Toast` | Top-center; haptic + ses; undo pill right-aligned. |
| `FAB` | 64×64 primary, merkez-alt (Terminal butonu olarak mevcut). |
| `TabBar` | Mevcut DepocuLayout alt nav (dark mode'a geçer). |
| `QuantityStepper` | h-14 −/+ + Mono sayı ortada. |
| `OfflineBadge` | Sticky chip; "SENKRON BEKLİYOR (n)". |

### Hook'lar (`hooks/`)
- `useAutoRefocus(ref)` — ScanField odağını pencere blur/sheet sonrası geri yakalar.
- `useHapticFeedback()` — `success()` / `error()` / `tap()` (vibration + Web Audio).
- `useOfflineQueue()` — placeholder (localStorage'da bekleyen eylem sayısı).

---

## 4. Sayfa-Sayfa Layout Özeti

1. **DepocuAnaSayfasi** — Hero durum + 2 kol grid (6 kutu) + alt liste. Üst sağda saat + offline chip.
2. **KabulSecimPage** — 2 tam-genişlik seçenek kartı (h-32), emerald/amber accent bar.
3. **DepocuStokHareketleriPage** — StepIndicator (Palet → Miktar → Hedef Raf). Her adımda ScanMonolith; alt "sepetim" sheet; "Gönder" sticky primary.
4. **DepocuSevkiyatlarPage** — Segment (Hazırlanıyor/Yolda/Teslim); kart listesi; swipe-sağ=Yükle, swipe-sol=İptal; tap → sheet detay.
5. **DepocuIrsaliyelerPage** — Segment (Sevk/İade); kart liste; FAB "+"; yeni form = tam-ekran sheet, plaka büyük ScanField.
6. **DepocuMalKabulPage** — 4-adım wizard: Tedarikçi → Kalem ekle (loop) → Varyans → Onay. Alt "sepet n kalem"; kalemde swipe-sol sil.
7. **DepocuStokSayimPage** — Tek odak: ScanField `h-20`; son 10 tarama liste; beep success/err; "Bitir & Varyans" sticky.
8. **DepocuUretimKabulPage** — Tam-ekran ScanMonolith + son 10 palet chip.
9. **DepocuDestekPage** — Segment (Açık/İşlemde/Çözüldü); kart liste; FAB "+"; detay → chat sheet.
10. **DepocuProfilPage** — 2 bölüm kartı (Profil / Şifre); tap → tam-ekran form sheet.
11. **Terminal/GorevListesiPage** — Sticky filtre chip; "Sıradaki Görevi Al" sticky primary; swipe-sağ başlat.
12. **Terminal/YerlestirmePage** — 4 StepIndicator + Scan Monolith her adımda; override sheet.
13. **Terminal/TerminalOzetPage** — 2×2 KPI grid (display font) + son tamamlananlar zaman çizelgesi.
14. **DepocuLayout** — Dark mod aktif; header sağında `OfflineBadge`; FAB korunur; safe-area.

---

## 5. Dosya Ağacı (Sonuç)

```
ReactProje/src/
├─ styles/
│  └─ depocu-tokens.css                       # FAZ 1
├─ components/
│  ├─ layout/
│  │  └─ DepocuLayout.jsx                     # FAZ 1 (dark + offline)
│  └─ depocu/
│     └─ ui/
│        ├─ Button.jsx
│        ├─ IconButton.jsx
│        ├─ InputField.jsx
│        ├─ ScanField.jsx
│        ├─ ScanMonolith.jsx
│        ├─ Sheet.jsx
│        ├─ Card.jsx
│        ├─ ListItem.jsx
│        ├─ StatusPill.jsx
│        ├─ StepIndicator.jsx
│        ├─ EmptyState.jsx
│        ├─ Toast.jsx
│        ├─ QuantityStepper.jsx
│        ├─ OfflineBadge.jsx
│        └─ index.js
├─ hooks/
│  ├─ useAutoRefocus.js                       # FAZ 1
│  ├─ useHapticFeedback.js                    # FAZ 1
│  └─ useOfflineQueue.js                      # FAZ 1 (placeholder)
└─ pages/depocu/
   ├─ DepocuAnaSayfasi.jsx                    # FAZ 2 (mevcut — uyarla)
   ├─ KabulSecimPage.jsx                      # FAZ 2 (mevcut — uyarla)
   ├─ DepocuProfilPage.jsx                    # FAZ 2
   ├─ DepocuUretimKabulPage.jsx               # FAZ 2
   ├─ DepocuStokSayimPage.jsx                 # FAZ 3
   ├─ DepocuIrsaliyelerPage.jsx               # FAZ 3
   ├─ DepocuDestekPage.jsx                    # FAZ 3
   ├─ DepocuSevkiyatlarPage.jsx               # FAZ 4
   ├─ DepocuStokHareketleriPage.jsx           # FAZ 4 (wizard)
   └─ DepocuMalKabulPage.jsx                  # FAZ 5 (4-adım wizard)
```

Ayrıca:
- `ReactProje/src/App.jsx` — depocu route'ları yeni bileşenlere bağlanır, mevcut redirect'ler korunur.
- `ReactProje/src/pages/terminal/*` — dark mod + ScanMonolith kullanımı (FAZ 5).

---

## 6. Faz Faz Uygulama Planı

### FAZ 1 — Design System Temeli *(Deploy: tokens + Layout güncellemesi canlıya; sayfalar henüz değişmedi)*

**Kapsam**
- In: Tailwind/Font yapılandırma, `depocu-tokens.css`, 15 UI bileşeni, 3 hook, `DepocuLayout` dark mod + OfflineBadge.
- Out: Sayfa yeniden yazımları, route değişiklikleri, form entegrasyonları.

**Action Items**
1. [ ] Manrope + JetBrains Mono'yu `index.html` veya Vite font yolu ile yükle (self-hosted woff2).
2. [ ] `tailwind.config.js`: `theme.extend` altına radius / spacing / fontFamily / ring tokenları ekle; `darkMode: 'class'` zorla.
3. [ ] `src/styles/depocu-tokens.css` oluştur (CSS vars light + `.dark` override) ve `main.jsx`'e import et.
4. [ ] `ThemeContext` — `depocu` rolü giriş yaptığında `document.documentElement.classList.add('dark')` default (kullanıcı toggle edebilir, tercih localStorage).
5. [ ] 15 UI bileşenini yaz (`components/depocu/ui/*`); her birine Storybook yerine `pages/depocu/_sandbox.jsx` demo rotası ekle (dev only).
6. [ ] 3 hook yaz: `useAutoRefocus`, `useHapticFeedback`, `useOfflineQueue` (placeholder).
7. [ ] `DepocuLayout.jsx` — dark mode sınıfları, header sağına `OfflineBadge` + tema toggle IconButton, safe-area korunur.
8. [ ] A11y baseline: kontrast testi (axe), focus ring görünürlüğü, `prefers-reduced-motion` davranışı.

**Teslim Kriterleri**
- Depocu girişinde tüm sayfalar dark modda açılır; layout bozulmaz.
- Sandbox rotasında 15 bileşen demo edilebilir.
- Lighthouse a11y ≥ 95 (sandbox).

---

### FAZ 2 — Basit Sayfalar + Ana Akış *(Deploy: Ana Sayfa, Kabul Seçim, Profil, Üretim Kabul canlı)*

**Kapsam**
- In: `DepocuAnaSayfasi` yenileme, `KabulSecimPage` yenileme, `DepocuProfilPage`, `DepocuUretimKabulPage` (Scan Monolith'in ilk gerçek kullanım yeri).
- Out: Kompleks wizard sayfaları.

**Action Items**
1. [ ] `DepocuAnaSayfasi` — yeni token + bileşenlere geçir; offline chip, ikon setini koru.
2. [ ] `KabulSecimPage` — `Card` bileşeniyle yeniden kur; emerald/amber accent bar.
3. [ ] `DepocuProfilPage` — 2 bölüm kartı; tıklamada `Sheet` (fullscreen snap-92) form; şifre değiştirme ayrı sheet.
4. [ ] `DepocuUretimKabulPage` — `ScanMonolith` + `useAutoRefocus` + `useHapticFeedback`; son 10 palet chip strip.
5. [ ] `App.jsx` — `/depocu/profil` → `DepocuProfilPage`, `/depocu/kabul/uretimden` → `DepocuUretimKabulPage` (feature flag korunur).
6. [ ] Gerçek cihazda smoke test (mümkünse Zebra emulator ya da 5" Android Chrome).

**Teslim Kriterleri**
- Üretim kabul ekranında 10 ardışık tarama (1sn arayla) kaybolmaz; her başarıda haptic + ses.
- Profil sheet klavye açıkken ekran kaymaz; safe-area ihlali yok.

---

### FAZ 3 — Orta Kompleks Sayfalar *(Deploy)*

**Kapsam**
- In: `DepocuStokSayimPage`, `DepocuIrsaliyelerPage`, `DepocuDestekPage`.
- Out: Wizard'lı sayfalar (Stok Hareketleri, Mal Kabul, Sevkiyatlar).

**Action Items**
1. [ ] `DepocuStokSayimPage` — ScanField h-20 + son taramalar liste + varyans bitir sheet; mevcut audio mantığını `useHapticFeedback`'e taşı.
2. [ ] `DepocuIrsaliyelerPage` — segment (Sevk/İade), kart liste, yeni = fullscreen sheet form (plaka ScanField).
3. [ ] `DepocuDestekPage` — segment (Açık/İşlemde/Çözüldü), kart liste, FAB → yeni talep sheet, detay → chat sheet.
4. [ ] `App.jsx` — `/depocu/stok-sayim`, `/depocu/irsaliyeler`, `/depocu/destek` yeni sayfalara yönlendir; eski route'ları `Navigate` ile taşı.
5. [ ] Empty / error / loading state'leri her 3 sayfada tutarlı `EmptyState` + skeleton pattern.

**Teslim Kriterleri**
- Stok sayımda 50 tarama sonrası liste virtualize'sız akıcı (<16ms frame).
- İrsaliyeler segment geçişleri 240ms slide, ara yok.

---

### FAZ 4 — Liste + İlk Wizard *(Deploy)*

**Kapsam**
- In: `DepocuSevkiyatlarPage` (swipe-list + sheet), `DepocuStokHareketleriPage` (3-adım wizard).
- Out: MalKabul wizard, terminal sayfaları.

**Action Items**
1. [ ] `ListItem` swipe-to-act primitifini pointer event'lerle yaz (Framer Motion drag + snap).
2. [ ] `DepocuSevkiyatlarPage` — segment + swipe-list + bottom-sheet detay (kargo atama, barkod yazdır).
3. [ ] `DepocuStokHareketleriPage` wizard: Adım 1 Palet, Adım 2 Miktar (QuantityStepper + parçalama toggle), Adım 3 Hedef Raf; "sepetim" sheet alta yapışır; son "Gönder" sticky.
4. [ ] Wizard state için lokal `useReducer` (21 useState yerine tek state makinesi).
5. [ ] Orijinal 1361 satırlık admin sayfasındaki palet sorgulama/parçalama API çağrılarını birebir koru.
6. [ ] `App.jsx` — `/depocu/sevkiyat`, `/depocu/stok` yeni sayfalara bağla.

**Teslim Kriterleri**
- Wizard 3 adım → başarılı gönderim akışı uçtan uca çalışır; back tuşu adım geri alır (history stack).
- Swipe eylem hatası durumunda snap-back 200ms içinde.

---

### FAZ 5 — Mal Kabul Wizard + Terminal Uyarlama *(Deploy)*

**Kapsam**
- In: `DepocuMalKabulPage` (4-adım wizard), `pages/terminal/*` dark mod + ScanMonolith.
- Out: Son cila.

**Action Items**
1. [ ] `DepocuMalKabulPage` 4 adım: Tedarikçi seç → Kalem ekle loop → Varyans → Onay. Kalemde inline `QuantityStepper`, swipe-sol sil.
2. [ ] İstisna/varyans akışını ayrı `Sheet`'e çıkar; numeric hassasiyet korunur.
3. [ ] `pages/terminal/YerlestirmePage` — 4 adım StepIndicator + ScanMonolith; override modal → `Sheet`.
4. [ ] `pages/terminal/GorevListesiPage` — pagination kaldır (scroll), dark mod, "Sıradaki Al" sticky.
5. [ ] `pages/terminal/TerminalOzetPage` — KPI display font; son tamamlananlar zaman çizelgesi.
6. [ ] `App.jsx` — `/depocu/kabul/irsaliyeli` → `DepocuMalKabulPage`; `/gelen-mal/irsaliyeli` admin sürümü bozulmaz.

**Teslim Kriterleri**
- 10 kalemli mal kabul 90sn içinde tamamlanır (senaryo testi).
- Terminal/Yerlestirme'de mevcut ZXing kamera + DataWedge akışı regresyonsuz.

---

### FAZ 6 — Test, Polish, A11y & Release *(Deploy: production)*

**Kapsam**
- In: Gerçek cihaz testleri, a11y denetimi, performance, dokümantasyon.
- Out: Yeni özellik.

**Action Items**
1. [ ] Zebra TC21/TC26 veya Honeywell CT40 cihazında 14 ekranın el gezisi; DataWedge profili doğrula.
2. [ ] Playwright mobil viewport (360×640, 412×915) smoke: login → 14 ekran → logout.
3. [ ] axe-core a11y raporu; her sayfa ≥ 95 skor, kontrast ihlali 0.
4. [ ] Lighthouse performance (throttled 4G) her sayfa ≥ 85.
5. [ ] `CLAUDE.md` ve `DOCS/` altında kısa kullanım kılavuzu (hangi sayfa ne yapar, klavye/scanner davranışları).
6. [ ] Release notu + ekran görüntüleri + önceki vs yeni kıyas.

**Teslim Kriterleri**
- Tüm kapsam sayfalarında a11y ≥ 95, performance ≥ 85.
- Saha kullanıcısı pilotu (min 1 gün, 1 operatör) regresyon bildirmez.

---

## 7. Risk & Varsayımlar

| Risk | Etki | Azaltma |
|---|---|---|
| Kod çoğaltma (admin vs depocu aynı endpoint) | Orta | Ortak `services/` katmanı zaten var; sadece sunum katmanı ayrılıyor. Business logic dokunulmaz. |
| Kullanıcı dark moddan hoşlanmazsa | Düşük | Light mod eşit kalitede; header'daki toggle ile hızlı geçiş. |
| Bottom-sheet kütüphane yok — el yapımı | Orta | Framer Motion drag + spring ile; tek dosya (`Sheet.jsx`); snap mantığı test edilir. |
| DataWedge klavye odağı kaybolması | Yüksek (saha) | `useAutoRefocus` tüm sayfalarda mount; sheet kapanışında re-focus. |
| 1361 satırlık StokHareketleri davranışının kaybolması | Yüksek | Wizard yazımında admin sayfası referans alınır; API çağrıları ve validasyon birebir. |

---

## 8. Açık Sorular

1. **Sesli geri bildirim sesi:** Jenerik beep mi, yoksa özel kısa wav dosyaları mı (success.wav / error.wav) servise eklensin?
- Jenerik beep.
2. **Offline kuyruk:** Bu fazda sadece görsel placeholder mı kalsın (kullanıcı onayı), yoksa FAZ 2'de gerçek `localStorage` kuyruğuna bağlanıp sunucu 503'te otomatik yeniden deneme mi yapılsın?
- 
3. **Tema tercihi:** Depocu ilk girişte **daima dark** mı açılsın, yoksa sistem `prefers-color-scheme`'i mi izlesin?
- prefers-color-scheme'i izlesin.

---

## 9. Referanslar

- Admin kaynak sayfalar: `ReactProje/src/pages/*.jsx`
- Mevcut layout: `ReactProje/src/components/layout/DepocuLayout.jsx`
- CLAUDE.md (proje kökü)
- Mimari geçmiş: `BackendProje/MIMARI_KONSOLIDASYON_PLANI.md`, `PLAN.md`
