"""
CRUD Paketi — Domain bazinda modullere ayrilmis veri erisim fonksiyonlari.

Geriye donuk uyumluluk icin tum fonksiyonlar bu paketten dogrudan
import edilebilir:
    from crud import get_markalar, create_marka, ...
    veya
    from crud.marka_crud import get_markalar
"""

# Marka
from .marka_crud import (
    get_markalar, get_marka, create_marka, update_marka, delete_marka,
)

# Kategori
from .kategori_crud import (
    get_kategoriler, get_kategori, create_kategori, update_kategori, delete_kategori,
)

# Depo
from .depo_crud import (
    get_depolar, get_depo, create_depo, update_depo, delete_depo,
)

# Raf
from .raf_crud import (
    get_raflar, get_raf, create_raf, update_raf, delete_raf,
)

# Tedarikci
from .tedarikci_crud import (
    get_tedarikciler, get_tedarikci, create_tedarikci, update_tedarikci, delete_tedarikci,
)

# Urun
from .urun_crud import (
    get_urunler, get_urun, get_urun_by_barkod,
    create_urun, update_urun, delete_urun, get_kritik_urunler,
)

# Lot
from .lot_crud import (
    get_lotlar, get_lot, get_lot_by_no,
    create_lot, update_lot, delete_lot, get_skt_yaklasan_lotlar,
)

# Palet
from .palet_crud import (
    get_paletler, get_palet, get_palet_by_no,
    create_palet, update_palet, delete_palet, get_sonraki_palet_no,
)

# Stok Hareketi
from .stok_hareketi_crud import (
    get_stok_hareketleri, create_stok_hareketi,
)

# Dashboard
from .dashboard_crud import get_dashboard_stats

# Destek Masasi
from .destek_crud import (
    get_destek_talepleri, get_destek_talebi,
    create_destek_talebi, update_destek_talebi,
)

# Siparis
from .siparis_crud import (
    generate_siparis_no, get_siparisler, get_siparis,
    create_siparis, update_siparis, delete_siparis,
)

# Sevkiyat
from .sevkiyat_crud import (
    get_sevkiyat_planlari, get_sevkiyat_plani,
    create_sevkiyat_plani, update_sevkiyat_plani, delete_sevkiyat_plani,
)

# Irsaliye
from .irsaliye_crud import (
    generate_irsaliye_no, get_irsaliyeler, get_irsaliye,
    create_irsaliye, update_irsaliye,
)

# Rapor
from .rapor_crud import (
    get_rapor_sablonlari, get_rapor_sablonu,
    create_rapor_sablonu, update_rapor_sablonu, delete_rapor_sablonu,
    get_rapor_loglari, create_rapor_logu,
    get_rapor_schedules, get_rapor_schedule,
    create_rapor_schedule, update_rapor_schedule, delete_rapor_schedule,
    get_stok_raporu_verileri, get_siparis_raporu_verileri,
    get_hareket_raporu_verileri, get_kritik_stok_raporu,
    get_skt_raporu, get_abc_analiz, get_depo_doluluk,
)
