# Tema Sistemi Uygulama Planı

## Yaklaşım

**Tema (renk kimliği)** ve **Mod (açık/koyu/sistem)** ayrı boyutlar olarak yönetilir.
`<html>` elementine `data-theme` ve `data-mode` attribute'ları yazılır; tüm UI bu CSS
custom property'leri okur. Böylece 4 tema × 3 mod = 12 kombinasyon CSS seviyesinde
çalışır, JavaScript sadece state yönetir.

---

## Scope

**In:**
- 4 tema: `kurumsal` (mavi/lacivert), `ocean` (teal/cyan), `indigo` (indigo/violet), `emerald` (yeşil)
- 3 mod: `acik`, `koyu`, `sistem` (prefers-color-scheme)
- `ThemeContext` — tema + mod state, localStorage kalıcılığı, sistem tercihini dinleme
- Header'da mod toggle butonu (Sun ↔ Moon) — her temada görünür
- `AyarlarPage` → "Arayüz ve Görünüm" bölümüne tema kartları + mod seçici
- Geçiş animasyonu (`transition: color, background-color 200ms`)

**Out:**
- Backend'e tema kaydı (localStorage yeterli, user-specific olması bu fazda kapsam dışı)
- Terminal ve Depocu layout'larının tam dark adaptasyonu (ayrı iş)
- Font ve dil değiştirme (ayrı iş)

---

## Mimari Detaylar

### CSS Katmanı — `index.css`

```
[data-theme="kurumsal"]          → mevcut mavi/lacivert palette (zaten default)
[data-theme="ocean"]             → --color-primary-* teal/cyan tonları
[data-theme="indigo"]            → --color-primary-* indigo/violet tonları
[data-theme="emerald"]           → --color-primary-* yeşil/emerald tonları

[data-mode="koyu"]               → surface, border, text token'larını dark değerlere override eder
[data-theme="X"][data-mode="koyu"] → gerekirse tema-spesifik dark tweakler
```

Her tema, yalnızca `--color-primary-*` ve `--color-accent-*` token'larını override eder.
`--color-surface`, `--color-text-*`, `--color-sidebar-*` token'ları mod tarafından yönetilir.

### `ThemeContext` — `src/contexts/ThemeContext.jsx`

```js
{
  tema,          // "kurumsal" | "ocean" | "indigo" | "emerald"
  mod,           // "acik" | "koyu" | "sistem"
  resolvedMod,   // "acik" | "koyu" — sistem seçiliyse MediaQuery'den resolve edilir
  setTema(t),
  setMod(m),
  toggleMod(),   // acik ↔ koyu (sistem modundaysa override eder)
}
```

- `localStorage` anahtarları: `depo_tema`, `depo_mod`
- `sistem` modunda `window.matchMedia('(prefers-color-scheme: dark)')` listener'ı aktif
- `useEffect` içinde `document.documentElement.setAttribute('data-theme', tema)` ve `setAttribute('data-mode', resolvedMod)` çağrısı

### Header Mod Toggle Butonu

- Her zaman görünür (tüm temalarda)
- `resolvedMod === 'acik'` → Moon ikonu, tooltip "Koyu Moda Geç"
- `resolvedMod === 'koyu'` → Sun ikonu, tooltip "Açık Moda Geç"
- `mod === 'sistem'` durumdayken tıklanırsa: sistem modunu kırarak explicit `acik`/`koyu` set eder
- Bildirim badge gibi küçük bir "S" göstergesi ile sistem modunda olduğunu belirtir (opsiyonel ama profesyonel)

### `AyarlarPage` — "Arayüz ve Görünüm" Bölümü

**Tema Seçici** — 4 kart, her birinde:
- Renk swatch (primary + surface önizleme)
- Tema adı
- Aktif olanın üzerinde checkmark + ring

**Mod Seçici** — 3 buton grubu (segmented control):
- ☀️ Açık | 🌙 Koyu | 💻 Sistemle Eşleştir

---

## Tema Renk Tanımları

### `kurumsal` (mevcut default — değiştirilmez)
- Primary: Blue `#2563eb` / `#1d4ed8`
- Accent: Amber `#f59e0b`

