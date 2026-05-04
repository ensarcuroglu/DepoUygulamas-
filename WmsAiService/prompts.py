"""
Prompt şablonları ve few-shot örnekleri.

Yerel/küçük LLM'lerde (phi3, qwen2.5-coder:7b vb.) SQL üretim doğruluğunu
artırmanın en etkili yolu zengin sistem prompt + Türkçe few-shot örnekleridir.
Şema açıklaması + allowed-values listesi + örnek soru/SQL çiftleri modelin
hallucination ihtimalini ciddi şekilde düşürür.
"""

# ----------------------------------------------------------------------------
# Şema açıklaması — view kolonları ve izinli değerler
# ----------------------------------------------------------------------------
# Yeni view ekledikçe buraya kolon açıklamasını ve örnek satırları ekle.

SCHEMA_DESCRIPTION = """
Veritabanı: MySQL (utf8mb4)
Erişilebilir tek view: `ai_stok_durumu_view`

Kolonlar:
- urun_id (INT)               : Ürün PK
- urun_kodu (VARCHAR)         : Ürün stok kodu (örn. 'ABC-123')
- urun_adi (VARCHAR)          : Ürün adı
- kategori_adi (VARCHAR)      : Kategori (örn. 'Gıda', 'Temizlik')
- marka_adi (VARCHAR)         : Marka adı
- birim (VARCHAR)             : Stok birimi ('adet', 'kg', 'lt')
- minimum_stok (DECIMAL)      : Tanımlı minimum stok eşiği
- toplam_stok (DECIMAL)       : Aktif paletlerdeki toplam stok miktarı
- stok_durumu (VARCHAR)       : SADECE 'Kritik Stok' veya 'Yeterli' değerini alır
- depo_adi (VARCHAR, NULL)    : Stoğun bulunduğu depo (palet yoksa NULL)
- aktif_palet_sayisi (INT)    : Ürünün aktif palet sayısı

ÖNEMLİ KURALLAR:
1. SADECE SELECT sorgusu üret. INSERT/UPDATE/DELETE/DROP yasak.
2. Sadece `ai_stok_durumu_view` view'ını kullan. Başka tablo isimleri uydurma.
3. `stok_durumu` filtresinde sadece 'Kritik Stok' veya 'Yeterli' değerlerini kullan.
4. LIKE kullanırken `%` wildcard ekle: `urun_adi LIKE '%süt%'`.
5. Sayım soruları için COUNT(*), toplam için SUM(toplam_stok) kullan.
6. Limit belirtilmediyse `LIMIT 50` ekle.
7. Türkçe karakterleri (ç,ş,ğ,ü,ö,ı) olduğu gibi kullan.
8. Sonucu sadece SQL olarak ver, açıklama veya markdown kullanma.
"""


# ----------------------------------------------------------------------------
# Türkçe few-shot örnekleri
# ----------------------------------------------------------------------------
# Çeşitli soru tiplerini kapsasın: filtreleme, agregasyon, sıralama,
# eşanlamlı kelimeler ('kritik' = 'azalan' = 'biten').

FEW_SHOT_EXAMPLES = [
    {
        "soru": "Stoğu kritik olan ürünleri listele",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok, minimum_stok FROM ai_stok_durumu_view WHERE stok_durumu = 'Kritik Stok' LIMIT 50;",
    },
    {
        "soru": "Azalan stoklar neler?",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok, minimum_stok, depo_adi FROM ai_stok_durumu_view WHERE stok_durumu = 'Kritik Stok' ORDER BY toplam_stok ASC LIMIT 50;",
    },
    {
        "soru": "Biten ürünler",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok FROM ai_stok_durumu_view WHERE toplam_stok = 0 LIMIT 50;",
    },
    {
        "soru": "Süt içeren ürünleri göster",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok, birim FROM ai_stok_durumu_view WHERE urun_adi LIKE '%süt%' LIMIT 50;",
    },
    {
        "soru": "Gıda kategorisinde kaç farklı ürün var?",
        "sql": "SELECT COUNT(DISTINCT urun_id) AS urun_sayisi FROM ai_stok_durumu_view WHERE kategori_adi = 'Gıda';",
    },
    {
        "soru": "Eti markasının toplam stoğu nedir?",
        "sql": "SELECT marka_adi, SUM(toplam_stok) AS toplam_miktar FROM ai_stok_durumu_view WHERE marka_adi = 'Eti' GROUP BY marka_adi;",
    },
    {
        "soru": "En çok stoğu olan 10 ürün",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok FROM ai_stok_durumu_view ORDER BY toplam_stok DESC LIMIT 10;",
    },
    {
        "soru": "1 numaralı depodaki kritik stoklar",
        "sql": "SELECT urun_kodu, urun_adi, toplam_stok, depo_adi FROM ai_stok_durumu_view WHERE stok_durumu = 'Kritik Stok' AND depo_adi LIKE '%1%' LIMIT 50;",
    },
    {
        "soru": "Hiç paleti olmayan ürünler",
        "sql": "SELECT urun_kodu, urun_adi FROM ai_stok_durumu_view WHERE aktif_palet_sayisi = 0 LIMIT 50;",
    },
    {
        "soru": "Kategoriye göre toplam ürün sayısı",
        "sql": "SELECT kategori_adi, COUNT(DISTINCT urun_id) AS urun_sayisi FROM ai_stok_durumu_view GROUP BY kategori_adi ORDER BY urun_sayisi DESC;",
    },
]


def render_few_shot_block() -> str:
    """Few-shot örneklerini sistem promptu içine gömülecek metne çevirir."""
    parts = []
    for ex in FEW_SHOT_EXAMPLES:
        parts.append(f"Soru: {ex['soru']}\nSQL: {ex['sql']}")
    return "\n\n".join(parts)


# ----------------------------------------------------------------------------
# SQL üretim sistemi promptu (LCEL ChatPromptTemplate ile birlikte kullanılır)
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
- Türkçe eş anlamlıları yorumla: 'kritik'='azalan'='biten'='düşük' = stok_durumu='Kritik Stok'.
- 'yeterli'='bol'='çok'='dolu' = stok_durumu='Yeterli'.
"""


SQL_USER_PROMPT = """Önceki konuşma (varsa, bağlam için):
{history}

Yeni soru: {soru}

SQL:"""


# ----------------------------------------------------------------------------
# Self-correction promptu — SQL execute edilemediğinde
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
# Cevap üretim promptu — SQL sonucunu Türkçe doğal cevaba çevirir
# ----------------------------------------------------------------------------

ANSWER_GENERATION_PROMPT = """Sen bir depo yönetim asistanısın. Kullanıcının sorusuna ve SQL sonucuna bakarak
KISA, NET ve Türkçe bir cevap yaz. Sayıları rakamla yaz. Liste uzunsa "ilk N tanesi" diye özetle.
Tablo yapma, düz metin kullan. Veri yoksa "Bu kriterlere uygun kayıt bulunamadı." de.

Soru: {soru}
Çalıştırılan SQL: {sql}
Sonuç (ilk satırlar):
{sonuc}

Cevap:"""
