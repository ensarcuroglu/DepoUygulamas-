# Stok İşlemleri Revizyon Planı — Palet Numarası Bazlı Giriş/Çıkış

> **Durum:** Faz 1a–1e Tamamlandı | **Tarih:** 2026-03-27 | **Yöntem:** Brainstorming → Tasarım → Fazlı Uygulama

---

## 1. Amaç

Stok İşlemleri sayfasını ürün bazlı akıştan **palet numarası bazlı** akışa dönüştürmek. Kullanıcı yalnızca palet numarası girer; ürün, lot, miktar, lokasyon ve durum bilgileri otomatik getirilir. Sistem, ERP entegrasyonuna hazır bir mimari ile geliştirilir.

## 2. Kapsam

### Dahil
- Palet numarası bazlı stok giriş ve çıkış
- Mal Kabul İrsaliyesi modülü (yeni)
- ERP-ready soyutlama katmanı
- Rol bazlı depo erişim kontrolü
- Tam ve kısmi palet çıkışı
- Manuel + fiziksel okuyucu + kamera ile palet no girişi

### Hariç (Faz 2+)
- Toplu palet işlemi (çoklu tarama)
- ERP API entegrasyonu
- Mevcut sevkiyat FIFO akışı değişikliği

---

## 3. Mimari Kararlar

| # | Karar | Alternatifler | Neden |
|---|---|---|---|
| K1 | ERP = source of truth, WMS API-ready interface | WMS kendi palet üretir | Veri tutarlılığı, ERP entegrasyonuna hazırlık |
| K2 | Geçiş döneminde İrsaliye bazlı palet tanımlama | Palet Yönetimi'nden ön-tanım, Stok Giriş'te doğrudan oluşturma | ERP geçişinde sadece adapter swap yeterli |
| K3 | Ayrı MalKabulIrsaliyesi entity (ortak base değil) | Mevcut İrsaliye'ye tür ekleme | Farklı iş kuralları, Single Responsibility |
| K4 | Tam + kısmi çıkış desteklenir | Sadece tam çıkış, sadece FIFO | Operasyonel esneklik |
| K5 | Faz 1 tekli palet, Faz 2 toplu palet | Baştan toplu | Kontrollü geliştirme süreci |
| K6 | Rol bazlı depo kısıtlaması | Sert engel, uyarı+onay, kısıtsız | Güvenlik + admin esnekliği |
| K7 | Manuel + fiziksel okuyucu + kamera | Sadece barkod okuyucu | Farklı depo koşullarına uyum |
| K8 | Adapter Pattern + Domain Service mimarisi | Use case genişletme, event-driven | Clean Architecture uyumu, ERP-ready, SRP |

---

## 4. Mevcut Durum → Hedef Durum

### Mevcut Akış
```
Tip Seç → Ürün Ara/Seç → Miktar Gir → Onayla
```
- Giriş: Otomatik lot + otomatik palet (OTM-<uuid>) oluşturulur
- Çıkış: Ürüne ait tüm aktif paletlerden FIFO ile düşülür

### Hedef Akış
```
Tip Seç → Palet No Gir/Tara → Bilgi Önizleme → Onayla
```
- Giriş: Mal Kabul İrsaliyesi'ndeki palet referans alınır, lot+palet oluşturulur
- Çıkış: Belirli paletten tam veya kısmi çıkış yapılır

---

## 5. Teknik Tasarım

### 5.1 Yeni Entity'ler

#### MalKabulIrsaliyesi
```
MalKabulIrsaliyesi
├── id
├── irsaliye_no          (unique, MKI-YYYY-NNNNN)
├── tedarikci_id         (FK → Tedarikci)
├── depo_id              (FK → Depo)
├── tir_plaka            (opsiyonel)
├── sofor_adi            (opsiyonel)
├── durum                (Taslak → Onaylandi → Tamamlandi)
├── tarih
├── olusturma_tarihi
├── guncelleme_tarihi
└── kalemler[]           (1:N → MalKabulKalemi)
```

