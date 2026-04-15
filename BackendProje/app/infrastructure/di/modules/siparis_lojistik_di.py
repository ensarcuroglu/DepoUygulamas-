"""DI — Sipariş, İrsaliye, Sevkiyat Planı, Mal Kabul İrsaliyesi, Stok Çıkış Service,
Toplama Görevi, Palet Rezervasyonu."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemySiparisRepository,
    SqlAlchemyIrsaliyeRepository,
    SqlAlchemySevkiyatPlaniRepository,
    SqlAlchemyToplamaGoreviRepository,
    SqlAlchemyPaletRezervasyonuRepository,
)
from app.application.use_cases import (
    SiparisListeleUseCase,
    SiparisGetirUseCase,
    SiparisOlusturUseCase,
    SiparisGuncelleUseCase,
    SiparisSilUseCase,
    IrsaliyeListeleUseCase,
    IrsaliyeGetirUseCase,
    IrsaliyeOlusturUseCase,
    IrsaliyeGuncelleUseCase,
    IrsaliyeYazdirVerisiGetirUseCase,
    SevkiyatPlaniListeleUseCase,
    SevkiyatPlaniGetirUseCase,
    SevkiyatPlaniOlusturUseCase,
    SevkiyatPlaniGuncelleUseCase,
    SevkiyatPlaniSilUseCase,
    YuklemeOnaylaUseCase,
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeSilUseCase,
    IrsaliyeOnaylaVeGorevOlusturUseCase,
    MalKabulKalemiIstisnaBildirUseCase,
    InboundDashboardUseCase,
    InboundKpiUseCase,
)
from app.application.use_cases.palet_rezervasyonu_use_cases import (
    PaletRezervasyonuListeleUseCase,
    SiparisRezervasyonlariGetirUseCase,
    RezervasyonBaslatUseCase,
    RezervasyonIptalUseCase,
    RezervasyonKesinlestirUseCase,
    RezervasyonDegistirUseCase,
    StokDetayUseCase,
)
from app.application.use_cases.toplama_gorevi_use_cases import (
    ToplamaGoreviListeleUseCase,
    ToplamaGoreviGetirUseCase,
    PickTaskUretUseCase,
    SiradanGorevAlUseCase,
    GorevBaslatUseCase,
    GorevTamamlaUseCase,
    GorevIptalUseCase,
    FefoOverrideUseCase,
)
from app.core.services.stok_cikis_domain_service import StokCikisDomainService
from app.core.services.siparis_durum_orchestrator import SiparisDurumOrchestrator
from app.core.services.fefo_secim_servisi import FEFOSecimServisi

from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo
from app.infrastructure.di.modules.katalog_di import get_tedarikci_repo
from app.infrastructure.di.modules.depo_envanter_di import (
    get_depo_repo,
    get_raf_repo,
    get_lot_repo,
    get_palet_repo,
    get_hareket_repo,
    get_mal_kabul_irsaliye_repo,
    get_yerlestirme_gorevi_repo,
    get_yerlestirme_algoritmasi,
)


# ── Repository factory'leri ──

def get_siparis_repo(db: Session = Depends(get_db)):
    return SqlAlchemySiparisRepository(db)


def get_irsaliye_repo(db: Session = Depends(get_db)):
    return SqlAlchemyIrsaliyeRepository(db)


def get_sevkiyat_repo(db: Session = Depends(get_db)):
    return SqlAlchemySevkiyatPlaniRepository(db)


def get_toplama_gorevi_repo(db: Session = Depends(get_db)):
    return SqlAlchemyToplamaGoreviRepository(db)


def get_rezervasyon_repo(db: Session = Depends(get_db)):
    return SqlAlchemyPaletRezervasyonuRepository(db)


# ── Stok Çıkış Domain Service factory ──

def get_stok_cikis_service(
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return StokCikisDomainService(palet_repo, hareket_repo, log_repo)


# ── Palet Rezervasyonu use case factory'leri ──

def get_fefo_servisi():
    return FEFOSecimServisi()


def get_rezervasyon_baslat_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    palet_repo=Depends(get_palet_repo),
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
    fefo=Depends(get_fefo_servisi),
):
    return RezervasyonBaslatUseCase(rezervasyon_repo, palet_repo, siparis_repo, log_repo, fefo)


def get_rezervasyon_iptal_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    log_repo=Depends(get_log_repo),
):
    return RezervasyonIptalUseCase(rezervasyon_repo, log_repo)


def get_rezervasyon_kesinlestir_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    log_repo=Depends(get_log_repo),
):
    return RezervasyonKesinlestirUseCase(rezervasyon_repo, log_repo)


def get_rezervasyon_degistir_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return RezervasyonDegistirUseCase(rezervasyon_repo, palet_repo, log_repo)


def get_rezervasyon_listele_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
):
    return PaletRezervasyonuListeleUseCase(rezervasyon_repo)


def get_siparis_rezervasyonlari_uc(
    rezervasyon_repo=Depends(get_rezervasyon_repo),
):
    return SiparisRezervasyonlariGetirUseCase(rezervasyon_repo)


def get_stok_detay_uc(
    palet_repo=Depends(get_palet_repo),
    rezervasyon_repo=Depends(get_rezervasyon_repo),
):
    return StokDetayUseCase(palet_repo, rezervasyon_repo)


# ── Toplama Görevi use case factory'leri ──

def get_toplama_gorevi_listele_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
):
    return ToplamaGoreviListeleUseCase(gorev_repo)


def get_toplama_gorevi_getir_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
):
    return ToplamaGoreviGetirUseCase(gorev_repo)


def get_pick_task_uret_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return PickTaskUretUseCase(gorev_repo, rezervasyon_repo, sevkiyat_repo, palet_repo, log_repo)


def get_siradan_gorev_al_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
):
    return SiradanGorevAlUseCase(gorev_repo)


def get_gorev_baslat_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
):
    return GorevBaslatUseCase(gorev_repo)


def get_gorev_tamamla_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return GorevTamamlaUseCase(gorev_repo, palet_repo, rezervasyon_repo, hareket_repo, log_repo)


def get_gorev_iptal_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    log_repo=Depends(get_log_repo),
):
    return GorevIptalUseCase(gorev_repo, rezervasyon_repo, log_repo)


def get_fefo_override_uc(
    gorev_repo=Depends(get_toplama_gorevi_repo),
    rezervasyon_repo=Depends(get_rezervasyon_repo),
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
    fefo=Depends(get_fefo_servisi),
):
    return FefoOverrideUseCase(gorev_repo, rezervasyon_repo, palet_repo, log_repo, fefo)


# ── Sipariş Durum Orchestrator factory ──

def get_siparis_durum_orchestrator(
    siparis_repo=Depends(get_siparis_repo),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    rezervasyon_baslat_uc=Depends(get_rezervasyon_baslat_uc),
    rezervasyon_iptal_uc=Depends(get_rezervasyon_iptal_uc),
):
    return SiparisDurumOrchestrator(
        siparis_repo, sevkiyat_repo, rezervasyon_baslat_uc, rezervasyon_iptal_uc
    )


# ── Sipariş use case factory'leri ──

def get_siparis_listele_uc(
    siparis_repo=Depends(get_siparis_repo),
):
    return SiparisListeleUseCase(siparis_repo)


def get_siparis_getir_uc(
    siparis_repo=Depends(get_siparis_repo),
):
    return SiparisGetirUseCase(siparis_repo)


def get_siparis_olustur_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisOlusturUseCase(siparis_repo, log_repo)


def get_siparis_guncelle_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisGuncelleUseCase(siparis_repo, log_repo)


def get_siparis_sil_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisSilUseCase(siparis_repo, log_repo)


# ── İrsaliye use case factory'leri ──

def get_irsaliye_listele_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
):
    return IrsaliyeListeleUseCase(irsaliye_repo)


def get_irsaliye_getir_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
):
    return IrsaliyeGetirUseCase(irsaliye_repo)


def get_irsaliye_olustur_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
    siparis_repo=Depends(get_siparis_repo),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    log_repo=Depends(get_log_repo),
):
    return IrsaliyeOlusturUseCase(
        irsaliye_repo, siparis_repo, sevkiyat_repo, log_repo,
    )


def get_irsaliye_guncelle_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
    log_repo=Depends(get_log_repo),
    hareket_repo=Depends(get_hareket_repo),
    siparis_repo=Depends(get_siparis_repo),
):
    return IrsaliyeGuncelleUseCase(irsaliye_repo, log_repo, hareket_repo, siparis_repo)


def get_irsaliye_yazdir_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
    siparis_repo=Depends(get_siparis_repo),
):
    return IrsaliyeYazdirVerisiGetirUseCase(irsaliye_repo, siparis_repo)


# ── Sevkiyat Planı use case factory'leri ──

def get_sevkiyat_listele_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
):
    return SevkiyatPlaniListeleUseCase(sevkiyat_repo)


def get_sevkiyat_getir_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
):
    return SevkiyatPlaniGetirUseCase(sevkiyat_repo)


def get_sevkiyat_olustur_uc(
    db: Session = Depends(get_db),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
    orchestrator=Depends(get_siparis_durum_orchestrator),
):
    return SevkiyatPlaniOlusturUseCase(
        sevkiyat_repo,
        siparis_repo,
        log_repo,
        db,
        orchestrator,
    )


def get_sevkiyat_guncelle_uc(
    db: Session = Depends(get_db),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    log_repo=Depends(get_log_repo),
    orchestrator=Depends(get_siparis_durum_orchestrator),
):
    return SevkiyatPlaniGuncelleUseCase(sevkiyat_repo, log_repo, db, orchestrator)


def get_yukleme_onayla_uc(
    db: Session = Depends(get_db),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    siparis_repo=Depends(get_siparis_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
    stok_cikis_service=Depends(get_stok_cikis_service),
    orchestrator=Depends(get_siparis_durum_orchestrator),
):
    return YuklemeOnaylaUseCase(
        sevkiyat_repo,
        siparis_repo,
        hareket_repo,
        log_repo,
        stok_cikis_service,
        db,
        orchestrator,
    )


def get_sevkiyat_sil_uc(
    db: Session = Depends(get_db),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    log_repo=Depends(get_log_repo),
    orchestrator=Depends(get_siparis_durum_orchestrator),
):
    return SevkiyatPlaniSilUseCase(sevkiyat_repo, log_repo, db, orchestrator)


# ── Mal Kabul İrsaliyesi use case factory'leri ──

def get_mal_kabul_irsaliye_listele_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
):
    return MalKabulIrsaliyeListeleUseCase(repo)


def get_mal_kabul_irsaliye_getir_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
):
    return MalKabulIrsaliyeGetirUseCase(repo)


def get_mal_kabul_irsaliye_olustur_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    tedarikci_repo=Depends(get_tedarikci_repo),
    depo_repo=Depends(get_depo_repo),
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeOlusturUseCase(repo, tedarikci_repo, depo_repo, urun_repo, log_repo)


def get_mal_kabul_irsaliye_guncelle_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeGuncelleUseCase(repo, urun_repo, log_repo)


def get_mal_kabul_irsaliye_sil_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeSilUseCase(repo, log_repo)


def get_irsaliye_onayla_ve_gorev_olustur_uc(
    db: Session = Depends(get_db),
    repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    lot_repo=Depends(get_lot_repo),
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    gorev_repo=Depends(get_yerlestirme_gorevi_repo),
    raf_repo=Depends(get_raf_repo),
    algoritma=Depends(get_yerlestirme_algoritmasi),
    log_repo=Depends(get_log_repo),
):
    return IrsaliyeOnaylaVeGorevOlusturUseCase(
        repo, urun_repo, lot_repo, palet_repo, hareket_repo,
        gorev_repo, raf_repo, algoritma, log_repo, db,
    )


def get_mal_kabul_kalemi_istisna_bildir_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulKalemiIstisnaBildirUseCase(repo, log_repo)


def get_inbound_dashboard_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
):
    return InboundDashboardUseCase(repo)


def get_inbound_kpi_uc(
    db: Session = Depends(get_db),
):
    return InboundKpiUseCase(db)
