# Üretim Paleti Saha Akışı — Pratik Redesign

Üretimden gelen paletin "etiket okut → kabul et → rafa yerleştir" akışını saha gerçekliğine uygun, 2-taramalık pratik bir iş akışına dönüştürme planı.

---

## 1. Sorun: Mevcut Akış Saha İçin Kullanılamaz

### Mevcut Akış (5 adım, 2 sayfa)

```
① UretimPaletleriPage → "Yeni Palet" modalı (form doldur) → OLUSTURULDU
② UretimPaletleriPage → "Kabul Bekle" butonu → KABUL_BEKLIYOR
③ UretimPaletiKabulPage → barkod okut → KABUL_EDILDI
④ UretimPaletleriPage → "Yerleştirme Bekle" butonu → YERLESTIRME_BEKLIYOR
⑤ UretimPaletleriPage → raf seç + "Yerleştir" → YERLESTIRILDI
```

### Saha Gerçekliği (2 tarama)

```
① Palet etiketini okut → KABUL EDILDI + yerleştirme görevi oluştu
② Raf barkodunu okut → YERLESTIRILDI
```

### Kopukluklar

| # | Sorun | Neden |
|---|-------|-------|
| 1 | Etiket okutulduğunda palet sistemde yoksa ne olacak? | ERP entegrasyonu yok; paleti uygulama içinden oluşturman gerekiyor |
| 2 | KABUL_BEKLIYOR durumu sahada anlamsız | ERP'den bildirim gelmiyor; depocu paleti fiziksel görüyor |
| 3 | Kabul sonrası yerleştirme ayrı sayfada | Depocu kabul ettiği paleti hemen rafa götürüyor, arada sayfa değiştiremez |
| 4 | Yerleştirme için raf seçimi dropdown | Saha terminalde dropdown değil barkod okutma ile yapılır |

---

## 2. Hedef Akış: 2-Tarama Modeli

### Akış Şeması

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SAHA AKIŞI (2 TARAMA)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HAZIRLIK (Admin/Depocu — ofisten 1 kez)                           │
│  ┌──────────────────────────────────────────────┐                   │
│  │ ① Palet oluştur (form) → OLUSTURULDU       │                   │
│  │ ② Etiket yazdır / oluştur                   │                   │
│  │ ③ Etiketi fiziksel palete yapıştır          │                   │
│  └──────────────────────────────────────────────┘                   │
│                         │                                           │
│                         ▼                                           │
│  SAHA (Depocu — el terminalinde)                                   │
│  ┌──────────────────────────────────────────────┐                   │
│  │ ④ Palet etiketini okut                       │                   │
│  │    → Otomatik: OLUSTURULDU → KABUL_EDILDI    │                   │
│  │    → Stok GIRIS hareketi yazılır             │                   │
│  │    → Yerleştirme görevi oluşur               │                   │
│  │    → Durum: YERLESTIRME_BEKLIYOR             │                   │
│  └──────────────────────────────────────────────┘                   │
│                         │                                           │
│                         ▼                                           │
│  ┌──────────────────────────────────────────────┐                   │
│  │ ⑤ Raf barkodunu okut                         │                   │
│  │    → Otomatik: YERLESTIRME_BEKLIYOR →        │                   │
│  │      YERLESTIRILDI                           │                   │
│  │    → Raf kapasite kontrolü                   │                   │
│  │    → Palet rafa atanır                       │                   │
│  └──────────────────────────────────────────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Basitleştirilmiş State Machine

```
Mevcut (7 durum, 5 adım):          Hedef (5 durum, 2 adım):
                                    
OLUSTURULDU                        OLUSTURULDU (hazırlık)
    ↓                                  ↓ (barkod okutma)
KABUL_BEKLIYOR ← KALDIR             KABUL_EDILDI + YERLESTIRME_BEKLIYOR
    ↓                                  ↓ (raf barkod okutma)
KABUL_EDILDI                        YERLESTIRILDI
    ↓
YERLESTIRME_BEKLIYOR
    ↓
YERLESTIRILDI

+ KARANTINA (ayrı kalite akışı — dokunulmaz)
+ IPTAL_EDILDI (admin — dokunulmaz)
```

