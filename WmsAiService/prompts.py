"""
Prompt şablonları ve few-shot örnekleri.

Yerel/küçük LLM'lerde (qwen2.5-coder:7b vb.) SQL üretim doğruluğunu artırmanın en etkili
yolu zengin sistem prompt + Türkçe few-shot örnekleridir. Şema açıklaması +
allowed-values listesi + örnek soru/SQL çiftleri modelin hallucination
ihtimalini ciddi şekilde düşürür.
"""

# ----------------------------------------------------------------------------
# Şema açıklaması — view kolonları ve izinli değerler (gerçek DB şemasına göre)
# ----------------------------------------------------------------------------

SCHEMA_DESCRIPTION = """
Veritabanı: MySQL (utf8mb4)

Erişilebilir view'lar (sadece bunları kullan, başka tablo/view UYDURMA):

============================================================================
VIEW 1: `ai_stok_durumu_view` — Ürün bazlı güncel stok durumu
============================================================================
- urun_id (INT)                     : Ürün PK
- urun_adi (VARCHAR)                : Ürün adı (örn. 'DEV Makarna 500g')
- barkod (VARCHAR, NULL)            : Ürün barkodu
- kategori_adi (VARCHAR, NULL)      : Kategori (örn. 'Makarna')
- marka_adi (VARCHAR, NULL)         : Marka (örn. 'ARBELLA')
- guncel_stok_miktari (DECIMAL)     : Mevcut stok (palet koli toplamı)
- kritik_stok_siniri (INT)          : Kritik stok eşiği
- birim (VARCHAR)                   : 'Adet', 'Kg', 'Lt'
- stok_durumu (VARCHAR)             : SADECE 'Yeterli' veya 'Stok Yok'

============================================================================
VIEW 2: `ai_palet_view` — Palet + lot + ürün + raf + depo birleşimi
============================================================================
- palet_id (INT), palet_no (VARCHAR), koli_adedi (INT)
- palet_kg, brut_kg, net_kg (FLOAT, NULL)
- vardiya, kaynak (VARCHAR, NULL)
- palet_durumu (VARCHAR, NULL)      : 'OLUSTURULDU','KABUL_BEKLIYOR','KABUL_EDILDI',
                                       'YERLESTIRME_BEKLIYOR','YERLESTIRILDI',
                                       'KARANTINA','IPTAL_EDILDI'
- aktif (BOOL)                      : 1 = aktif, 0 = sevk/iptal
- uretim_tarihi (DATE, NULL), uretim_hatti, makine_kodu (VARCHAR, NULL)
- palet_kayit_tarihi (DATETIME), kabul_tarihi (DATETIME, NULL)
- lot_id, lot_no, son_kullanma_tarihi (DATE, NULL)
- urun_id, urun_adi, urun_barkod, birim, kategori_adi, marka_adi
- raf_id, raf_kodu, raf_bolge, raf_koridor, raf_staging_mi (BOOL)
- depo_id, depo_adi

============================================================================
VIEW 3: `ai_lot_view` — Lot + ürün + palet özeti
============================================================================
- lot_id, lot_no, parti_no (VARCHAR, NULL)
- uretim_tarihi (DATE, NULL), son_kullanma_tarihi (DATE, NULL)
- aktif (BOOL), olusturma_tarihi (DATETIME)
- urun_id, urun_adi, birim, kategori_adi, marka_adi
- palet_sayisi (INT), toplam_koli (INT)
- skt_kalan_gun (INT, NULL)         : Bugüne göre SKT'ye kalan gün; negatifse geçmiş.

============================================================================
VIEW 4: `ai_irsaliye_view` — Çıkış (sevk) irsaliyeleri
============================================================================
- irsaliye_id, irsaliye_no, irsaliye_tarihi (DATE)
- belge_turu (VARCHAR)              : 'SevkIrsaliyesi' default
- tir_plaka, sofor_adi (VARCHAR, NULL)
- durum (VARCHAR)                   : 'Taslak','Onaylandi','Sevkedildi','Iptal'
- olusturma_tarihi (DATETIME)
- siparis_id, siparis_no, musteri_adi
- teslimat_tarihi (DATE), siparis_durumu, siparis_top_miktar, siparis_top_tutar

============================================================================
VIEW 5: `ai_mal_kabul_view` — Giriş (mal kabul) irsaliyeleri
============================================================================
- mal_kabul_id, irsaliye_no, tarih (DATE)
- durum (VARCHAR)                   : 'Taslak','Tamamlandi','Iptal' vb.
- tir_plaka, sofor_adi (VARCHAR, NULL)
- olusturma_tarihi (DATETIME)
- tedarikci_id, tedarikci_adi
- depo_id, depo_adi
- kalem_sayisi (INT), toplam_miktar (INT)

============================================================================
VIEW 6: `ai_siparis_view` — Siparişler + sevkiyat planı özeti
============================================================================
- siparis_id, siparis_no, musteri_adi
- teslimat_tarihi (DATE)
- siparis_durumu (VARCHAR)          : 'Bekleme','Hazirlaniyor','Yuklemede','Sevkedildi','Iptal'
- top_miktar (INT), top_tutar (FLOAT), aktif (BOOL)
- olusturma_tarihi (DATETIME)
- sevkiyat_id, sevkiyat_tir_plaka, sevkiyat_sofor_adi
- yukleme_tarihi (DATE), sevkiyat_durumu
- kalem_sayisi (INT), irsaliye_sayisi (INT)

============================================================================
VIEW 7: `ai_sevkiyat_view` — Sevkiyat planı + sipariş + müşteri
============================================================================
- sevkiyat_id, tir_plaka, sofor_adi, depo_kapi (VARCHAR, NULL)
- yukleme_tarihi (DATE), cikis_saati, varis_saati (VARCHAR, NULL)
- durum (VARCHAR)                   : 'Planlandi','Yuklemede','Sevkedildi','Iptal'
- olusturma_tarihi (DATETIME)
- siparis_id, siparis_no, musteri_adi, teslimat_tarihi, siparis_top_miktar

============================================================================
VIEW 8: `ai_stok_hareketi_view` — Stok hareketleri (giriş/çıkış)
============================================================================
- hareket_id, hareket_tipi (VARCHAR): 'GIRIS' veya 'CIKIS'
- miktar (INT), tarih (DATETIME)
- siparis_no, irsaliye_no, tir_plaka, depo_kapi, tasiyici_firma, aciklama
- urun_id, urun_adi, birim, kategori_adi, marka_adi
- palet_id, palet_no, lot_id, lot_no
- raf_id, raf_kodu, depo_id, depo_adi
- kullanici_id, kullanici_adi

============================================================================
VIEW 9: `ai_depo_doluluk_view` — Depo bazlı raf/palet özeti
============================================================================
- depo_id, depo_adi
- toplam_raf (INT), dolu_raf (INT), bos_raf (INT)
- aktif_palet_sayisi (INT), toplam_koli (INT)

============================================================================
HANGİ VIEW'I SEÇ?
- "stok", "ürün stoğu", "kritik stok"           => ai_stok_durumu_view
- "palet", "aktif palet", "raftaki palet"       => ai_palet_view (aktif=1 filtrele)
- "lot", "SKT", "son kullanma"                  => ai_lot_view
- "irsaliye" (çıkış/sevk), "müşteriye sevk"     => ai_irsaliye_view
- "mal kabul", "tedarikçi girişi"               => ai_mal_kabul_view
- "sipariş", "müşteri siparişi"                 => ai_siparis_view
- "sevkiyat planı", "tır", "yükleme"            => ai_sevkiyat_view
- "stok hareketi", "giriş/çıkış kaydı"          => ai_stok_hareketi_view
- "depo doluluk", "boş raf", "kapasite"         => ai_depo_doluluk_view

ÖNEMLİ KURALLAR:
1. SADECE SELECT sorgusu üret. INSERT/UPDATE/DELETE/DROP/SHOW/DESCRIBE yasak.
2. Yalnızca yukarıdaki 9 view'dan birini kullan. JOIN GEREKMEZ — view'lar zaten birleşik.
3. Yukarıda LİSTELENMEYEN kolon adı UYDURMA.
4. Aktif palet sorularında `WHERE aktif = 1` ekle (ai_palet_view'da).
5. "Son N gün" için: `tarih_kolonu >= CURDATE() - INTERVAL N DAY`.
6. `stok_durumu` filtresinde sadece 'Yeterli' veya 'Stok Yok' kullan.
7. Eşanlamlı haritası:
     - 'kritik','azalan','biten','tükenen','stoğu olmayan' => stok_durumu = 'Stok Yok'
     - 'yeterli','bol','çok','dolu'                        => stok_durumu = 'Yeterli'
     - 'kritik altında','eşiğin altında','azalmış'         => guncel_stok_miktari < kritik_stok_siniri
8. LIKE'da `%` wildcard kullan: `urun_adi LIKE '%makarna%'`.
9. Limit belirtilmediyse listeleme için `LIMIT 50` ekle. Sayım/toplam için LIMIT EKLEME.
10. Türkçe karakterleri (ç,ş,ğ,ü,ö,ı) olduğu gibi kullan.
11. Cevap SADECE SQL olsun, açıklama veya markdown KULLANMA.
12. Eğer soru yukarıdaki view'larla yanıtlanamıyorsa, en yakın view üzerinden BOŞ sonuç dönecek bir SELECT yaz (örn. `SELECT urun_id FROM ai_stok_durumu_view WHERE 1=0 LIMIT 50;`).
"""


