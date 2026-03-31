"""DI — Depo, Raf, Lot, Palet, Palet Bazlı Stok İşlemleri."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemyDepoRepository,
    SqlAlchemyRafRepository,
    SqlAlchemyLotRepository,
    SqlAlchemyPaletRepository,
    SqlAlchemyStokHareketiRepository,
    SqlAlchemyMalKabulIrsaliyeRepository,
)
from app.application.use_cases import (
    DepoListeleUseCase,
    DepoGetirUseCase,
    DepoOlusturUseCase,
    DepoGuncelleUseCase,
    DepoSilUseCase,
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
from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.infrastructure.services.irsaliye_palet_veri_kaynagi_service import IrsaliyePaletVeriKaynagiService
from app.infrastructure.services.palet_sorgulama_service import PaletSorgulamaService
from app.infrastructure.config.erp_config import ErpConfig, PaletVeriKaynagi

from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo

_erp_config = ErpConfig.from_env()
_mock_erp_adapter = None


# ── Repository factory'leri ──

def get_depo_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDepoRepository(db)


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


# ── Depo use case factory'leri ──

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


# ── Raf use case factory'leri ──

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
):
    return RafOlusturUseCase(raf_repo, depo_repo, log_repo)


def get_raf_guncelle_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return RafGuncelleUseCase(raf_repo, log_repo)


def get_raf_sil_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return RafSilUseCase(raf_repo, log_repo)


# ── Lot use case factory'leri ──

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


# ── Palet use case factory'leri ──

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


# ── Palet Veri Kaynağı Adapter + Domain Service factory'leri ──

def get_palet_veri_kaynagi(
    mal_kabul_repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    depo_repo=Depends(get_depo_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
):
    """PALET_VERI_KAYNAGI env değişkenine göre adapter döner.

    LOCAL → IrsaliyePaletVeriKaynagiService (varsayılan)
    MOCK  → MockErpPaletVeriKaynagiService (demo/dev)
    ERP   → ErpPaletVeriKaynagiService (gerçek ERP)
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

    # LOCAL (varsayılan)
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
