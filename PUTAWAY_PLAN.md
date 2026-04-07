# Putaway (Yerleştirme) Sistemi — Uygulama Planı

> **Prensip:** _"Sistem Yönlendirir, Operatör Uygular, Sistem Doğrular"_

## Yaklaşım

Mal kabul irsaliyesi onaylandığında paletler otomatik oluşturulacak ve bir **Yerleştirme Algoritması** ile en uygun rafa önerilecek. Ancak fiziksel raf ataması, saha operatörünün el terminaliyle raf barkodunu okutup onaylamasıyla kesinleşecek. Sistem her adımda zon uygunluğu ve kapasite doğrulaması yapacak.

---

## Kapsam

### Dahil
- Zon (Bölge) entity ve yönetimi
- Ürün depolama tipi alanı
- Raf entity'ye zon_id + max_agirlik + hiyerarşik kod (ZON-KORIDOR-RAF-KAT) eklenmesi
- Yerleştirme Görevi (Putaway Task) entity ve yaşam döngüsü (Yerlestirme + Transfer + BelirsizKonum tipleri)
- Pull-based FIFO görev kuyruğu + pessimistic locking
- Yerleştirme Algoritması (domain service)
- Kapasite doğrulama servisi (hibrit: slot + ağırlık)
- İrsaliye onay → otomatik palet oluşturma + görev üretimi
- Karantina çıkış akışı (admin/QC onay → transfer görevi)
- Mobil terminal scan-to-verify iş akışı
- Süpervizör override mekanizması
- Legacy data migration (MIGRATION_STAGING)
- PWA kurulumu (mobil terminal için)

### Hariç
- Picking (toplama) iş akışı (ayrı proje)
- ERP entegrasyonu değişiklikleri
- Çoklu depo arası transfer
- Raf fiziksel boyut/ölçü yönetimi (palet ölçüsü vs. raf boyutu)
- Native mobil uygulama (PWA yeterli)

---

## Faz 0 — Altyapı: Veri Modeli Genişletme

> **Amaç:** Yeni entity'ler ve mevcut entity değişiklikleri ile veritabanı temelini kurmak.

### 0.1 — Zon (Bölge) Entity Oluştur
> **Durum (2026-04-06):** ✅ Tamamlandı.
> **Kısa Uygulama Notu:** `zon_mapper.py` yerine mevcut mimari nedeniyle mapper entegrasyonu `depo_envanter_mapper.py` içinde yapıldı.
> **Doğrulama:** `tests/api/routers/test_zonlar_api.py` eklendi (6/6 geçti).
> **Endpoint:** `/api/zonlar`

**Yeni dosyalar:**
- `app/core/entities/zon.py`
- `app/core/repositories/zon_repository.py`
- `app/infrastructure/persistence/repositories/sa_zon_repository.py`
- `app/infrastructure/persistence/mappers/zon_mapper.py`
- `app/application/dto/zon_dto.py`
- `app/application/use_cases/zon_use_cases.py`
- `app/api/v1/routers/zonlar.py`

**Zon Entity:**
```
Zon:
  id: int (PK)
  depo_id: int (FK → depolar.id)
  isim: str              # "Genel Stok", "Soğuk Depo", vb.
  tip: str               # ZonTipi enum: MAL_KABUL, GENEL, SOGUK, KARANTINA, SEVKIYAT
  kod: str (unique)      # "A", "B", "C" — zon kodu
  aciklama: str
  sira: int              # Görüntüleme sırası
  aktif: bool
  olusturma_tarihi: datetime
```

**ZonTipi sabitler:**
```python
class ZonTipi:
    MAL_KABUL = "MalKabul"       # Staging alanı
    GENEL = "Genel"               # Kuru genel depolama
    SOGUK = "Soguk"               # Soğuk hava deposu
    KARANTINA = "Karantina"       # Karantina bölgesi
    SEVKIYAT = "Sevkiyat"         # Sevkiyat hazırlık alanı
    TEHLIKELI = "Tehlikeli"       # Tehlikeli madde deposu
```

**İş kuralları:**
- Zon tipi → izin verilen depolama tipleri eşleştirmesi (domain logic)
- Karantina zonundan çıkış sadece admin/süpervizör onayıyla

**ORM modeli (`models.py`):**
```python
class Zon(Base):
    __tablename__ = "zonlar"
    id = Column(Integer, primary_key=True, index=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=False)
    isim = Column(String(100), nullable=False)
    tip = Column(String(30), nullable=False)  # ZonTipi
    kod = Column(String(10), unique=True, nullable=False)
    aciklama = Column(Text, default="")
    sira = Column(Integer, default=0)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    # İlişkiler
    depo = relationship("Depo", back_populates="zonlar")
    raflar = relationship("Raf", back_populates="zon")
```

---

### 0.2 — Raf Entity Genişletme
> **Durum (2026-04-07):** ✅ Tamamlandı.
> **Uygulama Notu:** `bolge` deprecated olarak bırakıldı, tüm yeni alanlar optional — eski API sözleşmesi korundu. `zon_repo` DI factory'lerine inject edildi (`RafOlusturUseCase`, `RafGuncelleUseCase`). Migration: `migrate_raf_genisletme.py` (4-parçalı eski kodlar otomatik `GNL-` prefix ile dönüştürülür).
> **Agent Notu:** `bolge` alanı backward-compat için korunmalı; `zon_id` geçişinde mevcut raf API sözleşmesi kırılmamalı.

**Değişen dosyalar:**
- `app/core/entities/raf.py`
- `app/application/dto/raf_dto.py`
- `app/application/use_cases/raf_use_cases.py`
- `models.py` (Raf ORM)

**Raf'a eklenen alanlar:**
```
zon_id: int (FK → zonlar.id)       # Hangi zona ait
max_agirlik_kg: float               # Maksimum ağırlık kapasitesi (kg)
koridor: str                         # Koridor kodu (ör: "A", "B")
kat: int                             # Kat numarası (ör: 1, 2, 3)
goz: int                             # Göz numarası (ör: 1, 2, 3)
```

**`bolge` alanı:** Geriye dönük uyumluluk için korunur, ancak yeni akışlarda `zon_id` kullanılır. `bolge` alanı deprecated olarak işaretlenir.