# ----------------------------------------------------------------------------
# Türkçe few-shot örnekleri (gerçek kolon adları + gerçek enum değerleriyle)
# ----------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = [
    {
        "soru": "Stoğu olmayan ürünleri listele",
        "sql": "SELECT urun_adi, kategori_adi, guncel_stok_miktari FROM ai_stok_durumu_view WHERE stok_durumu = 'Stok Yok' LIMIT 50;",
    },
    {
        "soru": "Kritik stoktaki ürün sayısı kaç?",
        "sql": "SELECT COUNT(*) AS urun_sayisi FROM ai_stok_durumu_view WHERE stok_durumu = 'Stok Yok';",
    },
    {
        "soru": "Stok seviyesi kritik eşiğin altında olan ürünler",
        "sql": "SELECT urun_adi, guncel_stok_miktari, kritik_stok_siniri FROM ai_stok_durumu_view WHERE guncel_stok_miktari < kritik_stok_siniri ORDER BY guncel_stok_miktari ASC LIMIT 50;",
    },
    {
        "soru": "Makarna içeren ürünleri göster",
        "sql": "SELECT urun_adi, marka_adi, guncel_stok_miktari, birim FROM ai_stok_durumu_view WHERE urun_adi LIKE '%makarna%' LIMIT 50;",
    },
    {
        "soru": "Makarna kategorisinde kaç farklı ürün var?",
        "sql": "SELECT COUNT(DISTINCT urun_id) AS urun_sayisi FROM ai_stok_durumu_view WHERE kategori_adi = 'Makarna';",
    },
    {
        "soru": "ARBELLA markasının toplam stok miktarı",
        "sql": "SELECT marka_adi, SUM(guncel_stok_miktari) AS toplam_miktar FROM ai_stok_durumu_view WHERE marka_adi = 'ARBELLA' GROUP BY marka_adi;",
    },
    {
        "soru": "En çok stoğu olan 10 ürün",
        "sql": "SELECT urun_adi, guncel_stok_miktari, birim FROM ai_stok_durumu_view ORDER BY guncel_stok_miktari DESC LIMIT 10;",
    },
    {
        "soru": "Yeterli stoğu olan ürün sayısı",
        "sql": "SELECT COUNT(*) AS urun_sayisi FROM ai_stok_durumu_view WHERE stok_durumu = 'Yeterli';",
    },
    {
        "soru": "Kategoriye göre toplam ürün sayısı",
        "sql": "SELECT kategori_adi, COUNT(DISTINCT urun_id) AS urun_sayisi FROM ai_stok_durumu_view GROUP BY kategori_adi ORDER BY urun_sayisi DESC LIMIT 50;",
    },
    {
        "soru": "Barkodu boş olan ürünler",
        "sql": "SELECT urun_adi, kategori_adi FROM ai_stok_durumu_view WHERE barkod IS NULL LIMIT 50;",
    },
    {
        "soru": "stok_durumu kolonundaki değerleri ve sayılarını grupla",
        "sql": "SELECT stok_durumu, COUNT(*) AS adet FROM ai_stok_durumu_view GROUP BY stok_durumu;",
    },
    {
        "soru": "Adet biriminde satılan ürünlerden stoğu olmayanlar",
        "sql": "SELECT urun_adi, guncel_stok_miktari FROM ai_stok_durumu_view WHERE birim = 'Adet' AND stok_durumu = 'Stok Yok' LIMIT 50;",
    },
    # ----- ai_palet_view örnekleri -----
    {
        "soru": "Aktif palet sayısı kaç?",
        "sql": "SELECT COUNT(*) AS aktif_palet_sayisi FROM ai_palet_view WHERE aktif = 1;",
    },
    {
        "soru": "Yerleştirilmiş aktif palet sayısı",
        "sql": "SELECT COUNT(*) AS palet_sayisi FROM ai_palet_view WHERE aktif = 1 AND palet_durumu = 'YERLESTIRILDI';",
    },
    {
        "soru": "Karantinadaki paletleri listele",
        "sql": "SELECT palet_no, urun_adi, koli_adedi, raf_kodu FROM ai_palet_view WHERE palet_durumu = 'KARANTINA' AND aktif = 1 LIMIT 50;",
    },
    {
        "soru": "1 numaralı depodaki aktif palet sayısı",
        "sql": "SELECT COUNT(*) AS palet_sayisi FROM ai_palet_view WHERE depo_id = 1 AND aktif = 1;",
    },
    {
        "soru": "Depoya göre aktif palet dağılımı",
        "sql": "SELECT depo_adi, COUNT(*) AS palet_sayisi FROM ai_palet_view WHERE aktif = 1 GROUP BY depo_adi ORDER BY palet_sayisi DESC LIMIT 50;",
    },
    # ----- ai_lot_view örnekleri -----
    {
        "soru": "Son kullanma tarihi 30 günden az kalan lotlar",
        "sql": "SELECT lot_no, urun_adi, son_kullanma_tarihi, skt_kalan_gun FROM ai_lot_view WHERE aktif = 1 AND skt_kalan_gun IS NOT NULL AND skt_kalan_gun BETWEEN 0 AND 30 ORDER BY skt_kalan_gun ASC LIMIT 50;",
    },
    {
        "soru": "SKT'si geçmiş aktif lot sayısı",
        "sql": "SELECT COUNT(*) AS lot_sayisi FROM ai_lot_view WHERE aktif = 1 AND skt_kalan_gun < 0;",
    },
    {
        "soru": "Toplam aktif lot sayısı",
        "sql": "SELECT COUNT(*) AS lot_sayisi FROM ai_lot_view WHERE aktif = 1;",
    },
    # ----- ai_irsaliye_view örnekleri -----
    {
        "soru": "Son 7 günde oluşturulan irsaliye sayısı",
        "sql": "SELECT COUNT(*) AS irsaliye_sayisi FROM ai_irsaliye_view WHERE olusturma_tarihi >= CURDATE() - INTERVAL 7 DAY;",
    },
    {
        "soru": "Bugün sevkedilmesi planlanan irsaliyeler",
        "sql": "SELECT irsaliye_no, musteri_adi, tir_plaka, durum FROM ai_irsaliye_view WHERE irsaliye_tarihi = CURDATE() LIMIT 50;",
    },
    {
        "soru": "Taslak durumundaki irsaliye sayısı",
        "sql": "SELECT COUNT(*) AS adet FROM ai_irsaliye_view WHERE durum = 'Taslak';",
    },
    # ----- ai_mal_kabul_view örnekleri -----
    {
        "soru": "Bu ay gelen mal kabul irsaliyesi sayısı",
        "sql": "SELECT COUNT(*) AS adet FROM ai_mal_kabul_view WHERE YEAR(tarih) = YEAR(CURDATE()) AND MONTH(tarih) = MONTH(CURDATE());",
    },
    {
        "soru": "Tedarikçi bazında mal kabul irsaliye sayısı",
        "sql": "SELECT tedarikci_adi, COUNT(*) AS irsaliye_sayisi FROM ai_mal_kabul_view GROUP BY tedarikci_adi ORDER BY irsaliye_sayisi DESC LIMIT 50;",
    },
    # ----- ai_siparis_view örnekleri -----
    {
        "soru": "Bekleyen sipariş sayısı",
        "sql": "SELECT COUNT(*) AS adet FROM ai_siparis_view WHERE siparis_durumu = 'Bekleme';",
    },
    {
        "soru": "Bugünkü teslimat tarihli siparişler",
        "sql": "SELECT siparis_no, musteri_adi, top_miktar, siparis_durumu FROM ai_siparis_view WHERE teslimat_tarihi = CURDATE() LIMIT 50;",
    },
    {
        "soru": "En çok sipariş veren 10 müşteri",
        "sql": "SELECT musteri_adi, COUNT(*) AS siparis_sayisi FROM ai_siparis_view GROUP BY musteri_adi ORDER BY siparis_sayisi DESC LIMIT 10;",
    },
    # ----- ai_sevkiyat_view örnekleri -----
    {
        "soru": "Bugün yüklenecek sevkiyatlar",
        "sql": "SELECT siparis_no, musteri_adi, tir_plaka, sofor_adi, durum FROM ai_sevkiyat_view WHERE yukleme_tarihi = CURDATE() LIMIT 50;",
    },
    {
        "soru": "Planlandı durumundaki sevkiyat sayısı",
        "sql": "SELECT COUNT(*) AS adet FROM ai_sevkiyat_view WHERE durum = 'Planlandi';",
    },
    # ----- ai_stok_hareketi_view örnekleri -----
    {
        "soru": "Son 7 günde yapılan giriş hareketi sayısı",
        "sql": "SELECT COUNT(*) AS adet FROM ai_stok_hareketi_view WHERE hareket_tipi = 'GIRIS' AND tarih >= CURDATE() - INTERVAL 7 DAY;",
    },
    {
        "soru": "Bugün yapılan stok çıkışları",
        "sql": "SELECT urun_adi, miktar, palet_no, tarih FROM ai_stok_hareketi_view WHERE hareket_tipi = 'CIKIS' AND DATE(tarih) = CURDATE() ORDER BY tarih DESC LIMIT 50;",
    },
    {
        "soru": "Hareket tipine göre toplam miktar",
        "sql": "SELECT hareket_tipi, SUM(miktar) AS toplam FROM ai_stok_hareketi_view GROUP BY hareket_tipi;",
    },
    # ----- ai_depo_doluluk_view örnekleri -----
    {
        "soru": "Depoların doluluk durumu",
        "sql": "SELECT depo_adi, toplam_raf, dolu_raf, bos_raf, aktif_palet_sayisi FROM ai_depo_doluluk_view ORDER BY dolu_raf DESC LIMIT 50;",
    },
    {
        "soru": "En çok boş raf hangi depoda?",
        "sql": "SELECT depo_adi, bos_raf FROM ai_depo_doluluk_view ORDER BY bos_raf DESC LIMIT 1;",
    },
]