#### MalKabulKalemi
```
MalKabulKalemi
├── id
├── mal_kabul_irsaliyesi_id  (FK)
├── palet_no                  (unique, PLT-YYYY-XXXXX)
├── urun_id                   (FK → Urun)
├── lot_no                    (lot tanımlama)
├── miktar                    (koli adedi)
├── raf_id                    (FK → Raf, opsiyonel)
├── durum                     (Bekliyor → GirisYapildi)
├── uretim_tarihi             (opsiyonel)
├── son_kullanma_tarihi       (opsiyonel)
├── olusturma_tarihi
```

### 5.2 Soyutlama Katmanı (ERP-Ready)

```python
class IPaletVeriKaynagiService(ABC):
    """Palet bilgi kaynağı soyutlaması.

    Geçiş dönemi: IrsaliyePaletVeriKaynagiService → MalKabulKalemi'nden okur
    Hedef:        ErpPaletVeriKaynagiService → ERP API'den okur
    """

    @abstractmethod
    def palet_bilgisi_getir(self, palet_no: str) -> PaletBilgiDTO:
        """Palet numarasına göre tüm bilgileri getirir."""
        ...

    @abstractmethod
    def palet_giris_onayla(self, palet_no: str) -> None:
        """Palet girişi yapıldığını kaynağa bildirir."""
        ...
```

### 5.3 Domain Service

```
PaletBazliStokDomainService
│
├── palet_giris(palet_no, kullanici_id)
│   1. IPaletVeriKaynagiService → palet bilgisi getir
│   2. Depo yetki kontrolü (kullanıcı ↔ palet.depo)
│   3. Palet zaten sistemde mi? (çift giriş engeli)
│   4. Lot bul/oluştur
│   5. Palet oluştur (koli_adedi, raf_id)
│   6. StokHareketi kaydı yaz
│   7. MalKabulKalemi.durum → GirisYapildi
│   8. SistemLog yaz
│
├── palet_cikis(palet_no, miktar, kullanici_id, siparis_no?, aciklama?)
│   1. Palet bul (palet_no ile DB'den)
│   2. Palet aktif mi? Boş mu? kontrolü
│   3. Depo yetki kontrolü
│   4. miktar == null → tam çıkış (palet.sevk_et)
│   5. miktar < koli_adedi → kısmi çıkış (palet.stok_dus)
│   6. StokHareketi kaydı yaz
│   7. SistemLog yaz
│
└── palet_sorgula(palet_no)
    → PaletBilgiDTO döner (ürün, lot, miktar, lokasyon, durum)
```

### 5.4 Mevcut Yapıya Etki Analizi

| Bileşen | Değişiklik |
|---|---|
| `StokHareketiOlusturUseCase` | **Dokunulmaz** — sevkiyat FIFO akışı aynen kullanır |
| `StokHareketi` entity | Değişiklik yok — `palet_id` zaten mevcut |
| `Palet` entity | Değişiklik yok — `stok_dus()` ve `sevk_et()` zaten mevcut |
| `Kullanici` entity | `depo_id` alanı eklenir (atanmış depo) |
| Sevkiyat modülü | **Dokunulmaz** — kendi FIFO akışını kullanmaya devam eder |
| Mevcut `POST /api/stok-hareketleri/` | **Korunur** — eski akış ve sevkiyat kullanmaya devam eder |

---

## 6. API Tasarımı

### 6.1 Yeni Endpoint'ler

```
# Palet Sorgulama (giriş/çıkış öncesi bilgi getirme)
GET  /api/stok-islemleri/palet/{palet_no}
→ PaletBilgiResponseDTO

# Palet Bazlı Giriş
POST /api/stok-islemleri/palet-giris
Body: { palet_no: str }
→ StokHareketiResponseDTO

# Palet Bazlı Çıkış
POST /api/stok-islemleri/palet-cikis
Body: { palet_no: str, miktar?: int, siparis_no?: str, aciklama?: str }
→ StokHareketiResponseDTO

# Mal Kabul İrsaliyesi CRUD
GET    /api/mal-kabul-irsaliyeleri/
POST   /api/mal-kabul-irsaliyeleri/
GET    /api/mal-kabul-irsaliyeleri/{id}
PUT    /api/mal-kabul-irsaliyeleri/{id}
DELETE /api/mal-kabul-irsaliyeleri/{id}
```

### 6.2 PaletBilgiResponseDTO

