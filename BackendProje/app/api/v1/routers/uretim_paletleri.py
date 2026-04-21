"""Üretim Paleti API Router — FAZ 4.

Thin controller: yetki kontrolü use case katmanında yapılır.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse

from app.core.auth import get_current_user
from app.infrastructure.persistence.mappers.kullanici_destek_mapper import kullanici_to_entity
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_uretim_paletleri_listele_uc,
    get_uretim_paleti_getir_uc,
    get_uretim_paleti_olustur_uc,
    get_uretim_paleti_kabul_bekle_uc,
    get_uretim_paleti_kabul_et_uc,
    get_uretim_paleti_karantina_al_uc,
    get_uretim_paleti_karantina_cikar_uc,
    get_uretim_paleti_iptal_uc,
    get_uretim_paleti_yerlestirme_bekle_uc,
    get_uretim_paleti_yerlestir_uc,
)
from app.application.dto.uretim_paleti_dto import (
    UretimPaletiOlusturRequestDTO,
    UretimPaletiKabulRequestDTO,
    UretimPaletiKarantinaRequestDTO,
    UretimPaletiKarantinaCikarRequestDTO,
    UretimPaletiIptalRequestDTO,
    UretimPaletiYerlestirRequestDTO,
    UretimPaletiResponseDTO,
)
from app.application.use_cases.uretim_paleti_use_cases import (
    UretimPaletleriListeleUseCase,
    UretimPaletiGetirUseCase,
    UretimPaletiOlusturUseCase,
    UretimPaletiKabulBekleUseCase,
    UretimPaletiKabulEtUseCase,
    UretimPaletiKarantinaAlUseCase,
    UretimPaletiKarantinaCikarUseCase,
    UretimPaletiIptalUseCase,
    UretimPaletiYerlestirmeBekleUseCase,
    UretimPaletiYerlestirUseCase,
)
router = APIRouter(prefix="/api/uretim-paletleri", tags=["Üretim Paletleri"])


# ── Listele ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[UretimPaletiResponseDTO])
@limiter.limit("100/minute")
def uretim_paletleri_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    lot_id: Optional[int] = Query(None),
    durum: Optional[str] = Query(None),
    vardiya: Optional[str] = Query(None),
    sadece_aktif: bool = Query(True),
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletleriListeleUseCase = Depends(get_uretim_paletleri_listele_uc),
):
    return uc.execute(
        skip=skip, limit=limit, lot_id=lot_id,
        durum=durum, vardiya=vardiya, sadece_aktif=sadece_aktif,
    )


# ── Detay ─────────────────────────────────────────────────────────────────────

@router.get("/{palet_no}", response_model=UretimPaletiResponseDTO)
@limiter.limit("100/minute")
def uretim_paleti_getir(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiGetirUseCase = Depends(get_uretim_paleti_getir_uc),
):
    return uc.execute(palet_no)


# ── Oluştur ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=UretimPaletiResponseDTO, status_code=201)
@limiter.limit("50/minute")
def uretim_paleti_olustur(
    request: Request,
    dto: UretimPaletiOlusturRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiOlusturUseCase = Depends(get_uretim_paleti_olustur_uc),
):
    return uc.execute(dto, kullanici_to_entity(current_user))


# ── Kabul Bekle ───────────────────────────────────────────────────────────────

@router.post("/{palet_no}/kabul-bekle", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_kabul_bekle(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiKabulBekleUseCase = Depends(get_uretim_paleti_kabul_bekle_uc),
):
    return uc.execute(palet_no, current_user)


# ── Kabul Et (Barkod Okutma) ──────────────────────────────────────────────────

@router.post("/{palet_no}/kabul-et", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_kabul_et(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiKabulEtUseCase = Depends(get_uretim_paleti_kabul_et_uc),
):
    return uc.execute(palet_no, current_user)


# ── Karantinaya Al ────────────────────────────────────────────────────────────

@router.post("/{palet_no}/karantina", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_karantina_al(
    request: Request,
    palet_no: str,
    dto: UretimPaletiKarantinaRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiKarantinaAlUseCase = Depends(get_uretim_paleti_karantina_al_uc),
):
    return uc.execute(palet_no, current_user, sebep=dto.sebep)


# ── Karantinadan Çıkar ────────────────────────────────────────────────────────

@router.post("/{palet_no}/karantina-cikar", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_karantina_cikar(
    request: Request,
    palet_no: str,
    dto: UretimPaletiKarantinaCikarRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiKarantinaCikarUseCase = Depends(get_uretim_paleti_karantina_cikar_uc),
):
    return uc.execute(palet_no, current_user, sebep=dto.sebep)


# ── İptal ─────────────────────────────────────────────────────────────────────

@router.post("/{palet_no}/iptal", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_iptal(
    request: Request,
    palet_no: str,
    dto: UretimPaletiIptalRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiIptalUseCase = Depends(get_uretim_paleti_iptal_uc),
):
    return uc.execute(palet_no, current_user, sebep=dto.sebep)


# ── Yerleştirme Bekle ─────────────────────────────────────────────────────────

@router.post("/{palet_no}/yerlestirme-bekle", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_yerlestirme_bekle(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiYerlestirmeBekleUseCase = Depends(get_uretim_paleti_yerlestirme_bekle_uc),
):
    return uc.execute(palet_no, current_user)


# ── Yerleştir ─────────────────────────────────────────────────────────────────

@router.post("/{palet_no}/yerlestir", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_yerlestir(
    request: Request,
    palet_no: str,
    dto: UretimPaletiYerlestirRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiYerlestirUseCase = Depends(get_uretim_paleti_yerlestir_uc),
):
    return uc.execute(palet_no, dto.raf_id, current_user)


# ── ZPL Etiket ────────────────────────────────────────────────────────────────

@router.get("/{palet_no}/etiket", response_class=PlainTextResponse)
@limiter.limit("30/minute")
def uretim_paleti_etiket(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiGetirUseCase = Depends(get_uretim_paleti_getir_uc),
):
    dto = uc.execute(palet_no)
    zpl = _zpl_olustur(dto)
    return PlainTextResponse(content=zpl, media_type="text/plain")


def _zpl_olustur(dto: UretimPaletiResponseDTO) -> str:
    pn = dto.palet_no
    urun_isim = dto.urun_isim or "-"
    lot_no = dto.lot_no or "-"
    skt_str = str(dto.lot_skt) if dto.lot_skt else "-"
    koli = dto.koli_adedi
    vardiya = dto.vardiya or "-"
    durum = dto.durum or "OLUSTURULDU"

    return (
        "^XA\n"
        "^CF0,30\n"
        f"^FO20,20^FDURETIM PALETI^FS\n"
        "^CF0,60\n"
        f"^FO20,60^FD{pn}^FS\n"
        "^BY3,2,100\n"
        f"^FO20,130^BC^FD{pn}^FS\n"
        "^CF0,25\n"
        f"^FO20,250^FDUrun: {urun_isim}^FS\n"
        f"^FO20,280^FDLot: {lot_no}^FS\n"
        f"^FO20,310^FDSKT: {skt_str}^FS\n"
        f"^FO20,340^FDKoli: {koli} adet^FS\n"
        f"^FO20,370^FDVardiya: {vardiya}^FS\n"
        f"^FO400,370^FD{durum}^FS\n"
        "^XZ\n"
    )
