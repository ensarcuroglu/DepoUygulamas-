# Üretim Paleti FAZ 5 — Staging Smoke Test Runbook

**Hedef:** Production deploy öncesi staging ortamında migration, backfill ve uçtan uca operasyonel akışları doğrulamak.  
**Ortam:** Staging MySQL 8.0+, `depo_db_staging`  
**Rollback SLA:** Seviye 1 ≤15dk (flag kapatma), Seviye 2 ≤30dk (veri rollback)  
**Sorumlu:** Sistem Yöneticisi / DevOps  
**Tarih:** _______________  
**Çalıştıran:** _______________

---

## Ön Koşullar

- [ ] Staging DB yedeği alındı (`mysqldump depo_db_staging > staging_backup_$(date +%Y%m%d_%H%M%S).sql`)
- [ ] Kod değişiklikleri staging'e deploy edildi (Faz 1-5 tüm commit'ler)
- [ ] `.env.staging` hazır: `DB_NAME=depo_db_staging`, `JWT_SECRET_KEY=<staging-secret>`
- [ ] `FEATURE_URETIM_PALET_PILOT_DEPO_IDS` henüz boş (flag kapalı)
- [ ] Test kullanıcıları mevcut: admin, depocu (pilot depo atanmış), goruntuleyen

---

## Adım 1 — DB Snapshot ve Başlangıç Durumu

```bash
# Palet satır sayısını not al
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME \
  -e "SELECT COUNT(*), SUM(kaynak IS NULL) AS null_kaynak, SUM(durum IS NULL) AS null_durum FROM paletler;"
```

**Beklenen:** Mevcut satır sayısı kayıt edildi.  
**Sonuç:** `Toplam: ___  null_kaynak: ___  null_durum: ___`  
- [ ] Kaydedildi

---

## Adım 2 — FAZ 2 Migration (Şema)

```bash
cd BackendProje
python migrate_uretim_palet_faz2.py
```

**Beklenen:** `✓ Tüm doğrulamalar başarılı.`  
**Süre hedefi:** <2 dakika  
**Sonuç:** [ ] Başarılı   [ ] Hata → ________________  
**Süre:** ___s

---

## Adım 3 — FAZ 5 Backfill Dry-Run

```bash
python migrate_uretim_palet_faz5_backfill.py --dry-run
```

**Beklenen:** Etkilenecek satır sayıları gösterildi, veritabanında değişiklik yapılmadı.  
**Sonuç:** `kaynak NULL: ___  durum NULL: ___`  
- [ ] Backup tablosu oluşmadı (doğrulandı)

---

## Adım 4 — FAZ 5 Backfill (Gerçek Çalıştırma)

```bash
python migrate_uretim_palet_faz5_backfill.py --batch-size=1000
```

**Beklenen:** `✓ Doğrulama başarılı — NULL kaynak/durum yok.`  
**Süre hedefi:** <5 dakika (veri miktarına bağlı)  
**Sonuç:** [ ] Başarılı   [ ] Hata → ________________  
**Süre:** ___s

### Backfill Doğrulama Sorguları

```sql
SELECT COUNT(*) FROM paletler WHERE kaynak IS NULL;   -- 0 olmalı
SELECT COUNT(*) FROM paletler WHERE durum IS NULL;    -- 0 olmalı
SELECT kaynak, COUNT(*) FROM paletler GROUP BY kaynak;
SELECT durum, COUNT(*) FROM paletler GROUP BY durum;
SELECT COUNT(*) FROM paletler_faz5_backup;            -- snapshot satır sayısı
```

**Sonuç:**  
```
kaynak dağılımı: _______________
durum dağılımı: _______________
```
- [ ] NULL satır kalmadı

---

## Adım 5 — Pilot Depo Feature Flag Aktivasyonu

```bash
# .env.staging veya ortam değişkeni olarak:
export FEATURE_URETIM_PALET_PILOT_DEPO_IDS=<pilot_depo_id>
export VITE_FEATURE_URETIM_PALET_ENABLED=true

# Backend yeniden başlat
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Frontend yeniden build (staging URL)
cd ReactProje && npm run build
```

**Beklenen:** Backend ayağa kalktı, frontend yeniden derlendi.  
- [ ] Backend `/api/uretim-paletleri/` endpoint'i 200 dönüyor (admin token ile)
- [ ] Sidebar'da "Üretim" menüsü görünüyor

---

## Adım 6 — Uçtan Uca Manuel Akış

### 6.1 Palet Oluşturma (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"lot_id": <mevcut_lot_id>, "koli_adedi": 48}'
```

**Beklenen:** `201`, `durum: OLUSTURULDU`, `kaynak: uretim`, `palet_no: PRD-...`  
**Oluşan palet_no:** `_______________`  
- [ ] Başarılı

### 6.2 ZPL Etiket Alma (GET)

```bash
curl http://localhost:8000/api/uretim-paletleri/<palet_no>/etiket \
  -H "Authorization: Bearer <admin_token>"
```

**Beklenen:** `^XA...^XZ` ZPL içeriği, palet_no ve lot_no alanları dolu.  
- [ ] Başarılı

### 6.3 Kabul Bekle (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/kabul-bekle \
  -H "Authorization: Bearer <depocu_token>"
```

**Beklenen:** `durum: KABUL_BEKLIYOR`  
- [ ] Başarılı