```
PaletBilgiResponseDTO
├── palet_no
├── urun_id, urun_adi, urun_barkod
├── lot_no, lot_id
├── miktar (koli_adedi)
├── raf_bilgi (depo_adi, raf_kodu)
├── depo_id, depo_adi
├── durum (aktif/pasif)
├── kaynak ("irsaliye" | "erp")
├── son_kullanma_tarihi
└── giris_yapildi_mi (bool)
```

### 6.3 Mevcut Endpoint Uyumu

| Endpoint | Durum |
|---|---|
| `POST /api/stok-hareketleri/` | **Korunur** — sevkiyat ve eski akış kullanır |
| `GET /api/paletler/barkod/{palet_no}` | **Korunur** — palet yönetimi sayfası kullanır |
| `/api/sevkiyat-planlama/` | **Dokunulmaz** |

---

## 7. Veritabanı Migrasyonu

### 7.1 Yeni Tablolar

```sql
CREATE TABLE mal_kabul_irsaliyeleri (
    id                INT PRIMARY KEY AUTO_INCREMENT,
    irsaliye_no       VARCHAR(50) UNIQUE NOT NULL,
    tedarikci_id      INT NOT NULL REFERENCES tedarikciler(id),
    depo_id           INT NOT NULL REFERENCES depolar(id),
    tir_plaka         VARCHAR(20),
    sofor_adi         VARCHAR(100),
    durum             VARCHAR(20) DEFAULT 'Taslak',
    tarih             DATE NOT NULL,
    olusturma_tarihi  DATETIME DEFAULT NOW(),
    guncelleme_tarihi DATETIME DEFAULT NOW()
);

CREATE TABLE mal_kabul_kalemleri (
    id                          INT PRIMARY KEY AUTO_INCREMENT,
    mal_kabul_irsaliyesi_id     INT NOT NULL REFERENCES mal_kabul_irsaliyeleri(id),
    palet_no                    VARCHAR(30) UNIQUE NOT NULL,
    urun_id                     INT NOT NULL REFERENCES urunler(id),
    lot_no                      VARCHAR(50),
    miktar                      INT NOT NULL,
    raf_id                      INT REFERENCES raflar(id),
    durum                       VARCHAR(20) DEFAULT 'Bekliyor',
    uretim_tarihi               DATE,
    son_kullanma_tarihi         DATE,
    olusturma_tarihi            DATETIME DEFAULT NOW()
);
```

### 7.2 Mevcut Tablo Değişiklikleri

```sql
ALTER TABLE kullanicilar ADD COLUMN depo_id INT REFERENCES depolar(id);
```

### 7.3 Dokunulmayan Tablolar

| Tablo | Durum |
|---|---|
| `paletler` | Değişiklik yok — yeni giriş akışı bu tabloya yazar |
| `lotlar` | Değişiklik yok — lot bul/oluştur mantığı korunur |
| `stok_hareketleri` | Değişiklik yok — `palet_id` zaten mevcut |
| `irsaliyeler` | Dokunulmaz — çıkış/sevk irsaliyeleri aynen kalır |

### 7.4 Geriye Uyumluluk

- Eski `StokHareketi` kayıtları `palet_id=NULL` olabilir → sorun yok
- Mevcut `POST /api/stok-hareketleri/` endpoint'i çalışmaya devam eder
- `Urun.stok_miktari` column_property → `paletler` tablosundan hesaplar, değişiklik gereksiz

---

## 8. Frontend Tasarımı

### 8.1 Yeni Sayfa Akışı

```
Mevcut:  Tip Seç → Ürün Ara → Miktar Gir → Onayla
Yeni:    Tip Seç → Palet No Gir → Bilgi Önizleme → Onayla
```

### 8.2 Adım 2 — Palet No Girişi

- Metin alanı (manuel yazım)
- Fiziksel barkod okuyucu (`useBarcodeScanner` hook adapte edilir)
- Kamera tarama (`ZXingBarcodeScanner` bileşeni yeniden kullanılır)
- Palet no girilince → `GET /api/stok-islemleri/palet/{palet_no}` çağrılır

### 8.3 Adım 3 — Bilgi Önizleme

