# Üretim Paleti Giriş Sistemi - Revize Analiz Raporu (v2)

**Özet:** Mevcut `Palet` entity'si genişletilerek tek canonical model korunacak; stok artışı depo kabulü anında gerçekleşecek; tam state machine ile operasyonel yaşam döngüsü yönetilecektir.

---

## 1. Mimari Kararlar (Onaylanmış)

| Karar | Seçenek | Gerekçe |
|-------|---------|---------|
| **Palet Modeli** | Mevcut `Palet` genişletme | Tek canonical model, basit migration |
| **Stok Tetikleyici** | Depo kabulü (okutma) | Fiziksel doğrulama, WMS güvenliği |
| **State Machine** | Tam (7 durum) | Gerçek operasyon senaryoları, karantina/iptal desteği |

### 1.1. State Machine Durumları

```
OLUSTURULDU → KABUL_BEKLIYOR → KABUL_EDILDI → YERLESTIRME_BEKLIYOR → YERLESTIRILDI
                    ↓                    ↓
              IPTAL_EDILDI           KARANTINA
```

### 1.2. Stok Etkisi Durumlarına Göre

| Durum | Stokta | Kullanılabilir |
|-------|--------|----------------|
| `KABUL_EDILDI` | ✅ Evet | ✅ Evet |
| `YERLESTIRILDI` | ✅ Evet | ✅ Evet |
| `KARANTINA` | ✅ Evet | ❌ Hayır |
| `IPTAL_EDILDI` | ❌ Hayır | ❌ Hayır |

---

## 2. Canonical Palet Modeli (Genişletilmiş)

### 2.1. Terminoloji Standardı

| Terim | Format | Örnek |
|-------|--------|-------|
| **Palet No** | `PRD-YYYYMMDD-NNNN` | `PRD-20250416-0001` |
| **Lot No** | `LOT-YYYYMMDD-NNNN-V` | `LOT-20250416-001-A` |
| **Kaynak** | `uretim`, `irsaliye`, `erp`, `manuel` | `uretim` |
| **Durum** | `KABUL_EDILDI`, `KARANTINA`, ... | `YERLESTIRILDI` |

### 2.2. Veritabanı Şema Güncellemesi

```sql
-- Yeni alanlar (nullable başlayıp sonra NOT NULL)
ALTER TABLE paletler ADD COLUMN kaynak VARCHAR(20) DEFAULT 'manuel';
ALTER TABLE paletler ADD COLUMN durum VARCHAR(30) DEFAULT 'OLUSTURULDU';
ALTER TABLE paletler ADD COLUMN uretim_tarihi DATE;
ALTER TABLE paletler ADD COLUMN lot_no VARCHAR(30);

-- Audit alanları
ALTER TABLE paletler ADD COLUMN kabul_eden_kullanici_id INTEGER;
ALTER TABLE paletler ADD COLUMN kabul_tarihi TIMESTAMP;
ALTER TABLE paletler ADD COLUMN iptal_sebebi VARCHAR(255);

-- Seri numara sayaç (transaction güvenli)
CREATE TABLE uretim_seri_sayac (
    tarih DATE PRIMARY KEY,
    son_seri_no INTEGER DEFAULT 0 NOT NULL
);

-- Durum geçiş logu
CREATE TABLE palet_durum_log (
    id SERIAL PRIMARY KEY,
    palet_id INTEGER REFERENCES paletler(id),
    eski_durum VARCHAR(30),
    yeni_durum VARCHAR(30) NOT NULL,
    degistiren_kullanici_id INTEGER,
    degisim_tarihi TIMESTAMP DEFAULT NOW(),
    sebep VARCHAR(255)
);
```

---

## 3. İş Kuralları (Özet)

### 3.1. Seri Numara Üretimi (Transaction Güvenli)

```python
# SELECT FOR UPDATE + UNIQUE constraint ile race condition önlenir
# Transaction rollback durumunda sayaç geri alınmaz (gap kabul edilir)
def uret_seri_no(tarih: date) -> str:
    with transaction():
        mevcut = db.execute(
            "SELECT son_seri_no FROM uretim_seri_sayac WHERE tarih = ? FOR UPDATE"
        ).fetchone()
        yeni_seri = (mevcut.son_seri_no + 1) if mevcut else 1
        return f"PRD-{tarih.strftime('%Y%m%d')}-{yeni_seri:04d}"
```

### 3.2. Çift Giriş Kontrolü

