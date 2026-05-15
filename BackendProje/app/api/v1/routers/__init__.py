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
from .belge_taslaklari import router as belge_taslaklari_router
from .mal_kabul import router as mal_kabul_router
from .stok_islemleri import router as stok_islemleri_router
from .yerlestirme_gorevleri import router as yerlestirme_gorevleri_router
from .mobil_terminal import router as mobil_terminal_router
from .toplama_gorevleri import router as toplama_gorevleri_router
from .palet_rezervasyonlari import router as palet_rezervasyonlari_router
from .uretim_paletleri import router as uretim_paletleri_router
from .etiket_sablonlari import router as etiket_sablonlari_router
from .talep_tahmini import router as talep_tahmini_router
from .ai_proxy import router as ai_proxy_router
from .excel_ai import router as excel_ai_router
from .data_gen import router as data_gen_router
from .operator_performans import router as operator_performans_router
from .agv_callbacks import router as agv_callbacks_router

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
    "belge_taslaklari_router",
    "mal_kabul_router",
    "stok_islemleri_router",
    "yerlestirme_gorevleri_router",
    "mobil_terminal_router",
    "toplama_gorevleri_router",
    "palet_rezervasyonlari_router",
    "uretim_paletleri_router",
    "etiket_sablonlari_router",
    "talep_tahmini_router",
    "ai_proxy_router",
    "excel_ai_router",
    "data_gen_router",
    "operator_performans_router",
    "agv_callbacks_router",
]
