"""
Başlangıç Verileri (Seed Data) — Endüstriyel Depo Yönetim Sistemi v2
Veritabanını örnek verilerle doldurmak için bu scripti çalıştırın:
    python seed.py
"""

from database import SessionLocal, engine
from models import (
    Base, Marka, Kategori, Depo, Raf, Tedarikci,
    Urun, Lot, Palet, StokHareketi, Kullanici
)
from passlib.context import CryptContext
from datetime import datetime, timedelta, date
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Mevcut veri varsa işlemi atla
        if db.query(Marka).count() > 0:
            print("⚠️  Veritabanında zaten veri var. Seed işlemi atlandı.")
            return

        print("🌱 Endüstriyel başlangıç verileri oluşturuluyor...\n")

        # ==================
        # MARKALAR
        # ==================
        markalar = [
            Marka(isim="ARBELLA", aciklama="Makarna ve gıda ürünleri"),
            Marka(isim="PASTAWILLA", aciklama="Premium makarna markası"),
            Marka(isim="KARTAL", aciklama="Geleneksel makarna"),
        ]
        db.add_all(markalar)
        db.flush()
        print(f"  ✅ {len(markalar)} marka eklendi")

        # ==================
        # KATEGORİLER
        # ==================
        kategoriler = [
            Kategori(isim="Makarna", aciklama="Tüm makarna çeşitleri"),
            Kategori(isim="Şehriye", aciklama="İnce ve kalın şehriye çeşitleri"),
            Kategori(isim="Küçük Kesme", aciklama="Küçük kesme makarna çeşitleri"),
            Kategori(isim="Glutensiz", aciklama="Glutensiz ürünler"),
            Kategori(isim="Özel Seri", aciklama="Premium ve özel üretim serisi"),
        ]
        db.add_all(kategoriler)
        db.flush()
        print(f"  ✅ {len(kategoriler)} kategori eklendi")

        # ==================
        # DEPOLAR
        # ==================
        depolar = [
            Depo(isim="Ana Depo", adres="Organize Sanayi Bölgesi 1. Cadde No:12", aciklama="Ana üretim deposu"),
            Depo(isim="Sevkiyat Deposu", adres="Organize Sanayi Bölgesi 2. Cadde No:5", aciklama="Sevkiyat ve dağıtım"),
        ]
        db.add_all(depolar)
        db.flush()
        print(f"  ✅ {len(depolar)} depo eklendi")

        # ==================
        # RAFLAR
        # ==================
        raflar = [
            Raf(depo_id=1, kod="A-01", bolge="Zemin Kat", kapasite=200),
            Raf(depo_id=1, kod="A-05", bolge="Zemin Kat", kapasite=150),
            Raf(depo_id=1, kod="A-12", bolge="Üst Kat", kapasite=100),
            Raf(depo_id=1, kod="B-04", bolge="Soğuk Depo", kapasite=80),
            Raf(depo_id=2, kod="S-01", bolge="Sevkiyat Alanı", kapasite=300),
            Raf(depo_id=2, kod="S-02", bolge="Sevkiyat Alanı", kapasite=250),
        ]
        db.add_all(raflar)
        db.flush()
        print(f"  ✅ {len(raflar)} raf eklendi")

        # ==================
        # TEDARİKÇİLER
        # ==================
        tedarikciler = [
            Tedarikci(firma_adi="Arbella Gıda A.Ş.", iletisim_kisi="Mehmet Demir",
                      telefon="0212-555-0001", email="mehmet@arbella.com",
                      adres="İstanbul, Esenyurt", vergi_no="1234567890"),
            Tedarikci(firma_adi="PastaWilla Ltd.", iletisim_kisi="Ayşe Yıldız",
                      telefon="0216-555-0002", email="ayse@pastawilla.com",
                      adres="İstanbul, Tuzla", vergi_no="0987654321"),
        ]
        db.add_all(tedarikciler)
        db.flush()
        print(f"  ✅ {len(tedarikciler)} tedarikçi eklendi")

        # ==================
        # ÜRÜNLER
        # ==================
        urunler = [
            Urun(isim="Yüksük", marka_id=1, kategori_id=1, tedarikci_id=1,
                 ean="8697430089416", barkod="ARB-001",
                 ic_adet=20, gramaj=0.5, birim="Adet", fiyat=18.50, min_stok=50,
                 aciklama="Arbella Yüksük Makarna 500g"),
            Urun(isim="Küçük Çizgili", marka_id=1, kategori_id=3, tedarikci_id=1,
                 ean="8697430089767", barkod="ARB-002",
                 ic_adet=20, gramaj=0.5, birim="Adet", fiyat=18.50, min_stok=50,
                 aciklama="Arbella Küçük Çizgili Makarna 500g"),
            Urun(isim="Domateslı Burgu", marka_id=1, kategori_id=1, tedarikci_id=1,
                 ean="8697430089446", barkod="ARB-003",
                 ic_adet=20, gramaj=0.067, birim="Adet", fiyat=22.00, min_stok=30,
                 aciklama="Arbella Domatesli Burgu Makarna"),
            Urun(isim="Boncuk", marka_id=1, kategori_id=2, tedarikci_id=1,
                 ean="8697430089416", barkod="ARB-004",
                 ic_adet=20, gramaj=0.5, birim="Adet", fiyat=16.00, min_stok=40,
                 aciklama="Arbella Boncuk Şehriye 500g"),
            Urun(isim="1.7MM SPG", marka_id=1, kategori_id=1, tedarikci_id=1,
                 ean="8690684001039", barkod="ARB-005",
                 ic_adet=20, gramaj=1.0, birim="Adet", fiyat=35.00, min_stok=30,
                 aciklama="Arbella 1.7mm Spagetti 1kg"),
            Urun(isim="Veggi Pasta (Glutensiz)", marka_id=2, kategori_id=4, tedarikci_id=2,
                 ean=None, barkod="PW-001",
                 ic_adet=1, gramaj=0.35, birim="Adet", fiyat=45.00, min_stok=20,
                 aciklama="Pastawilla Veggi Pasta Glutensiz 350g"),
            Urun(isim="Sevimli Raka", marka_id=2, kategori_id=5, tedarikci_id=2,
                 ean=None, barkod="PW-002",
                 ic_adet=12, gramaj=0.35, birim="Adet", fiyat=28.00, min_stok=25,
                 aciklama="Pastawilla Sevimli Raka Makarna 350g"),
            Urun(isim="Rigatoni", marka_id=2, kategori_id=1, tedarikci_id=2,
                 ean="8690684910362", barkod="PW-003",
                 ic_adet=12, gramaj=0.5, birim="Adet", fiyat=32.00, min_stok=20,
                 aciklama="Pastawilla Rigatoni / Burgu 500g"),
            Urun(isim="Kelebek", marka_id=2, kategori_id=5, tedarikci_id=2,
                 ean=None, barkod="PW-004",
                 ic_adet=5, gramaj=0.5, birim="Adet", fiyat=30.00, min_stok=30,
                 aciklama="Pastawilla Kelebek Makarna 500g"),
            Urun(isim="Kalem Kesme", marka_id=1, kategori_id=3, tedarikci_id=1,
                 ean="0869743008213", barkod="ARB-006",
                 ic_adet=10, gramaj=1.0, birim="Adet", fiyat=38.00, min_stok=20,
                 aciklama="Arbella Kalem Kesme Makarna 1kg"),
            Urun(isim="Glutensiz Spagetti", marka_id=1, kategori_id=4, tedarikci_id=1,
                 ean="5941634000712", barkod="ARB-007",
                 ic_adet=12, gramaj=0.4, birim="Adet", fiyat=42.00, min_stok=15,
                 aciklama="Arbella Glutensiz Spagetti 400g"),
            Urun(isim="Midye", marka_id=1, kategori_id=1, tedarikci_id=1,
                 ean="8697430088425", barkod="ARB-008",
                 ic_adet=20, gramaj=0.5, birim="Adet", fiyat=19.00, min_stok=40,
                 aciklama="Arbella Midye Makarna 500g"),
        ]
        db.add_all(urunler)
        db.flush()
        print(f"  ✅ {len(urunler)} ürün eklendi")

        # ==================
        # KULLANICILAR
        # ==================
        admin = Kullanici(
            kullanici_adi="admin",
            sifre_hash=pwd_context.hash("admin123"),
            ad_soyad="Sistem Yöneticisi",
            rol="admin"
        )
        depocu = Kullanici(
            kullanici_adi="depocu1",
            sifre_hash=pwd_context.hash("depo123"),
            ad_soyad="Ahmet Yılmaz",
            rol="depocu"
        )
        db.add_all([admin, depocu])
        db.flush()
        print(f"  ✅ 2 kullanıcı eklendi (admin / depocu1)")

        # ==================
        # LOTLAR ve PALETLER
        # ==================
        now = datetime.utcnow()
        palet_sayac = 1000001
        toplam_lot = 0
        toplam_palet = 0

        for urun in urunler:
            # Her ürün için 1-3 lot oluştur
            lot_sayisi = random.randint(1, 3)
            for j in range(lot_sayisi):
                uretim = date.today() - timedelta(days=random.randint(10, 180))
                skt = uretim + timedelta(days=random.randint(365, 1095))  # 1-3 yıl SKT

                lot = Lot(
                    urun_id=urun.id,
                    lot_no=f"{random.randint(8690000000000, 8699999999999)}",
                    parti_no=f"P-{random.randint(1000, 9999)}",
                    uretim_tarihi=uretim,
                    son_kullanma_tarihi=skt,
                    aciklama=f"{urun.isim} - Üretim partisi"
                )
                db.add(lot)
                db.flush()
                toplam_lot += 1

                # Her lot için 1-4 palet oluştur
                palet_sayisi = random.randint(1, 4)
                for k in range(palet_sayisi):
                    raf_id = random.choice([r.id for r in raflar])
                    koli = random.choice([23, 34, 45, 54, 56])
                    palet_kg_val = round(koli * urun.gramaj * urun.ic_adet, 2) if urun.gramaj else round(koli * 5, 2)
                    vardiya_sec = random.choice(["fg", "ghjg", "fgdfg", "hjhjg", None])

                    palet = Palet(
                        lot_id=lot.id,
                        raf_id=raf_id,
                        palet_no=str(palet_sayac),
                        koli_adedi=koli,
                        palet_kg=palet_kg_val,
                        vardiya=vardiya_sec,
                        tarih=now - timedelta(days=random.randint(0, 30)),
                        aktif=True
                    )
                    db.add(palet)
                    palet_sayac += 1
                    toplam_palet += 1

        db.flush()
        print(f"  ✅ {toplam_lot} lot eklendi")
        print(f"  ✅ {toplam_palet} palet eklendi")

        # ==================
        # STOK HAREKETLERİ (Son 30 gün)
        # ==================
        hareketler = []
        for i in range(40):
            tarih = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 12))
            urun = random.choice(urunler)
            tip = random.choice(["giris", "cikis"])
            miktar = random.randint(1, 20)

            hareketler.append(StokHareketi(
                urun_id=urun.id,
                hareket_tipi=tip,
                miktar=miktar,
                aciklama=f"{'Tedarikçiden alım' if tip == 'giris' else 'Müşteriye sevk'}",
                kullanici_id=random.choice([1, 2]),
                tarih=tarih
            ))

        db.add_all(hareketler)
        print(f"  ✅ {len(hareketler)} stok hareketi eklendi (son 30 gün)")

        db.commit()
        print("\n🎉 Endüstriyel başlangıç verileri başarıyla oluşturuldu!")
        print("   Kullanıcılar:")
        print("   - admin / admin123 (Yönetici)")
        print("   - depocu1 / depo123 (Depocu)")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