| Senaryo | Durum | Sonuç |
|---------|-------|-------|
| Zaten kabul edilmiş | `KABUL_EDILDI` | ❌ Red: "zaten kabul edilmiş" |
| İptal edilmiş | `IPTAL_EDILDI` | ❌ Red: "yeniden etiket gerekir" |
| Karantinada | `KARANTINA` | ⚠️ Yetkili kullanıcı onaylı geçiş |

### 3.3. Yetki Matrisi

| İşlem | depocu | admin | kalite |
|-------|--------|-------|--------|
| Depo kabulü (okutma) | ✅ | ✅ | ❌ |
| Karantina başlatma | ✅ | ✅ | ✅ |
| İptal işlemi | ❌ | ✅ | ❌ |
| Lot override | ❌ | ✅ | ❌ |

---

## 4. Barkod ve Etiket Standardı

### 4.1. Barkod Formatları

| Tip | Standart | İçerik |
|-----|----------|--------|
| **1D** | Code 128 | `PRD-20250416-0001` |
| **2D** | Data Matrix | JSON: `{"pn":"PRD-...","lot":"LOT-..."}` |

### 4.2. Etiket Alanları (Zebra ZPL)

```zpl
^XA
^CF0,30
^FO20,20^FDURETIM PALETI^FS
^CF0,60
^FO20,60^FDPRD-20250416-0001^FS      ; Palet No (büyük)
^BY3,2,100
^FO20,130^BC^FDPRD-20250416-0001^FS   ; Barkod
^CF0,25
^FO20,250^FDUrun: ELMA JUICE 1L^FS
^FO20,280^FDLot: LOT-20250416-001-A^FS
^FO20,310^FDSKT: 2026-04-16^FS
^FO20,340^FDKoli: 48 adet^FS
^FO20,370^FDVardiya: A^FS
^FO400,370^FDKabul Bekliyor^FS        ; Durum
^XZ
```

### 4.3. Yeniden Baskı Kuralları

| Senaryo | İzin | Log |
|---------|------|-----|
| Etiket hasar/zayi | ✅ Evet | `YENIDEN_BASIM` |
| Bilgi değişikliği | ❌ Hayır | Yeni palet oluştur |

---

## 5. Implementasyon Fazları

### FAZ 1: Domain Kuralları
- [ ] State machine durumları tanımla
- [ ] İş kuralları dokümantasyonu
- [ ] Terminoloji standardı

### FAZ 2: Veri Modeli
- [ ] `Palet` entity güncelle
- [ ] Migration scriptleri
- [ ] Seri sayaç ve audit tabloları

### FAZ 3: Servis Katmanı
- [ ] `UretimPaletService` (domain)
- [ ] `UretimSeriNoUretici` (transaction-güvenli)
- [ ] Adaptör implementasyonu

### FAZ 4: API/UI
- [ ] Backend endpoints
- [ ] Frontend ekranları
- [ ] Barkod entegrasyonu

### FAZ 5: Test ve Rollout
- [ ] Concurrency testleri
- [ ] Yetki testleri
- [ ] Migration ve deploy

---

## 6. Test Senaryoları (Somut)

| ID | Senaryo | Beklenen |
|----|---------|----------|
| TC-001 | 10 thread seri no üretimi | 10 unique numara, çakışma yok |
| TC-002 | Aynı palet 2 kez okutma | 2. reddedilir |
| TC-003 | İptal edilmiş palet okutma | "yeniden etiket" mesajı |
| TC-004 | Stoklu palet iptali | Stok düşümü + çıkış hareketi |
| TC-005 | Karantina → Kabul (yetkili) | Başarılı geçiş |
| TC-006 | Karantina → Kabul (yetkisiz) | Red: "kalite onayı gerekli" |

---

## 7. Migration Stratejisi

```sql
-- Aşama 1: Nullable ekle (forward compatible)
ALTER TABLE paletler ADD COLUMN kaynak VARCHAR(20) DEFAULT 'irsaliye';
ALTER TABLE paletler ADD COLUMN durum VARCHAR(30) DEFAULT 'YERLESTIRILDI';

-- Aşama 2: Constraint (deploy sonrası)
ALTER TABLE paletler ALTER COLUMN kaynak SET NOT NULL;
ALTER TABLE paletler ADD CONSTRAINT chk_kaynak 
    CHECK (kaynak IN ('irsaliye', 'erp', 'uretim', 'manuel'));
```

**Geriye Uyumluluk:**
- Mevcut paletler: `kaynak='irsaliye'`, `durum='YERLESTIRILDI'`
- API: Yeni alanlar opsiyonel
- Stok hesaplama: Mevcut filtresiz çalışır

---

*Rapor Tarihi: 16 Nisan 2025*  
*Revizyon: v2 - Tüm kullanıcı kararları entegre edilmiş*
