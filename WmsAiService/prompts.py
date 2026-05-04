"""
Prompt şablonları ve few-shot örnekleri.

Yerel/küçük LLM'lerde (phi3 vb.) SQL üretim doğruluğunu artırmanın en etkili
yolu zengin sistem prompt + Türkçe few-shot örnekleridir. Şema açıklaması +
allowed-values listesi + örnek soru/SQL çiftleri modelin hallucination
ihtimalini ciddi şekilde düşürür.
"""

# ----------------------------------------------------------------------------
# Şema açıklaması — view kolonları ve izinli değerler (gerçek DB şemasına göre)
# ----------------------------------------------------------------------------

SCHEMA_DESCRIPTION = """
Veritabanı: MySQL (utf8mb4)
Erişilebilir tek view: `ai_stok_durumu_view`

Kolonlar (TAMAMI):
- urun_id (INT)                       : Ürün PK
- urun_adi (VARCHAR(200))             : Ürün adı (örn. 'DEV Makarna 500g')
- barkod (VARCHAR(50), NULL)          : Ürün barkodu
- kategori_adi (VARCHAR(100), NULL)   : Kategori (örn. 'Makarna', 'Özel Seri', 'Küçük Kesme')
- marka_adi (VARCHAR(100), NULL)      : Marka (örn. 'ARBELLA')
- guncel_stok_miktari (DECIMAL)       : Mevcut/güncel stok miktarı
- kritik_stok_siniri (INT)            : Kritik stok eşiği (bu değerin altı = azalmış stok)
- birim (VARCHAR(20))                 : 'Adet', 'Kg', 'Lt' gibi (Büyük harfle başlar)
- stok_durumu (VARCHAR(11))           : SADECE iki değer alır: 'Yeterli' veya 'Stok Yok'

ÖNEMLİ KURALLAR:
1. SADECE SELECT sorgusu üret. INSERT/UPDATE/DELETE/DROP/SHOW/DESCRIBE yasak.
2. Sadece `ai_stok_durumu_view` view'ını kullan. Başka tablo/view ismi UYDURMA.
3. Yukarıda LİSTELENMEYEN kolon adı UYDURMA. ('urun_kodu', 'toplam_stok', 'minimum_stok', 'depo_adi', 'aktif_palet_sayisi' YOKTUR.)
4. `stok_durumu` filtresinde sadece 'Yeterli' veya 'Stok Yok' kullan.
5. Eşanlamlı haritası:
     - 'kritik', 'azalan', 'biten', 'tükenen', 'stok yok', 'stoğu olmayan'
       => `stok_durumu = 'Stok Yok'`
     - 'yeterli', 'bol', 'çok', 'dolu'
       => `stok_durumu = 'Yeterli'`
     - 'kritik altında', 'eşiğin altında', 'azalmış'
       => `guncel_stok_miktari < kritik_stok_siniri`
6. LIKE kullanırken `%` wildcard ekle: `urun_adi LIKE '%makarna%'`.
7. Sayım için COUNT(*), toplam için SUM(guncel_stok_miktari) kullan.
8. Limit belirtilmediyse `LIMIT 50` ekle.
9. Türkçe karakterleri (ç,ş,ğ,ü,ö,ı) olduğu gibi kullan.
10. Cevap SADECE SQL olsun, açıklama veya markdown KULLANMA.
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

Aşağıda örnek soru/SQL çiftleri var. Bunları referans al:

{examples}

KURALLAR:
- Cevabın SADECE SQL sorgusu olsun. Açıklama, markdown, "SQLQuery:" gibi prefix EKLEME.
- Cevap mutlaka `SELECT` ile başlasın ve `;` ile bitsin.
- Yukarıda olmayan kolon veya tablo ismi UYDURMA.
- 'kritik'/'azalan'/'biten'/'tükenen' = stok_durumu='Stok Yok' (NOT: 'Kritik Stok' literali YOK).
- 'yeterli'/'bol'/'çok'/'dolu' = stok_durumu='Yeterli'.
"""


SQL_USER_PROMPT = """Önceki konuşma (varsa, bağlam için):
{history}

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
