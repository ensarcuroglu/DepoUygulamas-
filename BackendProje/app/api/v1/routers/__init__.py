from .urunler import router as urunler_router
from .stok_hareketleri import router as stok_hareketleri_router
from .siparisler import router as siparisler_router
from .markalar import router as markalar_router
from .kategoriler import router as kategoriler_router
from .tedarikciler import router as tedarikciler_router
from .depolar import router as depolar_router
from .raflar import router as raflar_router

__all__ = [
    "urunler_router",
    "stok_hareketleri_router",
    "siparisler_router",
    "markalar_router",
    "kategoriler_router",
    "tedarikciler_router",
    "depolar_router",
    "raflar_router",
]
