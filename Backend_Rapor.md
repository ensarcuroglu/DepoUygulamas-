# 🔍 Backend Genel Analiz Raporu

**Tarih:** 13 Mart 2026  
**Proje:** Depo Yönetim Sistemi — FastAPI Backend  
**Kapsam:** Mimari, kod kalitesi, güvenlik, performans ve düzen analizi

---

## 📊 Genel Bakış

| Metrik | Değer |
|---|---|
| Toplam Python dosyası | ~50+ |
| `crud.py` satır sayısı | **1.426** (monolitik) |
| `models.py` satır sayısı | 524 |
| `schemas.py` satır sayısı | 721 |
| Legacy router sayısı | 15 |
| Clean Architecture router | 3 (Ürünler, Stok Hareketleri, Siparişler) |
| Service sınıfı | 13 |
| Use Case sınıfı | 13 |
| Test dosyası | **0** ❌ |

---

## 🚨 1. Kritik Düzeyde — İkili Mimari Karmaşası

> [!CAUTION]
> Proje şu anda **iki farklı mimari deseni** aynı anda kullanmaktadır. Bu, bakımı ciddi şekilde zorlaştırır.

### Sorun

Birlikte çalışan ama **farklı kalıplara sahip** iki yapı var:

| Katman | Legacy (15 modül) | Clean Architecture (3 modül) |
|---|---|---|
| Router | `routers/*.py` → `services/` → `crud.py` | `app/api/v1/routers/` → Use Case → Repository |
| İş mantığı | `crud.py` içinde karışık | `app/application/use_cases/` |
| Veri erişimi | Doğrudan `crud.py` fonksiyonları | `app/infrastructure/persistence/repositories/` |
| DTO | `schemas.py` (Pydantic) | `app/application/dto/` |
| Entity | `models.py` (SQLAlchemy = Entity) | `app/core/entities/` (ayrı domain entity) |
| Exception | `core/exceptions.py` (APIException) | `app/core/exceptions/` (DomainException) |

### Neden Sorun?

- Aynı kavramlar (Ürün, Sipariş) **iki farklı yerde** farklı kalıplarla tanımlı
- Yeni gelen geliştirici hangi kalıbı izleyeceğini bilemez
- Hata ayıklama sırasında iki exception hiyerarşisi var (`APIException` vs `DomainException`)
- `main.py`'de **her iki sistemin handler'ları** ayrı ayrı kayıtlanıyor (satır 190-206)

### Öneri

Kalan 15 legacy modülü kademeli olarak Clean Architecture'a taşıyın veya **tersi yönde**, eğer Clean Architecture gereksiz karmaşıklık getiriyorsa, services katmanını standart hale getirip tek bir kalıp kullanın.

---

## 🔴 2. Yüksek Düzeyde — Monolitik `crud.py` (1.426 satır)

> [!WARNING]
> Tek bir dosyada **16 farklı domain'e** ait CRUD operasyonları bulunuyor.

### Mevcut Durum

```
crud.py
├── Marka CRUD         (satır 32-68)
├── Kategori CRUD      (satır 71-136)
├── Depo CRUD          (satır 139-185)
├── Raf CRUD           (satır 188-226)
├── Tedarikçi CRUD     (satır 229-265)
├── Ürün CRUD          (satır 268-389)
├── Lot CRUD           (satır 392-450)
├── Palet CRUD         (satır 453-514)
├── Stok Hareketi      (satır 517-645)  ← İş mantığı da içeriyor
├── Dashboard          (satır 648-674)
├── Destek Masası      (satır 677-731)
├── Sipariş            (satır 734-869)
├── Sevkiyat Planı     (satır 872-976)  ← İş mantığı da içeriyor
├── İrsaliye           (satır 979-1101) ← İş mantığı da içeriyor
├── Rapor Şablonu      (satır 1104-1175)
├── Rapor Logu         (satır 1178-1197)
├── Rapor Schedule     (satır 1200-1266)
└── Rapor Veri Üretimi (satır 1269-1426)
```

