"""
ORM Model ↔ Domain Entity dönüşüm fonksiyonları — re-export hub.

Tüm importlar `from app.infrastructure.persistence.mappers import <fn>` şeklinde çalışır.
Alt modüller domain grubuna göre ayrılmıştır:
  - katalog_mapper          : Marka, Kategori, Tedarikci
  - depo_envanter_mapper    : Depo, Zon, Raf, Lot, Palet
  - urun_mapper             : Urun, StokHareketi
  - kullanici_destek_mapper : Kullanici, SistemLog, DestekTalebi
  - siparis_lojistik_mapper : Siparis, SiparisKalemi, SevkiyatPlani, Irsaliye
  - rapor_mapper            : RaporSablonu, RaporLogu, RaporSchedule
  - stok_sayim_mal_kabul_mapper : StokSayim, StokSayimKalemi, MalKabulIrsaliye, MalKabulKalemi
"""

from app.infrastructure.persistence.mappers.katalog_mapper import (  # noqa: F401
    marka_to_entity,
    marka_to_orm,
    kategori_to_entity,
    kategori_to_orm,
    tedarikci_to_entity,
    tedarikci_to_orm,
)

from app.infrastructure.persistence.mappers.depo_envanter_mapper import (  # noqa: F401
    depo_to_entity,
    depo_to_orm,
    zon_to_entity,
    zon_to_orm,
    raf_to_entity,
    raf_to_orm,
    lot_to_entity,
    lot_to_orm,
    palet_to_entity,
    palet_to_orm,
)

from app.infrastructure.persistence.mappers.urun_mapper import (  # noqa: F401
    urun_to_entity,
    urun_to_orm,
    stok_hareketi_to_entity,
    stok_hareketi_to_orm,
)

from app.infrastructure.persistence.mappers.kullanici_destek_mapper import (  # noqa: F401
    kullanici_to_entity,
    kullanici_to_orm,
    sistem_log_to_entity,
    sistem_log_to_orm,
    destek_talebi_to_entity,
    destek_talebi_to_orm,
)

from app.infrastructure.persistence.mappers.siparis_lojistik_mapper import (  # noqa: F401
    siparis_kalemi_to_entity,
    siparis_kalemi_to_orm,
    siparis_to_entity,
    siparis_to_orm,
    sevkiyat_plani_to_entity,
    sevkiyat_plani_to_orm,
    sevkiyat_kalemi_to_entity,
    sevkiyat_kalemi_to_orm,
    irsaliye_to_entity,
    irsaliye_to_orm,
)

from app.infrastructure.persistence.mappers.rapor_mapper import (  # noqa: F401
    rapor_sablonu_to_entity,
    rapor_sablonu_to_orm,
    rapor_logu_to_entity,
    rapor_logu_to_orm,
    rapor_schedule_to_entity,
    rapor_schedule_to_orm,
)

from app.infrastructure.persistence.mappers.stok_sayim_mal_kabul_mapper import (  # noqa: F401
    stok_sayim_kalemi_to_entity,
    stok_sayim_kalemi_to_orm,
    stok_sayim_to_entity,
    stok_sayim_to_orm,
    mal_kabul_kalemi_to_entity,
    mal_kabul_kalemi_to_orm,
    mal_kabul_irsaliye_to_entity,
    mal_kabul_irsaliye_to_orm,
)

from app.infrastructure.persistence.mappers.belge_taslagi_mapper import (  # noqa: F401
    belge_taslagi_to_entity,
    belge_taslagi_to_orm,
)

from app.infrastructure.persistence.mappers.yerlestirme_mapper import (  # noqa: F401
    yerlestirme_gorevi_to_entity,
    yerlestirme_gorevi_to_orm,
)
