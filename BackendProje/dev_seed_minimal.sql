-- Development seed (industry-grade, deterministic, idempotent)
-- ------------------------------------------------------------------
-- Goals
-- 1) Keep users and optional master tables.
-- 2) Seed clean DEV-namespaced operational data for development.
-- 3) Be safe to run multiple times (idempotent).
-- 4) Roll back automatically on errors.
--
-- Usage (MySQL Workbench):
-- 1) Open this file and run all.
-- 2) Script validates selected DB and required tables.
-- 3) If validation fails, no partial writes are committed.
--
-- NOTE:
-- - This script intentionally touches only DEV-* records in operational tables.
-- - Existing non-DEV business data is preserved.

USE depo_yonetim;

-- Safety gate: expected DB
SET @expected_db := 'depo_yonetim';

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_dev_seed_minimal $$
CREATE PROCEDURE sp_dev_seed_minimal()
BEGIN
    DECLARE v_db VARCHAR(128);
    DECLARE v_admin_id INT;
    DECLARE v_marka_id INT;
    DECLARE v_kategori_id INT;
    DECLARE v_depo_id INT;
    DECLARE v_raf1 INT;
    DECLARE v_raf2 INT;
    DECLARE v_raf3 INT;
    DECLARE v_tedarikci_id INT;
    DECLARE v_u1 INT;
    DECLARE v_u2 INT;
    DECLARE v_u3 INT;
    DECLARE v_l1 INT;
    DECLARE v_l2 INT;
    DECLARE v_l3 INT;
    DECLARE v_p1 INT;
    DECLARE v_p2 INT;
    DECLARE v_p3 INT;
    DECLARE v_p4 INT;
    DECLARE v_required_tables INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET SQL_SAFE_UPDATES = 1;
        RESIGNAL;
    END;

    SET v_db = DATABASE();
    IF v_db IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No database selected. Select target schema first.';
    END IF;

    IF @expected_db IS NOT NULL AND @expected_db <> '' AND BINARY v_db <> BINARY @expected_db THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Wrong database selected for DEV seed.';
    END IF;

    SELECT COUNT(*) INTO v_required_tables
    FROM information_schema.tables
    WHERE table_schema = v_db
      AND table_name IN (
          'kullanicilar', 'markalar', 'kategoriler', 'depolar', 'raflar', 'tedarikciler',
          'urunler', 'lotlar', 'paletler', 'stok_hareketleri', 'mal_kabul_irsaliyeleri'
      );

    IF v_required_tables <> 11 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Required tables are missing. Run migrations first.';
    END IF;

    START TRANSACTION;
    SET SQL_SAFE_UPDATES = 0;

    -- ------------------------------------------------------------------
    -- 0) Resolve safe actor (admin preferred, any user fallback)
    -- ------------------------------------------------------------------
    SELECT id INTO v_admin_id
    FROM kullanicilar
    WHERE rol = 'admin'
    ORDER BY id
    LIMIT 1;

    IF v_admin_id IS NULL THEN
        SELECT id INTO v_admin_id
        FROM kullanicilar
        ORDER BY id
        LIMIT 1;
    END IF;

    IF v_admin_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No users found. Seed requires at least one user.';
    END IF;

    -- ------------------------------------------------------------------
    -- 1) Ensure deterministic master references (upsert style)
    -- ------------------------------------------------------------------
    INSERT INTO markalar (isim, aciklama, olusturma_tarihi)
    VALUES ('DEV-MARKA', 'Deterministic development brand', UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        aciklama = 'Deterministic development brand',
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_marka_id = LAST_INSERT_ID();

    INSERT INTO kategoriler (isim, aciklama, olusturma_tarihi)
    VALUES ('DEV-KATEGORI', 'Deterministic development category', UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        aciklama = 'Deterministic development category',
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_kategori_id = LAST_INSERT_ID();

    INSERT INTO depolar (isim, adres, aciklama, aktif, olusturma_tarihi)
    VALUES ('DEV-DEPO', 'DEV Address', 'Deterministic development warehouse', 1, UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        adres = 'DEV Address',
        aciklama = 'Deterministic development warehouse',
        aktif = 1,
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_depo_id = LAST_INSERT_ID();

    INSERT INTO raflar (depo_id, kod, bolge, kapasite, aktif, olusturma_tarihi)
    VALUES (v_depo_id, 'DEV-RAF-01', 'DEV-ZONE', 200, 1, UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        depo_id = v_depo_id,
        bolge = 'DEV-ZONE',
        kapasite = 200,
        aktif = 1,
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_raf1 = LAST_INSERT_ID();

    INSERT INTO raflar (depo_id, kod, bolge, kapasite, aktif, olusturma_tarihi)
    VALUES (v_depo_id, 'DEV-RAF-02', 'DEV-ZONE', 200, 1, UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        depo_id = v_depo_id,
        bolge = 'DEV-ZONE',
        kapasite = 200,
        aktif = 1,
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_raf2 = LAST_INSERT_ID();

    INSERT INTO raflar (depo_id, kod, bolge, kapasite, aktif, olusturma_tarihi)
    VALUES (v_depo_id, 'DEV-RAF-03', 'DEV-ZONE', 200, 1, UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        depo_id = v_depo_id,
        bolge = 'DEV-ZONE',
        kapasite = 200,
        aktif = 1,
        olusturma_tarihi = COALESCE(olusturma_tarihi, UTC_TIMESTAMP());
    SET v_raf3 = LAST_INSERT_ID();

    SELECT id INTO v_tedarikci_id
    FROM tedarikciler
    WHERE firma_adi = 'DEV-TEDARIKCI'
    ORDER BY id
    LIMIT 1;

    IF v_tedarikci_id IS NULL THEN
        INSERT INTO tedarikciler (
            firma_adi, iletisim_kisi, telefon, email, adres, vergi_no, aktif, olusturma_tarihi
        ) VALUES (
            'DEV-TEDARIKCI', 'Dev Contact', '0000000000', 'dev@seed.local', 'DEV Address', 'DEV-VKN', 1, UTC_TIMESTAMP()
        );
        SET v_tedarikci_id = LAST_INSERT_ID();
    ELSE
        UPDATE tedarikciler
        SET iletisim_kisi = 'Dev Contact',
            telefon = '0000000000',
            email = 'dev@seed.local',
            adres = 'DEV Address',
            vergi_no = 'DEV-VKN',
            aktif = 1
        WHERE id = v_tedarikci_id;
    END IF;

    -- Keep one canonical DEV supplier; remove only unreferenced duplicates.
    DELETE FROM tedarikciler
    WHERE firma_adi = 'DEV-TEDARIKCI'
      AND id <> v_tedarikci_id
      AND NOT EXISTS (SELECT 1 FROM urunler WHERE urunler.tedarikci_id = tedarikciler.id)
      AND NOT EXISTS (
          SELECT 1
          FROM mal_kabul_irsaliyeleri
          WHERE mal_kabul_irsaliyeleri.tedarikci_id = tedarikciler.id
      );

    -- ------------------------------------------------------------------
    -- 2) Cleanup previous DEV operational records (idempotent)
    -- ------------------------------------------------------------------
    DELETE FROM stok_hareketleri
    WHERE aciklama LIKE '[DEV-SEED]%'
       OR urun_id IN (SELECT id FROM urunler WHERE barkod LIKE 'DEV-%')
       OR lot_id IN (SELECT id FROM lotlar WHERE lot_no LIKE 'DEV-LOT-%')
       OR palet_id IN (SELECT id FROM paletler WHERE palet_no LIKE 'DEV-PLT-%');

    DELETE FROM paletler
    WHERE palet_no LIKE 'DEV-PLT-%';

    DELETE FROM lotlar
    WHERE lot_no LIKE 'DEV-LOT-%';

    DELETE FROM urunler
    WHERE barkod LIKE 'DEV-%';

    -- ------------------------------------------------------------------
    -- 3) Insert deterministic DEV products
    -- ------------------------------------------------------------------
    INSERT INTO urunler (
      isim, marka_id, kategori_id, tedarikci_id, barkod, ean,
      ic_adet, gramaj, birim, fiyat, min_stok, aciklama, aktif, olusturma_tarihi, guncelleme_tarihi
    ) VALUES
      ('DEV Makarna 500g', v_marka_id, v_kategori_id, v_tedarikci_id, 'DEV-001', '8699000000001', 20, 0.5, 'Adet', 25.0, 30, 'Deterministic DEV seed product 1', 1, UTC_TIMESTAMP(), UTC_TIMESTAMP()),
      ('DEV Pirinc 1kg',   v_marka_id, v_kategori_id, v_tedarikci_id, 'DEV-002', '8699000000002', 10, 1.0, 'Adet', 40.0, 20, 'Deterministic DEV seed product 2', 1, UTC_TIMESTAMP(), UTC_TIMESTAMP()),
      ('DEV Bulgur 1kg',   v_marka_id, v_kategori_id, v_tedarikci_id, 'DEV-003', '8699000000003', 10, 1.0, 'Adet', 32.0, 20, 'Deterministic DEV seed product 3', 1, UTC_TIMESTAMP(), UTC_TIMESTAMP());

    SELECT id INTO v_u1 FROM urunler WHERE barkod = 'DEV-001' LIMIT 1;
    SELECT id INTO v_u2 FROM urunler WHERE barkod = 'DEV-002' LIMIT 1;
    SELECT id INTO v_u3 FROM urunler WHERE barkod = 'DEV-003' LIMIT 1;

    -- ------------------------------------------------------------------
    -- 4) Insert deterministic DEV lots
    -- ------------------------------------------------------------------
    INSERT INTO lotlar (
      urun_id, lot_no, parti_no, uretim_tarihi, son_kullanma_tarihi, aciklama, aktif, olusturma_tarihi
    ) VALUES
      (v_u1, 'DEV-LOT-001', 'DEV-P-001', '2026-03-01', '2027-03-01', 'Deterministic DEV lot 1', 1, UTC_TIMESTAMP()),
      (v_u2, 'DEV-LOT-002', 'DEV-P-002', '2026-03-05', '2027-03-05', 'Deterministic DEV lot 2', 1, UTC_TIMESTAMP()),
      (v_u3, 'DEV-LOT-003', 'DEV-P-003', '2026-03-10', '2027-03-10', 'Deterministic DEV lot 3', 1, UTC_TIMESTAMP());

    SELECT id INTO v_l1 FROM lotlar WHERE lot_no = 'DEV-LOT-001' LIMIT 1;
    SELECT id INTO v_l2 FROM lotlar WHERE lot_no = 'DEV-LOT-002' LIMIT 1;
    SELECT id INTO v_l3 FROM lotlar WHERE lot_no = 'DEV-LOT-003' LIMIT 1;

    -- ------------------------------------------------------------------
    -- 5) Insert deterministic DEV pallets
    -- ------------------------------------------------------------------
    INSERT INTO paletler (
      lot_id, raf_id, palet_no, koli_adedi, palet_kg, vardiya, tarih, aktif, olusturma_tarihi
    ) VALUES
      (v_l1, v_raf1, 'DEV-PLT-001', 40, 400.0, 'G1', UTC_TIMESTAMP(), 1, UTC_TIMESTAMP()),
      (v_l1, v_raf2, 'DEV-PLT-002', 30, 300.0, 'G1', UTC_TIMESTAMP(), 1, UTC_TIMESTAMP()),
      (v_l2, v_raf2, 'DEV-PLT-003', 20, 200.0, 'G2', UTC_TIMESTAMP(), 1, UTC_TIMESTAMP()),
      (v_l3, v_raf3, 'DEV-PLT-004', 25, 250.0, 'G2', UTC_TIMESTAMP(), 1, UTC_TIMESTAMP());

    SELECT id INTO v_p1 FROM paletler WHERE palet_no = 'DEV-PLT-001' LIMIT 1;
    SELECT id INTO v_p2 FROM paletler WHERE palet_no = 'DEV-PLT-002' LIMIT 1;
    SELECT id INTO v_p3 FROM paletler WHERE palet_no = 'DEV-PLT-003' LIMIT 1;
    SELECT id INTO v_p4 FROM paletler WHERE palet_no = 'DEV-PLT-004' LIMIT 1;

    -- ------------------------------------------------------------------
    -- 6) Insert deterministic DEV stock movements
    -- ------------------------------------------------------------------
    INSERT INTO stok_hareketleri (
      urun_id, lot_id, palet_id, raf_id, hareket_tipi, miktar, aciklama, kullanici_id, tarih
    ) VALUES
      (v_u1, v_l1, v_p1, v_raf1, 'giris', 40, '[DEV-SEED] initial stock load', v_admin_id, UTC_TIMESTAMP()),
      (v_u1, v_l1, v_p2, v_raf2, 'giris', 30, '[DEV-SEED] initial stock load', v_admin_id, UTC_TIMESTAMP()),
      (v_u2, v_l2, v_p3, v_raf2, 'giris', 20, '[DEV-SEED] initial stock load', v_admin_id, UTC_TIMESTAMP()),
      (v_u3, v_l3, v_p4, v_raf3, 'giris', 25, '[DEV-SEED] initial stock load', v_admin_id, UTC_TIMESTAMP());

    COMMIT;
    SET SQL_SAFE_UPDATES = 1;

    -- ------------------------------------------------------------------
    -- 7) Verification snapshot
    -- ------------------------------------------------------------------
    SELECT
        v_db AS selected_database,
        v_admin_id AS seed_admin_user_id,
        v_marka_id AS seed_marka_id,
        v_kategori_id AS seed_kategori_id,
        v_depo_id AS seed_depo_id,
        v_tedarikci_id AS seed_tedarikci_id;

    SELECT 'kullanicilar (preserved)' AS tablo, COUNT(*) AS adet FROM kullanicilar
    UNION ALL SELECT 'urunler (DEV)', COUNT(*) FROM urunler WHERE barkod LIKE 'DEV-%'
    UNION ALL SELECT 'lotlar (DEV)', COUNT(*) FROM lotlar WHERE lot_no LIKE 'DEV-LOT-%'
    UNION ALL SELECT 'paletler (DEV)', COUNT(*) FROM paletler WHERE palet_no LIKE 'DEV-PLT-%'
    UNION ALL SELECT 'stok_hareketleri (DEV)', COUNT(*)
      FROM stok_hareketleri WHERE aciklama LIKE '[DEV-SEED]%';
END $$

CALL sp_dev_seed_minimal() $$
DROP PROCEDURE sp_dev_seed_minimal $$

DELIMITER ;
