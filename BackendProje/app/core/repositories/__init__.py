from .marka_repository import IMarkaRepository
from .kategori_repository import IKategoriRepository
from .depo_repository import IDepoRepository
from .zon_repository import IZonRepository
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
from .mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from .toplama_gorevi_repository import IToplamaGoreviRepository
from .palet_rezervasyonu_repository import IPaletRezervasyonuRepository
from .uretim_seri_sayac_repository import IUretimSeriSayacRepository
from .palet_durum_log_repository import IPaletDurumLogRepository

__all__ = [
    "IMarkaRepository", "IKategoriRepository", "IDepoRepository", "IZonRepository",
    "IRafRepository", "ITedarikciRepository", "IUrunRepository",
    "ILotRepository", "IPaletRepository", "IStokHareketiRepository",
    "IKullaniciRepository", "ISistemLogRepository", "IDestekTalebiRepository",
    "ISiparisRepository", "ISevkiyatPlaniRepository", "IIrsaliyeRepository",
    "IRaporSablonuRepository", "IRaporLoguRepository", "IRaporScheduleRepository",
    "IStokSayimRepository",
    "IDashboardRepository",
    "IMalKabulIrsaliyeRepository",
    "IToplamaGoreviRepository",
    "IPaletRezervasyonuRepository",
    "IUretimSeriSayacRepository",
    "IPaletDurumLogRepository",
]
