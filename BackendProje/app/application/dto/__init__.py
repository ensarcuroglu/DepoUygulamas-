from .urun_dto import (
    UrunOlusturRequestDTO,
    UrunGuncelleRequestDTO,
    UrunResponseDTO,
    UrunListResponseDTO,
)
from .stok_hareketi_dto import (
    StokHareketiOlusturRequestDTO,
    StokHareketiResponseDTO,
)
from .siparis_dto import (
    SiparisKalemiOlusturRequestDTO,
    SiparisKalemiResponseDTO,
    SiparisOlusturRequestDTO,
    SiparisGuncelleRequestDTO,
    SiparisResponseDTO,
    SiparisDetayResponseDTO,
)
from .marka_dto import (
    MarkaOlusturRequestDTO,
    MarkaGuncelleRequestDTO,
    MarkaResponseDTO,
)
from .kategori_dto import (
    KategoriOlusturRequestDTO,
    KategoriGuncelleRequestDTO,
    KategoriResponseDTO,
)
from .tedarikci_dto import (
    TedarikciOlusturRequestDTO,
    TedarikciGuncelleRequestDTO,
    TedarikciResponseDTO,
)
from .depo_dto import (
    DepoOlusturRequestDTO,
    DepoGuncelleRequestDTO,
    DepoResponseDTO,
)
from .zon_dto import (
    ZonOlusturRequestDTO,
    ZonGuncelleRequestDTO,
    ZonResponseDTO,
)
from .raf_dto import (
    RafOlusturRequestDTO,
    RafGuncelleRequestDTO,
    RafResponseDTO,
)
from .lot_dto import (
    LotOlusturRequestDTO,
    LotGuncelleRequestDTO,
    LotResponseDTO,
)
from .palet_dto import (
    PaletOlusturRequestDTO,
    PaletGuncelleRequestDTO,
    PaletResponseDTO,
)
from .kullanici_dto import (
    KullaniciGuncelleRequestDTO,
    KullaniciResponseDTO,
)
from .destek_talebi_dto import (
    DestekTalebiOlusturRequestDTO,
    DestekTalebiGuncelleRequestDTO,
    DestekTalebiResponseDTO,
)
from .sistem_log_dto import (
    SistemLogOlusturRequestDTO,
    SistemLogResponseDTO,
)
from .irsaliye_dto import (
    IrsaliyeOlusturRequestDTO,
    IrsaliyeGuncelleRequestDTO,
    IrsaliyeResponseDTO,
    IrsaliyeYazdirResponseDTO,
    IrsaliyeYazdirIrsaliyeDTO,
    IrsaliyeYazdirSiparisDTO,
    IrsaliyeYazdirKalemDTO,
)
from .sevkiyat_plani_dto import (
    SevkiyatPlaniOlusturRequestDTO,
    SevkiyatPlaniGuncelleRequestDTO,
    SevkiyatPlaniResponseDTO,
    SevkiyatKalemiResponseDTO,
)
from .stok_sayim_dto import (
    StokSayimOlusturRequestDTO,
    StokSayimKalemiKaydetRequestDTO,
    StokSayimResponseDTO,
    StokSayimKalemiResponseDTO,
    VaryansResponseDTO,
    VaryansKalemDTO,
)

from .mal_kabul_irsaliye_dto import (
    MalKabulKalemiOlusturDTO,
    MalKabulKalemiResponseDTO,
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeResponseDTO,
    MalKabulKalemiIstisnaRequestDTO,
    InboundDashboardResponseDTO,
    InboundIrsaliyeOzetDTO,
    InboundKpiResponseDTO,
    OperatorVerimDTO,
)
from .talep_tahmini_dto import (
    BacktestOzetDTO,
    GunlukTahminDTO,
    GunlukTalepDTO,
    RiskliUrunDTO,
    TalepTahminResponseDTO,
    TalepTahminUrunOzetDTO,
    TalepTrendDTO,
)

__all__ = [
    # Ürün
    "UrunOlusturRequestDTO", "UrunGuncelleRequestDTO",
    "UrunResponseDTO", "UrunListResponseDTO",
    # Stok Hareketi
    "StokHareketiOlusturRequestDTO", "StokHareketiResponseDTO",
    # Sipariş
    "SiparisKalemiOlusturRequestDTO", "SiparisKalemiResponseDTO",
    "SiparisOlusturRequestDTO", "SiparisGuncelleRequestDTO",
    "SiparisResponseDTO", "SiparisDetayResponseDTO",
    # Marka
    "MarkaOlusturRequestDTO", "MarkaGuncelleRequestDTO", "MarkaResponseDTO",
    # Kategori
    "KategoriOlusturRequestDTO", "KategoriGuncelleRequestDTO", "KategoriResponseDTO",
    # Tedarikçi
    "TedarikciOlusturRequestDTO", "TedarikciGuncelleRequestDTO", "TedarikciResponseDTO",
    # Depo
    "DepoOlusturRequestDTO", "DepoGuncelleRequestDTO", "DepoResponseDTO",
    # Zon
    "ZonOlusturRequestDTO", "ZonGuncelleRequestDTO", "ZonResponseDTO",
    # Raf
    "RafOlusturRequestDTO", "RafGuncelleRequestDTO", "RafResponseDTO",
    # Lot
    "LotOlusturRequestDTO", "LotGuncelleRequestDTO", "LotResponseDTO",
    # Palet
    "PaletOlusturRequestDTO", "PaletGuncelleRequestDTO", "PaletResponseDTO",
    # Kullanıcı
    "KullaniciGuncelleRequestDTO", "KullaniciResponseDTO",
    # Destek Talebi
    "DestekTalebiOlusturRequestDTO", "DestekTalebiGuncelleRequestDTO", "DestekTalebiResponseDTO",
    # Sistem Log
    "SistemLogOlusturRequestDTO", "SistemLogResponseDTO",
    # İrsaliye
    "IrsaliyeOlusturRequestDTO", "IrsaliyeGuncelleRequestDTO",
    "IrsaliyeResponseDTO", "IrsaliyeYazdirResponseDTO",
    "IrsaliyeYazdirIrsaliyeDTO", "IrsaliyeYazdirSiparisDTO", "IrsaliyeYazdirKalemDTO",
    # Sevkiyat Planı
    "SevkiyatPlaniOlusturRequestDTO", "SevkiyatPlaniGuncelleRequestDTO",
    "SevkiyatPlaniResponseDTO", "SevkiyatKalemiResponseDTO",
    # Stok Sayım
    "StokSayimOlusturRequestDTO", "StokSayimKalemiKaydetRequestDTO",
    "StokSayimResponseDTO", "StokSayimKalemiResponseDTO",
    "VaryansResponseDTO", "VaryansKalemDTO",
    # Mal Kabul İrsaliyesi
    "MalKabulKalemiOlusturDTO", "MalKabulKalemiResponseDTO",
    "MalKabulIrsaliyeOlusturRequestDTO", "MalKabulIrsaliyeGuncelleRequestDTO",
    "MalKabulIrsaliyeResponseDTO", "MalKabulKalemiIstisnaRequestDTO",
    "InboundDashboardResponseDTO", "InboundIrsaliyeOzetDTO",
    "InboundKpiResponseDTO", "OperatorVerimDTO",
    # Talep Tahmini
    "GunlukTahminDTO", "GunlukTalepDTO", "TalepTahminResponseDTO",
    "TalepTahminUrunOzetDTO", "TalepTrendDTO",
    "RiskliUrunDTO", "BacktestOzetDTO",
]
