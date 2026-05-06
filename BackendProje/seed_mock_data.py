import sys
import random
import time
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Depo

# Tüm factory'leri import ediyoruz
from tests.factories.base_factory import BaseFactory
from tests.factories.kategori_factory import KategoriFactory
from tests.factories.marka_factory import MarkaFactory
from tests.factories.tedarikci_factory import TedarikciFactory
from tests.factories.depo_factory import DepoFactory
from tests.factories.zon_factory import ZonFactory
from tests.factories.raf_factory import RafFactory
from tests.factories.urun_factory import UrunFactory
from tests.factories.lot_factory import LotFactory
from tests.factories.palet_factory import PaletFactory
from tests.factories.kullanici_factory import KullaniciFactory

ALL_FACTORIES = [
    KategoriFactory, MarkaFactory, TedarikciFactory,
    DepoFactory, ZonFactory, RafFactory,
    UrunFactory, LotFactory, PaletFactory, KullaniciFactory,
]

def set_factory_session(db: Session):
    """
    Normalde factory'ler test yazarken conftest.py üzerinden test DB'sine bağlanır.
    Gerçek veritabanına yazabilmek için BaseFactory'nin session'ını manuel atıyoruz.
    """
    for f in ALL_FACTORIES:
        f._meta.sqlalchemy_session = db


def bump_factory_sequences():
    # Zaman damgasını 1000 ile çarparak her saniye arasında 1000'lik bir boşluk yaratıyoruz.
    # Böylece tek seferde 1000'den az kayıt ürettiğin sürece çakışma yaşanmaz.
    offset = int(time.time() * 1000) % 10**8
    for f in ALL_FACTORIES:
        f.reset_sequence(offset)
    print(f"🔢 Factory sequence offset: {offset}")

def generate_mock_data():
    db = SessionLocal()
    set_factory_session(db)
    bump_factory_sequences()

    try:
        print("🚀 Veritabanı seed işlemi başlatılıyor...")

        # 1. BAĞIMSIZ VERİLER (Kategori, Marka, Tedarikci)
        print("📦 Kategoriler, Markalar ve Tedarikçiler oluşturuluyor...")
        kategoriler = KategoriFactory.create_batch(5)
        markalar = MarkaFactory.create_batch(10)
        tedarikciler = TedarikciFactory.create_batch(5)

        # 2. DEPO HİYERARŞİSİ (Depo -> Zon -> Raf)
        print("🏢 Depo, Zon ve Raflar oluşturuluyor...")
        # "Merkez Depo" varsa onu kullan; yoksa oluştur (isim UNIQUE)
        ana_depo = db.query(Depo).filter(Depo.isim == "Merkez Depo").first()
        if ana_depo is None:
            ana_depo = DepoFactory(isim="Merkez Depo")
        else:
            print("   ↪ Mevcut 'Merkez Depo' kullanılıyor.")
        zonlar = ZonFactory.create_batch(3, depo=ana_depo)
        raflar = []
        for zon in zonlar:
            # Her zona 10'ar raf ekle
            raflar.extend(RafFactory.create_batch(10, zon=zon, depo=ana_depo))

        # 3. ÜRÜNLER (Ürünler kategori ve markalara bağlanır)
        print("🏷️ Ürünler oluşturuluyor...")
        urunler = []
        for _ in range(50):
            urunler.append(
                UrunFactory(
                    kategori=random.choice(kategoriler),
                    marka=random.choice(markalar)
                )
            )

        # 4. LOT VE PALETLER (Paletler raflara ve lotlara bağlanır)
        print("🟩 Lotlar ve Paletler raflara yerleştiriliyor...")
        toplam_palet = 0
        for urun in urunler:
            # Her ürün için 1-3 arası Lot oluştur
            lotlar = LotFactory.create_batch(random.randint(1, 3), urun=urun)
            
            for lot in lotlar:
                # Her lot için 2-5 arası palet oluştur ve rastgele raflara koy
                palet_sayisi = random.randint(2, 5)
                PaletFactory.create_batch(
                    palet_sayisi,
                    lot=lot,
                    raf=random.choice(raflar),
                    aktif=True
                )
                toplam_palet += palet_sayisi

        db.commit()
        print(f"✅ İşlem Tamamlandı!")
        print(f"📊 Özet: 1 Depo, {len(zonlar)} Zon, {len(raflar)} Raf, {len(urunler)} Ürün, {toplam_palet} Aktif Palet üretildi.")

    except Exception as e:
        db.rollback()
        print(f"❌ Bir hata oluştu ve işlemler geri alındı (Rollback): {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    generate_mock_data()