def render_few_shot_block() -> str:
    parts = []
    for ex in FEW_SHOT_EXAMPLES:
        parts.append(f"Soru: {ex['soru']}\nSQL: {ex['sql']}")
    return "\n\n".join(parts)


# ----------------------------------------------------------------------------
# SQL üretim sistemi promptu
# ----------------------------------------------------------------------------

SQL_SYSTEM_PROMPT = """Sen kıdemli bir MySQL veritabanı uzmanısın ve Türkçe çalışırsın.
Kullanıcının doğal dildeki sorusunu, aşağıdaki şemaya uygun TEK bir geçerli MySQL SELECT sorgusuna çevirirsin.

{schema}

KRİTİK KURALLAR:
- Cevabın SADECE ve SADECE ham MySQL kodu olsun.
- Markdown işaretleri KULLANMA: ```sql, ```, **, # gibi hiçbir markdown formatı YASAK.
- "SQLQuery:", "SQL:", "Cevap:" gibi prefix EKLEME.
- Cevap mutlaka SELECT ile başlasın ve ; ile bitsin. Arada başka hiçbir şey olmasın.
- Yukarıdaki şemada LİSTELENMEYEN kolon veya tablo ismi UYDURMA.
- Şemadaki gerçek kategorik değerlere (stok_durumu, palet_durumu, durum, hareket_tipi vb.) HARFİYEN sadık kal.
- 'kritik'/'azalan'/'biten'/'tükenen' = stok_durumu='Stok Yok' (NOT: 'Kritik Stok' literali YOK).
- 'yeterli'/'bol'/'çok'/'dolu' = stok_durumu='Yeterli'.
- hareket_tipi değerleri: 'GIRIS' veya 'CIKIS' (büyük harf).
- palet_durumu değerleri: 'OLUSTURULDU','KABUL_BEKLIYOR','KABUL_EDILDI','YERLESTIRME_BEKLIYOR','YERLESTIRILDI','KARANTINA','IPTAL_EDILDI'.
- Sadece listelenen `ai_*_view` view'larını kullan; `information_schema`, `performance_schema`, `mysql`, `sys` veya sistem tablolarını sorgulama.
- `SLEEP`, `BENCHMARK`, `LOAD_FILE`, `VERSION`, `DATABASE`, `USER`, `CURRENT_USER`, `RAND`, `UUID`, `CONNECTION_ID` gibi sistem fonksiyonlarını kullanma.
- Liste dönen sorgularda LIMIT kullan; LIMIT belirtilmediyse 50, üst sınır 200 olmalıdır.
- Boş sonuç gerektiğinde bile izinli bir view kullan; `SELECT 1`, `SELECT @@version` veya view içermeyen sorgu yazma.
"""