### Sorunlar

1. **Single Responsibility ihlali** — Bir dosya, tüm veri erişim katmanını oluşturuyor
2. **İş mantığı sızması** — `_fifo_palet_azalt()` (FIFO stok çıkışı), `create_stok_hareketi()`, `update_sevkiyat_plani()` fonksiyonları ciddi iş mantığı içeriyor
3. **Merge conflict riski** — Birden fazla geliştiricinin aynı anda çalışması

### Öneri

Her domain için ayrı dosya oluşturun: `crud/marka_crud.py`, `crud/urun_crud.py`, vb. veya doğrudan repository pattern'e geçin.

---

## 🔴 3. Yüksek Düzeyde — Test Altyapısı Yok

> [!CAUTION]
> Projede **hiçbir birim testi veya entegrasyon testi** bulunmamaktadır.

### Riskler

- Refactoring sırasında regresyon tespiti yapılamaz
- İş mantığındaki edge case'ler (FIFO stok, sipariş durumu geçişleri) doğrulanamaz
- CI/CD pipeline kurulamaz

### Öneri

1. `pytest` + `httpx` ile test altyapısı kurun
2. En kritik iş mantıklarını (FIFO stok çıkışı, sevkiyat durumu geçişleri) öncelikli test edin
3. `conftest.py` ile test veritabanı fixture'ı oluşturun

---

## 🟠 4. Orta Düzeyde — `models.py` ve `schemas.py` Monolitik Yapısı

### Models (524 satır — 17 model)

Tüm SQLAlchemy modelleri tek dosyada. Domain'ler arası ilişkiler karmaşıklaşıyor.

### Schemas (721 satır — 50+ Pydantic schema)  

Create, Update, Response şemaları iç içe geçmiş. Forward reference sorunu nedeniyle `KullaniciResponse` schema'dan önce tanımlanması gerekiyor ama dosyada bu sıralama doğru yapılmış.

### Öneri

Dosyaları domain bazında ayırın:

```
models/
├── __init__.py      # Tüm modelleri re-export et
├── kullanici.py
├── urun.py
├── siparis.py
├── stok.py          # Lot, Palet, StokHareketi
└── rapor.py
```

---

## 🟠 5. Orta Düzeyde — Services Katmanı Tutarsızlığı

### Mevcut Yapı

`services/` klasöründe 13 service sınıfı var ama bunlar sadece **legacy router'lar** tarafından kullanılıyor. Clean Architecture modülleri bunları kullanmıyor — kendi Use Case'lerini kullanıyor.

### Sorunlar

- Services çoğunlukla `crud.py`'ye **ince birer wrapper** — gerçek iş mantığı eklemiyor
- Örneğin `RaporService.get_stok_verisi()` sadece `crud.get_stok_raporu_verileri()` çağırıyor
- Bazı router'lar service kullanıyor, bazıları doğrudan `crud` kullanıyor — **tutarsız**

### Öneri

Bir karar verin: ya tüm router'lar service'leri kullansın ya da service katmanı kaldırılıp doğrudan repository/use case kullanılsın.

---

## 🟠 6. Orta Düzeyde — Exception Handling Karmaşası

### İki Ayrı Exception Hiyerarşisi

```python
# core/exceptions.py (Legacy)
APIException → NotFoundError, DuplicateError, BadRequestError, ...

# app/core/exceptions/ (Clean Architecture)
DomainException → KayitBulunamadiError, YetersizStokError, CakismaHatasi, ...
```

### main.py'deki Handler Kayıtları (satır 190-206)

