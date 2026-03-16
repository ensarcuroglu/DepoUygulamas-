# Mimari Konsolidasyon Planı: İkili Mimari Karmaşası Çözümü

## Problem Özeti

Proje şu anda iki farklı mimari deseni eş zamanlı kullanmaktadır:

| Katman | Legacy (15 modül) | Clean Architecture (3 modül) |
|--------|-------------------|------------------------------|
| Router | `routers/*.py` | `app/api/v1/routers/` |
| İş Mantığı | `crud.py` içinde | `app/application/use_cases/` |
| Veri Erişimi | Doğrudan `crud.py` | `app/infrastructure/persistence/repositories/` |
| Entity | `models.py` | `app/core/entities/` |
| Exception | `core/exceptions.py` (APIException) | `app/core/exceptions/` (DomainException) |

### Neden Bu Plan?

1. **Proje Boyutu**: 15 modülün tamamını Clean Architecture'a taşımak aylar alabilir ve risklidir
2. **Mevcut Durum**: Clean Architecture sadece 3 modülde (Ürünler, Stok Hareketleri, Siparişler) kullanılıyor
3. **Kritik Nokta**: Her iki exception sisteminin `main.py`'de ayrı ayrı kayıtlı olması (satır 190-206)

---

## Önerilen Çözüm: Hibrit Konsolidasyon

**Tercİh Nedeni**: Mevcut proje için en düşük riskli, orta yol bir çözüm. Clean Architecture'ın faydalarını korurken, legacy modüllerin sadeliğini de bozmadan ilerler.

### Temel İlkeler

1. **Exception Hiyerarşisini Birleştir**: İki farklı exception sistemini tek bir yapıda birleştir
2. **Database Bağlantısını Tekilleştir**: İki `database.py` dosyasını kaldır
3. **Repository Pattern'e Geçiş (Kademeli)**: `crud.py`'yi domain bazında ayır, ancak Clean Architecture'a tam geçiş yerine "Service + Repository" hibrit model kullan
4. **Router Yapısını Sadeleştir**: Legacy router'ları `app/api/v1/routers/` altında yeniden organize et

---

## Adım Adım Uygulama Planı

### Faz 1: Exception Birleştirme (En Kritik)

**Hedef**: Tek bir exception hiyerarşisi

**Dosyalar**:
- `core/exceptions.py` (Legacy - mevcut)
- `app/core/exceptions/__init__.py` (Clean Architecture - mevcut)
- `core/exception_handlers.py` (mevcut)

**Eylemler**:

1. **Yeni birleşik exception dosyası oluştur** (`core/api_exceptions.py`):

```python
# core/api_exceptions.py
from fastapi import status
from typing import Any, Optional

class APIException(Exception):
    """Birleşik base exception - tüm API hatalarının atası"""
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# Legacy exception'ları koru (geriye dönük uyumluluk)
class NotFoundError(APIException):
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            f"{resource} (ID: {resource_id}) bulunamadı",
            {"resource": resource, "id": str(resource_id)}
        )

class DuplicateError(APIException):
    def __init__(self, field: str, value: str):
        super().__init__(
            status.HTTP_409_CONFLICT,
            f"{field} '{value}' zaten mevcut",
            {"field": field, "value": value}
        )

class PermissionDeniedError(APIException):
    def __init__(self, message: str = "Bu işlemi yapmaya yetkiniz yok"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)

class AuthenticationError(APIException):
    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)

class BadRequestError(APIException):
    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)

class InputValidationError(APIException):
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, details)

# Domain exception'ları da aynı yapıya ekle
class KayitBulunamadiError(APIException):
    def __init__(self, entity_adi: str, entity_id: int | str | None = None):
        mesaj = f"{entity_adi} bulunamadı"
        if entity_id is not None:
            mesaj += f" (ID: {entity_id})"
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            mesaj,
            {"entity": entity_adi, "id": str(entity_id) if entity_id else None}
        )

class YetkisizIslemError(APIException):
    def __init__(self, message: str = "Bu işlem için yetkiniz bulunmamaktadır."):
        super().__init__(status.HTTP_403_FORBIDDEN, message)

class YetersizStokError(APIException):
    def __init__(self, urun_ismi: str, mevcut: int, istenen: int):
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            f"Yetersiz stok! Ürün: {urun_ismi}, Mevcut: {mevcut}, İstenen: {istenen}",
            {"urun": urun_ismi, "mevcut": mevcut, "istenen": istenen}
        )

class StokVeriUyumsuzluguError(APIException):
    def __init__(self, urun_ismi: str):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Stok veri uyuşmazlığı: {urun_ismi}",
            {"urun": urun_ismi}
        )

class GecersizDurumGecisiError(APIException):
    def __init__(self, entity_adi: str, mevcut: str, hedef: str):
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            f"{entity_adi} için geçersiz durum geçişi: {mevcut} → {hedef}",
            {"entity": entity_adi, "mevcut_durum": mevcut, "hedef_durum": hedef}
        )

class CakismaHatasi(APIException):
    def __init__(self, alan: str, deger: str):
        super().__init__(
            status.HTTP_409_CONFLICT,
            f"Bu {alan} zaten kullanılıyor: {deger}",
            {"field": alan, "value": deger}
        )

class GecersizIslemError(APIException):
    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)
```