**Kaldırılan:** `KABUL_BEKLIYOR` durumu ve `kabul-bekle` endpoint'i sahada kullanılmayacak.
**Birleştirilen:** Barkod okutma ile `OLUSTURULDU → KABUL_EDILDI → YERLESTIRME_BEKLIYOR` tek adımda.

---

## 3. Değişiklik Planı

### 3.1. Backend Değişiklikleri

#### A. Yeni Use Case: `UretimPaletiHizliKabulUseCase`

**Mevcut `kabul-et` endpoint'ini genişlet:** Sadece `KABUL_BEKLIYOR` değil, `OLUSTURULDU` durumundan da kabul edebilsin.

| Dosya | Değişiklik |
|-------|------------|
| `palet.py` state machine | `OLUSTURULDU → KABUL_EDILDI` geçişi ekle |
| `palet.py` entity | `kabul_et()` metodunun `OLUSTURULDU`'dan da çalışmasına izin ver |
| `uretim_palet_service.py` | `kabul_et()` — OLUSTURULDU durumunu da kabul etsin |
| `uretim_paleti_use_cases.py` | `UretimPaletiKabulEtUseCase` — OLUSTURULDU durumunu da işlesin; kabul sonrası otomatik `YERLESTIRME_BEKLIYOR`'a geçirsin |

**İş mantığı:** Barkod okutulduğunda:
1. Palet `OLUSTURULDU` ise → `KABUL_EDILDI` (stok GIRIS) → `YERLESTIRME_BEKLIYOR` (otomatik)
2. Palet `KABUL_BEKLIYOR` ise → `KABUL_EDILDI` (stok GIRIS) → `YERLESTIRME_BEKLIYOR` (otomatik)
3. Palet `KABUL_EDILDI` veya sonrası ise → hata ("zaten kabul edilmiş")

#### B. Yeni Endpoint: `POST /{palet_no}/yerlestir-barkod`

Saha terminalde dropdown yerine raf barkod okutma ile yerleştirme.

| Dosya | Değişiklik |
|-------|------------|
| `uretim_paletleri.py` router | Yeni endpoint: raf_barkod (string) alır, raf_id'ye resolve eder |
| `uretim_paleti_use_cases.py` | `UretimPaletiYerlestirUseCase` — raf_barkod ile raf bulma eklenebilir veya mevcut `yerlestir` endpoint'ine raf_barkod parametresi eklenebilir |

**Alternatif (daha basit):** Mevcut `yerlestir` endpoint'i `raf_id` alıyor. Frontend raf_barkod → raf_id resolve işini yapabilir. Backend değişmez.

#### C. Raf Kapasite Kontrolü (Yerleştirme)

| Dosya | Değişiklik |
|-------|------------|
| `uretim_paleti_use_cases.py` | `UretimPaletiYerlestirUseCase.execute()` — hedef rafın `kapasite_yeterli_mi()` kontrolü ekle; yetersiz ise `GecersizIslemError` |

### 3.2. Frontend Değişiklikleri

#### A. `UretimPaletiKabulPage` → 2-adımlı akış

Mevcut sayfa sadece "kabul et" yapıyor. Yerleştirme adımını da aynı sayfaya ekleyeceğiz.

**Mevcut UX:**
```
Barkod okut → "Kabul edildi — X koli" → BİTTİ (sonra ne?)
```

**Hedef UX:**
```
① Palet barkod okut → "Kabul edildi — X koli — Şimdi raf barkodunu okutun"
② Raf barkod okut → "Yerleştirildi — Raf A-01-02-03"
③ Otomatik sıfırla → sıradaki paleti bekler
```