**Hiyerarşik Konum Kodu (Barkod Formatı):**
Raf `kod` alanı `ZON-KORIDOR-RAF-KAT-GOZ` formatında olacak (5 segment).
Örnek: `GNL-A-12-01-01` = Genel Stok zonu, A koridoru, 12. raf, 1. kat, 1. göz

```python
class Raf:
    @staticmethod
    def kod_olustur(zon_kod: str, koridor: str, raf_no: int, kat: int, goz: int) -> str:
        """Hiyerarşik raf kodu oluşturur: ZON-KORIDOR-RAF-KAT-GOZ"""
        return f"{zon_kod}-{koridor}-{raf_no:02d}-{kat:02d}-{goz:02d}"

    @staticmethod
    def kod_parse(kod: str) -> dict:
        """Raf kodunu parse eder.
        Returns: {"zon_kod": "GNL", "koridor": "A", "raf_no": 12, "kat": 1, "goz": 1}
        Raises: ValueError — geçersiz format
        """
        parcalar = kod.split("-")
        if len(parcalar) != 5:
            raise ValueError(f"Geçersiz raf kodu formatı: {kod}. Beklenen: ZON-KORIDOR-RAF-KAT-GOZ")
        return {
            "zon_kod": parcalar[0],
            "koridor": parcalar[1],
            "raf_no": int(parcalar[2]),
            "kat": int(parcalar[3]),
            "goz": int(parcalar[4]),
        }
```

**Mevcut raf kodu formatı:** `KORIDOR-RAF-KAT-GOZ` (ör: "A-12-01-01")
**Migration:** Tüm mevcut raflara `GNL-` prefix'i eklenir → "A-12-01-01" → "GNL-A-12-01-01"

**Güncellenmiş iş kuralları:**
```python
class Raf:
    def kapasite_yeterli_mi(self, mevcut_palet_sayisi: int, mevcut_agirlik_kg: float, yeni_palet_kg: float) -> KapasiteSonuc:
        """Hibrit kapasite kontrolü: hem slot hem ağırlık."""
        if mevcut_palet_sayisi >= self.kapasite:
            return KapasiteSonuc(yeterli=False, neden="Hacim Limiti Aşıldı")
        if self.max_agirlik_kg and (mevcut_agirlik_kg + yeni_palet_kg) > self.max_agirlik_kg:
            return KapasiteSonuc(yeterli=False, neden="Ağırlık Limiti Aşıldı")
        return KapasiteSonuc(yeterli=True)
```

**KapasiteSonuc value object:**
```python
@dataclass
class KapasiteSonuc:
    yeterli: bool
    neden: Optional[str] = None  # "Hacim Limiti Aşıldı" veya "Ağırlık Limiti Aşıldı"
```

---

### 0.3 — Urun Entity'ye Depolama Tipi Ekle
> **Durum (2026-04-07):** ✅ Tamamlandı.
> **Uygulama Notu:** `DepolamaTipi` sınıfı `urun.py`'da tanımlandı. `zon_uygun_mu(zon_tipi)` metodu lazy import ile `ZonTipi`'yi kullanır (circular import önlemi). DTO'larda validator eklendi; güncelleme use case `setattr` loop'u üzerinden çalışır, ayrı bir değişiklik gerekmedi. Migration: `migrate_urun_depolama_tipi.py`.
> **Agent Notu:** `depolama_tipi` varsayılanı `"Kuru"` korunmalı; legacy ürün kayıtlarıyla uyumluluk bozulmamalı.

**Değişen dosyalar:**
- `app/core/entities/urun.py`
- `app/application/dto/urun_dto.py`
- `models.py` (Urun ORM)

**Eklenen alan:**
```
depolama_tipi: str = "Kuru"   # DepolamaTipi: Kuru, Soguk, Tehlikeli
```

**DepolamaTipi sabitler:**
```python
class DepolamaTipi:
    KURU = "Kuru"
    SOGUK = "Soguk"
    TEHLIKELI = "Tehlikeli"
```

