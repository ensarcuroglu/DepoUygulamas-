from tests.factories.kullanici_factory import KullaniciFactory
from tests.factories.marka_factory import MarkaFactory
from tests.factories.kategori_factory import KategoriFactory
from tests.factories.depo_factory import DepoFactory
from tests.factories.raf_factory import RafFactory
from tests.factories.tedarikci_factory import TedarikciFactory
from tests.factories.urun_factory import UrunFactory
from tests.factories.lot_factory import LotFactory
from tests.factories.palet_factory import PaletFactory
from tests.factories.stok_hareketi_factory import StokHareketiFactory
from tests.factories.siparis_factory import SiparisFactory, SiparisKalemiFactory
from tests.factories.sevkiyat_plani_factory import SevkiyatPlaniFactory
from tests.factories.irsaliye_factory import IrsaliyeFactory
from tests.factories.rapor_sablonu_factory import RaporSablonuFactory, RaporLoguFactory, RaporScheduleFactory
from tests.factories.stok_sayim_factory import StokSayimFactory, StokSayimKalemiFactory

ALL_FACTORIES = [
    KullaniciFactory, MarkaFactory, KategoriFactory, DepoFactory,
    RafFactory, TedarikciFactory, UrunFactory, LotFactory,
    PaletFactory, StokHareketiFactory,
    SiparisFactory, SiparisKalemiFactory,
    SevkiyatPlaniFactory, IrsaliyeFactory,
    RaporSablonuFactory, RaporLoguFactory, RaporScheduleFactory,
    StokSayimFactory, StokSayimKalemiFactory,
]

__all__ = [
    "KullaniciFactory",
    "MarkaFactory",
    "KategoriFactory",
    "DepoFactory",
    "RafFactory",
    "TedarikciFactory",
    "UrunFactory",
    "LotFactory",
    "PaletFactory",
    "StokHareketiFactory",
    "SiparisFactory",
    "SiparisKalemiFactory",
    "SevkiyatPlaniFactory",
    "IrsaliyeFactory",
    "RaporSablonuFactory",
    "RaporLoguFactory",
    "RaporScheduleFactory",
    "StokSayimFactory",
    "StokSayimKalemiFactory",
    "ALL_FACTORIES",
]
