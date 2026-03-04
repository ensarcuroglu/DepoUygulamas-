"""
Başlangıç Verileri (Seed Data)
Veritabanını örnek verilerle doldurmak için bu scripti çalıştırın:
    python seed.py
"""

from database import SessionLocal, engine
from models import Base, Kategori, Raf, Urun, StokHareketi, Kullanici
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Mevcut veri varsa işlemi atla
        if db.query(Kategori).count() > 0:
            print("⚠️  Veritabanında zaten veri var. Seed işlemi atlandı.")
            return

        print("🌱 Başlangıç verileri oluşturuluyor...\n")

        # ==================
        # KATEGORİLER
        # ==================
        kategoriler = [
            Kategori(isim="Otomasyon", aciklama="Sensörler, PLC modülleri ve otomasyon bileşenleri"),
            Kategori(isim="Mekanik", aciklama="Robot kolları, eklemler ve mekanik parçalar"),
            Kategori(isim="Motor", aciklama="AC/DC motorlar, servo motorlar"),
            Kategori(isim="Elektronik", aciklama="Kontrol kartları, güç kaynakları, kablolar"),
            Kategori(isim="Paketleme", aciklama="Bantlama, etiketleme ve paketleme malzemeleri"),
            Kategori(isim="Hidrolik", aciklama="Hidrolik silindirler, pompalar ve valfler"),
        ]
        db.add_all(kategoriler)
        db.flush()
        print(f"  ✅ {len(kategoriler)} kategori eklendi")

        # ==================
        # RAFLAR
        # ==================
        raflar = [
            Raf(kod="A-01", bolge="Depo-1 Zemin", kapasite=200),
            Raf(kod="A-05", bolge="Depo-1 Zemin", kapasite=150),
            Raf(kod="A-12", bolge="Depo-1 Üst Kat", kapasite=100),
            Raf(kod="B-04", bolge="Depo-2 Zemin", kapasite=80),
            Raf(kod="B-08", bolge="Depo-2 Zemin", kapasite=120),
            Raf(kod="C-01", bolge="Depo-3 Motor Alanı", kapasite=50),
            Raf(kod="C-06", bolge="Depo-3 Motor Alanı", kapasite=60),
            Raf(kod="D-02", bolge="Dış Alan", kapasite=300),
        ]
        db.add_all(raflar)
        db.flush()
        print(f"  ✅ {len(raflar)} raf eklendi")

        # ==================
        # ÜRÜNLER
        # ==================
        urunler = [
            Urun(isim="Optik Sensör (Mesafe)", barkod="OPT-001", kategori_id=1, raf_id=3,
                 stok_miktari=145, min_stok=20, birim="Adet", fiyat=85.50,
                 aciklama="Mesafe ölçümü için endüstriyel optik sensör"),
            Urun(isim="Paletleme Robot Kolu Eklemi", barkod="MKN-002", kategori_id=2, raf_id=4,
                 stok_miktari=4, min_stok=10, birim="Adet", fiyat=2450.00,
                 aciklama="6 eksenli paletleme robotu için yedek eklem"),
            Urun(isim="Koli Bantlama Motoru (AC)", barkod="MTR-003", kategori_id=3, raf_id=6,
                 stok_miktari=34, min_stok=5, birim="Adet", fiyat=720.00,
                 aciklama="Otomatik koli bantlama hattı için AC motor"),
            Urun(isim="PLC Kontrol Modülü", barkod="ELK-004", kategori_id=4, raf_id=2,
                 stok_miktari=8, min_stok=15, birim="Adet", fiyat=1850.00,
                 aciklama="Siemens S7-1200 serisi PLC modülü"),
            Urun(isim="Endüstriyel Etiket Yazıcı Kafası", barkod="PKT-005", kategori_id=5, raf_id=1,
                 stok_miktari=12, min_stok=5, birim="Adet", fiyat=340.00,
                 aciklama="Termal transfer etiket yazıcı yedek kafası"),
            Urun(isim="Servo Motor (1.5kW)", barkod="MTR-006", kategori_id=3, raf_id=7,
                 stok_miktari=22, min_stok=8, birim="Adet", fiyat=980.00,
                 aciklama="Yüksek hassasiyetli servo motor"),
            Urun(isim="Kapasitif Yakınlık Sensörü", barkod="OPT-007", kategori_id=1, raf_id=3,
                 stok_miktari=67, min_stok=15, birim="Adet", fiyat=125.00,
                 aciklama="Metal ve plastik algılama için kapasitif sensör"),
            Urun(isim="Hidrolik Silindir (50mm)", barkod="HDR-008", kategori_id=6, raf_id=8,
                 stok_miktari=3, min_stok=5, birim="Adet", fiyat=1200.00,
                 aciklama="Çift etkili hidrolik silindir"),
            Urun(isim="Güç Kaynağı 24V/10A", barkod="ELK-009", kategori_id=4, raf_id=2,
                 stok_miktari=45, min_stok=10, birim="Adet", fiyat=195.00,
                 aciklama="Endüstriyel 24V DC güç kaynağı"),
            Urun(isim="Konveyör Bant (1m)", barkod="MKN-010", kategori_id=2, raf_id=5,
                 stok_miktari=18, min_stok=5, birim="Metre", fiyat=450.00,
                 aciklama="PVC konveyör bandı, genişlik 60cm"),
            Urun(isim="Pnömatik Valf (5/2)", barkod="HDR-011", kategori_id=6, raf_id=8,
                 stok_miktari=30, min_stok=10, birim="Adet", fiyat=275.00,
                 aciklama="5 yollu 2 konumlu pnömatik yön kontrol valfi"),
            Urun(isim="Shrink Ambalaj Filmi", barkod="PKT-012", kategori_id=5, raf_id=1,
                 stok_miktari=200, min_stok=50, birim="Rulo", fiyat=65.00,
                 aciklama="Isıyla daralan ambalaj filmi, 50cm genişlik"),
        ]
        db.add_all(urunler)
        db.flush()
        print(f"  ✅ {len(urunler)} ürün eklendi")

        # ==================
        # KULLANICI
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
        # STOK HAREKETLERİ (Son 30 gün)
        # ==================
        hareketler = []
        now = datetime.utcnow()
        for i in range(30):
            tarih = now - timedelta(days=i, hours=random.randint(0, 12))
            urun_id = random.randint(1, len(urunler))
            tip = random.choice(["giris", "cikis"])
            miktar = random.randint(1, 20)

            hareketler.append(StokHareketi(
                urun_id=urun_id,
                hareket_tipi=tip,
                miktar=miktar,
                aciklama=f"{'Tedarikçiden alım' if tip == 'giris' else 'Üretime sevk'}",
                kullanici_id=random.choice([1, 2]),
                tarih=tarih
            ))

        db.add_all(hareketler)
        print(f"  ✅ {len(hareketler)} stok hareketi eklendi (son 30 gün)")

        db.commit()
        print("\n🎉 Başlangıç verileri başarıyla oluşturuldu!")
        print("   Kullanıcılar:")
        print("   - admin / admin123 (Yönetici)")
        print("   - depocu1 / depo123 (Depocu)")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Hata oluştu: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