2. **Exception handler'ı güncelle** (`core/exception_handlers.py`):

```python
# core/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from core.api_exceptions import APIException

async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            **exc.details
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    # Beklenmeyen hatalar için
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Sunucu hatası. Lütfen sistem yöneticisiyle iletişime geçin."
        }
    )
```

3. **main.py güncellemeleri** (satır 20-46 ve 190-206):

```python
# Kaldırılacak satırlar (20-46):
# - Legacy exception import'ları
# - Domain exception import'ları

# Yeni import:
from core.api_exceptions import (
    APIException,
    NotFoundError,
    DuplicateError,
    # ... tüm exception'lar
    KayitBulunamadiError,
    YetersizStokError,
    # ...
)
from core.exception_handlers import api_exception_handler, generic_exception_handler

# Handler kayıtları (190-206 yerine):
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

4. **Tüm kullanım noktalarını güncelle**:
   - `routers/*.py` dosyalarındaki import'ları güncelle
   - `app/api/v1/routers/*.py` dosyalarındaki import'ları güncelle
   - `app/application/use_cases/*.py` dosyalarındaki import'ları güncelle
   - `services/*.py` dosyalarındaki import'ları güncelle
   - `crud.py`'deki exception kullanımlarını güncelle

**Doğrulama**:
- Tüm endpoint'lerin çalıştığını test et
- Hata mesajlarının doğru döndüğünü doğrula

---

### Faz 2: Database Bağlantısı Tekilleştirme

**Hedef**: İki `database.py` dosyasını tek bir dosyada birleştir

**Dosyalar**:
- `BackendProje/database.py` (Legacy)
- `BackendProje/app/infrastructure/persistence/database.py` (Clean Architecture)

**Eylemler**:

1. **Mevcut yapıyı analiz et**:
   - Her iki dosyadaki `get_db`, `engine`, `SessionLocal` tanımlamalarını karşılaştır
   - Farklılıkları not al

2. **Ana `database.py`'yi güçlendir** (eğer farklılık yoksa doğrudan kullan):

```python
# database.py (güncelleme)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "depo_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager olarak database oturumu"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

3. **Clean Architecture modüllerini güncelle**:
   - `app/infrastructure/persistence/database.py`'yi kaldır
   - İlgili dosyalarda import'u değiştir:
     ```python
     # Eski:
     from app.infrastructure.persistence.database import get_db
     # Yeni:
     from database import get_db
     ```

**Doğrulama**:
- Tüm veritabanı işlemlerinin çalıştığını doğrula

---

### Faz 3: CRUD Modülerleştirme

**Hedef**: Monolitik `crud.py`'yi (1.426 satır) domain bazında ayır

**Mevcut Yapı** (`crud.py` içindeki bölümler):
```
├── Marka CRUD         (satır 32-68)
├── Kategori CRUD      (satır 71-136)
├── Depo CRUD          (satır 139-185)
├── Raf CRUD           (satır 188-226)
├── Tedarikçi CRUD     (satır 229-265)
├── Ürün CRUD          (satır 268-389)
├── Lot CRUD           (satır 392-450)
├── Palet CRUD         (satır 453-514)
├── Stok Hareketi      (satır 517-645)
├── Dashboard          (satır 648-674)
├── Destek Masası      (satır 677-731)
├── Sipariş            (satır 734-869)
├── Sevkiyat Planı     (satır 872-976)
├── İrsaliye           (satır 979-1101)
├── Rapor Şablonu      (satır 1104-1175)
├── Rapor Logu         (satır 1178-1197)
├── Rapor Schedule     (satır 1200-1266)
└── Rapor Veri Üretimi (satır 1269-1426)
```

**Eylemler**:

1. **`crud/` klasörü oluştur**:
```
BackendProje/crud/
├── __init__.py        # Tüm CRUD'ları re-export et
├── marka_crud.py
├── kategori_crud.py
├── depo_crud.py
├── raf_crud.py
├── tedarikci_crud.py
├── urun_crud.py
├── lot_crud.py
├── palet_crud.py
├── stok_hareketi_crud.py
├── destek_crud.py
├── siparis_crud.py
├── sevkiyat_crud.py
├── irsaliye_crud.py
├── rapor_crud.py
└── utils.py          # Ortak yardımcı fonksiyonlar
```

2. **Örnek: `crud/marka_crud.py`**:

```python
# crud/marka_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from models import Marka
from core.api_exceptions import NotFoundError, DuplicateError

def get_all_markalar(db: Session, skip: int = 0, limit: int = 100) -> List[Marka]:
    return db.query(Marka).filter(Marka.aktif == True).offset(skip).limit(limit).all()

def get_marka_by_id(db: Session, marka_id: int) -> Marka:
    marka = db.query(Marka).filter(Marka.id == marka_id, Marka.aktif == True).first()
    if not marka:
        raise NotFoundError("Marka", marka_id)
    return marka

def create_marka(db: Session, ad: str) -> Marka:
    existing = db.query(Marka).filter(Marka.ad == ad).first()
    if existing:
        raise DuplicateError("Marka adı", ad)
    marka = Marka(ad=ad, aktif=True)
    db.add(marka)
    db.commit()
    db.refresh(marka)
    return marka

def update_marka(db: Session, marka_id: int, ad: str) -> Marka:
    marka = get_marka_by_id(db, marka_id)
    existing = db.query(Marka).filter(Marka.ad == ad, Marka.id != marka_id).first()
    if existing:
        raise DuplicateError("Marka adı", ad)
    marka.ad = ad
    db.commit()
    db.refresh(marka)
    return marka

def delete_marka(db: Session, marka_id: int) -> None:
    marka = get_marka_by_id(db, marka_id)
    marka.aktif = False
    db.commit()
```

3. **`crud/__init__.py` oluştur**:

```python
# crud/__init__.py
from .marka_crud import *
from .kategori_crud import *
from .depo_crud import *
# ... tüm domainler

# Geriye dönük uyumluluk için eski import yollarını koru
import crud
# Bu sayede eski kod: crud.get_all_markalar() hâlâ çalışır
```

4. **Mevcut `crud.py`'yi güncelle** (geriye dönük uyumluluk):

```python
# crud.py (minimal wrapper)
"""
Bu dosya geriye dönük uyumluluk için korunmaktadır.
Yeni kod doğrudan crud/ paketini kullanmalıdır.
"""
from crud import (
    get_all_markalar, get_marka_by_id, create_marka, update_marka, delete_marka,
    # ... tüm fonksiyonlar
)

__all__ = [
    "get_all_markalar",
    # ...
]
```

**Doğrulama**:
- Mevcut router'ların çalıştığını doğrula (geriye dönük uyumluluk)
- Yeni modüllerin import edildiğini doğrula

---

### Faz 4: Router Yeniden Organizasyonu (Opsiyonel)

**Hedef**: Legacy router'ları daha düzenli bir yapıya taşı

**Mevcut Yapı**:
- `routers/markalar.py`
- `routers/kategoriler.py`
- ...

**Önerilen Yapı**:
```
BackendProje/routers/
├── __init__.py
├── auth.py           # Auth (özel - session management)
├── v1/
│   ├── __init__.py
│   ├── markalar.py
│   ├── kategoriler.py
│   ├── depolar.py
│   ├── raflar.py
│   ├── tedarikciler.py
│   ├── urunler.py
│   ├── lotlar.py
│   ├── paletler.py
│   ├── stok_hareketleri.py
│   ├── siparisler.py
│   ├── sevkiyat_planlama.py
│   ├── irsaliyeler.py
│   ├── raporlar.py
│   ├── stok_sayim.py
│   ├── kullanicilar.py
│   ├── sistem_loglari.py
│   └── destek.py
```

**Not**: Bu faz zorunlu değildir. Mevcut yapı çalışıyorsa olduğu gibi bırakılabilir.

---

## Kontrol Listesi

### Faz 1 - Exception Birleştirme ✅
- [x] `core/api_exceptions.py` oluşturuldu (birleşik hiyerarşi: APIException base)
- [x] `core/exception_handlers.py` güncellendi (tek handler yeterli)
- [x] `main.py` güncellendi (10 handler → 2 handler)
- [x] `core/exceptions.py` re-export wrapper'a dönüştürüldü (geriye dönük uyumluluk)
- [x] `app/core/exceptions/__init__.py` re-export wrapper'a dönüştürüldü
- [x] Tüm mevcut import yolları korundu — sıfır kırılma
- [ ] API testleri başarılı (sunucuda doğrulanacak)

### Faz 2 - Database Tekilleştirme ✅
- [x] İki database.py dosyası analiz edildi (birebir aynı)
- [x] `app/infrastructure/persistence/database.py` re-export wrapper'a dönüştürüldü
- [x] DI container import'u `database` modülüne yönlendirildi
- [ ] API testleri başarılı (sunucuda doğrulanacak)

### Faz 3 - CRUD Modülerleştirme ✅
- [x] `crud/` paketi oluşturuldu (15 modül)
- [x] Domain bazında CRUD dosyaları: marka, kategori, depo, raf, tedarikci, urun, lot, palet, stok_hareketi, dashboard, destek, siparis, sevkiyat, irsaliye, rapor
- [x] `crud/__init__.py` tüm fonksiyonları re-export ediyor
- [x] Eski `crud.py` → `_crud_legacy.py` olarak yedeklendi
- [ ] API testleri başarılı (sunucuda doğrulanacak)

### Faz 4 - Router Organizasyonu (Ertelendi)
- Bu faz bilinçli olarak ertelendi. İleride Clean Architecture geçişi sırasında yapılacak.

---

## Risk Yönetimi

| Risk | Önlem |
|------|-------|
| Geriye dönük uyumluluk kaybı | Her faz sonunda test, geri dönüş planı |
| Büyük kod değişikliği | Faz bazlı ilerleme, her fazda doğrulama |
| Yeni hatalar | Mevcut işlevselliği koruyarak ilerleme |

---

## Başarı Kriterleri

1. Tek bir exception sistemi çalışıyor
2. Tek bir database bağlantısı kullanılıyor
3. `crud.py` domain bazında ayrılmış (okunabilirlik artmış)
4. Mevcut 15+ router sorunsuz çalışıyor
5. Clean Architecture'daki 3 modül (Ürünler, Stok Hareketleri, Siparişler) hâlâ çalışıyor
6. Hiçbir API endpoint'i bozulmamış

---

## İlerleme Takibi

| Faz | Tahmini Süre | Tamamlandı |
|-----|--------------|------------|
| Faz 1: Exception Birleştirme | 2-3 saat | [x] |
| Faz 2: Database Tekilleştirme | 1 saat | [x] |
| Faz 3: CRUD Modülerleştirme | 3-4 saat | [x] |
| Faz 4: Router Organizasyonu | 1-2 saat | Ertelendi |

**Durum**: Faz 1-3 tamamlandı. Faz 4 ileride CA geçişi ile birlikte yapılacak.
