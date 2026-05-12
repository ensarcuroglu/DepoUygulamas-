-- =============================================================================
-- WMS AI SERVİSİ — READ-ONLY VIEW'LAR
-- =============================================================================
-- Bu view'lar, AI servisinin LLM'in SQL üretirken kullandığı yüzey alanını
-- tanımlar. Her view sadece SELECT izinli `depo_ai_reader` kullanıcısına
-- okuma erişimi verecek şekilde tasarlanmıştır.
--
-- Çalıştırma:
--   mysql -u root -p depo_yonetim < views.sql
--
-- Yeni view eklenirse `WmsAiService/sql_guard.py`'deki ALLOWED_TABLES setine
-- ve `prompts.py` içindeki SCHEMA_DESCRIPTION/FEW_SHOT_EXAMPLES alanlarına
-- mutlaka eklenmelidir.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1) ai_stok_durumu_view  (mevcut — tekrar oluşturmayı garanti edelim)
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_stok_durumu_view;
CREATE VIEW ai_stok_durumu_view AS
SELECT
    u.id                                AS urun_id,
    u.isim                              AS urun_adi,
    u.barkod                            AS barkod,
    k.isim                              AS kategori_adi,
    m.isim                              AS marka_adi,
    COALESCE(SUM(p.koli_adedi), 0)      AS guncel_stok_miktari,
    u.min_stok                          AS kritik_stok_siniri,
    u.birim                             AS birim,
    CASE
        WHEN COALESCE(SUM(p.koli_adedi), 0) <= 0 THEN 'Stok Yok'
        ELSE 'Yeterli'
    END                                 AS stok_durumu
FROM urunler u
LEFT JOIN kategoriler k ON k.id = u.kategori_id
LEFT JOIN markalar    m ON m.id = u.marka_id
LEFT JOIN lotlar      l ON l.urun_id = u.id   AND l.aktif = 1
LEFT JOIN paletler    p ON p.lot_id = l.id    AND p.aktif = 1
WHERE u.aktif = 1
GROUP BY u.id, u.isim, u.barkod, k.isim, m.isim, u.min_stok, u.birim;


-- -----------------------------------------------------------------------------
-- 2) ai_palet_view — palet + lot + ürün + raf + depo birleştirmesi
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_palet_view;
CREATE VIEW ai_palet_view AS
SELECT
    p.id                    AS palet_id,
    p.palet_no              AS palet_no,
    p.koli_adedi            AS koli_adedi,
    p.palet_kg              AS palet_kg,
    p.brut_kg               AS brut_kg,
    p.net_kg                AS net_kg,
    p.vardiya               AS vardiya,
    p.kaynak                AS kaynak,
    p.durum                 AS palet_durumu,
    p.aktif                 AS aktif,
    p.uretim_tarihi         AS uretim_tarihi,
    p.uretim_hatti          AS uretim_hatti,
    p.makine_kodu           AS makine_kodu,
    p.tarih                 AS palet_kayit_tarihi,
    p.kabul_tarihi          AS kabul_tarihi,
    l.id                    AS lot_id,
    l.lot_no                AS lot_no,
    l.son_kullanma_tarihi   AS son_kullanma_tarihi,
    u.id                    AS urun_id,
    u.isim                  AS urun_adi,
    u.barkod                AS urun_barkod,
    u.birim                 AS birim,
    k.isim                  AS kategori_adi,
    m.isim                  AS marka_adi,
    r.id                    AS raf_id,
    r.kod                   AS raf_kodu,
    r.bolge                 AS raf_bolge,
    r.koridor               AS raf_koridor,
    r.is_staging            AS raf_staging_mi,
    d.id                    AS depo_id,
    d.isim                  AS depo_adi
FROM paletler p
LEFT JOIN lotlar       l ON l.id = p.lot_id
LEFT JOIN urunler      u ON u.id = l.urun_id
LEFT JOIN kategoriler  k ON k.id = u.kategori_id
LEFT JOIN markalar     m ON m.id = u.marka_id
LEFT JOIN raflar       r ON r.id = p.raf_id
LEFT JOIN depolar      d ON d.id = r.depo_id;


-- -----------------------------------------------------------------------------
-- 3) ai_lot_view — lot + ürün + toplam koli
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_lot_view;
CREATE VIEW ai_lot_view AS
SELECT
    l.id                                  AS lot_id,
    l.lot_no                              AS lot_no,
    l.parti_no                            AS parti_no,
    l.uretim_tarihi                       AS uretim_tarihi,
    l.son_kullanma_tarihi                 AS son_kullanma_tarihi,
    l.aktif                               AS aktif,
    l.olusturma_tarihi                    AS olusturma_tarihi,
    u.id                                  AS urun_id,
    u.isim                                AS urun_adi,
    u.birim                               AS birim,
    k.isim                                AS kategori_adi,
    m.isim                                AS marka_adi,
    COUNT(p.id)                           AS palet_sayisi,
    COALESCE(SUM(p.koli_adedi), 0)        AS toplam_koli,
    CASE
        WHEN l.son_kullanma_tarihi IS NULL THEN NULL
        ELSE DATEDIFF(l.son_kullanma_tarihi, CURDATE())
    END                                   AS skt_kalan_gun