```
┌─────────────────────────────────┐
│  📦 PLT-2026-00142              │
│                                 │
│  Ürün:      Makarna 500g        │
│  Lot:       LOT-2026-0034       │
│  Miktar:    120 koli            │
│  Lokasyon:  Depo-A / R-03-B    │
│  SKT:       2027-01-15          │
│                                 │
│  ── Çıkış Detay ──             │  ← sadece çıkışta görünür
│  Çıkış Miktarı: [120]  (edit)  │
│  Sipariş No:     [____]        │
│  Açıklama:       [____]        │
│                                 │
│  [İptal]          [✓ Onayla]   │
└─────────────────────────────────┘
```

### 8.4 Hata Durumları

| Durum | Mesaj |
|---|---|
| Palet bulunamadı | "Bu palet numarası sistemde bulunamadı" |
| Farklı depo + yetki yok | "Bu palet X deposuna ait, yetkiniz bulunmuyor" |
| Zaten giriş yapılmış (giriş modunda) | "Bu palet zaten sisteme kaydedilmiş" |
| Pasif/boş palet (çıkış modunda) | "Bu palette stok bulunmuyor" |

---

## 9. Test Stratejisi

### Unit Testler
- `PaletBazliStokDomainService` — giriş, çıkış, sorgulama iş kuralları
- `MalKabulIrsaliyesi` entity — durum geçişleri (Taslak → Onaylandi → Tamamlandi)
- `MalKabulKalemi` entity — durum geçişleri (Bekliyor → GirisYapildi)
- Depo yetki kontrolü — rol bazlı erişim senaryoları
- Palet no format doğrulama

### Integration Testler
- `IrsaliyePaletVeriKaynagiService` → DB'den doğru palet bilgisi getirme
- Palet giriş akışı: irsaliye kalemi → lot → palet → stok hareketi (atomik)
- Palet çıkış akışı: tam çıkış + kısmi çıkış + yetersiz stok hatası
- Çapraz depo engeli: yetkisiz depo paleti → hata

### API Testler
- `GET /api/stok-islemleri/palet/{palet_no}` — bulunan, bulunamayan, yetkisiz
- `POST /api/stok-islemleri/palet-giris` — başarılı, çift giriş engeli, yetkisiz depo
- `POST /api/stok-islemleri/palet-cikis` — tam, kısmi, boş palet, pasif palet

---

## 10. Uygulama Fazları

| Faz | Kapsam | Durum | Detay |
|---|---|---|---|
| **Faz 1a** | MalKabulIrsaliyesi entity + repository + CRUD API + frontend sayfası | **TAMAMLANDI** | Entity, ORM, mapper, repository, use case, DTO, router, React sayfası, /simplify review |
| **Faz 1b** | IPaletVeriKaynagiService + IrsaliyePaletVeriKaynagi adapter | **TAMAMLANDI** | Interface, adapter, PaletBilgiDTO, PaletSorgulamaService |
| **Faz 1c** | PaletBazliStokDomainService + stok-islemleri endpoint'leri | **TAMAMLANDI** | Domain service (giriş/çıkış), 3 API endpoint, request DTO'lar, DI setup |
| **Faz 1d** | Kullanıcı depo ataması + yetki kontrolü | **TAMAMLANDI** | Entity, ORM, mapper, DTO, schema, domain service yetki kontrolü, DepoErisimHatasi, migration |
| **Faz 1e** | Frontend StokHareketleriPage yeni akış | **TAMAMLANDI** | Palet no bazlı UI, barkod/kamera entegrasyonu, Son İşlemler palet_no gösterimi |
| **Faz 1f** | Testler + entegrasyon doğrulama | Bekliyor | Unit, integration, API test suite |
| **Faz 2** | Toplu palet işlemi (çoklu tarama) | Bekliyor | Çoklu palet tarama, toplu onay |
| **Faz 3** | ERP adapter (`ErpPaletVeriKaynagiService`) | Bekliyor | ERP API entegrasyonu, adapter swap |

---

## 14. Faz 1a — Tamamlanan Çalışma ve Notlar

**Tamamlanma:** 2026-03-26 | **/simplify review:** Yapıldı (3 agent: reuse, quality, efficiency)

### Oluşturulan Dosyalar