SQL_USER_PROMPT = """Önceki konuşma (varsa, bağlam için):
{history}

Aşağıda benzer soru/SQL çiftleri var, bunları referans al:

{examples}

Yeni soru: {soru}

SQL:"""


# ----------------------------------------------------------------------------
# Self-correction promptu
# ----------------------------------------------------------------------------

SQL_CORRECTION_PROMPT = """Aşağıdaki SQL sorgusu MySQL'de hata verdi. Şemayı ve hatayı dikkate alarak düzelt.
Cevabın SADECE düzeltilmiş SQL olsun.

{schema}

Hatalı SQL:
{sql}

MySQL hatası:
{hata}

Kullanıcının orijinal sorusu: {soru}

Düzeltilmiş SQL:"""


# ----------------------------------------------------------------------------
# Cevap üretimi few-shot örnekleri (gerçek kolonlarla)
# ----------------------------------------------------------------------------

ANSWER_FEW_SHOT_EXAMPLES = [
    {
        "soru": "Stoğu olmayan ürünleri listele",
        "sonuc": (
            "1) urun_adi=DEV Makarna 500g, kategori_adi=Makarna, guncel_stok_miktari=0\n"
            "2) urun_adi=Mini Bisküvi, kategori_adi=Atıştırmalık, guncel_stok_miktari=0\n"
            "3) urun_adi=Toz Şeker 1kg, kategori_adi=Bakliyat, guncel_stok_miktari=0"
        ),
        "cevap": "Stoğu olmayan 3 ürün var: DEV Makarna 500g, Mini Bisküvi ve Toz Şeker 1kg.",
    },
    {
        "soru": "En çok stoğu olan 3 ürün",
        "sonuc": (
            "1) urun_adi=Su 1.5L, guncel_stok_miktari=1500, birim=Adet\n"
            "2) urun_adi=Un 5kg, guncel_stok_miktari=900, birim=Adet\n"
            "3) urun_adi=Tuz 1kg, guncel_stok_miktari=700, birim=Adet"
        ),
        "cevap": "En çok stoğu olan ürünler: Su 1.5L (1500 adet), Un 5kg (900 adet) ve Tuz 1kg (700 adet).",
    },
    {
        "soru": "Kategoriye göre toplam ürün sayısı",
        "sonuc": (
            "1) kategori_adi=Makarna, urun_sayisi=12\n"
            "2) kategori_adi=Özel Seri, urun_sayisi=5\n"
            "3) kategori_adi=Küçük Kesme, urun_sayisi=3"
        ),
        "cevap": "Makarna kategorisinde 12, Özel Seri'de 5 ve Küçük Kesme'de 3 ürün bulunuyor.",
    },
    {
        "soru": "Süt içeren ürünleri göster",
        "sonuc": "(boş sonuç)",
        "cevap": "Bu kriterlere uygun kayıt bulunamadı.",
    },
]


