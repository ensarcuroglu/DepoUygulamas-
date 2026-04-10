"""
Mobil Terminal API Router — Saha operatörü için scan-to-verify iş akışı.

Tüm endpoint'ler depocu rolü gerektirir.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.auth import require_role
from app.core.entities.sistem_log import SistemLog, OlayTipi
from app.core.exceptions import GecersizIslemError, KayitBulunamadiError
from app.infrastructure.di.container import (
    get_log_repo,
    get_kapasite_dogrulama_servisi,
    get_lot_repo,
    get_palet_barkod_ile_getir_uc,
    get_palet_repo,
    get_raf_repo,
    get_urun_repo,
    get_yerlestirme_gorevi_listele_uc,
    get_yerlestirme_gorevi_repo,
    get_yerlestirme_onayla_uc,
    get_zon_repo,
)
from app.application.dto.yerlestirme_gorevi_dto import (
    AlternatifRafDTO,
    YerlestirmeGoreviResponseDTO,
    YerlestirmeOnaylaRequestDTO,
    YerlestirmeOnaylaSonucDTO,
)
from app.application.use_cases.yerlestirme_gorevi_use_cases import (
    YerlestirmeGoreviListeleUseCase,
    YerlestirmeOnaylaUseCase,
)
from app.application.use_cases.palet_use_cases import PaletBarkodIleGetirUseCase
from limiter import limiter
from models import Kullanici

router = APIRouter(prefix="/api/terminal", tags=["Mobil Terminal"])
AKTIF_GOREV_DURUMLARI = ("Atandi", "DevamEdiyor")


def _terminal_depo_id(
    current_user: Kullanici,
    requested_depo_id: Optional[int] = None,
) -> int:
    if current_user.rol == "depocu":
        if getattr(current_user, "depo_erisimi_yok", False):
            raise GecersizIslemError(
                "Bu kullanıcının hiçbir depoda yetkisi yok. Lütfen yöneticiniz ile iletişime geçin."
            )
        if current_user.depo_id is None:
            raise GecersizIslemError(
                "Depocu kullanıcısına depo atanmamış. Lütfen yöneticiniz ile iletişime geçin."
            )
        return current_user.depo_id

    if requested_depo_id is not None:
        return requested_depo_id

    if current_user.depo_id is not None:
        return current_user.depo_id

    raise GecersizIslemError("Bu işlem için depo bağlamı çözümlenemedi.")


def _aktif_gorevleri_getir(
    uc: YerlestirmeGoreviListeleUseCase,
    kullanici_id: int,
    depo_id: Optional[int] = None,
    limit: int = 10000,
) -> List[YerlestirmeGoreviResponseDTO]:
    gorevler: List[YerlestirmeGoreviResponseDTO] = []
    eklenen_idler = set()
    for durum in AKTIF_GOREV_DURUMLARI:
        durum_gorevleri = uc.execute(
            durum=durum,
            atanan_kullanici_id=kullanici_id,
            depo_id=depo_id,
            limit=limit,
        )
        for gorev in durum_gorevleri:
            if gorev.id not in eklenen_idler:
                gorevler.append(gorev)
                eklenen_idler.add(gorev.id)
    return gorevler


# ─────────────────────────────────────────
# İSTEK / YANIT ŞEMALARI
# ─────────────────────────────────────────

class PaletScanRequestDTO(BaseModel):
    palet_barkod: str = Field(..., min_length=1, max_length=100)
    depo_id: Optional[int] = Field(None, gt=0)


class RafScanRequestDTO(BaseModel):
    raf_barkod: str = Field(..., min_length=1, max_length=100)
    depo_id: Optional[int] = Field(None, gt=0)


class YerlestirRequestDTO(BaseModel):
    gorev_id: int = Field(..., gt=0)
    palet_barkod: str = Field(..., min_length=1, max_length=100)
    raf_barkod: str = Field(..., min_length=1, max_length=100)
    depo_id: Optional[int] = Field(None, gt=0)


class AlternatifRafRequestDTO(BaseModel):
    zon_id: int = Field(..., gt=0)
    palet_kg: float = Field(default=0.0, ge=0)
    limit: int = Field(default=5, ge=1, le=20)


class PaletBilgiResponseDTO(BaseModel):
    palet_id: int
    palet_no: str
    lot_no: Optional[str]
    urun_adi: Optional[str]
    koli_adedi: Optional[int]
    palet_kg: Optional[float]
    raf_id: Optional[int]
    raf_kod: Optional[str]
    aktif: bool


class RafBilgiResponseDTO(BaseModel):
    raf_id: int
    raf_kod: str
    zon_id: Optional[int]
    zon_adi: Optional[str]
    zon_tip: Optional[str]
    kapasite: Optional[int]
    mevcut_palet_sayisi: int
    bos_slot: Optional[int]
    max_agirlik_kg: Optional[float]
    mevcut_agirlik_kg: float


class TerminalOzetResponseDTO(BaseModel):
    tarih: str
    kullanici_id: int
    bekleyen_gorev: int
    benim_atanan_gorev: int
    bugun_tamamlanan: int


# ─────────────────────────────────────────
# ENDPOINT'LER
# ─────────────────────────────────────────

@router.post("/scan/palet", response_model=PaletBilgiResponseDTO)
@limiter.limit("120/minute")
def palet_barkod_scan(
    request: Request,
    dto: PaletScanRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: PaletBarkodIleGetirUseCase = Depends(get_palet_barkod_ile_getir_uc),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    raf_repo=Depends(get_raf_repo),
):
    """Palet barkodu okutulduğunda palet + lot + ürün bilgisini döner."""
    palet = uc.execute(dto.palet_barkod)

    lot_no = None
    urun_adi = None
    if palet.lot_id:
        lot = lot_repo.getir_id_ile(palet.lot_id)
        if lot:
            lot_no = lot.lot_no
            urun = urun_repo.getir_id_ile(lot.urun_id) if lot.urun_id else None
            urun_adi = urun.ad if urun else None

    raf_kod = None
    if palet.raf_id:
        raf = raf_repo.getir_id_ile(palet.raf_id)
        raf_kod = raf.kod if raf else None

    return PaletBilgiResponseDTO(
        palet_id=palet.id,
        palet_no=palet.palet_no,
        lot_no=lot_no,
        urun_adi=urun_adi,
        koli_adedi=palet.koli_adedi,
        palet_kg=palet.palet_kg,
        raf_id=palet.raf_id,
        raf_kod=raf_kod,
        aktif=palet.aktif,
    )


@router.post("/scan/raf", response_model=RafBilgiResponseDTO)
@limiter.limit("120/minute")
def raf_barkod_scan(
    request: Request,
    dto: RafScanRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    raf_repo=Depends(get_raf_repo),
    zon_repo=Depends(get_zon_repo),
    palet_repo=Depends(get_palet_repo),
):
    """Raf barkodu okutulduğunda raf bilgisi + kapasite durumu döner."""
    depo_id = _terminal_depo_id(current_user, dto.depo_id)
    raf = raf_repo.getir_kod_ile(dto.raf_barkod, depo_id)
    if not raf:
        raise KayitBulunamadiError("Raf", dto.raf_barkod)

    zon_adi = None
    zon_tip = None
    if raf.zon_id:
        zon = zon_repo.getir_id_ile(raf.zon_id)
        if zon:
            zon_adi = zon.isim
            zon_tip = zon.tip

    mevcut_paletler = palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True, limit=500)
    mevcut_palet_sayisi = len(mevcut_paletler)
    mevcut_agirlik_kg = sum(p.palet_kg or 0.0 for p in mevcut_paletler)
    bos_slot = (raf.kapasite - mevcut_palet_sayisi) if raf.kapasite else None

    return RafBilgiResponseDTO(
        raf_id=raf.id,
        raf_kod=raf.kod,
        zon_id=raf.zon_id,
        zon_adi=zon_adi,
        zon_tip=zon_tip,
        kapasite=raf.kapasite,
        mevcut_palet_sayisi=mevcut_palet_sayisi,
        bos_slot=bos_slot,
        max_agirlik_kg=raf.max_agirlik_kg,
        mevcut_agirlik_kg=mevcut_agirlik_kg,
    )


@router.post("/yerlestir", response_model=YerlestirmeOnaylaSonucDTO)
@limiter.limit("60/minute")
def yerlestir(
    request: Request,
    dto: YerlestirRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeOnaylaUseCase = Depends(get_yerlestirme_onayla_uc),
    gorev_repo=Depends(get_yerlestirme_gorevi_repo),
    palet_repo=Depends(get_palet_repo),
):
    """
    Ana scan-to-verify yerleştirme akışı.

    Palet barkodu + raf barkodu okutulur. Sistem:
    1. Zon uyumluluk + kapasite doğrular.
    2. Başarılı ise → palet rafına atanır, görev TAMAMLANDI'ya geçer.
    3. Başarısız ise → hata tipi + alternatif raflar döner.
    """
    # Palet barkodunu gorev_id ile çapraz doğrula
    gorev = gorev_repo.getir_id_ile(dto.gorev_id)
    if not gorev:
        raise KayitBulunamadiError("YerlestirmeGorevi", dto.gorev_id)
    if current_user.rol == "depocu":
        depo_id = _terminal_depo_id(current_user, dto.depo_id)
        if gorev.depo_id is not None and gorev.depo_id != depo_id:
            raise GecersizIslemError("Bu görev farklı bir depoya ait.")
    palet = palet_repo.getir_id_ile(gorev.palet_id)
    if not palet or palet.palet_no != dto.palet_barkod:
        raise GecersizIslemError(
            f"Görev {dto.gorev_id} beklenen paleti ({palet.palet_no if palet else '?'}) "
            f"ile okutulan barkod ({dto.palet_barkod}) eşleşmiyor."
        )

    onayla_dto = YerlestirmeOnaylaRequestDTO(
        okutulan_raf_kodu=dto.raf_barkod,
    )
    return uc.execute(dto.gorev_id, onayla_dto, kullanici_id=current_user.id)


@router.get("/gorevlerim", response_model=List[YerlestirmeGoreviResponseDTO])
@limiter.limit("100/minute")
def gorevlerim(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviListeleUseCase = Depends(get_yerlestirme_gorevi_listele_uc),
):
    """Oturum açmış operatöre atanmış aktif görevler."""
    return _aktif_gorevleri_getir(
        uc=uc,
        kullanici_id=current_user.id,
        depo_id=_terminal_depo_id(current_user) if current_user.rol == "depocu" else None,
    )


@router.get("/ozet", response_model=TerminalOzetResponseDTO)
@limiter.limit("60/minute")
def terminal_ozet(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviListeleUseCase = Depends(get_yerlestirme_gorevi_listele_uc),
):
    """Operatörün günlük istatistik özeti."""
    depo_id = _terminal_depo_id(current_user) if current_user.rol == "depocu" else None
    bekleyen = uc.execute(durum="Bekliyor", limit=10000, depo_id=depo_id)
    aktif_atanan = _aktif_gorevleri_getir(uc=uc, kullanici_id=current_user.id, depo_id=depo_id)

    # Bugün tamamlananlar — atanan kullanıcının TAMAMLANDI görevleri
    bugun_tamamlanan = sum(
        1 for g in uc.execute(durum="Tamamlandi", limit=10000, depo_id=depo_id)
        if g.atanan_kullanici_id == current_user.id
        and g.tamamlanma_tarihi
        and g.tamamlanma_tarihi.date() == datetime.now(timezone.utc).date()
    )

    return TerminalOzetResponseDTO(
        tarih=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        kullanici_id=current_user.id,
        bekleyen_gorev=len(bekleyen),
        benim_atanan_gorev=len(aktif_atanan),
        bugun_tamamlanan=bugun_tamamlanan,
    )


@router.post("/alternatif-raf", response_model=List[AlternatifRafDTO])
@limiter.limit("60/minute")
def alternatif_raf_oner(
    request: Request,
    dto: AlternatifRafRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    kapasite_svc=Depends(get_kapasite_dogrulama_servisi),
    palet_repo=Depends(get_palet_repo),
):
    """Kapasite hatası sonrası aynı zondaki alternatif rafları önerir."""
    raflar = kapasite_svc.alternatif_raflar_getir(
        zon_id=dto.zon_id, palet_kg=dto.palet_kg, limit=dto.limit
    )
    sonuc = []
    for raf in raflar:
        mevcut = palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True, limit=500)
        sonuc.append(AlternatifRafDTO(
            raf_id=raf.id,
            raf_kod=raf.kod,
            bos_slot=max(0, (raf.kapasite or 0) - len(mevcut)),
            skor=round(kapasite_svc.doluluk_orani(raf) * 100, 1),
        ))
    return sonuc


# ─────────────────────────────────────────
# PALET HATA LOGLAMA (KPI veri kaynağı)
# ─────────────────────────────────────────

class PaletHataLogRequestDTO(BaseModel):
    palet_barkod: str = Field(..., min_length=1, max_length=100)
    beklenen_palet_barkod: Optional[str] = Field(None, max_length=100)
    gorev_id: Optional[int] = None


@router.post("/log-palet-hata", status_code=204)
@limiter.limit("120/minute")
def palet_hata_logla(
    request: Request,
    dto: PaletHataLogRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    log_repo=Depends(get_log_repo),
):
    """Terminal: palet barkod eşleşmeme durumunu KPI için loglar."""
    detay = f"Palet hata: okutulan={dto.palet_barkod}"
    if dto.beklenen_palet_barkod:
        detay += f" | beklenen={dto.beklenen_palet_barkod}"
    if dto.gorev_id:
        detay += f" | gorev_id={dto.gorev_id}"

    log_repo.olustur(
        SistemLog.olustur(
            kullanici_id=current_user.id,
            islem_tipi=OlayTipi.PALET_OKUTMA_HATASI,
            modul="Terminal",
            detay=detay,
        )
    )