```python
# 1. Legacy
app.add_exception_handler(APIException, api_exception_handler)

# 2. Domain (Clean Architecture) — 7 ayrı handler
app.add_exception_handler(KayitBulunamadiError, kayit_bulunamadi_handler)
app.add_exception_handler(YetersizStokError, yetersiz_stok_handler)
# ... 5 tane daha

# 3. Genel fallback
app.add_exception_handler(Exception, generic_exception_handler)
```

### Öneri

Exception hiyerarşisini birleştirin. Tek bir base exception ile spesifik alt sınıflar yeterli.

---

## 🟠 7. Orta Düzeyde — Veritabanı ve ORM Sorunları

### 7.1 `declarative_base` Uyarısı

```python
# database.py satır 21
from sqlalchemy.ext.declarative import declarative_base  # ⚠️ DEPRECATED
Base = declarative_base()
```

**SQLAlchemy 2.0+'da** `DeclarativeBase` sınıfı kullanılmalı:

```python
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

### 7.2 `datetime.utcnow()` Kullanımı

> [!WARNING]
> `datetime.utcnow()` Python 3.12'de **deprecated** olarak işaretlendi.

Proje genelinde yaygın olarak kullanılıyor:
- `models.py` — Tüm model default değerleri
- `auth.py` — Token oluşturma
- `crud.py` — Stok hareketi tarihleri

**Doğrusu:** `datetime.now(timezone.utc)` kullanılmalı.

### 7.3 `column_property` ile N+1 Çözümü

```python
# models.py satır 515-524
Urun.stok_miktari = column_property(
    select(func.coalesce(func.sum(Palet.koli_adedi), 0))
    .select_from(Lot).join(Palet, ...)
    ...
)
```

Bu yaklaşım **her ürün sorgusu** için bir alt sorgu çalıştırır. Liste sorguları için performans kaybı yaratabilir. Büyük veri setlerinde `column_property` yerine ayrı bir sorgu veya denormalizasyon düşünülebilir.

---

## 🟠 8. Orta Düzeyde — Güvenlik İyileştirmeleri

### 8.1 JWT Secret Key Loglama

```python
# main.py satır 51
logger.info(f"🔐 JWT Secret Key: {SECRET_KEY[:8]}... (yapılandırıldı)")
```

> [!WARNING]
> Secret key'in ilk 8 karakteri bile loglara sızmamalı. Sadece "JWT Key yapılandırıldı" yeterli.

### 8.2 CORS Ayarları

```python
# main.py satır 220-226
allow_origins=["http://localhost:5173", "http://localhost:3000"],
allow_methods=["*"],
allow_headers=["*"],
```

Geliştirme ortamı için uygun, ancak **üretim için** bu ayarlar sıkılaştırılmalı. Ortam değişkeninden okunması önerilir.

### 8.3 Register Endpoint Yetki Kontrolü

```python
# routers/auth.py satır 167-178
@router.post("/register", ...)
def register(..., current_user = Depends(get_current_user)):
    if current_user.rol != "admin":  # Manuel kontrol
        raise HTTPException(...)
```

`require_role("admin")` dependency'si zaten mevcut ama burada kullanılmamış. Manuel kontrol yerine mevcut dependency kullanılmalı.

---

## 🟡 9. Kod Düzeni ve Standart Sorunları

### 9.1 Silme Tutarsızlığı

| Modül | Silme Yöntemi |
|---|---|
| Marka, Raf, Tedarikçi | `aktif = False` (soft delete) — **Log kaydı yok** |
| Kategori, Depo, Ürün | `aktif = False` (soft delete) — Log kaydı var |
| Sevkiyat Planı | `db.delete()` **(hard delete)** — Log kaydı var |
| Rapor Schedule | `db.delete()` **(hard delete)** — Log kaydı var |

**Sorun:** Bazı modüller soft delete, bazıları hard delete kullanıyor. Log kaydı da tutarsız.

### 9.2 Bare `except` Kullanımı

```python
# crud.py satır 753, 997
except:
    yeni_no = 1
