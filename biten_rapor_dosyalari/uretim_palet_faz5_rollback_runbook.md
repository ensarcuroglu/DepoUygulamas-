# Üretim Paleti FAZ 5 — Rollback Runbook

**İki seviyeli rollback:**
- **Seviye 1 (≤15dk):** Feature flag kapatma — operasyonel durdurma
- **Seviye 2 (≤30dk):** Seviye 1 + veri rollback (snapshot'tan geri yükleme)

---

## Rollback Tetikleyici Sinyaller

Aşağıdaki durumlardan herhangi biri gözlemlenirse rollback başlatılır:

| Sinyal | Eşik | Seviye |
|--------|------|--------|
| Backend 5xx hata oranı | >%5 (5 dakika) | 1 |
| `palet_durum_log` hata yoğunluğu | >10/dk beklenmedik | 1 |
| Stok hareketi tutarsızlığı | Herhangi bir tespit | 2 |
| Migration/backfill hatası | Herhangi bir hata | 2 |
| Depocu kullanıcı şikayeti kritik | Operasyon durdu | 1 |

---

## Seviye 1 — Feature Flag Kapatma (Hedef: ≤15 dakika)

### Adım 1.1 — Backend flag'i kapat

```bash
# Seçenek A: .env dosyasını düzenle
sed -i 's/^FEATURE_URETIM_PALET_PILOT_DEPO_IDS=.*/FEATURE_URETIM_PALET_PILOT_DEPO_IDS=/' /path/to/BackendProje/.env

# Seçenek B: Ortam değişkenini override et (container/systemd)
export FEATURE_URETIM_PALET_PILOT_DEPO_IDS=""
```

### Adım 1.2 — Backend yeniden başlat

```bash
# uvicorn direkt çalışıyorsa:
pkill -f "uvicorn main:app"
cd /path/to/BackendProje
uvicorn main:app --host 127.0.0.1 --port 8000 &

# systemd ile:
systemctl restart depo-backend

# Docker:
docker restart depo-backend
```

### Adım 1.3 — Frontend flag'i kapat ve yeniden derle

```bash
# .env.production dosyasını güncelle:
# VITE_FEATURE_URETIM_PALET_ENABLED=false

cd /path/to/ReactProje
npm run build
# Build çıktısını web sunucusuna kopyala/deploy et
```

### Adım 1.4 — Seviye 1 Doğrulama

```bash
# Admin hariç 403 alınıyor mu?
curl -X POST http://localhost:8000/api/uretim-paletleri/test/kabul-bekle \
  -H "Authorization: Bearer <depocu_token>"
# Beklenen: 403 OZELLIK_PILOTA_KAPALI

# Admin erişiyor mu?
curl http://localhost:8000/api/uretim-paletleri/ \
  -H "Authorization: Bearer <admin_token>"
# Beklenen: 200
```

- [ ] Depocu 403 alıyor  
- [ ] Admin erişiyor  
- [ ] Sidebar'da Üretim menüsü kayboldu

**Süre:**  
- Başlama: `____:____`  
- Bitiş: `____:____`  
- Toplam: ____ dakika  
- SLA (≤15dk): [ ] KARŞILANDI   [ ] AŞILDI

---

## Seviye 2 — Veri Rollback (Hedef: ≤30 dakika, Seviye 1 dahil)

> Seviye 1 tamamlandıktan sonra uygulanır.

### Adım 2.1 — Snapshot tablosunu doğrula

```bash
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME \
  -e "SELECT COUNT(*) AS snapshot_satir FROM paletler_faz5_backup;"
```

**Beklenen:** 0'dan büyük satır sayısı (backfill sırasında oluşturuldu).  
**Sonuç:** _______ satır

### Adım 2.2 — Rollback dry-run

```bash
cd /path/to/BackendProje
python rollback_uretim_palet_faz5_backfill.py --dry-run
```

**Beklenen:** Etkilenecek satır sayısı gösterildi, değişiklik yapılmadı.  
**Sonuç:** _______ satır rollback edilecek

### Adım 2.3 — Rollback gerçek çalıştırma

```bash
time python rollback_uretim_palet_faz5_backfill.py --batch-size=1000
```

**Beklenen:** `✓ Rollback tamamlandı`  
**Sonuç:** [ ] Başarılı   [ ] Hata → ________________  
**Süre:** ___s

### Adım 2.4 — Veri Doğrulama

```sql
-- Backfill öncesi NULL duruma döndü mü?
SELECT
  SUM(b.kaynak IS NULL AND p.kaynak IS NULL) AS kaynak_rollback_ok,
  SUM(b.durum  IS NULL AND p.durum  IS NULL) AS durum_rollback_ok,
  SUM(b.kaynak IS NULL AND p.kaynak IS NOT NULL) AS kaynak_eksik,
  SUM(b.durum  IS NULL AND p.durum  IS NOT NULL) AS durum_eksik
FROM paletler p
JOIN paletler_faz5_backup b ON b.id = p.id;

-- Snapshot dışı (zaten dolu olan) paletler etkilenmedi mi?
SELECT COUNT(*) FROM paletler
WHERE kaynak = 'uretim' AND durum IS NOT NULL;
```

**Sonuç:**  
```
kaynak_rollback_ok: ___  kaynak_eksik: ___
durum_rollback_ok:  ___  durum_eksik:  ___
```

- [ ] kaynak_eksik = 0  
- [ ] durum_eksik = 0  
- [ ] Üretim kaynaklı paletler etkilenmedi

### Adım 2.5 — Snapshot Temizliği (Rollback tamamlandıktan sonra)

```sql
DROP TABLE IF EXISTS paletler_faz5_backup;
```

**Not:** Rollback tamamen doğrulandıktan sonra silin.

**Seviye 2 Süre:**  
- Başlama: `____:____`  
- Bitiş: `____:____`  
- Toplam (Seviye 1 + 2): ____ dakika  
- SLA (≤30dk): [ ] KARŞILANDI   [ ] AŞILDI

---

## Rollback Sonrası İzleme

```sql
-- SistemLog hataları (son 1 saat)
SELECT COUNT(*), islem_tipi, modul
FROM sistem_loglari
WHERE olusturma_tarihi > DATE_SUB(NOW(), INTERVAL 1 HOUR)
  AND modul = 'Üretim Paleti'
GROUP BY islem_tipi, modul;

-- Stok hareketi tutarsızlık kontrolü
SELECT urun_id, SUM(CASE WHEN hareket_tipi='GIRIS' THEN miktar ELSE -miktar END) AS net_stok
FROM stok_hareketleri
WHERE palet_no LIKE 'PRD-%'
GROUP BY urun_id;
```

---

## İletişim Şablonu (Rollback Sonrası)

```
Konu: [ROLLBACK] Üretim Paleti Özelliği Geçici Devre Dışı

Tarih/Saat: _______________
Rollback Süresi: ___ dakika
Etkilenen Depo: <pilot_depo_adi>

Yapılan:
- Feature flag kapatıldı (Seviye 1)
- [Veri rollback uygulandı — Seviye 2] (gerekirse)

Sebep: _______________

Operasyonel Etki:
- Yeni üretim paleti girişi geçici olarak kapalıdır
- Mevcut paletler etkilenmedi
- Diğer WMS özellikleri normal çalışmaktadır

Sonraki Adım: Kök neden analizi yapıldıktan sonra tekrar devreye alma planı paylaşılacaktır.
```

---

*Son güncelleme: 2026-04-21*