| Katman | Dosya | Not |
|---|---|---|
| Entity | `app/core/entities/mal_kabul_irsaliye.py` | `MalKabulDurum` state machine, `MalKabulKalemi`, `MalKabulIrsaliye` (composite) |
| Repository | `app/core/repositories/mal_kabul_irsaliye_repository.py` | ABC interface, `getir_kalem_palet_no_ile()` Faz 1b'de kullanılacak |
| SA Repository | `app/infrastructure/persistence/repositories/sa_mal_kabul_irsaliye_repository.py` | joinedload, kalem sync, MKI-YYYY-NNNNN numara |
| DTO | `app/application/dto/mal_kabul_irsaliye_dto.py` | Olustur/Guncelle/Response DTO'lar, kalem DTO |
| Use Cases | `app/application/use_cases/mal_kabul_irsaliye_use_cases.py` | Listele, Getir, Olustur, Guncelle, Sil |
| Router | `app/api/v1/routers/mal_kabul_irsaliyeleri.py` | CRUD endpoint'ler, rol: admin+depocu+lojistik |
| ORM | `models.py` (ekleme) | `MalKabulIrsaliye`, `MalKabulKalemi` ORM modelleri |
| Mapper | `mappers.py` (ekleme) | `mal_kabul_*_to_entity/orm` (composite pattern) |
| DI | `container.py` (ekleme) | Repo + 5 use case factory |
| Frontend | `ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx` | Expandable list, modal CRUD, durum gecisileri |
| API | `ReactProje/src/services/api.js` (ekleme) | 5 yeni API fonksiyonu |
| Route | `App.jsx`, `Sidebar.jsx` (ekleme) | `/mal-kabul-irsaliyeleri` route + nav |

### /simplify Review Sonrası Yapılan Düzeltmeler

1. `ValueError` → `GecersizIslemError` (SilUseCase — HTTP 500 engelendi)
2. N+1 ürün doğrulama → `_urunleri_dogrula()` helper (deduplicated ID set)
3. Duplicate kalem mapping → `_dto_to_kalem_entity()` helper
4. Redundant condition `duzenlenebilir_mi() or eski_durum == TASLAK` → sadece `eski_durum == TASLAK`
5. Silent `except Exception: pass` kaldırıldı (mapper)
6. DTO validator: `TASLAK` izinli durumlardan çıkarıldı (domain zaten reddediyordu)
7. `guncelle()` repo: `return None` → `raise KayitBulunamadiError` (interface kontratı)
8. Dead state `detayModal` + unused import `Edit3` kaldırıldı
9. Referans veriler (tedarikci, depo, urun, raf) ayrı `useEffect` ile tek seferde yükleniyor

### Faz 1b'ye Geçiş Notları

- `IMalKabulIrsaliyeRepository.getir_kalem_palet_no_ile(palet_no)` metodu **hazır** — Faz 1b adapter bunu kullanacak
- `MalKabulKalemi.durum` alanı (`Bekliyor` → `GirisYapildi`) **hazır** — adapter `palet_giris_onayla()` bunu güncelleyecek
- `IPaletVeriKaynagiService` interface → `app/core/services/` altında oluşturulacak
- `IrsaliyePaletVeriKaynagiService` adapter → `app/infrastructure/services/` altında, `getir_kalem_palet_no_ile()` çağırarak implement edilecek
- `PaletBilgiDTO` → use case veya DTO katmanında tanımlanacak (kaynak: Bölüm 6.2)

---

## 15. Faz 1b+1c — Tamamlanan Çalışma ve Notlar

**Tamamlanma:** 2026-03-27

### Oluşturulan Dosyalar

| Katman | Dosya | Not |
|---|---|---|
| Interface | `app/core/services/palet_veri_kaynagi_service.py` | `IPaletVeriKaynagiService` ABC — `palet_bilgisi_getir()`, `palet_giris_onayla()` |
| Adapter | `app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py` | `IrsaliyePaletVeriKaynagiService` — MalKabulKalemi'nden okur |
| Query Service | `app/infrastructure/services/palet_sorgulama_service.py` | Read-model assembler: DB paleti > veri kaynağı fallback |
| Domain Service | `app/core/services/palet_bazli_stok_domain_service.py` | `PaletBazliStokDomainService` — giriş/çıkış iş kuralları |
| DTO | `app/application/dto/palet_bilgi_dto.py` | Kaynak bağımsız palet bilgi DTO |
| Request DTO | `app/application/dto/stok_islemleri_dto.py` | `PaletGirisRequestDTO`, `PaletCikisRequestDTO` |
| Router | `app/api/v1/routers/stok_islemleri.py` | 3 endpoint: sorgula, giriş, çıkış |
| DI | `container.py` (ekleme) | 3 factory: veri_kaynagi, domain_service, sorgulama_service |