### 6.4 Kabul Et — Stok Hareketi Doğrulama (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/kabul-et \
  -H "Authorization: Bearer <depocu_token>"
```

**Beklenen:** `durum: KABUL_EDILDI`, `kabul_tarihi` dolu.

```sql
-- Stok hareketi GIRIS yazıldı mı?
SELECT id, hareket_tipi, miktar, palet_no, aciklama
FROM stok_hareketleri
WHERE palet_no = '<palet_no>' ORDER BY id DESC LIMIT 1;
```

**Sonuç:** `hareket_tipi: GIRIS  miktar: 48`  
- [ ] Başarılı   - [ ] StokHareketi kaydı mevcut

### 6.5 Karantinaya Al (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/karantina \
  -H "Authorization: Bearer <depocu_token>" \
  -H "Content-Type: application/json" \
  -d '{"palet_no": "<palet_no>", "sebep": "Smoke test karantina"}'
```

**Beklenen:** `durum: KARANTINA`  
- [ ] Başarılı

### 6.6 Karantinadan Çıkar (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/karantina-cikar \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"palet_no": "<palet_no>", "sebep": "QC onaylandı"}'
```

**Beklenen:** `durum: KABUL_EDILDI`  
- [ ] Başarılı

### 6.7 Yerleştirme Bekle (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/yerlestirme-bekle \
  -H "Authorization: Bearer <depocu_token>"
```

**Beklenen:** `durum: YERLESTIRME_BEKLIYOR`  
- [ ] Başarılı

### 6.8 Yerleştir (POST)

```bash
curl -X POST http://localhost:8000/api/uretim-paletleri/<palet_no>/yerlestir \
  -H "Authorization: Bearer <depocu_token>" \
  -H "Content-Type: application/json" \
  -d '{"palet_no": "<palet_no>", "raf_id": <hedef_raf_id>}'
```

**Beklenen:** `durum: YERLESTIRILDI`  
- [ ] Başarılı

---

## Adım 7 — İptal Senaryosu

Yeni bir palet oluşturup iptal et:

```bash
# Oluştur
curl -X POST http://localhost:8000/api/uretim-paletleri/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"lot_id": <mevcut_lot_id>, "koli_adedi": 12}'
# → palet_no not al

# İptal et
curl -X POST http://localhost:8000/api/uretim-paletleri/<yeni_palet_no>/iptal \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"palet_no": "<yeni_palet_no>", "sebep": "Smoke test iptal"}'
```

**Beklenen:** `durum: IPTAL_EDILDI`, `aktif: false`  
- [ ] Başarılı

---

## Adım 8 — Pilot Dışı Depo 403 Doğrulaması

```bash
# pilot_disinda_depocu token'ı ile olustur
curl -X POST http://localhost:8000/api/uretim-paletleri/ \
  -H "Authorization: Bearer <pilot_disinda_depocu_token>" \
  -H "Content-Type: application/json" \
  -d '{"lot_id": <mevcut_lot_id>, "koli_adedi": 10}'
```

**Beklenen:** `403` + `code: OZELLIK_PILOTA_KAPALI`  
- [ ] Başarılı

---

## Adım 9 — Rollback Tatbikatı

### 9.1 Seviye 1 (Feature Flag Kapatma)

```bash
time (
  export FEATURE_URETIM_PALET_PILOT_DEPO_IDS=""
  export VITE_FEATURE_URETIM_PALET_ENABLED=false
  # Backend restart
  # kill <pid> && uvicorn main:app --host 127.0.0.1 --port 8000 &
  # Frontend rebuild
  # cd ReactProje && npm run build
  echo "Seviye 1 tamamlandı"
)
```

**SLA hedefi:** ≤15 dakika  
**Gerçekleşen süre:** _____ dakika  
- [ ] Sidebar'da üretim menüsü kayboldu
- [ ] POST `/api/uretim-paletleri/` → admin hariç 403

### 9.2 Seviye 2 (Veri Rollback)

```bash
time (
  python rollback_uretim_palet_faz5_backfill.py --dry-run
  # Çıktı onaylandıktan sonra:
  python rollback_uretim_palet_faz5_backfill.py --batch-size=1000
)
```

**SLA hedefi:** ≤30 dakika (Seviye 1 dahil)  
**Gerçekleşen süre:** _____ dakika

```sql
-- Rollback doğrulama
SELECT COUNT(*) FROM paletler WHERE kaynak IS NULL;
SELECT COUNT(*) FROM paletler WHERE durum IS NULL;
-- Snapshot satır sayısı ile eşleşmeli
SELECT COUNT(*) FROM paletler_faz5_backup;
```

- [ ] Satırlar orijinal NULL değerine döndü
- [ ] Seviye 2 toplam süre SLA içinde

---

## Sonuç Özeti

| Adım | Başarılı | Süre | Notlar |
|------|----------|------|--------|
| 1. DB Snapshot | | | |
| 2. FAZ 2 Migration | | | |
| 3. Backfill Dry-Run | | | |
| 4. Backfill Gerçek | | | |
| 5. Feature Flag Aktivasyon | | | |
| 6. Uçtan Uca Akış | | | |
| 7. İptal Senaryosu | | | |
| 8. Pilot Dışı 403 | | | |
| 9a. Rollback Seviye 1 | | | |
| 9b. Rollback Seviye 2 | | | |

**Genel sonuç:** [ ] PRODUCTION'A GEÇİŞE HAZIR   [ ] SORUN VAR — Açıklama: _______________
