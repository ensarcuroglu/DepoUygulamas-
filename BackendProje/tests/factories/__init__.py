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

ALL_FACTORIES = [
    KullaniciFactory, MarkaFactory, KategoriFactory, DepoFactory,
    RafFactory, TedarikciFactory, UrunFactory, LotFactory,
    PaletFactory, StokHareketiFactory,
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
    "ALL_FACTORIES",
]