FROM lotlar l
LEFT JOIN urunler     u ON u.id = l.urun_id
LEFT JOIN kategoriler k ON k.id = u.kategori_id
LEFT JOIN markalar    m ON m.id = u.marka_id
LEFT JOIN paletler    p ON p.lot_id = l.id AND p.aktif = 1
GROUP BY l.id, l.lot_no, l.parti_no, l.uretim_tarihi, l.son_kullanma_tarihi,
         l.aktif, l.olusturma_tarihi, u.id, u.isim, u.birim, k.isim, m.isim;


-- -----------------------------------------------------------------------------
-- 4) ai_irsaliye_view — çıkış (sevk) irsaliyeleri + sipariş özeti
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_irsaliye_view;
CREATE VIEW ai_irsaliye_view AS
SELECT
    i.id                          AS irsaliye_id,
    i.irsaliye_no                 AS irsaliye_no,
    i.irsaliye_tarihi             AS irsaliye_tarihi,
    i.belge_turu                  AS belge_turu,
    i.tir_plaka                   AS tir_plaka,
    i.sofor_adi                   AS sofor_adi,
    i.durum                       AS durum,
    i.olusturma_tarihi            AS olusturma_tarihi,
    s.id                          AS siparis_id,
    s.siparis_no                  AS siparis_no,
    s.musteri_adi                 AS musteri_adi,
    s.teslimat_tarihi             AS teslimat_tarihi,
    s.durum                       AS siparis_durumu,
    s.top_miktar                  AS siparis_top_miktar,
    s.top_tutar                   AS siparis_top_tutar
FROM irsaliyeler i
LEFT JOIN siparisler s ON s.id = i.siparis_id;


-- -----------------------------------------------------------------------------
-- 5) ai_mal_kabul_view — giriş (mal kabul) irsaliyeleri + tedarikçi + depo
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_mal_kabul_view;
CREATE VIEW ai_mal_kabul_view AS
SELECT
    mki.id                AS mal_kabul_id,
    mki.irsaliye_no       AS irsaliye_no,
    mki.tarih             AS tarih,
    mki.durum             AS durum,
    mki.tir_plaka         AS tir_plaka,
    mki.sofor_adi         AS sofor_adi,
    mki.olusturma_tarihi  AS olusturma_tarihi,
    t.id                  AS tedarikci_id,
    t.firma_adi           AS tedarikci_adi,
    d.id                  AS depo_id,
    d.isim                AS depo_adi,
    (SELECT COUNT(*) FROM mal_kabul_kalemleri mk WHERE mk.mal_kabul_irsaliyesi_id = mki.id)               AS kalem_sayisi,
    (SELECT COALESCE(SUM(mk.miktar), 0) FROM mal_kabul_kalemleri mk WHERE mk.mal_kabul_irsaliyesi_id = mki.id) AS toplam_miktar
FROM mal_kabul_irsaliyeleri mki
LEFT JOIN tedarikciler t ON t.id = mki.tedarikci_id
LEFT JOIN depolar      d ON d.id = mki.depo_id;


-- -----------------------------------------------------------------------------
-- 6) ai_siparis_view — sipariş + sevkiyat planı + irsaliye sayısı
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_siparis_view;
CREATE VIEW ai_siparis_view AS
SELECT
    s.id                          AS siparis_id,
    s.siparis_no                  AS siparis_no,
    s.musteri_adi                 AS musteri_adi,
    s.teslimat_tarihi             AS teslimat_tarihi,
    s.durum                       AS siparis_durumu,
    s.top_miktar                  AS top_miktar,
    s.top_tutar                   AS top_tutar,
    s.aktif                       AS aktif,
    s.olusturma_tarihi            AS olusturma_tarihi,
    sp.id                         AS sevkiyat_id,
    sp.tir_plaka                  AS sevkiyat_tir_plaka,
    sp.sofor_adi                  AS sevkiyat_sofor_adi,
    sp.yukleme_tarihi             AS yukleme_tarihi,
    sp.durum                      AS sevkiyat_durumu,
    (SELECT COUNT(*) FROM siparis_kalemleri sk WHERE sk.siparis_id = s.id) AS kalem_sayisi,
    (SELECT COUNT(*) FROM irsaliyeler i      WHERE i.siparis_id  = s.id) AS irsaliye_sayisi
FROM siparisler s
LEFT JOIN sevkiyat_planlari sp ON sp.siparis_id = s.id;


