from .marka_repository import IMarkaRepository
from .kategori_repository import IKategoriRepository
from .depo_repository import IDepoRepository
from .raf_repository import IRafRepository
from .tedarikci_repository import ITedarikciRepository
from .urun_repository import IUrunRepository
from .lot_repository import ILotRepository
from .palet_repository import IPaletRepository
from .stok_hareketi_repository import IStokHareketiRepository
from .kullanici_repository import IKullaniciRepository
from .sistem_log_repository import ISistemLogRepository
from .destek_talebi_repository import IDestekTalebiRepository
from .siparis_repository import ISiparisRepository
from .sevkiyat_plani_repository import ISevkiyatPlaniRepository
from .irsaliye_repository import IIrsaliyeRepository
from .rapor_repository import IRaporSablonuRepository, IRaporLoguRepository, IRaporScheduleRepository
from .stok_sayim_repository import IStokSayimRepository
from .dashboard_repository import IDashboardRepository

__all__ = [
    "IMarkaRepository", "IKategoriRepository", "IDepoRepository",
    "IRafRepository", "ITedarikciRepository", "IUrunRepository",
    "ILotRepository", "IPaletRepository", "IStokHareketiRepository",
    "IKullaniciRepository", "ISistemLogRepository", "IDestekTalebiRepository",
    "ISiparisRepository", "ISevkiyatPlaniRepository", "IIrsaliyeRepository",
    "IRaporSablonuRepository", "IRaporLoguRepository", "IRaporScheduleRepository",
    "IStokSayimRepository",
    "IDashboardRepository",
]
