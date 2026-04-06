from .urunler import router as urunler_router
from .stok_hareketleri import router as stok_hareketleri_router
from .siparisler import router as siparisler_router
from .markalar import router as markalar_router
from .kategoriler import router as kategoriler_router
from .tedarikciler import router as tedarikciler_router
from .depolar import router as depolar_router
from .zonlar import router as zonlar_router
from .raflar import router as raflar_router
from .lotlar import router as lotlar_router
from .paletler import router as paletler_router
from .kullanicilar import router as kullanicilar_router
from .destek import router as destek_router
from .sistem_loglari import router as sistem_loglari_router
from .irsaliyeler import router as irsaliyeler_router
from .sevkiyat_planlama import router as sevkiyat_planlama_router
from .stok_sayim import router as stok_sayim_router
from .raporlar import router as raporlar_router
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .mal_kabul_irsaliyeleri import router as mal_kabul_irsaliyeleri_router
from .stok_islemleri import router as stok_islemleri_router

__all__ = [
    "urunler_router",
    "stok_hareketleri_router",
    "siparisler_router",
    "markalar_router",
    "kategoriler_router",
    "tedarikciler_router",
    "depolar_router",
    "zonlar_router",
    "raflar_router",
    "lotlar_router",
    "paletler_router",
    "kullanicilar_router",
    "destek_router",
    "sistem_loglari_router",
    "irsaliyeler_router",
    "sevkiyat_planlama_router",
    "stok_sayim_router",
    "raporlar_router",
    "auth_router",
    "dashboard_router",
    "mal_kabul_irsaliyeleri_router",
    "stok_islemleri_router",
]