-- -----------------------------------------------------------------------------
-- 7) ai_sevkiyat_view — sevkiyat planı + sipariş + müşteri
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_sevkiyat_view;
CREATE VIEW ai_sevkiyat_view AS
SELECT
    sp.id                  AS sevkiyat_id,
    sp.tir_plaka           AS tir_plaka,
    sp.sofor_adi           AS sofor_adi,
    sp.depo_kapi           AS depo_kapi,
    sp.yukleme_tarihi      AS yukleme_tarihi,
    sp.cikis_saati         AS cikis_saati,
    sp.varis_saati         AS varis_saati,
    sp.durum               AS durum,
    sp.olusturma_tarihi    AS olusturma_tarihi,
    s.id                   AS siparis_id,
    s.siparis_no           AS siparis_no,
    s.musteri_adi          AS musteri_adi,
    s.teslimat_tarihi      AS teslimat_tarihi,
    s.top_miktar           AS siparis_top_miktar
FROM sevkiyat_planlari sp
LEFT JOIN siparisler s ON s.id = sp.siparis_id;


-- -----------------------------------------------------------------------------
-- 8) ai_stok_hareketi_view — stok hareketleri + ürün + palet + raf
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_stok_hareketi_view;
CREATE VIEW ai_stok_hareketi_view AS
SELECT
    sh.id                AS hareket_id,
    sh.hareket_tipi      AS hareket_tipi,
    sh.miktar            AS miktar,
    sh.tarih             AS tarih,
    sh.siparis_no        AS siparis_no,
    sh.irsaliye_no       AS irsaliye_no,
    sh.tir_plaka         AS tir_plaka,
    sh.depo_kapi         AS depo_kapi,
    sh.tasiyici_firma    AS tasiyici_firma,
    sh.aciklama          AS aciklama,
    u.id                 AS urun_id,
    u.isim               AS urun_adi,
    u.birim              AS birim,
    k.isim               AS kategori_adi,
    m.isim               AS marka_adi,
    p.id                 AS palet_id,
    p.palet_no           AS palet_no,
    l.id                 AS lot_id,
    l.lot_no             AS lot_no,
    r.id                 AS raf_id,
    r.kod                AS raf_kodu,
    d.id                 AS depo_id,
    d.isim               AS depo_adi,
    ku.id                AS kullanici_id,
    ku.kullanici_adi     AS kullanici_adi
FROM stok_hareketleri sh
LEFT JOIN urunler      u  ON u.id  = sh.urun_id
LEFT JOIN kategoriler  k  ON k.id  = u.kategori_id
LEFT JOIN markalar     m  ON m.id  = u.marka_id
LEFT JOIN paletler     p  ON p.id  = sh.palet_id
LEFT JOIN lotlar       l  ON l.id  = sh.lot_id
LEFT JOIN raflar       r  ON r.id  = sh.raf_id
LEFT JOIN depolar      d  ON d.id  = r.depo_id
LEFT JOIN kullanicilar ku ON ku.id = sh.kullanici_id;


-- -----------------------------------------------------------------------------
-- 9) ai_depo_doluluk_view — depo bazında raf doluluğu özeti
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS ai_depo_doluluk_view;
CREATE VIEW ai_depo_doluluk_view AS
SELECT
    d.id                                 AS depo_id,
    d.isim                               AS depo_adi,
    COUNT(DISTINCT r.id)                 AS toplam_raf,
    COUNT(DISTINCT CASE WHEN p.id IS NOT NULL AND p.aktif = 1 THEN r.id END) AS dolu_raf,
    COUNT(DISTINCT CASE WHEN p.id IS NULL THEN r.id END)                     AS bos_raf,
    COUNT(CASE WHEN p.aktif = 1 THEN p.id END)                               AS aktif_palet_sayisi,
    COALESCE(SUM(CASE WHEN p.aktif = 1 THEN p.koli_adedi ELSE 0 END), 0)     AS toplam_koli
FROM depolar d
LEFT JOIN raflar   r ON r.depo_id = d.id AND r.aktif = 1
LEFT JOIN paletler p ON p.raf_id  = r.id
WHERE d.aktif = 1
GROUP BY d.id, d.isim;


-- -----------------------------------------------------------------------------
-- İZİNLER — depo_ai_reader sadece SELECT + view metadata okuyabilir
-- -----------------------------------------------------------------------------
GRANT SHOW VIEW ON depo_yonetim.* TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_stok_durumu_view    TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_palet_view          TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_lot_view            TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_irsaliye_view       TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_mal_kabul_view      TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_siparis_view        TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_sevkiyat_view       TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_stok_hareketi_view  TO 'depo_ai_reader'@'localhost';
GRANT SELECT ON depo_yonetim.ai_depo_doluluk_view   TO 'depo_ai_reader'@'localhost';
GRANT SHOW VIEW ON depo_yonetim.* TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_stok_durumu_view    TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_palet_view          TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_lot_view            TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_irsaliye_view       TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_mal_kabul_view      TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_siparis_view        TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_sevkiyat_view       TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_stok_hareketi_view  TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.ai_depo_doluluk_view   TO 'depo_ai_reader'@'%';
FLUSH PRIVILEGES;
