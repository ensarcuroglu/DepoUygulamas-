"""Üretim Paleti API Router — FAZ 4 + FAZ 5 (Feature Flag).

Thin controller: yetki kontrolü use case katmanında yapılır.
Pilot depo kontrolü feature flag ile yönetilir.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from app.core.auth import get_current_user
from app.core.config import get_feature_flags
from app.core.entities.kullanici import KullaniciRol
from app.core.idempotency import idempotency_kaydet, idempotency_kontrol
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
    get_palet_etiket_olustur_uc,
    get_palet_etiketleri_listele_uc,
    get_palet_etiket_yazdir_uc,
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
from app.application.dto.etiket_dto import (
    PaletEtiketOlusturDTO,
    PaletEtiketResponseDTO,
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
from app.application.use_cases.palet_etiket_use_cases import (
    PaletEtiketOlusturUseCase,
    PaletEtiketleriListeleUseCase,
    PaletEtiketYazdirUseCase,
)
router = APIRouter(prefix="/api/uretim-paletleri", tags=["Üretim Paletleri"])


# ── Feature Flag Guard ────────────────────────────────────────────────────────

def _pilot_kontrol(current_user: Kullanici) -> None:
    """Kullanıcının pilot kapsamında olup olmadığını kontrol eder.

    Admin rolü her zaman erişebilir (ops/debug için bypass).
    """
    if current_user.rol == KullaniciRol.ADMIN:
        return
    flags = get_feature_flags()
    if not flags.uretim_paleti_aktif_mi(current_user.depo_id):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "OZELLIK_PILOTA_KAPALI",
                "message": "Üretim paleti özelliği şu anda yalnızca pilot depolar için aktiftir.",
            },
        )


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
    _pilot_kontrol(current_user)
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
    _pilot_kontrol(current_user)
    return uc.execute(palet_no, current_user)


# ── Kabul Et (Barkod Okutma) ──────────────────────────────────────────────────

@router.post("/{palet_no}/kabul-et", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_kabul_et(
    request: Request,
    palet_no: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiKabulEtUseCase = Depends(get_uretim_paleti_kabul_et_uc),
    db: Session = Depends(get_db),
):
    _pilot_kontrol(current_user)
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, "uretim_paleti_kabul_et")
        if cached is not None:
            return cached

    sonuc = uc.execute(palet_no, current_user)
    if idempotency_key:
        idempotency_kaydet(
            db,
            idempotency_key,
            "uretim_paleti_kabul_et",
            sonuc.model_dump(mode="json"),
        )
    return sonuc


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
    _pilot_kontrol(current_user)
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
    _pilot_kontrol(current_user)
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
    _pilot_kontrol(current_user)
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
    _pilot_kontrol(current_user)
    return uc.execute(palet_no, current_user)


# ── Yerleştir ─────────────────────────────────────────────────────────────────

@router.post("/{palet_no}/yerlestir", response_model=UretimPaletiResponseDTO)
@limiter.limit("50/minute")
def uretim_paleti_yerlestir(
    request: Request,
    palet_no: str,
    dto: UretimPaletiYerlestirRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(get_current_user),
    uc: UretimPaletiYerlestirUseCase = Depends(get_uretim_paleti_yerlestir_uc),
    db: Session = Depends(get_db),
):
    _pilot_kontrol(current_user)
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, "uretim_paleti_yerlestir")
        if cached is not None:
            return cached

    sonuc = uc.execute(palet_no, dto.raf_id, current_user)
    if idempotency_key:
        idempotency_kaydet(
            db,
            idempotency_key,
            "uretim_paleti_yerlestir",
            sonuc.model_dump(mode="json"),
        )
    return sonuc


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


# ── Palet Etiket (Şablon Bazlı) ───────────────────────────────────────────────

@router.get("/{palet_no}/etiketler", response_model=List[PaletEtiketResponseDTO])
@limiter.limit("100/minute")
def palet_etiketlerini_listele(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletEtiketleriListeleUseCase = Depends(get_palet_etiketleri_listele_uc),
):
    return uc.execute(palet_no)


@router.post("/{palet_no}/etiketler", response_model=PaletEtiketResponseDTO, status_code=201)
@limiter.limit("50/minute")
def palet_etiketi_olustur(
    request: Request,
    palet_no: str,
    dto: PaletEtiketOlusturDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletEtiketOlusturUseCase = Depends(get_palet_etiket_olustur_uc),
):
    return uc.execute(palet_no, dto, kullanici_to_entity(current_user))


@router.post("/etiketler/{etiket_id}/yazdir", response_model=PaletEtiketResponseDTO)
@limiter.limit("100/minute")
def palet_etiketi_yazdir(
    request: Request,
    etiket_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletEtiketYazdirUseCase = Depends(get_palet_etiket_yazdir_uc),
):
    return uc.execute(etiket_id, kullanici_to_entity(current_user))


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
