# Tema Renk Uyumu — Analiz & Uygulama Planı

## Analiz Raporu

### Kök Neden

CSS custom property (`--color-primary-*`) değişkenleri tema değişiminde doğru güncelleniyor.  
Sorun: bileşenler bu değişkenleri **okumaz** — hardcode Tailwind renk sınıfları kullanır.

| Metrik | Sayı | Dosya |
|---|---|---|
| `blue-*` sınıfları (base) | **349** | 32 |
| `blue-*` opacity varyantları (`/10`, `/20`…) | **85** | 23 |
| `indigo-*` sınıfları | **117** | 19 |
| Gradient sınıfları (`from-blue-`, `to-blue-`…) | **35** | 14 |
| **Toplam** | **~586** | **32** |

Tema "Ocean"a geçildiğinde `--color-primary-500` = `#06b6d4` oluyor.  
Ama `bg-blue-500` → Tailwind'in `rgb(59 130 246)` = sabit mavi kalıyor. Bağlantı yok.

---

### Neden `dark:` ekleme yaklaşımı BURADA da işe yaramaz?
586 sınıf, 32 dosya — `dark:` gibi `theme-ocean:` prefix'i Tailwind'de yoktur.

---

### Doğru Çözüm: CSS @layer Cascade Override (Sıfır Dosya Değişikliği)

Tailwind v4, kendi utility sınıflarını `@layer utilities` içine yazar.  
`@layer` dışında tanımlanan CSS kuralları **her zaman** `@layer utilities` kurallarını yener —  
specificity fark etmeksizin (CSS Cascade Level 5 kuralı).

```css
/* index.css — @layer dışında */
.bg-blue-500 { background-color: var(--color-primary-500); }
```

Bu tek kural, `bg-blue-500` kullanan tüm 32 dosyayı etkiler.  
`--color-primary-500` tema değişince otomatik güncellenir.

---

## Kapsam Haritası

### Renk Ailesi → Primary Token Eşleştirmesi

| Tailwind Ailesi | CSS Token |
|---|---|
| `blue-50`…`blue-950` | `--color-primary-50`…`--color-primary-950` |
| `indigo-50`…`indigo-950` | `--color-primary-50`…`--color-primary-950` |

> **Neden indigo da?** — Uygulama Ayarlar, ProfilAyarları, Header gibi bileşenlerde `indigo-*` kullanılan alanlar da tema primary rengiyle boyandığında tutarlılık sağlanır. Bağımsız semantik anlamı olmayan her `indigo-*` kullanımı primary'e bağlanmalı.

### Korunacaklar (override yapılmayacak)

| Renk | Neden |
|---|---|
| `sky-*` | Sidebar aktif göstergesi — kasıtlı farklı ton |
| `emerald-*`, `green-*` | Başarı/aktif semantik renk |
| `red-*`, `rose-*` | Tehlike/hata semantik renk |
| `amber-*`, `orange-*` | Uyarı semantik renk |
| `slate-*`, `gray-*` | Nötr yüzey/metin (dark mode kapsamında) |

---

## Kapsanacak Property × Varyant Matrisi

```
Properties : bg-, text-, border-, ring-, from-, to-, via-, shadow-
States     : base, hover:, focus:, active:, group-hover:, group-focus-within:
Opacity    : /5, /10, /15, /20, /25, /30, /40, /50, /60, /70, /75, /80
Shades     : 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950
```

Toplam kural sayısı tahmini: **~120 CSS satırı** — sıfır bileşen dosyası değişikliği.

---

## Teknik Detay: Opacity Varyantları

Tailwind v4'te `bg-blue-500/10` şu CSS'i üretir:
```css
.bg-blue-500\/10 {
  background-color: color-mix(in oklab, #3b82f6 10%, transparent);
}
```

Override:
```css
.bg-blue-500\/10 {
  background-color: color-mix(in oklab, var(--color-primary-500) 10%, transparent);
}
```

CSS değişkeni `color-mix()` içinde geçerlidir — modern tarayıcıların tamamı destekler.

---

## Özel Durum: `focus:ring-blue-500/10`

Tailwind v4'te `ring` utility, `--tw-ring-color` CSS değişkenini kullanır.  
Override:
```css
.focus\:ring-blue-500\/10:focus {
  --tw-ring-color: color-mix(in oklab, var(--color-primary-500) 10%, transparent);
}
```

---

## Action Items

- [ ] **1. Shade listesi ve opacity setini doğrula** — Projede kullanılan tüm `blue-*` shade ve opacity kombinasyonlarını çıkar (`50..950`, `/5../80`). Gereksiz şadeleri override listesine ekleme.

- [ ] **2. `bg-blue-*` → `var(--color-primary-*)` override bloğu yaz** — `index.css`'e, tüm shade seviyelerini kapsar (base + hover: + focus: + active: + group-hover:).

- [ ] **3. `bg-blue-*/opacity` varyantlarını yaz** — `color-mix()` ile opacity'li versiyonlar (`/5` → `/80`).

- [ ] **4. `text-blue-*` override bloğu yaz** — Tüm shade + state varyantları.

- [ ] **5. `border-blue-*` ve `ring-blue-*` override bloğu yaz** — focus:border-, hover:border-, focus:ring- dahil.

- [ ] **6. Gradient token'ları yaz** — `from-blue-*`, `to-blue-*`, `via-blue-*` sınıfları `--tw-gradient-*` değişkenlerini override eder.

- [ ] **7. `indigo-*` sınıflarını aynı şekilde primary'e bağla** — `bg-indigo-*`, `text-indigo-*`, `border-indigo-*`.

- [ ] **8. Sidebar `sky-*` istisnasını koru** — Override bloğuna `sky-*` eklenmeyecek şekilde koru.

- [ ] **9. Validation** — 4 tema × UrunlerPage, Header, AyarlarPage, DashboardPage üzerinde renk geçişini gözle doğrula.

---

## Dosya Listesi

| Dosya | Değişiklik |
|---|---|
| `src/index.css` | **~120 satır CSS override** — başka hiçbir dosya değişmez |

---

## Validation

- [ ] Ocean temasında `focus:border-blue-500` → teal border oluyor mu?
- [ ] Indigo temasında `bg-blue-50` arka plan → indigo/violet tonu oluyor mu?
- [ ] Emerald temasında buton hover (`hover:bg-blue-500`) → yeşil oluyor mu?
- [ ] Kurumsal temada geri dönünce her şey orijinal maviye döndü mü?
- [ ] `sky-*` (sidebar aktif rengi) değişmeden kaldı mı?
- [ ] Semantik renkler (`text-red-600`, `bg-green-100`) etkilenmedi mi?
