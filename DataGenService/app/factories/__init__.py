"""Sentetik veri üretici factory katmanı.

Her factory deterministik bir Pydantic DTO üretir. Aynı (seed, count, overrides)
girdisiyle iki ayrı koşum byte-by-byte aynı çıktıyı verir.
"""

from .base import BaseFactory, ReferenceTable
from .lot_factory import LotFactory
from .palet_factory import PaletFactory
from .performans_event_factory import PerformansEventFactory
from .raf_factory import RafFactory
from .schemas import (
    LotDTO,
    PaletDTO,
    PerformansEventDTO,
    RafDTO,
    SiparisDTO,
    SiparisKalemDTO,
    TalepGecmisKaydiDTO,
    ToplamaGoreviDTO,
    UrunDTO,
    YerlestirmeGoreviDTO,
)
from .siparis_factory import SiparisFactory
from .talep_zaman_serisi_factory import TalepZamanSerisiFactory
from .toplama_gorev_factory import ToplamaGorevFactory
from .urun_factory import UrunFactory
from .yerlestirme_gorev_factory import YerlestirmeGorevFactory

__all__ = [
    # Base
    "BaseFactory",
    "ReferenceTable",
    # Schemas
    "UrunDTO",
    "RafDTO",
    "LotDTO",
    "PaletDTO",
    "SiparisDTO",
    "SiparisKalemDTO",
    "YerlestirmeGoreviDTO",
    "ToplamaGoreviDTO",
    "PerformansEventDTO",
    "TalepGecmisKaydiDTO",
    # Factories
    "UrunFactory",
    "RafFactory",
    "LotFactory",
    "PaletFactory",
    "SiparisFactory",
    "YerlestirmeGorevFactory",
    "ToplamaGorevFactory",
    "PerformansEventFactory",
    "TalepZamanSerisiFactory",
]
