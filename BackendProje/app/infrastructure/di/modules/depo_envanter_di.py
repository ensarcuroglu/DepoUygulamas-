"""DI - Depo, Raf, Lot, Palet, Palet Bazli Stok Islemleri, Yerlestirme Gorevi."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemyDepoRepository,
    SqlAlchemyZonRepository,
    SqlAlchemyRafRepository,
    SqlAlchemyLotRepository,
    SqlAlchemyPaletRepository,
    SqlAlchemyStokHareketiRepository,
    SqlAlchemyMalKabulIrsaliyeRepository,
    SqlAlchemyYerlestirmeGoreviRepository,
)
from app.application.use_cases import (
    DepoListeleUseCase,
    DepoGetirUseCase,
    DepoOlusturUseCase,
    DepoGuncelleUseCase,
    DepoSilUseCase,
    ZonListeleUseCase,
    ZonGetirUseCase,
    ZonOlusturUseCase,
    ZonGuncelleUseCase,
    ZonSilUseCase,
    RafListeleUseCase,
    RafGetirUseCase,
    RafOlusturUseCase,
    RafGuncelleUseCase,
    RafSilUseCase,
    LotListeleUseCase,
    LotGetirUseCase,
    LotSktYaklasanUseCase,
    LotOlusturUseCase,
    LotGuncelleUseCase,
    LotSilUseCase,
    PaletListeleUseCase,
    PaletGetirUseCase,
    PaletBarkodIleGetirUseCase,
    PaletSonrakiNumaraUseCase,
    PaletOlusturUseCase,
    PaletGuncelleUseCase,
    PaletSilUseCase,
)
from app.application.use_cases.yerlestirme_gorevi_use_cases import (
    YerlestirmeGoreviListeleUseCase,
    YerlestirmeGoreviGetirUseCase,
    YerlestirmeGoreviOlusturUseCase,
    SonrakiGorevisiniAlUseCase,
    YerlestirmeGoreviBaslatUseCase,
    YerlestirmeGoreviTamamlaUseCase,
    YerlestirmeGoreviOverrideUseCase,
    YerlestirmeGoreviIptalUseCase,
    YerlestirmeGoreviBirakUseCase,
    YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase,
    YerlestirmeOnaylaUseCase,
    BilinmeyenKonumGorevleriOlusturUseCase,
    KarantinadanCikarUseCase,
    KarantinayaAlUseCase,
    ZamanAsimiBirakUseCase,
)
from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi
from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi
from app.core.services.yerlestirme_algoritmasi import YerlestirmeAlgoritmasi
from app.infrastructure.services.irsaliye_palet_veri_kaynagi_service import IrsaliyePaletVeriKaynagiService
from app.infrastructure.services.palet_sorgulama_service import PaletSorgulamaService
from app.infrastructure.config.erp_config import ErpConfig, PaletVeriKaynagi

from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo

_erp_config = ErpConfig.from_env()
_mock_erp_adapter = None


# â”€â”€ Repository factory'leri â”€â”€

def get_depo_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDepoRepository(db)


def get_zon_repo(db: Session = Depends(get_db)):
    return SqlAlchemyZonRepository(db)


def get_raf_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRafRepository(db)


def get_lot_repo(db: Session = Depends(get_db)):
    return SqlAlchemyLotRepository(db)


def get_palet_repo(db: Session = Depends(get_db)):
    return SqlAlchemyPaletRepository(db)


def get_hareket_repo(db: Session = Depends(get_db)):
    return SqlAlchemyStokHareketiRepository(db)


def get_mal_kabul_irsaliye_repo(db: Session = Depends(get_db)):
    return SqlAlchemyMalKabulIrsaliyeRepository(db)


# â”€â”€ Depo use case factory'leri â”€â”€

def get_depo_listele_uc(
    depo_repo=Depends(get_depo_repo),
):
    return DepoListeleUseCase(depo_repo)


def get_depo_getir_uc(
    depo_repo=Depends(get_depo_repo),
):
    return DepoGetirUseCase(depo_repo)


def get_depo_olustur_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoOlusturUseCase(depo_repo, log_repo)


def get_depo_guncelle_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoGuncelleUseCase(depo_repo, log_repo)


def get_depo_sil_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoSilUseCase(depo_repo, log_repo)

def get_zon_listele_uc(
    zon_repo=Depends(get_zon_repo),
):
    return ZonListeleUseCase(zon_repo)


def get_zon_getir_uc(
    zon_repo=Depends(get_zon_repo),
):
    return ZonGetirUseCase(zon_repo)


def get_zon_olustur_uc(
    zon_repo=Depends(get_zon_repo),
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return ZonOlusturUseCase(zon_repo, depo_repo, log_repo)


def get_zon_guncelle_uc(
    zon_repo=Depends(get_zon_repo),
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return ZonGuncelleUseCase(zon_repo, depo_repo, log_repo)


def get_zon_sil_uc(
    zon_repo=Depends(get_zon_repo),
    log_repo=Depends(get_log_repo),
):
    return ZonSilUseCase(zon_repo, log_repo)


# â”€â”€ Raf use case factory'leri â”€â”€

def get_raf_listele_uc(
    raf_repo=Depends(get_raf_repo),
):
    return RafListeleUseCase(raf_repo)


def get_raf_getir_uc(
    raf_repo=Depends(get_raf_repo),
):
    return RafGetirUseCase(raf_repo)


def get_raf_olustur_uc(
    raf_repo=Depends(get_raf_repo),
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
    zon_repo=Depends(get_zon_repo),
):
    return RafOlusturUseCase(raf_repo, depo_repo, log_repo, zon_repo)


def get_raf_guncelle_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
    zon_repo=Depends(get_zon_repo),
):
    return RafGuncelleUseCase(raf_repo, log_repo, zon_repo)


def get_raf_sil_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return RafSilUseCase(raf_repo, log_repo)


# â”€â”€ Lot use case factory'leri â”€â”€

def get_lot_listele_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotListeleUseCase(lot_repo)


def get_lot_getir_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotGetirUseCase(lot_repo)


def get_lot_skt_yaklasan_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotSktYaklasanUseCase(lot_repo)


def get_lot_olustur_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotOlusturUseCase(lot_repo, log_repo)


def get_lot_guncelle_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotGuncelleUseCase(lot_repo, log_repo)


def get_lot_sil_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotSilUseCase(lot_repo, log_repo)


# â”€â”€ Palet use case factory'leri â”€â”€

def get_palet_listele_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletListeleUseCase(palet_repo)


def get_palet_getir_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletGetirUseCase(palet_repo)


def get_palet_barkod_ile_getir_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletBarkodIleGetirUseCase(palet_repo)


def get_palet_sonraki_numara_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletSonrakiNumaraUseCase(palet_repo)


def get_palet_olustur_uc(
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletOlusturUseCase(palet_repo, lot_repo, raf_repo, log_repo)


def get_palet_guncelle_uc(
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletGuncelleUseCase(palet_repo, log_repo)


def get_palet_sil_uc(
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletSilUseCase(palet_repo, log_repo)


# â”€â”€ Palet Veri KaynaÄŸÄ± Adapter + Domain Service factory'leri â”€â”€

def get_palet_veri_kaynagi(
    mal_kabul_repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    depo_repo=Depends(get_depo_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
):
    """PALET_VERI_KAYNAGI env deÄŸiÅŸkenine gÃ¶re adapter dÃ¶ner.

    LOCAL â†’ IrsaliyePaletVeriKaynagiService (varsayÄ±lan)
    MOCK  â†’ MockErpPaletVeriKaynagiService (demo/dev)
    ERP   â†’ ErpPaletVeriKaynagiService (gerÃ§ek ERP)
    """
    global _mock_erp_adapter

    if _erp_config.palet_veri_kaynagi == PaletVeriKaynagi.MOCK:
        if _mock_erp_adapter is None:
            from app.infrastructure.services.mock_erp_palet_veri_kaynagi_service import (
                MockErpPaletVeriKaynagiService,
            )
            _mock_erp_adapter = MockErpPaletVeriKaynagiService()
        return _mock_erp_adapter

    if _erp_config.palet_veri_kaynagi == PaletVeriKaynagi.ERP:
        from app.infrastructure.services.erp_palet_veri_kaynagi_service import (
            ErpPaletVeriKaynagiService,
        )
        return ErpPaletVeriKaynagiService(_erp_config)

    # LOCAL (varsayÄ±lan)
    return IrsaliyePaletVeriKaynagiService(
        mal_kabul_repo, urun_repo, depo_repo, raf_repo, lot_repo,
    )


def get_palet_bazli_stok_service(
    veri_kaynagi=Depends(get_palet_veri_kaynagi),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    raf_repo=Depends(get_raf_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletBazliStokDomainService(
        veri_kaynagi, palet_repo, lot_repo, raf_repo, hareket_repo, log_repo,
    )


def get_palet_sorgulama_service(
    veri_kaynagi=Depends(get_palet_veri_kaynagi),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    depo_repo=Depends(get_depo_repo),
    raf_repo=Depends(get_raf_repo),
):
    return PaletSorgulamaService(
        veri_kaynagi, palet_repo, lot_repo, urun_repo, depo_repo, raf_repo,
    )


# ── Yerleştirme Görevi repository + use case factory'leri ──

def get_yerlestirme_gorevi_repo(db: Session = Depends(get_db)):
    return SqlAlchemyYerlestirmeGoreviRepository(db)


def get_yerlestirme_gorevi_listele_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return YerlestirmeGoreviListeleUseCase(repo)


def get_yerlestirme_gorevi_getir_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return YerlestirmeGoreviGetirUseCase(repo)


def get_yerlestirme_gorevi_olustur_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return YerlestirmeGoreviOlusturUseCase(repo, palet_repo, raf_repo, log_repo)


def get_sonraki_gorevini_al_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return SonrakiGorevisiniAlUseCase(repo)


def get_yerlestirme_gorevi_baslat_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return YerlestirmeGoreviBaslatUseCase(repo)


def get_yerlestirme_gorevi_tamamla_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return YerlestirmeGoreviTamamlaUseCase(repo, palet_repo, raf_repo, log_repo)


def get_yerlestirme_gorevi_override_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return YerlestirmeGoreviOverrideUseCase(repo, palet_repo, raf_repo, log_repo)


def get_yerlestirme_gorevi_iptal_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    log_repo=Depends(get_log_repo),
):
    return YerlestirmeGoreviIptalUseCase(repo, log_repo)


def get_yerlestirme_gorevi_birak_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return YerlestirmeGoreviBirakUseCase(repo)


def get_yerlestirme_gorevi_bekleyen_ozet_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    return YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase(repo)


def get_zaman_asimi_birak_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
):
    import os
    timeout_dk = int(os.getenv("PUTAWAY_TIMEOUT", "60"))
    return ZamanAsimiBirakUseCase(repo, timeout_dk=timeout_dk)


# ── Faz 1 — Domain Servis factory'leri ──

def get_zon_uyumluluk_servisi(
    zon_repo=Depends(get_zon_repo),
):
    return ZonUyumlulukServisi(zon_repo)


def get_kapasite_dogrulama_servisi(
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
):
    return KapasiteDogrulamaServisi(palet_repo, raf_repo)


def get_yerlestirme_algoritmasi(
    raf_repo=Depends(get_raf_repo),
    zon_repo=Depends(get_zon_repo),
    palet_repo=Depends(get_palet_repo),
    zon_uyumluluk=Depends(get_zon_uyumluluk_servisi),
    kapasite=Depends(get_kapasite_dogrulama_servisi),
):
    return YerlestirmeAlgoritmasi(raf_repo, zon_repo, palet_repo, zon_uyumluluk, kapasite)


# ── Faz 2 — İş Akışı Entegrasyonu factory'leri ──

def get_yerlestirme_onayla_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    zon_repo=Depends(get_zon_repo),
    zon_uyumluluk=Depends(get_zon_uyumluluk_servisi),
    kapasite=Depends(get_kapasite_dogrulama_servisi),
    log_repo=Depends(get_log_repo),
):
    return YerlestirmeOnaylaUseCase(
        repo, palet_repo, raf_repo, lot_repo, urun_repo,
        zon_repo, zon_uyumluluk, kapasite, log_repo,
    )


def get_bilinmeyen_konum_gorevleri_olustur_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    algoritma=Depends(get_yerlestirme_algoritmasi),
    log_repo=Depends(get_log_repo),
):
    return BilinmeyenKonumGorevleriOlusturUseCase(
        repo, palet_repo, raf_repo, lot_repo, urun_repo, algoritma, log_repo,
    )


def get_karantinadan_cikar_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    zon_repo=Depends(get_zon_repo),
    algoritma=Depends(get_yerlestirme_algoritmasi),
    log_repo=Depends(get_log_repo),
):
    return KarantinadanCikarUseCase(
        repo, palet_repo, raf_repo, lot_repo, urun_repo, zon_repo, algoritma, log_repo,
    )


def get_karantinaya_al_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    zon_repo=Depends(get_zon_repo),
    kapasite=Depends(get_kapasite_dogrulama_servisi),
    log_repo=Depends(get_log_repo),
):
    return KarantinayaAlUseCase(
        repo, palet_repo, raf_repo, zon_repo, kapasite, log_repo,
    )
