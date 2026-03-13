from .urunler import router as urunler_router
from .stok_hareketleri import router as stok_hareketleri_router
from .siparisler import router as siparisler_router

__all__ = [
    "urunler_router",
    "stok_hareketleri_router",
    "siparisler_router",
]
