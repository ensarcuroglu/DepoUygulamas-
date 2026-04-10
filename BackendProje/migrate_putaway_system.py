"""
Faz 0.5 — Putaway Sistemi Kapsamlı Migration

Tüm Faz 0 (0.1–0.4) yapısal ve veri değişikliklerini tek idempotent script'te
birleştirir. Bireysel migration scriptleri (0.2, 0.3, 0.4) daha önce çalıştırılmış
olsa da bu script tekrar çalıştırılabilir.

Adımlar:
  [DDL]
  1.  zonlar tablosunu oluştur
  2.  raflar: zon_id, max_agirlik_kg, koridor, kat, goz sütunlarını ekle
  3.  urunler: depolama_tipi sütununu ekle
  4.  yerlestirme_gorevleri tablosunu oluştur + composite index

  [DATA]
  5.  Her depo için varsayılan 6 zon oluştur
  6.  bolge → zon_id data migration
  7.  Raf kodlarını hiyerarşik formata dönüştür (KORIDOR-RAF-KAT-GOZ → ZON-KORIDOR-RAF-KAT-GOZ)
      + koridor / kat / goz alanlarını mevcut koddan parse ederek doldur
  8.  Her depo için MIGRATION_STAGING sanal rafını oluştur
  9.  Rafa atanmamış paletleri MIGRATION_STAGING rafına ata
  10. paletler.raf_id sütununu NOT NULL yap

Not (multi-depo): İlk depo (en küçük id) zone kodlarını GNL, MKB, SGK, KRN, TEH, SVK
olarak alır; ek depolar {depo_id}GNL, {depo_id}MKB, ... kodlarını alır. Bu sayede
ilk deponun mevcut raf kodları (GNL-A-12-01-01 formatı) tutarlı kalır.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?charset=utf8mb4"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı fonksiyonlar
# ─────────────────────────────────────────────────────────────────────────────

def tablo_var_mi(conn, tablo: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :t"
        ),
        {"t": tablo},
    )
    return r.scalar() > 0


def sutun_var_mi(conn, tablo: str, sutun: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
        ),
        {"t": tablo, "c": sutun},
    )
    return r.scalar() > 0


def index_var_mi(conn, tablo: str, index_adi: str) -> bool:
    r = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :i"
        ),
        {"t": tablo, "i": index_adi},
    )
    return r.scalar() > 0


def alter_ekle(conn, tablo: str, sutun: str, tanim: str) -> None:
    if sutun_var_mi(conn, tablo, sutun):
        print(f"    ↳ {tablo}.{sutun} zaten var — atlandı.")
        return
    conn.execute(text(f"ALTER TABLE {tablo} ADD COLUMN {sutun} {tanim}"))
    print(f"    ✓ {tablo}.{sutun} eklendi.")


def bolge_den_zon_tipi_cikart(bolge: str) -> str:
    """bolge string'ini ZonTipi string'ine çevirir (keyword eşleşmesi)."""
    b = (bolge or "").lower()
    if any(k in b for k in ("soğuk", "soguk", "cold", "frigor")):
        return "Soguk"
    if any(k in b for k in ("karantina", "quarantine", "krn")):
        return "Karantina"
    if any(k in b for k in ("tehlikeli", "tehlike", "hazard", "teh")):
        return "Tehlikeli"
    if any(k in b for k in ("mal kabul", "malkabul", "staging", "mkb", "giris")):
        return "MalKabul"
    if any(k in b for k in ("sevkiyat", "dispatch", "svk", "cikis")):
        return "Sevkiyat"
    return "Genel"


# ─────────────────────────────────────────────────────────────────────────────
# Adım 1 — zonlar tablosunu oluştur
# ─────────────────────────────────────────────────────────────────────────────

ZONLAR_DDL = """
CREATE TABLE IF NOT EXISTS zonlar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    depo_id INT NOT NULL,
    isim VARCHAR(100) NOT NULL,
    tip VARCHAR(30) NOT NULL,
    kod VARCHAR(10) NOT NULL,
    aciklama TEXT NULL,
    sira INT DEFAULT 0,
    aktif TINYINT(1) DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_zon_kod (kod),
    CONSTRAINT fk_zon_depo FOREIGN KEY (depo_id) REFERENCES depolar(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# ─────────────────────────────────────────────────────────────────────────────
# Adım 4 — yerlestirme_gorevleri tablosunu oluştur
# ─────────────────────────────────────────────────────────────────────────────

YERLESTIRME_GOREVLERI_DDL = """
CREATE TABLE IF NOT EXISTS yerlestirme_gorevleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    palet_id INT NOT NULL,
    mal_kabul_irsaliye_id INT DEFAULT NULL,
    tip VARCHAR(20) NOT NULL DEFAULT 'Yerlestirme',
    kaynak_raf_id INT DEFAULT NULL,
    onerilen_raf_id INT NOT NULL,
    gerceklesen_raf_id INT DEFAULT NULL,
    durum VARCHAR(20) NOT NULL DEFAULT 'Bekliyor',
    oncelik INT NOT NULL DEFAULT 5,
    atanan_kullanici_id INT DEFAULT NULL,
    override_kullanici_id INT DEFAULT NULL,
    override_neden TEXT DEFAULT NULL,
    olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    baslama_tarihi DATETIME DEFAULT NULL,
    tamamlanma_tarihi DATETIME DEFAULT NULL,
    iptal_nedeni TEXT DEFAULT NULL,
    CONSTRAINT fk_yg_palet FOREIGN KEY (palet_id) REFERENCES paletler(id),
    CONSTRAINT fk_yg_mal_kabul FOREIGN KEY (mal_kabul_irsaliye_id) REFERENCES mal_kabul_irsaliyeleri(id),
    CONSTRAINT fk_yg_kaynak_raf FOREIGN KEY (kaynak_raf_id) REFERENCES raflar(id),
    CONSTRAINT fk_yg_onerilen_raf FOREIGN KEY (onerilen_raf_id) REFERENCES raflar(id),
    CONSTRAINT fk_yg_gerceklesen_raf FOREIGN KEY (gerceklesen_raf_id) REFERENCES raflar(id),
    CONSTRAINT fk_yg_atanan_kullanici FOREIGN KEY (atanan_kullanici_id) REFERENCES kullanicilar(id),
    CONSTRAINT fk_yg_override_kullanici FOREIGN KEY (override_kullanici_id) REFERENCES kullanicilar(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# ─────────────────────────────────────────────────────────────────────────────
# Varsayılan zon tanımları
# ─────────────────────────────────────────────────────────────────────────────

VARSAYILAN_ZONLAR = [
    {"kisa_kod": "MKB", "isim": "Mal Kabul",         "tip": "MalKabul",  "sira": 1},
    {"kisa_kod": "GNL", "isim": "Genel Stok",         "tip": "Genel",     "sira": 2},
    {"kisa_kod": "SGK", "isim": "Soğuk Depo",          "tip": "Soguk",     "sira": 3},
    {"kisa_kod": "KRN", "isim": "Karantina",           "tip": "Karantina", "sira": 4},
    {"kisa_kod": "TEH", "isim": "Tehlikeli Madde",     "tip": "Tehlikeli", "sira": 5},
    {"kisa_kod": "SVK", "isim": "Sevkiyat Hazırlık",  "tip": "Sevkiyat",  "sira": 6},
]


def zon_kodu_olustur(depo_id: int, kisa_kod: str, ilk_depo_id: int) -> str:
    """
    İlk depo için düz kod (GNL, MKB, ...) döner — mevcut raf kodlarıyla uyumluluk.
    Ek depolar için {depo_id}{kisa_kod} döner (örn: 2GNL, 2MKB).
    Maks uzunluk 10 karakter (VARCHAR(10) sınırı).
    """
    if depo_id == ilk_depo_id:
        return kisa_kod
    prefix = str(depo_id)
    return f"{prefix}{kisa_kod}"[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Ana migration
# ─────────────────────────────────────────────────────────────────────────────

def calistir():
    print("=" * 60)
    print("Faz 0.5 — Putaway Sistemi Migration Başlatılıyor")
    print("=" * 60)

    with engine.begin() as conn:

        # ── Adım 1: zonlar tablosu ──────────────────────────────────────────
        print("\n[1/10] zonlar tablosu...")
        conn.execute(text(ZONLAR_DDL))
        print("    ✓ Tamamlandı (IF NOT EXISTS).")

        # ── Adım 2: raflar sütunları ────────────────────────────────────────
        print("\n[2/10] raflar sütunları...")
        alter_ekle(conn, "raflar", "zon_id",        "INT DEFAULT NULL")
        alter_ekle(conn, "raflar", "max_agirlik_kg", "FLOAT DEFAULT NULL")
        alter_ekle(conn, "raflar", "koridor",        "VARCHAR(10) DEFAULT ''")
        alter_ekle(conn, "raflar", "kat",            "INT DEFAULT 0")
        alter_ekle(conn, "raflar", "goz",            "INT DEFAULT 0")

        # FK zon_id — constraint yoksa ekle
        fk_var = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.referential_constraints "
                "WHERE constraint_schema = DATABASE() AND constraint_name = 'fk_raf_zon'"
            )
        ).scalar()
        if not fk_var:
            try:
                conn.execute(text(
                    "ALTER TABLE raflar ADD CONSTRAINT fk_raf_zon "
                    "FOREIGN KEY (zon_id) REFERENCES zonlar(id)"
                ))
                print("    ✓ raflar.zon_id FK eklendi.")
            except SQLAlchemyError as e:
                print(f"    ↳ FK eklenemedi (atlandı): {e}")

        # ── Adım 3: urunler.depolama_tipi ───────────────────────────────────
        print("\n[3/10] urunler.depolama_tipi sütunu...")
        alter_ekle(conn, "urunler", "depolama_tipi",
                   "VARCHAR(20) NOT NULL DEFAULT 'Kuru'")

        # ── Adım 4: yerlestirme_gorevleri tablosu ───────────────────────────
        print("\n[4/10] yerlestirme_gorevleri tablosu...")
        conn.execute(text(YERLESTIRME_GOREVLERI_DDL))
        print("    ✓ Tamamlandı (IF NOT EXISTS).")

        if not index_var_mi(conn, "yerlestirme_gorevleri", "ix_yg_fifo"):
            conn.execute(text(
                "CREATE INDEX ix_yg_fifo "
                "ON yerlestirme_gorevleri (durum, oncelik, olusturma_tarihi)"
            ))
            print("    ✓ ix_yg_fifo composite index eklendi.")
        else:
            print("    ↳ ix_yg_fifo zaten var — atlandı.")

        # ── Adım 5: Varsayılan zonları oluştur ──────────────────────────────
        print("\n[5/10] Varsayılan zonlar...")

        depolar = conn.execute(text("SELECT id, isim FROM depolar ORDER BY id")).fetchall()
        if not depolar:
            print("    ↳ Hiç depo bulunamadı — atlandı.")
        else:
            ilk_depo_id = depolar[0][0]
            zon_id_haritasi: dict[tuple, int] = {}  # (depo_id, tip) → zon_id

            for depo_id, depo_isim in depolar:
                for zon_tanim in VARSAYILAN_ZONLAR:
                    kod = zon_kodu_olustur(depo_id, zon_tanim["kisa_kod"], ilk_depo_id)

                    # Zaten bu depo + tip kombinasyonu var mı?
                    mevcut = conn.execute(
                        text("SELECT id FROM zonlar WHERE depo_id = :d AND tip = :t"),
                        {"d": depo_id, "t": zon_tanim["tip"]},
                    ).fetchone()

                    if mevcut:
                        zon_id_haritasi[(depo_id, zon_tanim["tip"])] = mevcut[0]
                        print(f"    ↳ Zon '{zon_tanim['tip']}' ({depo_isim}) zaten var — atlandı.")
                        continue

                    # Kod çakışması var mı?
                    kod_sahibi = conn.execute(
                        text("SELECT id FROM zonlar WHERE kod = :k"),
                        {"k": kod},
                    ).fetchone()
                    if kod_sahibi:
                        zon_id_haritasi[(depo_id, zon_tanim["tip"])] = kod_sahibi[0]
                        print(f"    ↳ Zon kodu '{kod}' zaten kullanılıyor — atlandı.")
                        continue

                    r = conn.execute(
                        text(
                            "INSERT INTO zonlar (depo_id, isim, tip, kod, sira, aktif, olusturma_tarihi) "
                            "VALUES (:d, :i, :t, :k, :s, 1, NOW())"
                        ),
                        {
                            "d": depo_id,
                            "i": zon_tanim["isim"],
                            "t": zon_tanim["tip"],
                            "k": kod,
                            "s": zon_tanim["sira"],
                        },
                    )
                    yeni_id = r.lastrowid
                    zon_id_haritasi[(depo_id, zon_tanim["tip"])] = yeni_id
                    print(f"    ✓ Zon '{kod}' ({zon_tanim['isim']}) oluşturuldu — Depo: {depo_isim}.")

        # ── Adım 6: bolge → zon_id data migration ───────────────────────────
        print("\n[6/10] bolge → zon_id data migration...")

        raflar = conn.execute(
            text("SELECT id, depo_id, bolge, zon_id FROM raflar")
        ).fetchall()

        guncellenen = 0
        for raf_id, depo_id, bolge, mevcut_zon_id in raflar:
            if mevcut_zon_id is not None:
                continue  # zaten atanmış

            zon_tipi = bolge_den_zon_tipi_cikart(bolge or "")
            # Bu depo + tip için zon_id bul
            zon_row = conn.execute(
                text("SELECT id FROM zonlar WHERE depo_id = :d AND tip = :t"),
                {"d": depo_id, "t": zon_tipi},
            ).fetchone()

            if not zon_row:
                # Genel zone'u dene
                zon_row = conn.execute(
                    text("SELECT id FROM zonlar WHERE depo_id = :d AND tip = 'Genel'"),
                    {"d": depo_id},
                ).fetchone()

            if zon_row:
                conn.execute(
                    text("UPDATE raflar SET zon_id = :z WHERE id = :r"),
                    {"z": zon_row[0], "r": raf_id},
                )
                guncellenen += 1

        print(f"    ✓ {guncellenen} raf zon_id ile güncellendi.")

        # ── Adım 7: Raf kodlarını hiyerarşik formata dönüştür ────────────────
        print("\n[7/10] Raf kodu dönüşümü + koridor/kat/goz parse...")

        raflar = conn.execute(
            text(
                "SELECT r.id, r.kod, r.koridor, r.kat, r.goz, r.depo_id, z.kod AS zon_kod "
                "FROM raflar r "
                "LEFT JOIN zonlar z ON z.id = r.zon_id AND z.tip = 'Genel'"
            )
        ).fetchall()

        kod_guncellenen = 0
        parse_guncellenen = 0
        for raf_id, raf_kod, koridor, kat, goz, depo_id, zon_kod in raflar:
            parcalar = (raf_kod or "").split("-")

            # 4-parça → 5-parça dönüşüm (örn: "A-12-01-01" → "GNL-A-12-01-01")
            if len(parcalar) == 4:
                # Bu deponun GNL zone kodunu bul
                gnl_zon = conn.execute(
                    text("SELECT kod FROM zonlar WHERE depo_id = :d AND tip = 'Genel'"),
                    {"d": depo_id},
                ).fetchone()
                prefix = gnl_zon[0] if gnl_zon else "GNL"
                yeni_kod = f"{prefix}-{raf_kod}"
                try:
                    conn.execute(
                        text("UPDATE raflar SET kod = :k WHERE id = :r"),
                        {"k": yeni_kod, "r": raf_id},
                    )
                    parcalar = yeni_kod.split("-")
                    kod_guncellenen += 1
                except SQLAlchemyError:
                    pass  # UNIQUE constraint ihlali — bu kod zaten var

            # 5-parça kod → koridor/kat/goz parse et (boşsa)
            if len(parcalar) == 5:
                yeni_koridor = parcalar[1] if not koridor else koridor
                try:
                    yeni_kat = int(parcalar[3]) if not kat else kat
                    yeni_goz = int(parcalar[4]) if not goz else goz
                except (ValueError, IndexError):
                    yeni_kat = kat or 0
                    yeni_goz = goz or 0

                if not koridor or not kat or not goz:
                    conn.execute(
                        text(
                            "UPDATE raflar SET koridor = :kor, kat = :kat, goz = :goz "
                            "WHERE id = :r"
                        ),
                        {"kor": yeni_koridor, "kat": yeni_kat, "goz": yeni_goz, "r": raf_id},
                    )
                    parse_guncellenen += 1

        print(f"    ✓ {kod_guncellenen} raf kodu 5-parça formata dönüştürüldü.")
        print(f"    ✓ {parse_guncellenen} raf için koridor/kat/goz parse edildi.")

        # ── Adım 8: MIGRATION_STAGING sanal rafı ────────────────────────────
        print("\n[8/10] MIGRATION_STAGING sanal rafları...")

        staging_raf_ids: dict[int, int] = {}  # depo_id → staging raf_id

        depolar = conn.execute(text("SELECT id, isim FROM depolar ORDER BY id")).fetchall()
        for depo_id, depo_isim in depolar:
            # MKB (Mal Kabul) zone'unu bul
            mkb_zon = conn.execute(
                text("SELECT id FROM zonlar WHERE depo_id = :d AND tip = 'MalKabul'"),
                {"d": depo_id},
            ).fetchone()
            zon_id_staging = mkb_zon[0] if mkb_zon else None

            # Staging raf kodu
            ilk_depo_id = depolar[0][0]
            mkb_kod = zon_kodu_olustur(depo_id, "MKB", ilk_depo_id)
            staging_kod = f"{mkb_kod}-X-00-00-00"

            mevcut_staging = conn.execute(
                text("SELECT id FROM raflar WHERE kod = :k"),
                {"k": staging_kod},
            ).fetchone()

            if mevcut_staging:
                staging_raf_ids[depo_id] = mevcut_staging[0]
                print(f"    ↳ MIGRATION_STAGING '{staging_kod}' zaten var ({depo_isim}) — atlandı.")
            else:
                r = conn.execute(
                    text(
                        "INSERT INTO raflar "
                        "(depo_id, zon_id, kod, bolge, kapasite, koridor, kat, goz, aktif, is_staging, olusturma_tarihi) "
                        "VALUES (:d, :z, :k, 'MIGRATION_STAGING', 9999, 'X', 0, 0, 1, 1, NOW())"
                    ),
                    {"d": depo_id, "z": zon_id_staging, "k": staging_kod},
                )
                staging_raf_ids[depo_id] = r.lastrowid
                print(f"    ✓ MIGRATION_STAGING '{staging_kod}' oluşturuldu ({depo_isim}).")

        # ── Adım 9: Rafa atanmamış paletleri MIGRATION_STAGING'e ata ────────
        print("\n[9/10] Rafa atanmamış paletler → MIGRATION_STAGING...")

        null_paletler = conn.execute(
            text(
                "SELECT p.id, l.urun_id, "
                "COALESCE( "
                "  (SELECT r2.depo_id "
                "   FROM paletler p2 "
                "   JOIN raflar r2 ON r2.id = p2.raf_id "
                "   WHERE p2.lot_id = p.lot_id AND p2.raf_id IS NOT NULL "
                "   ORDER BY p2.id DESC "
                "   LIMIT 1), "
                "  (SELECT MIN(id) FROM depolar) "
                ") AS depo_id "
                "FROM paletler p "
                "LEFT JOIN lotlar l ON l.id = p.lot_id "
                "WHERE p.raf_id IS NULL"
            )
        ).fetchall()

        if not null_paletler:
            print("    ↳ Rafa atanmamış palet yok — atlandı.")
        else:
            # Her depo için default staging raf_id
            ilk_depo_id = conn.execute(text("SELECT MIN(id) FROM depolar")).scalar()

            atanan = 0
            for palet_id, urun_id, depo_id in null_paletler:
                # Bu deponun staging rafını bul; yoksa ilk deponunkini kullan
                s_raf_id = staging_raf_ids.get(depo_id) or staging_raf_ids.get(ilk_depo_id)
                if s_raf_id:
                    conn.execute(
                        text("UPDATE paletler SET raf_id = :r WHERE id = :p"),
                        {"r": s_raf_id, "p": palet_id},
                    )
                    atanan += 1

            print(f"    ✓ {atanan} palet MIGRATION_STAGING rafına atandı.")

        # ── Adım 10: paletler.raf_id NOT NULL ───────────────────────────────
        print("\n[10/10] paletler.raf_id NOT NULL...")

        # Hâlâ NULL raf_id var mı?
        null_kalan = conn.execute(
            text("SELECT COUNT(*) FROM paletler WHERE raf_id IS NULL")
        ).scalar()

        if null_kalan > 0:
            print(f"    ⚠ {null_kalan} palette hâlâ raf_id=NULL! NOT NULL değişikliği atlandı.")
            print("      Önce bu paletlere raf atayın, sonra scripti tekrar çalıştırın.")
        else:
            # Sütunun mevcut nullable durumunu kontrol et
            col_info = conn.execute(
                text(
                    "SELECT IS_NULLABLE FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() AND table_name = 'paletler' "
                    "AND column_name = 'raf_id'"
                )
            ).fetchone()

            if col_info and col_info[0] == "NO":
                print("    ↳ raf_id zaten NOT NULL — atlandı.")
            else:
                conn.execute(text(
                    "ALTER TABLE paletler MODIFY COLUMN raf_id INT NOT NULL"
                ))
                print("    ✓ paletler.raf_id NOT NULL yapıldı.")

    print("\n" + "=" * 60)
    print("Migration tamamlandı.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        calistir()
    except Exception as e:
        print(f"\n❌ Migration başarısız: {e}")
        raise