**Sayfa yapısı:**
- Tek input alanı, ama durum bazlı farklı placeholder
- Durum 1 (palet bekliyor): "Palet barkodunu okutun..."
- Durum 2 (raf bekliyor): "Raf barkodunu okutun..." (yeşil vurgu)
- Sonuç kartı: kabul + yerleştirme bilgisi birlikte
- Geçmiş listesi: her satırda palet no + raf kodu

#### B. `UretimPaletleriPage` — "Kabul Bekle" butonu kaldır

`OLUSTURULDU` durumundaki palet için "Kabul Bekle" butonu yerine doğrudan "Kabul Et" butonu gösterilecek. Saha akışında bu sayfa yönetim/raporlama amaçlı; saha operasyonu `UretimPaletiKabulPage` üzerinden.

### 3.3. Kapsam Dışı (Yapılmayacak)

| Özellik | Neden |
|---------|-------|
| QC_ONAYLANDI / QC_REDDEDILDI durumları | Şu an sahada kalite departmanı akışı yok; KARANTINA yeterli |
| Putaway öneri servisi | Over-engineering; depocu rafı biliyor |
| Ürün bazlı QC zorunluluğu | ERP yok, ürün master'da bu alan yok |
| Tartım doğrulama | Sahada tartım yapılmıyor |
| SKT kontrolü | Lot oluşturulurken zaten kontrol ediliyor |
| ERP entegrasyonu | Bağımsız sistem |

---

## 4. Action Items

### Adım 1: State Machine genişletme (Backend)
- [ ] `palet.py`: `OLUSTURULDU → KABUL_EDILDI` geçişi ekle
- [ ] `palet.py`: `kabul_et()` metodunun OLUSTURULDU'dan da çalışmasını sağla
- [ ] `uretim_palet_service.py`: `kabul_et()` — OLUSTURULDU'yu da kabul etsin

### Adım 2: Kabul → Yerleştirme otomatik bağlantı (Backend)
- [ ] `UretimPaletiKabulEtUseCase`: kabul sonrası otomatik `yerlestirme_bekle()` çağrısı ekle
- [ ] Kabul sonucu response'a `yerlestirme_bekliyor: true` bilgisi ekle

### Adım 3: Raf kapasite kontrolü (Backend)
- [ ] `UretimPaletiYerlestirUseCase`: hedef raf `kapasite_yeterli_mi()` kontrolü

### Adım 4: Frontend — 2-adımlı kabul sayfası
- [ ] `UretimPaletiKabulPage`: 2-fazlı akış (palet okut → raf okut)
- [ ] Durum bazlı input placeholder ve renk değişimi
- [ ] Sonuç kartında kabul + yerleştirme bilgisi
- [ ] Geçmiş listesinde palet + raf bilgisi

### Adım 5: Frontend — Yönetim sayfası güncelleme
- [ ] `UretimPaletleriPage`: OLUSTURULDU durumunda "Kabul Et" butonu göster (Kabul Bekle yerine)
- [ ] `UretimPaletleriPage`: KABUL_EDILDI durumunda "Yerleştir" butonu göster (Yerleştirme Bekle yerine)

### Adım 6: Test
- [ ] Backend test: OLUSTURULDU → KABUL_EDILDI → YERLESTIRME_BEKLIYOR akışı
- [ ] Backend test: Raf kapasite aşımı senaryosu
- [ ] Frontend smoke: 2-tarama akışı uçtan uca

---

## 5. Mevcut Akış vs Hedef Akış Karşılaştırması

| Ölçüt | Mevcut | Hedef |
|-------|--------|-------|
| Palet kabul adım sayısı | 3 (oluştur + kabul bekle + kabul et) | 2 (oluştur + barkod okut) |
| Yerleştirme adım sayısı | 2 (bekle + yerleştir) | 1 (raf barkod okut) |
| Toplam saha tıklama/tarama | 5+ | 2 |
| Sayfa geçişi | 2 sayfa | 1 sayfa |
| ERP bağımlılığı | KABUL_BEKLIYOR varsayıyor | Yok |
| Saha kullanılabilirlik | Kullanılamaz | Kullanılabilir |