def render_answer_few_shot_block() -> str:
    parts = []
    for ex in ANSWER_FEW_SHOT_EXAMPLES:
        parts.append(
            f"Soru: {ex['soru']}\n"
            f"Sonuç:\n{ex['sonuc']}\n"
            f"Cevap: {ex['cevap']}"
        )
    return "\n\n".join(parts)


ANSWER_SYSTEM_PROMPT = """Sen bir Türk depo yönetim asistanısın.
Kullanıcının sorusuna ve SQL sonucuna bakarak TEK PARAGRAFLIK, akıcı, doğru Türkçe bir cevap yazarsın.

KURALLAR:
- Cevabın mutlaka düzgün Türkçe olsun. Devrik veya bozuk cümle kurma.
- Cevapta SQL sonucundaki sayı ve isimleri MUTLAKA kullan. Sayıları rakamla yaz.
- Tablo, madde listesi, markdown, kod bloğu KULLANMA. Düz cümle yaz.
- En fazla 2 kısa cümle. Gereksiz açıklama yapma.
- Sonuç boşsa SADECE şunu yaz: "Bu kriterlere uygun kayıt bulunamadı."
- "var değildir" gibi bozuk ifadeler kullanma; "yok" veya "bulunamadı" kullan.
- Sonuçtaki ürün/kategori/marka isimlerini AYNEN yaz, çevirme veya değiştirme.

Aşağıdaki örnekler ideal cevap stilini gösterir:

{examples}
"""


ANSWER_USER_PROMPT = """Soru: {soru}
Sonuç:
{sonuc}

Cevap:"""


# Geriye dönük uyumluluk
ANSWER_GENERATION_PROMPT = ANSWER_USER_PROMPT