```

`except Exception` veya spesifik exception kullanılmalı.

### 9.3 `startswith` SQL Filtresi

```python
# crud.py satır 745, 990
Siparis.siparis_no.startswith(f"SIP-{yil}-")
```

SQLAlchemy'de `startswith` kullanımı desteklenmektedir ancak **`like` ile daha kararlı** çalışır ve bazı veritabanı sürücülerinde sorun çıkarabilir.

---

## 🟡 10. `main.py` Aşırı Sorumluluk

`main.py` dosyası **272 satır** olup şu sorumlulukları taşımakta:

1. FastAPI uygulama oluşturma
2. APScheduler kurulumu ve zamanlama mantığı (~80 satır)
3. E-posta gönderimi (`_zamanlama_email_gonder`)
4. CORS ayarları
5. Exception handler kayıtları
6. Router kayıtları
7. Dashboard endpoint'i
8. Lifespan yönetimi

### Öneri

- Scheduler mantığını `scheduler/` modülüne taşıyın
- E-posta gönderimini `utils/email.py`'ye taşıyın
- Dashboard endpoint'ini ilgili router'a taşıyın

---

## 🟡 11. Duplicate `database.py` Dosyası

Projede **iki ayrı** `database.py` dosyası var:

| Dosya | Konum |
|---|---|
| Ana | `BackendProje/database.py` |
| Clean Architecture | `app/infrastructure/persistence/database.py` |

Her ikisi de `get_db` fonksiyonu sağlıyor. Biri `from database import get_db`, diğeri `from app.infrastructure.persistence.database import get_db` şeklinde kullanılıyor.

### Öneri

Tek bir `database.py` kullanılmalı. Clean Architecture modülleri de ana `database.py`'yi kullanabilir veya tam tersi.

---

## 🟡 12. Eksik Altyapı Dosyaları

| Eksik | Açıklama |
|---|---|
| `requirements.txt` detayı | Versiyon pinleme yok — sadece paket adları |
| `.gitignore` | Proje kökünde yok (kontrol edilmeli) |
| `Dockerfile` | Konteynerize etme desteği yok |
| `alembic/` | Veritabanı migration aracı yok — `Base.metadata.create_all()` kullanılıyor |
| `tests/` | Test klasörü yok |
| Logging konfigürasyonu | Sadece `basicConfig` — dosyaya yazma, log seviyesi yönetimi yok |

---

## 📋 Öncelikli İyileştirme Sıralaması

| # | İyileştirme | Öncelik | Etki |
|---|---|---|---|
| 1 | Mimari kararı ver (Legacy vs Clean Architecture) | 🔴 Kritik | Tüm geliştirme yönünü belirler |
| 2 | `crud.py`'yi domain bazında ayır | 🔴 Yüksek | Bakım kolaylığı |
| 3 | Test altyapısı kur | 🔴 Yüksek | Güvenli refactoring |
| 4 | Exception hiyerarşisini birleştir | 🟠 Orta | Hata yönetimi tutarlılığı |
| 5 | `models.py` ve `schemas.py`'yi böl | 🟠 Orta | Kod okunabilirliği |
| 6 | `main.py`'yi hafiflet | 🟡 Normal | Sorumluluk ayrımı |
| 7 | `datetime.utcnow()` → `datetime.now(UTC)` | 🟡 Normal | Deprecation uyumu |
| 8 | Silme ve loglama tutarlılığı | 🟡 Normal | Veri bütünlüğü |
| 9 | Alembic migration sistemi kur | 🟡 Normal | Veritabanı versiyonlama |
| 10 | Güvenlik iyileştirmeleri | 🟡 Normal | Üretim hazırlığı |

---

> [!NOTE]
> Bu rapor backend kodunun **mevcut halini** analiz etmektedir. Clean Architecture dönüşümü yarım kalmış durumdadır. Öncelikle bir mimari karar alınmalı, ardından tutarlı bir şekilde uygulanmalıdır.
