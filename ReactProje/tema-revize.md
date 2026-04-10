# Tema Sistemi — Dark Mode Uyumluluk Revizyonu

## Analiz Raporu

### Kök Neden

Mevcut yaklaşımın 3 temel problemi var:

| Problem | Detay |
|---|---|
| **Hardcode renk hacmi** | 32 sayfa dosyasında **638** adet `bg-white/slate-50/100`, **818** adet `text-slate-[5-9]00`, **480** adet `border-slate-[12]00` → toplam ~1900+ sabit Tailwind sınıfı |
| **`dark:` kapsama eksikliği** | `dark:` sınıfı yalnızca 3 dosyada var (Header, DashboardLayout, AyarlarPage). Hiçbir page dosyası içermiyor |
| **`@variant dark` belirsizliği** | Tailwind v4'te `@variant dark (&:where([data-mode="koyu"] *))` sözdizimi doğru çalışmıyor olabilir — DevTools doğrulaması gerekiyor |

### Neden `dark:` ekleme yaklaşımı ölçeklenmez?
~1900 ayrı sınıfa tek tek `dark:` eklemek → her sayfa dosyasında 50-150 satır değişiklik → sürdürülemez ve PR review'da gürültülü.

### Doğru Mimari

**CSS Global Override Stratejisi:**
`[data-mode="koyu"]` ancestor selector + Tailwind sınıf adları → tek bir CSS bloğu 32 dosyayı aynı anda etkiler.

```css
/* Örnek — 1 kural 32 dosyadaki tüm bg-white'ları etkiler */
[data-mode="koyu"] .bg-white { background-color: #1e293b; }
```

CSS specificity: `[data-mode="koyu"] .bg-white` (0,1,1) > `.bg-white` (0,0,1) → `!important` gerekmez.

Kasıtlı istisnaları (beyaz rozet, renkli badge) `dark:bg-white` ile koruma altına alınır.

---

## Scope

**In:**
- `index.css`'e global `[data-mode="koyu"]` override bloğu (arka plan, metin, border, divider, input, ring)
- `@variant dark` sözdizimini Tailwind v4'e uygun doğrulama/düzeltme
- `LoginPage` dark uyumu (DashboardLayout dışında bağımsız sayfa)
- Modal/overlay backdrop'ları dark uyumu
- `DashboardPage` CSS-in-JS inline style'larını CSS token'larına bağlama

**Out:**
- Tema renk override'ları (mavi → teal vb.) — zaten çalışıyor, bu kapsam dışı
- Terminal ve Depocu layout'ları — ayrı iş kalemi
- Recharts grafik renklerinin dark uyumu — sonraki fazda

---

## Renk Eşleştirme Tablosu

| Tailwind Sınıfı (açık) | Dark Override Değeri | Token |
|---|---|---|
| `bg-white` | `#1e293b` | slate-800 |
| `bg-white/75` | `rgba(15,23,42,0.8)` | slate-900/80 |
| `bg-slate-50` | `#0f172a` | slate-950 |
| `bg-slate-50/50` | `rgba(15,23,42,0.5)` | |
| `bg-slate-100` | `#1e293b` | slate-800 |
| `bg-slate-200` | `#334155` | slate-700 |
| `text-slate-900` | `#f1f5f9` | slate-100 |
| `text-slate-800` | `#e2e8f0` | slate-200 |
| `text-slate-700` | `#cbd5e1` | slate-300 |
| `text-slate-600` | `#94a3b8` | slate-400 |
| `text-slate-500` | `#64748b` | slate-500 |
| `border-slate-200` | `#334155` | slate-700 |
| `border-slate-100` | `#1e293b` | slate-800 |
| `divide-slate-100` | `#1e293b` | |
| `divide-slate-200` | `#334155` | |
| `ring-slate-200` | `#334155` | |
| `placeholder-slate-400` | `#475569` | slate-600 |

### Korunacak (override yapılmayacak) sınıflar
- `bg-blue-*`, `bg-green-*`, `bg-red-*`, `bg-amber-*` → semantik renkler, doğru kalmalı
- `bg-white border-2 ...` aktif seçim halkaları → tema primary rengiyle zaten çalışıyor

---

## Action Items

- [ ] **1. `@variant dark` doğrula** — Tailwind v4'te `@custom-variant dark` vs `@variant dark` farkını test et; CSS çıktısında `[data-mode="koyu"] .dark\:bg-slate-900` gibi selector üretiliyor mu kontrol et. Gerekiyorsa sözdizimini düzelt.

- [ ] **2. `[data-mode="koyu"]` global override bloğu yaz** — `index.css`'e arka plan (bg-white/50/100), metin (text-slate-500/600/700/800/900), border (border-slate-100/200), divider, placeholder, ring için ~20 kural yaz. `@layer utilities` içinde değil, doğrudan root scope'ta yaz (specificity kontrolü için).

- [ ] **3. Input alanı dark override'ı** — `bg-slate-50 focus:bg-white` pattern'i projedeki en yaygın input stili. `[data-mode="koyu"] input, [data-mode="koyu"] select, [data-mode="koyu"] textarea` global kuralı yaz.

- [ ] **4. Modal/dialog backdrop fix** — Overlay'lerin `bg-white` içeren container'larına override uygulan (portal ile render edildiği için DashboardLayout scope'u dışına çıkabilir — `document.documentElement`'e attribute yazıldığı için sorun olmamalı, test et).

- [ ] **5. `LoginPage` dark uyumu** — Bağımsız sayfa, DashboardLayout dışında. Global override yeterli olacak; login kartının `bg-white` overflow sorunu varsa düzelt.

- [ ] **6. `DashboardPage` inline style fix** — CSS-in-JS `injectStyles()` bloğundaki hardcode `#fff`, `#f8fafc` gibi değerleri CSS variable referanslarına (`var(--color-surface)`) bağla veya `[data-mode="koyu"]` context'e ayrı kural ekle.

- [ ] **7. Scrollbar + skeleton dark** — `index.css`'teki scrollbar thumb rengi (`#cbd5e1`) ve skeleton gradient dark modda kaynaşıyor; override ekle.

- [ ] **8. Validation** — 4 kritik sayfa × 4 tema × 2 mod = 32 kombinasyonu gözle kontrol et: UrunlerPage, StokHareketleriPage, DashboardPage, AyarlarPage.

---

## Dosya Listesi

| Dosya | Değişiklik |
|---|---|
| `src/index.css` | Global `[data-mode="koyu"]` override bloğu (~30 kural), `@variant dark` düzeltmesi, scrollbar dark, skeleton dark |
| `src/pages/DashboardPage.jsx` | `injectStyles()` CSS-in-JS bloğundaki hardcode renkler |
| `src/pages/LoginPage.jsx` | Gerekirse bireysel dark class'lar |
| Diğer 30 sayfa | **Değişiklik gerekmez** — global override yeterli |

---

## Validation

- [ ] `[data-mode="koyu"]` attribute'u `<html>`'de set edildiğinde UrunlerPage kartları karardı mı?
- [ ] Input alanları `bg-slate-50` → dark background'a geçti mi?
- [ ] Login sayfası dark'ta okunabilir mi?
- [ ] Renkli badge'ler (success, danger, warning) bozulmadı mı?
- [ ] Tailwind `dark:` sınıfları (Header'da yazılmış olanlar) gerçekten çalışıyor mu?
- [ ] 4 tema × koyu mod kombinasyonunda sidebar renkleri doğru mu?