### `ocean`
- Primary-500: `#0891b2` (Cyan-600)
- Primary-600: `#0e7490`
- Primary-700: `#155e75`
- Primary-900: `#164e63`
- Accent: Teal `#14b8a6`
- Sidebar-bg: `#0c2d3a`

### `indigo`
- Primary-500: `#6366f1` (Indigo-500)
- Primary-600: `#4f46e5`
- Primary-700: `#4338ca`
- Primary-900: `#312e81`
- Accent: Violet `#8b5cf6`
- Sidebar-bg: `#1e1b4b`

### `emerald`
- Primary-500: `#10b981` (Emerald-500)
- Primary-600: `#059669`
- Primary-700: `#047857`
- Primary-900: `#064e3b`
- Accent: Green `#22c55e`
- Sidebar-bg: `#022c22`

### Dark Mod Token Override'ları (tüm temalar için ortak)
```css
[data-mode="koyu"] {
  --color-surface:           #0f172a;
  --color-surface-secondary: #1e293b;
  --color-surface-tertiary:  #334155;
  --color-border:            #334155;
  --color-border-light:      #1e293b;
  --color-text-primary:      #f1f5f9;
  --color-text-secondary:    #94a3b8;
  --color-text-tertiary:     #64748b;
  --color-sidebar-bg:        #020617;
  --color-sidebar-hover:     #0f172a;
}
```

---

## Action Items

- [ ] **1. CSS token katmanı** — `index.css`'e 4 tema × açık/koyu CSS custom property bloklarını yaz
- [ ] **2. ThemeContext oluştur** — `src/contexts/ThemeContext.jsx` yaz; localStorage + sistem MediaQuery desteği
- [ ] **3. ThemeProvider'ı App'e bağla** — `App.jsx`'te `AuthProvider` ile birlikte wrap et
- [ ] **4. Header mod toggle butonu** — `Header.jsx`'e Sun/Moon butonu ekle; `useTheme()` hook'u kullan
- [ ] **5. AyarlarPage güncelle** — "Arayüz ve Görünüm" bölümüne tema kartları + mod segmented control yaz
- [ ] **6. Geçiş animasyonu** — `body` veya `html`'e `transition` ekle (color, background-color, border-color 200ms)
- [ ] **7. Bileşen doğrulama** — Header, Sidebar, DashboardLayout'u 4 tema × 2 mod'da gözle kontrol et
- [ ] **8. Edge case** — `sistem` modunda sayfa yükleme anında flash (FOUC) önleme: `main.jsx`'te inline script ile erken attribute set etme

---

## Dosya Listesi (Değişecek / Oluşacak)

| Dosya | İşlem |
|---|---|
| `src/index.css` | Tema + dark token blokları eklenir |
| `src/contexts/ThemeContext.jsx` | **Yeni oluşturulur** |
| `src/App.jsx` | ThemeProvider wrap eklenir |
| `src/components/layout/Header.jsx` | Mod toggle butonu eklenir |
| `src/pages/AyarlarPage.jsx` | Tema/mod seçici UI eklenir |
| `src/main.jsx` | FOUC önleme inline script |

---

## Validation

- [ ] 4 tema × Açık/Koyu mod = 8 kombinasyonu tarayıcıda gözle doğrula
- [ ] Sayfa yenileme sonrası localStorage'dan doğru tema/mod geri yükleniyor mu?
- [ ] `sistem` modunda OS dark mode toggle edilince UI otomatik geçiyor mu?
- [ ] Header'daki toggle `sistem` modunu override ediyor mu?
- [ ] FOUC (flash of unstyled content) yok mu?

---

## Açık Notlar

- Tailwind v4 `@theme` bloğu **build-time** token'lar içindir; runtime override için `[data-*]` attribute
  selector'ları kullanılır — bu plan bu ayrımı doğru şekilde uygular.
- Tema token'larının renkleri başlangıç değerleridir; görsel revizyon ayrı bir adımda yapılacak.
- Terminal ve Depocu layout'larının dark uyumu ayrı iş kalemi olarak kapsam dışıdır.