---

## 16. Faz 1d — Tamamlanan Çalışma ve Notlar

**Tamamlanma:** 2026-03-27

### Değişiklikler

| Katman | Dosya | Değişiklik |
|---|---|---|
| Exception | `core/api_exceptions.py` | `DepoErisimHatasi` eklendi (403, kullanici_depo_id + hedef_depo_id + depo_adi) |
| Exception Re-export | `app/core/exceptions/__init__.py` | `DepoErisimHatasi` re-export eklendi |
| Entity | `app/core/entities/kullanici.py` | `depo_id: Optional[int]` alanı + `depo_erisim_var(hedef_depo_id)` metodu |
| ORM | `models.py` → `Kullanici` | `depo_id = Column(Integer, FK→depolar.id, nullable=True)` + `depo` relationship |
| Mapper | `mappers.py` | `kullanici_to_entity` ve `kullanici_to_orm` → `depo_id` eklendi |
| Repository | `sa_kullanici_repository.py` | `guncelle()` → `orm.depo_id` güncelleme eklendi |
| DTO | `kullanici_dto.py` | Response ve Guncelle DTO'lara `depo_id` eklendi |
| Schema | `schemas.py` | `KullaniciBase`, `KullaniciUpdate` → `depo_id` eklendi |
| Domain Service | `palet_bazli_stok_domain_service.py` | TODO'lar implement edildi — `_depo_yetki_kontrol()`, `_raf_depo_id_coz()`, `raf_repo` enjekte |
| Router | `stok_islemleri.py` | `current_user.depo_id` ve `current_user.rol == "admin"` bilgileri service'e geçiriliyor |
| Use Case | `kullanici_use_cases.py` | `depo_id` güncelleme desteği (sadece admin) |
| DI | `container.py` | `get_palet_bazli_stok_service` → `raf_repo` enjekte eklendi |
| Migration | `migrate_mysql.py` | `ALTER TABLE kullanicilar ADD COLUMN depo_id` + FK constraint |

### Yetki Kontrol Kuralları

- **Admin** → tüm depolara erişim (rol kontrolü)
- **depo_id=NULL** → tüm depolara erişim (henüz atanmamış, geriye uyumlu)
- **depo_id=X** → sadece X deposundaki paletlere erişim
- Yetkisiz erişim → `DepoErisimHatasi` (HTTP 403)

### Faz 1e'ye Geçiş Notları

- Backend tamamen hazır: 3 endpoint (`GET /palet/{no}`, `POST /palet-giris`, `POST /palet-cikis`) çalışır durumda
- `PaletBilgiDTO` response formatı frontend'in ihtiyaç duyduğu tüm bilgileri içeriyor
- Frontend `StokHareketleriPage.jsx` → palet no bazlı akışa dönüştürülecek
- `useBarcodeScanner` hook adapte edilecek (palet no girişi için)
- `ZXingBarcodeScanner` bileşeni yeniden kullanılacak (kamera tarama)
- Hata mesajları Türkçe ve kullanıcı dostu — frontend'te doğrudan gösterilebilir
- `KullaniciResponse` artık `depo_id` döndürüyor — frontend'te depo bilgisi gösterilebilir
- Admin panelinde kullanıcı düzenleme formuna "Atanmış Depo" select alanı eklenecek

---

## 17. Faz 1e — Tamamlanan Çalışma ve Notlar

**Tamamlanma:** 2026-03-27

### Frontend Değişiklikleri

| Dosya | Değişiklik |
|---|---|
| `ReactProje/src/services/api.js` | 3 yeni API fonksiyonu: `stokIslemleriPaletSorgula`, `stokIslemleriPaletGiris`, `stokIslemleriPaletCikis` |
| `ReactProje/src/pages/StokHareketleriPage.jsx` | Ürün bazlı akış → palet no bazlı akış dönüşümü (tam yeniden yazım) |