**Zon-Depolama Tipi uyumluluk matrisi (domain entity'de):**
```python
ZON_DEPOLAMA_UYUMLULUK = {
    ZonTipi.GENEL: {DepolamaTipi.KURU},
    ZonTipi.SOGUK: {DepolamaTipi.KURU, DepolamaTipi.SOGUK},
    ZonTipi.TEHLIKELI: {DepolamaTipi.TEHLIKELI},
    ZonTipi.MAL_KABUL: {DepolamaTipi.KURU, DepolamaTipi.SOGUK, DepolamaTipi.TEHLIKELI},  # Geçici
    ZonTipi.SEVKIYAT: {DepolamaTipi.KURU, DepolamaTipi.SOGUK, DepolamaTipi.TEHLIKELI},   # Geçici
    ZonTipi.KARANTINA: {DepolamaTipi.KURU, DepolamaTipi.SOGUK, DepolamaTipi.TEHLIKELI},  # Hepsi
}
```

---

### 0.4 — Yerleştirme Görevi (Putaway Task) Entity
> **Agent Notu:** Görev durum stringleri stabil tutulmalı; mevcut exception/log patterni ile ilerlenmeli.

**Yeni dosyalar:**
- `app/core/entities/yerlestirme_gorevi.py`
- `app/core/repositories/yerlestirme_gorevi_repository.py`
- `app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py`
- `app/infrastructure/persistence/mappers/yerlestirme_mapper.py`
- `app/application/dto/yerlestirme_gorevi_dto.py`
- `app/application/use_cases/yerlestirme_gorevi_use_cases.py`
- `app/api/v1/routers/yerlestirme_gorevleri.py`

**YerlestirmeGorevi Entity:**
```
YerlestirmeGorevi:
  id: int (PK)
  palet_id: int (FK → paletler.id)
  mal_kabul_irsaliye_id: Optional[int] (FK)      # Kaynak irsaliye
  tip: str                                         # GorevTipi: Yerlestirme, Transfer, BelirsizKonum
  kaynak_raf_id: Optional[int] (FK)               # Transfer görevlerinde: paletin şu anki rafı
  onerilen_raf_id: int (FK → raflar.id)           # Algoritmanın önerdiği hedef raf
  gerceklesen_raf_id: Optional[int] (FK)          # Operatörün yerleştirdiği raf
  durum: str                                       # GorevDurum
  oncelik: int                                     # 1=Acil, 5=Normal
  atanan_kullanici_id: Optional[int] (FK)         # Görevi çeken operatör
  override_kullanici_id: Optional[int] (FK)       # Süpervizör override varsa
  override_neden: Optional[str]                    # Override gerekçesi
  olusturma_tarihi: datetime
  baslama_tarihi: Optional[datetime]               # Operatör görevi çektiğinde
  tamamlanma_tarihi: Optional[datetime]
  iptal_nedeni: Optional[str]
```

**GorevTipi:**
```python
class GorevTipi:
    YERLESTIRME = "Yerlestirme"   # Mal kabul sonrası normal yerleştirme
    TRANSFER = "Transfer"          # Karantina çıkış vb. zon-arası transfer
    BELIRSIZ_KONUM = "BelirsizKonum"  # MIGRATION_STAGING'den yerleştirme
```

**GorevDurum yaşam döngüsü:**
```
BEKLIYOR → ATANDI → DEVAM_EDIYOR → TAMAMLANDI
                                  → IPTAL_EDILDI
```

**Pull-Based FIFO Kilitleme:** Operatör "Sıradaki Görevi Al" butonuna bastığında, sistem
`GorevDurum.BEKLIYOR` olan görevlerden `oncelik ASC, olusturma_tarihi ASC` sırasıyla
ilkini `SELECT ... FOR UPDATE` ile kilitler ve `ATANDI` statüsüne çeker.
Diğer operatörler aynı görevi alamaz.

```python
class GorevDurum:
    BEKLIYOR = "Bekliyor"           # Sistem oluşturdu, havuzda bekliyor
    ATANDI = "Atandi"               # Operatör çekti (kilitli)
    DEVAM_EDIYOR = "DevamEdiyor"    # Operatör paleti aldı
    TAMAMLANDI = "Tamamlandi"       # Raf okutuldu, doğrulandı, yerleştirildi
    IPTAL_EDILDI = "IptalEdildi"    # İptal (raf değişikliği, stok iadesi vb.)

    _GECISLER = {
        BEKLIYOR: {ATANDI, IPTAL_EDILDI},
        ATANDI: {DEVAM_EDIYOR, BEKLIYOR, IPTAL_EDILDI},  # BEKLIYOR = bırak
        DEVAM_EDIYOR: {TAMAMLANDI, IPTAL_EDILDI},
        TAMAMLANDI: set(),
        IPTAL_EDILDI: set(),
    }
```

**İş kuralları:**
```python
class YerlestirmeGorevi:
    def tamamla(self, gerceklesen_raf_id: int) -> None:
        """Görevi tamamlar — fiziksel yerleştirme onayı."""
        self._durum_gecisi(GorevDurum.TAMAMLANDI)
        self.gerceklesen_raf_id = gerceklesen_raf_id
        self.tamamlanma_tarihi = datetime.utcnow()

    def override_ile_tamamla(self, gerceklesen_raf_id: int, supervisor_id: int, neden: str) -> None:
        """Süpervizör override ile tamamlar (kapasite/zon kuralı ihlali)."""
        self._durum_gecisi(GorevDurum.TAMAMLANDI)
        self.gerceklesen_raf_id = gerceklesen_raf_id
        self.override_kullanici_id = supervisor_id
        self.override_neden = neden
        self.tamamlanma_tarihi = datetime.utcnow()

    def onerilen_raf_farkli_mi(self) -> bool:
        """Operatör farklı bir rafa mı yerleştirdi?"""
        return (self.gerceklesen_raf_id is not None 
                and self.gerceklesen_raf_id != self.onerilen_raf_id)
```

**ORM modeli (`models.py`):**
```python
class YerlestirmeGorevi(Base):
    __tablename__ = "yerlestirme_gorevleri"
    id = Column(Integer, primary_key=True, index=True)
    palet_id = Column(Integer, ForeignKey("paletler.id"), nullable=False)
    mal_kabul_irsaliye_id = Column(Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=True)
    tip = Column(String(20), default="Yerlestirme", nullable=False)  # GorevTipi
    kaynak_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)  # Transfer görevleri için
    onerilen_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=False)
    gerceklesen_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)
    durum = Column(String(20), default="Bekliyor", nullable=False, index=True)
    oncelik = Column(Integer, default=5, index=True)
    atanan_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    override_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    override_neden = Column(Text, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow, index=True)
    baslama_tarihi = Column(DateTime, nullable=True)
    tamamlanma_tarihi = Column(DateTime, nullable=True)
    iptal_nedeni = Column(Text, nullable=True)
    # İlişkiler
    palet = relationship("Palet")
    kaynak_raf = relationship("Raf", foreign_keys=[kaynak_raf_id])
    onerilen_raf = relationship("Raf", foreign_keys=[onerilen_raf_id])
    gerceklesen_raf = relationship("Raf", foreign_keys=[gerceklesen_raf_id])
```

**Index'ler:** `durum + oncelik + olusturma_tarihi` composite index — FIFO görev çekme sorgusunu hızlandırır.

---

### 0.5 — DB Migration Script
> **Agent Notu:** Migration script idempotent yazılmalı; model şeması ve test DB (`create_all`) tutarlılığı korunmalı.

**Yeni dosya:** `migrate_putaway_system.py`

**SQL işlemleri (sırasıyla):**
1. `CREATE TABLE zonlar` (yeni tablo)
2. `ALTER TABLE raflar ADD COLUMN zon_id INT` + FK
3. `ALTER TABLE raflar ADD COLUMN max_agirlik_kg FLOAT DEFAULT NULL`
4. `ALTER TABLE raflar ADD COLUMN koridor VARCHAR(10) DEFAULT NULL`
5. `ALTER TABLE raflar ADD COLUMN kat INT DEFAULT 1`
6. `ALTER TABLE raflar ADD COLUMN goz INT DEFAULT 1`
7. `ALTER TABLE urunler ADD COLUMN depolama_tipi VARCHAR(30) DEFAULT 'Kuru'`
8. `CREATE TABLE yerlestirme_gorevleri` (yeni tablo) + composite index (durum, oncelik, olusturma_tarihi)
9. Varsayılan zonları oluştur (her depo için):
   - `MKB` = Mal Kabul (Staging)
   - `GNL` = Genel Stok
   - `SGK` = Soğuk Depo
   - `KRN` = Karantina
   - `TEH` = Tehlikeli Madde
   - `SVK` = Sevkiyat
10. `bolge` → `zon_id` data migration: Mevcut `bolge` değerlerini en yakın zona eşle
11. Raf kodlarını hiyerarşik formata dönüştür:
    Mevcut format: `KORIDOR-RAF-KAT-GOZ` (ör: "A-12-01-01")
    Yeni format: `ZON-KORIDOR-RAF-KAT-GOZ` → `UPDATE raflar SET kod = CONCAT('GNL-', kod)`
    Ayrıca `koridor`, `kat`, `goz` alanlarını mevcut koddan parse ederek doldur
12. `MIGRATION_STAGING` sanal raf oluştur (her depo için, zon=MKB, kod="MKB-X-00-00-00")
13. `UPDATE paletler SET raf_id = <MIGRATION_STAGING_ID> WHERE raf_id IS NULL AND aktif = 1`
14. `ALTER TABLE paletler MODIFY raf_id INT NOT NULL` (artık zorunlu)

---

## Faz 1 — Domain Servisleri
> **Agent Notu:** Domain servisleri pure kalmalı; DB erişimi sadece repository katmanından yapılmalı.

> **Amaç:** Yerleştirme algoritması ve doğrulama servislerini oluşturmak.

### 1.1 — Zon Uyumluluk Servisi

**Yeni dosya:** `app/core/services/zon_uyumluluk_servisi.py`

```python
class ZonUyumlulukServisi:
    """Ürün depolama tipi ile zon tipi uyumluluğunu doğrular."""

    def uyumlu_mu(self, depolama_tipi: str, zon_tipi: str) -> bool:
        """Ürünün bu zona yerleştirilip yerleştirilemeyeceğini kontrol eder."""

    def uyumlu_zonlari_getir(self, depo_id: int, depolama_tipi: str) -> List[Zon]:
        """Ürün tipiyle uyumlu tüm zonları döner."""
```

### 1.2 — Kapasite Doğrulama Servisi

**Yeni dosya:** `app/core/services/kapasite_dogrulama_servisi.py`

```python
class KapasiteDogrulamaServisi:
    """Rafın hibrit kapasitesini (slot + ağırlık) doğrular."""

    def __init__(self, palet_repo: IPaletRepository):
        self._palet_repo = palet_repo

    def dogrula(self, raf: Raf, yeni_palet_kg: float) -> KapasiteSonuc:
        """Rafın yeni paleti kabul edip edemeyeceğini kontrol eder."""
        mevcut_paletler = self._palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True)
        mevcut_palet_sayisi = len(mevcut_paletler)
        mevcut_agirlik = sum(p.palet_kg or 0 for p in mevcut_paletler)
        return raf.kapasite_yeterli_mi(mevcut_palet_sayisi, mevcut_agirlik, yeni_palet_kg)

    def alternatif_raflar_getir(self, zon_id: int, palet_kg: float, limit: int = 5) -> List[Raf]:
        """Kapasitesi yeterli alternatif rafları önerir."""
```

### 1.3 — Yerleştirme Algoritması (Putaway Algorithm)

**Yeni dosya:** `app/core/services/yerlestirme_algoritmasi.py`

```python
class YerlestirmeAlgoritmasi:
    """WMS endüstri standardı yerleştirme algoritması.

    Karar hiyerarşisi:
      1. Uygunluk: Ürün depolama tipi ⊂ Zon izin verilen tipler
      2. Kapasite: Raf slot + ağırlık kapasitesi yeterli mi
      3. Verimlilik:
         a) Aynı ürün olan rafa yakın (konsolidasyon)
         b) FIFO: Son kullanma tarihine göre sıralı yerleştirme
         c) Doluluk: En boş rafa değil, en dolu ama hâlâ uygun rafa (boşluk konsolidasyonu)
    """

    def __init__(
        self,
        raf_repo: IRafRepository,
        zon_repo: IZonRepository,
        palet_repo: IPaletRepository,
        zon_uyumluluk: ZonUyumlulukServisi,
        kapasite_dogrulama: KapasiteDogrulamaServisi,
    ): ...

    def raf_oner(self, palet: Palet, urun: Urun, depo_id: int) -> YerlestirmeOnerisi:
        """Palet için en uygun rafı önerir.

        Returns:
            YerlestirmeOnerisi: onerilen_raf, skor, alternatifler, gerekce
        """

    def _skorla(self, raf: Raf, urun: Urun, palet: Palet) -> float:
        """Her raf için 0-100 arası skor hesaplar.

        Ağırlıklar:
        - Aynı ürün konsolidasyonu: %40
        - Doluluk oranı (yüksek = iyi): %30
        - FIFO uyumu: %20
        - Zon önceliği: %10
        """
```

**YerlestirmeOnerisi value object:**
```python
@dataclass
class YerlestirmeOnerisi:
    onerilen_raf: Raf
    skor: float                        # 0-100
    alternatifler: List[Raf]           # Top 3 alternatif
    gerekce: str                       # "Aynı üründen 5 palet mevcut, %72 dolu"
```

---

## Faz 2 — İş Akışı Entegrasyonu
> **Agent Notu:** İş akışında tek transaction sınırı korunmalı; parçalı commit yapılmamalı.

> **Amaç:** İrsaliye onayından fiziksel yerleştirmeye kadar uçtan uca akışı kurmak.

### 2.1 — İrsaliye Onay → Palet + Görev Oluşturma

**Değişen dosya:** `app/application/use_cases/mal_kabul_irsaliye_use_cases.py`

**Yeni use case:** `IrsaliyeOnaylaVeGorevOlusturUseCase`

```
Tetiklenme: İrsaliye durumu Taslak → Onaylandi geçişi

Akış:
  1. İrsaliye doğrulama (mevcut onayla() mantığı)
  2. Her MalKabulKalemi için:
     a. Lot bul veya oluştur (lot_no + urun_id + tarihler)
     b. Palet oluştur (palet_no, lot_id, koli_adedi, palet_kg)
     c. Palet'in raf_id = MIGRATION_STAGING (geçici — henüz yerleştirilmedi)
     d. StokHareketi oluştur (giris)
     e. Yerleştirme Algoritması çalıştır → önerilen raf
     f. YerlestirmeGorevi oluştur (palet_id, onerilen_raf_id, durum=BEKLIYOR)
     g. Kalem durumunu GirisYapildi olarak işaretle
  3. Atomik transaction: hepsi başarılı olmalı
  4. SistemLog yaz

Sonuç: N adet kalem → N adet palet + N adet yerleştirme görevi
```

**Not:** Mevcut `PaletGirisService.palet_giris()` mantığı büyük ölçüde tekrar kullanılacak. Fark: raf_id artık STAGING'e atanıyor ve ayrıca bir YerlestirmeGorevi oluşturuluyor.

---

### 2.2 — Fiziksel Yerleştirme Onayı (Putaway Confirmation)

**Yeni use case:** `YerlestirmeOnayla UseCase`

```
Tetiklenme: Operatör el terminalinden raf barkodu okuttuğunda

Girdi: gorev_id, okutulan_raf_kodu, kullanici_id

Akış:
  1. Görevi getir, durum kontrolü (ATANDI veya DEVAM_EDIYOR olmalı)
  2. Okutulan raf kodundan raf bul
  3. Doğrulama katmanı:
     a. Zon uyumluluk kontrolü (ürün tipi ↔ zon tipi)
     b. Kapasite kontrolü (slot + ağırlık)
  4a. Doğrulama BAŞARILI:
      - Palet.raf_id = okutulan raf
      - Görev.gerceklesen_raf_id = okutulan raf
      - Görev.durum = TAMAMLANDI
      - SistemLog yaz
  4b. Doğrulama BAŞARISIZ:
      - Hata döndür: "Kapasite Yetersiz: [Hacim/Ağırlık] Limiti Aşıldı"
                     veya "Zon Uyumsuzluğu: [Soğuk] ürün [Genel] zona yerleştirilemez"
      - Frontend'de alternatif raf öner veya süpervizör override seçeneği sun
  5. Önerilen raf ≠ okutulan raf ise → farkı logla (analiz için)
```

### 2.3 — Süpervizör Override

**Yeni use case:** `SupervizorOverrideUseCase`

```
Tetiklenme: Operatör doğrulama hatası aldığında "Süpervizör Onayı İste" butonuna basar

Girdi: gorev_id, hedef_raf_id, supervisor_kullanici_id, neden

Akış:
  1. Kullanıcı rolü kontrolü: admin veya supervisor rolü gerekli
  2. Doğrulama atlanarak (bypass) görev tamamlanır
  3. override_kullanici_id ve override_neden kaydedilir
  4. SistemLog'a UYARI seviyesinde override kaydı yazılır
  5. Palet.raf_id güncellenir
```

### 2.4 — Konumu Belirsiz Paletleri Yerleştirme

**Yeni use case:** `BilinmeyenKonumGorevleriOlusturUseCase`

```
Tetiklenme: Migration sonrası veya manuel tetikleme

Akış:
  1. MIGRATION_STAGING raftaki tüm aktif paletleri getir
  2. Her biri için YerlestirmeAlgoritmasi çalıştır
  3. YerlestirmeGorevi oluştur (oncelik=1, yüksek öncelikli)
  4. Operatör listesinde "Konumu Belirsiz Paletleri Yerleştir" başlığıyla göster
```

### 2.5 — Karantina Çıkış Akışı (Transfer Görevi)

**Yeni use case:** `KarantinadanCikarUseCase`

```
Tetiklenme: Admin/QC kullanıcısı paleti "Karantinadan Çıkar" butonuna basar

Girdi: palet_id, onaylayan_kullanici_id

Ön koşul: Palet aktif ve karantina zonundaki bir rafta olmalı

Akış:
  1. Palet ve raf doğrulama: raf.zon.tip == KARANTINA olmalı
  2. Kullanıcı yetki kontrolü: admin rolü gerekli
  3. YerlestirmeAlgoritmasi çalıştır → ürün tipine uygun normal stok rafı öner
  4. YerlestirmeGorevi oluştur:
     - tip = TRANSFER
     - kaynak_raf_id = palet'in mevcut raf_id (karantina rafı)
     - onerilen_raf_id = algoritmanın önerdiği hedef raf
     - oncelik = 2 (yüksek — karantina çıkışı önemli)
  5. SistemLog yaz: "Karantinadan çıkış onayı: {palet_no}, onaylayan: {kullanici}"
  6. Operatör mobil terminalden Transfer Görevini alır → paleti karantinadan alır → hedef rafa yerleştirir
  7. Yerleştirme tamamlandığında palet.raf_id güncellenir

**Karantinaya Alma (ters yön):**

**Yeni use case:** `KarantinayaAlUseCase`

```
Tetiklenme: Admin paleti "Karantinaya Al" butonuna basar

Girdi: palet_id, neden (zorunlu), onaylayan_kullanici_id

Akış:
  1. Palet doğrulama: aktif olmalı, zaten karantinada olmamalı
  2. Kullanıcı yetki kontrolü: admin rolü gerekli
  3. Karantina zonundaki uygun rafı bul (KapasiteDogrulamaServisi)
  4. YerlestirmeGorevi oluştur:
     - tip = TRANSFER
     - kaynak_raf_id = palet'in mevcut raf_id
     - onerilen_raf_id = karantina rafı
     - oncelik = 1 (en yüksek — karantina acil)
  5. SistemLog: "Karantinaya alma: {palet_no}, neden: {neden}"
  6. Operatör terminalde Transfer Görevini alır → paleti mevcut raftan alır → karantina rafına yerleştirir
```
```

### 2.6 — Sevkiyat Kısıtlaması

**Değişen dosya:** `app/core/services/palet_cikis_service.py`

```
Kural: MIGRATION_STAGING raftaki paletlerin sevkiyatına izin verilmez.

Kontrol noktası: palet_cikis() metodu içinde
  if palet.raf_id == MIGRATION_STAGING_RAF_ID:
      raise GecersizIslemError("Konumu belirsiz palet sevk edilemez. Önce yerleştirme yapılmalı.")
```

---

## Faz 3 — API Endpoints
> **Agent Notu:** Router standardı `/api/<çoğul>` + `require_role(...)` + rate-limit dekoratörü korunmalı.

> **Amaç:** Mobil terminal ve web yönetim paneli için gerekli API'leri sunmak.

### 3.1 — Zon Yönetimi (Admin)

**Yeni router:** `app/api/v1/routers/zonlar.py`

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| GET | `/api/zonlar/` | Zon listele (depo_id filter) | Tüm roller |
| GET | `/api/zonlar/{zon_id}` | Zon detay | Tüm roller |
| POST | `/api/zonlar/` | Zon oluştur | admin |
| PUT | `/api/zonlar/{zon_id}` | Zon güncelle | admin |
| DELETE | `/api/zonlar/{zon_id}` | Zon sil (soft) | admin |

### 3.2 — Yerleştirme Görevleri

**Yeni router:** `app/api/v1/routers/yerlestirme_gorevleri.py`

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| GET | `/api/yerlestirme-gorevleri/` | Görev listele (filtreli) | Tüm roller |
| GET | `/api/yerlestirme-gorevleri/{id}` | Görev detay | Tüm roller |
| GET | `/api/yerlestirme-gorevleri/bekleyen` | Havuzdaki bekleyen görev sayısı/özet | depocu |
| POST | `/api/yerlestirme-gorevleri/siradaki-al` | FIFO sırasına göre sonraki görevi çek + kilitle | depocu |
| POST | `/api/yerlestirme-gorevleri/{id}/birak` | Çekilen görevi bırak (ATANDI→BEKLIYOR) | depocu |
| POST | `/api/yerlestirme-gorevleri/{id}/baslat` | Görevi başlat (paleti aldı) | depocu |
| POST | `/api/yerlestirme-gorevleri/{id}/tamamla` | Görevi tamamla (raf scan) | depocu |
| POST | `/api/yerlestirme-gorevleri/{id}/iptal` | Görevi iptal et | admin |
| POST | `/api/yerlestirme-gorevleri/{id}/override` | Süpervizör override | admin |
| POST | `/api/yerlestirme-gorevleri/karantinadan-cikar` | Karantina çıkış → transfer görevi oluştur | admin |
| POST | `/api/yerlestirme-gorevleri/karantinaya-al` | Karantinaya alma → transfer görevi oluştur | admin |

### 3.3 — Mobil Terminal Scan Endpoints

**Yeni router:** `app/api/v1/routers/mobil_terminal.py`

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| POST | `/api/terminal/scan/palet` | Palet barkodu okut → bilgi getir | depocu |
| POST | `/api/terminal/scan/raf` | Raf barkodu okut → doğrulama yap | depocu |
| POST | `/api/terminal/yerlestir` | Scan-to-verify yerleştirme | depocu |
| GET | `/api/terminal/gorevlerim` | Operatörün aktif görevleri | depocu |
| GET | `/api/terminal/ozet` | Günlük özet (tamamlanan, bekleyen) | depocu |
| POST | `/api/terminal/alternatif-raf` | Kapasite hatası sonrası alternatif raf öner | depocu |

**`POST /api/terminal/yerlestir` — Ana yerleştirme akışı:**
```json
// Request
{
  "gorev_id": 42,
  "palet_barkod": "PLT-2026-00123",
  "raf_barkod": "GNL-A-12-03-01"
}

// Response (başarılı)
{
  "durum": "TAMAMLANDI",
  "palet_no": "PLT-2026-00123",
  "raf_kod": "GNL-A-12-03-01",
  "zon": "Genel Stok",
  "onerilen_raf_kod": "GNL-A-12-01-01",  // farklıysa göster
  "mesaj": "Palet başarıyla yerleştirildi."
}

// Response (hata)
{
  "durum": "DOGRULAMA_HATASI",
  "hata_tipi": "KAPASITE_YETERSIZ",
  "mesaj": "Kapasite Yetersiz: Hacim Limiti Aşıldı (8/8 palet)",
  "alternatifler": [
    {"raf_kod": "GNL-A-12-05-01", "bos_slot": 3, "skor": 85},
    {"raf_kod": "GNL-A-13-01-01", "bos_slot": 6, "skor": 72}
  ],
  "override_gerekli": true
}
```

### 3.4 — Raporlama Ek Endpoint'leri

**Değişen dosya:** `app/api/v1/routers/` (mevcut rapor router'a eklenecek)

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/rapor/depo-doluluk` | Depo/zon/raf bazlı doluluk raporu |
| GET | `/api/rapor/yerlestirme-performans` | Ortalama yerleştirme süresi, override oranı |
| GET | `/api/rapor/bilinmeyen-konum` | MIGRATION_STAGING'deki palet sayısı |

**Doluluk raporu uyarı:**
```json
{
  "uyari": "Geçici Veri İçeriyor",
  "bilinmeyen_konum_palet_sayisi": 23,
  "mesaj": "23 palet henüz konumlandırılmamış. Doluluk oranları kesin değildir."
}
```

---

## Faz 4 — Frontend: Mobil Terminal UI
> **Agent Notu:** Terminal akışı ayrı route grubu ile eklenmeli; mevcut web panel route yapısı bozulmamalı.

> **Amaç:** Saha operatörleri için scan-to-verify iş akışını sunan mobil-optimized PWA arayüzü.

### 4.1 — PWA Kurulumu

**Yeni/değişen dosyalar:**
- `ReactProje/public/manifest.json` — PWA manifest
- `ReactProje/public/sw.js` veya `vite-plugin-pwa` entegrasyonu
- `ReactProje/index.html` — PWA meta tags
- `ReactProje/vite.config.js` — PWA plugin ekleme

**PWA özellikleri:**
- Homescreen'e eklenebilir (Add to Home Screen)
- Fullscreen/standalone mode
- Offline fallback sayfası (sadece "Bağlantı yok" mesajı — çevrimdışı operasyon kapsam dışı)
- Push notification altyapısı (gelecek için)

### 4.2 — Mobil Terminal Layout

**Yeni dosya:** `ReactProje/src/components/layout/TerminalLayout.jsx`

```
Özellikler:
- Tam ekran (sidebar yok, header minimal)
- Alt navigasyon çubuğu (Görevlerim, Scan, Özet)
- Büyük dokunmatik butonlar (min 48x48px)
- Yüksek kontrast renkler (depo ortamı için)
- Landscape + Portrait desteği
```

### 4.3 — Terminal Sayfaları

**Yeni dosyalar:**

| Dosya | Sayfa | Açıklama |
|-------|-------|----------|
| `pages/terminal/GorevListesiPage.jsx` | Görevlerim | Bekleyen yerleştirme görevleri listesi |
| `pages/terminal/YerlestirmePage.jsx` | Yerleştirme | Ana scan-to-verify akışı |
| `pages/terminal/TerminalOzetPage.jsx` | Özet | Günlük istatistikler |

### 4.4 — Yerleştirme Sayfası (Ana Akış)

**`YerlestirmePage.jsx` — Adım adım akış:**

```
┌─────────────────────────────────────┐
│ ADIM 1: Sıradaki Görevi Al          │
│                                     │
│ Havuzda bekleyen: 12 görev          │
│                                     │
│    [SIRADAKI GÖREVİ AL]            │
│                                     │
│ ─── Görev atandı: ──────────────── │
│ ┌─────────────────────────────────┐ │
│ │ 📦 PLT-2026-00123              │ │
│ │ Tip: Yerleştirme                │ │
│ │ Ürün: Çikolata 100g            │ │
│ │ Miktar: 48 koli                │ │
│ │ Hedef Raf: GNL-A-12-03-01            │ │
│ │   [BAŞLAT]        [BIRAK]      │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ADIM 2: Paleti Tara / Doğrula       │
│                                     │
│     ┌───────────────────┐           │
│     │   📷 KAMERA       │           │
│     │   Palet barkodunu │           │
│     │   okutun          │           │
│     └───────────────────┘           │
│                                     │
│ Beklenen: PLT-2026-00123           │
│ [Manuel Giriş]                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ADIM 3: Rafa Yerleştir              │
│                                     │
│ Önerilen Raf: GNL-A-12-01-01          │
│ Zon: Genel Stok                     │
│                                     │
│     ┌───────────────────┐           │
│     │   📷 KAMERA       │           │
│     │   Raf barkodunu   │           │
│     │   okutun          │           │
│     └───────────────────┘           │
│                                     │
│ [Manuel Giriş]                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ADIM 4: Sonuç                       │
│                                     │
│   ✓ Yerleştirme Tamamlandı          │
│                                     │
│ Palet: PLT-2026-00123              │
│ Raf: GNL-A-12-01-01 (Genel Stok)      │
│                                     │
│ [Sonraki Görev] [Görev Listesine]   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ HATA DURUMU: Doğrulama Başarısız    │
│                                     │
│ ⚠ Kapasite Yetersiz:               │
│   Hacim Limiti Aşıldı (8/8 palet)  │
│                                     │
│ Alternatif Raflar:                  │
│ ┌─────────────────────────────────┐ │
│ │ GNL-A-12-05-01 | 3 boş slot | %85     │ │
│ │ GNL-A-13-01-01 | 6 boş slot | %72     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Alternatif Seç] [Süpervizör Çağır] │
└─────────────────────────────────────┘
```

### 4.5 — Web Yönetim Paneli Değişiklikleri

**Değişen dosyalar:**
- `pages/DepolarPage.jsx` — Zon yönetimi tab'ı ekle
- `pages/PaletlerPage.jsx` — Konum bilgisi sütunu (zon + raf)
- `pages/DashboardPage.jsx` — Yerleştirme istatistikleri widget'ı

**Yeni dosyalar:**
- `pages/ZonlarPage.jsx` — Zon CRUD sayfası (admin)
- `pages/YerlestirmeGorevleriPage.jsx` — Görev takip sayfası (admin)

### 4.6 — Routing Güncellemesi

**Değişen dosya:** `App.jsx`

```jsx
// Mobil Terminal Routes (TerminalLayout)
/terminal/gorevler          → GorevListesiPage
/terminal/yerlestirme       → YerlestirmePage
/terminal/yerlestirme/:id   → YerlestirmePage (belirli görev)
/terminal/ozet              → TerminalOzetPage

// Web Admin Routes (DashboardLayout)
/zonlar                     → ZonlarPage (admin)
/yerlestirme-gorevleri      → YerlestirmeGorevleriPage (admin)
```

---

## Faz 5 — Test & Doğrulama
> **Agent Notu:** Her fazda önce dar kapsam test, sonra kritik regresyon (depo/raf/palet) çalıştırılmalı.

### 5.1 — Unit Testler

| Test | Kapsam |
|------|--------|
| `test_zon_uyumluluk.py` | Tüm depolama tipi ↔ zon tipi kombinasyonları |
| `test_kapasite_dogrulama.py` | Slot aşımı, ağırlık aşımı, her ikisi, sınır değerler |
| `test_yerlestirme_algoritmasi.py` | Skor hesaplama, konsolidasyon, FIFO sıralaması |
| `test_gorev_durum_gecisleri.py` | Tüm geçerli/geçersiz durum geçişleri |
| `test_irsaliye_onay_akisi.py` | Onay → palet + görev oluşturma atomikliği |

### 5.2 — Entegrasyon Testleri

| Test | Kapsam |
|------|--------|
| Uçtan uca yerleştirme | İrsaliye oluştur → onayla → görev al → scan → tamamla |
| Override akışı | Kapasite hatası → süpervizör onay → yerleştirme |
| Legacy migration | STAGING paletler → görev oluşturma → yerleştirme |
| Sevkiyat kısıtlama | STAGING paleti sevk etmeye çalış → hata |

### 5.3 — Mobil Test Senaryoları

| Senaryo | Beklenen |
|---------|----------|
| Palet barkodu okut | Doğru görev eşleşmesi |
| Önerilen rafa okut | Direkt tamamlanma |
| Farklı geçerli rafa okut | Doğrulama → tamamlanma |
| Dolu rafa okut | Hata + alternatif öneri |
| Yanlış zon rafa okut | Hata (zon uyumsuzluğu) |
| Kamera erişimi yok | Manuel giriş fallback |

---

## Uygulama Sırası (Bağımlılık Grafiği)

```
Faz 0.1 (Zon Entity)
  ↓
Faz 0.2 (Raf genişletme) ← 0.1'e bağlı (zon_id FK)
  ↓
Faz 0.3 (Urun depolama_tipi) — bağımsız, paralel yapılabilir
  ↓
Faz 0.4 (YerlestirmeGorevi Entity) ← 0.2'ye bağlı
  ↓
Faz 0.5 (Migration Script) ← 0.1-0.4 tamamlandıktan sonra
  ↓
Faz 1.1 (Zon Uyumluluk) ← 0.1 + 0.3
Faz 1.2 (Kapasite Doğrulama) ← 0.2
Faz 1.3 (Yerleştirme Algoritması) ← 1.1 + 1.2
  ↓
Faz 2.1 (İrsaliye Onay Akışı) ← 1.3
Faz 2.2 (Fiziksel Yerleştirme) ← 1.1 + 1.2
Faz 2.3 (Override) ← 2.2
Faz 2.4 (Legacy Görevler) ← 1.3 + 0.5
Faz 2.5 (Karantina Çıkış / Transfer) ← 1.3 + 2.2
Faz 2.6 (Sevkiyat Kısıtlama) ← 0.5
  ↓
Faz 3.1-3.4 (API Endpoints) ← Faz 2 tamamlandıktan sonra
  ↓
Faz 4.1 (PWA) — bağımsız, erken başlanabilir
Faz 4.2-4.5 (Terminal UI) ← Faz 3 + 4.1
Faz 4.6 (Routing) ← 4.2-4.5
  ↓
Faz 5 (Test) — her faz sonrası kendi testleri yazılır
```

---

## Tahmini Dosya Listesi

### Yeni Dosyalar (~25 dosya)

**Backend (17):**
1. `app/core/entities/zon.py`
2. `app/core/entities/yerlestirme_gorevi.py`
3. `app/core/repositories/zon_repository.py`
4. `app/core/repositories/yerlestirme_gorevi_repository.py`
5. `app/core/services/zon_uyumluluk_servisi.py`
6. `app/core/services/kapasite_dogrulama_servisi.py`
7. `app/core/services/yerlestirme_algoritmasi.py`
8. `app/infrastructure/persistence/repositories/sa_zon_repository.py`
9. `app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py`
10. `app/infrastructure/persistence/mappers/zon_mapper.py`
11. `app/infrastructure/persistence/mappers/yerlestirme_mapper.py`
12. `app/application/dto/zon_dto.py`
13. `app/application/dto/yerlestirme_gorevi_dto.py`
14. `app/application/use_cases/zon_use_cases.py`
15. `app/application/use_cases/yerlestirme_gorevi_use_cases.py`
16. `app/api/v1/routers/zonlar.py`
17. `app/api/v1/routers/yerlestirme_gorevleri.py`
18. `app/api/v1/routers/mobil_terminal.py`
19. `migrate_putaway_system.py`

**Frontend (8):**
20. `src/components/layout/TerminalLayout.jsx`
21. `src/pages/terminal/GorevListesiPage.jsx`
22. `src/pages/terminal/YerlestirmePage.jsx`
23. `src/pages/terminal/TerminalOzetPage.jsx`
24. `src/pages/ZonlarPage.jsx`
25. `src/pages/YerlestirmeGorevleriPage.jsx`
26. `public/manifest.json`

### Değişen Dosyalar (~20 dosya)

**Backend:**
- `models.py` — Zon + YerlestirmeGorevi ORM + Raf/Palet/Urun alan değişiklikleri
- `app/core/entities/raf.py` — zon_id, max_agirlik_kg, KapasiteSonuc
- `app/core/entities/palet.py` — raf_id artık zorunlu
- `app/core/entities/urun.py` — depolama_tipi
- `app/core/entities/__init__.py` — yeni entity export'lar
- `app/core/repositories/__init__.py` — yeni repo export'lar
- `app/core/services/__init__.py` — yeni servis export'lar
- `app/application/dto/raf_dto.py` — zon_id, max_agirlik_kg
- `app/application/dto/urun_dto.py` — depolama_tipi
- `app/application/use_cases/mal_kabul_irsaliye_use_cases.py` — onay akışı
- `app/core/services/palet_cikis_service.py` — STAGING kısıtlama
- `app/infrastructure/di/modules/depo_envanter_di.py` — yeni DI factory'ler
- `app/api/v1/routers/__init__.py` — yeni router export'lar
- `main.py` — yeni router'ları kaydet

**Frontend:**
- `App.jsx` — terminal route'ları
- `services/api.js` — yeni endpoint'ler
- `pages/DepolarPage.jsx` — zon tab
- `pages/PaletlerPage.jsx` — konum sütunu
- `pages/DashboardPage.jsx` — yerleştirme widget
- `vite.config.js` — PWA plugin
- `index.html` — PWA meta tags

---

## Kesinleşen Kararlar (Eski "Açık Sorular")

### Karar 1 — Operatör Atama: Pull-Based + FIFO Kilitleme
Operatör listeden seçmez, **"Sıradaki Görevi Al"** butonuyla sistemin belirlediği öncelik sırasına göre (FIFO Task Queue) bir sonraki görevi çeker. Görev alındığında `ATANDI` statüsüne geçer ve diğer operatörler için **kilitlenir** (pessimistic lock).

### Karar 2 — Karantina Çıkış: Statü Değişimi + Transfer Görevi
Admin/QC onayı ile palet statüsü `Karantina → Kullanılabilir` olarak değiştirilir. Bu işlem otomatik olarak bir **Transfer Görevi** (YerlestirmeGorevi, tip=TRANSFER) tetikler. Operatör paleti karantina zonundan alıp sistemin önerdiği normal stok rafına yerleştirir.

### Karar 3 — Raf Barkod Formatı: Hiyerarşik Konum Kodu
Raf kodları `ZON-KORIDOR-RAF-KAT-GOZ` formatında olacak (ör: `GNL-A-12-01-01`). Sistem okutma sırasında bu kodu parse edip zon/koridor/raf/kat/göz doğrulaması yapacak. Mevcut kodlar migration sırasında `GNL-` prefix'i eklenerek yeni formata dönüştürülecek.