### Backend Değişiklikleri (palet_no Son İşlemler desteği)

| Dosya | Değişiklik |
|---|---|
| `app/core/entities/stok_hareketi.py` | `palet_no: Optional[str]` alanı eklendi |
| `app/application/dto/stok_hareketi_dto.py` | Response DTO'ya `palet_no` eklendi |
| `app/infrastructure/persistence/mappers.py` | `stok_hareketi_to_entity` → `orm.palet.palet_no` mapping |
| `app/infrastructure/persistence/repositories/sa_stok_hareketi_repository.py` | `joinedload(palet)` eklendi |

### Yeni Akış Detayları

1. **Adım 1:** GİRİŞ/ÇIKIŞ seçimi (Palet Kabul / Palet Sevk)
2. **Adım 2:** Palet No girişi — metin + fiziksel okuyucu (`useBarcodeScanner`) + kamera (`ZXingBarcodeScanner`)
3. **Adım 3:** PaletBilgiDTO önizleme kartı (ürün, lot, miktar, raf, depo, SKT, durum, kaynak)
   - Giriş: önizle + onayla
   - Çıkış: kısmi miktar (±/+5/+10/+50/MAX) + sipariş no + açıklama
4. **Son İşlemler:** `palet_no` bilgisi gösteriliyor (backend'den joinedload ile gelir)

### Korunan Bileşenler

- `HareketModal` export'u geriye uyumlu (Header'dan çağrılır)
- `getStokHareketleri` Son İşlemler listesi için kullanılmaya devam ediyor
- Mevcut `POST /api/stok-hareketleri/` endpoint'i dokunulmadı

### Kaldırılan Bileşenler

- Ürün arama/filtreleme state ve UI (urunler, aramaText, aramaFocused, filteredUrunler)
- Raf seçimi (giriş modunda)
- Tır plaka, depo kapı, barkodlar alanları (çıkış modunda)
- `getUrunler`, `getRaflar` çağrıları (artık gerekli değil)

### Faz 1f'ye Geçiş Notları

- Unit test hedefleri: `PaletBazliStokDomainService` giriş/çıkış, depo yetki kontrolü
- Integration test: palet giriş → lot+palet+stok_hareketi atomik akış
- API test: 3 endpoint başarılı/hata senaryoları
- Frontend E2E: palet no girişi → sorgulama → onay akışı (manuel test)

---

## 11. Non-Functional Gereksinimler

| Gereksinim | Hedef |
|---|---|
| Palet sorgulama yanıt süresi | < 500ms |
| Toplu işlem limiti (Faz 2) | Max 50 palet/işlem |
| Eşzamanlılık kontrolü | SELECT FOR UPDATE — ilk gelen kazanır |
| Atomiklik | Tüm işlem tek transaction, hata → rollback |
| Geriye uyumluluk | Eski kayıtlar bozulmaz, mevcut endpoint'ler çalışır |
| Audit trail | Her palet işlemi SistemLog'a yazılır |

---

## 12. Varsayımlar

1. Mevcut sevkiyat modülünün FIFO çıkış akışı **aynen korunacak**
2. `Kullanici` entity'sine `depo_id` alanı eklenecek (atanmış depo)
3. Mevcut `StokHareketi` tablosu geriye uyumlu kalacak
4. `palet_no` unique constraint zaten mevcut (`Palet.palet_no` unique=True)
5. ERP geldiğinde sadece `IPaletVeriKaynagiService` implementasyonu değişecek
6. Palet no geçici formatı: `PLT-YYYY-XXXXX` (ERP formatı geldiğinde adapter'da güncellenir)

---

## 13. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| Mal Kabul İrsaliyesi'ndeki palet_no ile Palet tablosundaki palet_no çakışması | Veri tutarsızlığı | UNIQUE constraint + giriş öncesi kontrol |
| ERP format standardı farklı olabilir | Adapter değişikliği | Format doğrulama soyutlanmış, regex adapter'da |
| Mevcut kullanıcıların depo ataması eksik | Yetki hatası | Migration sırasında varsayılan depo atanır veya admin uyarılır |
